FROM python:3.12-bookworm

ARG TIKA_URL=http://localhost:9998/
ARG IRODS_PKG_VERSION="4.3.5"
ARG IRODS_PKG_SUFFIX="-0~bookworm"

ENV TIKA_URL=$TIKA_URL
ENV spOption="ManGO_portal"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get -y upgrade && \
    apt-get -y install libimage-exiftool-perl nano poppler-utils vim nodejs npm wget gpg && \
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
COPY requirements-mango-flow.txt requirements.txt
RUN pip install -r requirements.txt
COPY src /app/

# Build the Vue app
RUN npm install
RUN npm run build

EXPOSE 80 3000
CMD ["./run_waitress_generic_local.sh"]
