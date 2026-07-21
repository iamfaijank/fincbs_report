import frappe
import json
from frappe.boot import load_translations

no_cache = 1


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()  # nosempgrep
	context.csrf_token = csrf_token
	context.boot = json.dumps(get_boot(), default=str)
	context.site_name = frappe.local.site
	return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(frappe._("This method is only meant for developer mode"))
	return get_boot()


def get_boot():
	bootinfo = frappe._dict(
		{
			"site_name": frappe.local.site,
			"default_route": get_default_route(),
		}
	)

	bootinfo.lang = frappe.local.lang
	load_translations(bootinfo)

	return bootinfo


def get_default_route():
	return "/drishti"


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_report_preference():
	user = frappe.session.user
	if not user or user == "Guest":
		return {"user": user or "Guest", "zone": [], "region": [], "district": [], "sol_id": []}

	pref = frappe.db.get_value(
		"Report Preference",
		{"user": user, "enabled": 1},
		["name"],
	)
	if not pref:
		return {"user": user, "zone": [], "region": [], "district": [], "sol_id": []}

	doc = frappe.get_doc("Report Preference", pref)
	return {
		"user": user,
		"zone": [d.zone for d in doc.get("zone", []) if d.zone],
		"region": [d.region for d in doc.get("region", []) if d.region],
		"district": [d.district for d in doc.get("district", []) if d.district],
		"sol_id": [d.sol_id for d in doc.get("sol_id", []) if d.sol_id],
	}


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_filter_options():
	zones = frappe.get_all("Zone", fields=["name"], order_by="name asc")
	regions = frappe.get_all("Region", fields=["name"], order_by="name asc")
	districts = frappe.get_all("District", fields=["name"], order_by="name asc")
	sol_ids = frappe.get_all("Sol ID", fields=["name"], order_by="name asc") if frappe.db.exists("DocType", "Sol ID") else []

	return {
		"zones": [z.name for z in zones],
		"regions": [r.name for r in regions],
		"districts": [d.name for d in districts],
		"sol_ids": [s.name for s in sol_ids],
	}
