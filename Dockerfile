# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12
ARG PDM_VERSION=2.26.7

FROM python:${PYTHON_VERSION}-slim AS builder
ARG PDM_VERSION
ENV PDM_CHECK_UPDATE=false \
    PDM_USE_VENV=1
RUN pip install --no-cache-dir "pdm==${PDM_VERSION}"
WORKDIR /app
COPY pyproject.toml pdm.lock README.md ./
COPY src ./src
RUN pdm install --prod --no-editable --frozen-lockfile

FROM python:${PYTHON_VERSION}-slim AS runtime
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER app
ENTRYPOINT ["python-framework"]
CMD ["hello"]
