import frappe
from custom_report.db_connection import get_dr_connection

def get_context(context):
    # Prevent caching and require login
    context.no_cache = 1
    context.login_required = True
    
    # Check if user has "CIF Tracker" role
    context.has_access = check_user_access()

def check_user_access():
    """Helper to check if user has access based on designation OR role"""
    user = frappe.session.user
    if user == "Administrator":
        return True

    user_roles = set(frappe.get_roles(user))
    if "System Manager" in user_roles:
        return True
        
    # Check designation first (Full access for these designations)
    designation = frappe.db.get_value("Employee", {"user_id": user}, "designation")
    if designation in ['BRANCH MANAGER', 'Branch Operation Manager', 'CLUSTER OPERATION MANAGER', 'Asst. Branch Manager']:
        return True

    # Fallback to role-based access if designation doesn't match
    if "CIF Tracker" in user_roles:
        return True
        
    return False

@frappe.whitelist()
def get_cif_details(cif_id):
    # Security check for API call
    if not check_user_access():
        frappe.throw("Only BOM, ABM, BM, and COM users have access to the CIF Tracker; please connect with them for assistance.", frappe.PermissionError)

    if not cif_id or len(str(cif_id)) < 4 or len(str(cif_id)) > 9:
        return {"success": False, "error": "CIF ID must be between 4 and 9 digits"}

    conn = None
    try:
        conn = get_dr_connection()
        cursor = conn.cursor()
        
        # SQL query updated to use INNER JOINs for critical assignment data
        query = """
            SELECT 
                u.loginid AS user_id,
                g.sol_id AS branch_code,
                s.sol_desc as branch_name,
                g.emp_name AS user_name,
                am.orgkey
            FROM crmuser.accounts_mod am
            INNER JOIN crmuser.users u ON am.assignedto = u.personid
            INNER JOIN tbaadm."get" g ON u.loginid = g.emp_id
            LEFT JOIN tbaadm.sol s ON s.sol_id = g.sol_id
            WHERE am.orgkey = %s
        """
        cursor.execute(query, (cif_id,))
        rows = cursor.fetchall()
        
        data = []
        if rows:
            for r in rows:
                # Extra safety check: ensure we have a user_id
                if r[0]:
                    data.append({
                        "user_id": r[0],
                        "branch_code": r[1],
                        "branch_name": r[2],
                        "user_name": r[3],
                        "cif_id": r[4]
                    })
        
        if data:
            return {"success": True, "data": data}
        else:
            return {"success": False, "error": "The mentioned CIF has either not been submitted correctly or has already been verified. Please verify the details and try again."}

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="CIF Tracker Error")
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            conn.close()
