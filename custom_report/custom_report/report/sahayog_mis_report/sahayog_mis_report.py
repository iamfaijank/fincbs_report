import frappe
from frappe import _
from frappe.utils import getdate, flt
import calendar


# ---------------------------------------------------------------------

def execute(filters=None):
    if not filters:
        filters = {}

    filters.setdefault("target_period", "Monthly")
    filters.setdefault("date", frappe.utils.today())

    print("\n================ REPORT EXECUTION =================")
    print(f"Filters Received : {filters}")
    print("==================================================\n")

    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


# ---------------------------------------------------------------------

def get_columns(filters):
    period = filters.get("target_period")

    return [
        {"fieldname": "zone", "label": _("Zone"), "fieldtype": "Data", "width": 120},
        {"fieldname": "region", "label": _("Region"), "fieldtype": "Data", "width": 120},
        {"fieldname": "district", "label": _("District"), "fieldtype": "Data", "width": 120},
        {"fieldname": "sol_id", "label": _("SOL ID"), "fieldtype": "Data", "width": 90},
        {"fieldname": "branch", "label": _("Branch"), "fieldtype": "Data", "width": 180},
        {
            "fieldname": "target",
            "label": _(f"{period} Target"),
            "fieldtype": "Currency",
            "options": "INR",
            "width": 140,
            "precision":0,
        },
        {
            "fieldname": "achievement",
            "label": _(f"{period} Achievement"),
            "fieldtype": "Currency",
            "options": "INR",
            "width": 140,
            "precision":0,
        },
        {
            "fieldname": "achievement_pct",
            "label": _("Achievement %"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 110,
        },
        {"fieldname": "grade", "label": _("Grade"), "fieldtype": "Data", "width": 80},
        {"fieldname": "category", "label": _("Category"), "fieldtype": "Data", "width": 120},
        {
            "fieldname": "shortfall",
            "label": _("Shortfall"),
            "fieldtype": "Currency",
            "options": "INR",
            "width": 140,
              "precision":0,
        },
    ]


# ---------------------------------------------------------------------

def get_data(filters):
    target_period = filters["target_period"]
    selected_date = filters["date"]
    zone_filter = filters.get("zone")

    branches = get_all_branches(zone_filter)
    targets = get_targets(target_period, selected_date)
    achievements = get_achievements(target_period, selected_date)

    result = []

    for b in branches:
        sol_id = b["sol_id"]

        target = flt(targets.get(sol_id))
        achievement = flt(achievements.get(sol_id))

        achievement_pct = (achievement / target * 100) if target else 0
        grade_info = calculate_category(achievement_pct)

        result.append({
            "zone": b["zone"],
            "region": b["region"],
            "district": b["district"],
            "sol_id": sol_id,
            "branch": b["branch"],
            "target": target,
            "achievement": achievement,
            "achievement_pct": achievement_pct,
            "grade": grade_info["grade"],
            "category": grade_info["category"],
            "shortfall": target - achievement,
        })

    return result


# ---------------------------------------------------------------------

def get_all_branches(zone=None):
    condition = ""
    params = {}

    if zone:
        condition = "AND zone = %(zone)s"
        params["zone"] = zone

    return frappe.db.sql(
        f"""
        SELECT DISTINCT
            sol_id, branch, zone, region, district
        FROM `tabBranch Category Report`
        WHERE docstatus < 2 {condition}
        ORDER BY zone, sol_id
        """,
        params,
        as_dict=1,
    )


# ---------------------------------------------------------------------

def get_targets(target_period, selected_date):
    current_date = getdate(selected_date)
    fy = get_financial_year(current_date)
    month_code = calendar.month_abbr[current_date.month].upper()

    print("\n============= TARGET DEBUG =============")
    print(f"Target Period : {target_period}")
    print(f"Selected Date : {current_date}")
    print(f"Month Code    : {month_code}")
    print(f"Financial Yr  : {fy}")

    if target_period == "Monthly":
        print("Fetching MONTHLY target")

        rows = frappe.db.sql(
            """
            SELECT sol_id, target
            FROM `tabTarget Vs Achivement`
            WHERE
                type = 'Monthly'
                AND financial_year = %(fy)s
                AND month = %(month)s
                AND docstatus < 2
            """,
            {"fy": fy, "month": month_code},
            as_dict=1,
        )

    elif target_period == "YTD":
        print("Fetching YTD target")

        rows = frappe.db.sql(
            """
            SELECT sol_id, target
            FROM `tabTarget Vs Achivement`
            WHERE
                type = 'YTD'
                AND financial_year = %(fy)s
                AND docstatus < 2
            """,
            {"fy": fy},
            as_dict=1,
        )

    else:
        print("Fetching YEARLY target")

        rows = frappe.db.sql(
            """
            SELECT sol_id, target
            FROM `tabTarget Vs Achivement`
            WHERE
                type = 'Yearly'
                AND financial_year = %(fy)s
                AND docstatus < 2
            """,
            {"fy": fy},
            as_dict=1,
        )

    print(f"Target Rows Fetched : {len(rows)}")
    print("=======================================\n")

    return {r["sol_id"]: flt(r["target"]) for r in rows}


# ---------------------------------------------------------------------

def get_achievements(target_period, selected_date):
    field = "achievement" if target_period == "Monthly" else "yearly_achievement"

    print("\n=========== ACHIEVEMENT DEBUG ===========")
    print(f"Target Period : {target_period}")
    print(f"Using Field   : {field}")
    print(f"Date Filter  : {selected_date}")
    print("========================================\n")

    rows = frappe.db.sql(
        f"""
        SELECT
            sol_id,
            CAST({field} AS DECIMAL(15,2)) AS achievement
        FROM `tabBranch Category Report`
        WHERE
            date = %(date)s
            AND docstatus < 2
        """,
        {"date": selected_date},
        as_dict=1,
    )

    return {r["sol_id"]: flt(r["achievement"]) for r in rows}


# ---------------------------------------------------------------------

def get_financial_year(date):
    """
    Returns Financial Year in DB format: YYYY-YYYY
    Example:
    Dec 2025 → 2025-2026
    Feb 2026 → 2025-2026
    """
    if date.month < 4:
        return f"{date.year - 1}-{date.year}"
    return f"{date.year}-{date.year + 1}"


# ---------------------------------------------------------------------

def calculate_category(pct):
    if pct > 100:
        return {"grade": "A+", "category": "Pinnacle"}
    if pct >= 80:
        return {"grade": "A", "category": "Master"}
    if pct >= 60:
        return {"grade": "B", "category": "Accelerator"}
    if pct >= 40:
        return {"grade": "C", "category": "Starter"}
    if pct >= 20:
        return {"grade": "D", "category": "Learner"}
    return {"grade": "E", "category": "Zero Level"}
