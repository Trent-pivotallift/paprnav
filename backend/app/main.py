import json
import logging
from enum import Enum

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette._utils import get_route_path
from urllib.parse import urlsplit

from app.api.deps import SESSION_COOKIE_NAME
from app.api.router import api_router
from app.core.config import get_settings, validate_runtime_settings
from app.core.http_protocol import cancellation_kind
from app.core.request_context import (
    CORRELATION_ID_HEADER,
    choose_correlation_id,
    reset_correlation_id,
    set_correlation_id,
)


unexpected_error_logger = logging.getLogger("paprnav.unexpected_error")


class HTTPDeliveryState(Enum):
    NEW = "not_started"
    PENDING = "start_buffered"
    START_ATTEMPTED = "start_delivery_uncertain"
    STARTED = "start_delivered"
    BODY_ATTEMPTED = "body_delivery_uncertain"
    STREAMING = "body_delivered"
    END_ATTEMPTED = "end_delivery_uncertain"
    COMPLETE = "complete"
    DISCONNECTED = "disconnected"


class HTTPDeliveryStopped(Exception):
    """Unwind an HTTP producer without retaining transport exception content."""


class PilotRequestBoundaryMiddleware:
    """Own correlation and sanitized failures for the complete HTTP lifecycle."""

    def __init__(self, app: ASGIApp, *, settings) -> None:
        self.app = app
        self.settings = settings

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        correlation_id = choose_correlation_id(
            request.headers.get(CORRELATION_ID_HEADER)
        )
        correlation_token = set_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id
        pending_start: Message | None = None
        delivery_state = HTTPDeliveryState.NEW
        response_status: int | None = None
        failure_state: HTTPDeliveryState | None = None
        cancellation: BaseException | None = None

        async def receive_with_disconnect() -> Message:
            nonlocal delivery_state
            message = await receive()
            if (
                message["type"] == "http.disconnect"
                and delivery_state != HTTPDeliveryState.COMPLETE
            ):
                delivery_state = HTTPDeliveryState.DISCONNECTED
            return message

        async def deliver(
            message: Message,
            attempted: HTTPDeliveryState,
            delivered: HTTPDeliveryState,
        ) -> None:
            nonlocal delivery_state
            # A send can fail before or after writing bytes. Set the state
            # before awaiting it; an exception must never authorize a retry.
            delivery_state = attempted
            await send(message)
            if delivery_state == HTTPDeliveryState.DISCONNECTED:
                raise HTTPDeliveryStopped()
            delivery_state = delivered

        async def send_with_correlation(message: Message) -> None:
            nonlocal pending_start, delivery_state, response_status
            message_type = message["type"]
            if message_type == "http.response.start":
                if delivery_state != HTTPDeliveryState.NEW:
                    raise HTTPDeliveryStopped()
                pending_start = dict(message)
                pending_start["headers"] = list(message.get("headers", []))
                MutableHeaders(scope=pending_start)[CORRELATION_ID_HEADER] = (
                    correlation_id
                )
                delivery_state = HTTPDeliveryState.PENDING
                return

            if message_type != "http.response.body" or delivery_state not in {
                HTTPDeliveryState.PENDING,
                HTTPDeliveryState.STARTED,
                HTTPDeliveryState.STREAMING,
            }:
                raise HTTPDeliveryStopped()

            if delivery_state == HTTPDeliveryState.PENDING:
                response_status = pending_start["status"]
                await deliver(
                    pending_start,
                    HTTPDeliveryState.START_ATTEMPTED,
                    HTTPDeliveryState.STARTED,
                )
                pending_start = None

            final_body = not message.get("more_body", False)
            await deliver(
                message,
                HTTPDeliveryState.END_ATTEMPTED if final_body else HTTPDeliveryState.BODY_ATTEMPTED,
                HTTPDeliveryState.COMPLETE if final_body else HTTPDeliveryState.STREAMING,
            )

        async def send_generic_error() -> None:
            response = JSONResponse(
                status_code=500,
                content={
                    "detail": "Unexpected server error",
                    "correlationId": correlation_id,
                },
            )

            await response(scope, receive_with_disconnect, send_with_correlation)

        try:
            try:
                if not self.settings.ad_v4_routes_enabled and is_ad_v4_path(
                    get_route_path(scope)
                ):
                    response = JSONResponse(
                        status_code=404,
                        content={"detail": "Not Found"},
                    )
                    await response(scope, receive_with_disconnect, send_with_correlation)
                elif (
                    self.settings.environment == "pilot"
                    and request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
                    and request.cookies.get(SESSION_COOKIE_NAME)
                    and request_origin(request) != self.settings.cors_origins[0]
                ):
                    response = JSONResponse(
                        status_code=403,
                        content={"detail": "Cross-origin request rejected"},
                    )
                    await response(scope, receive_with_disconnect, send_with_correlation)
                else:
                    await self.app(scope, receive_with_disconnect, send_with_correlation)

                if delivery_state == HTTPDeliveryState.PENDING:
                    await send_with_correlation(
                        {
                            "type": "http.response.body",
                            "body": b"",
                            "more_body": False,
                        }
                    )
                elif delivery_state in {
                    HTTPDeliveryState.NEW,
                    HTTPDeliveryState.STARTED,
                    HTTPDeliveryState.STREAMING,
                }:
                    raise HTTPDeliveryStopped()
            except BaseException as error:
                # Uvicorn logs even cancellation/BaseExceptionGroup failures
                # with exc_info. The HTTP boundary owns that entire path.
                failure_state = delivery_state
                if cancellation_kind(error) is not None:
                    cancellation = error
                try:
                    if cancellation is not None:
                        pass
                    elif delivery_state in {HTTPDeliveryState.NEW, HTTPDeliveryState.PENDING}:
                        pending_start = None
                        delivery_state = HTTPDeliveryState.NEW
                        await send_generic_error()
                    elif delivery_state in {HTTPDeliveryState.STARTED, HTTPDeliveryState.STREAMING}:
                        # Only confirmed delivery permits a terminator for the
                        # existing response. Never retry any uncertain send.
                        await send_with_correlation(
                            {"type": "http.response.body", "body": b"", "more_body": False}
                        )
                except BaseException as recovery_error:
                    # Recovery shares the same state machine and containment.
                    # A transport failure cannot reach Uvicorn's traceback log.
                    if cancellation_kind(recovery_error) is not None:
                        cancellation = recovery_error
            if failure_state is not None or delivery_state not in {HTTPDeliveryState.COMPLETE}:
                route = scope.get("route")
                route_template = getattr(route, "path", None) or "unmatched"
                method = request.method.upper()
                log_record = {
                    "event": "unexpected_request_error",
                    "routeTemplate": route_template,
                    "method": method if method in {"GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"} else "OTHER",
                    "status": 500,
                    "release": self.settings.app_version,
                    "correlationId": correlation_id,
                    "failureState": (failure_state or delivery_state).value,
                    "deliveryState": delivery_state.value,
                    "responseStatus": response_status,
                }
                if cancellation is not None:
                    log_record["failureKind"] = cancellation_kind(cancellation)
                for state_name, output_name in (
                    ("actor_user_id", "actorUserId"),
                    ("organization_id", "organizationId"),
                    ("aircraft_id", "aircraftId"),
                ):
                    value = getattr(request.state, state_name, None)
                    if value:
                        log_record[output_name] = value
                try:
                    unexpected_error_logger.error(
                        json.dumps(log_record, sort_keys=True, separators=(",", ":"))
                    )
                except Exception:
                    # A broken log sink must not expose its exception context
                    # through the default server traceback logger either.
                    pass
            if cancellation is not None:
                # The owned HTTP protocol consumes cancellation only after
                # request-local evidence and context cleanup, without a send.
                raise cancellation
        finally:
            reset_correlation_id(correlation_token)


def is_ad_v4_path(path: str) -> bool:
    segments = [segment for segment in path.split("/") if segment]
    return (
        len(segments) >= 4
        and segments[:3] == ["api", "v1", "ads"]
        and "v4" in segments[3:]
    )


def request_origin(request: Request) -> str | None:
    origin = request.headers.get("origin")
    if origin:
        return origin
    referer = request.headers.get("referer")
    if not referer:
        return None
    parsed = urlsplit(referer)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def create_app() -> FastAPI:
    settings = get_settings()
    validate_runtime_settings(settings)
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(PilotRequestBoundaryMiddleware, settings=settings)

    app.include_router(api_router)

    return app


app = create_app()
