import frappe
from frappe.utils import getdate


@frappe.whitelist()
def search_branches(txt):
    """
    Search branches by SOL ID or branch name
    """
    if not txt:
        return []

    return frappe.db.get_list(
        "Sahayog Branch",
        filters={
            "sol_id": ["like", f"%{txt}%"],
        },
        fields=["name", "sol_id", "branch"],
        limit_page_length=10,
    )


@frappe.whitelist()
def get_branch_data(sol_id):
    """
    Get branch master data by SOL ID
    """
    return frappe.db.get_list(
        "Sahayog Branch",
        filters={"sol_id": sol_id},
        fields=[
            "name",
            "sol_id",
            "branch",
            "state",
            "state_code",
            "district",
            "zone",
            "region",
            "email",
            "address",
        ],
        limit_page_length=1,
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
        limit_page_length=1,
    )
    return data[0] if data else {}


@frappe.whitelist()
def get_performance_data(sol_id, date):
    """
    Get branch performance data for a specific date
    Returns data_exists + latest_date for frontend integration
    """
    try:
        frappe.logger().info(f"Fetching performance data for SOL: {sol_id}, Date: {date}")

        # 1. EXACT DATE MATCH CHECK (priority 1)
        branch_category_data = frappe.db.get_list(
            "Branch Category Report",
            filters={
                "sol_id": sol_id,
                "date": date  # Exact date match
            },
            fields=["name", "sol_id", "date", "achievement", "yearly_achievement"],
            limit_page_length=1,
        )

        # 2. If exact date data exists → return full data
        if branch_category_data:
            monthly_achievement = float(branch_category_data[0].get("achievement", 0) or 0)
            yearly_achievement = float(branch_category_data[0].get("yearly_achievement", 0) or 0)

            # Get targets
            fiscal_year = get_fiscal_year(date)
            targets = get_targets(sol_id, fiscal_year)

            return {
                "data_exists": True,
                "monthly_achievement": monthly_achievement,
                "monthly_target": targets.get("monthly", 0),
                "yearly_achievement": yearly_achievement,
                "yearly_target": targets.get("yearly", 0),
                "ytd_target": targets.get("ytd", targets.get("ytd ", 0)),
                "selected_date": date,
                "financial_year": fiscal_year,
            }

        # 3. NO EXACT DATE DATA → Find latest available date
        latest_record = frappe.db.sql("""
            SELECT date, achievement, yearly_achievement 
            FROM `tabBranch Category Report`
            WHERE sol_id = %s 
            ORDER BY date DESC 
            LIMIT 1
        """, (sol_id,), as_dict=1)

        if latest_record:
            latest_date = latest_record[0].date
            frappe.logger().info(f"Latest data found for {sol_id}: {latest_date}")

            return {
                "data_exists": False,
                "latest_date": latest_date.strftime('%Y-%m-%d'),
            }

        # 4. NO DATA AT ALL for this branch
        return {
            "data_exists": False,
            "latest_date": None
        }

    except Exception as e:
        frappe.log_error(
            title="Branch Performance Data Error",
            message=f"SOL: {sol_id}, Date: {date}, Error: {str(e)}"
        )
        return {
            "data_exists": False,
            "latest_date": None,
            "error": str(e)
        }


@frappe.whitelist()
def get_crm_data(sol_id, from_date, to_date):
    """
    Fetch CRM lead statistics for a branch within date range

    Lead Status Options:
    - Lead
    - Converted
    - Follow Up
    - Not Interested

    Note: Lead doctype uses 'sol_id' field to link to branches
    """
    try:
        from frappe.utils import getdate

        # Validate dates
        from_date = getdate(from_date)
        to_date = getdate(to_date)

        # Base filters - using sol_id field directly
        base_filters = {
            "sol_id": sol_id,
            "creation": ["between", [from_date, to_date]]
        }

        # Total leads (all statuses)
        total_leads = frappe.db.count("Lead", filters=base_filters)

        # Converted leads (status = "Converted")
        converted_filters = base_filters.copy()
        converted_filters["status"] = "Converted"
        converted_leads = frappe.db.count("Lead", filters=converted_filters)

        # Follow up leads (status = "Follow Up")
        follow_up_filters = base_filters.copy()
        follow_up_filters["status"] = "Follow Up"
        follow_up = frappe.db.count("Lead", filters=follow_up_filters)

        # Not interested leads (status = "Not Interested")
        not_interested_filters = base_filters.copy()
        not_interested_filters["status"] = "Not Interested"
        not_interested = frappe.db.count("Lead", filters=not_interested_filters)

        frappe.logger().info(
            f"CRM Data for SOL {sol_id} ({from_date} to {to_date}): "
            f"Total={total_leads}, Converted={converted_leads}, "
            f"FollowUp={follow_up}, NotInterested={not_interested}"
        )

        return {
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "follow_up": follow_up,
            "not_interested": not_interested,
            "from_date": from_date.strftime('%Y-%m-%d'),
            "to_date": to_date.strftime('%Y-%m-%d')
        }

    except Exception as e:
        frappe.log_error(
            title="CRM Data Fetch Error",
            message=f"SOL: {sol_id}, From: {from_date}, To: {to_date}, Error: {str(e)}"
        )
        return {
            "total_leads": 0,
            "converted_leads": 0,
            "follow_up": 0,
            "not_interested": 0,
            "from_date": str(from_date),
            "to_date": str(to_date),
            "error": str(e)
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_fiscal_year(date_str):
    """
    Calculate Indian Financial Year (Apr 1 - Mar 31)

    Args:
        date_str: Date string in any valid format

    Returns:
        str: Financial year in format "YYYY-YYYY" (e.g., "2024-2025")
    """
    date_obj = getdate(date_str)
    year = date_obj.year
    month = date_obj.month

    if month >= 4:  # April onwards
        return f"{year}-{year+1}"
    else:  # Jan-Mar
        return f"{year-1}-{year}"


def get_targets(sol_id, fiscal_year):
    """
    Get targets from Target Vs Achievement doctype

    Args:
        sol_id: SOL ID of the branch
        fiscal_year: Financial year in format "YYYY-YYYY"

    Returns:
        dict: Dictionary with target types as keys and target values
    """
    target_data = frappe.db.sql("""
        SELECT type, target 
        FROM `tabTarget Vs Achivement`
        WHERE sol_id = %s AND financial_year = %s
    """, (sol_id, fiscal_year), as_dict=1)

    targets = {}
    for item in target_data:
        type_key = item.type.lower().strip()
        targets[type_key] = float(item.target or 0)

    return targets