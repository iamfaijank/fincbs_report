# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
import frappe.sessions
from frappe.utils import cint

no_cache = 1

def get_context(context):
	context.title = "Automation Sync Tracker"
	try:
		context.csrf_token = frappe.sessions.get_csrf_token()
	except Exception:
		context.csrf_token = getattr(frappe.session, "csrf_token", "") or ""
	context.site_name = getattr(frappe.local, "site", "")
	context.auto_sync_enabled = cint(frappe.db.get_single_value("Drishti Settings", "auto_sync"))
	context.initial_sync_data = "{}"
	return context

