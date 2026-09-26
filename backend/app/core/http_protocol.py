"""Production HTTP transport boundary for the pinned Uvicorn h11 protocol."""

from asyncio import CancelledError

from starlette.types import Message, Receive, Scope, Send
from uvicorn.protocols.http.h11_impl import H11Protocol

from app.core.request_context import reset_correlation_id, set_correlation_id


def cancellation_kind(error: BaseException) -> str | None:
    """Classify by types only, including mixed nested cancellation groups."""
    if isinstance(error, CancelledError):
        return "cancelled"
    pending = [error]
    while pending:
        current = pending.pop()
        if isinstance(current, CancelledError):
            return "cancelled_group"
        if isinstance(current, BaseExceptionGroup):
            pending.extend(current.exceptions)
    return None


class HTTPTransportStopped(Exception):
    """An observed disconnect makes this request's delivery terminal."""


class PilotH11Protocol(H11Protocol):
    """Make an uncertain send terminal before Uvicorn considers a fallback 500."""

    def on_response_complete(self) -> None:
        # Uvicorn can spawn a pipelined successor here, inside the old task's
        # final send. Give the new task a neutral correlation context while
        # retaining the old task's own context for its remaining cleanup.
        token = set_correlation_id(None)
        try:
            super().on_response_complete()
        finally:
            reset_correlation_id(token)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        application = self.app

        async def transport_boundary(scope: Scope, receive: Receive, send: Send) -> None:
            # Capture this request's cycle before a keep-alive request can
            # replace self.cycle. WebSocket upgrades use their own protocol.
            if scope["type"] != "http":
                await application(scope, receive, send)
                return
            cycle = self.cycle
            transport = self.transport
            final_send_returned = False

            def abort_owned_cycle() -> None:
                # Successful completion transfers connection ownership even
                # while this application's task continues unwinding. The
                # server's response_complete flag precedes its final write,
                # so it cannot stand in for successful final-send return.
                if final_send_returned:
                    return
                cycle.disconnected = True
                cycle.keep_alive = False
                # No await may intervene between this check and close. An old
                # task must never close a successor's shared transport.
                if self.cycle is cycle and self.transport is transport:
                    try:
                        transport.close()
                    except BaseException:
                        pass

            async def send_once(message: Message) -> None:
                nonlocal final_send_returned
                try:
                    if cycle.disconnected:
                        raise HTTPTransportStopped()
                    await send(message)
                    if cycle.disconnected:
                        raise HTTPTransportStopped()
                    if message["type"] == "http.response.body" and not message.get("more_body", False):
                        final_send_returned = True
                except BaseException:
                    # In particular, flow.drain() can fail before Uvicorn sets
                    # response_started. Returning to run_asgi with disconnected
                    # false would authorize its own second response attempt.
                    abort_owned_cycle()
                    raise

            try:
                await application(scope, receive, send_once)
            except BaseException as error:
                if cancellation_kind(error) is None:
                    raise
                # Cancellation is terminal, including before any send or at an
                # unrelated application await. Never expose it to run_asgi's
                # traceback/fallback response path and never attempt recovery.
                abort_owned_cycle()

        self.app = transport_boundary
