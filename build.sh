#!/bin/bash

export REPO=ghcr.io/bihealth/mango-sodar
export IRODS_PKG_VERSION=${IRODS_PKG_VERSION-4.3.5}
export MANGO_VERSION=${MANGO_VERSION-dev}
export BUILD_VERSION=${BUILD_VERSION-0}

docker build \
    -t "${REPO}:${MANGO_VERSION}-${BUILD_VERSION}" \
    --build-arg IRODS_PKG_VERSION=${IRODS_PKG_VERSION} \
    .

echo "Now do:"
echo "docker push ${REPO}:${MANGO_VERSION}-${BUILD_VERSION}"
