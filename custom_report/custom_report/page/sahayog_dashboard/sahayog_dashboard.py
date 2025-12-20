# sahayog_dashboard.py
#
# Backend for Sahayog MIS Dashboard with date-timeline and proper month mapping

import frappe
from frappe import _
from frappe.utils import getdate, formatdate, add_days
from datetime import datetime


@frappe.whitelist()
def get_available_dates():
    """
    Get list of unique dates from Branch Category Report.
    Excludes Sundays and returns last 30 days.
    Returns: List of dates in descending order (latest first)
    """
    dates = frappe.db.sql(
        """
        SELECT DISTINCT date 
        FROM `tabBranch Category Report` 
        WHERE date IS NOT NULL 
        ORDER BY date DESC 
        LIMIT 30
        """,
        as_dict=True,
    )

    available_dates = []
    for row in dates:
        date_obj = getdate(row["date"])
        # Exclude Sundays (weekday 6)
        if date_obj.weekday() != 6:
            available_dates.append(
                {
                    "date": str(date_obj),
                    "display": formatdate(date_obj, "EEE dd"),
                    "display_full": formatdate(date_obj, "dd MMM yyyy"),
                    "day_name": formatdate(date_obj, "EEE"),
                    "day_num": date_obj.day,
                    "month": date_obj.month,
                    "year": date_obj.year,
                }
            )

    return available_dates


@frappe.whitelist()
def get_dashboard_data(selected_date=None):
    """
    Get dashboard data for selected date with proper month-wise breakdown.
    
    Args:
        selected_date: Date string (YYYY-MM-DD). If None, latest date is used.
    
    Returns:
        Dict with aggregated data grouped by zone+category and proper month columns
    """
    settings = frappe.get_single("Report Settings")

    if not settings.is_active:
        frappe.throw(_("Data source is not active"))

    # Get latest date if not provided
    if not selected_date:
        dates = get_available_dates()
        if dates:
            selected_date = dates[0]["date"]
        else:
            return {"zones": [], "grand_total": {}, "selected_date": None}

    selected_date_obj = getdate(selected_date)
    
    # Master doctype
    doctype_name = settings.master_doctype or "Branch Category Report"

    # Fetch data for selected date ONLY
    branch_data = frappe.get_all(
        doctype_name,
        filters={"date": selected_date},
        fields=[
            "zone",
            "region",
            "district",
            "branch",
            "sol_id",
            "achievement",
            "branch_score",
            "branch_category",
            "date",
        ],
    )

    # Get yearly targets
    financial_year = get_financial_year(selected_date)
    yearly_targets = get_yearly_targets(financial_year)

    # Aggregate with proper month mapping
    aggregated = aggregate_with_month_mapping(
        branch_data, yearly_targets, selected_date_obj
    )

    return aggregated


def get_financial_year(date_str=None):
    """
    Get financial year string from date.
    Returns: "2025-2026"
    """
    if not date_str:
        date = getdate()
    else:
        date = getdate(date_str)

    if date.month > 3:
        return f"{date.year}-{date.year + 1}"
    else:
        return f"{date.year - 1}-{date.year}"


def get_yearly_targets(financial_year):
    """
    Fetch yearly targets from Target Vs Achivement.
    Returns: {sol_id: target_amount}
    """
    targets = frappe.get_all(
        "Target Vs Achivement",
        filters={"type": "Yearly", "financial_year": financial_year},
        fields=["sol_id", "target"],
    )

    targets_map = {}
    for t in targets:
        sol_id = str(t.sol_id) if t.sol_id else None
        if sol_id:
            targets_map[sol_id] = float(t.target or 0)

    return targets_map


def aggregate_with_month_mapping(data, yearly_targets, selected_date_obj):
    """
    Aggregate data with proper month-wise mapping.
    
    Logic:
    - If selected_date is in December 2025, show actual achievement in DEC-25 column
    - For future months (JAN-26, FEB-26, MAR-26), show N/A or 0
    - Target is divided equally across 4 months (DEC, JAN, FEB, MAR)
    
    Returns: Dict with zones, categories, and grand_total
    """
    zone_map = {}

    # Define month keys based on financial year pattern
    # For DJFM drive: Dec, Jan, Feb, Mar
    month_keys = ["dec", "jan", "feb", "mar"]
    
    # Map month number to month key
    month_number_to_key = {
        12: "dec",  # December
        1: "jan",   # January
        2: "feb",   # February
        3: "mar",   # March
    }

    # Get current month from selected date
    selected_month = selected_date_obj.month
    selected_year = selected_date_obj.year

    for row in data:
        zone_name = row.get("zone") or "Unknown"
        category = row.get("branch_score") or "Unknown"
        sol_id = str(row.get("sol_id")) if row.get("sol_id") else None

        # Initialize zone
        if zone_name not in zone_map:
            zone_map[zone_name] = {}

        # Initialize category within zone
        if category not in zone_map[zone_name]:
            zone_map[zone_name][category] = {
                "zone": zone_name,
                "category": category,
                "branch_count": 0,
                "dec": {"tgt": 0.0, "ach": 0.0, "available": False},
                "jan": {"tgt": 0.0, "ach": 0.0, "available": False},
                "feb": {"tgt": 0.0, "ach": 0.0, "available": False},
                "mar": {"tgt": 0.0, "ach": 0.0, "available": False},
                "total": {"tgt": 0.0, "ach": 0.0},
            }

        # Get yearly target
        yearly_target = 0.0
        if sol_id and sol_id in yearly_targets:
            yearly_target = float(yearly_targets[sol_id])

        # Total achievement from selected date record
        total_ach = float(row.get("achievement") or 0)

        # Divide yearly target equally across 4 months
        monthly_target = yearly_target / 4.0

        # Update category aggregation
        cat_data = zone_map[zone_name][category]
        cat_data["branch_count"] += 1
        cat_data["total"]["tgt"] += yearly_target
        cat_data["total"]["ach"] += total_ach

        # Set monthly targets (all 4 months get equal target)
        for month_key in month_keys:
            cat_data[month_key]["tgt"] += monthly_target

        # Set achievement ONLY for current month
        current_month_key = month_number_to_key.get(selected_month)
        if current_month_key:
            cat_data[current_month_key]["ach"] += total_ach
            cat_data[current_month_key]["available"] = True

    # Flatten to list
    result = []
    for zone_name, categories in zone_map.items():
        for category, cat_data in categories.items():
            result.append(cat_data)

    return result


@frappe.whitelist()
def get_drill_down_data(zone, category, selected_date=None):
    """
    Get branch-level drill-down data.
    """
    settings = frappe.get_single("Report Settings")
    doctype_name = settings.master_doctype or "Branch Category Report"

    if not selected_date:
        dates = get_available_dates()
        if dates:
            selected_date = dates[0]["date"]

    selected_date_obj = getdate(selected_date)

    # Build filters
    filters = {"date": selected_date}
    if zone == "ALL":
        filters["branch_score"] = category
    else:
        filters["zone"] = zone
        filters["branch_score"] = category

    branches = frappe.get_all(
        doctype_name,
        filters=filters,
        fields=[
            "branch",
            "sol_id",
            "region",
            "district",
            "zone",
            "achievement",
            "branch_score",
            "branch_category",
            "date",
        ],
        order_by="zone asc, branch asc",
    )

    # Get yearly targets
    sol_ids = [str(b.get("sol_id")) for b in branches if b.get("sol_id")]
    yearly_targets = {}
    financial_year = get_financial_year(selected_date)

    if sol_ids:
        targets = frappe.get_all(
            "Target Vs Achivement",
            filters={
                "sol_id": ["in", sol_ids],
                "type": "Yearly",
                "financial_year": financial_year,
            },
            fields=["sol_id", "target"],
        )

        for t in targets:
            sol_id = str(t.sol_id) if t.sol_id else None
            if sol_id:
                yearly_targets[sol_id] = float(t.target or 0)

    # Enhance branch data with month mapping
    month_number_to_key = {12: "dec", 1: "jan", 2: "feb", 3: "mar"}
    selected_month = selected_date_obj.month
    current_month_key = month_number_to_key.get(selected_month)

    for branch in branches:
        sol_id = str(branch.get("sol_id")) if branch.get("sol_id") else None

        yearly_target = 0.0
        if sol_id and sol_id in yearly_targets:
            yearly_target = float(yearly_targets[sol_id])

        monthly_target = yearly_target / 4.0
        total_ach = float(branch.get("achievement") or 0)

        # Branch data with month breakdown
        branch["category"] = branch.get("branch_score")
        branch["branch_name"] = branch.get("branch")
        branch["yearly_target"] = yearly_target
        branch["total_ach"] = total_ach

        # Month-wise breakdown
        branch["dec"] = {
            "tgt": monthly_target,
            "ach": total_ach if current_month_key == "dec" else 0,
            "available": current_month_key == "dec",
        }
        branch["jan"] = {
            "tgt": monthly_target,
            "ach": total_ach if current_month_key == "jan" else 0,
            "available": current_month_key == "jan",
        }
        branch["feb"] = {
            "tgt": monthly_target,
            "ach": total_ach if current_month_key == "feb" else 0,
            "available": current_month_key == "feb",
        }
        branch["mar"] = {
            "tgt": monthly_target,
            "ach": total_ach if current_month_key == "mar" else 0,
            "available": current_month_key == "mar",
        }

        # Achievement percentage
        if yearly_target > 0:
            branch["ach_pct"] = round((total_ach / yearly_target) * 100, 2)
        else:
            branch["ach_pct"] = 0.0

    return branches


@frappe.whitelist()
def get_branch_targets(selected_date=None):
    """
    Get yearly targets for Branch Targets tab.
    """
    financial_year = get_financial_year(selected_date)

    targets = frappe.get_all(
        "Target Vs Achivement",
        filters={"type": "Yearly", "financial_year": financial_year},
        fields=["sol_id", "target", "financial_year", "type"],
        order_by="sol_id asc",
        limit=1000,
    )

    return targets
