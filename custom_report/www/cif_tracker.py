import frappe
from custom_report.db_connection import get_dr_connection

def get_context(context):
    # Prevent caching and require login
    context.no_cache = 1
    context.login_required = True
    
    # Check if user has "CIF Tracker" role
    context.has_access = check_user_access()

def check_user_access():
    """Helper to check if user has 'CIF Tracker' or 'Administrator' access"""
    user = frappe.session.user
    if user == "Administrator":
        return True

    user_roles = set(frappe.get_roles(user))
    if "CIF Tracker" in user_roles or "System Manager" in user_roles:
        return True
        
    return False

@frappe.whitelist()
def get_cif_details(cif_id):
    # Security check for API call
    if not check_user_access():
        frappe.throw("Access Denied: You do not have the 'CIF Tracker' role.", frappe.PermissionError)

    if not cif_id:
        return {"success": False, "error": "CIF ID is required"}

    conn = None
    try:
        conn = get_dr_connection()
        cursor = conn.cursor()
        
        # SQL query provided by user
        query = """
            SELECT 
                u.loginid AS user_id,
                g.sol_id AS branch_code,
                s.sol_desc as branch_name,
                g.emp_name AS user_name,
                am.orgkey
            FROM crmuser.accounts_mod am
            LEFT JOIN crmuser.users u ON am.assignedto = u.personid
            LEFT JOIN tbaadm."get" g ON u.loginid = g.emp_id
            LEFT JOIN tbaadm.sol s ON s.sol_id = g.sol_id
            WHERE am.orgkey = %s
        """
        cursor.execute(query, (cif_id,))
        rows = cursor.fetchall()
        
        if rows:
            data = []
            for r in rows:
                data.append({
                    "user_id": r[0],
                    "branch_code": r[1],
                    "branch_name": r[2],
                    "user_name": r[3],
                    "cif_id": r[4]
                })
            return {"success": True, "data": data}
        else:
            return {"success": False, "error": "No records found for this CIF ID."}

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="CIF Tracker Error")
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            conn.close()
