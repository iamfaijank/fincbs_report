import frappe
import psycopg2
from frappe import _

def get_dr_connection():
    """
    Establishes a connection to the Disaster Recovery (DR) / External Finacle DB 
    using credentials from the 'Finacle DB Credentials' Single Doctype.
    """
    try:
        # Fetch configuration from the Single Doctype
        config = frappe.get_single("Finacle DB Credentials")
        
        # Validate mandatory fields before attempting connection
        if not config.db_host or not config.db_name or not config.db_user:
            frappe.throw(_("DR Database configuration is incomplete. Please check 'Finacle DB Credentials'."))

        # Prepare connection parameters
        connection_params = {
            "host": config.db_host,
            "port": config.db_port or 5432,
            "database": config.db_name,
            "user": config.db_user,
            "password": config.get_password("db_password"),
            "connect_timeout": 10  # Prevents the app from hanging if DB is unreachable
        }

        # Return the established connection
        return psycopg2.connect(**connection_params)

    except psycopg2.Error as e:
        # Log the specific database error for debugging
        frappe.log_error(message=frappe.get_traceback(), title="DR DB Connection Error")
        frappe.throw(_("Unable to connect to the DR Database. Please verify credentials and network access."))