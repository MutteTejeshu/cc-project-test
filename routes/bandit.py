from flask import Blueprint, request, jsonify, g

from services.bandit_service import process_bandit_request
from routes.auth import token_required  # Import auth decorator
from datetime import datetime, timedelta

bandit_bp = Blueprint("bandit", __name__, url_prefix="/api/bandit")


@bandit_bp.route("/", methods=["POST"])
# @token_required
def bandit_scan_route():
    data = request.get_json()
    # user_id = g.current_user_profile.get("id")

    if not data or "project_id" not in data or "scan_id" not in data:
        return (
            jsonify(
                {
                    "error": True,
                    "success": False,
                    "message": "Invalid request data.",
                    "data": None,
                }
            ),
            400,
        )

    project_id = data["project_id"]
    scan_id = data["scan_id"]

    res, error = process_bandit_request(project_id=project_id, scan_id=scan_id)

    if error:
        return (
            jsonify(
                {
                    "error": True,
                    "success": False,
                    "message": res,
                    "data": None,
                }
            ),
            400,
        )

    return (
        jsonify(
            {
                "error": False,
                "success": True,
                "message": "Project scan completed successfully.",
                "data": res,
            }
        ),
        200,
    )
