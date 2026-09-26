"""Backend-only production privacy oracle. Run against requirements.lock; no skips."""
from __future__ import annotations

import asyncio
import importlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uvicorn import Server
from uvicorn.server import ServerState

from app.core.config import get_settings
from app.core.http_protocol import cancellation_kind
from app.core.request_context import get_correlation_id
from app.db.session import get_db
from app.main import PilotRequestBoundaryMiddleware
from app.models.core import IngestionJob, IngestionPage, Upload
from tests.conftest import login


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _assert_locked_versions(versions):
    lock = (BACKEND_ROOT / "requirements.lock").read_text()
    for name, actual in versions.items():
        pins = re.findall(rf"^{re.escape(name)}==([^\s]+)", lock, re.MULTILINE)
        assert len(pins) == 1, (name, pins)
        assert actual == pins[0], (name, actual, pins[0])


@pytest.fixture(scope="module", autouse=True)
def locked_runtime_gate():
    # Runs before every case in this module. A stale venv is a failure, not a
    # skipped image assertion or a second source of expected package versions.
    names = ("uvicorn", "h11", "starlette", "anyio", "fastapi")
    _assert_locked_versions({name: importlib.metadata.version(name) for name in names})
    result = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    for name in names:
        module_path = Path(importlib.import_module(name).__file__).resolve()
        assert module_path.is_file()
        assert "site-packages" in module_path.parts


def _fresh_process(code, *args):
    # Deliberately do not inherit host credentials or configurable providers.
    environment = {
        "PATH": os.environ["PATH"], "PYTHONPATH": str(BACKEND_ROOT),
        "PAPRNAV_DISABLE_DOTENV": "1", "DATABASE_URL": "sqlite+pysqlite:///:memory:",
        "PAPRNAV_ENV": "local", "AWS_EC2_METADATA_DISABLED": "true",
    }
    result = subprocess.run([sys.executable, "-c", code, *args], cwd=BACKEND_ROOT,
                            env=environment, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_launcher_startup_shutdown_and_handler_graph():
    command = next(line for line in (BACKEND_ROOT / "Dockerfile").read_text().splitlines() if line.startswith("CMD "))
    assert json.loads(command[4:]) == ["python", "-m", "pilot_server"]
    result = _fresh_process('''
import asyncio, builtins, logging, sys
original_import = builtins.__import__
seen = []
def checked_import(name, *args, **kwargs):
    if name == "uvicorn" or name == "app.main":
        assert logging.raiseExceptions is False
        seen.append(name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = checked_import
import pilot_server
assert "uvicorn" not in sys.modules
config = pilot_server.create_config()
assert logging.raiseExceptions is False
assert config.app == "main:app" and config.host == "0.0.0.0" and config.port == 8000
assert config.http == "app.core.http_protocol:PilotH11Protocol"
assert config.access_log is False and config.log_level == "info"
assert config.timeout_graceful_shutdown == 10
config.load()
assert config.http_protocol_class.__name__ == "PilotH11Protocol"
assert not logging.getLogger("uvicorn.access").hasHandlers()
assert logging.getLogger("uvicorn.error").isEnabledFor(logging.INFO)
assert not logging.getLogger("uvicorn.error").isEnabledFor(logging.DEBUG)
assert not logging.getLogger("uvicorn.error").isEnabledFor(5)
handlers = logging.getLogger("uvicorn").handlers
assert len(handlers) == 1 and type(handlers[0]) is logging.StreamHandler
assert not handlers[0].filters
assert type(logging.lastResort).__name__ == "_StderrHandler"
assert not logging.lastResort.filters
assert not logging.getLogger().handlers
assert not logging.getLogger("paprnav.unexpected_error").handlers
logging.getLogger("uvicorn.error").info("healthy operational record")
logging.getLogger("paprnav.unexpected_error").error("healthy safe application record")
async def lifecycle():
    lifespan = config.lifespan_class(config)
    await lifespan.startup()
    assert not lifespan.should_exit and logging.raiseExceptions is False
    await lifespan.shutdown()
    assert logging.raiseExceptions is False
asyncio.run(lifecycle())
logging.shutdown()
assert logging.raiseExceptions is False
assert "uvicorn" in seen and "app.main" in seen
sys.argv = ["pilot_server", "--log-level=trace"]
try:
    pilot_server.main()
except SystemExit:
    pass
else:
    raise AssertionError("launcher allowed an override")
print("startup-shutdown-policy-ok")
''')
    assert "startup-shutdown-policy-ok" in result.stdout
    assert "healthy operational record" in result.stderr
    assert "healthy safe application record" in result.stderr
    assert "Traceback" not in result.stderr


SINK_PROBE = '''
import asyncio, io, json, logging, sys
import pilot_server
pilot_server.create_config()
from app.core.config import get_settings
from app.core.request_context import get_correlation_id
from app.main import PilotRequestBoundaryMiddleware
family, failure, negative = sys.argv[1:]
secret = "sink-" + failure + "-private-sentinel"
records, handle_errors = [], []
original_factory = logging.getLogRecordFactory()
def factory(*args, **kwargs):
    record = original_factory(*args, **kwargs)
    records.append(record)
    return record
logging.setLogRecordFactory(factory)
logger = logging.getLogger("uvicorn.error" if family == "uvicorn" else "paprnav.unexpected_error")
handler = logging.getLogger("uvicorn").handlers[0] if family == "uvicorn" else logging.lastResort
old_stderr, old_stdout = sys.stderr, sys.stdout
diagnostics, output, partial = io.StringIO(), io.StringIO(), io.StringIO()
class BrokenStream:
    def write(self, value):
        if failure == "write_partial":
            partial.write(value[:9])
        if failure in ("write", "write_partial"):
            raise OSError(secret)
        partial.write(value)
    def flush(self):
        if failure in ("flush", "shutdown"):
            raise OSError(secret)
class BrokenFormatter(logging.Formatter):
    def format(self, record):
        raise ValueError(secret)
saved_formatter = handler.formatter
saved_handle_error = handler.handleError
def observe_handle_error(record):
    handle_errors.append(record)
    # _StderrHandler's stream is dynamic. Separate the failing sink from the
    # stderr diagnostic channel while invoking the real stdlib implementation.
    sys.stderr = diagnostics
    try:
        saved_handle_error(record)
    finally:
        sys.stderr = broken if family == "fallback" else diagnostics
handler.handleError = observe_handle_error
broken = BrokenStream()
if family == "uvicorn":
    handler.stream = broken
    sys.stderr = diagnostics
else:
    sys.stderr = broken
sys.stdout = output
if failure == "formatter":
    handler.setFormatter(BrokenFormatter())
if negative == "true":
    logging.raiseExceptions = True
if failure == "shutdown":
    # Exercise the real shutdown branch against this exact effective handler.
    import weakref
    logging.shutdown([weakref.ref(handler)])
else:
    if family == "fallback":
        sent = []
        async def application(scope, receive, send):
            raise RuntimeError("application-private-sentinel")
        async def send(message):
            sent.append(message)
        async def receive():
            return {"type": "http.request", "body": b"private body"}
        async def request():
            scope = {"type": "http", "method": "GET", "path": "/private-path", "root_path": "",
                     "headers": [(b"x-correlation-id", b"sink-request")], "query_string": b"secret=query", "state": {}}
            await PilotRequestBoundaryMiddleware(application, settings=get_settings())(scope, receive, send)
            assert get_correlation_id() is None
        asyncio.run(request())
        assert len(sent) == 2 and sent[0]["status"] == 500
        assert json.loads(sent[1]["body"])["correlationId"] == "sink-request"
    else:
        logger.error("sanitized failure event")
    assert len(records) == 1 and len(handle_errors) == 1
assert all(r.exc_info is None and r.exc_text is None and r.stack_info is None for r in records)
assert secret not in repr([r.__dict__ for r in records])
handler.handleError = saved_handle_error
handler.setFormatter(saved_formatter)
if family == "uvicorn":
    handler.stream = old_stderr
sys.stderr, sys.stdout = old_stderr, old_stdout
logging.raiseExceptions = False
logger.error("later healthy record")
print(json.dumps({"diagnostics": diagnostics.getvalue(), "stdout": output.getvalue(),
                  "partial": partial.getvalue(), "secret": secret, "records": len(records)}))
'''


@pytest.mark.parametrize("family", ["uvicorn", "fallback"])
@pytest.mark.parametrize("failure", ["formatter", "write", "write_partial", "flush", "shutdown"])
def test_effective_handler_failures(family, failure):
    result = _fresh_process(SINK_PROBE, family, failure, "false")
    evidence = json.loads(result.stdout)
    assert evidence["diagnostics"] == evidence["stdout"] == ""
    assert evidence["secret"] not in evidence["partial"] + result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    assert "application-private-sentinel" not in result.stdout + result.stderr
    assert "later healthy record" in result.stderr
    assert evidence["records"] == (1 if failure == "shutdown" else 2)


def test_negative_controls_detect_version_and_handler_policy():
    with pytest.raises(AssertionError):
        _assert_locked_versions({"uvicorn": "0.0.0"})
    result = _fresh_process(SINK_PROBE, "uvicorn", "write", "true")
    evidence = json.loads(result.stdout)
    assert evidence["secret"] in evidence["diagnostics"]
    assert "Traceback" in evidence["diagnostics"]


def test_nested_cancellation_classification_never_formats_or_recurses():
    class PrivateError(RuntimeError):
        def __str__(self):
            raise AssertionError("exception was serialized")
        def __repr__(self):
            raise AssertionError("exception was serialized")
    grouped = BaseExceptionGroup("private group", [asyncio.CancelledError(), PrivateError()])
    ordinary = ExceptionGroup("private group", [PrivateError()])
    for _ in range(1200):
        grouped = BaseExceptionGroup("private group", [grouped])
        ordinary = ExceptionGroup("private group", [ordinary])
    assert cancellation_kind(grouped) == "cancelled_group"
    assert cancellation_kind(ordinary) is None


HTTP_SECRETS = {
    name: f"private-{name}-sentinel"
    for name in ("query", "body", "cookie", "authorization", "filename", "exception", "storage-key", "session", "path")
}


def _http_scope():
    return {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": f"/probe/{HTTP_SECRETS['path']}", "root_path": "",
        "query_string": f"token={HTTP_SECRETS['query']}".encode(),
        "headers": [
            (b"host", b"testserver"), (b"x-correlation-id", b"http-matrix-1"),
            (b"cookie", f"paprnav_session={HTTP_SECRETS['cookie']}".encode()),
            (b"authorization", HTTP_SECRETS["authorization"].encode()),
        ],
        "client": ("127.0.0.1", 1234), "server": ("127.0.0.1", 8000), "state": {},
    }


def _http_scenario(scenario):
    async def application(scope, receive, send):
        scope["route"] = SimpleNamespace(path="/probe/{subject_id}")
        scope["state"].update(
            actor_user_id="server-actor", organization_id="server-org", aircraft_id="server-aircraft",
        )
        if scenario == "before_start":
            raise RuntimeError(HTTP_SECRETS["exception"])
        if scenario == "disconnect_before":
            await receive()
        await send({"type": "http.response.start", "status": 403 if scenario == "http_error" else 200, "headers": []})
        if scenario == "disconnect_pending":
            await receive()
        if scenario == "before_body":
            raise RuntimeError(HTTP_SECRETS["exception"])
        if scenario == "cancelled":
            raise asyncio.CancelledError(HTTP_SECRETS["exception"])
        await send({"type": "http.response.body", "body": b"first", "more_body": True})
        if scenario == "disconnect_body":
            await receive()
        if scenario == "after_body":
            raise RuntimeError(HTTP_SECRETS["exception"])
        await send({"type": "http.response.body", "body": b"second", "more_body": True})
        await send({"type": "http.response.body", "body": b"", "more_body": False})
        if scenario == "after_complete":
            raise RuntimeError(HTTP_SECRETS["exception"])

    return PilotRequestBoundaryMiddleware(application, settings=get_settings())


def _assert_private_http_logs(caplog, *, expected_errors, context=True):
    records = [record for record in caplog.records if record.name in {"paprnav.unexpected_error", "uvicorn.error", "uvicorn.access"}]
    retained = repr([record.__dict__ for record in records]) + caplog.text
    assert all(secret not in retained for secret in HTTP_SECRETS.values())
    assert all(record.exc_info is None and record.stack_info is None for record in records)
    assert not any(record.name.startswith("uvicorn.") for record in records)
    errors = [json.loads(record.getMessage()) for record in records]
    assert len(errors) == expected_errors
    for error in errors:
        assert error["correlationId"] == "http-matrix-1"
        assert error["routeTemplate"] == "/probe/{subject_id}"
        if context:
            assert error["actorUserId"] == "server-actor"
            assert error["organizationId"] == "server-org"
            assert error["aircraftId"] == "server-aircraft"
    return errors


@pytest.mark.parametrize(
    "scenario,fail_at,after_effect,attempt_count,status,delivery_state",
    [
        ("success", None, False, 4, 200, None),
        ("http_error", None, False, 4, 403, None),
        ("before_start", None, False, 2, 500, "complete"),
        ("before_body", None, False, 2, 500, "complete"),
        ("after_body", None, False, 3, 200, "complete"),
        ("after_complete", None, False, 4, 200, "complete"),
        ("success", 1, False, 1, 200, "start_delivery_uncertain"),
        ("success", 1, True, 1, 200, "start_delivery_uncertain"),
        ("success", 2, False, 2, 200, "body_delivery_uncertain"),
        ("success", 2, True, 2, 200, "body_delivery_uncertain"),
        ("success", 3, False, 3, 200, "body_delivery_uncertain"),
        ("success", 3, True, 3, 200, "body_delivery_uncertain"),
        ("success", 4, False, 4, 200, "end_delivery_uncertain"),
        ("success", 4, True, 4, 200, "end_delivery_uncertain"),
        ("before_start", 1, False, 1, 500, "start_delivery_uncertain"),
        ("before_start", 1, True, 1, 500, "start_delivery_uncertain"),
        ("before_start", 2, False, 2, 500, "end_delivery_uncertain"),
        ("before_start", 2, True, 2, 500, "end_delivery_uncertain"),
        ("before_body", 2, False, 2, 500, "end_delivery_uncertain"),
        ("before_body", 2, True, 2, 500, "end_delivery_uncertain"),
        ("after_body", 3, True, 3, 200, "end_delivery_uncertain"),
        ("after_body", 3, False, 3, 200, "end_delivery_uncertain"),
        ("disconnect_before", None, False, 0, None, "disconnected"),
        ("disconnect_pending", None, False, 0, None, "disconnected"),
        ("disconnect_body", None, False, 2, 200, "disconnected"),
    ],
)
def test_http_delivery_lifecycle_matrix(
    scenario, fail_at, after_effect, attempt_count, status, delivery_state, caplog,
):
    caplog.set_level(logging.ERROR)
    attempts, delivered = [], []

    async def receive():
        if scenario.startswith("disconnect"):
            return {"type": "http.disconnect"}
        return {"type": "http.request", "body": HTTP_SECRETS["body"].encode(), "more_body": False}

    async def send(message):
        attempts.append(message)
        failing = len(attempts) == fail_at
        if not failing or after_effect:
            delivered.append(message)
        if failing:
            raise OSError(" ".join(HTTP_SECRETS.values()))

    asyncio.run(_http_scenario(scenario)(_http_scope(), receive, send))
    assert len(attempts) == attempt_count
    starts = [message for message in attempts if message["type"] == "http.response.start"]
    assert len(starts) == (status is not None)
    if starts:
        assert starts[0]["status"] == status
        assert (b"x-correlation-id", b"http-matrix-1") in starts[0]["headers"]
    assert len(delivered) == attempt_count - (fail_at is not None and not after_effect)
    errors = _assert_private_http_logs(caplog, expected_errors=int(delivery_state is not None))
    if errors:
        assert errors[0]["deliveryState"] == delivery_state
    assert get_correlation_id() is None


@pytest.fixture
def production_http_config(monkeypatch, caplog):
    """Use the shipped launcher configuration, substituting only the probe app."""
    import pilot_server
    # Restore logging configuration after exercising Config.configure_logging.
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        for attribute in ("handlers", "propagate", "level", "disabled"):
            monkeypatch.setattr(logger, attribute, getattr(logger, attribute))

    def configure(application):
        config = pilot_server.create_config()
        assert config.app == "main:app"
        assert config.access_log is False
        assert config.http == "app.core.http_protocol:PilotH11Protocol"
        assert config.log_level == "info"
        assert config.timeout_graceful_shutdown == 10
        config.app = application
        config.load()
        assert not logging.getLogger("uvicorn.access").hasHandlers()
        logging.getLogger("uvicorn.error").addHandler(caplog.handler)
        return config

    return configure


class ProbeTransport(asyncio.Transport):
    def __init__(self, *, fail_write=None, after_effect=False):
        self.writes = []
        self.attempts = 0
        self.close_count = 0
        self.fail_write = fail_write
        self.after_effect = after_effect
        self.on_write = lambda: None

    def get_extra_info(self, name, default=None):
        return ("127.0.0.1", 8000) if name in {"sockname", "peername"} else default

    def is_closing(self):
        return bool(self.close_count)

    def close(self):
        self.close_count += 1

    def write(self, data):
        self.attempts += 1
        failing = self.attempts == self.fail_write
        if not failing or self.after_effect:
            self.writes.append(data)
        if failing:
            raise OSError(" ".join(HTTP_SECRETS.values()))
        self.on_write()

    def pause_reading(self):
        pass

    def resume_reading(self):
        pass


def _request_bytes(correlation="http-matrix-1"):
    return (f"GET /probe/{HTTP_SECRETS['path']}?token={HTTP_SECRETS['query']} HTTP/1.1\r\n"
            f"Host: testserver\r\nX-Correlation-ID: {correlation}\r\n"
            f"Cookie: paprnav_session={HTTP_SECRETS['cookie']}\r\n"
            f"Authorization: {HTTP_SECRETS['authorization']}\r\n\r\n").encode()


def _protocol(configure, application, transport=None):
    contexts = []
    async def observed(scope, receive, send):
        try:
            await application(scope, receive, send)
        finally:
            if scope["type"] == "http":
                contexts.append(get_correlation_id())
    config = configure(observed)
    state = ServerState()
    protocol = config.http_protocol_class(config, state, {})
    transport = transport or ProbeTransport()
    protocol.connection_made(transport)
    return config, state, protocol, transport, contexts


async def _done_before_cleanup(tasks, transport):
    # asyncio.wait never cancels the subject to manufacture completion. Save
    # the pre-cleanup state in the assertion so a failure remains diagnosable.
    done, pending = await asyncio.wait(tasks, timeout=1)
    snapshot = {"pending": len(pending), "writes": transport.attempts,
                "closed": transport.is_closing(), "cancel_counts": [t.cancelling() for t in tasks]}
    assert not pending, snapshot
    for task in done:
        task.result()
    return snapshot


async def _cleanup(state, protocol):
    protocol._unset_keepalive_if_required()
    remaining = [task for task in state.tasks if not task.done()]
    for task in remaining:
        task.cancel()
    if remaining:
        await asyncio.gather(*remaining, return_exceptions=True)


def _cancellation(kind):
    plain = asyncio.CancelledError(HTTP_SECRETS["exception"])
    if kind == "plain":
        return plain
    pure = BaseExceptionGroup(HTTP_SECRETS["body"], [plain])
    if kind == "pure_group":
        return pure
    return BaseExceptionGroup(HTTP_SECRETS["cookie"], [RuntimeError(HTTP_SECRETS["storage-key"]), pure])


@pytest.mark.parametrize("kind", ["plain", "pure_group", "mixed_group"])
@pytest.mark.parametrize("place,expected_writes", [("before_start", 0), ("body", 2), ("recovery", 0), ("unrelated", 0)])
def test_single_cancellation_is_terminal(kind, place, expected_writes, production_http_config, caplog):
    caplog.set_level(logging.ERROR)
    async def run():
        suspended = asyncio.Event()
        async def application(scope, receive, send):
            if place in {"before_start", "unrelated"}:
                suspended.set()
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    raise _cancellation(kind)
            if place == "recovery":
                raise RuntimeError(HTTP_SECRETS["exception"])
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"first", "more_body": True})
            await send({"type": "http.response.body", "body": b"second"})
        boundary = PilotRequestBoundaryMiddleware(application, settings=get_settings())
        _, state, protocol, transport, contexts = _protocol(production_http_config, boundary)
        drain = protocol.flow.drain
        async def observed_drain():
            suspended.set()
            try:
                await drain()
            except asyncio.CancelledError:
                raise _cancellation(kind)
        protocol.flow.drain = observed_drain
        if place == "recovery":
            protocol.pause_writing()
        elif place == "body":
            transport.on_write = lambda: protocol.pause_writing() if transport.attempts == 2 else None
        protocol.data_received(_request_bytes())
        tasks = list(state.tasks)
        try:
            await asyncio.wait_for(suspended.wait(), timeout=1)
            assert not tasks[0].done()
            tasks[0].cancel()
            snapshot = await _done_before_cleanup(tasks, transport)
            assert snapshot["cancel_counts"] == [1]
            assert transport.attempts == expected_writes
            assert protocol.cycle.disconnected and not protocol.cycle.keep_alive
            assert transport.is_closing()
            assert contexts == [None]
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    records = [record for record in caplog.records if record.name in {"paprnav.unexpected_error", "uvicorn.error", "uvicorn.access"}]
    assert len(records) == 1 and records[0].name == "paprnav.unexpected_error"
    assert json.loads(records[0].getMessage())["failureKind"] == ("cancelled" if kind == "plain" else "cancelled_group")
    assert all(secret not in repr([r.__dict__ for r in records]) for secret in HTTP_SECRETS.values())
    assert records[0].exc_info is None and records[0].exc_text is None


@pytest.mark.parametrize("action,expected_writes,errors", [("resume", 5, 0), ("disconnect", 0, 1)])
def test_actual_paused_output(action, expected_writes, errors, production_http_config, caplog):
    caplog.set_level(logging.ERROR)
    async def run():
        _, state, protocol, transport, contexts = _protocol(production_http_config, _http_scenario("success"))
        protocol.pause_writing()
        entered = asyncio.Event()
        original = protocol.flow.drain
        async def drain():
            entered.set()
            await original()
        protocol.flow.drain = drain
        protocol.data_received(_request_bytes())
        tasks = list(state.tasks)
        try:
            await asyncio.wait_for(entered.wait(), timeout=1)
            assert not tasks[0].done() and transport.attempts == 0
            if action == "resume":
                protocol.resume_writing()
            else:
                protocol.connection_lost(None)
            await _done_before_cleanup(tasks, transport)
            assert transport.attempts == expected_writes and contexts == [None]
            if action == "resume":
                wire = b"".join(transport.writes)
                assert b"first" in wire and b"second" in wire and wire.endswith(b"0\r\n\r\n")
                assert not transport.is_closing()
            else:
                assert protocol.cycle.disconnected and transport.is_closing()
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    _assert_private_http_logs(caplog, expected_errors=errors)


def test_negative_controls_detect_access_logs_and_adapter_bypass(production_http_config, caplog):
    async def run():
        # Mutations affect this test process only. Both controls must visibly
        # fail the same privacy oracle used by the positive matrix.
        config = production_http_config(_http_scenario("success"))
        access = logging.getLogger("uvicorn.access")
        access.addHandler(caplog.handler)
        access.setLevel(logging.INFO)
        state = ServerState()
        protocol = config.http_protocol_class(config, state, {})
        transport = ProbeTransport()
        protocol.connection_made(transport)
        assert protocol.access_log
        protocol.data_received(_request_bytes())
        try:
            await _done_before_cleanup(list(state.tasks), transport)
            with pytest.raises(AssertionError):
                _assert_private_http_logs(caplog, expected_errors=0)
            assert any(HTTP_SECRETS["query"] in r.getMessage() for r in caplog.records if r.name == "uvicorn.access")
        finally:
            await _cleanup(state, protocol)
        caplog.clear()
        from uvicorn.protocols.http.h11_impl import H11Protocol
        config = production_http_config(_http_scenario("success"))
        state = ServerState()
        protocol = H11Protocol(config, state, {})
        transport = ProbeTransport()
        protocol.connection_made(transport)
        protocol.pause_writing()
        calls = []
        async def fail_first_drain():
            calls.append(None)
            if len(calls) == 1:
                raise OSError(HTTP_SECRETS["exception"])
        protocol.flow.drain = fail_first_drain
        protocol.data_received(_request_bytes())
        try:
            await _done_before_cleanup(list(state.tasks), transport)
            with pytest.raises(AssertionError):
                _assert_private_http_logs(caplog, expected_errors=1)
            assert b"Internal Server Error" in b"".join(transport.writes)
            assert len(calls) == 3  # initial failure plus stock fallback start/body
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())


def test_group_without_cancellation_keeps_sanitized_recovery(production_http_config, caplog):
    caplog.set_level(logging.ERROR)
    async def application(scope, receive, send):
        raise ExceptionGroup(HTTP_SECRETS["body"], [RuntimeError(HTTP_SECRETS["exception"])])
    async def run():
        _, state, protocol, transport, contexts = _protocol(
            production_http_config, PilotRequestBoundaryMiddleware(application, settings=get_settings()))
        protocol.data_received(_request_bytes())
        try:
            await _done_before_cleanup(list(state.tasks), transport)
            assert b"HTTP/1.1 500" in b"".join(transport.writes)
            assert not transport.is_closing() and contexts == [None]
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    records = [r for r in caplog.records if r.name == "paprnav.unexpected_error"]
    assert len(records) == 1 and "failureKind" not in json.loads(records[0].getMessage())
    assert all(secret not in repr([r.__dict__ for r in caplog.records]) for secret in HTTP_SECRETS.values())


def test_sequential_keepalive_context_isolation(production_http_config, caplog):
    async def run():
        _, state, protocol, transport, contexts = _protocol(production_http_config, _http_scenario("success"))
        try:
            for correlation in ("sequential-A", "sequential-B"):
                protocol.data_received(_request_bytes(correlation))
                await _done_before_cleanup(list(state.tasks), transport)
                assert protocol.cycle.response_complete and not transport.is_closing()
            wire = b"".join(transport.writes)
            assert wire.count(b"HTTP/1.1 200") == 2
            assert wire.count(b"x-correlation-id: sequential-A") == 1
            assert wire.count(b"x-correlation-id: sequential-B") == 1
            assert contexts == [None, None]
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    _assert_private_http_logs(caplog, expected_errors=0)


def test_disconnect_unrelated_await_requires_real_shutdown_owner(production_http_config, caplog):
    async def run():
        entered, cancelled = asyncio.Event(), asyncio.Event()
        async def application(scope, receive, send):
            if scope["type"] == "lifespan":
                while True:
                    message = await receive()
                    await send({"type": message["type"] + ".complete"})
                    if message["type"] == "lifespan.shutdown":
                        return
            entered.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise
        config, state, protocol, transport, contexts = _protocol(
            production_http_config, PilotRequestBoundaryMiddleware(application, settings=get_settings()))
        protocol.data_received(_request_bytes())
        tasks = list(state.tasks)
        try:
            await asyncio.wait_for(entered.wait(), timeout=1)
            protocol.connection_lost(None)
            done, pending = await asyncio.wait(tasks, timeout=0.03)
            # This observation precedes shutdown and every cleanup cancellation.
            assert not done and pending == set(tasks)
            assert not cancelled.is_set() and tasks[0].cancelling() == 0
            config.timeout_graceful_shutdown = 0.01
            server = Server(config)
            server.server_state = state
            server.servers = []
            server.lifespan = config.lifespan_class(config)
            await asyncio.wait_for(server.lifespan.startup(), timeout=1)
            shutdown = asyncio.create_task(server.shutdown())
            await asyncio.wait_for(cancelled.wait(), timeout=1)
            snapshot = await _done_before_cleanup(tasks, transport)
            assert snapshot["cancel_counts"] == [1]
            assert contexts == [None] and transport.attempts == 0
            await asyncio.wait_for(shutdown, timeout=1)
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    records = [r for r in caplog.records if r.name in {"uvicorn.error", "paprnav.unexpected_error"}]
    assert any("timeout graceful shutdown exceeded" in r.getMessage() for r in records)
    assert all(r.exc_info is None for r in records)
    assert all(secret not in repr([r.__dict__ for r in records]) for secret in HTTP_SECRETS.values())


@pytest.mark.parametrize("kind", ["plain", "pure_group", "mixed_group"])
@pytest.mark.parametrize("ownership", ["completed_current", "completed_successor", "noncurrent_incomplete", "different_transport"])
def test_cancellation_cannot_abort_successor(kind, ownership, production_http_config, caplog):
    caplog.set_level(logging.ERROR)
    async def run():
        old_waiting, successor_waiting, release_successor = asyncio.Event(), asyncio.Event(), asyncio.Event()
        correlations = []
        async def application(scope, receive, send):
            correlation = get_correlation_id()
            correlations.append(correlation)
            if correlation == "successor-B":
                successor_waiting.set()
                await release_successor.wait()
                await send({"type": "http.response.start", "status": 201, "headers": []})
                await send({"type": "http.response.body", "body": b"successor"})
                return
            if ownership.startswith("completed"):
                await send({"type": "http.response.start", "status": 200, "headers": []})
                await send({"type": "http.response.body", "body": b"old"})
            old_waiting.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                raise _cancellation(kind)
        _, state, protocol, transport, contexts = _protocol(
            production_http_config, PilotRequestBoundaryMiddleware(application, settings=get_settings()))
        protocol.data_received(_request_bytes("old-A"))
        old_task = next(iter(state.tasks))
        old_cycle = protocol.cycle
        try:
            if ownership == "completed_successor":
                # Pipeline B before A completes so on_response synchronously
                # transfers the current cycle before A's final send returns.
                protocol.data_received(_request_bytes("successor-B"))
                await asyncio.wait_for(successor_waiting.wait(), timeout=1)
                assert protocol.cycle is not old_cycle
            await asyncio.wait_for(old_waiting.wait(), timeout=1)
            if ownership == "noncurrent_incomplete":
                # Explicitly exercise the identity guard even when the old
                # wrapper has never observed a successful final send.
                protocol.cycle = SimpleNamespace(disconnected=False, keep_alive=True, response_complete=False)
            elif ownership == "different_transport":
                protocol.transport = ProbeTransport()
            current = protocol.cycle
            before = (current.disconnected, current.keep_alive, transport.attempts)
            old_task.cancel()
            await _done_before_cleanup([old_task], transport)
            assert not transport.is_closing()
            assert not protocol.transport.is_closing()
            assert transport.attempts == before[2]
            if ownership != "different_transport":
                assert (current.disconnected, current.keep_alive) == before[:2]
            if ownership == "completed_successor":
                assert not current.response_complete
                release_successor.set()
                await _done_before_cleanup(list(state.tasks), transport)
                assert current.response_complete
                wire = b"".join(transport.writes)
                assert wire.count(b"HTTP/1.1 ") == 2 and b"successor" in wire
                assert correlations == ["old-A", "successor-B"]
                assert contexts == [None, None]
            else:
                assert contexts == [None]
            if ownership in {"noncurrent_incomplete", "different_transport"}:
                assert old_cycle.disconnected and not old_cycle.keep_alive
            else:
                assert not old_cycle.disconnected and old_cycle.keep_alive
        finally:
            await _cleanup(state, protocol)
    asyncio.run(run())
    records = [r for r in caplog.records if r.name in {"paprnav.unexpected_error", "uvicorn.error", "uvicorn.access"}]
    assert len(records) == 1 and records[0].name == "paprnav.unexpected_error"
    assert json.loads(records[0].getMessage())["correlationId"] == "old-A"
    assert all(secret not in repr([r.__dict__ for r in records]) for secret in HTTP_SECRETS.values())


@pytest.mark.parametrize(
    "scenario,fail_write,drain_failure,status",
    [
        ("success", None, False, 200), ("http_error", None, False, 403),
        ("before_start", None, False, 500), ("before_body", None, False, 500),
        ("after_body", None, False, 200), ("after_complete", None, False, 200),
        ("success", None, True, None), ("success", 1, False, None),
        ("success", 2, False, 200), ("success", 3, False, 200),
        ("success", 5, False, 200), ("before_start", 1, False, None),
        ("before_body", 2, False, 500), ("after_body", 4, False, 200),
        ("disconnect_before", None, False, None),
        ("disconnect_pending", None, False, None),
        ("disconnect_body", None, False, 200),
    ],
)
@pytest.mark.parametrize("after_effect", [False, True])
def test_effective_uvicorn_http_logging(
    scenario, fail_write, drain_failure, status, after_effect, production_http_config, caplog,
):
    caplog.set_level(logging.ERROR)

    class Transport(asyncio.Transport):
        def __init__(self):
            self.writes = []
            self.attempts = 0
            self.closed = False
            self.on_disconnect = lambda: None

        def get_extra_info(self, name, default=None):
            return ("127.0.0.1", 8000) if name in {"sockname", "peername"} else default

        def is_closing(self):
            return self.closed

        def close(self):
            self.closed = True

        def write(self, data):
            self.attempts += 1
            failing = self.attempts == fail_write
            if not failing or after_effect:
                self.writes.append(data)
            if failing:
                raise OSError(" ".join(HTTP_SECRETS.values()))
            if scenario == "disconnect_body" and self.attempts == 2:
                self.close()
                self.on_disconnect()

    async def run():
        config = production_http_config(_http_scenario(scenario))
        server = ServerState()
        protocol = config.http_protocol_class(config, server, {})
        assert protocol.access_log is False
        # Capture any erroneously emitted access record without changing the
        # protocol's effective decision, made from the real configured logger.
        logging.getLogger("uvicorn.access").addHandler(caplog.handler)
        transport = Transport()
        protocol.connection_made(transport)
        transport.on_disconnect = lambda: protocol.connection_lost(None)
        if drain_failure:
            protocol.flow.write_paused = True

            async def fail_drain():
                raise OSError(" ".join(HTTP_SECRETS.values()))

            protocol.flow.drain = fail_drain
        scope = _http_scope()
        target = scope["path"].encode() + b"?" + scope["query_string"]
        request = b"GET " + target + b" HTTP/1.1\r\n"
        request += b"\r\n".join(name + b": " + value for name, value in scope["headers"])
        body = HTTP_SECRETS["body"].encode()
        request += b"\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
        protocol.data_received(request)
        if scenario in {"disconnect_before", "disconnect_pending"}:
            transport.close()
            transport.on_disconnect()
        try:
            await _done_before_cleanup(list(server.tasks), transport)
            assert get_correlation_id() is None
            return transport, protocol.cycle
        finally:
            await _cleanup(server, protocol)

    transport, cycle = asyncio.run(run())
    wire = b"".join(transport.writes)
    if fail_write == 1 and after_effect:
        status = 500 if scenario in {"before_start", "before_body"} else 200
    if status is None:
        assert b"HTTP/1.1" not in wire
    else:
        assert wire.count(b"HTTP/1.1 ") == 1
        assert wire.startswith(f"HTTP/1.1 {status}".encode())
        assert b"x-correlation-id: http-matrix-1" in wire
    if fail_write or drain_failure:
        assert cycle.disconnected and transport.closed
        assert transport.attempts == (fail_write or 0)
        if scenario == "success" and fail_write == 5:
            # The pinned server has already set response_complete, but the
            # final write is still uncertain and must close the current cycle.
            assert cycle.response_complete
    elif scenario.startswith("disconnect"):
        assert cycle.disconnected and transport.closed
        assert transport.attempts == (2 if scenario == "disconnect_body" else 0)
    else:
        assert cycle.response_complete
    _assert_private_http_logs(caplog, expected_errors=int(scenario not in {"success", "http_error"} or fail_write is not None or drain_failure))


@pytest.mark.parametrize("scope_type", ["lifespan", "websocket"])
@pytest.mark.parametrize("kind", ["ordinary", "plain", "pure_group", "mixed_group"])
def test_http_boundary_preserves_non_http_behavior(scope_type, kind, production_http_config):
    observed = []
    error = RuntimeError("non-http behavior unchanged") if kind == "ordinary" else _cancellation(kind)

    async def application(scope, receive, send):
        observed.append(scope["type"])
        assert get_correlation_id() is None
        raise error

    async def run():
        boundary = PilotRequestBoundaryMiddleware(application, settings=get_settings())
        config = production_http_config(boundary)
        protocol = config.http_protocol_class(config, ServerState(), {})
        await protocol.app({"type": scope_type}, None, None)
    with pytest.raises(BaseException) as caught:
        asyncio.run(run())
    assert caught.value is error
    assert observed == [scope_type]


@pytest.mark.parametrize("download_kind", ["upload", "page_image"])
def test_streaming_download_failures_are_sanitized_before_and_after_headers(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    caplog,
    download_kind,
) -> None:
    aircraft = demo_data["aircraft"]
    owner = demo_data["owner_user"]
    upload = Upload(
        aircraft_id=aircraft.id,
        uploaded_by_user_id=owner.id,
        original_filename=f"{HTTP_SECRETS['filename']}.pdf",
        content_type="application/pdf",
        file_size_bytes=7,
        storage_backend="s3",
        storage_key=f"package-d/{HTTP_SECRETS['storage-key']}.pdf",
        sha256="f" * 64,
        status="stored",
        pilot_consent_accepted=True,
    )
    db_session.add(upload)
    db_session.flush()
    job = IngestionJob(
        upload_id=upload.id, aircraft_id=aircraft.id, created_by_user_id=owner.id,
    )
    db_session.add(job)
    db_session.flush()
    page = IngestionPage(
        ingestion_job_id=job.id, upload_id=upload.id, source_page_number=1,
        current_page_order=1, page_label="Page 1", image_storage_backend="s3",
        image_storage_key=f"package-d/{HTTP_SECRETS['storage-key']}.png",
    )
    db_session.add(page)
    db_session.commit()
    url = (
        f"/api/v1/uploads/{upload.id}/download" if download_kind == "upload"
        else f"/api/v1/ingestion-jobs/{job.id}/pages/{page.id}/image"
    )
    route_template = (
        "/api/v1/uploads/{upload_id}/download" if download_kind == "upload"
        else "/api/v1/ingestion-jobs/{job_id}/pages/{page_id}/image"
    )

    observed_correlations: list[str | None] = []

    class FailingBody:
        def __init__(self, *, yield_first: bool, fail: bool) -> None:
            self.yield_first = yield_first
            self.fail = fail

        def iter_chunks(self):
            observed_correlations.append(get_correlation_id())
            if self.yield_first:
                yield b"partial"
            if self.fail:
                raise RuntimeError(" ".join(HTTP_SECRETS.values()))

    class FakeS3Client:
        def __init__(self) -> None:
            self.yield_first = False
            self.fail = True

        def get_object(self, **_kwargs):
            return {"Body": FailingBody(yield_first=self.yield_first, fail=self.fail)}

    fake_s3 = FakeS3Client()
    monkeypatch.setenv("PAPRNAV_S3_UPLOAD_BUCKET", "package-d-test-bucket")
    monkeypatch.setattr(
        f"app.api.routes.{'uploads' if download_kind == 'upload' else 'ingestion'}.get_s3_client",
        lambda _region: fake_s3,
    )
    get_settings.cache_clear()
    login(client, "owner.test@paprnav.local")
    caplog.set_level(logging.ERROR)

    before_headers = client.get(
        url + f"?token={HTTP_SECRETS['query']}",
        headers={"X-Correlation-ID": "stream-preheader"},
    )
    assert before_headers.status_code == 500
    assert before_headers.json() == {
        "detail": "Unexpected server error",
        "correlationId": "stream-preheader",
    }
    assert before_headers.headers["X-Correlation-ID"] == "stream-preheader"

    fake_s3.yield_first = True
    after_headers = client.get(
        url + f"?token={HTTP_SECRETS['query']}",
        headers={"X-Correlation-ID": "stream-postheader"},
    )
    assert after_headers.status_code == 200
    assert after_headers.content == b"partial"
    assert after_headers.headers["X-Correlation-ID"] == "stream-postheader"
    fake_s3.fail = False
    successful = client.get(url, headers={"X-Correlation-ID": "stream-success"})
    assert successful.status_code == 200
    assert successful.content == b"partial"
    assert observed_correlations == ["stream-preheader", "stream-postheader", "stream-success"]

    records = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "paprnav.unexpected_error"
    ]
    assert [record["correlationId"] for record in records] == [
        "stream-preheader",
        "stream-postheader",
    ]
    for record in records:
        assert record["routeTemplate"] == route_template
        assert record["actorUserId"] == owner.id
        assert record["organizationId"] == aircraft.owner_organization_id
        assert record["aircraftId"] == aircraft.id
        assert record["status"] == 500
    retained = caplog.text + repr([record.__dict__ for record in caplog.records])
    assert all(secret not in retained for secret in HTTP_SECRETS.values())
    assert all(record.exc_info is None for record in caplog.records)
    assert "traceback" not in caplog.text.lower()


def test_correlation_generic_error_db_outage(
    client: TestClient,
    caplog,
) -> None:
    valid = client.get("/health", headers={"X-Correlation-ID": "pilot.safe-123"})
    assert valid.status_code == 200
    assert valid.headers["X-Correlation-ID"] == "pilot.safe-123"
    invalid = client.get("/health", headers={"X-Correlation-ID": "bad token/value"})
    assert invalid.status_code == 200
    assert invalid.headers["X-Correlation-ID"] != "bad token/value"
    assert len(invalid.headers["X-Correlation-ID"]) == 32

    def unavailable_database():
        raise RuntimeError("postgres://user:password@db secret exception text")

    client.app.dependency_overrides[get_db] = unavailable_database
    caplog.set_level(logging.ERROR, logger="paprnav.unexpected_error")
    response = client.get(
        "/api/v1/admin/pilot-summary?token=query-secret",
        headers={
            "X-Correlation-ID": "db-outage-1",
            "Cookie": "paprnav_session=cookie-secret",
            "Authorization": "Bearer header-secret",
        },
    )
    client.app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 500
    assert response.json() == {
        "detail": "Unexpected server error",
        "correlationId": "db-outage-1",
    }
    assert response.headers["X-Correlation-ID"] == "db-outage-1"
    log_payload = json.loads(caplog.records[-1].message)
    assert log_payload == {
        "correlationId": "db-outage-1",
        "event": "unexpected_request_error",
        "method": "GET",
        "release": "0.1.0",
        "routeTemplate": "/api/v1/admin/pilot-summary",
        "status": 500,
        "failureState": "not_started",
        "deliveryState": "complete",
        "responseStatus": 500,
    }
    lowered_logs = caplog.text.lower()
    for forbidden in (
        "query-secret",
        "cookie-secret",
        "header-secret",
        "password",
        "exception text",
    ):
        assert forbidden not in lowered_logs
