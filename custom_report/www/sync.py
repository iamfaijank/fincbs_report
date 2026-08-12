# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, nowdate, add_days, cint
from frappe import _

no_cache = 1

JOBS_REGISTRY = [
	{
		"key": "sync_dd_sav_daily",
		"title": "DD SAV Report Sync",
		"category": "SS & VS Reports",
		"schedule_time": "07:00 AM",
		"method": "custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.sync_dd_sav_daily",
		"doctype": "SS and VS Report",
		"filters": {"report_type": "DD SAV"},
		"error_title": "SS & VS"
	},
	{
		"key": "sync_dd_tda_daily",
		"title": "DD TDA Report Sync",
		"category": "SS & VS Reports",
		"schedule_time": "07:05 AM",
		"method": "custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.sync_dd_tda_daily",
		"doctype": "SS and VS Report",
		"filters": {"report_type": "DD TDA"},
		"error_title": "SS & VS"
	},
	{
		"key": "sync_rd_daily",
		"title": "RD Report Sync",
		"category": "SS & VS Reports",
		"schedule_time": "07:10 AM",
		"method": "custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.sync_rd_daily",
		"doctype": "SS and VS Report",
		"filters": {"report_type": "RD"},
		"error_title": "SS & VS"
	},
	{
		"key": "sync_smbg_daily",
		"title": "SMBG Report Sync",
		"category": "SS & VS Reports",
		"schedule_time": "07:15 AM",
		"method": "custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.sync_smbg_daily",
		"doctype": "SS and VS Report",
		"filters": {"report_type": "SMBG"},
		"error_title": "SS & VS"
	},
	{
		"key": "sync_fd_1_daily",
		"title": "FD 1 Report Sync",
		"category": "SS & VS Reports",
		"schedule_time": "07:20 AM",
		"method": "custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.sync_fd_1_daily",
		"doctype": "SS and VS Report",
		"filters": {"report_type": "FD 1"},
		"error_title": "SS & VS"
	},
	{
		"key": "sync_dam_daily",
		"title": "DAM Report Sync",
		"category": "SS & VS Reports",
		"schedule_time": "07:25 AM",
		"method": "custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.sync_dam_daily",
		"doctype": "SS and VS Report",
		"filters": {"report_type": "DAM"},
		"error_title": "SS & VS"
	},
	{
		"key": "sync_fd_daily",
		"title": "FD Report Sync",
		"category": "SS & VS Reports",
		"schedule_time": "07:30 AM",
		"method": "custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.sync_fd_daily",
		"doctype": "SS and VS Report",
		"filters": {"report_type": "FD"},
		"error_title": "SS & VS"
	},
	{
		"key": "sync_share_daily",
		"title": "SHARE Report Sync",
		"category": "SS & VS Reports",
		"schedule_time": "07:35 AM",
		"method": "custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.sync_share_daily",
		"doctype": "SS and VS Report",
		"filters": {"report_type": "SHARE"},
		"error_title": "SS & VS"
	},
	{
		"key": "daily_sync_maturity_tracker",
		"title": "Maturity Tracker Sync",
		"category": "Financial Trackers",
		"schedule_time": "07:40 AM",
		"method": "custom_report.custom_report.doctype.maturity_tracker.maturity_tracker.daily_sync_maturity_tracker",
		"doctype": "Maturity Tracker",
		"filters": {},
		"error_title": "Maturity Tracker"
	},
	{
		"key": "cleanup_ss_vs_old_monthly_records",
		"title": "SS & VS Monthly Cleanup",
		"category": "System Maintenance",
		"schedule_time": "07:45 AM",
		"method": "custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.cleanup_ss_vs_old_monthly_records",
		"doctype": None,
		"filters": {},
		"error_title": "SS & VS Cleanup"
	},
	{
		"key": "daily_sync_cron",
		"title": "Sahayog Achievement Sync",
		"category": "Sahayog Dashboard",
		"schedule_time": "08:00 AM",
		"method": "custom_report.custom_report.page.sahayog_dashboard.achievement.daily_sync_cron",
		"doctype": "Branch Category Report",
		"filters": {},
		"error_title": "Branch Category"
	},
	{
		"key": "daily_tda_sync",
		"title": "Sahayog TDA Sync",
		"category": "Sahayog Dashboard",
		"schedule_time": "08:10 AM",
		"method": "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.daily_tda_sync",
		"doctype": "Product Wise Report",
		"filters": {"product": "TDA"},
		"error_title": "TDA Sync"
	},
	{
		"key": "daily_casa_sync",
		"title": "Sahayog CASA Sync",
		"category": "Sahayog Dashboard",
		"schedule_time": "08:15 AM",
		"method": "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.daily_casa_sync",
		"doctype": "Product Wise Report",
		"filters": {"product": "CASA"},
		"error_title": "CASA Sync"
	},
	{
		"key": "daily_sync_book_position",
		"title": "Book Position & Account Details Sync",
		"category": "Financial Trackers",
		"schedule_time": "08:30 AM",
		"method": "custom_report.custom_report.doctype.book_position_and_account_details.book_position_and_account_details.daily_sync_book_position",
		"doctype": "Book Position and Account Details",
		"filters": {},
		"error_title": "Book Position"
	},
	{
		"key": "daily_sync_dd_tracker",
		"title": "DD Tracker Report Sync",
		"category": "Financial Trackers",
		"schedule_time": "08:40 AM",
		"method": "custom_report.custom_report.doctype.dd_tracker_report.dd_tracker_report.daily_sync_dd_tracker",
		"doctype": "DD Tracker Report",
		"filters": {},
		"error_title": "DD Tracker"
	}
]


def get_context(context):
	context.title = "Automation Sync Tracker"
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.site_name = frappe.local.site
	context.auto_sync_enabled = cint(frappe.db.get_single_value("Drishti Settings", "auto_sync"))
	context.initial_sync_data = frappe.as_json(get_automation_sync_status())
	return context


@frappe.whitelist()
def get_automation_sync_status(sync_date=None):
	if not sync_date:
		sync_date = str(add_days(getdate(nowdate()), -1))

	target_date = str(getdate(sync_date))
	auto_sync_enabled = cint(frappe.db.get_single_value("Drishti Settings", "auto_sync"))

	result_jobs = []
	success_count = 0
	failed_count = 0
	pending_count = 0

	for job in JOBS_REGISTRY:
		job_info = {
			"key": job["key"],
			"title": job["title"],
			"category": job["category"],
			"schedule_time": job["schedule_time"],
			"method": job["method"],
			"target_date": target_date,
			"records_synced": 0,
			"status": "Pending",
			"error_message": "",
			"last_execution": None
		}

		rec_count = 0
		if job["doctype"]:
			try:
				f = dict(job["filters"])
				f["date"] = target_date
				rec_count = frappe.db.count(job["doctype"], filters=f)
			except Exception:
				rec_count = 0
		job_info["records_synced"] = rec_count

		error_logs = frappe.db.sql("""
			SELECT name, method, error, creation
			FROM `tabError Log`
			WHERE DATE(creation) = %s
			  AND (method LIKE %s OR error LIKE %s OR title LIKE %s)
			ORDER BY creation DESC LIMIT 1
		""", (target_date, f"%{job['error_title']}%", f"%{job['error_title']}%", f"%{job['error_title']}%"), as_dict=True)

		if error_logs:
			job_info["status"] = "Failed"
			job_info["error_message"] = error_logs[0].error or "Execution error logged."
			job_info["last_execution"] = str(error_logs[0].creation)
			failed_count += 1
		elif rec_count > 0 or job["doctype"] is None:
			job_info["status"] = "Success"
			success_count += 1
		else:
			job_info["status"] = "Pending"
			job_info["error_message"] = f"No synced records found for date {target_date}"
			pending_count += 1

		result_jobs.append(job_info)

	total_jobs = len(JOBS_REGISTRY)
	success_rate = round((success_count / total_jobs * 100), 1) if total_jobs > 0 else 0.0

	return {
		"sync_date": target_date,
		"auto_sync_enabled": bool(auto_sync_enabled),
		"summary": {
			"total_jobs": total_jobs,
			"success_count": success_count,
			"failed_count": failed_count,
			"disabled_count": 0,
			"pending_count": pending_count,
			"success_rate": success_rate
		},
		"jobs": result_jobs
	}


@frappe.whitelist()
def trigger_manual_sync(job_key, sync_date=None):
	job = next((j for j in JOBS_REGISTRY if j["key"] == job_key), None)
	if not job:
		frappe.throw(_("Invalid job key specified."))

	method_path = job["method"]
	module_name, func_name = method_path.rsplit(".", 1)

	try:
		mod = __import__(module_name, fromlist=[func_name])
		fn = getattr(mod, func_name)

		res = fn()
		frappe.db.commit()
		return {"status": "success", "message": f"Successfully executed {job['title']}.", "result": str(res)}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Manual Sync Execution Error for {job['title']}: {str(e)}", f"{job['title']} Manual Error")
		return {"status": "error", "message": f"Error executing {job['title']}: {str(e)}"}


@frappe.whitelist()
def toggle_drishti_auto_sync(enabled):
	val = 1 if cint(enabled) else 0
	frappe.db.set_single_value("Drishti Settings", "auto_sync", val)
	frappe.db.commit()
	return {"status": "success", "auto_sync_enabled": bool(val)}
