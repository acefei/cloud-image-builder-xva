FROM python:slim AS base
RUN apt-get update && \
    apt-get install --no-install-recommends -y libguestfs-tools \
                                               linux-image-generic \
                                               qemu-utils \
                                               cloud-init && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV LIBGUESTFS_BACKEND=direct \
    LIBGUESTFS_DEBUG=0 \
    LIBGUESTFS_TRACE=0

FROM base AS guestfish
ENTRYPOINT ["guestfish"]

FROM base AS cloud-init-validator
ENTRYPOINT ["cloud-init", "schema", "--config-file"]

FROM base AS xva-builder
ENTRYPOINT ["python", "/app/src/xva-builder/img2xva.py"]
