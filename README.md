## ManGO: an iRODS Python Client based portal

**This is a fork of KU Leuven's [ManGO
portal](https://github.com/kuleuven/mango-portal) adding integration with
[SODAR](https://github.com/bihealth/sodar-server).** Find the original Readme
below.

### First-time setup

Copy env.example to .env and update the environment variables as appropriate for
your setup.

### Building the Docker image

To build the image, use the following command:

```bash
MANGO_VERSION=x.x.x BUILD_VERSION=z ./build.sh
```

### Running ManGO

The docker-compose.yml file provides a baisc development setup for ManGO. It
includes Apache Tika as a supporting service, runs a Docker image with all the
system dependencies, and mounts the local ./src directory into the container, so
that any edits will be effective without re-building the image. Instead of using
our Docker compose, you may also follow the instructions in the original Readme
below to run ManGO on the host directly.

- Make sure that irods is running and accessible from the host.
- Obtain the irods server certificate and save its path in the environment
  variable IRODS_SSL_CA_CERTIFICATE_PATH.
- From the ./src directory, `npm install` (only the first time) and `npm
  build` every time the Vue app changes (note that src/static/dist is also
  tracked in git).
- Run `docker compose up` and point your browser to http://localhost:3000.

---

> UPDATE: 2026-10-02 BREAKING CHANGES

This repository now hosts the refactored version of ManGO Portal as part of a refactored ManGO platform.

The main changes are:

- The entire ManGO platform is now basically a set of Python packages
- Some plugins have moved out of this repository and are now in their own repository (KuLeuven specific are now in an internal repository)

In the current phase, there are hardly any functional changes, it is mostly refactoring for standard Python packaging

Documentation is in the works on how to deal with this new incarnation of the ManGO platform, but the we are quite sure the changes for any "fork" of implementation of the ManGo POrtal code base is rather small, and much more customisable and maintanable in the future

Stay tuned for more information in the coming weeks


