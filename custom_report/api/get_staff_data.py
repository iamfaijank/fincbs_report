import frappe
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from custom_report.db_connection import get_dr_connection

@frappe.whitelist()
def get_staff_details(staff_id=None):
    """
    Fetches staff details (ID and Name) from the external Finacle database.
    
    :param staff_id: Staff ID (internally emp_id) to search for.
    :return: Dictionary containing staff details or error status.
    """
    if not staff_id:
        frappe.throw(frappe._("Staff ID (staff_id) is required"), frappe.ValidationError)

    conn = None
    try:
        # Establish connection using existing utility
        conn = get_dr_connection()
        cursor = conn.cursor()

        # Secure parameterized query execution (mapping staff_id to emp_id column)
        query = "SELECT emp_id, emp_name FROM tbaadm.get WHERE emp_id = %s"
        cursor.execute(query, (staff_id,))
        row = cursor.fetchone()

        if not row:
            return {
                "status": "not_found",
                "message": frappe._("No staff records found for Staff ID: {0}").format(staff_id)
            }

        # Return successful response mapping emp_id -> staff_id
        return {
            "staff_id": row[0],
            "staff_name": row[1]
        }

    except Exception:
        # Log error with traceback in Frappe Error Log
        frappe.log_error(message=frappe.get_traceback(), title="Get Staff Data API Error")
        frappe.throw(frappe._("An error occurred while fetching staff data from the external database."))

    finally:
        # Ensure connection is closed to prevent leaks
        if conn:
            conn.close()
