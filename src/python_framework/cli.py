"""Command-line entrypoint for local and container execution."""

from __future__ import annotations

import argparse
import json
import logging

from dotenv import load_dotenv

from python_framework import __version__
from python_framework.config import Settings
from python_framework.logging_config import configure_logging


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
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level for python_framework loggers.",
    )
    parser.add_argument(
        "--log-json",
        action="store_true",
        help="Emit log records as JSON lines (useful in containers).",
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
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level, json_format=args.log_json)

    log = logging.getLogger(__name__)

    if args.command == "hello":
        name = args.name or "world"
        log.info("hello command", extra={"greeting_name": name})
        print(f"Hello, {name}!")
        return 0
    if args.command == "ping":
        log.info("ping")
        print("pong")
        return 0
    if args.command == "config":
        settings = Settings()
        log.debug("config dump", extra={"app_name": settings.app_name, "debug": settings.debug})
        if args.json:
            payload = {"app_name": settings.app_name, "debug": settings.debug}
            print(json.dumps(payload, sort_keys=True))
        else:
            print(f"app_name={settings.app_name}")
            print(f"debug={settings.debug}")
        return 0

    raise AssertionError(f"unhandled command: {args.command!r}")  # pragma: no cover
