import boto3
import json
from supabase_client import get_supabase
from config import (
    PROJECTS_TABLE,
    SCANS_TABLE,
    SQS_QUEUE_URL,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)

supabase = get_supabase()
sqs = boto3.client(
    "sqs",
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


def create_scan_request(user_id, project_id):

    # Check if the project exists
    project = (
        supabase.table(PROJECTS_TABLE)
        .select("*")
        .eq("project_owner", user_id)
        .eq("id", project_id)
        .execute()
    )

    if not project.data:
        return "Project not found.", True

    request = {"project_id": project_id, "scan_requested_by": user_id, "status": 0}

    # Insert the scan request into the database
    response = supabase.table(SCANS_TABLE).insert(request).execute()

    if response.data:
        scan_id = response.data[0]["id"]

        # Add message to SQS queue
        message = {
            "scan_id": scan_id,
            "project_id": project_id,
        }
        res = sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message),
        )
        print(f"Message sent to SQS: {message}")
        print(res)
        # if res.error:
        #     print(f"Error sending message to SQS: {res.error.message}")
        #     return "Failed to send message to SQS.", True
        # else:
        #     print("Message sent to SQS successfully.")
        return scan_id, False

    else:
        return "Failed to create scan request.", True


def get_project_scan(user_id, project_id, scan_id):

    # Get scan details
    scan = (
        supabase.table(SCANS_TABLE)
        .select("*")
        .eq("id", scan_id)
        .eq("project_id", project_id)
        .eq("scan_requested_by", user_id)
        .execute()
    )

    if not scan.data:
        return "Scan not found.", True

    res = scan.data[0]

    res["status_code"] = res["status"]
    res["status"] = map_status(res["status"])

    return res, False


def get_project_scans(user_id, project_id):

    # Get scan details
    scans = (
        supabase.table(SCANS_TABLE)
        .select("*")
        .eq("project_id", project_id)
        .eq("scan_requested_by", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    if not scans.data:
        return [], False

    res = scans.data

    for scan in res:
        scan["status_code"] = scan["status"]
        scan["status"] = map_status(scan["status"])

    return res, False


def map_status(status_code):
    status_map = {
        0: "Pending",
        1: "In Progress",
        2: "In Progress",
        3: "Completed",
        -1: "Failed",
    }
    return status_map.get(status_code, "Unknown")
