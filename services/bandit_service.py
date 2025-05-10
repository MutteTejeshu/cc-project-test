import os
import logging
import tempfile
import subprocess
import json
import time
from datetime import datetime
from supabase_client import get_supabase
from config import FILES_TABLE, STORAGE_BUCKET, VULNERABILITIES_TABLE, SCANS_TABLE

supabase = get_supabase()

logger = logging.getLogger(__name__)


def process_bandit_request(project_id, scan_id):

    files = get_files_by_project(project_id)

    if not files:
        update_scan_status(
            scan_id=scan_id,
            status=-1,
        )

        return "No files found", True

    scan_files(scan_id=scan_id, project_id=project_id, files=files)

    return "Scan completed", False


def get_files_by_project(project_id):
    """Get all files for a project"""
    try:

        print("Fetching files for project:", project_id)
        response = (
            supabase.table(FILES_TABLE)
            .select("*")
            .eq("project_id", project_id)
            .execute()
        )

        return response.data
    except Exception as e:
        logger.error(f"Error fetching files: {str(e)}")
        return []


def update_scan_status(scan_id, status, stats=None):
    """Update scan status and stats"""
    try:
        update_data = {"status": status, "modified_at": datetime.now().isoformat()}

        if stats:
            update_data.update(stats)

        supabase.table(SCANS_TABLE).update(update_data).eq("id", scan_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error updating scan status: {str(e)}")
        return False


def scan_files(scan_id, project_id, files):
    """Scan files for vulnerabilities"""

    start_time = time.time()

    # Process Python files
    files_processed = 0
    total_vulnerabilities = 0

    if files:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(
            f"Found {len(files)} files in the database for project {project_id}"
        )
        # Process each file
        for file in files:
            file_id = file.get("id", None)
            file_path = file.get("storage_path", None)
            if file_path:

                local_file_path = download_file_from_supabase(file_path, temp_dir)

                logger.info(f"Processing downloaded file: {local_file_path}")

                file_count, vuln_count = scan_file_for_vulnerabilities(
                    file_path=local_file_path, file_id=file_id, scan_id=scan_id
                )

                files_processed += file_count
                total_vulnerabilities += vuln_count

            else:
                logger.warning(f"File path not found for file: {file}")

    # Update scan record with final statistics
    end_time = time.time()
    duration = round(end_time - start_time, 2)

    update_scan_status(
        scan_id=scan_id,
        status=2,
        stats={
            "scanned_files_count": files_processed,
            "total_vuln_count": total_vulnerabilities,
            "duration_seconds": duration,
        },
    )

    logger.info(
        f"Scan completed. Files processed: {files_processed}, Vulnerabilities found: {total_vulnerabilities}"
    )

    return True


def download_file_from_supabase(file_key, output_dir):
    """
    Download a file from Supabase storage to a local directory

    Args:
        file_key (str): The key/path of the file in the bucket
        output_dir (str): Directory where the file should be saved
        bucket_name (str): Name of the storage bucket, defaults to "files"

    Returns:
        str: Path to the downloaded file, or None if download failed
    """
    try:
        logger.info(f"Downloading file '{file_key}' from bucket '{STORAGE_BUCKET}'")

        # Get storage client for the specified bucket
        storage = supabase.storage.from_(STORAGE_BUCKET)

        # Normalize file path to use as local filename
        local_filename = os.path.basename(file_key)
        output_path = os.path.join(output_dir, local_filename)

        # Download the file
        with open(output_path, "wb+") as f:
            # Get the file data
            res = storage.download(file_key)
            # Write to the local file
            f.write(res)

        logger.info(f"Successfully downloaded file to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error downloading file '{file_key}' from storage: {str(e)}")
        return None


def scan_file_for_vulnerabilities(file_path, file_id, scan_id):
    """Process a single file and scan it for vulnerabilities"""
    try:

        # Run Bandit scan on the file
        logger.info(f"Scanning file: {file_path}")
        scan_result = run_bandit_scan(file_path)

        vulnerabilities_count = 0

        if scan_result["success"] and "report" in scan_result:
            # Process vulnerabilities
            if "results" in scan_result["report"]:
                vulnerabilities = []

                for result in scan_result["report"]["results"]:

                    print(result)

                    vuln_data = {
                        "scan_id": scan_id,
                        "file_id": file_id,
                        "bandit_test_id": result.get("test_id", "unknown"),
                        "vuln_description": result.get("issue_text", ""),
                        "severity": result.get("issue_severity", "LOW"),
                        "confidence": result.get("issue_confidence", "LOW"),
                        "line_from": result.get("line_range", [])[0],
                        "line_to": result.get("line_range", [])[-1],
                        "code": result.get("code", ""),
                        "cwe_id": result.get("issue_cwe", {}).get("id", ""),
                    }
                    vulnerabilities.append(vuln_data)

                # Store vulnerabilities
                if vulnerabilities:
                    result = store_vulnerability_records(vulnerabilities)
                    if result:
                        vulnerabilities_count = len(vulnerabilities)
                        logger.info(
                            f"Added {vulnerabilities_count} vulnerabilities for {file_id}"
                        )
                    else:
                        logger.error(f"Failed to insert vulnerabilities for {file_id}")
        else:
            logger.warning(
                f"Scan failed for {file_path}: {scan_result.get('error', 'Unknown error')}"
            )

        return 1, vulnerabilities_count

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return 0, 0


def run_bandit_scan(file_path):
    """Run Bandit security scan on a file"""
    try:
        # Set up a temporary file for output
        output_file = tempfile.mktemp(suffix=".json")

        # Run Bandit as a subprocess
        cmd = ["bandit", "-f", "json", "-o", output_file, file_path]

        process = subprocess.run(cmd, capture_output=True, text=True)

        # Check if the scan completed successfully
        if process.returncode not in [0, 1]:  # 0: no issues, 1: issues found
            return {"success": False, "error": f"Bandit scan failed: {process.stderr}"}

        # Read and parse the JSON report
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                report = json.load(f)

            # Clean up
            os.remove(output_file)

            return {"success": True, "report": report}
        else:
            return {"success": False, "error": "Failed to generate report"}

    except Exception as e:
        logger.error(f"Error in Bandit scan: {str(e)}")
        return {"success": False, "error": str(e)}


def store_vulnerability_records(vulnerabilities):
    """Store vulnerability records in the database"""
    try:
        if not vulnerabilities:
            return True

        print(vulnerabilities)

        result = supabase.table(VULNERABILITIES_TABLE).insert(vulnerabilities).execute()
        return bool(result.data)
    except Exception as e:
        logger.error(f"Error storing vulnerability records: {str(e)}")
        return False
