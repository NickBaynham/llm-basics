"""Run every registered LLM / prompt-engineering example in sequence."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from python_framework.examples import prompt_example

ExampleMain = Callable[[list[str] | None], int]


def registered_examples() -> Sequence[tuple[str, ExampleMain]]:
    """Human-readable title and ``main(argv) -> int`` entrypoint per example."""
    return (("Contact extraction (structured email → JSON)", prompt_example.main),)


def main(argv: list[str] | None = None) -> int:
    """
    Execute all examples in order. Stops at the first non-zero exit status.

    ``argv`` is reserved for future flags (e.g. filtering examples).
    """
    _ = argv
    for title, example_main in registered_examples():
        print(f"\n=== {title} ===\n", flush=True)
        code = example_main([])
        if code != 0:
            return code
    return 0
