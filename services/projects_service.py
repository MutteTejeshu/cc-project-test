import tempfile
import subprocess
import shutil
from pathlib import Path
from supabase_client import get_supabase
from services.scans_service import create_scan_request

from config import STORAGE_BUCKET, FILES_TABLE, PROJECTS_TABLE

supabase = get_supabase()

print(supabase.storage_url)


def parse_repo(project_id, repo_url):
    """Clone the repository and parse Python files for analysis."""
    temp_dir = tempfile.mkdtemp()

    error = False

    try:
        # Clone the repository
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)

        # Find all Python files
        python_files = list(Path(temp_dir).rglob("*.py"))

        if not python_files or len(python_files) == 0:
            print("No Python files found in the repository.")
            raise Exception("No Python files found in the repository.")

        for file in python_files:

            print(file)
            # Extract the folder and file path
            # folder_path = file.parent.relative_to(temp_dir)
            file_path = str(file.relative_to(temp_dir))
            file_name = file.name

            print(file_path, file_name)

            # Here you can add logic to analyze the Python files
            print(f"Found Python file: {file}")
            # For example, you can upload the file to Supabase storage
            storage_file_path = f"{project_id}/{file_path}"

            print(storage_file_path)

            with open(file, "rb") as file_obj:

                res = supabase.storage.from_(STORAGE_BUCKET).upload(
                    path=storage_file_path, file=file_obj
                )

            print(res)
            # if res.error:
            #     print(f"Error uploading file {file.name}: {res.error.message}")
            #     raise Exception(
            #         f"Error uploading file {file.name}: {res.error.message}"
            #     )

            loc = 0

            with file.open("r", encoding="utf-8") as f:
                loc = sum(1 for line in f if line.strip())

            # Add file metadata to the database - files table
            file_data = {
                "project_id": project_id,
                "file_name": file.name,
                "file_path": file_path,
                "file_type": "python",
                "loc": loc,
                "storage_path": storage_file_path,
            }

            print(f"File metadata: {file_data}")

            file_response = supabase.table(FILES_TABLE).insert(file_data).execute()

            # if file_response.error:
            #     print(f"Error inserting file metadata: {file_response.error.message}")
            #     raise Exception(
            #         f"Error inserting file metadata: {file_response.error.message}"
            #     )

        # raise Exception("Testing file upload failed.")

        # Update projects record with the number of files
        file_count = len(python_files)
        project_data = {
            "file_count": file_count,
        }
        project_response = (
            supabase.table(PROJECTS_TABLE)
            .update(project_data)
            .eq("id", project_id)
            .execute()
        )

        return True

    except Exception as e:
        print(f"Error parsing repository: {str(e)}")
        error = True

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

        if error:
            raise Exception("Error parsing repository.")


def create_project(user_id, repo_url):

    # Check if the project already exists
    existing_project = (
        supabase.table(PROJECTS_TABLE).select("*").eq("repo_url", repo_url).execute()
    )

    if existing_project.data:
        return "Project already exists.", True

    # Extract the project name from the repo URL
    project_name = repo_url.split("/")[-1].split(".")[0]

    # Create a new project in supabase
    project_data = {
        "name": project_name,
        "project_owner": user_id,
        "repo_url": repo_url,
    }

    response = supabase.table(PROJECTS_TABLE).insert(project_data).execute()

    if response.data:
        project_id = response.data[0]["id"]

        # Upload files to supabase storage

        try:
            # python_files = parse_repo(project_id=project_id, repo_url=repo_url)
            res = parse_repo(project_id=project_id, repo_url=repo_url)

            # Create initial scan request for the project
            scan_id, scan_error = create_scan_request(
                user_id=user_id, project_id=project_id
            )

            return project_id, False

        except Exception as e:
            print(f"Error uploading files: {str(e)}")

            # Delete folder from storage if any error occurs, loop through files and remove from storage
            # Get all files in the project folder
            files = (
                supabase.table(FILES_TABLE)
                .select("storage_path")
                .eq("project_id", project_id)
                .execute()
            )
            file_names = []
            for file in files.data:
                file_names.append(file["storage_path"])

            print(file_names)

            if file_names and len(file_names) > 0:
                supabase.storage.from_(STORAGE_BUCKET).remove(file_names)

            # Remove files from storage table if any error occurs
            supabase.table(FILES_TABLE).delete().eq("project_id", project_id).execute()

            # Remove project from projects table
            supabase.table(PROJECTS_TABLE).delete().eq("id", project_id).execute()

            return "Failed to create project.", True

    else:
        return "Failed to create project.", True


def get_project(user_id, project_id):
    """Get project details."""
    # Get project details
    project = (
        supabase.table(PROJECTS_TABLE)
        .select("*")
        .eq("id", project_id)
        .eq("project_owner", user_id)
        .execute()
    )

    if not project.data:
        return "Project not found.", True

    return project.data[0], False


def get_projects(user_id):
    """Get all projects for a user."""
    # Get all projects for the user
    projects = (
        supabase.table(PROJECTS_TABLE)
        .select("*")
        .eq("project_owner", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    if not projects.data:
        return [], False

    return projects.data, False
