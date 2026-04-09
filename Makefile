PYTHON ?= python3
PDM ?= pdm
IMAGE ?= python-framework:local

.PHONY: help setup configure lock install build lint format test run clean docker-build docker-run

help:  ## Show available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "%-18s %s\n", $$1, $$2}'

setup: configure install  ## One-shot local bootstrap
configure:  ## Create a local .env from the example when missing
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; fi

lock:  ## Refresh the lockfile after dependency changes
	$(PDM) lock

install:  ## Install all dependency groups (including dev)
	$(PDM) install -G dev

build:  ## Build sdist/wheel artifacts
	$(PDM) build

lint:  ## Static analysis (ruff + mypy)
	$(PDM) run ruff check src tests
	$(PDM) run ruff format --check src tests
	$(PDM) run mypy src

format:  ## Auto-format with Ruff
	$(PDM) run ruff format src tests
	$(PDM) run ruff check --fix src tests

test:  ## Run unit tests with coverage gates
	$(PDM) run pytest

run:  ## Run the CLI locally via PDM
	$(PDM) run python-framework hello

run-ping:  ## Run the ping subcommand locally
	$(PDM) run python-framework ping

docker-build:  ## Build the runtime image tagged $(IMAGE)
	docker build -t $(IMAGE) .

docker-run:  ## Run the default container entrypoint
	docker run --rm $(IMAGE)

docker-run-ping:  ## Run ping inside the container
	docker run --rm $(IMAGE) ping

clean:  ## Remove build artifacts and caches
	rm -rf dist build .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
