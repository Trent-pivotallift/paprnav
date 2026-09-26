"""The production API entry point; logging policy precedes all server imports."""

import logging

# StreamHandler/lastResort/shutdown failures must not print their exception,
# traceback or record arguments. Failed evidence can be lost; never retry it in
# another sink. Keep this policy for the entire process, including shutdown.
logging.raiseExceptions = False


def create_config():
    import uvicorn

    return uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        http="app.core.http_protocol:PilotH11Protocol",
        access_log=False,
        log_level="info",
        timeout_graceful_shutdown=10,
    )


def main():
    import sys

    # The image has one reviewed configuration, not a second CLI for overrides.
    if len(sys.argv) != 1:
        raise SystemExit("The pilot API launcher accepts no arguments")
    config = create_config()
    import uvicorn

    uvicorn.Server(config).run()


if __name__ == "__main__":
    main()
