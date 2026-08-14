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
    Fetch Branch Profile Data based on SOL ID, dynamically overriding BDE, BDO, RO,
    and Actual Staff Count from Employee DocType.
    """
    profile_data = frappe.db.get_value(
        "Branch Profile Data",
        {"sol_id": sol_id},
        "*",
        as_dict=True,
    ) or {}

    if not sol_id:
        return profile_data

    sol_id_str = str(sol_id).strip()

    # Find Sahayog Branch doc names and details if any
    branch_docs = frappe.db.get_all(
        "Sahayog Branch",
        filters=[["sol_id", "=", sol_id_str]],
        fields=["name", "branch", "sol_id"],
    )

    possible_branch_values = [sol_id_str]
    for bd in branch_docs:
        if bd.get("name"):
            possible_branch_values.append(bd["name"])
        if bd.get("branch"):
            possible_branch_values.append(bd["branch"])
            clean_b = bd["branch"].replace(" BRANCH", "").replace("Branch", "").strip()
            if clean_b:
                possible_branch_values.append(clean_b)
        if bd.get("sol_id"):
            possible_branch_values.append(bd["sol_id"])

    possible_branch_values = list(set(possible_branch_values))

    counts_query = """
        SELECT
            SUM(CASE WHEN designation LIKE %(bde)s THEN 1 ELSE 0 END) as bde_count,
            SUM(CASE WHEN designation LIKE %(bdo)s THEN 1 ELSE 0 END) as bdo_count,
            SUM(CASE WHEN designation LIKE %(ro)s THEN 1 ELSE 0 END) as ro_count,
            COUNT(*) as total_active_staff
        FROM `tabEmployee`
        WHERE status = 'Active'
          AND (sahayog_branch IN %(branches)s OR sol_id IN %(branches)s OR branch IN %(branches)s)
    """
    params = {
        "bde": "%Business Development Executive%",
        "bdo": "%Block Development Officer%",
        "ro": "%Relationship Officer%",
        "branches": possible_branch_values,
    }

    counts = frappe.db.sql(counts_query, params, as_dict=True)
    if counts and counts[0]:
        c = counts[0]
        profile_data["bde"] = int(c.get("bde_count") or 0)
        profile_data["bdo"] = int(c.get("bdo_count") or 0)
        profile_data["ro"] = int(c.get("ro_count") or 0)
        if "staff_count" not in profile_data or not profile_data.get("staff_count"):
            profile_data["staff_count"] = int(c.get("total_active_staff") or 0)

    return profile_data


@frappe.whitelist()
def get_bm_details_from_employee(sol_id: str):
    """
    Fetch Branch Manager (BM) details for a given SOL ID from Employee DocType.
    Filters employees by sahayog_branch matching sol_id or branch name, and designation LIKE '%Branch Manager%'.
    Also fetches Reporting Person details from Employee.reports_to.
    """
    if not sol_id:
        return {"status": "error", "message": "SOL ID is required", "data": []}

    sol_id_str = str(sol_id).strip()

    # Find Sahayog Branch doc names and details if any
    branch_docs = frappe.db.get_all(
        "Sahayog Branch",
        filters=[["sol_id", "=", sol_id_str]],
        fields=["name", "branch", "sol_id"],
    )

    possible_branch_values = [sol_id_str]
    for bd in branch_docs:
        if bd.get("name"):
            possible_branch_values.append(bd["name"])
        if bd.get("branch"):
            possible_branch_values.append(bd["branch"])
            clean_b = bd["branch"].replace(" BRANCH", "").replace("Branch", "").strip()
            if clean_b:
                possible_branch_values.append(clean_b)
        if bd.get("sol_id"):
            possible_branch_values.append(bd["sol_id"])

    conditions = [
        "designation LIKE %(bm_desig)s",
        "designation NOT LIKE %(excl_assist)s",
        "designation NOT LIKE %(excl_jll)s",
    ]
    params = {
        "bm_desig": "%Branch Manager%",
        "excl_assist": "%Assistant%",
        "excl_jll": "%JLL%",
        "branches": possible_branch_values,
    }
    conditions.append("(sahayog_branch IN %(branches)s OR sol_id IN %(branches)s OR branch IN %(branches)s)")

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT
            name,
            employee_name,
            employee_number,
            designation,
            cell_number,
            date_of_joining,
            reports_to,
            image,
            user_id,
            sahayog_branch,
            status
        FROM `tabEmployee`
        WHERE {where_clause}
        ORDER BY (status = 'Active') DESC, date_of_joining ASC
    """

    bm_employees = frappe.db.sql(query, params, as_dict=True)

    result = []
    for emp in bm_employees:
        reporting_person = {
            "name": "",
            "employee_name": "--",
            "designation": "--",
            "cell_number": "--",
        }

        reports_to_id = emp.get("reports_to")
        if reports_to_id:
            rep_doc = frappe.db.get_value(
                "Employee",
                reports_to_id,
                ["name", "employee_name", "employee_number", "designation", "cell_number"],
                as_dict=True,
            )
            if rep_doc:
                reporting_person = {
                    "name": rep_doc.get("name") or "",
                    "employee_name": rep_doc.get("employee_name") or "--",
                    "employee_number": rep_doc.get("employee_number") or rep_doc.get("name") or "",
                    "designation": rep_doc.get("designation") or "--",
                    "cell_number": rep_doc.get("cell_number") or "--",
                }

        result.append({
            "name": emp.get("name"),
            "employee_name": emp.get("employee_name") or "--",
            "employee_number": emp.get("employee_number") or "",
            "designation": emp.get("designation") or "Branch Manager",
            "cell_number": emp.get("cell_number") or "--",
            "date_of_joining": str(emp.get("date_of_joining")) if emp.get("date_of_joining") else "",
            "image": emp.get("image") or "",
            "reports_to": emp.get("reports_to") or "",
            "reporting_person": reporting_person,
        })

    return {
        "status": "success",
        "count": len(result),
        "data": result,
    }

@frappe.whitelist()
def get_book_position_details(sol_id: str):
    """
    Fetch Book Position data from 'Book Position and Account Details' doctype.
    Sums up closing_balance for specific group_name and group_subname.
    """
    if not sol_id:
        return {}

    # Get the latest date for this sol_id
    latest_date = frappe.db.get_value(
        "Book Position and Account Details",
        {"sol_id": sol_id},
        "date",
        order_by="date desc"
    )

    result = {
        "sa_book": 0.0, "ca_book": 0.0, "fd_book": 0.0,
        "rd_book": 0.0, "dds_book": 0.0, "smbg_book": 0.0, "dam_book": 0.0,
        "total_book": 0.0,
        
        "sa_accounts_opened": 0, "sa_accounts_total": 0,
        "ca_accounts_opened": 0, "ca_accounts_total": 0,
        "fd_accounts_opened": 0, "fd_accounts_total": 0,
        "rd_accounts_opened": 0, "rd_accounts_total": 0,
        "dds_accounts_opened": 0, "dds_accounts_total": 0,
        "smbg_accounts_opened": 0, "smbg_accounts_total": 0,
        "dam_accounts_opened": 0, "dam_accounts_total": 0,
        "total_accounts_opened": 0, "total_accounts_total": 0
    }

    if not latest_date:
        return result

    data = frappe.db.get_list(
        "Book Position and Account Details",
        filters={"sol_id": sol_id, "date": latest_date},
        fields=["group_name", "group_subname", "closing_balance", "account_opened", "closing_no_of_accounts"],
    )

    total_balance = 0.0
    for row in data:
        balance = flt(row.closing_balance)
        opened = frappe.utils.cint(row.account_opened)
        total = frappe.utils.cint(row.closing_no_of_accounts)
        
        g_name = (row.group_name or "").upper().strip()
        g_subname = (row.group_subname or "").upper().strip()

        if g_name == "CASA" and g_subname == "SA":
            result["sa_book"] += balance
            result["sa_accounts_opened"] += opened
            result["sa_accounts_total"] += total
        elif g_name == "CASA" and g_subname == "CA":
            result["ca_book"] += balance
            result["ca_accounts_opened"] += opened
            result["ca_accounts_total"] += total
        elif g_name == "FD":
            result["fd_book"] += balance
            result["fd_accounts_opened"] += opened
            result["fd_accounts_total"] += total
        elif g_name == "RD":
            result["rd_book"] += balance
            result["rd_accounts_opened"] += opened
            result["rd_accounts_total"] += total
        elif g_name == "DD":
            result["dds_book"] += balance
            result["dds_accounts_opened"] += opened
            result["dds_accounts_total"] += total
        elif g_name == "SMBG":
            result["smbg_book"] += balance
            result["smbg_accounts_opened"] += opened
            result["smbg_accounts_total"] += total
        elif g_name == "DAM":
            result["dam_book"] += balance
            result["dam_accounts_opened"] += opened
            result["dam_accounts_total"] += total
            
        total_balance += balance

    # Total Book should probably be sum of all categories, or sum of everything.
    # The requirement is just showing these compositions of the total book.
    # Let's sum all mapped ones for composition 100%.
    result["total_book"] = (
        result["sa_book"] + result["ca_book"] + result["fd_book"] +
        result["rd_book"] + result["dds_book"] + result["smbg_book"] + result["dam_book"]
    )
    
    result["total_accounts_opened"] = (
        result["sa_accounts_opened"] + result["ca_accounts_opened"] + result["fd_accounts_opened"] +
        result["rd_accounts_opened"] + result["dds_accounts_opened"] + result["smbg_accounts_opened"] + result["dam_accounts_opened"]
    )
    
    result["total_accounts_total"] = (
        result["sa_accounts_total"] + result["ca_accounts_total"] + result["fd_accounts_total"] +
        result["rd_accounts_total"] + result["dds_accounts_total"] + result["smbg_accounts_total"] + result["dam_accounts_total"]
    )
    
    # Fetch DDS Demand, Collection, and Demand vs Collection from 'DD Tracker Report' for this sol_id
    dd_latest_date = frappe.db.get_value(
        "DD Tracker Report",
        {"sol_id": sol_id},
        "date",
        order_by="date desc"
    )
    if not dd_latest_date:
        dd_latest_date = frappe.db.get_value(
            "DD Tracker Report",
            {},
            "date",
            order_by="date desc"
        )

    dds_demand = 0.0
    dds_collection = 0.0
    if dd_latest_date:
        dd_records = frappe.db.get_all(
            "DD Tracker Report",
            filters={"sol_id": sol_id, "date": dd_latest_date},
            fields=["monthly_demand", "monthly_collection"]
        )
        for r in dd_records:
            dds_demand += flt(r.monthly_demand)
            dds_collection += flt(r.monthly_collection)

    result["dds_demand"] = dds_demand
    result["dds_collection"] = dds_collection
    result["dds_demand_vs_collection"] = (dds_collection / dds_demand * 100.0) if dds_demand > 0 else 0.0

    return result



# ============================================================================
# PERFORMANCE DATA API (Note: Implementation moved to the bottom of the file)
# ============================================================================




# ============================================================================
# Employee DATA API
# ============================================================================

import frappe
from frappe.query_builder import DocType, functions as fn, Case
from frappe.utils import get_first_day, get_last_day, today

# @frappe.whitelist()
# def get_employee_details_by_sol(sol_id: str):
#     """
#     Fetch comprehensive employee details including monthly lead generation 
#     and conversion performance metrics filtered by SOL ID.
    
#     Args:
#         sol_id (str): The Branch/Service Outlet ID to filter employees.
        
#     Returns:
#         dict: Success status, record count, and data containing employee info 
#               plus lead analytics (Total, Converted, and Ratio).
#     """
#     if not sol_id:
#         return {"status": "error", "message": "SOL ID is required"}

#     try:
#         # 1. Initialize Doctypes for Query Builder
#         Employee = DocType("Employee")
#         Lead = DocType("Lead")

#         # 2. Define the date range for the current month
#         # This ensures we only count leads created between the 1st and today
#         start_date = get_first_day(today())
#         end_date = get_last_day(today())

#         # 3. Construct the Query
#         # We use a LEFT JOIN to ensure employees are listed even if they have 0 leads.
#         # The join condition matches Employee.user_id with Lead.lead_owner.
#         query = (
#             frappe.qb.from_(Employee)
#             .left_join(Lead).on(
#                 (Employee.user_id == Lead.lead_owner) & 
#                 (Lead.creation.between(start_date, end_date))
#             )
#             .select(
#                 # Employee Identity and Contact Fields
#                 Employee.sol_id,
#                 Employee.employee_name,
#                 Employee.employee_number,
#                 Employee.user_id,
#                 Employee.designation,
#                 Employee.cell_number,
#                 Employee.date_of_joining,
#                 Employee.pip_status,
                
#                 # Aggregate Lead Analytics
#                 fn.Count(Lead.name).as_("total_leads"),
#                 fn.Sum(
#                     Case().when(Lead.status == "Converted", 1).else_(0)
#                 ).as_("total_converted")
#             )
#             .where(Employee.sol_id == sol_id)
#             .groupby(Employee.name)
#             .orderby(Employee.employee_name)
#         )

#         # 4. Execute the query and fetch results as a list of dictionaries
#         employee_records = query.run(as_dict=True)

#         # 5. Post-process data to calculate Conversion Ratios
#         for record in employee_records:
#             total = record.get("total_leads") or 0
#             # SQL SUM on Case returns float (e.g. 1.0), converting to int for clean JSON
#             converted = int(record.get("total_converted") or 0)
            
#             record["total_converted"] = converted
            
#             # Calculate conversion ratio percentage
#             if total > 0:
#                 conversion_ratio = (converted / total) * 100
#                 record["conversion_ratio"] = f"{conversion_ratio:.2f}%"
#             else:
#                 record["conversion_ratio"] = "0.00%"

#         return {
#             "status": "success",
#             "count": len(employee_records),
#             "data": employee_records
#         }

#     except Exception as e:
#         # Log the full error traceback in Frappe Error Log for debugging
#         frappe.log_error(frappe.get_traceback(), "Employee Lead Details API Error")
#         return {
#             "status": "error", 
#             "message": "An internal error occurred while fetching details."
#         }


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

        sol_id_str = str(sol_id).strip()

        # Find Sahayog Branch doc names and details if any
        branch_docs = frappe.db.get_all(
            "Sahayog Branch",
            filters=[["sol_id", "=", sol_id_str]],
            fields=["name", "branch", "sol_id"],
        )

        possible_branch_values = [sol_id_str]
        for bd in branch_docs:
            if bd.get("name"):
                possible_branch_values.append(bd["name"])
            if bd.get("branch"):
                possible_branch_values.append(bd["branch"])
                clean_b = bd["branch"].replace(" BRANCH", "").replace("Branch", "").strip()
                if clean_b:
                    possible_branch_values.append(clean_b)
            if bd.get("sol_id"):
                possible_branch_values.append(bd["sol_id"])

        possible_branch_values = list(set(possible_branch_values))

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
                
                # --- NEW FIELDS ADDED HERE ---
                Employee.monthly_business,
                Employee.yearly_business,
                # -----------------------------
                
                # Aggregate Lead Analytics
                fn.Count(Lead.name).as_("total_leads"),
                fn.Sum(
                    Case().when(Lead.status == "Converted", 1).else_(0)
                ).as_("total_converted")
            )
            .where(
                (Employee.sol_id.isin(possible_branch_values)) |
                (Employee.sahayog_branch.isin(possible_branch_values))
            )
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
            
            # --- Ensure new fields have a default 0 if null ---
            record["monthly_business"] = record.get("monthly_business") or 0
            record["yearly_business"] = record.get("yearly_business") or 0
            # --------------------------------------------------
            
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
def get_performance_data(sol_id, date=None, fy=None):
    try:
        start_date = None
        end_date = None
        if fy:
            try:
                parts = fy.split("-")
                if len(parts) == 2:
                    start_date = f"{parts[0]}-04-01"
                    end_date = f"{parts[1]}-03-31"
            except Exception:
                pass

        # 1. Fetch Latest Record for the SOL
        if start_date and end_date:
            latest_record = frappe.db.sql("""
                SELECT date, achievement, yearly_achievement 
                FROM `tabBranch Category Report`
                WHERE sol_id = %s AND date >= %s AND date <= %s
                ORDER BY date DESC 
                LIMIT 1
            """, (sol_id, start_date, end_date), as_dict=1)
        else:
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
        fiscal_year = fy or get_fiscal_year(report_date)
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
                "ytd": format_ui_output(res.yearly_achievement, targets.get("ytd", 0)),
                "yearly": format_ui_output(res.yearly_achievement, targets.get("yearly", 0))
            }
        }

    except Exception as e:
        frappe.log_error(f"Branch Performance Error: {sol_id}", frappe.get_traceback())
        return {
            "status": "error", 
            "message": str(e)
        }


@frappe.whitelist()
def get_attrition_rate(sol_id: str, period: str = "3"):
    """
    Fetch Attrition Rate for a given branch (sol_id) for periods: 3, 6, 12 months.
    Returns calculated rates and headcount breakdown for 3 Months, 6 Months, and 12 Months.
    """
    if not sol_id:
        return {
            "status": "error",
            "message": "SOL ID is required",
            "rates": {"3": 0.0, "6": 0.0, "12": 0.0},
            "counts": {"3": {"left": 0, "headcount": 0}, "6": {"left": 0, "headcount": 0}, "12": {"left": 0, "headcount": 0}}
        }

    try:
        from frappe.utils import add_months, today
        current_today = today()

        # Get current active employee count for this sol_id
        active_count = frappe.db.count("Employee", filters={"sol_id": sol_id, "status": "Active"})
        
        # If active_count is 0, check staff_count in Branch Profile Data
        if active_count == 0:
            staff_count_str = frappe.db.get_value("Branch Profile Data", {"sol_id": sol_id}, "staff_count")
            active_count = frappe.utils.cint(staff_count_str) or 0

        rates = {}
        counts = {}

        for p_months in [3, 6, 12]:
            start_date = add_months(current_today, -p_months)
            
            # Count employees relieved/left in period
            left_count = frappe.db.sql("""
                SELECT COUNT(*) FROM `tabEmployee`
                WHERE sol_id = %s
                  AND (
                      (relieving_date IS NOT NULL AND relieving_date >= %s)
                      OR (resignation_letter_date IS NOT NULL AND resignation_letter_date >= %s)
                      OR (status != 'Active' AND status IS NOT NULL AND modified >= %s)
                  )
            """, (sol_id, start_date, start_date, start_date))[0][0] or 0

            headcount = active_count + left_count
            if headcount > 0:
                rate = (left_count / headcount) * 100
            else:
                rate = 0.0

            rates[str(p_months)] = round(rate, 1)
            counts[str(p_months)] = {
                "left": left_count,
                "headcount": headcount,
                "active": active_count
            }

        return {
            "status": "success",
            "sol_id": sol_id,
            "selected_period": str(period),
            "rates": rates,
            "counts": counts
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Attrition Rate Error")
        return {
            "status": "error",
            "rates": {"3": 0.0, "6": 0.0, "12": 0.0},
            "counts": {"3": {"left": 0, "headcount": 0}, "6": {"left": 0, "headcount": 0}, "12": {"left": 0, "headcount": 0}}
        }