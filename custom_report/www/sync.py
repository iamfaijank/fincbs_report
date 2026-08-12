# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint
from custom_report.api import get_automation_sync_status, trigger_manual_sync, toggle_drishti_auto_sync

no_cache = 1

def get_context(context):
	context.title = "Automation Sync Tracker"
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.site_name = frappe.local.site
	context.auto_sync_enabled = cint(frappe.db.get_single_value("Drishti Settings", "auto_sync"))
	try:
		context.initial_sync_data = frappe.as_json(get_automation_sync_status())
	except Exception as e:
		frappe.log_error(f"Sync tracker context error: {str(e)}")
		context.initial_sync_data = "{}"
	return context
