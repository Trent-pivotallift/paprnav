#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stream Claude JSON events and preserve reviewer artifacts."
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--partial", required=True, type=Path)
    return parser.parse_args()


def progress(message: str) -> None:
    print(f"[claude-review] {message}", file=sys.stderr, flush=True)


def main() -> int:
    args = parse_args()
    for path in (args.output, args.events, args.partial):
        path.parent.mkdir(parents=True, exist_ok=True)

    result_seen = False
    result_error = False
    args.partial.write_text("", encoding="utf-8")

    with args.events.open("w", encoding="utf-8") as events:
        for raw_line in sys.stdin:
            events.write(raw_line)
            events.flush()
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                progress("received non-JSON diagnostic output")
                print(raw_line, file=sys.stderr, end="", flush=True)
                continue

            event_type = event.get("type")
            if event_type == "system":
                subtype = event.get("subtype")
                if subtype == "init":
                    progress(
                        "started "
                        f"model={event.get('model')} "
                        f"session={event.get('session_id')}"
                    )
                elif subtype == "status":
                    progress(f"status={event.get('status')}")
                continue

            if event_type == "stream_event":
                stream_event = event.get("event") or {}
                stream_type = stream_event.get("type")
                if stream_type == "content_block_start":
                    content_block = stream_event.get("content_block") or {}
                    if content_block.get("type") == "tool_use":
                        progress(f"tool={content_block.get('name')}")
                elif stream_type == "content_block_delta":
                    delta = stream_event.get("delta") or {}
                    if delta.get("type") == "text_delta":
                        text = str(delta.get("text") or "")
                        with args.partial.open("a", encoding="utf-8") as partial:
                            partial.write(text)
                            partial.flush()
                        print(text, end="", flush=True)
                continue

            if event_type == "result":
                result_seen = True
                result_error = bool(event.get("is_error"))
                final_text = event.get("result")
                if isinstance(final_text, str):
                    args.output.write_text(final_text, encoding="utf-8")
                print(flush=True)
                progress(
                    "finished "
                    f"reason={event.get('terminal_reason')} "
                    f"duration_ms={event.get('duration_ms')} "
                    f"cost_usd={event.get('total_cost_usd')}"
                )

    if not result_seen:
        progress(
            "ended without a result event; partial text and diagnostics were preserved"
        )
        return 2
    return 1 if result_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
