from supabase_client import get_supabase
from config import STORAGE_BUCKET, PROJECTS_TABLE, FILES_TABLE

supabase = get_supabase()

# Upload a file to Supabase storage


def upload_file_to_supabase(project_id, file_path):
    """Upload a file to Supabase storage."""
    with open(file_path, "rb") as file:
        res = supabase.storage.from_(STORAGE_BUCKET).upload(
            f"{project_id}/setup.py", file
        )

        print(res)

        return res


def delete_project(project_id):

    # Remove project from projects table
    project = supabase.table(PROJECTS_TABLE).delete().eq("id", project_id).execute()

    print(project)

    print(project.data)

    return True


def delete_files_from_storage(project_id):
    """Delete files from Supabase storage."""
    # Get all files in the project folder
    # files = supabase.storage.from_(STORAGE_BUCKET).list(f"{project_id}/")

    # file_names = []

    # # Loop through files and remove from storage
    # for file in files:
    #     file_names.append(f"{project_id}/{file['name']}")

    # print(file_names)

    # res = supabase.storage.from_(STORAGE_BUCKET).remove(file_names)

    # print(res)
    # if res.error:
    #     print(f"Error deleting file: {res.error.message}")
    #     return False

    files = supabase.table(FILES_TABLE).select("storage_path").execute()

    file_names = []
    for file in files.data:
        file_names.append(file["storage_path"])

    print(file_names)

    return True


def delete_project_data(project_id):

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

    return True


if __name__ == "__main__":

    project_id = "e3e8a0e1-1631-4b3a-be10-b08db258c2ef"

    res = upload_file_to_supabase(project_id, "app.py")

    # res = delete_project("00000000-0000-0000-0000-000000000001")
    # res = delete_files_from_storage("cba326b1-0d94-4304-8798-85a6128c8009")
    # res = delete_project_data(project_id)

    print(res)
