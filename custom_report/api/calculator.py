import frappe
from custom_report.db_connection import get_dr_connection

def fetch_data():
    conn = None
    try:
        # Calling your centralized function
        conn = get_dr_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT col1, col2 FROM some_table")
        return cursor.fetchall()
        
    finally:
        # Always close the connection to prevent memory leaks
        if conn:
            conn.close()