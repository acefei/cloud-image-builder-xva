FROM python:slim AS base

FROM base AS seed-iso-builder
RUN apt-get update && \
    apt-get install --no-install-recommends -y genisoimage cloud-init && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

VOLUME [ "/output" ]
COPY src/cloud-config-templates /app


FROM base AS xva-builder
COPY src/xva-builder /app
VOLUME [ "/output" ]
CMD [ "echo" ]