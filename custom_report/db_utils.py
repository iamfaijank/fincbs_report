import frappe
import psycopg2

def get_pg_connection():
    try:
        creds = frappe.get_single("Finacle DB Credentials")

        conn = psycopg2.connect(
            host=creds.db_host,
            port=creds.db_port,
            user=creds.db_user,
            password=creds.get_password("db_password"),
            database=creds.db_name
        )
        return conn   # dict nahi, actual connection return karo

    except Exception as e:
        frappe.throw(f"Postgres Connection Error: {str(e)}")
