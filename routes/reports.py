from flask import Blueprint, request, jsonify, g

from services.reports_service import (
    get_scan_report,
)
from routes.auth import token_required  # Import auth decorator
from datetime import datetime, timedelta

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@reports_bp.route("/", methods=["GET"])
@token_required
def get_scan_report_route():

    data = request.args
    user_id = g.current_user_profile.get("id")

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

    res, error = get_scan_report(
        user_id=user_id, project_id=project_id, scan_id=scan_id
    )

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
                "message": "Scan report fetched successfully.",
                "data": res,
            }
        ),
        201,
    )
