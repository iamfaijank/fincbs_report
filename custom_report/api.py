import frappe
import io
import os
import time
import tempfile
import re
import csv
from datetime import datetime
from custom_report.db_utils import get_pg_connection


# ============================================================================
# PUBLIC API METHODS
# ============================================================================

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
        frappe.log_error(frappe.get_traceback(), "Error fetching user reports")
        return []


@frappe.whitelist()
def report_download(report_docname, start_date=None, end_date=None, file_type="csv"):
    """
    Download report data filtered by user's sol_id, date range, and SQL placeholders.
    
    Args:
        report_docname (str): Name of the Finacle Report document
        start_date (str, optional): Start date for filtering (YYYY-MM-DD format)
        end_date (str, optional): End date for filtering (YYYY-MM-DD format)
        file_type (str, optional): Output file type (default: 'csv')
    
    Returns:
        dict: Status response with filename on success
        
    Raises:
        frappe.ValidationError: If user doesn't have valid sol_id when required
    """
    try:
        # Step 1: Get user context and fetch sol_id
        user = frappe.session.user
        sol_id = _get_user_sol_id(user)
        
        # Step 2: Fetch report configuration
        report_doc = frappe.get_doc("Finacle Report", report_docname)
        raw_sql = report_doc.sql_query.strip()
        
        # Step 3: Establish database connection
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Step 4: Check if query result contains sol_id column
        has_sol_id_column = _check_sol_id_column_exists(cursor, raw_sql)
        
        # Step 5: Apply sol_id filter if applicable
        filtered_sql = _apply_sol_id_filter(raw_sql, sol_id, has_sol_id_column)
        
        # Step 6: Prepare query parameters for date range and sol_id
        query_params = _build_query_parameters(filtered_sql, start_date, end_date, sol_id)
        
        # Step 7: Execute SQL query and fetch results
        frappe.log_error(filtered_sql, "Final SQL Executed")
        cursor.execute(filtered_sql, query_params if query_params else None)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        # Step 8: Generate CSV file content
        csv_data = _generate_csv_content(columns, rows)
        
        # Step 9: Save file temporarily and prepare download
        filename = _generate_filename(report_doc.report_name, file_type)
        temp_path = _save_temp_file(filename, csv_data)
        
        # Step 10: Cleanup database connection
        cursor.close()
        conn.close()
        
        # Step 11: Serve file for download
        _prepare_file_download(temp_path, filename)
        
        return {"status": "success", "filename": filename}

    except Exception as e:
        frappe.log_error(f"Error in report_download: {str(e)}", "report_download")
        raise e


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


def _get_user_sol_id(user):
    """
    Retrieve sol_id associated with the given user.
    
    Args:
        user (str): Username/email of the user
    
    Returns:
        str or None: sol_id if exists, None otherwise
    """
    sol_id = None
    try:
        sol_id = frappe.db.get_value("User", user, "sol_id")
    except Exception as e:
        frappe.log_error(
            f"sol_id column not found in User table: {str(e)}", 
            "report_download"
        )
    return sol_id


# ============================================================================
# PRIVATE HELPER METHODS - SQL QUERY MANIPULATION
# ============================================================================

def _check_sol_id_column_exists(cursor, sql_query):
    """
    Check if the SQL query result contains a sol_id column.
    
    Args:
        cursor: Database cursor object
        sql_query (str): SQL query to check
    
    Returns:
        bool: True if sol_id column exists, False otherwise
    """
    has_sol_id_column = False
    try:
        # Execute preview query to get column names
        preview_sql = f"SELECT * FROM ({sql_query}) AS subq LIMIT 1"
        cursor.execute(preview_sql)
        colnames = [desc[0].lower() for desc in cursor.description]
        has_sol_id_column = "sol_id" in colnames
    except Exception as e:
        has_sol_id_column = False
        cursor.connection.rollback()
        frappe.log_error(f"Preview check failed: {str(e)}", "report_download")
    
    return has_sol_id_column


def _apply_sol_id_filter(sql_query, sol_id, has_sol_id_column):
    """
    Apply sol_id filter to SQL query if applicable.
    
    Args:
        sql_query (str): Original SQL query
        sol_id (str): User's sol_id value
        has_sol_id_column (bool): Whether query result has sol_id column
    
    Returns:
        str: Modified SQL query with sol_id filter
        
    Raises:
        frappe.ValidationError: If sol_id is required but not available
    """
    if not has_sol_id_column:
        return sql_query
    
    # If query has sol_id column but user doesn't have sol_id, deny access
    if not sol_id:
        frappe.throw("❌ You don't have a valid sol_id assigned. Access denied.")
    
    # Add sol_id filter to WHERE clause
    if re.search(r"\bwhere\b", sql_query, flags=re.IGNORECASE):
        sql_query = f"{sql_query} AND sol_id = %(sol_id)s"
    else:
        sql_query = f"{sql_query} WHERE sol_id = %(sol_id)s"
    
    return sql_query


def _build_query_parameters(sql_query, start_date, end_date, sol_id):
    """
    Build parameter dictionary for SQL query execution.
    
    Args:
        sql_query (str): SQL query to check for placeholders
        start_date (str): Start date value
        end_date (str): End date value
        sol_id (str): User's sol_id value
    
    Returns:
        dict: Dictionary of query parameters, or None if no parameters needed
    """
    params = {}
    
    # Add date parameters if placeholders exist in query
    if "%(start_date)s" in sql_query or "%(end_date)s" in sql_query:
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    # Add sol_id parameter if placeholder exists
    if "%(sol_id)s" in sql_query and sol_id:
        params["sol_id"] = sol_id
    
    return params if params else None


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


def _generate_filename(report_name, file_type):
    """
    Generate filename with report name and current timestamp.
    Format: report_name_DD-MM-YYYY HH-MM AM-PM.ext
    
    Args:
        report_name (str): Name of the report
        file_type (str): File extension (e.g., 'csv')
    
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
    
    # Build filename: report_name_DD-MM-YYYY HH-MM AM.ext
    filename = f"{sanitized_report_name}_{formatted_datetime}.{file_type}"
    
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
