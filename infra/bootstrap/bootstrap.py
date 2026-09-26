#!/usr/bin/env python3
"""Fixed-phase bootstrap for the sealed Paprnav pilot image.

This module deliberately has no import from ``app``. Production credentials are
read in-process from task-scoped Secrets Manager ARNs and are never accepted as
command-line values or printed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
from typing import Any, Callable, Mapping
from urllib.parse import quote
import uuid

import psycopg
from psycopg import sql


APP_ROLE = "paprnav_app"
CONTROL_SCHEMA = "pilot_control"
ADVISORY_LOCK_KEY = 824082
PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
PHASES = ("migration", "runtime-role", "reference", "first-admin")
BOOTSTRAP_ROOT = Path(__file__).resolve().parent
MIGRATION_ROOT = Path(os.getenv("PAPRNAV_MIGRATION_ROOT", "/migration"))
GRANT_MANIFEST = BOOTSTRAP_ROOT / "grant-manifest.json"
REFERENCE_DATA = BOOTSTRAP_ROOT / "reference-data.json"
SAFE_IDENTITY = re.compile(r"^[^\x00-\x1f\x7f]+$")
DATABASE_HOST = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)


class BootstrapError(RuntimeError):
    """A sanitized, operator-actionable bootstrap failure."""


def emit(phase: str, status: str, **identifiers: str) -> None:
    payload = {"phase": phase, "status": status, **identifiers}
    print(json.dumps(payload, sort_keys=True), flush=True)


def require_env(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise BootstrapError(f"required environment input is absent: {name}")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"invalid sealed JSON input: {path.name}") from exc
    if not isinstance(value, dict):
        raise BootstrapError(f"sealed JSON input is not an object: {path.name}")
    return value


def secret_json(client: Any, arn: str, *, exact_keys: set[str] | None = None) -> dict[str, Any]:
    response = client.get_secret_value(SecretId=arn)
    value = response.get("SecretString")
    if not isinstance(value, str):
        raise BootstrapError("required secret is not a SecretString")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise BootstrapError("required secret is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise BootstrapError("required secret JSON is not an object")
    if exact_keys is not None and set(parsed) != exact_keys:
        raise BootstrapError("required secret has an unexpected schema")
    return parsed


def admin_connection(secret_client: Any) -> dict[str, Any]:
    value = secret_json(secret_client, require_env("PAPRNAV_ADMIN_SECRET_ARN"))
    required = {"username", "password"}
    if not required.issubset(value):
        raise BootstrapError("RDS administrator secret is missing required credentials")
    if value["username"] != "paprnav_admin":
        raise BootstrapError("RDS administrator secret has the wrong username")
    if not isinstance(value["password"], str) or not value["password"]:
        raise BootstrapError("RDS administrator secret has an invalid password")

    host = require_env("PAPRNAV_DATABASE_HOST")
    if DATABASE_HOST.fullmatch(host) is None:
        raise BootstrapError("database host environment input is invalid")
    port_text = require_env("PAPRNAV_DATABASE_PORT")
    if re.fullmatch(r"[0-9]{1,5}", port_text) is None:
        raise BootstrapError("database port environment input is invalid")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise BootstrapError("database port environment input is outside 1..65535")
    return {
        "host": host,
        "port": port,
        "dbname": os.getenv("PAPRNAV_DATABASE_NAME", "paprnav"),
        "user": value["username"],
        "password": value["password"],
        "sslmode": os.getenv("PAPRNAV_DATABASE_SSLMODE", "require"),
    }


def sqlalchemy_url(connection: Mapping[str, Any]) -> str:
    return (
        "postgresql+psycopg://"
        f"{quote(str(connection['user']), safe='')}:{quote(str(connection['password']), safe='')}"
        f"@{connection['host']}:{connection['port']}/{quote(str(connection['dbname']), safe='')}"
        f"?sslmode={quote(str(connection['sslmode']), safe='')}"
    )


def alembic_environment_url(connection: Mapping[str, Any]) -> str:
    """Return a URL that survives Alembic's ConfigParser interpolation.

    ``env.py`` copies ``DATABASE_URL`` into Alembic's Config object.  Percent
    escapes in a valid SQLAlchemy URL therefore need ConfigParser's literal
    percent spelling.  This escaping belongs only at the migration-process
    boundary; the application secret retains the ordinary URL.
    """

    return sqlalchemy_url(connection).replace("%", "%%")


def run_migration(secret_client: Any) -> None:
    connection = admin_connection(secret_client)
    command = [
        sys.executable,
        "-I",
        "-B",
        "-m",
        "alembic",
        "-c",
        str(MIGRATION_ROOT / "alembic.ini"),
        "upgrade",
        "20260913_0029",
    ]
    environment = {
        "DATABASE_URL": alembic_environment_url(connection),
        "PAPRNAV_DISABLE_DOTENV": "1",
        "PAPRNAV_ENV": "pilot",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PATH": os.environ.get("PATH", ""),
    }
    result = subprocess.run(
        command,
        cwd=MIGRATION_ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode:
        raise BootstrapError("sealed migration failed; child output suppressed")


def relation_inventory(cursor: Any, relation_kind: str) -> list[str]:
    if relation_kind == "tables":
        cursor.execute(
            "SELECT tablename FROM pg_catalog.pg_tables "
            "WHERE schemaname='public' ORDER BY tablename"
        )
    elif relation_kind == "sequences":
        cursor.execute(
            "SELECT sequencename FROM pg_catalog.pg_sequences "
            "WHERE schemaname='public' ORDER BY sequencename"
        )
    else:  # pragma: no cover - internal programming guard
        raise AssertionError(relation_kind)
    return [row[0] for row in cursor.fetchall()]


def exact_grant_inventory(cursor: Any, manifest: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    cursor.execute("SELECT version_num FROM public.alembic_version")
    rows = cursor.fetchall()
    if rows != [(manifest["expectedHead"],)]:
        raise BootstrapError("database is not at the sealed migration head")
    actual_tables = relation_inventory(cursor, "tables")
    actual_sequences = relation_inventory(cursor, "sequences")
    expected_tables = sorted([*manifest["publicTables"], *manifest["excludedTables"]])
    expected_sequences = sorted(manifest["publicSequences"])
    if actual_tables != expected_tables or actual_sequences != expected_sequences:
        raise BootstrapError("post-migration relation inventory differs from the reviewed grant manifest")
    return sorted(manifest["publicTables"]), expected_sequences


def install_control_schema(cursor: Any) -> None:
    cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION CURRENT_USER").format(
        sql.Identifier(CONTROL_SCHEMA)
    ))
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pilot_control.bootstrap_consumptions (
          bootstrap_key text PRIMARY KEY CHECK (bootstrap_key = 'first-admin'),
          consumed_at timestamptz NOT NULL DEFAULT now(),
          user_id varchar(36) NOT NULL,
          organization_id varchar(36) NOT NULL,
          identity_sha256 char(64) NOT NULL
        )
        """
    )
    cursor.execute("REVOKE ALL ON SCHEMA pilot_control FROM PUBLIC")


def ensure_app_role(cursor: Any, password: str) -> None:
    cursor.execute("SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=%s", (APP_ROLE,))
    if cursor.fetchone() is None:
        cursor.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT").format(
            sql.Identifier(APP_ROLE)
        ))
    cursor.execute(
        sql.SQL("ALTER ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD {}").format(
            sql.Identifier(APP_ROLE), sql.Literal(password)
        )
    )


def apply_exact_grants(cursor: Any, tables: list[str], sequences: list[str], database_name: str) -> None:
    cursor.execute(sql.SQL("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
    cursor.execute(sql.SQL("REVOKE ALL ON SCHEMA public FROM {}").format(sql.Identifier(APP_ROLE)))
    cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(APP_ROLE)))
    cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
        sql.Identifier(database_name), sql.Identifier(APP_ROLE)
    ))
    cursor.execute(sql.SQL("REVOKE ALL ON SCHEMA pilot_control FROM {}").format(sql.Identifier(APP_ROLE)))
    cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES REVOKE ALL ON TABLES FROM {}").format(
        sql.Identifier(APP_ROLE)
    ))
    cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES REVOKE ALL ON SEQUENCES FROM {}").format(
        sql.Identifier(APP_ROLE)
    ))
    for table in tables:
        identifier = sql.Identifier("public", table)
        cursor.execute(sql.SQL("REVOKE ALL ON TABLE {} FROM {}").format(identifier, sql.Identifier(APP_ROLE)))
        cursor.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {} TO {}").format(
            identifier, sql.Identifier(APP_ROLE)
        ))
    for sequence in sequences:
        identifier = sql.Identifier("public", sequence)
        cursor.execute(sql.SQL("REVOKE ALL ON SEQUENCE {} FROM {}").format(identifier, sql.Identifier(APP_ROLE)))
        cursor.execute(sql.SQL("GRANT USAGE, SELECT ON SEQUENCE {} TO {}").format(
            identifier, sql.Identifier(APP_ROLE)
        ))


def app_connection(admin: Mapping[str, Any], password: str) -> dict[str, Any]:
    return {**admin, "user": APP_ROLE, "password": password}


def run_runtime_role(secret_client: Any, connect: Callable[..., Any] = psycopg.connect) -> None:
    admin = admin_connection(secret_client)
    manifest = load_json(GRANT_MANIFEST)
    generated_password = secrets.token_urlsafe(48)
    with connect(**admin) as connection:
        with connection.cursor() as cursor:
            tables, sequences = exact_grant_inventory(cursor, manifest)
            install_control_schema(cursor)
            ensure_app_role(cursor, generated_password)
            apply_exact_grants(cursor, tables, sequences, str(admin["dbname"]))
        connection.commit()

    app_secret_arn = require_env("PAPRNAV_APP_DATABASE_SECRET_ARN")
    token = str(uuid.uuid4())
    payload = json.dumps(
        {"DATABASE_URL": sqlalchemy_url(app_connection(admin, generated_password))},
        sort_keys=True,
        separators=(",", ":"),
    )
    publication = secret_client.put_secret_value(
        SecretId=app_secret_arn,
        SecretString=payload,
        ClientRequestToken=token,
        VersionStages=["AWSCURRENT"],
    )
    version_id = publication.get("VersionId")
    if not isinstance(version_id, str) or not version_id:
        raise BootstrapError("app database secret publication returned no VersionId")
    metadata = secret_client.describe_secret(SecretId=app_secret_arn)
    stages = metadata.get("VersionIdsToStages", {}).get(version_id, [])
    if "AWSCURRENT" not in stages:
        raise BootstrapError("published app database secret version is not AWSCURRENT")
    with connect(**app_connection(admin, generated_password)) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user")
            if cursor.fetchone() != (APP_ROLE,):
                raise BootstrapError("fresh runtime-role connection proof failed")


def run_reference(secret_client: Any, connect: Callable[..., Any] = psycopg.connect) -> None:
    data = load_json(REFERENCE_DATA)
    rows = data.get("logbookSections")
    if not isinstance(rows, list) or not rows:
        raise BootstrapError("reference manifest has no logbook sections")
    admin = admin_connection(secret_client)
    with connect(**admin) as connection:
        with connection.cursor() as cursor:
            for row in rows:
                if set(row) != {"id", "key", "name", "sortOrder"}:
                    raise BootstrapError("reference row has an unexpected schema")
                cursor.execute(
                    """
                    INSERT INTO public.logbook_sections (id, key, name, sort_order)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET name=EXCLUDED.name, sort_order=EXCLUDED.sort_order
                    """,
                    (row["id"], row["key"], row["name"], row["sortOrder"]),
                )
        connection.commit()


def clean_identity(name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 255 or SAFE_IDENTITY.fullmatch(normalized) is None:
        raise BootstrapError(f"invalid first-admin identity input: {name}")
    return normalized


def password_hash(password: str) -> str:
    if len(password.encode("utf-8")) < 12:
        raise BootstrapError("first-admin password does not meet the minimum length")
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "$".join((PASSWORD_ALGORITHM, str(PASSWORD_ITERATIONS), salt.hex(), digest.hex()))


def maybe_fail(point: str) -> None:
    if os.getenv("PAPRNAV_BOOTSTRAP_FAIL_AFTER") == point:
        raise BootstrapError(f"injected failure after {point}")


def run_first_admin(
    secret_client: Any,
    connect: Callable[..., Any] = psycopg.connect,
    identity: Mapping[str, str] | None = None,
) -> dict[str, str]:
    admin = admin_connection(secret_client)
    password_value = secret_json(
        secret_client,
        require_env("PAPRNAV_FIRST_ADMIN_SECRET_ARN"),
        exact_keys={"password"},
    )
    password = password_value["password"]
    if not isinstance(password, str):
        raise BootstrapError("first-admin password secret has the wrong type")
    supplied_identity = identity or {
        "email": require_env("PAPRNAV_FIRST_ADMIN_EMAIL"),
        "name": require_env("PAPRNAV_FIRST_ADMIN_NAME"),
        "organization": require_env("PAPRNAV_FIRST_ADMIN_ORGANIZATION"),
    }
    if set(supplied_identity) != {"email", "name", "organization"}:
        raise BootstrapError("first-admin identity has an unexpected schema")
    email = clean_identity("email", supplied_identity["email"]).lower()
    name = clean_identity("name", supplied_identity["name"])
    organization_name = clean_identity("organization", supplied_identity["organization"])
    identity_sha256 = hashlib.sha256(email.encode("utf-8")).hexdigest()
    user_id = f"usr_{uuid.uuid4().hex}"
    organization_id = f"org_{uuid.uuid4().hex}"
    membership_id = f"mem_{uuid.uuid4().hex}"
    event_id = f"pev_{uuid.uuid4().hex}"

    with connect(**admin) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", (ADVISORY_LOCK_KEY,))
            cursor.execute("SELECT to_regclass('pilot_control.bootstrap_consumptions')")
            if cursor.fetchone() != ("pilot_control.bootstrap_consumptions",):
                raise BootstrapError("bootstrap control schema is absent; run runtime-role first")
            cursor.execute("SELECT count(*) FROM pilot_control.bootstrap_consumptions")
            consumed = cursor.fetchone()[0]
            counts: list[int] = []
            for table in ("users", "organizations", "organization_memberships"):
                cursor.execute(sql.SQL("SELECT count(*) FROM public.{}").format(sql.Identifier(table)))
                counts.append(cursor.fetchone()[0])
            if consumed != 0 or counts != [0, 0, 0]:
                raise BootstrapError("first-admin bootstrap is permanently unavailable")

            cursor.execute(
                "INSERT INTO public.users (id,email,name,password_hash,status) VALUES (%s,%s,%s,%s,'active')",
                (user_id, email, name, password_hash(password)),
            )
            maybe_fail("user")
            cursor.execute(
                "INSERT INTO public.organizations (id,name,type) VALUES (%s,%s,'platform')",
                (organization_id, organization_name),
            )
            maybe_fail("organization")
            cursor.execute(
                """
                INSERT INTO public.organization_memberships
                  (id,organization_id,user_id,role,status)
                VALUES (%s,%s,%s,'platform_admin','active')
                """,
                (membership_id, organization_id, user_id),
            )
            maybe_fail("membership")
            cursor.execute(
                """
                INSERT INTO public.product_events
                  (id,actor_user_id,organization_id,event_type,event_source,subject_type,subject_id,properties_json)
                VALUES (%s,%s,%s,'pilot_first_admin_created','bootstrap','user',%s,%s::json)
                """,
                (
                    event_id,
                    user_id,
                    organization_id,
                    user_id,
                    json.dumps({"identitySha256": identity_sha256}, separators=(",", ":")),
                ),
            )
            maybe_fail("audit")
            cursor.execute(
                """
                INSERT INTO pilot_control.bootstrap_consumptions
                  (bootstrap_key,user_id,organization_id,identity_sha256)
                VALUES ('first-admin',%s,%s,%s)
                """,
                (user_id, organization_id, identity_sha256),
            )
            maybe_fail("consumption")
        connection.commit()
    return {"userId": user_id, "organizationId": organization_id}


def secrets_client() -> Any:
    # Keep the AWS SDK import inside the production boundary; unit tests inject
    # a fake client without importing an application package.
    import boto3

    return boto3.client("secretsmanager", region_name=require_env("AWS_REGION"))


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("phase", choices=PHASES)
    args = parser.parse_args()
    phase = args.phase
    try:
        client = secrets_client()
        if phase == "migration":
            run_migration(client)
            result: dict[str, str] = {}
        elif phase == "runtime-role":
            run_runtime_role(client)
            result = {}
        elif phase == "reference":
            run_reference(client)
            result = {}
        else:
            result = run_first_admin(client)
        emit(phase, "success", **result)
        return 0
    except (BootstrapError, psycopg.Error, OSError, ValueError) as exc:
        # Messages are written by this module and never include secret values or
        # connection strings. Driver exceptions are intentionally suppressed.
        message = str(exc) if isinstance(exc, BootstrapError) else "phase failed; sensitive detail suppressed"
        emit(phase, "failure", reason=message)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
