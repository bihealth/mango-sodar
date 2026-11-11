import os
from uuid import uuid4
from . import get_app

os.environ.setdefault("IRODS_ZONES_CONFIG", "mango_portal.irods_zones_config_minimal")
os.environ.setdefault("IRODS_HOST", "localhost")
os.environ.setdefault("IRODS_PORT", "1247")
os.environ.setdefault("IRODS_SSL_CA_CERTIFICATE_PATH", "/path/to/irods/server.crt")
os.environ.setdefault("SECRET_KEY", uuid4())
# os.environ.setdefault("FLASK_DEBUG_TOOLBAR", "enabled")

app = get_app(static_folder="static")
app.config.update(APPLICATION_ROOT="/mango")
