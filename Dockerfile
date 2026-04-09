# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12
# Must match site-packages layout for the image tag (3.12 -> python3.12, 3.13 -> python3.13).
ARG PYTHON_LIBDIR=python3.12
ARG PDM_VERSION=2.26.7

# Resolve a pinned requirements.txt from pdm.lock (no prompts).
FROM python:${PYTHON_VERSION}-slim AS exporter
ARG PDM_VERSION
ENV PDM_NON_INTERACTIVE=1 \
    CI=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install --no-cache-dir --no-input "pdm==${PDM_VERSION}"
WORKDIR /app
COPY pyproject.toml pdm.lock README.md ./
RUN pdm export --prod --without-hashes -o /requirements.txt

# Install into the image Python under /usr/local (no virtualenv — isolation is the container).
FROM python:${PYTHON_VERSION}-slim AS builder
ARG PYTHON_LIBDIR
ENV PIP_DEFAULT_TIMEOUT=120 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY --from=exporter /requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-input -r /tmp/requirements.txt
COPY src ./src
COPY pyproject.toml pdm.lock README.md ./
RUN pip install --no-cache-dir --no-input --no-deps .

FROM python:${PYTHON_VERSION}-slim AS runtime
ARG PYTHON_LIBDIR
RUN useradd --create-home --uid 10001 app
WORKDIR /home/app
COPY --from=builder /usr/local/lib/${PYTHON_LIBDIR}/site-packages /usr/local/lib/${PYTHON_LIBDIR}/site-packages
COPY --from=builder /usr/local/bin/python-framework /usr/local/bin/python-framework
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHON_FRAMEWORK_PLAIN_LOG=1
USER app
ENTRYPOINT ["python-framework"]
CMD ["hello"]
