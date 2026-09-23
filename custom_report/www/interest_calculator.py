import frappe


def get_context(context):
    # Role-dependent page must never be cached across users.
    context.no_cache = 1
    try:
        context.can_switch_db = "Migration" in (frappe.get_roles(frappe.session.user) or [])
    except Exception:
        context.can_switch_db = False
    try:
        context.csrf_token = frappe.sessions.get_csrf_token()
    except Exception:
        context.csrf_token = getattr(frappe.session, "csrf_token", "") or ""
