PYTHON ?= python3
PDM ?= pdm
IMAGE ?= python-framework:local

.PHONY: help setup configure lock install build lint format test run clean \
	pre-commit-install pre-commit-run security sbom docker-build docker-run \
	docker-buildx-multi compose-up compose-down prompt-example structured-tutorial

help:  ## Show available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "%-22s %s\n", $$1, $$2}'

setup: configure install pre-commit-install  ## One-shot local bootstrap
configure:  ## Create a local .env from the example when missing
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; fi

lock:  ## Refresh the lockfile after dependency changes
	$(PDM) lock

install:  ## Install all dependency groups (including dev)
	$(PDM) install -G dev

pre-commit-install:  ## Install git hooks for pre-commit
	$(PDM) run pre-commit install

pre-commit-run:  ## Run pre-commit on all files
	$(PDM) run pre-commit run --all-files

build:  ## Build sdist/wheel artifacts
	$(PDM) build

lint:  ## Static analysis (ruff + mypy + bandit)
	$(PDM) run ruff check src tests
	$(PDM) run ruff format --check src tests
	$(PDM) run mypy src tests
	$(PDM) run bandit -r src -c pyproject.toml

format:  ## Auto-format with Ruff
	$(PDM) run ruff format src tests
	$(PDM) run ruff check --fix src tests

security:  ## Dependency audit + pip-audit on exported requirements
	$(PDM) export -G dev -f requirements --without-hashes -o .requirements-audit.txt
	$(PDM) run pip-audit -r .requirements-audit.txt --desc on
	rm -f .requirements-audit.txt

sbom:  ## Write CycloneDX JSON under dist/sbom-cyclonedx.json
	@mkdir -p dist
	$(PDM) run cyclonedx-py environment -o dist/sbom-cyclonedx.json

test:  ## Run unit tests with coverage gates
	$(PDM) run pytest

prompt-example:  ## Run OpenAI contact extraction demo (needs OPENAI_API_KEY)
	$(PDM) run python -m python_framework.examples.prompt_example

structured-tutorial:  ## Full structured-outputs tutorial — many API calls (needs OPENAI_API_KEY)
	$(PDM) run python -m python_framework.examples.structured_outputs_tutorial.tutorial

run:  ## Run all registered LLM examples via PDM (needs OPENAI_API_KEY)
	$(PDM) run python-framework run-examples

run-ping:  ## Run the ping subcommand locally
	$(PDM) run python-framework ping

docker-build:  ## Build the runtime image tagged $(IMAGE)
	docker build -t $(IMAGE) .

docker-buildx-multi:  ## Build multi-arch to ./docker-multi (oci layout; same pattern as CI)
	docker buildx create --name fw-multi --use 2>/dev/null || docker buildx use fw-multi
	docker buildx inspect --bootstrap
	docker buildx build --platform linux/amd64,linux/arm64 -t $(IMAGE)-multi \
		-o type=local,dest=$(CURDIR)/docker-multi --pull=false .

docker-run:  ## Run the default container entrypoint
	docker run --rm $(IMAGE)

docker-run-ping:  ## Run ping inside the container
	docker run --rm $(IMAGE) ping

compose-up:  ## docker compose up (build + attach)
	docker compose -f compose.yaml up --build

compose-down:  ## docker compose down
	docker compose -f compose.yaml down

clean:  ## Remove build artifacts and caches
	rm -rf dist build .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage .requirements-audit.txt
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
