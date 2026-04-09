"""Command-line entrypoint for local and container execution."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

from python_framework import __version__
from python_framework.config import Settings
from python_framework.examples.prompt_example import main as prompt_example_main
from python_framework.examples.run_all import main as run_all_examples_main
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

    pex = sub.add_parser(
        "prompt-example",
        help="Extract contact fields from sample (or file) email via OpenAI; prints JSON.",
    )
    pex.add_argument(
        "--email-file",
        type=Path,
        default=None,
        help="Optional UTF-8 file with email body (default: built-in sample).",
    )

    sub.add_parser(
        "run-examples",
        help="Run all registered LLM / prompt demos in order (requires OPENAI_API_KEY).",
    )

    st = sub.add_parser(
        "structured-tutorial",
        help="Progressive structured-outputs tutorial (many API calls; needs OPENAI_API_KEY).",
    )
    st.add_argument(
        "--only",
        dest="structured_only",
        type=str,
        default="all",
        metavar="SECTIONS",
        help='Comma-separated section numbers 1–12, or "all" (default: all).',
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
    if args.command == "prompt-example":
        pe_args: list[str] = []
        if args.email_file is not None:
            pe_args.extend(["--email-file", str(args.email_file)])
        return prompt_example_main(pe_args)
    if args.command == "run-examples":
        return run_all_examples_main([])
    if args.command == "structured-tutorial":
        from python_framework.examples.structured_outputs_tutorial.tutorial import run_tutorial

        o = getattr(args, "structured_only", "all")
        return run_tutorial([] if str(o).strip().lower() == "all" else ["--only", str(o)])

    raise AssertionError(f"unhandled command: {args.command!r}")  # pragma: no cover
