# v0.29.1-2

## Development

N/A

## Upstream

- Fix file upload form (CSRF token was missing)
- Add `MANGO_MAX_UPLOAD_FILE_SIZE` environment variable

## SODAR

N/A

# v0.29.1-1

## Development

- Add `src/mango_portal/app.py` as main entrypoint for waitress, remove obsolete waitress scripts
- Add Dockerfile, docker-compose.yml, and build.sh files
- Fix typos and import errors
- Add redirection to referer after logging in
- Add HTTP Basic Auth
- Add `MANGO_URL_PREFIX` environment variable
- Add `IRODS_SSL_CA_CERTIFICATE_PATH` environment variable
- Add `MANGO_IRODS_ENSURE_SSL_IS_ACTIVE` environment variable
- Add `MANGO_DEFAULT_IRODS_ZONE` environment variable (used for Basic Auth)

## Upstream

- Add support for Byte-Range file download
- Add `MANGO_MAX_DOWNLOAD_FILE_SIZE` environment variable

## SODAR

- Add `src/mango_portal/irods_zones_config_sodar.py`, SODAR-specific iRODS config file
- Hide metadata schema view from the UI
- In the landing page, show a list of SODAR projects instead of the iRODS zone home
- Edit `src/mango_portal/kernel/user/templates/user/login_basic.html.j2` to replace KU Leuven with SODAR strings
- Add `MANGO_GLOBAL_ALERT` environment variable and modify `src/mango_portal/kernel/default_templates/templates/base.html.j2` template to show the global alert
