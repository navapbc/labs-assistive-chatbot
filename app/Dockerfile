# Use the official python3 image based on Debian 13 "Trixie".
# https://hub.docker.com/_/python

# The build stage that will be used to deploy to the various environments
# needs to be called `release` in order to integrate with the repo's
# top-level Makefile
#
# Stages:
#   base    - runtime OS packages and the app user; shared by every stage
#   dev     - base + build tools + poetry, with dev dependencies (docker-compose)
#   builder - base + build tools + poetry; builds the production virtualenv
#   release - base + the virtualenv and app code from builder; no build tools
FROM python:3.13-slim AS base

# Fail the RUN if any command in a pipe fails (e.g. the curl | gpg below)
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Pinning apt package versions breaks the build whenever Debian drops old versions;
# we rely on `apt-get upgrade` and the weekly vulnerability scans instead.
# hadolint ignore=DL3008
RUN apt-get update && apt-get install --no-install-recommends -y ca-certificates curl gnupg && \
    # Need to add the official PostgreSQL repo to install v16 -- https://www.postgresql.org/download/linux/debian/
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-archive-keyring.gpg && \
    . /etc/os-release && \
    echo "deb [signed-by=/usr/share/keyrings/postgresql-archive-keyring.gpg] http://apt.postgresql.org/pub/repos/apt ${VERSION_CODENAME}-pgdg main" > /etc/apt/sources.list.d/postgres.list && \
    apt-get update \
    # Install security updates
    # https://pythonspeed.com/articles/security-updates-in-docker/
    && apt-get upgrade --yes \
    # pg_dump/pg_restore for src/db/pg_dump_util.py. Need v16 or higher to be
    # compatible with the Postgres version in the main-db image
    && apt-get install --no-install-recommends --yes postgresql-client-16 \
    # curl and gnupg were only needed to add the PostgreSQL repo
    && apt-get purge --yes --auto-remove curl gnupg \
    # Reduce the image size by clear apt cached lists
    # Complies with https://github.com/codacy/codacy-hadolint/blob/master/codacy-hadolint/docs/description/DL3009.md
    && rm -fr /var/lib/apt/lists/*

# The base image's bundled pip lags behind security fixes
RUN pip install --no-cache-dir pip==26.2.1

ARG RUN_UID
ARG RUN_USER

# The following logic creates the RUN_USER home directory and the directory where
# we will be storing the application in the image. This runs when the user is not root
RUN : "${RUN_USER:?RUN_USER and RUN_UID need to be set and non-empty.}" && \
    [ "${RUN_USER}" = "root" ] || \
    (useradd --create-home --create --user-group --home "/home/${RUN_USER}" --uid ${RUN_UID} "${RUN_USER}" \
    && mkdir /app \
    && chown -R ${RUN_UID} "/home/${RUN_USER}" /app)

#------------------
# Build tools layer
#------------------

FROM base AS build-tools

# Compilers and headers for any dependency without a prebuilt wheel
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install --no-install-recommends --yes build-essential libpq-dev \
    && rm -fr /var/lib/apt/lists/*

# Install poetry, the package manager.
# https://python-poetry.org
RUN pip install --no-cache-dir poetry==2.3.4

#-----------
# Dev image
#-----------

FROM build-tools AS dev
ARG RUN_USER
USER ${RUN_USER}
WORKDIR /app

# Gunicorn requires this workaround to create writable temporary directory in
# our readonly root file system. https://github.com/aws/containers-roadmap/issues/736
RUN mkdir -p /tmp
VOLUME ["/tmp"]

COPY pyproject.toml poetry.lock ./
# Explicitly create a new virtualenv to avoid getting overridden by mounted .venv folders
RUN poetry config virtualenvs.in-project false && poetry env use python
# Install all dependencies including dev dependencies
RUN poetry install --no-root --with dev

COPY . /app

# Set the host to 0.0.0.0 to make the server available external
# to the Docker container that it's running in.
ENV HOST=0.0.0.0

# Run the application.
CMD ["poetry", "run", "gunicorn","-k uvicorn.workers.UvicornWorker","-b 0.0.0.0:8000", "src.app:app"]

#---------
# Builder
#---------

FROM build-tools AS builder

WORKDIR /app

# Set virtualenv location to be in project to be easy to find
# This will create a virtualenv in /app/.venv/
# See https://python-poetry.org/docs/configuration/#virtualenvsin-project
# See https://python-poetry.org/docs/configuration/#using-environment-variables
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Install production runtime dependencies only. Copying just the dependency
# manifests first lets Docker cache this layer until they change.
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main --no-interaction

COPY . /app

# Build the application binary (python wheel) defined in pyproject.toml
# Note that this will only copy over python files, and files stated in the
# include section in pyproject.toml. Also note that if you change the name or
# version section in pyproject.toml, you will need to change the dist/... to match
# or the application will not build
RUN poetry build --format wheel \
    && .venv/bin/pip install --no-cache-dir --no-deps 'dist/decision_support_tool-0.1.0-py3-none-any.whl' \
    # pip isn't needed at runtime
    && .venv/bin/pip uninstall --yes pip

#---------
# Release
#---------

FROM base AS release
ARG RUN_USER

# Gunicorn requires this workaround to create writable temporary directory in
# our readonly root file system. https://github.com/aws/containers-roadmap/issues/736
RUN mkdir -p /tmp
VOLUME ["/tmp"]

WORKDIR /app

# The virtualenv (/app/.venv) and app code; poetry and build tools stay behind
COPY --from=builder /app /app

# Add project's virtual env to the PATH so we can directly run the scripts
# defined in pyproject.toml (e.g. db-migrate)
ENV PATH="/app/.venv/bin:$PATH"

# Set the host to 0.0.0.0 to make the server available external
# to the Docker container that it's running in.
ENV HOST=0.0.0.0

USER ${RUN_USER}

# Run the application.
CMD ["gunicorn","-k uvicorn.workers.UvicornWorker","-b 0.0.0.0:8000", "src.app:app"]
