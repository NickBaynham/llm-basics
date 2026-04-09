"""Command-line entrypoint for local and container execution."""

from __future__ import annotations

import argparse

from python_framework import __version__
from python_framework.config import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python-framework",
        description="Python framework CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    hello = sub.add_parser("hello", help="Print a greeting.")
    hello.add_argument(
        "--name",
        default=None,
        help="Optional name to include in the greeting.",
    )

    sub.add_parser("ping", help="Health-style check; prints pong.")

    config = sub.add_parser("config", help="Show effective settings from the environment.")
    config.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable lines.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "hello":
        name = args.name or "world"
        print(f"Hello, {name}!")
        return 0
    if args.command == "ping":
        print("pong")
        return 0
    if args.command == "config":
        settings = Settings.from_environ()
        if args.json:
            import json

            payload = {"app_name": settings.app_name, "debug": settings.debug}
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"app_name={settings.app_name}")
            print(f"debug={settings.debug}")
        return 0

    raise AssertionError(f"unhandled command: {args.command!r}")  # pragma: no cover
