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
        frappe.log_error(message=frappe.get_traceback(), title="User Reports Error")
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
        _print_header("REPORT DOWNLOAD STARTED")
        
        # Step 1: Get user context and fetch sol_id
        user = frappe.session.user
        user_roles = set(frappe.get_roles())
        
        _print_info(f"Session User: {user}")
        _print_info(f"User Roles: {', '.join(sorted(user_roles))}")
        
        # Step 1.1: Check if user has "Branch Report" role and get sol_id
        sol_id, is_branch_user = _get_user_sol_id_with_branch_check(user, user_roles)
        
        if is_branch_user:
            _print_success(f"Final Sol ID to use: {sol_id or 'None'}")
            _print_info(f"Branch Report User: YES ✓")
            _print_warning("⚠️  Sol ID filter will be applied to query")
        else:
            _print_info(f"Branch Report User: NO ✗")
            _print_success("ℹ️  No Sol ID filter will be applied (original query)")
        
        # Step 2: Fetch report configuration
        report_doc = frappe.get_doc("Finacle Report", report_docname)
        raw_sql = report_doc.sql_query.strip()
        
        # Step 3: Establish database connection
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Step 4: Apply Branch Report filter ONLY if user has "Branch Report" role
        if is_branch_user:
            filtered_sql, branch_filter_applied = _apply_branch_report_filter(
                raw_sql, sol_id, is_branch_user
            )
        else:
            # No modification - use original query
            filtered_sql = raw_sql
            branch_filter_applied = False
        
        # Step 5: Prepare query parameters for date range and sol_id
        query_params = _build_query_parameters(filtered_sql, start_date, end_date, sol_id)
        
        # Step 6: Display final SQL and parameters
        _print_sql_debug(filtered_sql, query_params, branch_filter_applied, is_branch_user)
        
        # Step 7: Execute SQL query and fetch results
        frappe.log_error(message=filtered_sql, title="SQL Query Executed")
        
        _print_info("Executing query...")
        start_time = time.time()
        
        # FIXED: Handle parameters correctly to avoid syntax error
        if query_params:
            cursor.execute(filtered_sql, query_params)
        else:
            cursor.execute(filtered_sql)
        
        rows = cursor.fetchall()
        execution_time = time.time() - start_time
        
        columns = [desc[0] for desc in cursor.description]
        
        # Calculate performance metrics
        rows_per_sec = len(rows) / execution_time if execution_time > 0 else 0
        
        print()
        _print_success("Query executed successfully!")
        _print_metric("Execution Time", f"{execution_time:.2f} seconds")
        _print_metric("Rows Fetched", f"{len(rows):,}")
        _print_metric("Columns", f"{len(columns)}")
        _print_metric("Performance", f"{rows_per_sec:.2f} rows/sec")
        
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
        
        print()
        _print_success(f"File ready for download: {filename}")
        _print_footer("REPORT DOWNLOAD COMPLETED")
        
        return {"status": "success", "filename": filename}

    except Exception as e:
        print()
        _print_error(f"ERROR in report_download: {str(e)}")
        _print_footer("REPORT DOWNLOAD FAILED", success=False)
        
        frappe.log_error(
            message=f"Error in report_download: {str(e)}\n\n{frappe.get_traceback()}", 
            title="Report Download Error"
        )
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


def _get_user_sol_id_with_branch_check(user, user_roles):
    """
    Retrieve sol_id for the user with branch-specific logic.
    
    If user has "Branch Report" role, fetch sahayog_branch from Employee doctype.
    Otherwise, return None (no filtering needed).
    
    Args:
        user (str): Username/email of the user
        user_roles (set): Set of roles assigned to current user
    
    Returns:
        tuple: (sol_id, is_branch_user)
            - sol_id (str or None): sol_id value to use for filtering
            - is_branch_user (bool): True if user has Branch Report role
    """
    sol_id = None
    is_branch_user = False
    
    try:
        _print_section_header("CHECKING USER ROLE & SOL_ID")
        
        # Check if user has "Branch Report" role
        if "Branch Report" in user_roles:
            is_branch_user = True
            _print_success("User has 'Branch Report' role")
            _print_info("Fetching 'sahayog_branch' from Employee doctype...")
            
            # Fetch sahayog_branch from Employee doctype linked to this user
            sol_id = frappe.db.get_value(
                "Employee", 
                {"user_id": user}, 
                "sahayog_branch"
            )
            
            if sol_id:
                _print_success(f"Found sahayog_branch: {sol_id}")
            else:
                _print_warning("sahayog_branch NOT FOUND in Employee doctype")
            
            print()
            _print_highlight("BRANCH REPORT USER INFO:")
            _print_data("User", user)
            _print_data("Sol ID (Employee.sahayog_branch)", sol_id or 'NOT FOUND')
            _print_data("Filter Applied", 'YES ✓' if sol_id else 'NO ✗')
            _print_data("Roles Count", len(user_roles))
            
            frappe.log_error(
                message=f"Branch Report User Check\nUser: {user}\nSol ID: {sol_id}\nRoles: {', '.join(user_roles)}", 
                title="Branch User Sol ID"
            )
            
        else:
            _print_info("User does NOT have 'Branch Report' role")
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
    
    Args:
        sql_query (str): Original SQL query
        sol_id (str): User's sol_id value from Employee.sahayog_branch
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
            "❌ You have 'Branch Report' role but no sahayog_branch assigned in Employee record. "
            "Please contact administrator."
        )
    
    # Add sol_id filter to WHERE clause (safe parameterized approach)
    # Check if query already has WHERE clause
    if re.search(r"\bwhere\b", sql_query, flags=re.IGNORECASE):
        # Find the position of WHERE clause and add condition after it
        modified_sql = re.sub(
            r"(\bwhere\b)",
            r"\1 g.sol_id = %(branch_sol_id)s AND",
            sql_query,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        # No WHERE clause exists, add one
        # Find the position before ORDER BY, LIMIT, or end of query
        if re.search(r"\border\s+by\b", sql_query, flags=re.IGNORECASE):
            modified_sql = re.sub(
                r"(\border\s+by\b)",
                r"WHERE g.sol_id = %(branch_sol_id)s \1",
                sql_query,
                count=1,
                flags=re.IGNORECASE
            )
        elif re.search(r"\blimit\b", sql_query, flags=re.IGNORECASE):
            modified_sql = re.sub(
                r"(\blimit\b)",
                r"WHERE g.sol_id = %(branch_sol_id)s \1",
                sql_query,
                count=1,
                flags=re.IGNORECASE
            )
        else:
            # Add WHERE at the end
            modified_sql = f"{sql_query.rstrip(';')} WHERE g.sol_id = %(branch_sol_id)s"
    
    return modified_sql, True


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
    if "%(start_date)s" in sql_query:
        params["start_date"] = start_date
    
    if "%(end_date)s" in sql_query:
        params["end_date"] = end_date
    
    # Add branch sol_id parameter ONLY if placeholder exists
    if "%(branch_sol_id)s" in sql_query and sol_id:
        params["branch_sol_id"] = sol_id
    
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


# ============================================================================
# UTILITY METHODS - COLORED CONSOLE PRINTING
# ============================================================================


def _print_header(title):
    """Print formatted header for console output."""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🚀 {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'=' * 80}{Colors.RESET}\n")


def _print_footer(title, success=True):
    """Print formatted footer for console output."""
    color = Colors.BRIGHT_GREEN if success else Colors.BRIGHT_RED
    icon = "✅" if success else "❌"
    print(f"{Colors.BOLD}{color}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{color}{icon} {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{color}{'=' * 80}{Colors.RESET}\n")


def _print_section_header(title):
    """Print section header."""
    print(f"{Colors.BRIGHT_BLUE}{'─' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_BLUE}🔐 {title}{Colors.RESET}")
    print(f"{Colors.BRIGHT_BLUE}{'─' * 80}{Colors.RESET}")


def _print_section_footer():
    """Print section footer."""
    print(f"{Colors.BRIGHT_BLUE}{'─' * 80}{Colors.RESET}\n")


def _print_success(message):
    """Print success message."""
    print(f"{Colors.BRIGHT_GREEN}✅ {message}{Colors.RESET}")


def _print_error(message):
    """Print error message."""
    print(f"{Colors.BRIGHT_RED}❌ {message}{Colors.RESET}")


def _print_warning(message):
    """Print warning message."""
    print(f"{Colors.BRIGHT_YELLOW}⚠️  {message}{Colors.RESET}")


def _print_info(message):
    """Print info message."""
    print(f"{Colors.BRIGHT_CYAN}ℹ️  {message}{Colors.RESET}")


def _print_highlight(message):
    """Print highlighted message."""
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}📊 {message}{Colors.RESET}")


def _print_data(label, value):
    """Print data in key-value format."""
    print(f"{Colors.CYAN}   • {label}:{Colors.RESET} {Colors.WHITE}{value}{Colors.RESET}")


def _print_metric(label, value):
    """Print performance metric."""
    print(f"{Colors.YELLOW}⏱️  {label}:{Colors.RESET} {Colors.BOLD}{Colors.WHITE}{value}{Colors.RESET}")


def _print_sql_debug(sql_query, params, filter_applied, is_branch_user):
    """
    Print SQL query and parameters in a formatted way.
    
    Args:
        sql_query (str): The SQL query to display
        params (dict): Query parameters
        filter_applied (bool): Whether Branch Report filter was applied
        is_branch_user (bool): Whether user has Branch Report role
    """
    print(f"{Colors.BRIGHT_MAGENTA}{'─' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}📝 FINAL SQL QUERY{Colors.RESET}")
    print(f"{Colors.BRIGHT_MAGENTA}{'─' * 80}{Colors.RESET}")
    
    if is_branch_user and filter_applied:
        print(f"{Colors.BRIGHT_GREEN}🔒 BRANCH REPORT FILTER APPLIED{Colors.RESET}")
        print(f"{Colors.GREEN}   → sol_id filter added to WHERE clause{Colors.RESET}")
    elif not is_branch_user:
        print(f"{Colors.BRIGHT_BLUE}ℹ️  NO FILTER APPLIED{Colors.RESET}")
        print(f"{Colors.BLUE}   → Using original query (user doesn't have Branch Report role){Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}📄 Query:{Colors.RESET}")
    print(f"{Colors.WHITE}{sql_query}{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}📊 Parameters:{Colors.RESET}")
    if params:
        for key, value in params.items():
            print(f"{Colors.YELLOW}   • {key}:{Colors.RESET} {Colors.WHITE}{value}{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}   (No parameters){Colors.RESET}")
    
    print(f"{Colors.BRIGHT_MAGENTA}{'─' * 80}{Colors.RESET}\n")
