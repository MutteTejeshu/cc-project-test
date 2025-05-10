from config import SCANS_TABLE, VULNERABILITIES_TABLE, CWE_TABLE
from services.scans_service import map_status
from supabase_client import get_supabase

supabase = get_supabase()


def get_scan_report(user_id, project_id, scan_id):

    # Validate the scan and project exists

    project_res = (
        supabase.table("projects")
        .select("*")
        .eq("id", project_id)
        .eq("project_owner", user_id)
        .execute()
    )

    project_res = project_res.data[0]

    scan_res = (
        supabase.table(SCANS_TABLE)
        .select("*")
        .eq("id", scan_id)
        .eq("project_id", project_id)
        .eq("scan_requested_by", user_id)
        .execute()
    )

    if scan_res.data is None or len(scan_res.data) == 0:
        return "Requested scan not found.", True

    scan_res = scan_res.data[0]

    vulns_res = (
        supabase.table(VULNERABILITIES_TABLE)
        .select(
            "id,scan_id,file_id,line_from,line_to,code,cwe_id,vuln_description,"
            "files(file_name,file_type,loc,file_path)"
        )
        .eq("scan_id", scan_id)
        .execute()
    )

    res = vulns_res.data

    # Join with CWE table to get the CWE details
    if res is not None and len(res) > 0:
        cwe_ids = [vuln["cwe_id"] for vuln in res]

        # print(cwe_ids)

        cwe_res = supabase.table(CWE_TABLE).select("*").in_("id", cwe_ids).execute()

        # Create a mapping of CWE ID to its details
        cwe_mapping = {str(cwe["id"]): cwe for cwe in cwe_res.data}

        # print(cwe_mapping)

        # Add CWE details to each vulnerability
        for vuln in res:
            vuln["cwe_details"] = cwe_mapping.get(vuln["cwe_id"])
            vuln["file_name"] = vuln["files"]["file_name"]
            vuln["file_type"] = vuln["files"]["file_type"]
            vuln["loc"] = vuln["files"]["loc"]
            vuln["file_path"] = vuln["files"]["file_path"]
            vuln.pop("files", None)

    response = {
        "scan_id": scan_id,
        "project_id": project_id,
        "project_name": project_res["name"],
        "scan_requested_by": user_id,
        "scanned_files_count": scan_res["scanned_files_count"],
        "total_vuln_count": scan_res["total_vuln_count"],
        "status": map_status(scan_res["status"]),
        "status_code": scan_res["status"],
        "duration": scan_res["duration_seconds"],
        "scan_requested_at": scan_res["modified_at"],
        "vulnerabilities": res,
    }

    return response, None
