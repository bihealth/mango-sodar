import datetime
import importlib
import logging
import os
import platform

from flask import Response, current_app, flash, render_template, redirect, url_for, g, session
from irods.auth.pam_password import ENSURE_SSL_IS_ACTIVE
from irods.exception import PAM_AUTH_PASSWORD_FAILED
from irods.session import iRODSSession


def authorize_irods_credentials(username, password, zone, irods_session_pool, irods_zones_config, success=None):
    """
    Log-in wiht iRODS credentials

    Verify the username and password for the specified iRODS zone. If user is
    valid, add its credentials to the Flask session and its iRODS session to the
    global session pool.

    :param username: iRODS user name.
    :param password: iRODS password.
    :param zone: iRODS zone.
    :param session: Flask session, where user credentials are saved.
    :param success: Value to be returned in case of successful log in.
    :return: ``success`` if the credentials are valid, otherwise a redirect
             to an error view.
    """
    if not username:
        flash("Missing user id", category="danger")
        return redirect(url_for(current_app.config["MANGO_LOGIN_ACTION"]))
    if not password:
        flash("Missing password", category="danger")
        return redirect(url_for(current_app.config["MANGO_LOGIN_ACTION"]))
    if not zone:
        flash("Missing zone", category="danger")
        return redirect(url_for(current_app.config["MANGO_LOGIN_ACTION"]))

    try:
        irods_session = iRODSSession(
            user=username,
            password=password,
            **irods_zones_config[zone]["parameters"],
            **irods_zones_config[zone]["ssl_settings"],
        )
        irods_use_ssl = bool(int(os.getenv("IRODS_ENSURE_SSL_IS_ACTIVE", '1')))
        irods_session.set_auth_option_for_scheme(
            "pam_password",
            ENSURE_SSL_IS_ACTIVE,
            irods_use_ssl,
        )
    except Exception as e:
        logging.info(e)
        flash("Could not create iRODS session", category="danger")
        return redirect(url_for(current_app.config["MANGO_LOGIN_ACTION"]))

    # sanity check on credentials
    try:
        irods_session.collections.get(f"/{irods_session.zone}/home/{username}")
    except PAM_AUTH_PASSWORD_FAILED as e:
        logging.info(e)
        flash("Authentication failed: invalid password", category="danger")
        return redirect(url_for(current_app.config["MANGO_LOGIN_ACTION"]))
    except Exception as e:
        logging.info(e)
        flash("Authentication failed: " + str(e))
        return redirect(url_for(current_app.config["MANGO_LOGIN_ACTION"]))

    # should be ok now to add session to pool
    irods_session_pool.add_irods_session(username, irods_session)
    session["userid"] = username
    session["password"] = password
    session["zone"] = irods_session.zone
    irods_session_pool.irods_node_logins += [
        {
            "userid": username,
            "zone": irods_session.zone,
            "login_time": datetime.datetime.now(),
        }
    ]
    g.irods_session = irods_session
    user_home = f"/{g.irods_session.zone}/home/{irods_session.username}"
    zone_home = f"/{g.irods_session.zone}/home"
    g.user_home = user_home
    g.zone_home = zone_home
    logging.info(
        f"User {irods_session.username}, zone {irods_session.zone} logged in"
    )
    return success


def get_app(
    config_module_name: str | None = None,
    root_path: str | os.PathLike[str] | None = None,
    template_folder: str | os.PathLike[str] | None = None,
    static_folder: str | os.PathLike[str] | None = None,
):
    """Returns the Flask application instance, optionally loading a specific configuration module."""

    import flask
    import irods
    from flask import Flask, request
    from flask_bootstrap import Bootstrap5
    from flask_cors import CORS
    from flask_session import Session
    from jinja2 import select_autoescape
    from mango_lib.jinja import MangoJinjaExtension
    from werkzeug.exceptions import HTTPException, ServiceUnavailable

    import mango_portal.irods_session_pool as irods_session_pool
    import mango_portal.version as version

    from .cache import cache
    from .csrf import csrf
    from .kernel.user import get_irods_session_from_environment

    rootlogger = logging.getLogger()
    rootlogger.setLevel("INFO")

    app = Flask(
        __name__,
        root_path=root_path,
        template_folder=template_folder,
        static_folder=static_folder,
    )

    irods_zone_config_module = importlib.import_module(
        os.getenv("IRODS_ZONES_CONFIG", "mango_portal.irods_zones_config")
    )
    app.config["irods_zones"] = irods_zone_config_module.irods_zones
    app.config["DEFAULT_IRODS_ZONE"] = os.getenv("MANGO_DEFAULT_IRODS_ZONE")
    app.config["MAX_DOWNLOAD_FILE_SIZE"] = int(os.getenv("MANGO_MAX_DOWNLOAD_FILE_SIZE", "53687091200"))

    # Initialize Jinja extensions
    app.jinja_env.add_extension(MangoJinjaExtension)

    # 1) Load packaged defaults first (always)
    import mango_portal.default_config as _default_config

    app.config.from_object(_default_config)

    # 2) Then overlay the application config, if available

    try:
        if config_module_name:
            _app_config_module = importlib.import_module(config_module_name)
        else:
            import config as _app_config_module
        app.config.from_object(_app_config_module)
        app.logger.info(f"Loaded application config from {_app_config_module.__file__}")
    except Exception as e:
        app.logger.warning(f"Failed to load application config: {e}")

    # initialize kernel modules
    for kernel_module in app.config.get("MANGO_PORTAL_KERNEL", []):
        try:
            kernel_module = importlib.import_module(kernel_module)
            if hasattr(kernel_module, "init_app"):
                kernel_module.init_app(app)
                app.logger.info(f"Initialized kernel module {kernel_module.__name__}")
            else:
                app.logger.warning(
                    f"Kernel module {kernel_module.__name__} does not have an init_app function"
                )
        except Exception as e:
            app.logger.error(f"Failed to initialize kernel module {kernel_module}: {e}")

    # Initialize plugins
    for plugin_module in app.config.get("MANGO_PORTAL_PLUGINS", []):
        # try:
        plugin_module = importlib.import_module(plugin_module)
        if hasattr(plugin_module, "init_app"):
            plugin_module.init_app(app)
            app.logger.info(f"Initialized plugin module {plugin_module.__name__}")
        else:
            app.logger.warning(
                f"Plugin module {plugin_module.__name__} does not have an init_app function"
            )
        # except Exception as e:
        #     app.logger.error(f"Failed to initialize plugin module {plugin_module}: {e}")

    # global dict holding the irods sessions per user, identified either by their flask session id or by a magic key 'localdev'

    # use a non default session handler only if specified
    if app.config.get("SESSION_TYPE", None):
        Session(app)  # use session specified in config.py

    print(f"Flask version {flask.__version__}")

    # set the loggin level to the configured one
    rootlogger.setLevel(app.config.get("LOGGING_LEVEL", "INFO"))

    # Allow cross origin requests for SPA/Ajax situations
    CORS(app, supports_credentials=True)

    mango_server_info = {"server_start": datetime.datetime.now()}
    # app.config["EXPLAIN_TEMPLATE_LOADING"] = True
    ## enable auto escape in jinja2 templates
    # app.jinja_options["autoescape"] = lambda _: True

    app.jinja_env.autoescape = select_autoescape(
        enabled_extensions=("html", "htm", "xml", "xhtml", "svg", "j2", "jinja"),
        default_for_string=True,
        default=True,  # escape by default, opt out per template
    )

    # register bootstrap5 support
    bootstrap = Bootstrap5(app)
    # register csrf on the main app
    csrf.init_app(app)

    # Caching, make sure the filesystem dir existsif CACHE_TYPE  is FileSystemCache
    if app.config["CACHE_TYPE"] == "FileSystemCache" and not os.path.exists(
        app.config["CACHE_DIR"]
    ):
        os.makedirs(app.config["CACHE_DIR"])

    cache.init_app(app)
    with app.app_context():
        cache.clear()

    # Add debug toolbar if enabled via environment variable
    if os.getenv("FLASK_DEBUG_TOOLBAR", "disabled").lower() == "enabled":
        from flask_debugtoolbar import DebugToolbarExtension

        DebugToolbarExtension(app)

    if _mod_func := os.getenv(
        "LOCALDEV_SESSION_FUNC"
    ):  # in "module[.submodule].function" format
        _mod, _func = _mod_func.rsplit(".", 1)
        localdev_session_func = getattr(importlib.import_module(_mod), _func)
    else:
        localdev_session_func = get_irods_session_from_environment

    @app.context_processor
    def ui_navbars():
        from .mango_ui import admin_navbar_entries, navbar_entries

        for blueprint in admin_navbar_entries:
            logging.info(f"Admin UI: added {blueprint}")

        for blueprint in navbar_entries:
            logging.info(f"UI: added {blueprint}")

        return {
            "admin_navbar_entries": admin_navbar_entries,
            "navbar_entries": navbar_entries,
        }

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.exception(e)
        # pass through HTTP errors
        if isinstance(e, HTTPException):
            return e

        # non-HTTP exceptions only
        return render_template("500.html.j2", e=e), 500

    @app.before_request
    def init_and_secure_views():
        """ """
        # Always let static resources be served, eg css, js , images
        if request.endpoint in app.config["MANGO_NON_LOGGED_IN_ROUTES"]:
            return None

        # First check if there are no calamities and need to interrupt here
        if os.path.isfile("storage/service-down.txt"):
            message = ""
            with open("storage/service-down.txt") as f:
                message = f.read()
            raise ServiceUnavailable(message)

        # some globals for feeding the templates
        g.prc_version = irods.__version__
        g.flask_version = flask.__version__
        g.python_version = platform.python_version()
        g.mango_version = version.__version__
        g.mango_alert = os.getenv("MANGO_GLOBAL_ALERT")

        # check sessions cleanup daemon and spawn a new one if needed
        irods_session_pool.check_and_restart_cleanup()

        if current_app.config["MANGO_AUTH"] == "localdev":
            irods_session = None
            if not "userid" in session:
                print(f"No user id in session")
            if "userid" in session:
                irods_session = irods_session_pool.get_irods_session(session["userid"])
            if not irods_session:
                print("No irods session found in pool, recreating one")
                irods_session = localdev_session_func()
                session["userid"] = irods_session.username
                irods_session_pool.add_irods_session(session["userid"], irods_session)
            g.irods_session = irods_session
            print(f"Session id: {session['userid']}")
            g.user_home = f"/{g.irods_session.zone}/home/{irods_session.username}"
            g.zone_home = f"/{g.irods_session.zone}/home"

            g.mango_server_info = mango_server_info

            return None

        else:
            irods_session = None
            if not "userid" in session:
                print(f"No user id in session, need auth")
            if "userid" in session:
                irods_session = irods_session_pool.get_irods_session(session["userid"])

            if irods_session:
                g.irods_session = irods_session
                user_home = f"/{g.irods_session.zone}/home/{irods_session.username}"
                zone_home = f"/{g.irods_session.zone}/home"
                g.user_home = user_home
                g.zone_home = zone_home
                g.mango_server_info = mango_server_info
                return None
            elif auth := request.authorization:
                # Return None if Basic Auth succeeds, else redirect to login page
                return authorize_irods_credentials(
                    auth.username,
                    auth.password,
                    current_app.config["DEFAULT_IRODS_ZONE"],
                    irods_session_pool,
                    current_app.config["irods_zones"],
                )
            else:
                # save the request url which may come from a bookmark or a page that was iopen longer than the irods session lifetime
                session["redirect_after_login"] = (
                    request.url
                )  # this is with a http scheme, but gets rewritten as https
                return Response(
                    render_template("user/login_basic.html.j2"),
                    status=401,
                    direct_passthrough=True,
                    headers={"WWW-Authenticate": "Basic realm=mango-sodar"},
                )
            # else:
            #     print(f"Request url before login {request.url}")
            #     return redirect(url_for(current_app.config["MANGO_LOGIN_ACTION"]))

    @app.after_request
    def release_irods_session_lock(response):
        if "userid" in session:
            irods_session_pool.unlock_irods_session(session["userid"])
        return response

    # register the main landing page route dynamically
    main_landing_route = app.config.get(
        "MANGO_MAIN_LANDING_ROUTE",
        {"module": "kernel.common.browse", "function": "index"},
    )

    main_landing_route_module = importlib.import_module(
        main_landing_route["module"], package="app"
    )

    app.add_url_rule(
        "/",
        endpoint="index",
        view_func=getattr(main_landing_route_module, main_landing_route["function"]),
    )

    return app
