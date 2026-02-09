import frappe
from typing import Dict, Optional
from frappe.utils import flt, getdate


# ============================================================================
# BRANCH APIs
# ============================================================================

from custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard import get_user_report_permissions

@frappe.whitelist()
def search_branches(txt: str):
    """
    Search branches by SOL ID or Branch Name
    Used for header search autosuggest
    Returns max 5 records
    """
    if not txt:
        return []

    user = frappe.session.user
    perms = get_user_report_permissions(user)

    conditions = ["(sol_id LIKE %(txt)s OR branch LIKE %(txt)s)"]
    params = {"txt": f"%{txt}%"}

    if perms.get("is_restricted"):
        # Priority 1: Specific SOL IDs
        if perms.get("sol_ids"):
            conditions.append("sol_id IN %(sol_ids)s")
            params["sol_ids"] = perms["sol_ids"]
        
        # Priority 2: Zone & Region
        else:
            if perms.get("zone_ids"):
                zone_regex = "|".join(perms["zone_ids"])
                conditions.append(f"zone REGEXP '({zone_regex})'")
            
            if not perms.get("all_regions") and perms.get("region_ids"):
                region_regex = "|".join(perms["region_ids"])
                conditions.append(f"region REGEXP '({region_regex})'")
            
            if not perms.get("zone_ids") and not perms.get("region_ids") and not perms.get("all_regions"):
                conditions.append("1=0")

    where_clause = " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT
            name,
            sol_id,
            branch,
            zone,
            region,
            state
        FROM `tabSahayog Branch`
        WHERE {where_clause}
        ORDER BY sol_id ASC
        LIMIT 10
        """,
        params,
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
# Employee DATA API
# ============================================================================

import frappe
from frappe.query_builder import DocType, functions as fn, Case
from frappe.utils import get_first_day, get_last_day, today

@frappe.whitelist()
def get_employee_details_by_sol(sol_id: str):
    """
    Fetch comprehensive employee details including monthly lead generation 
    and conversion performance metrics filtered by SOL ID.
    
    Args:
        sol_id (str): The Branch/Service Outlet ID to filter employees.
        
    Returns:
        dict: Success status, record count, and data containing employee info 
              plus lead analytics (Total, Converted, and Ratio).
    """
    if not sol_id:
        return {"status": "error", "message": "SOL ID is required"}

    try:
        # 1. Initialize Doctypes for Query Builder
        Employee = DocType("Employee")
        Lead = DocType("Lead")

        # 2. Define the date range for the current month
        # This ensures we only count leads created between the 1st and today
        start_date = get_first_day(today())
        end_date = get_last_day(today())

        # 3. Construct the Query
        # We use a LEFT JOIN to ensure employees are listed even if they have 0 leads.
        # The join condition matches Employee.user_id with Lead.lead_owner.
        query = (
            frappe.qb.from_(Employee)
            .left_join(Lead).on(
                (Employee.user_id == Lead.lead_owner) & 
                (Lead.creation.between(start_date, end_date))
            )
            .select(
                # Employee Identity and Contact Fields
                Employee.sol_id,
                Employee.employee_name,
                Employee.employee_number,
                Employee.user_id,
                Employee.designation,
                Employee.cell_number,
                Employee.date_of_joining,
                Employee.pip_status,
                
                # Aggregate Lead Analytics
                fn.Count(Lead.name).as_("total_leads"),
                fn.Sum(
                    Case().when(Lead.status == "Converted", 1).else_(0)
                ).as_("total_converted")
            )
            .where(Employee.sol_id == sol_id)
            .groupby(Employee.name)
            .orderby(Employee.employee_name)
        )

        # 4. Execute the query and fetch results as a list of dictionaries
        employee_records = query.run(as_dict=True)

        # 5. Post-process data to calculate Conversion Ratios
        for record in employee_records:
            total = record.get("total_leads") or 0
            # SQL SUM on Case returns float (e.g. 1.0), converting to int for clean JSON
            converted = int(record.get("total_converted") or 0)
            
            record["total_converted"] = converted
            
            # Calculate conversion ratio percentage
            if total > 0:
                conversion_ratio = (converted / total) * 100
                record["conversion_ratio"] = f"{conversion_ratio:.2f}%"
            else:
                record["conversion_ratio"] = "0.00%"

        return {
            "status": "success",
            "count": len(employee_records),
            "data": employee_records
        }

    except Exception as e:
        # Log the full error traceback in Frappe Error Log for debugging
        frappe.log_error(frappe.get_traceback(), "Employee Lead Details API Error")
        return {
            "status": "error", 
            "message": "An internal error occurred while fetching details."
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

def get_achievement_category(percentage):
    """
    Returns only the Category Name based on percentage
    """
    p = flt(percentage)
    if p > 100: return "Pinnacle"
    if p >= 80: return "Master"
    if p >= 60: return "Accelerator"
    if p >= 40: return "Starter"
    if p >= 20: return "Learner"
    return "Zero Level"

def format_ui_output(achievement, target):
    """
    Calculates percentage and formats it as '00.00 %'
    """
    ach = flt(achievement)
    tar = flt(target)
    perc = (ach / tar * 100) if tar > 0 else 0
    
    return {
        "target": tar,
        "achievement": ach,
        "percentage": "{:05.2f} %".format(perc),
        "category": get_achievement_category(perc)
    }

@frappe.whitelist()
def get_performance_data(sol_id, date=None):
    try:
        # 1. Fetch Latest Record for the SOL
        # Agar date pass nahi ki, toh latest record uthayega
        latest_record = frappe.db.sql("""
            SELECT date, achievement, yearly_achievement 
            FROM `tabBranch Category Report`
            WHERE sol_id = %s 
            ORDER BY date DESC 
            LIMIT 1
        """, (sol_id,), as_dict=1)

        if not latest_record:
            return {
                "status": "no_data",
                "message": "No data found for this branch",
                "data_exists": False
            }

        res = latest_record[0]
        report_date = res.date
        
        # 2. Get Targets
        fiscal_year = get_fiscal_year(report_date)
        targets = get_targets(sol_id, fiscal_year) 

        # 3. Final Response with Monthly, YTD, and Yearly segments
        return {
            "status": "success",
            "data_exists": True,
            "sol_id": sol_id,
            "report_date": report_date.strftime('%Y-%m-%d'),
            "financial_year": fiscal_year,
            "performance": {
                "monthly": format_ui_output(res.achievement, targets.get("monthly", 0)),
                "ytd": format_ui_output(res.achievement, targets.get("ytd", 0)),
                "yearly": format_ui_output(res.yearly_achievement, targets.get("yearly", 0))
            }
        }

    except Exception as e:
        frappe.log_error(f"Branch Performance Error: {sol_id}", frappe.get_traceback())
        return {
            "status": "error", 
            "message": str(e)
        }