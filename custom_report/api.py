import frappe
import io
import os
import time
import tempfile
import re
from custom_report.db_utils import get_pg_connection


@frappe.whitelist()
def get_user_reports():
    """Return reports allowed for the current user with last download duration."""
    try:
        user_roles = set(frappe.get_roles())
        reports = frappe.get_all("Finacle Report", fields=["name", "report_name"])
        allowed_reports = []

        for report in reports:
            roles = frappe.get_all(
                "Finacle Report User",
                filters={"parent": report.name},
                fields=["role"]
            )
            allowed_roles = [r.role for r in roles]

            if user_roles.intersection(allowed_roles):
                report_doc = frappe.get_doc("Finacle Report", report.name)
                last_duration = getattr(report_doc, "last_download_duration", None)
                allowed_reports.append({
                    "name": report.name,
                    "report_name": report.report_name,
                    "last_duration": last_duration
                })

        return allowed_reports

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Error fetching user reports")
        return []


@frappe.whitelist()
def report_download(report_docname, start_date=None, end_date=None, file_type="csv"):
    """Download the report data filtered by user's sol_id, date, and placeholders."""
    try:
        user = frappe.session.user
        sol_id = None

        # Step 1: Try fetching sol_id if column exists in User
        try:
            sol_id = frappe.db.get_value("User", user, "sol_id")
        except Exception as e:
            frappe.log_error(f"sol_id column not found in User table: {str(e)}", "report_download")

        # Step 2: Get report details
        report_doc = frappe.get_doc("Finacle Report", report_docname)
        raw_sql = report_doc.sql_query.strip()

        # Step 3: Connect to Postgres
        conn = get_pg_connection()
        cursor = conn.cursor()

        # Step 4: Detect if sol_id column exists in query result
        has_sol_id_column = False
        try:
            preview_sql = f"SELECT * FROM ({raw_sql}) AS subq LIMIT 1"
            cursor.execute(preview_sql)
            colnames = [desc[0].lower() for desc in cursor.description]
            has_sol_id_column = "sol_id" in colnames
        except Exception as e:
            has_sol_id_column = False
            conn.rollback()
            frappe.log_error(f"Preview check failed: {str(e)}", "report_download")

        # Step 5: Apply sol_id filter if applicable
        if sol_id:
            if has_sol_id_column:
                if re.search(r"\bwhere\b", raw_sql, flags=re.IGNORECASE):
                    raw_sql = f"{raw_sql} AND sol_id = %(sol_id)s"
                else:
                    raw_sql = f"{raw_sql} WHERE sol_id = %(sol_id)s"
        else:
            if has_sol_id_column:
                frappe.throw("❌ You don't have a valid sol_id assigned. Access denied.")

        # Step 6: Add date filter placeholders dynamically (if needed)
        params = {}
        if "%(start_date)s" in raw_sql or "%(end_date)s" in raw_sql:
            params["start_date"] = start_date
            params["end_date"] = end_date

        if "%(sol_id)s" in raw_sql and sol_id:
            params["sol_id"] = sol_id

        # Step 7: Execute final SQL
        frappe.log_error(raw_sql, "Final SQL Executed")  # Debug log
        cursor.execute(raw_sql, params if params else None)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Step 8: Generate CSV
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)
        csv_data = output.getvalue()
        output.close()

        # Step 9: Save temporarily
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{report_doc.report_name}_{timestamp}.csv"
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        with open(temp_path, "w", encoding="utf-8", newline="") as f:
            f.write(csv_data)

        cursor.close()
        conn.close()

        # Step 10: Serve file
        with open(temp_path, "rb") as f:
            filedata = f.read()

        frappe.local.response.filename = filename
        frappe.local.response.filecontent = filedata
        frappe.local.response.type = "download"

        return {"status": "success", "filename": filename}

    except Exception as e:
        frappe.log_error(f"Error in report_download: {str(e)}", "report_download")
        raise e




