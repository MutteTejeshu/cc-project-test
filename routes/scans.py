from flask import Blueprint, request, jsonify, g

from services.scans_service import (
    create_scan_request,
    get_project_scan,
    get_project_scans,
)
from routes.auth import token_required  # Import auth decorator
from datetime import datetime, timedelta

scans_bp = Blueprint("scans", __name__, url_prefix="/api/scans")


@scans_bp.route("/", methods=["POST"])
@token_required
def create_scan_request_route():

    data = request.get_json()
    user_id = g.current_user_profile.get("id")

    if not data or "project_id" not in data:
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

    res, error = create_scan_request(user_id=user_id, project_id=project_id)

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
                "message": "Project scan created successfully.",
                "data": res,
            }
        ),
        201,
    )


# @scans_bp.route("/<string:scan_id>", methods=["GET"])
# @token_required
# def get_scan_route(scan_id):
#     user_id = g.current_user_profile.get("id")

#     if not scan_id:
#         return (
#             jsonify(
#                 {
#                     "error": True,
#                     "success": False,
#                     "message": "Scan ID is required.",
#                     "data": None,
#                 }
#             ),
#             400,
#         )

#     res, error = get_scan(user_id=user_id, scan_id=scan_id)

#     if error:
#         return (
#             jsonify(
#                 {
#                     "error": True,
#                     "success": False,
#                     "message": res,
#                     "data": None,
#                 }
#             ),
#             400,
#         )

#     return (
#         jsonify(
#             {
#                 "error": False,
#                 "success": True,
#                 "message": "Scan request retrieved successfully.",
#                 "data": res,
#             }
#         ),
#         200,
#     )


@scans_bp.route("/", methods=["GET"])
@token_required
def get_project_scans_route():
    user_id = g.current_user_profile.get("id")

    data = request.args

    project_id = data.get("project_id", None)

    if not project_id:
        return (
            jsonify(
                {
                    "error": True,
                    "success": False,
                    "message": "Project ID is required.",
                    "data": None,
                }
            ),
            400,
        )

    scan_id = data.get("scan_id", None)

    if not scan_id:
        res, error = get_project_scans(user_id=user_id, project_id=project_id)

    else:
        res, error = get_project_scan(
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
                "message": "Scan requests retrieved successfully.",
                "data": res,
            }
        ),
        200,
    )
