# python-framework

A production-oriented Python application skeleton using [**PDM**](https://pdm-project.org), [**Ruff**](https://docs.astral.sh/ruff/), [**mypy**](https://www.mypy-lang.org/) (with the **Pydantic** plugin), [**pytest**](https://pytest.org/) with coverage gates, [**pre-commit**](https://pre-commit.com/), [**Docker**](https://docs.docker.com/build/) / [**Compose**](https://docs.docker.com/compose/), a [**Dev Container**](https://containers.dev/), and **GitHub Actions** (lint, security, tests, SBOM, multi-arch image build).

Runtime stack: **Pydantic Settings**, **python-dotenv**, and **Rich** logging (optional **JSON** log lines for containers).

## Prerequisites

- Python 3.11+
- [PDM](https://pdm-project.org/latest/#installation) 2.x
- Docker / Docker Compose (optional)
- [pre-commit](https://pre-commit.com/) (installed into the project env via dev dependencies)

## Quick start

```bash
make setup          # .env stub, pdm install -G dev, pre-commit install
make lint           # ruff + mypy (src + tests) + bandit
make test
make run            # hello via PDM script
```

## Configuration

Copy env defaults (optional):

```bash
cp .env.example .env   # or: make configure
```

At CLI startup, `load_dotenv()` runs so a project `.env` is picked up before **Settings** is instantiated.

| Variable | Default | Meaning |
| --- | --- | --- |
| `PYTHON_FRAMEWORK_APP_NAME` | `python-framework` | Logical service name (`config` command). |
| `PYTHON_FRAMEWORK_DEBUG` | `false` | `true`/`1`/`yes`/`on` enable debug in settings. |

Global CLI flags:

| Flag | Meaning |
| --- | --- |
| `--log-level LEVEL` | `DEBUG` … `CRITICAL` for the `python_framework` logger tree. |
| `--log-json` | Structured JSON lines on stdout (omit Rich). |

## Project layout

| Path | Purpose |
| --- | --- |
| `src/python_framework/` | Package: CLI, **Settings**, logging helpers. |
| `tests/` | Pytest suite (`tests` is a package for mypy overrides). |
| `Dockerfile` | Multi-stage image: **`pdm export`** → **`pip install`** into **`/usr/local`** (no in-container venv); runtime copies **`site-packages`** + **`python-framework`** entrypoint. |
| `compose.yaml` | Compose service + **healthcheck** (`python-framework ping`). |
| `.devcontainer/` | VS Code Dev Container (Python 3.12, PDM). |
| `.pre-commit-config.yaml` | Ruff, basic file checks, mypy via `pdm run`. |
| `.github/workflows/ci.yml` | CI matrix, **Bandit**, **pip-audit**, **CycloneDX** SBOM, **multi-arch** Docker build + amd64 smoke tests. |
| `.github/dependabot.yml` | Weekly **pip** + **GitHub Actions** updates. |
| `CONTRIBUTING.md` | Tooling, hooks, versioning, Dev Container notes. |

## Versioning

`[tool.pdm.version]` uses **`source = "scm"`** with a **fallback** when `.git` or tags are unavailable (e.g. default Docker build context). Wheels get a PEP 440 version from tags (e.g. `v0.2.0`) or the fallback. `python_framework.__version__` comes from **importlib.metadata** (`python-framework` distribution).

## Make targets

| Target | Description |
| --- | --- |
| `make help` | List targets. |
| `make setup` | `configure`, `install`, `pre-commit-install`. |
| `make configure` | Create `.env` from `.env.example` if missing. |
| `make lock` / `make install` | PDM lock / `pip install -G dev` equivalent. |
| `make lint` | Ruff + mypy (`src` + `tests`) + Bandit on `src`. |
| `make format` | Ruff format + fix. |
| `make security` | Export requirements and run **pip-audit**. |
| `make sbom` | **CycloneDX** JSON → `dist/sbom-cyclonedx.json`. |
| `make test` | Pytest + coverage gate. |
| `make pre-commit-run` | Run every hook on all files. |
| `make docker-build` / `make docker-run` | Single-arch image. |
| `make docker-buildx-multi` | **linux/amd64** + **linux/arm64** → `./docker-multi/` (local OCI export). |
| `make compose-up` / `make compose-down` | Compose with `compose.yaml`. |
| `make clean` | Remove build artifacts and caches. |

## PDM and the CLI entrypoint

```bash
pdm run python-framework --help
pdm run python-framework --log-json --log-level INFO ping
```

**Why `[tool.pdm.scripts]` defines `python-framework`:** PDM resolves bare commands that **start with `python`** to the venv interpreter, so `pdm run python-framework` used to become `python hello`. The PDM script runs `python -m python_framework` instead. The **`[project.scripts]`** console script is unchanged for wheels and Docker.

## Docker & Compose

**Local development** still uses a **PDM-managed `.venv`** on your machine. **Container images** do **not** create a nested virtualenv: dependencies are installed with **`pip`** into the official image’s **`/usr/local`** Python, and the final stage copies **`site-packages`** plus the **`python-framework`** script. Isolation comes from the container, not from `.venv` inside it.

```bash
make docker-build
make docker-run              # runs hello once and exits (good smoke test)
docker compose -f compose.yaml up --build   # or: make compose-up
```

The default **image** runs **`hello`** once and exits (ideal for **`docker run`**). **Compose** overrides the command with **`sleep infinity`** so the container stays up; the **healthcheck** runs **`python-framework ping`** in parallel. That avoids Compose/Desktop “stuck” behavior when a service exits immediately while a healthcheck is defined.

Plain log formatting is the default in the image (`PYTHON_FRAMEWORK_PLAIN_LOG=1`); locally, Rich is used when **stderr is a TTY**.

Build stages, briefly:

1. **exporter** — install PDM only; **`pdm export --prod`** writes a pinned **`requirements.txt`** from **`pdm.lock`** (non-interactive).
2. **builder** — **`pip install -r requirements.txt`**, then **`pip install --no-deps .`** into **`/usr/local`**.
3. **runtime** — slim image; copy **`/usr/local/lib/${PYTHON_LIBDIR}/site-packages`** and **`/usr/local/bin/python-framework`**. Keep **`PYTHON_LIBDIR`** in sync with **`PYTHON_VERSION`** (e.g. `3.13` → `python3.13`). **`pytest`** includes **`tests/test_dockerfile.py`** so these conventions don’t regress silently.

The Compose file uses `.env.example` by default so it runs without a personal `.env`; switch `env_file` to `.env` when needed.

## Continuous integration

On pushes/PRs to `main` or `master`, CI:

1. Installs with `pdm install -G dev --frozen-lockfile`.
2. Runs Ruff, mypy, **Bandit**.
3. On Python 3.12: **pip-audit** on exported requirements.
4. Runs pytest and `pdm build`.
5. On Python 3.12: generates a **CycloneDX** SBOM and uploads **`dist/*`** as an artifact.
6. Builds a **multi-arch** image (`linux/amd64`, `linux/arm64`) to `docker-multi/` (validation), then builds **amd64** with `load: true` and smoke-tests **hello** / **ping**.

## License

See [LICENSE](./LICENSE).
