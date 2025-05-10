from flask import Blueprint, request, jsonify, g

from services.projects_service import create_project, get_project, get_projects
from routes.auth import token_required  # Import auth decorator
from datetime import datetime, timedelta

projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


@projects_bp.route("/", methods=["POST"])
@token_required
def add_project_route():

    data = request.get_json()
    user_id = g.current_user_profile.get("id")

    if not data or "repo_url" not in data:
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

    repo_url = data["repo_url"]

    # Validate the repo_url format - Should be like https://github.com/...
    if not repo_url.startswith("https://github.com/"):
        return (
            jsonify(
                {
                    "error": True,
                    "success": False,
                    "message": "Invalid repo_url format.",
                    "data": None,
                }
            ),
            400,
        )

    res, error = create_project(user_id=user_id, repo_url=repo_url)

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
                "message": "Project created successfully.",
                "data": res,
            }
        ),
        201,
    )


@projects_bp.route("/<string:project_id>", methods=["GET"])
@token_required
def get_project_route(project_id):

    user_id = g.current_user_profile.get("id")

    print(project_id)

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

    res, error = get_project(user_id=user_id, project_id=project_id)

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
                "message": "Project fetched successfully.",
                "data": res,
            }
        ),
        200,
    )


@projects_bp.route("/", methods=["GET"])
@token_required
def get_all_projects_route():

    user_id = g.current_user_profile.get("id")

    res, error = get_projects(user_id=user_id)

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
                "message": "Projects fetched successfully.",
                "data": res,
            }
        ),
        200,
    )

    return (
        jsonify(
            {
                "error": False,
                "success": True,
                "message": "Projects fetched successfully.",
                "data": None,
            }
        ),
        200,
    )
