# Contributing

## Environment

Install [PDM](https://pdm-project.org/latest/#installation) and Python 3.11+.

```bash
make setup
```

This installs dependencies, creates `.env` from `.env.example` if missing, and installs **pre-commit** hooks.

## Commands

| Command | Purpose |
| --- | --- |
| `make format` | Ruff format + auto-fix |
| `make lint` | Ruff check, Ruff format check, mypy (`src` + `tests`), Bandit on `src` |
| `make test` | Pytest with coverage gate |
| `make security` | Export requirements and run `pip-audit` |
| `make sbom` | Write CycloneDX JSON to `dist/sbom-cyclonedx.json` |
| `make pre-commit-run` | Run all pre-commit hooks on the tree |

## Commits and hooks

Hooks run **Ruff** (lint + format), **check-toml** / **check-yaml**, whitespace hygiene, and **mypy** via `pdm run mypy src tests`. Fix reported issues before pushing.

## Releases and versioning

Versions are derived from **git tags** when building wheels (`[tool.pdm.version]` `source = "scm"`). Without tags or outside a repository, the **fallback** version in `pyproject.toml` is used (suitable for Docker and reproducible CI).

Tag a release (example):

```bash
git tag v0.2.0
git push origin v0.2.0
pdm build
```

Keep `importlib.metadata.version("python-framework")` (used for `python_framework.__version__`) aligned with release tags.

## Dependency updates

[Dependabot](.github/dependabot.yml) opens weekly PRs for **pip** (including `pyproject.toml` / lockfile workflows supported by GitHub) and **GitHub Actions**. Review lockfile changes with `pdm lock` after merging dependency bumps when needed.

## Docker production image

The **`Dockerfile`** is **not** the same as local PDM workflows:

- **Exporter** stage runs **`pdm export`** (lockfile only) to avoid **`pdm install`** during `docker build` (interactive hangs).
- **Builder** installs with **`pip`** into **`/usr/local`**, not a **`.venv` inside the image**.
- **Runtime** copies **`site-packages`** and the **`python-framework`** console script; bumping **`PYTHON_VERSION`** requires updating **`PYTHON_LIBDIR`** (see Dockerfile comments).

Contract checks live in **`tests/test_dockerfile.py`**.

## Dev Containers

Open the repo in a Dev Container (`.devcontainer/devcontainer.json`) for a consistent Linux toolchain. **`postCreateCommand`** runs `pipx install pdm` and **`pdm install -G dev`**; the resulting **`.venv`** is for development inside the container only (the **production Dockerfile** does not use an in-image venv).
