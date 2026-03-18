import frappe
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from custom_report.db_connection import get_dr_connection

@frappe.whitelist()
def get_staff_details(staff_id=None):
    """
    Fetches staff details (ID and Name) from the external Finacle database.
    Validates that the staff_id starts with 'SAH'.
    
    :param staff_id: Staff ID (internally emp_id) to search for.
    :return: Dictionary containing staff details or error status.
    """
    if not staff_id:
        frappe.throw(frappe._("Staff ID (staff_id) is required"), frappe.ValidationError)

    # Prefix validation
    if not staff_id.startswith("SAH"):
        return {
            "status": "invalid_prefix",
            "message": frappe._("Staff ID must start with 'SAH' prefix.")
        }

    conn = None
    try:
        conn = get_dr_connection()
        cursor = conn.cursor()

        query = "SELECT emp_id, emp_name FROM tbaadm.get WHERE emp_id = %s"
        cursor.execute(query, (staff_id,))
        row = cursor.fetchone()

        if not row:
            return {
                "status": "not_found",
                "message": frappe._("No staff records found for Staff ID: {0}").format(staff_id)
            }

        return {
            "staff_id": row[0],
            "staff_name": row[1]
        }

    except Exception:
        frappe.log_error(message=frappe.get_traceback(), title="Get Staff Data API Error")
        frappe.throw(frappe._("An error occurred while fetching staff data from the external database."))

    finally:
        if conn:
            conn.close()

@frappe.whitelist()
def get_agent_details(agent_id=None):
    """
    Fetches agent details (ID and Name) from the external Finacle database.
    Validates that the agent_id starts with 'RDDSA' or 'DDDSA'.
    
    :param agent_id: Agent ID (internally emp_id) to search for.
    :return: Dictionary containing agent details or error status.
    """
    if not agent_id:
        frappe.throw(frappe._("Agent ID (agent_id) is required"), frappe.ValidationError)

    # Prefix validation
    if not (agent_id.startswith("RDDSA") or agent_id.startswith("DDDSA")):
        return {
            "status": "invalid_prefix",
            "message": frappe._("Agent ID must start with 'RDDSA' or 'DDDSA' prefix.")
        }

    conn = None
    try:
        conn = get_dr_connection()
        cursor = conn.cursor()

        # Assuming agents are also in the same table/schema as per standard Finacle access
        query = "SELECT emp_id, emp_name FROM tbaadm.get WHERE emp_id = %s"
        cursor.execute(query, (agent_id,))
        row = cursor.fetchone()

        if not row:
            return {
                "status": "not_found",
                "message": frappe._("No agent records found for Agent ID: {0}").format(agent_id)
            }

        return {
            "agent_id": row[0],
            "agent_name": row[1]
        }

    except Exception:
        frappe.log_error(message=frappe.get_traceback(), title="Get Agent Data API Error")
        frappe.throw(frappe._("An error occurred while fetching agent data from the external database."))

    finally:
        if conn:
            conn.close()
