import frappe
import csv
import io
from datetime import date, datetime
from decimal import Decimal


@frappe.whitelist(allow_guest=True)
def check_db_connectivity():
	"""Check DR database connectivity status."""
	from custom_report.db_connection import get_dr_connection
	import time

	is_admin = frappe.session.user == "Administrator"
	if not is_admin:
		return {"status": "forbidden", "message": "Only administrators can view this."}

	try:
		start = time.time()
		conn = get_dr_connection()
		elapsed = round((time.time() - start) * 1000)
		with conn.cursor() as cur:
			cur.execute("SELECT version()")
			db_version = cur.fetchone()[0]
			cur.execute("SELECT NOW()")
			db_time = cur.fetchone()[0]
		conn.close()
		return {
			"status": "connected",
			"message": "DR Database connected successfully",
			"latency_ms": elapsed,
			"db_version": db_version,
			"db_time": str(db_time),
		}
	except Exception as e:
		return {
			"status": "failed",
			"message": str(e),
		}


def _build_csv(rows, include_header=True):
	buf = io.StringIO()
	writer = csv.writer(buf, lineterminator="\r\n")

	if include_header:
		writer.writerow(["CIF_ID", "ACCOUNT_NO", "BACID", "ACCT_NAME", "SOL_ID",
		                  "GL_SUB_HEAD_CODE", "TRAN_ID", "TRAN_DATE", "TRAN_TYPE", "TRAN_AMT"])

	for row in rows:
		cleaned = []
		for val in row:
			if val is None:
				cleaned.append("")
			elif isinstance(val, Decimal):
				cleaned.append(format(val, "f"))
			elif isinstance(val, (date, datetime)):
				cleaned.append(val.isoformat())
			else:
				cleaned.append(str(val))
		writer.writerow(cleaned)

	csv_content = buf.getvalue()
	buf.close()
	return csv_content


@frappe.whitelist(allow_guest=True)
def download_transactions():
	"""API endpoint for batch CSV download of transactions."""
	from custom_report.db_connection import execute_dr_query

	account_type = frappe.form_dict.get("account_type")
	account_value = frappe.form_dict.get("account_value", "").strip()
	start_date = frappe.form_dict.get("start_date")
	end_date = frappe.form_dict.get("end_date")
	offset = int(frappe.form_dict.get("offset", 0))
	limit = int(frappe.form_dict.get("limit", 50000))

	if account_type not in ("bacid", "foracid", "gl_sub_head_code"):
		frappe.throw("Choose BACID, Account No. or GL SUB HEAD CODE.")
	if not account_value:
		frappe.throw("Enter the account value.")

	column_map = {
		"bacid": "g.bacid",
		"foracid": "g.foracid",
		"gl_sub_head_code": "g.gl_sub_head_code",
	}
	column = column_map[account_type]

	subquery_column_map = {
		"bacid": "g2.bacid",
		"foracid": "g2.foracid",
		"gl_sub_head_code": "g2.gl_sub_head_code",
	}
	subquery_column = subquery_column_map[account_type]

	base_join = f"""
		FROM tbaadm.gam g
		INNER JOIN tbaadm.htd h ON g.acid = h.acid AND h.pstd_flg = 'Y'
		INNER JOIN (
			SELECT DISTINCT h2.tran_id, h2.tran_date
			FROM tbaadm.htd h2
			INNER JOIN tbaadm.gam g2 ON h2.acid = g2.acid AND h2.pstd_flg = 'Y'
			WHERE {subquery_column} = %(account_value)s
			  AND h2.tran_date BETWEEN %(start_date)s AND %(end_date)s
		) v ON h.tran_date = v.tran_date AND h.tran_id = v.tran_id
	"""

	params = {
		"account_value": account_value,
		"start_date": start_date,
		"end_date": end_date,
		"limit": limit,
		"offset": offset,
	}

	try:
		count_rows = execute_dr_query("SELECT COUNT(*) " + base_join, params)
		total = count_rows[0][0] if count_rows else 0
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Transaction Count Error")
		frappe.throw("The report could not be generated. Try again in a moment.")

	if total == 0:
		frappe.throw("No posted transactions found for this account and date range.")

	data_sql = f"""
		SELECT g.cif_id, g.foracid, g.bacid, g.acct_name, g.sol_id, g.gl_sub_head_code,
		       h.tran_id, h.tran_date, h.tran_type, h.tran_amt
		{base_join}
		ORDER BY h.tran_date, h.tran_id
		LIMIT %(limit)s OFFSET %(offset)s
	"""
	try:
		rows = execute_dr_query(data_sql, params)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Transaction Data Error")
		frappe.throw("The report could not be generated. Try again in a moment.")

	csv_content = _build_csv(rows, include_header=(offset == 0))

	frappe.local.response["message"] = {
		"total": total,
		"batch_rows": len(rows),
		"csv": csv_content,
	}
