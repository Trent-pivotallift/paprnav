ARG PYTHON_BASE=python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7
FROM ${PYTHON_BASE}

ARG PAPRNAV_SOURCE_COMMIT
ARG PAPRNAV_MIGRATION_MANIFEST_SHA256
ARG PAPRNAV_BOOTSTRAP_MANIFEST_SHA256

LABEL org.opencontainers.image.revision="${PAPRNAV_SOURCE_COMMIT}" \
      io.paprnav.migration-manifest-sha256="${PAPRNAV_MIGRATION_MANIFEST_SHA256}" \
      io.paprnav.bootstrap-manifest-sha256="${PAPRNAV_BOOTSTRAP_MANIFEST_SHA256}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PAPRNAV_DISABLE_DOTENV=1 \
    PAPRNAV_MIGRATION_ROOT=/migration

RUN addgroup --system --gid 10001 paprnav \
    && adduser --system --uid 10001 --ingroup paprnav --home /nonexistent --no-create-home paprnav

WORKDIR /bootstrap
COPY bootstrap/requirements.lock /bootstrap/requirements.lock
RUN python -m pip install --no-cache-dir --require-hashes -r /bootstrap/requirements.lock \
    && rm -rf /root/.cache /tmp/*

COPY --chown=root:root migration/ /migration/
COPY --chown=root:root bootstrap/bootstrap.py bootstrap/grant-manifest.json bootstrap/reference-data.json /bootstrap/
RUN chmod -R a-w /migration /bootstrap

USER 10001:10001
ENTRYPOINT ["python", "-I", "-B", "/bootstrap/bootstrap.py"]
