import frappe
from custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard import get_user_report_permissions

def get_context(context):
    user = frappe.session.user
    
    # Dashboard wala same logic reuse karein
    perms = get_user_report_permissions(user)
    
    # Template context mein permissions bhej dein
    context.user_permissions = perms
    
    # Agar user restricted hai, to filter values template ko pass karein
    if perms.get("is_restricted"):
        context.allowed_zones = perms.get("zones", [])
        context.allowed_regions = perms.get("regions", [])
        context.allowed_sol_ids = perms.get("sol_ids", [])
        context.all_regions_allowed = perms.get("all_regions", False)
    else:
        context.allowed_zones = []
        context.allowed_regions = []
        context.allowed_sol_ids = []
        context.all_regions_allowed = True

    # Check if user designation is BRANCH MANAGER
    user_designation = ""
    employee = frappe.db.get_value("Employee", {"user_id": user}, ["designation"], as_dict=True)
    if employee and employee.designation:
        user_designation = employee.designation.upper().strip()
    context.is_branch_manager = (user_designation == "BRANCH MANAGER")
