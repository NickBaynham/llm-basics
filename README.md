# python-framework

A minimal, production-oriented Python application skeleton using [**PDM**](https://pdm-project.org) for environments and packaging, [**Ruff**](https://docs.astral.sh/ruff/) for linting and formatting, [**mypy**](https://www.mypy-lang.org/) for static typing, [**pytest**](https://pytest.org/) with coverage gates for tests, [**Docker**](https://docs.docker.com/build/) for portable execution, and a **GitHub Actions** workflow for continuous integration (lint, test, package build, and image build).

## Prerequisites

- Python 3.11 or newer
- [PDM](https://pdm-project.org/latest/#installation) 2.x (`pipx install pdm` is a common choice)
- Docker Desktop or compatible engine (optional, for container workflows)

## Quick start

```bash
make setup          # optional .env + pdm install -G dev
make lint           # ruff + mypy
make test           # pytest with coverage
make run            # hello subcommand via PDM
```

### Configure environment variables

```bash
cp .env.example .env   # or: make configure
```

| Variable | Default | Meaning |
| --- | --- | --- |
| `PYTHON_FRAMEWORK_APP_NAME` | `python-framework` | Logical service name (`config` command). |
| `PYTHON_FRAMEWORK_DEBUG` | `false` | `true`/`1`/`yes`/`on` enable debug flag in settings. |

## Project layout

| Path | Purpose |
| --- | --- |
| `src/python_framework/` | Application package (`config`, `cli`). |
| `tests/` | Pytest suite. |
| `pyproject.toml` | Project metadata, tool configuration, dependency groups. |
| `pdm.lock` | Resolved dependencies (commit this for reproducible CI and Docker). |
| `Makefile` | Stable developer entrypoints. |
| `Dockerfile` | Multi-stage image: PDM prod install, non-root runtime. |
| `.github/workflows/ci.yml` | Lint, test (matrix), `pdm build`, Docker image build + smoke test. |

## Make targets

| Target | Description |
| --- | --- |
| `make help` | List targets and descriptions. |
| `make setup` | `configure` + `install`. |
| `make configure` | Create `.env` from `.env.example` if missing. |
| `make lock` | Regenerate `pdm.lock` after dependency edits. |
| `make install` | `pdm install -G dev` |
| `make build` | `pdm build` (sdist + wheel). |
| `make lint` | `ruff check`, `ruff format --check`, `mypy src`. |
| `make format` | `ruff format` + `ruff check --fix`. |
| `make test` | `pytest` with coverage threshold. |
| `make run` | `pdm run python-framework hello` |
| `make run-ping` | `pdm run python-framework ping` |
| `make docker-build` | `docker build -t python-framework:local .` |
| `make docker-run` | `docker run --rm python-framework:local` |
| `make docker-run-ping` | `docker run --rm python-framework:local ping` |
| `make clean` | Remove `dist/`, caches, coverage artifacts. |

Override the image tag with `make docker-build IMAGE=myapp:dev`.

## PDM commands (without Make)

```bash
pdm install -G dev          # sync dev + runtime deps
pdm run pytest              # tests
pdm run ruff check src tests
pdm run mypy src
pdm run python-framework --help
pdm build
```

**Why `[tool.pdm.scripts]` defines `python-framework`:** PDM resolves any *bare* command name that starts with `python` to the project interpreter (so a console script literally named `python-framework` was previously executed as `python hello`). The PDM script runs `python -m python_framework` instead. The installed console script from `[project.scripts]` is unchanged and works normally in Docker or when you call `.venv/bin/python-framework` directly.

## CLI

The console script `python-framework` exposes:

- `hello [--name TEXT]` — greeting (default name `world`).
- `ping` — prints `pong` (useful for container probes).
- `config [--json]` — show effective settings from the environment.

Examples:

```bash
pdm run python-framework hello --name Alice
pdm run python-framework config --json
```

## Docker

Build and run locally:

```bash
make docker-build
make docker-run
```

The image runs as a non-root user, uses a frozen lockfile for production dependencies, and sets `ENTRYPOINT` to `python-framework` with default `CMD` of `hello`.

Pass environment variables:

```bash
docker run --rm -e PYTHON_FRAMEWORK_DEBUG=true python-framework:local config
```

## Continuous integration

On each push and pull request to `main` or `master`, CI:

1. Installs dependencies with `pdm install -G dev --frozen-lockfile`.
2. Runs Ruff (check + format check) and mypy on `src`.
3. Runs pytest.
4. Builds the Python package with `pdm build` and uploads artifacts from Python 3.12.
5. Builds the Docker image (without publishing) and smoke-tests `hello` and `ping`.

Adjust branch filters in `.github/workflows/ci.yml` for your default branch name.

## License

See [LICENSE](./LICENSE).
