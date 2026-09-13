from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any

import pypdf
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragment,
    ADEvidenceFragmentLifecycleEvent,
    ADPublication,
    ADSourceDocument,
    ADSourcePageRendition,
    ADSourcePageTextVersion,
    AirworthinessDirective,
    User,
)
from app.services.ad_extraction import (
    bounded_source_document_pages,
    extract_full_text_pages,
    retained_pdf_documents,
    verified_retained_document_bytes,
)
from app.services.page_images import (
    CANONICAL_RENDER_DPI,
    pdftoppm_version,
    png_dimensions,
    render_pdf_page_png,
)
from app.services.storage import read_stored_file_bytes, store_bytes


RENDITION_PROFILE = "ad-evidence-page-png-v1"
TEXT_PROFILE = "ad-evidence-bounded-native-text-v1"


class ADEvidenceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _canonical_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _hash_parts(*parts: object | None) -> str:
    """Match the PostgreSQL paprnav_hash_parts identity function exactly."""

    material = bytearray()
    for part in parts:
        if part is None:
            material.extend(b"-1:")
            continue
        encoded = str(part).encode("utf-8")
        material.extend(str(len(encoded)).encode("ascii"))
        material.extend(b":")
        material.extend(encoded)
    return hashlib.sha256(bytes(material)).hexdigest()


def _source_document_for_directive(
    db: Session,
    *,
    directive_id: str,
    source_document_id: str,
    lock_document: bool = True,
) -> tuple[AirworthinessDirective, ADSourceDocument]:
    directive = db.scalar(
        select(AirworthinessDirective).where(AirworthinessDirective.id == directive_id)
    )
    document_statement = select(ADSourceDocument).where(
        ADSourceDocument.id == source_document_id
    )
    if lock_document:
        document_statement = document_statement.with_for_update()
    document = db.scalar(document_statement)
    if directive is None or document is None:
        raise ADEvidenceError("not_found", "Directive or retained source document was not found")
    publication_id = db.scalar(
        select(ADPublication.id).where(
            ADPublication.directive_id == directive.id,
            ADPublication.source_document_id == document.id,
        )
    )
    if publication_id is None:
        raise ADEvidenceError(
            "wrong_document",
            "Retained source document is not attributable to this directive",
        )
    if document.media_type != "application/pdf":
        raise ADEvidenceError("unsupported_document", "Retained source document is not a PDF")
    return directive, document


def _bounded_page_identity_hash(pages: dict[tuple[str, int], str]) -> str:
    return _canonical_hash({
        "profile": TEXT_PROFILE,
        "pages": [
            {
                "sourceDocumentId": document_id,
                "pageNumber": page_number,
                "textHash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
            for (document_id, page_number), text in sorted(pages.items())
        ],
    })


def _bounded_page_text(
    db: Session,
    directive: AirworthinessDirective,
    *,
    source_document_id: str,
    page_number: int,
) -> str:
    documents = sorted(retained_pdf_documents(directive), key=lambda item: item.id)
    # Source bytes are reverified on every use. The cache avoids only repeated
    # PDF parsing inside one SQLAlchemy Session; it cannot hide stored-byte
    # tampering or cross a document/parser/configuration identity.
    for document in documents:
        try:
            verified_retained_document_bytes(document)
        except ValueError as exc:
            raise ADEvidenceError(
                "source_hash_mismatch",
                "Retained source bytes failed hash verification",
            ) from exc
        except Exception as exc:
            raise ADEvidenceError(
                "source_unavailable",
                "Retained source bytes are unavailable",
            ) from exc
    base_key = (
        "ad-evidence-bounded-pages-v1",
        getattr(pypdf, "__version__", "unknown"),
        directive.id,
        directive.ad_number,
        directive.title,
        tuple(
            (document.id, document.content_hash, document.storage_bytes)
            for document in documents
        ),
    )
    cache = db.info.setdefault("paprnav_ad_evidence_bounded_page_cache", {})
    identity_hash = cache.get(("index", base_key))
    page_map = cache.get((base_key, identity_hash)) if identity_hash is not None else None
    if page_map is not None and _bounded_page_identity_hash(page_map) != identity_hash:
        raise ADEvidenceError("page_text_hash_mismatch", "Cached bounded page identity failed verification")
    if page_map is None:
        pages = bounded_source_document_pages(
            extract_full_text_pages(directive),
            ad_number=directive.ad_number,
            title=directive.title,
        )
        page_map = {
            (str(page.get("sourceDocumentId")), int(page.get("pageNumber"))): str(page.get("text") or "")
            for page in pages
            if isinstance(page.get("pageNumber"), int) and str(page.get("text") or "").strip()
        }
        identity_hash = _bounded_page_identity_hash(page_map)
        cache[("index", base_key)] = identity_hash
        cache[(base_key, identity_hash)] = page_map
    match = page_map.get((source_document_id, page_number))
    if match is None or not match.strip():
        raise ADEvidenceError(
            "page_outside_directive",
            "Page is absent from the bounded official section for this directive",
        )
    return match


def _verified_rendition_bytes(rendition: ADSourcePageRendition) -> bytes:
    payload = read_stored_file_bytes(
        settings=get_settings(),
        storage_backend=rendition.storage_backend,
        storage_key=rendition.storage_key,
    )
    if (
        hashlib.sha256(payload).hexdigest() != rendition.rendition_hash
        or len(payload) != rendition.storage_bytes
    ):
        raise ADEvidenceError("rendition_hash_mismatch", "Stored page rendition failed hash verification")
    return payload


def _verified_new_rendition_bytes(
    *,
    storage_backend: str,
    storage_key: str,
    rendition_hash: str,
    storage_bytes: int,
    expected_dimensions: tuple[int, int],
) -> None:
    try:
        payload = read_stored_file_bytes(
            settings=get_settings(),
            storage_backend=storage_backend,
            storage_key=storage_key,
        )
    except Exception as exc:
        raise ADEvidenceError(
            "rendition_hash_mismatch",
            "Newly stored page rendition could not be read back",
        ) from exc
    if (
        hashlib.sha256(payload).hexdigest() != rendition_hash
        or len(payload) != storage_bytes
        or png_dimensions(payload) != expected_dimensions
    ):
        raise ADEvidenceError(
            "rendition_hash_mismatch",
            "Newly stored page rendition failed read-back verification",
        )


def materialize_source_page(
    db: Session,
    *,
    directive_id: str,
    source_document_id: str,
    page_number: int,
    expected_source_content_hash: str,
) -> tuple[ADSourcePageRendition, ADSourcePageTextVersion]:
    """Create or reuse immutable page artifacts from verified retained PDF bytes."""

    if page_number < 1:
        raise ADEvidenceError("invalid_page", "Page number must be one-based")
    directive, document = _source_document_for_directive(
        db,
        directive_id=directive_id,
        source_document_id=source_document_id,
    )
    if expected_source_content_hash != document.content_hash:
        raise ADEvidenceError("source_hash_mismatch", "Expected source hash does not match retained document")
    try:
        source_bytes = verified_retained_document_bytes(document)
    except ValueError as exc:
        raise ADEvidenceError("source_hash_mismatch", "Retained source bytes failed hash verification") from exc
    except Exception as exc:
        raise ADEvidenceError("source_unavailable", "Retained source bytes are unavailable") from exc

    bounded_text = _bounded_page_text(
        db,
        directive,
        source_document_id=document.id,
        page_number=page_number,
    )
    renderer_version = pdftoppm_version() or "unknown"
    renderer_configuration_hash = _canonical_hash({
        "profile": RENDITION_PROFILE,
        "renderer": "poppler_pdftoppm",
        "rendererVersion": renderer_version,
        "dpi": CANONICAL_RENDER_DPI,
        "format": "png",
    })
    rendition = db.scalar(
        select(ADSourcePageRendition).where(
            ADSourcePageRendition.source_document_id == document.id,
            ADSourcePageRendition.source_content_hash == document.content_hash,
            ADSourcePageRendition.page_number == page_number,
            ADSourcePageRendition.renderer_configuration_hash == renderer_configuration_hash,
        )
    )
    if rendition is None:
        try:
            rendered = render_pdf_page_png(
                source_bytes,
                page_number,
                dpi=CANONICAL_RENDER_DPI,
            )
        except Exception as exc:
            raise ADEvidenceError("rendition_failed", "Retained PDF page could not be rendered") from exc
        dimensions = png_dimensions(rendered or b"")
        if not rendered or dimensions is None:
            raise ADEvidenceError("rendition_failed", "Retained PDF page could not be rendered")
        rendition_hash = hashlib.sha256(rendered).hexdigest()
        storage_key = (
            f"ad-evidence-pages/{document.content_hash[:2]}/{document.content_hash}/"
            f"page-{page_number:05d}/{renderer_configuration_hash}/{rendition_hash}.png"
        )
        artifact_settings = replace(get_settings(), storage_backend=document.storage_backend)
        stored = store_bytes(
            rendered,
            settings=artifact_settings,
            storage_key=storage_key,
            content_type="image/png",
            cost_allocation_tags={
                "paprnav:cost-scope": "shared-ad-source",
                "paprnav:artifact": "ad-evidence-page-rendition",
                "paprnav:source-document": document.id,
            },
        )
        if stored.sha256 != rendition_hash or stored.file_size_bytes != len(rendered):
            raise ADEvidenceError("rendition_hash_mismatch", "Stored page rendition identity changed")
        _verified_new_rendition_bytes(
            storage_backend=stored.storage_backend,
            storage_key=stored.storage_key,
            rendition_hash=rendition_hash,
            storage_bytes=len(rendered),
            expected_dimensions=dimensions,
        )
        rendition = ADSourcePageRendition(
            source_document_id=document.id,
            source_content_hash=document.content_hash,
            page_number=page_number,
            renderer_name="poppler_pdftoppm",
            renderer_version=renderer_version,
            renderer_configuration_hash=renderer_configuration_hash,
            media_type="image/png",
            width_px=dimensions[0],
            height_px=dimensions[1],
            storage_backend=stored.storage_backend,
            storage_key=stored.storage_key,
            rendition_hash=stored.sha256,
            storage_bytes=stored.file_size_bytes,
        )
        db.add(rendition)
        db.flush()
    else:
        _verified_rendition_bytes(rendition)

    extractor_version = getattr(pypdf, "__version__", "unknown")
    extractor_configuration_hash = _canonical_hash({
        "profile": TEXT_PROFILE,
        "extractor": "pypdf-native-text",
        "extractorVersion": extractor_version,
        "scope": "bounded-official-ad-section",
        "directiveId": directive.id,
        "adNumber": directive.ad_number,
    })
    text_hash = hashlib.sha256(bounded_text.encode("utf-8")).hexdigest()
    text_version = db.scalar(
        select(ADSourcePageTextVersion).where(
            ADSourcePageTextVersion.rendition_id == rendition.id,
            ADSourcePageTextVersion.extractor_configuration_hash == extractor_configuration_hash,
            ADSourcePageTextVersion.text_hash == text_hash,
        )
    )
    if text_version is None:
        text_version = ADSourcePageTextVersion(
            rendition_id=rendition.id,
            source_document_id=document.id,
            source_content_hash=document.content_hash,
            page_number=page_number,
            extractor_name="pypdf-native-text",
            extractor_version=extractor_version,
            extractor_configuration_hash=extractor_configuration_hash,
            page_text=bounded_text,
            text_hash=text_hash,
            coordinate_map_storage_key=None,
            coordinate_map_hash=None,
            extraction_quality=None,
            text_classification="native",
        )
        db.add(text_version)
        db.flush()
    elif (
        text_version.page_text != bounded_text
        or hashlib.sha256(text_version.page_text.encode("utf-8")).hexdigest() != text_version.text_hash
    ):
        raise ADEvidenceError("page_text_hash_mismatch", "Stored page text failed hash verification")
    return rendition, text_version


def get_materialized_source_page(
    db: Session,
    *,
    directive_id: str,
    source_document_id: str,
    page_number: int,
    expected_source_content_hash: str,
) -> tuple[ADSourcePageRendition, ADSourcePageTextVersion]:
    """Read and verify existing page evidence without creating storage or rows."""

    if page_number < 1:
        raise ADEvidenceError("invalid_page", "Page number must be one-based")
    directive, document = _source_document_for_directive(
        db,
        directive_id=directive_id,
        source_document_id=source_document_id,
        lock_document=False,
    )
    if expected_source_content_hash != document.content_hash:
        raise ADEvidenceError("source_hash_mismatch", "Expected source hash does not match retained document")
    try:
        verified_retained_document_bytes(document)
    except ValueError as exc:
        raise ADEvidenceError("source_hash_mismatch", "Retained source bytes failed hash verification") from exc
    except Exception as exc:
        raise ADEvidenceError("source_unavailable", "Retained source bytes are unavailable") from exc
    bounded_text = _bounded_page_text(
        db,
        directive,
        source_document_id=document.id,
        page_number=page_number,
    )
    renderer_version = pdftoppm_version() or "unknown"
    renderer_configuration_hash = _canonical_hash({
        "profile": RENDITION_PROFILE,
        "renderer": "poppler_pdftoppm",
        "rendererVersion": renderer_version,
        "dpi": CANONICAL_RENDER_DPI,
        "format": "png",
    })
    rendition = db.scalar(select(ADSourcePageRendition).where(
        ADSourcePageRendition.source_document_id == document.id,
        ADSourcePageRendition.source_content_hash == document.content_hash,
        ADSourcePageRendition.page_number == page_number,
        ADSourcePageRendition.renderer_configuration_hash == renderer_configuration_hash,
    ))
    if rendition is None:
        raise ADEvidenceError("page_not_materialized", "Page evidence has not been materialized")
    _verified_rendition_bytes(rendition)
    extractor_version = getattr(pypdf, "__version__", "unknown")
    extractor_configuration_hash = _canonical_hash({
        "profile": TEXT_PROFILE,
        "extractor": "pypdf-native-text",
        "extractorVersion": extractor_version,
        "scope": "bounded-official-ad-section",
        "directiveId": directive.id,
        "adNumber": directive.ad_number,
    })
    text_hash = hashlib.sha256(bounded_text.encode("utf-8")).hexdigest()
    text_version = db.scalar(select(ADSourcePageTextVersion).where(
        ADSourcePageTextVersion.rendition_id == rendition.id,
        ADSourcePageTextVersion.source_document_id == document.id,
        ADSourcePageTextVersion.source_content_hash == document.content_hash,
        ADSourcePageTextVersion.page_number == page_number,
        ADSourcePageTextVersion.extractor_configuration_hash == extractor_configuration_hash,
        ADSourcePageTextVersion.text_hash == text_hash,
    ))
    if text_version is None:
        raise ADEvidenceError("page_not_materialized", "Page evidence has not been materialized")
    if text_version.page_text != bounded_text:
        raise ADEvidenceError("page_text_hash_mismatch", "Stored page text failed hash verification")
    return rendition, text_version


def _has_valid_admission_root(
    db: Session,
    *,
    fragment: ADEvidenceFragment,
) -> bool:
    event = db.scalar(select(ADEvidenceFragmentLifecycleEvent).where(
        ADEvidenceFragmentLifecycleEvent.fragment_id == fragment.id,
        ADEvidenceFragmentLifecycleEvent.event_type == "admitted",
        ADEvidenceFragmentLifecycleEvent.sequence_number == 0,
        ADEvidenceFragmentLifecycleEvent.predecessor_event_hash.is_(None),
    ))
    if event is None:
        return False
    return event.event_hash == _hash_parts(
        fragment.id,
        fragment.fragment_hash,
        event.event_type,
        event.actor_user_id,
        event.reason,
        event.sequence_number,
        event.predecessor_event_hash,
    )


def verified_evidence_lifecycle_events(
    db: Session,
    *,
    fragment: ADEvidenceFragment,
) -> list[ADEvidenceFragmentLifecycleEvent]:
    """Return a dense, hash-verified evidence lifecycle chain."""

    events = db.scalars(
        select(ADEvidenceFragmentLifecycleEvent)
        .where(ADEvidenceFragmentLifecycleEvent.fragment_id == fragment.id)
        .order_by(ADEvidenceFragmentLifecycleEvent.sequence_number)
    ).all()
    if not events or [event.sequence_number for event in events] != list(
        range(len(events))
    ):
        raise ADEvidenceError(
            "evidence_lifecycle_integrity",
            "Evidence lifecycle sequence is incomplete",
        )
    for index, event in enumerate(events):
        predecessor_hash = None if index == 0 else events[index - 1].event_hash
        if (
            event.predecessor_event_hash != predecessor_hash
            or (index == 0 and event.event_type != "admitted")
            or (index > 0 and event.event_type not in {"superseded", "quarantined"})
            or event.event_hash != _hash_parts(
                fragment.id,
                fragment.fragment_hash,
                event.event_type,
                event.actor_user_id,
                event.reason,
                event.sequence_number,
                event.predecessor_event_hash,
            )
        ):
            raise ADEvidenceError(
                "evidence_lifecycle_integrity",
                "Evidence lifecycle chain or hash differs",
            )
    return events


def admit_evidence_fragment(
    db: Session,
    *,
    directive_id: str,
    source_document_id: str,
    page_number: int,
    expected_source_content_hash: str,
    expected_page_text_hash: str,
    character_start: int,
    character_end: int,
    actor: User,
    reason: str,
    paragraph_locator: str | None = None,
    table_locator: str | None = None,
    row_locator: str | None = None,
    note_locator: str | None = None,
) -> tuple[ADEvidenceFragment, bool]:
    rendition, text_version = materialize_source_page(
        db,
        directive_id=directive_id,
        source_document_id=source_document_id,
        page_number=page_number,
        expected_source_content_hash=expected_source_content_hash,
    )
    if expected_page_text_hash != text_version.text_hash:
        raise ADEvidenceError("page_text_hash_mismatch", "Expected page-text hash is stale or incorrect")
    if character_start < 0 or character_end <= character_start:
        raise ADEvidenceError("invalid_selection", "Fragment selection must have a positive bounded length")
    if character_end > len(text_version.page_text):
        raise ADEvidenceError("invalid_selection", "Fragment selection extends beyond the bounded page text")
    exact_text = text_version.page_text[character_start:character_end]
    if not exact_text.strip():
        raise ADEvidenceError("empty_selection", "Fragment selection contains no source wording")
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise ADEvidenceError("missing_reason", "Fragment admission requires a reason")
    locators = {
        "paragraph": paragraph_locator.strip() if paragraph_locator and paragraph_locator.strip() else None,
        "table": table_locator.strip() if table_locator and table_locator.strip() else None,
        "row": row_locator.strip() if row_locator and row_locator.strip() else None,
        "note": note_locator.strip() if note_locator and note_locator.strip() else None,
    }
    fragment_hash = _hash_parts(
        directive_id, source_document_id, rendition.source_content_hash,
        rendition.id, text_version.id, page_number, page_number,
        character_start, character_end,
        locators["paragraph"], locators["table"], locators["row"], locators["note"],
        None, exact_text, text_version.extractor_name, text_version.extractor_version,
    )
    existing = db.scalar(
        select(ADEvidenceFragment).where(ADEvidenceFragment.fragment_hash == fragment_hash)
    )
    if existing is not None:
        if not _has_valid_admission_root(db, fragment=existing):
            raise ADEvidenceError(
                "fragment_not_admitted",
                "Existing evidence fragment lacks a valid admission root",
            )
        return existing, False

    fragment = ADEvidenceFragment(
        directive_id=directive_id,
        source_document_id=source_document_id,
        source_content_hash=rendition.source_content_hash,
        rendition_id=rendition.id,
        page_text_version_id=text_version.id,
        page_start=page_number,
        page_end=page_number,
        paragraph_locator=locators["paragraph"],
        table_locator=locators["table"],
        row_locator=locators["row"],
        note_locator=locators["note"],
        character_start=character_start,
        character_end=character_end,
        region_map_hash=None,
        exact_text=exact_text,
        fragment_hash=fragment_hash,
        parser_name=text_version.extractor_name,
        parser_version=text_version.extractor_version,
        created_by_user_id=actor.id,
    )
    db.add(fragment)
    db.flush()
    event_hash = _hash_parts(
        fragment.id, fragment.fragment_hash, "admitted", actor.id,
        normalized_reason, 0, None,
    )
    db.add(ADEvidenceFragmentLifecycleEvent(
        fragment_id=fragment.id,
        event_type="admitted",
        actor_user_id=actor.id,
        reason=normalized_reason,
        sequence_number=0,
        predecessor_event_hash=None,
        event_hash=event_hash,
    ))
    db.flush()
    return fragment, True
