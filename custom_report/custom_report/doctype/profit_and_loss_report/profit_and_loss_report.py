# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
import psycopg2.extras
from frappe.utils import flt
from frappe.model.document import Document

from custom_report.db_connection import get_dr_connection

TRIAL_BALANCE_QUERY = """
SELECT
	'OFFICE' AS acct_category,
	g.schm_type,
	g.schm_code,
	g.sol_id,
	g.gl_sub_head_code,
	g.bacid,
	g.acct_name,
	SUM(g.clr_bal_amt) AS clr_bal_amt,
	SUM(e.tran_date_bal) AS balance,
	g2.schm_desc,
	g.acct_cls_flg,
	g.del_flg
FROM
	tbaadm.gam g
JOIN
	tbaadm.gsp g2
		ON g.schm_code = g2.schm_code
		AND g.acct_ownership = 'O'
LEFT JOIN
	tbaadm.eab e
		ON e.acid = g.acid
		AND %(sync_date)s::DATE BETWEEN e.eod_date AND e.end_eod_date
GROUP BY
	g.schm_type,
	g.schm_code,
	g.sol_id,
	g.gl_sub_head_code,
	g.bacid,
	g.acct_name,
	g2.schm_desc,
	g.del_flg,
	g.acct_cls_flg
HAVING
	COALESCE(SUM(g.clr_bal_amt), 0) <> 0
	OR COALESCE(SUM(e.tran_date_bal), 0) <> 0
UNION ALL
SELECT
	'CUSTOMER' AS acct_category,
	g.schm_type,
	g.schm_code,
	g.sol_id,
	g.gl_sub_head_code,
	g.bacid,
	NULL AS acct_name,
	SUM(g.clr_bal_amt) AS clr_bal_amt,
	SUM(e.tran_date_bal) AS balance,
	g2.schm_desc,
	g.acct_cls_flg,
	g.del_flg
FROM
	tbaadm.gam g
JOIN
	tbaadm.gsp g2
		ON g.schm_code = g2.schm_code
LEFT JOIN
	tbaadm.eab e
		ON e.acid = g.acid
		AND %(sync_date)s::DATE BETWEEN e.eod_date AND e.end_eod_date
WHERE
	g.acct_ownership <> 'O'
GROUP BY
	g.schm_type,
	g.schm_code,
	g.sol_id,
	g.gl_sub_head_code,
	g.bacid,
	g2.schm_desc,
	g.del_flg,
	g.acct_cls_flg
HAVING
	COALESCE(SUM(g.clr_bal_amt), 0) <> 0
	OR COALESCE(SUM(e.tran_date_bal), 0) <> 0
ORDER BY
	acct_category,
	schm_type,
	schm_code,
	gl_sub_head_code
"""


class ProfitandLossReport(Document):
	pass


def execute_pl_report_bulk_insert(records: list, chunk_size: int = 5000) -> None:
	"""Direct DB-to-DB bulk INSERT into tabProfit and Loss Report without ORM overhead."""
	if not records:
		return

	db_type = getattr(frappe.db, "db_type", None) or "mariadb"
	row_placeholder = (
		"(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,"
		" %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
	)

	for i in range(0, len(records), chunk_size):
		chunk = records[i : i + chunk_size]
		placeholders = ", ".join([row_placeholder] * len(chunk))
		flattened_params = [val for row in chunk for val in row]

		if db_type == "mariadb":
			sql = f"""
			INSERT IGNORE INTO `tabProfit and Loss Report` (
				`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `idx`,
				`report_date`, `acct_category`, `schm_type`, `schm_code`, `sol_id`,
				`gl_sub_head_code`, `bacid`, `acct_name`, `clr_bal_amt`, `balance`,
				`schm_desc`, `acct_cls_flg`, `del_flg`, `schedule`, `sub_schedule`
			) VALUES {placeholders};
			"""
		else:
			sql = f"""
			INSERT INTO "tabProfit and Loss Report" (
				"name", "creation", "modified", "modified_by", "owner", "docstatus", "idx",
				"report_date", "acct_category", "schm_type", "schm_code", "sol_id",
				"gl_sub_head_code", "bacid", "acct_name", "clr_bal_amt", "balance",
				"schm_desc", "acct_cls_flg", "del_flg", "schedule", "sub_schedule"
			) VALUES {placeholders} ON CONFLICT DO NOTHING;
			"""
		frappe.db.sql(sql, flattened_params)


def get_gl_schedule_map() -> dict:
	"""Map gl_sub_head_code -> (schedule, sub_schedule) from GL Mapping."""
	mappings = frappe.get_all(
		"GL Mapping",
		fields=["gl_sub_head_code", "schedule", "sub_schedule"],
	)
	return {m.gl_sub_head_code: (m.schedule, m.sub_schedule) for m in mappings}


def send_email_notification(status, sync_date, details_or_error=""):
	recipients = ["talib.s@sahayogmultistate.com", "atul.n@sahayogmultistate.com"]
	subject = f"Profit and Loss Report Sync Status - {sync_date}"

	if status == "Success":
		message = f"""
		<p>Dear Team,</p>
		<p>The daily automated sync for <b>Profit and Loss Report</b> has completed successfully.</p>
		<table border="1" cellpadding="6" style="border-collapse: collapse; border-color: #cbd5e1;">
			<tr style="background-color: #f8fafc;">
				<th>Parameter</th>
				<th>Value</th>
			</tr>
			<tr>
				<td><b>Sync Target Date</b></td>
				<td>{sync_date}</td>
			</tr>
			<tr>
				<td><b>Status</b></td>
				<td style="color: green; font-weight: bold;">SUCCESS</td>
			</tr>
			<tr>
				<td><b>Records Saved</b></td>
				<td>{details_or_error}</td>
			</tr>
			<tr>
				<td><b>Execution Time</b></td>
				<td>{frappe.utils.now_datetime().strftime('%d-%m-%Y %I:%M %p')}</td>
			</tr>
		</table>
		<br>
		<p>Regards,<br>Sahayog System Automation</p>
		"""
	else:
		message = f"""
		<p>Dear Team,</p>
		<p style="color: red; font-weight: bold;">WARNING: The daily automated sync for Profit and Loss Report has FAILED.</p>
		<table border="1" cellpadding="6" style="border-collapse: collapse; border-color: #cbd5e1;">
			<tr style="background-color: #f8fafc;">
				<th>Parameter</th>
				<th>Value</th>
			</tr>
			<tr>
				<td><b>Sync Target Date</b></td>
				<td>{sync_date}</td>
			</tr>
			<tr>
				<td><b>Status</b></td>
				<td style="color: red; font-weight: bold;">FAILED</td>
			</tr>
			<tr>
				<td><b>Error Details</b></td>
				<td><pre style="color: red;">{details_or_error}</pre></td>
			</tr>
			<tr>
				<td><b>Execution Time</b></td>
				<td>{frappe.utils.now_datetime().strftime('%d-%m-%Y %I:%M %p')}</td>
			</tr>
		</table>
		<br>
		<p>Please check the scheduler logs or Finacle DB Credentials setting.</p>
		<br>
		<p>Regards,<br>Sahayog System Automation</p>
		"""

	try:
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			delayed=False,
		)
	except Exception as e:
		frappe.log_error(f"Profit and Loss Report Sync Email Error: {e}", "Email Error")


def daily_sync_profit_and_loss_report(sync_date=None):
	if sync_date is None:
		from frappe.utils import add_days, cint, today

		sync_enabled = cint(frappe.db.get_single_value("Drishti Settings", "auto_sync"))
		if not sync_enabled:
			frappe.logger("scheduler").info(
				"Daily Profit and Loss Report Sync: Sync is disabled in Drishti Settings. Skipping execution."
			)
			return

		# Sync data for yesterday (today - 1 day)
		sync_date = add_days(today(), -1)
		frappe.log_error("Starting Daily Profit and Loss Report Sync for: " + sync_date, "Profit and Loss Report Sync")
		try:
			sync_profit_and_loss_data(sync_date)
			count = frappe.db.count("Profit and Loss Report", {"report_date": sync_date})
			frappe.log_error(
				"Successfully synced Profit and Loss Report for: " + sync_date, "Profit and Loss Report Sync"
			)
			send_email_notification("Success", sync_date, str(count))
		except Exception as e:
			frappe.log_error("Failed to sync Profit and Loss Report: " + str(e), "Profit and Loss Report Sync Error")
			send_email_notification("Failed", sync_date, str(e))
		return

	sync_profit_and_loss_data(str(sync_date))
	return frappe.db.count("Profit and Loss Report", {"report_date": str(sync_date)})


@frappe.whitelist()
def sync_profit_and_loss_data(sync_date):
	import time

	conn = None
	try:
		max_retries = 5
		rows = []

		for attempt in range(max_retries):
			try:
				conn = get_dr_connection()
				with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
					try:
						cur.execute("SET statement_timeout = 0;")
					except Exception:
						pass
					cur.execute(TRIAL_BALANCE_QUERY, {"sync_date": sync_date})
					rows = cur.fetchall()
				break
			except Exception as e:
				err_str = str(e).lower()
				is_recovery_conflict = any(
					term in err_str
					for term in [
						"conflict with recovery",
						"canceling statement",
						"querycanceled",
						"serializationfailure",
						"55006",
						"40001",
					]
				)
				if is_recovery_conflict and attempt < max_retries - 1:
					retry_delay = (attempt + 1) * 3
					frappe.log_error(
						f"DR DB Query Conflict (Attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...",
						"Profit and Loss Report Sync Retry",
					)
					if conn:
						try:
							conn.close()
						except Exception:
							pass
					time.sleep(retry_delay)
				else:
					raise

		# Delete existing records for this date
		frappe.db.delete("Profit and Loss Report", {"report_date": sync_date})

		from frappe.utils import now_datetime

		now_time = now_datetime()
		session_user = (
			getattr(frappe.session, "user", "Administrator")
			if getattr(frappe, "session", None)
			else "Administrator"
		)

		gl_map = get_gl_schedule_map()

		bulk_data = []
		for row in rows:
			# OFFICE: match bacid to GL Mapping gl_sub_head_code
			# CUSTOMER: match gl_sub_head_code to GL Mapping gl_sub_head_code
			map_key = row["bacid"] if row["acct_category"] == "OFFICE" else row["gl_sub_head_code"]
			schedule, sub_schedule = gl_map.get(map_key, (None, None))

			bulk_data.append(
				(
					frappe.generate_hash(length=16),
					now_time,
					now_time,
					session_user,
					session_user,
					0,
					0,
					sync_date,
					row["acct_category"],
					row["schm_type"],
					row["schm_code"],
					row["sol_id"],
					row["gl_sub_head_code"],
					row["bacid"],
					row["acct_name"],
					row["clr_bal_amt"],
					row["balance"],
					row["schm_desc"],
					row["acct_cls_flg"],
					row["del_flg"],
					schedule,
					sub_schedule,
				)
			)

		execute_pl_report_bulk_insert(bulk_data, chunk_size=5000)
		frappe.db.commit()
		return "Success"
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Profit and Loss Report Sync Error")
		frappe.throw(f"An error occurred during sync: {str(e)}")
	finally:
		if conn:
			conn.close()


@frappe.whitelist()
def get_pl_summary(report_date=None, sol_id=None):
	"""Sum balance grouped by schedule/sub_schedule for schedules >= 13."""
	filters = ["COALESCE(schedule, '') != ''"]
	params = []
	if report_date:
		filters.append("report_date = %s")
		params.append(report_date)
	if sol_id:
		filters.append("sol_id LIKE %s")
		params.append(f"%{sol_id}%")
	rows = frappe.db.sql(
		"""
		SELECT schedule, sub_schedule, SUM(balance) AS total_balance
		FROM `tabProfit and Loss Report`
		WHERE {conditions}
		GROUP BY schedule, sub_schedule
		""".format(conditions=" AND ".join(filters)),
		tuple(params),
		as_dict=True,
	)

	import re

	def sched_num(s):
		m = re.search(r"Schedule\s*(\d+)", s or "")
		return int(m.group(1)) if m else None

	schedules = {}
	for r in rows:
		num = sched_num(r.schedule)
		if num is None or num < 13:
			continue
		schedules.setdefault(
			num,
			{"schedule": r.schedule.strip(), "schedule_number": num, "sub_schedules": []},
		)["sub_schedules"].append(
			{"sub_schedule": (r.sub_schedule or "").strip() or "-", "total_balance": flt(r.total_balance)}
		)

	result = []
	for num in sorted(schedules):
		entry = schedules[num]
		entry["sub_schedules"].sort(key=lambda x: x["sub_schedule"])
		entry["total_balance"] = sum(s["total_balance"] for s in entry["sub_schedules"])
		result.append(entry)
	return result


@frappe.whitelist()
def get_latest_pl_date():
	"""Return the latest report_date present in Profit and Loss Report."""
	return frappe.db.get_value(
		"Profit and Loss Report", {}, "report_date", order_by="report_date desc"
	)
