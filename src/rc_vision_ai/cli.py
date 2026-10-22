"""Command-line interface for the starter runtime."""

from __future__ import annotations

import argparse
import json

from . import __version__
from .monitor import collect_telemetry
from .scheduler import SequentialScheduler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rc-vision-ai",
        description="RC Vision AI — local-first research runtime (starter foundation).",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status", help="show project/runtime status")
    sub.add_parser("monitor", help="show best-effort local resource telemetry")
    sub.add_parser("scheduler-demo", help="run a tiny sequential scheduler self-check")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command or "status"

    if command == "status":
        print(f"RC Vision AI v{__version__}")
        print("Stage: runtime foundation")
        print("Image generation: not implemented yet")
        print("Remote AI APIs: not used")
        print("External model dependencies: none")
        print("Network access by this CLI: none")
        return 0

    if command == "monitor":
        print(json.dumps(collect_telemetry(), indent=2))
        return 0

    if command == "scheduler-demo":
        scheduler = SequentialScheduler()
        scheduler.submit("foundation-check", lambda: None)
        scheduler.submit("second-check", lambda: None)
        for task in scheduler.run_all():
            print(f"{task.name}: {task.state.value}")
        return 0

    return 2
