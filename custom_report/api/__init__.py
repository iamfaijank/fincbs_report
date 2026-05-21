import frappe
from frappe import _
import io
import os
import time
import tempfile
import shutil
import re
import csv
import json
import gzip
from datetime import datetime
from urllib.parse import quote
from custom_report.db_utils import get_pg_connection


# ============================================================================
# ANSI COLOR CODES FOR CONSOLE OUTPUT
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'


EXPORT_CACHE_PREFIX = "finacle_export"
EXPORT_CACHE_TTL_SECONDS = 60 * 60 * 12
EXPORT_FETCH_BATCH_SIZE = 500

# Global Admin Roles for consistent permission checks
ADMIN_ROLES = {"System Manager", "Finacle Report Admin", "Administrator"}

def get_department_roles():
    """Fetch department roles dynamically from Report Settings."""
    try:
        roles = frappe.get_all("Finacle Report User", 
            filters={"parent": "Report Settings", "parenttype": "Report Settings"}, 
            pluck="role")
        if roles:
            return set(roles)
    except Exception:
        pass
    
    # Minimal fallback to Admin roles if settings are not found
    return ADMIN_ROLES


class ReportExportCancelled(Exception):
    """Raised when user cancels a queued/running report export."""
    pass


# ============================================================================
# PUBLIC API METHODS
# ============================================================================


@frappe.whitelist()
def resolve_report_log(log_id):
    """
    Mark a failed Report Log as resolved and update status to Success.
    """
    if not log_id:
        frappe.throw(_("Log ID is required"))
    
    user_roles = set(frappe.get_roles())
    if not user_roles.intersection(ADMIN_ROLES):
        frappe.throw(_("You are not authorized to resolve report logs."))

    doc = frappe.get_doc("Report Log", log_id)
    if doc.status == "Success":
        frappe.msgprint(_("Log is already marked as Success."))
        return

    doc.status = "Success"
    doc.resolved = 1
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    
    return {"status": "success", "message": _("Log {0} has been resolved.").format(log_id)}


@frappe.whitelist()
def get_user_report_permissions():
    """
    Fetch user-specific report permissions.
    - Branch Report role: Returns sol_ids from Report Preference.
    - Department roles: Returns all sol_ids from 'Sahayog Branch' doctype.
    """
    user = frappe.session.user
    user_roles = set(frappe.get_roles())
    
    is_branch_user = "Branch Report" in user_roles
    is_dept_user = bool(user_roles.intersection(get_department_roles()))
    
    sol_data = [] # List of dicts: {"sol_id": "...", "branch_name": "..."}

    if is_branch_user and not is_dept_user:
        # Strict branch user - check preferences first
        pref_name = frappe.db.get_value("Report Preference", {"user": user}, "name")
        sol_ids = []
        if pref_name:
            doc = frappe.get_doc("Report Preference", pref_name)
            if hasattr(doc, "sol_id") and not isinstance(doc.sol_id, str):
                sol_ids = [d.sol_id for d in doc.sol_id if getattr(d, "sol_id", None)]
                sol_ids = list(set(sol_ids))
            else:
                sol_id_val = getattr(doc, "sol_id", None)
                if isinstance(sol_id_val, str):
                    sol_ids = [s.strip() for s in sol_id_val.split(",") if s.strip()]
        
        # USE CASE: If no Report Preference OR only one SOL ID is found, 
        # fallback to Employee doctype (single branch).
        if len(sol_ids) <= 1:
            employee_sol = frappe.db.get_value("Employee", {"user_id": user}, "sahayog_branch")
            if employee_sol:
                sol_ids = [employee_sol]
            elif not sol_ids:
                sol_ids = [] # Still empty if nothing in Employee either

        if sol_ids:
            # Fetch branch names for these sol_ids
            branches = frappe.get_all(
                "Sahayog Branch",
                filters={"name": ["in", sol_ids]},
                fields=["name as sol_id", "branch as branch_name"]
            )
            sol_data = branches
    
    elif is_dept_user:
        # Department user or Admin - show ALL sol_ids from Sahayog Branch doctype
        sol_data = frappe.get_all(
            "Sahayog Branch", 
            fields=["name as sol_id", "branch as branch_name"],
            order_by="name asc"
        )

    return {
        "is_branch_user": is_branch_user,
        "is_dept_user": is_dept_user,
        "sol_data": sol_data # Sorted by sol_id
    }


@frappe.whitelist()
def get_user_reports():
    """
    Fetch all reports accessible to the current user based on their roles.
    
    Returns:
        list: List of dictionaries containing report metadata including:
              - name: Report document name
              - report_name: Display name of the report
              - last_duration: Last download execution time
    """
    try:
        user_roles = set(frappe.get_roles())
        reports = frappe.get_all("Finacle Report", fields=["name", "report_name"])
        allowed_reports = []

        for report in reports:
            # Check if user has required role for this report
            if _user_has_report_access(report.name, user_roles):
                report_metadata = _get_report_metadata(report)
                allowed_reports.append(report_metadata)

        return allowed_reports

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="User Reports Error")
        return []


@frappe.whitelist()
def create_report_log_entry(report_docname, start_date=None, end_date=None, sol_id=None):
    """Create initial report log entry with queued status."""
    user = frappe.session.user
    manual_sol_id = _parse_manual_sol_id(sol_id)
    queue_position = _get_pending_report_count() + 1

    log_id = _log_report_download(
        report_docname=report_docname,
        user=user,
        start_date=start_date,
        end_date=end_date,
        manual_sol_id=manual_sol_id,
        status="Queued",
        queue_position=queue_position,
        log_message="Download requested by user."
    )

    return {"log_id": log_id, "queue_position": queue_position}


@frappe.whitelist()
def update_report_log_status(log_id, status, error_message=None, rows_fetched=None, file_size_mb=None):
    """Update status and metrics for a report log row."""
    if not log_id:
        frappe.throw(_("Log ID is required"))

    doc = frappe.get_doc("Report Log", log_id)
    user = frappe.session.user
    user_roles = set(frappe.get_roles())
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    
    if doc.employee != employee and not user_roles.intersection(ADMIN_ROLES):
        frappe.throw(_("You are not authorized to update this report log."))

    doc.status = status
    if error_message:
        doc.error_message = error_message
    if rows_fetched is not None:
        doc.rows_fetched = rows_fetched
    if file_size_mb is not None:
        doc.file_size_mb = file_size_mb
    if status in {"Success", "Failed", "Cancelled"}:
        doc.queue_position = 0
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "success"}


@frappe.whitelist()
def get_report_log_metrics(log_id):
    """Return queue/status metrics for a specific report log row."""
    if not log_id:
        frappe.throw(_("Log ID is required"))

    doc = frappe.get_doc("Report Log", log_id)
    user = frappe.session.user
    user_roles = set(frappe.get_roles())
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    
    if doc.employee != employee and not user_roles.intersection(ADMIN_ROLES):
        frappe.throw(_("You are not authorized to access this report log."))

    return {
        "status": doc.status,
        "queue_position": doc.queue_position,
        "rows_fetched": doc.rows_fetched or 0,
        "file_size_mb": doc.file_size_mb or 0,
    }


@frappe.whitelist()
def start_report_download(report_docname, start_date=None, end_date=None, file_type="csv", sol_id=None):
    """Queue an async report export and return request_id for polling."""
    user = frappe.session.user
    user_roles = set(frappe.get_roles())

    if not _user_has_report_access(report_docname, user_roles):
        frappe.throw(_("You are not authorized to access this report."))

    manual_sol_id = _parse_manual_sol_id(sol_id)
    request_id = frappe.generate_hash(length=16)
    queue_name = "short"

    _set_export_state(request_id, {
        "request_id": request_id,
        "user": user,
        "status": "queued",
        "message": f"Queued for processing ({queue_name})",
        "rows_processed": 0,
        "bytes_written": 0,
        "file_url": None,
        "download_url": None,
        "filename": None,
        "error": None,
        "cancel_requested": False,
    })

    frappe.enqueue(
        method=_run_report_export_job,
        queue=queue_name,
        timeout=60 * 60 * 4,
        job_name=f"finacle_export:{request_id}",
        request_id=request_id,
        user=user,
        report_docname=report_docname,
        start_date=start_date,
        end_date=end_date,
        file_type=file_type,
        manual_sol_id=manual_sol_id,
    )

    return {
        "status": "queued",
        "request_id": request_id,
    }


@frappe.whitelist()
def get_report_download_status(request_id):
    """Fetch current status for a queued/running/completed export."""
    state = _get_export_state(request_id)
    if not state:
        return {"status": "missing", "message": "Request not found or expired."}

    _ensure_export_access(state)

    return {
        "status": state.get("status"),
        "message": state.get("message"),
        "rows_processed": state.get("rows_processed", 0),
        "bytes_written": state.get("bytes_written", 0),
        "file_url": state.get("file_url"),
        "download_url": state.get("download_url"),
        "filename": state.get("filename"),
        "error": state.get("error"),
        "cancel_requested": bool(state.get("cancel_requested")),
        "updated_at": state.get("updated_at"),
    }


@frappe.whitelist()
def cancel_report_download(request_id):
    """Request cancellation for a queued/running export."""
    state = _get_export_state(request_id)
    if not state:
        return {"status": "missing", "message": "Request not found or expired."}

    _ensure_export_access(state)

    if state.get("status") in {"success", "failed", "cancelled"}:
        return {"status": state.get("status"), "message": state.get("message")}

    state["cancel_requested"] = True
    state["status"] = "cancel_requested"
    state["message"] = "Cancellation requested"
    _set_export_state(request_id, state)

    return {"status": "cancel_requested", "message": "Cancellation requested."}


@frappe.whitelist()
def download_report_file(request_id):
    """Download generated report file for the same user/admin using request_id."""
    from frappe.utils.response import send_private_file

    state = _get_export_state(request_id)
    if not state:
        frappe.throw(_("Download request not found or expired."))

    _ensure_export_access(state)

    if state.get("status") != "success" or not state.get("file_url"):
        frappe.throw(_("File is not ready for download."))

    file_url = state.get("file_url")
    if "/private" not in file_url:
        frappe.throw(_("Invalid file path."))

    relative_private_path = file_url.split("/private", 1)[1]
    absolute_path = frappe.get_site_path("private", relative_private_path.strip("/"))
    if not os.path.exists(absolute_path):
        frappe.throw(_("File wasn't available on site. Please regenerate the report."))

    return send_private_file(relative_private_path)


@frappe.whitelist()
def report_download(report_docname, start_date=None, end_date=None, file_type="csv", sol_id=None, log_id=None):
    """
    Download report data filtered by user's sol_id, date range, and SQL placeholders.
    
    Args:
        report_docname (str): Name of the Finacle Report document
        start_date (str, optional): Start date for filtering (YYYY-MM-DD format)
        end_date (str, optional): End date for filtering (YYYY-MM-DD format)
        file_type (str, optional): Output file type (default: 'csv')
        sol_id (str/list, optional): Manually selected sol_id(s) from frontend
    
    Returns:
        dict: Status response with filename on success
        
    Raises:
        frappe.ValidationError: If user doesn't have valid sol_id when required
    """
    try:
        # Initialize log buffer for this request
        frappe.local.report_log_buffer = []
        
        _print_header("REPORT DOWNLOAD STARTED")
        
        # Step 1: Get user context and fetch sol_id
        user = frappe.session.user
        user_roles = set(frappe.get_roles())
        
        _print_info(f"Session User: {user}")
        _print_info(f"User Roles: {', '.join(sorted(user_roles))}")
        
        # Parse manual sol_id if provided from frontend
        manual_sol_id = None
        if sol_id:
            if isinstance(sol_id, str):
                try:
                    # Attempt to parse as JSON list: '["1025", "1026"]'
                    manual_sol_id = json.loads(sol_id)
                except:
                    # Fallback to comma separated or single value: '1025,1026'
                    manual_sol_id = [s.strip() for s in sol_id.split(",") if s.strip()]
            elif isinstance(sol_id, list):
                manual_sol_id = sol_id
            
            # Final cleanup: Ensure all items are strings and not nested JSON strings
            if isinstance(manual_sol_id, list):
                cleaned_ids = []
                for s in manual_sol_id:
                    if isinstance(s, str):
                        # Fix for cases where a string might be doubly quoted or look like '["1025"]'
                        s = s.strip('[]"\' ')
                        if s: cleaned_ids.append(s)
                manual_sol_id = cleaned_ids

        # Step 1.1: Check if user has "Branch Report" role and get sol_id
        final_sol_id, is_branch_user = _get_user_sol_id_with_branch_check(user, user_roles, manual_sol_id)
        
        if is_branch_user:
            _print_success(f"Final Sol ID to use: {final_sol_id or 'None'}")
            _print_info(f"Branch Report User: YES ✓")
            _print_warning("⚠️  Sol ID filter will be applied to query")
        else:
            _print_info(f"Branch Report User: NO ✗")
            _print_success("ℹ️  No Sol ID filter will be applied (original query)")
        
        # Step 2: Fetch report configuration
        report_doc = frappe.get_doc("Finacle Report", report_docname)
        raw_sql = report_doc.sql_query.strip()

        if log_id:
            _log_report_download(
                report_docname=report_docname,
                user=user,
                start_date=start_date,
                end_date=end_date,
                manual_sol_id=manual_sol_id,
                status="Running",
                log_id=log_id,
                log_message="\n".join(getattr(frappe.local, "report_log_buffer", []))
            )
        
        # Step 3: Establish database connection
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Step 4: Apply Branch Report filter ONLY if user has "Branch Report" role
        if is_branch_user:
            filtered_sql, branch_filter_applied = _apply_branch_report_filter(
                raw_sql, final_sol_id, is_branch_user
            )
        else:
            # No modification - use original query
            filtered_sql = raw_sql
            branch_filter_applied = False

        filtered_sql = _escape_literal_percents_in_sql(filtered_sql)
        filtered_sql = _normalize_query_parameter_style(filtered_sql, start_date, end_date)
        
        # Step 5: Prepare query parameters for date range and sol_id
        query_params = _build_query_parameters(filtered_sql, start_date, end_date, final_sol_id)
        
        # Step 6: Display final SQL and parameters
        _print_sql_debug(filtered_sql, query_params, branch_filter_applied, is_branch_user)
        
        # Step 7: Execute query and stream CSV directly to file (faster, lower memory)
        frappe.log_error(message=filtered_sql, title="SQL Query Executed")
        _print_info("Executing query and generating CSV...")
        start_time = time.time()

        if query_params is None:
            query_params = {}

        normalized_file_type = _normalize_file_type(file_type)
        filename = _generate_filename(report_doc.report_name, normalized_file_type, start_date, end_date)
        temp_path = os.path.join(tempfile.gettempdir(), filename)

        if normalized_file_type == "csv.gz":
            rows_written = _write_csv_gzip_to_file(
                conn=conn,
                cursor=cursor,
                sql_query=filtered_sql,
                query_params=query_params,
                temp_path=temp_path,
            )
        else:
            rows_written = _write_csv_to_file(
                conn=conn,
                cursor=cursor,
                sql_query=filtered_sql,
                query_params=query_params,
                temp_path=temp_path,
            )
        execution_time = time.time() - start_time

        _print_success("CSV generated successfully!")
        _print_metric("Execution Time", f"{execution_time:.2f} seconds")
        if rows_written is not None:
            rows_per_sec = rows_written / execution_time if execution_time > 0 else 0
            _print_metric("Rows Written", f"{rows_written:,}")
            _print_metric("Performance", f"{rows_per_sec:.2f} rows/sec")
        else:
            _print_metric("Rows Written", "N/A (COPY fast path)")
            _print_metric("Performance", "N/A")
        
        # Step 10: Cleanup database connection
        cursor.close()
        conn.close()
        
        # Step 11: Serve file for download
        _prepare_file_download(temp_path, filename)
        
        # Step 12: Log the success
        _log_report_download(
            report_docname=report_docname,
            user=user,
            start_date=start_date,
            end_date=end_date,
            manual_sol_id=manual_sol_id,
            status="Success",
            log_id=log_id,
            rows_fetched=rows_written if rows_written is not None else _count_csv_data_rows(temp_path),
            file_size_mb=round((os.path.getsize(temp_path) / (1024 * 1024)), 2),
            log_message="\n".join(getattr(frappe.local, "report_log_buffer", []))
        )

        _print_success(f"File ready for download: {filename}")
        _print_footer("REPORT DOWNLOAD COMPLETED")
        
        return {"status": "success", "filename": filename}

    except Exception as e:
        _print_error(f"ERROR in report_download: {str(e)}")
        _print_footer("REPORT DOWNLOAD FAILED", success=False)
        
        # Log the failure
        try:
            _log_report_download(
                report_docname=report_docname,
                user=frappe.session.user,
                start_date=start_date,
                end_date=end_date,
                manual_sol_id=manual_sol_id,
                status="Failed",
                log_id=log_id,
                error_message=str(e),
                log_message="\n".join(getattr(frappe.local, "report_log_buffer", []))
            )
        except:
            pass

        frappe.log_error(
            message=f"Error in report_download: {str(e)}\n\n{frappe.get_traceback()}", 
            title="Report Download Error"
        )
        raise e


def _write_csv_to_file(conn, cursor, sql_query, query_params, temp_path):
    """
    Synchronous fast CSV writer.
    1) Try PostgreSQL COPY fast path (fastest)
    2) Fallback to fetchmany writer if COPY is not possible

    Returns:
        int | None: row count for fallback path, None for COPY fast path
    """
    execute_params = query_params or None
    try:
        rendered_sql = cursor.mogrify(sql_query, execute_params).decode() if execute_params is not None else sql_query
        rendered_sql = rendered_sql.strip().rstrip(";")
        copy_sql = f"COPY ({rendered_sql}) TO STDOUT WITH CSV HEADER"
        with open(temp_path, "w", encoding="utf-8", newline="") as out_file:
            cursor.copy_expert(copy_sql, out_file)
        return None
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

    cursor.execute(sql_query, execute_params)
    columns = [desc[0] for desc in cursor.description]
    rows_written = 0

    with open(temp_path, "w", encoding="utf-8", newline="") as out_file:
        writer = csv.writer(out_file)
        writer.writerow(columns)
        while True:
            rows = cursor.fetchmany(EXPORT_FETCH_BATCH_SIZE)
            if not rows:
                break
            writer.writerows(rows)
            rows_written += len(rows)

    return rows_written


def _write_csv_gzip_to_file(conn, cursor, sql_query, query_params, temp_path):
    """
    Fast gzip CSV writer for synchronous download.
    Returns:
        int | None: row count for fallback path, None for COPY fast path
    """
    execute_params = query_params or None
    try:
        rendered_sql = cursor.mogrify(sql_query, execute_params).decode() if execute_params is not None else sql_query
        rendered_sql = rendered_sql.strip().rstrip(";")
        copy_sql = f"COPY ({rendered_sql}) TO STDOUT WITH CSV HEADER"
        with gzip.open(temp_path, "wt", encoding="utf-8", newline="") as out_file:
            cursor.copy_expert(copy_sql, out_file)
        return None
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

    cursor.execute(sql_query, execute_params)
    columns = [desc[0] for desc in cursor.description]
    rows_written = 0

    with gzip.open(temp_path, "wt", encoding="utf-8", newline="") as out_file:
        writer = csv.writer(out_file)
        writer.writerow(columns)
        while True:
            rows = cursor.fetchmany(EXPORT_FETCH_BATCH_SIZE)
            if not rows:
                break
            writer.writerows(rows)
            rows_written += len(rows)

    return rows_written


def _run_report_export_job(request_id, user, report_docname, start_date=None, end_date=None, file_type="csv", manual_sol_id=None):
    """Background export job: stream DB rows in batches into a CSV file on disk."""
    cursor = None
    conn = None
    temp_path = None

    try:
        frappe.local.report_log_buffer = []
        _set_export_state(request_id, {
            **(_get_export_state(request_id) or {}),
            "status": "running",
            "message": "Preparing query...",
        })

        user_roles = set(frappe.get_roles(user))
        final_sol_id, is_branch_user = _get_user_sol_id_with_branch_check(user, user_roles, manual_sol_id)

        report_doc = frappe.get_doc("Finacle Report", report_docname)
        raw_sql = report_doc.sql_query.strip()

        conn = get_pg_connection()
        cursor = conn.cursor()

        if is_branch_user:
            filtered_sql, _ = _apply_branch_report_filter(raw_sql, final_sol_id, is_branch_user)
        else:
            filtered_sql = raw_sql

        filtered_sql = _escape_literal_percents_in_sql(filtered_sql)
        filtered_sql = _normalize_query_parameter_style(filtered_sql, start_date, end_date)

        query_params = _build_query_parameters(filtered_sql, start_date, end_date, final_sol_id) or {}

        start_time = time.time()
        _set_export_state(request_id, {
            **(_get_export_state(request_id) or {}),
            "status": "running",
            "message": "Executing query...",
        })
        cursor.execute(filtered_sql, query_params)

        # Some queries/cursor modes may not expose description on first pass.
        # Fallback to a regular cursor once before failing hard.
        if not cursor.description:
            cursor.close()
            cursor = conn.cursor()
            cursor.execute(filtered_sql, query_params)

        if not cursor.description:
            raise frappe.ValidationError(
                _("Report query did not return tabular rows. Please use a single SELECT query.")
            )

        columns = [desc[0] for desc in cursor.description]

        filename = _generate_filename(report_doc.report_name, file_type, start_date, end_date)
        temp_path = os.path.join(tempfile.gettempdir(), f"{request_id}_{filename}")

        rows_processed = 0

        with open(temp_path, "w", encoding="utf-8", newline="") as out_file:
            writer = csv.writer(out_file)
            writer.writerow(columns)
            _update_export_progress(request_id, rows_processed, temp_path)

            while True:
                if _is_export_cancel_requested(request_id):
                    raise ReportExportCancelled("Download cancelled by user.")

                rows = cursor.fetchmany(EXPORT_FETCH_BATCH_SIZE)
                if not rows:
                    break

                writer.writerows(rows)
                out_file.flush()
                rows_processed += len(rows)
                _update_export_progress(request_id, rows_processed, temp_path)

        _update_export_progress(request_id, rows_processed, temp_path)

        if _is_export_cancel_requested(request_id):
            raise ReportExportCancelled("Download cancelled by user.")

        execution_time = time.time() - start_time
        report_doc.db_set("last_download_duration", round(execution_time, 2), update_modified=False)

        stored_filename, file_url, download_url = _store_export_file(temp_path, request_id)
        temp_path = None

        _set_export_state(request_id, {
            **(_get_export_state(request_id) or {}),
            "status": "success",
            "message": "Download ready",
            "file_url": file_url,
            "download_url": download_url,
            "filename": stored_filename,
            "error": None,
        })

        _log_report_download(
            report_docname=report_docname,
            user=user,
            start_date=start_date,
            end_date=end_date,
            manual_sol_id=manual_sol_id,
            status="Success",
            log_message="\n".join(getattr(frappe.local, "report_log_buffer", []))
        )

    except ReportExportCancelled as e:
        _set_export_state(request_id, {
            **(_get_export_state(request_id) or {}),
            "status": "cancelled",
            "message": "Download cancelled",
            "error": str(e),
        })

    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Async Export Traceback ({report_docname})"
        )
        _set_export_state(request_id, {
            **(_get_export_state(request_id) or {}),
            "status": "failed",
            "message": "Download failed",
            "error": str(e),
        })

        try:
            _log_report_download(
                report_docname=report_docname,
                user=user,
                start_date=start_date,
                end_date=end_date,
                manual_sol_id=manual_sol_id,
                status="Failed",
                error_message=str(e),
                log_message="\n".join(getattr(frappe.local, "report_log_buffer", []))
            )
        except Exception:
            pass

        frappe.log_error(
            message=f"Error in async report export: {str(e)}\n\n{frappe.get_traceback()}",
            title="Async Report Export Error"
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def _log_report_download(
    report_docname,
    user,
    start_date,
    end_date,
    manual_sol_id,
    status,
    error_message=None,
    log_message=None,
    log_id=None,
    queue_position=None,
    rows_fetched=None,
    file_size_mb=None,
):
    """Create or update a Report Log row and return log id."""
    try:
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")

        if log_id and frappe.db.exists("Report Log", log_id):
            log = frappe.get_doc("Report Log", log_id)
            log.status = status
            log.error_message = error_message
            log.log_message = log_message
            if rows_fetched is not None:
                log.rows_fetched = rows_fetched
            if file_size_mb is not None:
                log.file_size_mb = file_size_mb
            if queue_position is not None:
                log.queue_position = queue_position
            if status in {"Success", "Failed", "Cancelled"}:
                log.queue_position = 0
            log.save(ignore_permissions=True)
        else:
            log = frappe.get_doc({
                "doctype": "Report Log",
                "report_name": report_docname,
                "employee": employee,
                "start_date": start_date,
                "end_date": end_date,
                "selected_sol_ids": json.dumps(manual_sol_id) if manual_sol_id else None,
                "date_time": frappe.utils.now_datetime(),
                "status": status,
                "queue_position": queue_position,
                "rows_fetched": rows_fetched,
                "file_size_mb": file_size_mb,
                "error_message": error_message,
                "log_message": log_message
            })
            log.insert(ignore_permissions=True)
        _refresh_report_log_queue_positions()
        frappe.db.commit()
        return log.name
    except Exception as log_err:
        frappe.log_error(message=f"Failed to create Report Log: {str(log_err)}", title="Report Log Error")
        return log_id


def _get_pending_report_count():
    return frappe.db.count("Report Log", {"status": ["in", ["Queued", "Running"]]})


def _refresh_report_log_queue_positions():
    pending_logs = frappe.get_all(
        "Report Log",
        filters={"status": ["in", ["Queued", "Running"]]},
        fields=["name"],
        order_by="date_time asc, name asc"
    )
    for idx, row in enumerate(pending_logs, start=1):
        frappe.db.set_value("Report Log", row.name, "queue_position", idx, update_modified=False)


def _count_csv_data_rows(file_path):
    """Count data rows (excluding header) for generated CSV file."""
    count = 0
    opener = gzip.open if file_path.lower().endswith(".gz") else open
    with opener(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return max(count - 1, 0)


def _normalize_file_type(file_type):
    ft = (file_type or "csv").strip().lower()
    if ft in {"csv.gz", "csv_gz", "gz"}:
        return "csv.gz"
    return "csv"


# ============================================================================
# PRIVATE HELPER METHODS - ASYNC EXPORT STATE
# ============================================================================


def _export_cache_key(request_id):
    return f"{EXPORT_CACHE_PREFIX}:{request_id}"


def _set_export_state(request_id, data):
    cache = frappe.cache()
    key = _export_cache_key(request_id)
    payload = dict(data or {})
    payload["updated_at"] = time.time()
    try:
        cache.set_value(key, payload, expires_in_sec=EXPORT_CACHE_TTL_SECONDS)
    except TypeError:
        cache.set_value(key, payload)


def _get_export_state(request_id):
    return frappe.cache().get_value(_export_cache_key(request_id))


def _ensure_export_access(state):
    user = frappe.session.user
    user_roles = set(frappe.get_roles())

    if state.get("user") != user and not user_roles.intersection(ADMIN_ROLES):
        frappe.throw(_("You are not authorized to access this export status."))


def _is_export_cancel_requested(request_id):
    state = _get_export_state(request_id) or {}
    return bool(state.get("cancel_requested"))


def _update_export_progress(request_id, rows_processed, temp_path):
    state = _get_export_state(request_id) or {}
    bytes_written = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
    if state.get("cancel_requested"):
        state.update({
            "status": "cancel_requested",
            "message": "Cancellation requested",
            "rows_processed": rows_processed,
            "bytes_written": bytes_written,
        })
        _set_export_state(request_id, state)
        return

    state.update({
        "status": "running",
        "message": f"Generating file... rows={rows_processed:,}, size={bytes_written:,} bytes",
        "rows_processed": rows_processed,
        "bytes_written": bytes_written,
    })
    _set_export_state(request_id, state)


def _parse_manual_sol_id(sol_id):
    manual_sol_id = None
    if not sol_id:
        return manual_sol_id

    if isinstance(sol_id, str):
        try:
            manual_sol_id = json.loads(sol_id)
        except Exception:
            manual_sol_id = [s.strip() for s in sol_id.split(",") if s.strip()]
    elif isinstance(sol_id, list):
        manual_sol_id = sol_id

    if isinstance(manual_sol_id, list):
        cleaned_ids = []
        for s in manual_sol_id:
            if isinstance(s, str):
                s = s.strip('[]"\' ')
                if s:
                    cleaned_ids.append(s)
        manual_sol_id = cleaned_ids

    return manual_sol_id


def _store_export_file(temp_path, request_id):
    original_filename = os.path.basename(temp_path).split("_", 1)[-1]
    stored_filename = f"{frappe.generate_hash(length=8)}_{original_filename}"
    file_url = f"/private/files/{stored_filename}"
    destination_path = frappe.get_site_path("private", "files", stored_filename)
    shutil.move(temp_path, destination_path)

    download_url = f"/api/method/custom_report.api.download_report_file?request_id={quote(request_id)}"
    return stored_filename, file_url, download_url


# ============================================================================
# PRIVATE HELPER METHODS - USER & ROLE MANAGEMENT
# ============================================================================


def _user_has_report_access(report_name, user_roles):
    """
    Check if user has access to a specific report based on assigned roles.
    
    Args:
        report_name (str): Name of the report document
        user_roles (set): Set of roles assigned to current user
    
    Returns:
        bool: True if user has access, False otherwise
    """
    roles = frappe.get_all(
        "Finacle Report User",
        filters={"parent": report_name},
        fields=["role"]
    )
    allowed_roles = [r.role for r in roles]
    return bool(user_roles.intersection(allowed_roles))


def _get_report_metadata(report):
    """
    Extract metadata from report document including last download duration.
    
    Args:
        report (dict): Report data containing name and report_name
    
    Returns:
        dict: Report metadata dictionary
    """
    report_doc = frappe.get_doc("Finacle Report", report.name)
    last_duration = getattr(report_doc, "last_download_duration", None)
    
    return {
        "name": report.name,
        "report_name": report.report_name,
        "last_duration": last_duration
    }


def _get_user_sol_id_with_branch_check(user, user_roles, manual_sol_id=None):
    """
    Retrieve sol_id for the user with branch-specific logic.
    - Branch Report role: Returns sol_ids from Report Preference (or manual selection from preferences).
    - Department roles: Returns manual selection (or None if all branches wanted).
    """
    sol_id = None
    is_branch_user = "Branch Report" in user_roles
    is_dept_user = bool(user_roles.intersection(get_department_roles()))

    try:
        _print_section_header("CHECKING USER ROLE & SOL_ID")
        
        # Scenario A: User is a Department User (sees all branches)
        if is_dept_user:
            _print_success("User is a Department/Admin user")
            # For department users, only apply filter if they manually select branches in sidebar
            if manual_sol_id:
                if isinstance(manual_sol_id, str):
                    manual_sol_id = [manual_sol_id]
                sol_id = manual_sol_id
                _print_info(f"Using manual sol_id selection: {', '.join(sol_id)}")
            else:
                sol_id = None # Do not apply any SOL ID filter (original query)
                _print_info("No manual filter selected - showing all branches")
            
            # For departments, is_branch_user logic for SQL filter should only trigger if sol_id is set
            is_branch_user = bool(sol_id) 

        # Scenario B: User is strictly a Branch User (Report Preference applies)
        elif is_branch_user:
            _print_success("User has 'Branch Report' role")
            
            # Fetch Report Preference for the user
            allowed_sol_ids = []
            pref_name = frappe.db.get_value("Report Preference", {"user": user}, "name")
            if pref_name:
                doc = frappe.get_doc("Report Preference", pref_name)
                if hasattr(doc, "sol_id") and not isinstance(doc.sol_id, str):
                    allowed_sol_ids = [d.sol_id for d in doc.sol_id if getattr(d, "sol_id", None)]
                    allowed_sol_ids = list(set(allowed_sol_ids))
                else:
                    sol_id_val = getattr(doc, "sol_id", None)
                    if isinstance(sol_id_val, str):
                        allowed_sol_ids = [s.strip() for s in sol_id_val.split(",") if s.strip()]

            # FALLBACK USE CASE: If no Report Preference OR only one SOL ID is found,
            # use the single branch from Employee doctype.
            if len(allowed_sol_ids) <= 1:
                _print_info("Report Preference has <= 1 SOL ID. Falling back to Employee doctype...")
                employee_sol = frappe.db.get_value("Employee", {"user_id": user}, "sahayog_branch")
                if employee_sol:
                    allowed_sol_ids = [employee_sol]
                    _print_success(f"Using branch from Employee record: {employee_sol}")

            # Use manual selection if provided, but validate against allowed list
            if manual_sol_id:
                if isinstance(manual_sol_id, str):
                    manual_sol_id = [manual_sol_id]
                sol_id = [s for s in manual_sol_id if s in allowed_sol_ids]
                _print_info(f"Using manual sol_id selection (validated): {', '.join(sol_id)}")
            else:
                sol_id = allowed_sol_ids
                if sol_id:
                    _print_success(f"Final sol_ids applied: {', '.join(sol_id)}")
                else:
                    _print_warning("No sol_id found in Report Preference or Employee")
            
            if not pref_name and len(allowed_sol_ids) == 0:
                _print_warning("Neither Report Preference nor Employee branch found for user")
            
            print()
            _print_highlight("BRANCH REPORT USER INFO:")
            _print_data("User", user)
            _print_data("Sol IDs to apply", ", ".join(sol_id) if sol_id else 'NOT FOUND')
            _print_data("Filter Applied", 'YES ✓' if sol_id else 'NO ✗')
            _print_data("Roles Count", len(user_roles))
            
            frappe.log_error(
                message=f"Branch Report User Check\nUser: {user}\nSol IDs: {sol_id}\nRoles: {', '.join(user_roles)}", 
                title="Branch User Sol IDs"
            )
            
        else:
            _print_info("User does NOT have 'Branch Report' or Department roles")
            _print_success("No sol_id filtering required - using original query")
            
            print()
            _print_highlight("STANDARD USER INFO:")
            _print_data("User", user)
            _print_data("Sol ID Filter", 'NOT APPLIED')
            _print_data("Query Modification", 'NONE (Original Query)')
            _print_data("Roles Count", len(user_roles))
        
        _print_section_footer()
            
    except Exception as e:
        _print_error(f"ERROR fetching sol_id for user {user}: {str(e)}")
        _print_section_footer()
        
        frappe.log_error(
            message=f"Sol ID Fetch Error\nUser: {user}\nError: {str(e)}\n\n{frappe.get_traceback()}", 
            title="Sol ID Error"
        )
    
    return sol_id, is_branch_user


# ============================================================================
# PRIVATE HELPER METHODS - SQL QUERY MANIPULATION
# ============================================================================

def _apply_branch_report_filter(sql_query, sol_id, is_branch_user):
    """
    Apply sol_id filter for Branch Report users ONLY.
    
    This function dynamically adds a WHERE condition to filter by sol_id
    ONLY if the user has the "Branch Report" role.
    
    Handles both simple queries and CTE-based queries correctly.
    
    Args:
        sql_query (str): Original SQL query
        sol_id (str or list): User's sol_id value(s) from Report Preference
        is_branch_user (bool): Whether user has Branch Report role
    
    Returns:
        tuple: (modified_sql, filter_applied)
            - modified_sql (str): SQL query with sol_id filter (if applicable)
            - filter_applied (bool): True if filter was added
    """
    # If not a branch user, return original query without modification
    if not is_branch_user:
        return sql_query, False
    
    # If branch user but no sol_id found, throw error
    if not sol_id:
        frappe.throw(
            "❌ You have 'Branch Report' role but no SOL IDs assigned in Report Preference. "
            "Please contact administrator."
        )
    
    # Check if query contains CTEs (WITH clause)
    # Ensure WITH is at depth 0
    has_cte = bool(_find_top_level_matches(r'^\s*WITH\s+', sql_query))
    
    if has_cte:
        # For CTE queries, find the main SELECT (after all CTEs)
        # Pattern: closing bracket followed by SELECT at depth 0
        cte_end_pattern = r'\)\s*\n?\s*SELECT'
        matches = _find_top_level_matches(cte_end_pattern, sql_query)
        
        if matches:
            # Get the last match - this is where main SELECT starts
            last_match = matches[-1]
            match_text = last_match.group(0)
            select_offset = match_text.upper().find("SELECT")
            split_pos = last_match.start() + select_offset
            
            # Split: CTE part + Main SELECT part
            cte_part = sql_query[:split_pos]
            main_part = sql_query[split_pos:]
            
            # Apply filter to main SELECT part only
            modified_main = _inject_sol_id_filter(main_part, sol_id)
            
            # Reconstruct full query
            modified_sql = cte_part + modified_main
            return modified_sql, True
    
    # For non-CTE queries, apply filter directly
    modified_sql = _inject_sol_id_filter(sql_query, sol_id)
    return modified_sql, True

def _get_nesting_level(text, position):
    """Calculate the parenthesis nesting level at a given position."""
    depth = 0
    for i in range(position):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
    return depth

def _find_top_level_matches(pattern, text, flags=re.IGNORECASE):
    """Find all regex matches that are at nesting level 0."""
    matches = list(re.finditer(pattern, text, flags=flags))
    return [m for m in matches if _get_nesting_level(text, m.start()) == 0]

def _inject_sol_id_filter(sql_segment, sol_id):
    """
    Inject sol_id filter into a SQL segment, handling UNIONs.
    """
    # Handle UNIONs at top level
    union_matches = _find_top_level_matches(r"\bUNION(\s+ALL)?\b", sql_segment)
    
    if union_matches:
        new_sql = ""
        last_pos = 0
        for m in union_matches:
            part = sql_segment[last_pos:m.start()]
            new_sql += _inject_sol_id_filter_single(part, sol_id) + " " + m.group(0) + " "
            last_pos = m.end()
        new_sql += _inject_sol_id_filter_single(sql_segment[last_pos:], sol_id)
        return new_sql
    else:
        return _inject_sol_id_filter_single(sql_segment, sol_id)

def _inject_sol_id_filter_single(sql_segment, sol_id):
    """
    Inject sol_id filter into the WHERE clause of a SINGLE SQL SELECT segment.
    """
    # Detect which table alias has sol_id column
    table_alias = _detect_sol_id_table_alias(sql_segment)
    
    # Build the filter condition
    if table_alias:
        condition_col = f"{table_alias}.sol_id"
    else:
        condition_col = "sol_id"

    if isinstance(sol_id, list):
        sol_id_condition = f"{condition_col} IN %(branch_sol_id)s"
    else:
        sol_id_condition = f"{condition_col} = %(branch_sol_id)s"
    
    # Find WHERE clause at top level
    top_wheres = _find_top_level_matches(r"\bWHERE\b", sql_segment)
    
    if top_wheres:
        # Multiple top-level WHEREs in a single segment shouldn't happen,
        # but if it does (e.g. malformed SQL), we inject into the first one.
        m = top_wheres[0]
        modified_sql = sql_segment[:m.end()] + f" ({sol_id_condition}) AND " + sql_segment[m.end():]
    else:
        # No top-level WHERE clause exists - add one before GROUP BY, ORDER BY, LIMIT, or at end
        inserted = False
        for keyword in [r"\bGROUP\s+BY\b", r"\bORDER\s+BY\b", r"\bLIMIT\b"]:
            top_keywords = _find_top_level_matches(keyword, sql_segment)
            if top_keywords:
                m = top_keywords[0]
                modified_sql = sql_segment[:m.start()] + f"WHERE {sol_id_condition} " + sql_segment[m.start():]
                inserted = True
                break
        
        if not inserted:
            # Add WHERE at the end, but before any trailing semicolon
            base_sql = sql_segment.strip()
            if base_sql.endswith(';'):
                modified_sql = f"{base_sql[:-1]} WHERE {sol_id_condition};"
            else:
                modified_sql = f"{base_sql} WHERE {sol_id_condition}"
    
    return modified_sql

def _detect_sol_id_table_alias(sql_segment):
    """
    Detect which table alias to use for sol_id filtering, looking only at top level.
    """
    # 1. Look for explicit sol_id usage at top level
    # (Matches g.sol_id where it's not in a subquery SELECT)
    matches = _find_top_level_matches(r'(\w+)\.sol_id', sql_segment)
    if matches:
        return matches[0].group(1)

    # 2. Look for known Finacle tables at top level
    matches = _find_top_level_matches(r'\b(?:FROM|JOIN)\s+(?:tbaadm\.)?(gam|smt|lad|acd)\s+(\w+)', sql_segment)
    if matches:
        return matches[0].group(2)
    
    # 3. Look for any table alias in top-level FROM clause
    matches = _find_top_level_matches(r'\bFROM\s+(?:\w+\.\w+|\w+|\([^)]+\))\s+(\w+)', sql_segment)
    if matches:
        alias = matches[0].group(1)
        if alias.upper() not in ('WHERE', 'GROUP', 'ORDER', 'LIMIT', 'JOIN', 'LEFT', 'INNER'):
            return alias

    # Default fallback to None if no match found
    return None


def _build_query_parameters(sql_query, start_date, end_date, sol_id):
    """
    Build parameter dictionary for SQL query execution.
    
    Args:
        sql_query (str): SQL query to check for placeholders
        start_date (str): Start date value
        end_date (str): End date value
        sol_id (str or list): User's sol_id value(s)
    
    Returns:
        dict: Dictionary of query parameters (never returns None)
    """
    params = {}
    
    # Add date parameters if placeholders exist in query
    if "%(start_date)s" in sql_query:
        params["start_date"] = start_date
    
    if "%(end_date)s" in sql_query:
        params["end_date"] = end_date
    
    # FIXED: Check for alternative date placeholder names
    if "%(tran_date)s" in sql_query:
        # Use start_date as tran_date if exists
        params["tran_date"] = start_date
    
    # Add branch sol_id parameter ONLY if placeholder exists
    if "%(branch_sol_id)s" in sql_query and sol_id:
        if isinstance(sol_id, list):
            params["branch_sol_id"] = tuple(sol_id)
        else:
            params["branch_sol_id"] = sol_id
    
    # Always return dictionary (empty if no params)
    return params


def _normalize_query_parameter_style(sql_query, start_date=None, end_date=None):
    """
    Normalize legacy positional placeholders to named placeholders for report exports.
    """
    named_pattern = r"%\([^)]+\)s"
    positional_pattern = r"(?<!%)%s"

    if not re.search(positional_pattern, sql_query) or not re.search(named_pattern, sql_query):
        return sql_query

    replacement_names = []
    if start_date is not None:
        replacement_names.append("start_date")
    if end_date is not None:
        replacement_names.append("end_date")

    positional_count = len(re.findall(positional_pattern, sql_query))
    if positional_count != len(replacement_names):
        frappe.throw(
            _("Report SQL mixes positional (%s) and named (%(key)s) parameters. Use named placeholders only.")
        )

    def replace_placeholder(_match):
        return f"%({replacement_names.pop(0)})s"

    return re.sub(positional_pattern, replace_placeholder, sql_query, count=positional_count)


def _escape_literal_percents_in_sql(sql_query):
    """
    Escape literal % characters for psycopg2 while preserving placeholders.
    """
    return re.sub(r"(?<!%)%(?!%|\([^)]+\)s|s)", "%%", sql_query)


# ============================================================================
# PRIVATE HELPER METHODS - FILE GENERATION & DOWNLOAD
# ============================================================================


def _generate_csv_content(columns, rows):
    """
    Generate CSV content from query results.
    
    Args:
        columns (list): List of column names
        rows (list): List of data rows
    
    Returns:
        str: CSV formatted string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    writer.writerows(rows)
    csv_data = output.getvalue()
    output.close()
    
    return csv_data


def _generate_filename(report_name, file_type, start_date=None, end_date=None):
    """
    Generate filename with report name, date filters (if any), and current timestamp.
    Format: report_name_START-DATE_to_END-DATE_DD-MM-YYYY HH-MM AM-PM.ext

    Args:
        report_name (str): Name of the report
        file_type (str): File extension (e.g., 'csv')
        start_date (str, optional): Start date in YYYY-MM-DD
        end_date (str, optional): End date in YYYY-MM-DD

    Returns:
        str: Generated filename with timestamp
    """
    # Get current datetime and format as DD-MM-YYYY HH-MM AM-PM
    current_time = datetime.now()

    # Format date as DD-MM-YYYY and time as HH-MM AM/PM
    date_str = current_time.strftime("%d-%m-%Y")  # DD-MM-YYYY
    time_str = current_time.strftime("%I-%M %p")  # HH-MM AM/PM
    formatted_datetime = f"{date_str} {time_str}"

    # Sanitize report name to remove invalid characters for filenames
    sanitized_report_name = re.sub(r'[<>:"/\\|?*]', '_', report_name)

    # Add date filters to filename if both are provided
    date_range = ""
    if start_date and end_date:
        try:
            # Convert YYYY-MM-DD to DD-MM-YYYY for filename
            s_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            e_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            date_range = f"_{s_date}_to_{e_date}"
        except (ValueError, TypeError):
            # Fallback if dates are not in expected format
            pass

    # Build filename: report_name_START-DATE_to_END-DATE_DD-MM-YYYY HH-MM AM.ext
    filename = f"{sanitized_report_name}{date_range}_{formatted_datetime}.{file_type}"

    return filename

def _save_temp_file(filename, content):
    """
    Save content to a temporary file.
    
    Args:
        filename (str): Name of the file
        content (str): File content to write
    
    Returns:
        str: Full path to temporary file
    """
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    with open(temp_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    
    return temp_path


def _prepare_file_download(temp_path, filename):
    """
    Prepare file for download by setting Frappe response attributes.
    
    Args:
        temp_path (str): Path to temporary file
        filename (str): Name for downloaded file
    """
    with open(temp_path, "rb") as f:
        filedata = f.read()
    
    frappe.local.response.filename = filename
    frappe.local.response.filecontent = filedata
    frappe.local.response.type = "download"


# ============================================================================
# UTILITY METHODS - COLORED CONSOLE PRINTING & LOGGING
# ============================================================================

def _log_process(message):
    """Internal log buffer for capturing process details."""
    if not hasattr(frappe.local, "report_log_buffer"):
        frappe.local.report_log_buffer = []
    
    # Strip ANSI colors for the database log
    clean_message = re.sub(r'\033\[[0-9;]*m', '', message)
    frappe.local.report_log_buffer.append(clean_message)

def _print_header(title):
    """Print formatted header for console output."""
    border = "=" * 80
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{border}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🚀 {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{border}{Colors.RESET}\n")
    _log_process(f"\n{border}\n🚀 {title}\n{border}\n")


def _print_footer(title, success=True):
    """Print formatted footer for console output."""
    color = Colors.BRIGHT_GREEN if success else Colors.BRIGHT_RED
    icon = "✅" if success else "❌"
    border = "=" * 80
    print(f"{Colors.BOLD}{color}{border}{Colors.RESET}")
    print(f"{Colors.BOLD}{color}{icon} {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{color}{border}{Colors.RESET}\n")
    _log_process(f"{border}\n{icon} {title}\n{border}\n")


def _print_section_header(title):
    """Print section header."""
    border = "─" * 80
    print(f"{Colors.BRIGHT_BLUE}{border}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_BLUE}🔐 {title}{Colors.RESET}")
    print(f"{Colors.BRIGHT_BLUE}{border}{Colors.RESET}")
    _log_process(f"{border}\n🔐 {title}\n{border}")


def _print_section_footer():
    """Print section footer."""
    border = "─" * 80
    print(f"{Colors.BRIGHT_BLUE}{border}{Colors.RESET}\n")
    _log_process(f"{border}\n")


def _print_success(message):
    """Print success message."""
    print(f"{Colors.BRIGHT_GREEN}✅ {message}{Colors.RESET}")
    _log_process(f"✅ {message}")


def _print_error(message):
    """Print error message."""
    print(f"{Colors.BRIGHT_RED}❌ {message}{Colors.RESET}")
    _log_process(f"❌ {message}")


def _print_warning(message):
    """Print warning message."""
    print(f"{Colors.BRIGHT_YELLOW}⚠️  {message}{Colors.RESET}")
    _log_process(f"⚠️  {message}")


def _print_info(message):
    """Print info message."""
    print(f"{Colors.BRIGHT_CYAN}ℹ️  {message}{Colors.RESET}")
    _log_process(f"ℹ️  {message}")


def _print_highlight(message):
    """Print highlighted message."""
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}📊 {message}{Colors.RESET}")
    _log_process(f"📊 {message}")


def _print_data(label, value):
    """Print data in key-value format."""
    print(f"{Colors.CYAN}   • {label}:{Colors.RESET} {Colors.WHITE}{value}{Colors.RESET}")
    _log_process(f"   • {label}: {value}")


def _print_metric(label, value):
    """Print performance metric."""
    print(f"{Colors.YELLOW}⏱️  {label}:{Colors.RESET} {Colors.BOLD}{Colors.WHITE}{value}{Colors.RESET}")
    _log_process(f"⏱️  {label}: {value}")


def _print_sql_debug(sql_query, params, filter_applied, is_branch_user):
    """
    Print SQL query and parameters in a formatted way.
    
    Args:
        sql_query (str): The SQL query to display
        params (dict): Query parameters
        filter_applied (bool): Whether Branch Report filter was applied
        is_branch_user (bool): Whether user has Branch Report role
    """
    border = "─" * 80
    print(f"{Colors.BRIGHT_MAGENTA}{border}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}📝 FINAL SQL QUERY{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}{border}{Colors.RESET}")
    
    _log_process(f"{border}\n📝 FINAL SQL QUERY\n{border}")

    if is_branch_user and filter_applied:
        print(f"{Colors.BRIGHT_GREEN}🔒 BRANCH REPORT FILTER APPLIED{Colors.RESET}")
        print(f"{Colors.GREEN}   → sol_id filter added to WHERE clause{Colors.RESET}")
        _log_process("🔒 BRANCH REPORT FILTER APPLIED\n   → sol_id filter added to WHERE clause")
    elif not is_branch_user:
        print(f"{Colors.BRIGHT_BLUE}ℹ️  NO FILTER APPLIED{Colors.RESET}")
        print(f"{Colors.BLUE}   → Using original query (user doesn't have Branch Report role){Colors.RESET}")
        _log_process("ℹ️  NO FILTER APPLIED\n   → Using original query (user doesn't have Branch Report role)")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}📄 Query:{Colors.RESET}")
    print(f"{Colors.WHITE}{sql_query}{Colors.RESET}")
    _log_process(f"\n📄 Query:\n{sql_query}")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}📊 Parameters:{Colors.RESET}")
    _log_process("\n📊 Parameters:")
    if params:
        for key, value in params.items():
            print(f"{Colors.YELLOW}   • {key}:{Colors.RESET} {Colors.WHITE}{value}{Colors.RESET}")
            _log_process(f"   • {key}: {value}")
    else:
        print(f"{Colors.YELLOW}   (No parameters){Colors.RESET}")
        _log_process("   (No parameters)")
    
    print(f"{Colors.BRIGHT_MAGENTA}{border}{Colors.RESET}\n")
    _log_process(f"{border}\n")
