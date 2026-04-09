"""Allow ``python -m python_framework`` for local and CI invocation."""

from python_framework.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
