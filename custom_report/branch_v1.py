import frappe
from frappe.utils import getdate
from typing import Dict, Optional


# ============================================================================
# BRANCH APIs
# ============================================================================

@frappe.whitelist()
def search_branches(txt: str):
    """
    Search branches by SOL ID or Branch Name
    Used for header search autosuggest
    Returns max 5 records
    """
    if not txt:
        return []

    txt_like = f"%{txt}%"

    return frappe.db.sql(
        """
        SELECT
            name,
            sol_id,
            branch,
            zone,
            region,
            state
        FROM `tabSahayog Branch`
        WHERE sol_id LIKE %(txt)s OR branch LIKE %(txt)s
        ORDER BY sol_id ASC
        LIMIT 10
        """,
        {"txt": txt_like},
        as_dict=True,
    )

@frappe.whitelist()
def get_branch_header_data(sol_id: str):
    """
    Fetch minimal branch data required for header & URL hydration
    """
    if not sol_id:
        return {}

    return frappe.db.get_value(
        "Sahayog Branch",
        {"sol_id": sol_id},
        [
            "sol_id",
            "branch",
            "zone",
            "region",
            "state",
            "email"
        ],
        as_dict=True,
    ) or {}


@frappe.whitelist()
def get_branch_profile_data(sol_id: str):
    """
    Fetch Branch Profile Data based on SOL ID
    """
    return frappe.db.get_value(
        "Branch Profile Data",
        {"sol_id": sol_id},
        "*",
        as_dict=True,
    ) or {}


# ============================================================================
# PERFORMANCE DATA API
# ============================================================================

@frappe.whitelist()
def get_performance_data(sol_id: str, date: Optional[str] = None):
    """
    Get branch performance data for a specific date
    If date not provided, latest available date is used
    """
    try:
        selected_date = date or get_latest_performance_date(sol_id)

        if not selected_date:
            return {
                "data_exists": False,
                "latest_date": None,
                "message": "No performance data available",
            }

        record = frappe.db.get_value(
            "Branch Category Report",
            {"sol_id": sol_id, "date": selected_date},
            ["achievement", "yearly_achievement"],
            as_dict=True,
        )

        if record:
            fiscal_year = get_fiscal_year(selected_date)
            targets = get_targets(sol_id, fiscal_year)

            return {
                "data_exists": True,
                "monthly_achievement": float(record.achievement or 0),
                "monthly_target": targets.get("monthly", 0),
                "yearly_achievement": float(record.yearly_achievement or 0),
                "yearly_target": targets.get("yearly", 0),
                "ytd_target": targets.get("ytd", 0),
                "selected_date": selected_date,
                "financial_year": fiscal_year,
            }

        latest_date = get_latest_performance_date(sol_id)
        return {
            "data_exists": False,
            "latest_date": latest_date,
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Branch Performance API Error")
        return {
            "data_exists": False,
            "latest_date": None,
        }


# ============================================================================
# CRM DATA API (OPTIMIZED – SINGLE QUERY)
# ============================================================================

@frappe.whitelist()
def get_crm_data(sol_id: str, from_date: str, to_date: str):
    """
    Fetch CRM lead statistics for a branch within date range
    """
    try:
        from_date = getdate(from_date)
        to_date = getdate(to_date)

        rows = frappe.db.sql(
            """
            SELECT
                l.status,
                COUNT(DISTINCT l.name) AS lead_count,
                COALESCE(SUM(lp.product_amount), 0) AS total_amount
            FROM `tabLead` l
            LEFT JOIN `tabLead Product` lp ON lp.parent = l.name
            WHERE
                l.sol_id = %s
                AND l.creation BETWEEN %s AND %s
            GROUP BY l.status
            """,
            (sol_id, from_date, to_date),
            as_dict=True,
        )

        result = {
            "total_leads": 0,
            "total_leads_amount": 0,
            "converted_leads": 0,
            "converted_amount": 0,
            "follow_up": 0,
            "follow_up_amount": 0,
            "not_interested": 0,
            "not_interested_amount": 0,
            "from_date": from_date.strftime("%Y-%m-%d"),
            "to_date": to_date.strftime("%Y-%m-%d"),
        }

        for row in rows:
            result["total_leads"] += row.lead_count
            result["total_leads_amount"] += row.total_amount

            if row.status == "Converted":
                result["converted_leads"] = row.lead_count
                result["converted_amount"] = row.total_amount
            elif row.status == "Follow Up":
                result["follow_up"] = row.lead_count
                result["follow_up_amount"] = row.total_amount
            elif row.status == "Not Interested":
                result["not_interested"] = row.lead_count
                result["not_interested_amount"] = row.total_amount

        return result

    except Exception:
        frappe.log_error(frappe.get_traceback(), "CRM Data API Error")
        return {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_latest_performance_date(sol_id: str) -> Optional[str]:
    """
    Fetch latest available performance date for a branch
    """
    return frappe.db.get_value(
        "Branch Category Report",
        {"sol_id": sol_id},
        "date",
        order_by="date desc",
    )


def get_fiscal_year(date_str: str) -> str:
    """
    Calculate Indian Financial Year (Apr–Mar)
    """
    date_obj = getdate(date_str)
    year = date_obj.year

    if date_obj.month >= 4:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"


def get_targets(sol_id: str, fiscal_year: str) -> Dict[str, float]:
    """
    Get targets from Target Vs Achievement doctype
    """
    rows = frappe.db.get_all(
        "Target Vs Achivement",
        filters={
            "sol_id": sol_id,
            "financial_year": fiscal_year,
        },
        fields=["type", "target"],
    )

    return {
        row.type.lower().strip(): float(row.target or 0)
        for row in rows
    }


# ============================================================================
# DRISHTI DASHBOARD API
# ============================================================================

@frappe.whitelist()
def get_drishti_dashboard_data(financial_year: str, filters: str):
	"""
	Fetch all master data required for the Drishti dashboard.
	This is a complex and potentially slow query, so it should be used with care.
	"""
	# NOTE: This is a placeholder implementation.
	# The actual implementation will require fetching and processing data
	# from various doctypes like Sahayog Branch, Branch Category Report, etc.

	dummy_data = {
		"consolidated_branches": [
			{
				"sol_id": "1001",
				"branch_name": "GONDIA",
				"zone": "ZONE-1",
				"region": "REGION-1",
				"latest_category": "Pinnacle",
				"monthly_data": {
					"APR": {"category": "Pinnacle", "target": 50000, "achievement": 60000},
					"MAY": {"category": "Pinnacle", "target": 55000, "achievement": 58000},
				},
			},
			{
				"sol_id": "1002",
				"branch_name": "NAGPUR",
				"zone": "ZONE-1",
				"region": "REGION-1",
				"latest_category": "Master",
				"monthly_data": {
					"APR": {"category": "Accelerator", "target": 40000, "achievement": 35000},
					"MAY": {"category": "Master", "target": 42000, "achievement": 45000},
				},
			},
		],
		"months": {
			"APR": {
				"grouped_by_category": {
					"Pinnacle": {"ZONE-1": {"branch_count": 1}},
					"Accelerator": {"ZONE-1": {"branch_count": 1}},
				}
			},
			"MAY": {
				"grouped_by_category": {
					"Pinnacle": {"ZONE-1": {"branch_count": 1}},
					"Master": {"ZONE-1": {"branch_count": 1}},
				}
			},
		},
		"financial_year": financial_year,
	}

	return {
		"status": "success",
		"data": dummy_data,
	}

