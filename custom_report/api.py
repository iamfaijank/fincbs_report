import frappe
import io
import os
import time
import tempfile
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
def report_download(report_docname, start_date, end_date, file_type="csv"):
    """
    High-performance report download:
    - Uses PostgreSQL COPY for fast CSV generation
    - Automatically names file as <Report Name>_<Start>_to_<End>.csv
    """

    # Step 1: Load report doc
    report_doc = frappe.get_doc("Finacle Report", report_docname)
    if not report_doc or not report_doc.sql_query:
        frappe.throw("❌ SQL query not defined for this report")

    # Step 2: Role-based filter (Branch Report)
    sol_id = None
    user = frappe.session.user
    user_roles = frappe.get_roles(user)

    if "Branch Report" in user_roles:
        sol_id = frappe.get_value("Employee", {"user_id": user}, "sahayog_branch")
        if not sol_id:
            frappe.throw("❌ No sahayog_branch found in your Employee record.")

    # Step 3: Check DB connection
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
    except Exception as db_exc:
        frappe.log_error(frappe.get_traceback(), "Database Connection Failed")
        frappe.throw(f"❌ Database connection failed.\n{db_exc}")

    # Step 4: Prepare SQL
    raw_sql = report_doc.sql_query.strip().rstrip(';')
    if sol_id:
        if "where" in raw_sql.lower():
            raw_sql += " AND g.sol_id = %(sol_id)s"
        else:
            raw_sql += " WHERE g.sol_id = %(sol_id)s"

    try:
        params = {"start_date": start_date, "end_date": end_date}
        if sol_id:
            params["sol_id"] = sol_id

        final_sql = cursor.mogrify(raw_sql, params).decode("utf-8")
    except Exception as sql_exc:
        frappe.log_error(frappe.get_traceback(), "SQL Mogrify Failed")
        frappe.throw(f"❌ SQL preparation failed: {sql_exc}")

    # Step 5: Generate temp CSV file
    tmp_csv = tempfile.NamedTemporaryFile(
        delete=False, prefix="frp_report_", suffix=".csv",
        mode="w", encoding="utf-8", newline=''
    )
    tmp_csv_name = tmp_csv.name
    tmp_csv.close()

    start_time = time.time()

    try:
        # Write directly from DB using COPY
        with open(tmp_csv_name, "w", encoding="utf-8", newline='') as f_out:
            cursor.copy_expert(f"COPY ({final_sql}) TO STDOUT WITH CSV HEADER", f_out)

        duration_seconds = max(2.0, time.time() - start_time)

        # Save duration
        frappe.db.set_value(
            "Finacle Report",
            report_docname,
            "last_download_duration",
            duration_seconds,
            update_modified=True
        )
        frappe.db.commit()

        # Step 6: Build proper filename — ✅ EXACT report name + date range
        clean_name = report_doc.report_name.strip().replace(" ", "_").replace("/", "_")
        final_filename = f"{clean_name}_{start_date}_to_{end_date}.csv"

        # Step 7: Prepare response (this part forces the correct filename)
        with open(tmp_csv_name, "rb") as f:
            file_bytes = f.read()

        frappe.local.response["type"] = "binary"
        frappe.local.response["filename"] = final_filename
        frappe.local.response["filecontent"] = file_bytes
        frappe.local.response["display_content_as"] = "attachment"
        frappe.local.response["headers"] = [
            ("Content-Type", "text/csv"),
            ("Content-Disposition", f'attachment; filename="{final_filename}"'),
        ]

    except Exception as exc:
        frappe.log_error(frappe.get_traceback(), f"Report Download Error ({report_docname})")
        frappe.throw(f"❌ Something went wrong during report download: {exc}")

    finally:
        try:
            if os.path.exists(tmp_csv_name):
                os.remove(tmp_csv_name)
        except Exception:
            pass
