# report_module.py
import psycopg2
import frappe

def test_db_connection():
    settings = frappe.get_doc("Finacle DB Credentials", "Finacle DB Credentials")

    try:
        connection = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port or 5432,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name
        )
        return {"status": "Success", "message": "Connected to PostgreSQL DB"}

    except Exception as e:
        print("Connection failed:", str(e))  # <-- Ye line print karegi agar connection fail ho
        return {"status": "Failed", "message": str(e)}

    finally:
        if 'connection' in locals() and connection:
            connection.close()
