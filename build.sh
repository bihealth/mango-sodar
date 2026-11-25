#!/bin/bash

export REPO=ghcr.io/bihealth/mango-sodar
export IRODS_PKG_VERSION=${IRODS_PKG_VERSION-4.3.5}
export MANGO_VERSION=${MANGO_VERSION-v0.29.1}
export MANGO_SODAR_VERSION=${MANGO_SODAR_VERSION-dev}
export BUILD_VERSION=${BUILD_VERSION-0}

image="${REPO}:${MANGO_VERSION}-${MANGO_SODAR_VERSION}-${BUILD_VERSION}"

docker build \
    -t $image \
    --build-arg IRODS_PKG_VERSION=${IRODS_PKG_VERSION} \
    .

echo "Now do:"
echo "docker push $image"
