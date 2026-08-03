import os
from flask import Blueprint, request, session, jsonify

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    pwd  = os.environ.get("ADMIN_PASSWORD", "botfarm2024")
    if data.get("password") == pwd:
        session["is_admin"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid password"}), 401


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("is_admin", None)
    return jsonify({"success": True})


@auth_bp.route("/status")
def status():
    return jsonify({"is_admin": bool(session.get("is_admin"))})
