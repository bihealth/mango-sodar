from flask import (
    Blueprint,
    current_app as app,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from irods.session import iRODSSession
from ..template_overrides import get_template_override_manager

import mango_portal.irods_session_pool as irods_session_pool
from mango_portal import authorize_irods_credentials
import logging
import importlib
import os


user_bp = Blueprint(
    "user_bp", __name__, static_folder="static/user", template_folder="templates"
)


@user_bp.route("/user/groups")
def my_groups():
    """ """

    my_groups = g.irods_session.my_groups
    return render_template("mygroups.html.j2", my_groups=my_groups)


@user_bp.route("/user/profile")
def my_profile():
    """ """

    me = g.irods_session.user
    my_groups = g.irods_session.my_groups

    # logged in since info
    logged_in_since = irods_session_pool.irods_user_sessions[session["userid"]].created

    home_total_size_in_bytes = 0
    n_data_objects = 0
    try:
        collection = g.irods_session.collections.get(
            f"/{g.irods_session.zone}/home/{g.irods_session.username}"
        )
        for info in collection.walk():
            n_data_objects += len(info[2])
            home_total_size_in_bytes += sum(d.size for d in info[2])
    except Exception:
        home_total_size_in_bytes = -1

    view_template = get_template_override_manager(
        g.irods_session.zone
    ).get_template_for_catalog_item(None, "user/myprofile.html.j2")
    return render_template(
        view_template,
        me=me,
        my_groups=my_groups,
        logged_in_since=logged_in_since,
        home_total_size=home_total_size_in_bytes,
        n_data_objects=n_data_objects,
    )


@user_bp.route("/group/members/<group_name>")
def group_members(group_name):
    """ """
    members = []
    status = "Ok"
    try:
        irods_session: iRODSSession = g.irods_session
        my_group = irods_session.groups.get(group_name)
        members = my_group.members

    except Exception:
        status = "Error"

    view_template = get_template_override_manager(
        g.irods_session.zone
    ).get_template_for_catalog_item(None, "user/group_members.html.j2")

    return render_template(
        view_template,
        group_name=group_name,
        members=members,
        status=status,
    )


@user_bp.route("/user/login", methods=["GET", "POST"])
def login_basic():
    """Basic login using username and password"""
    if request.method == "GET":
        userid = ""
        last_zone_name = ""
        if "userid" in session:
            userid = session["userid"]
        if "zone" in session:
            last_zone_name = session["zone"]
        return render_template(
            "user/login_basic.html.j2", userid=userid, last_zone_name=last_zone_name
        )
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        zone = request.form.get("irods_zone")

    # Redirect to the referer after logging in
    redirect_after_login = session.pop("redirect_after_login", url_for("index"))
    return authorize_irods_credentials(
        username,
        password,
        zone,
        irods_session_pool,
        app.config["irods_zones"],
        success=redirect(redirect_after_login),
    )


@user_bp.route("/user/logout")
def logout_basic():
    if "userid" in session:
        irods_session_pool.remove_irods_session(session["userid"])
        del session["password"]

    return redirect(url_for(app.config["MANGO_LOGIN_ACTION"]))
