import frappe
from custom_report.db_connection import get_dr_connection

def get_context(context):
    # Prevent caching and require login
    context.no_cache = 1
    context.login_required = True
    
    # Check if user is Administrator or has specific roles (optional, defaults to True for now)
    context.has_access = True

@frappe.whitelist()
def get_cif_details(cif_id):
    if not cif_id:
        return {"success": False, "error": "CIF ID is required"}

    conn = None
    try:
        conn = get_dr_connection()
        cursor = conn.cursor()
        
        # SQL query to fetch data for the given CIF ID from Finacle DB
        query = """
            SELECT 
                g.cif_id, g.foracid, g.acct_name, g.schm_code, g.schm_type, 
                g.acct_opn_date, g.sol_id, s.sol_desc
            FROM tbaadm.gam g
            JOIN tbaadm.sol s ON g.sol_id = s.sol_id
            WHERE g.cif_id = %s AND g.entity_cre_flg = 'Y' AND g.del_flg = 'N'
        """
        cursor.execute(query, (cif_id,))
        rows = cursor.fetchall()
        
        if rows:
            data = []
            for r in rows:
                data.append({
                    "cif_id": r[0],
                    "account_no": r[1],
                    "account_name": r[2],
                    "schm_code": r[3],
                    "schm_type": r[4],
                    "opening_date": str(r[5]),
                    "sol_id": r[6],
                    "sol_desc": r[7]
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
