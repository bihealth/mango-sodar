FROM python:3.14-bookworm

LABEL org.opencontainers.image.source=https://github.com/bihealth/mango-sodar

ARG IRODS_PKG_VERSION="4.3.5"
ARG IRODS_PKG_SUFFIX="-0~bookworm"

ENV spOption="ManGO_portal"
ENV MANGO_URL_PREFIX="/"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get -y upgrade && \
    apt-get -y install libimage-exiftool-perl nano poppler-utils vim wget gpg && \
    rm -rf /var/lib/apt/lists/*
RUN echo "Europe/Berlin" > /etc/timezone && rm /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

# Install iRODS icommands
RUN wget -qO - https://packages.irods.org/irods-signing-key.asc | \
    gpg \
        --no-options \
        --no-default-keyring \
        --no-auto-check-trustdb \
        --homedir /dev/null \
        --no-keyring \
        --import-options import-export \
        --output /etc/apt/keyrings/renci-irods-archive-keyring.pgp \
        --import
RUN echo "deb [signed-by=/etc/apt/keyrings/renci-irods-archive-keyring.pgp arch=amd64] https://packages.irods.org/apt/ bookworm main" | \
    tee /etc/apt/sources.list.d/renci-irods.list
RUN apt update && \
    apt install -y \
        irods-icommands=${IRODS_PKG_VERSION}${IRODS_PKG_SUFFIX} \
        irods-runtime=${IRODS_PKG_VERSION}${IRODS_PKG_SUFFIX} && \
    rm -rf /var/lib/apt/lists/*

# Install python app
COPY . ./
RUN pip install uv==0.11.23
RUN uv sync

EXPOSE 80 3000
CMD uv run waitress-serve --host 0.0.0.0 --port 3000 --url-prefix ${MANGO_URL_PREFIX} src.mango_portal.app:app
