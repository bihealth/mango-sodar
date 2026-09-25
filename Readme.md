## ManGO-SODAR

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

## ManGO: an iRODS Python Client based portal

> WARNING: the current state is geared towards deployments in the KU Leuven specific cloud services, see [Custom deployments](Custom-deployments.md) for your options. In the near future, the KU Leuven specifics will be entirely decoupled from the generic code base so a default installation will work with a vanilla iRODS installation 

> The current version requires python 3.10 or higher. See also the section on changing the python version below.

### Installation (local development mode, Linux, KULeuven specific for now)

You need to have a valid and initialised iRODS environment for your account, the easiest is to install the iRODS icommands and execute the instructions from the ManGO landing page for the chosen iRODS zone 

Create a python virtual environment in the root of this repository checkout and install the required modules, for example

```sh
$ python3 -m venv venv
$ . venv/bin/activate
$ pip3 install -r requirements.txt
```

### Vue2.js development and building

Currently the node module parcel and its dependencies are required for building, see https://parceljs.org/

Before using the first time, execute the following steps

```sh
$ cd src
$ npm install
$ npm run build
```

### Starting the development server (waitress version, recommended)

Make sure you activated the virtual environment

Launch the flask development server from the src directory:
```sh
$ cd src
$ ./run_waitress.sh
```
or

```sh
$ src/run_waitress.sh
```

This will start waitress as used in the production deployments, but adds a listener for reloading the app when you change files locally.

Point your browser to `http://localhost:3000`

### Updating

Check for new required python modules and or versions

```
$ pip3 install -r requirements.txt
```

If you encounter javascript related errors, the used js files may need an update:

```sh
$ cd src
$ npm install
$ npm run build
```

### Changing the python version

If you upgrade your python version, the requirements.txt may not be correct anymore (outdated packages). You can install updated python modules with:

```sh
$ pip list --outdated --format=freeze | grep -v '^\-e' | \
 cut -d = -f 1  | xargs -n1 pip install -U
```

### Technical:

- backend framework: Flask
- code organisation: Flask blueprints for making things modular
- leverage the irods-Python client
- optional OpenSearch integration

## Development guidelines

### Python

The preferred formatter is _black_ with its default options, it also has an integration with IDE's such as VSCode

### Javascript

The preferred formatter is _prettier_ with indenting to 4 spaces, no TAB's and single quotes for strings
