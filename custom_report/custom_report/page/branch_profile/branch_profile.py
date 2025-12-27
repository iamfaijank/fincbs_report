import frappe

@frappe.whitelist()
def search_branches(txt):
    if not txt:
        return []

    return frappe.db.get_list(
        "Sahayog Branch",
        filters={"sol_id": ["like", f"%{txt}%"]},
        fields=["name", "sol_id", "branch"],
        limit_page_length=10
    )


@frappe.whitelist()
def get_branch_data(sol_id):
    return frappe.db.get_list(
        "Sahayog Branch",
        filters={"sol_id": sol_id},
        fields=[
            "name", "sol_id", "branch",
            "state", "state_code",
            "district", "zone", "region", "email"
        ],
        limit_page_length=1
    )


@frappe.whitelist()
def get_branch_profile_data(sol_id):
    """
    Fetch Branch Profile Data based on SOL ID
    """
    data = frappe.db.get_list(
        "Branch Profile Data",
        filters={"sol_id": sol_id},
        fields="*",
        limit_page_length=1
    )
    return data[0] if data else None
