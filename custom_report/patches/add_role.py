import frappe
 
def execute():
    roles = [
        "HR Department Report",
        "JLL Department Report",
        "MIS Department Report",
        "Loan Department Report",
        "Audit Department Report",
        "Finance Department Report",
        "Operation Department Report",
        "Two Wheeler Department Report",
        "Branch Report",
        "Finacle Report Admin"
    ]
 
    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1
            }).insert(ignore_permissions=True)
 