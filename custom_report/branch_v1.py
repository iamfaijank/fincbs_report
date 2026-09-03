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


def get_possible_branch_values(sol_id: str) -> list:
    """
    Get all matching identifiers for a branch (sol_id, name, branch variants)
    with local caching to prevent redundant database hits.
    """
    if not sol_id:
        return []
    sol_id_str = str(sol_id).strip()
    cache_key = f"sahayog_branch_possible_vals_{sol_id_str}"
    cached = frappe.cache().get_value(cache_key)
    if cached is not None:
        return cached

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

    res = list(set(possible_branch_values))
    frappe.cache().set_value(cache_key, res, expires_in_sec=1800)
    return res


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
    possible_branch_values = get_possible_branch_values(sol_id_str)

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
def get_branch_complete_profile(sol_id: str, fy: str = None):
    """
    Consolidated high-performance API to fetch all branch dashboard components
    in a single network round-trip.
    """
    if not sol_id:
        return {"status": "error", "message": "SOL ID is required"}

    try:
        profile_data = get_branch_profile_data(sol_id)
        book_data = get_book_position_details(sol_id)
        bm_data = get_bm_details_from_employee(sol_id)
        perf_data = get_performance_data(sol_id, fy=fy)
        attrition_data = get_attrition_rate(sol_id)
        productivity_data = get_productivity_details(sol_id)
        months_list = get_book_position_months(sol_id)

        return {
            "status": "success",
            "sol_id": sol_id,
            "profile": profile_data,
            "book": book_data,
            "bm": bm_data,
            "performance": perf_data,
            "attrition": attrition_data,
            "productivity": productivity_data,
            "months": months_list
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Branch Complete Profile API Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_productivity_details(sol_id: str):
    """
    Fetch Productivity Details for a branch (sol_id).
    Calculates BDE productivity by fetching T-1 (or latest available) data from
    'Product Wise Report' for product = 'DD' and dividing by active BDE manpower count.
    """
    if not sol_id:
        return {
            "status": "error",
            "message": "SOL ID is required",
            "date": "",
            "month": "—",
            "dd_amount": 0.0,
            "bde_count": 0,
            "bdo_count": 0,
            "ro_count": 0,
            "bde_productivity": 0.0,
            "bdo_productivity": 0.0,
            "ro_productivity": 0.0,
            "total_productivity": 0.0
        }

    try:
        from frappe.utils import add_days, today, getdate, flt, cint

        sol_id_str = str(sol_id).strip()

        # 1. Determine Target Date (T-1 by default)
        target_date = add_days(today(), -1)

        # Check if records exist on or before target_date in Product Wise Report
        latest_date_row = frappe.db.sql("""
            SELECT MAX(date) as d FROM `tabProduct Wise Report`
            WHERE sol_id = %s AND date <= %s
        """, (sol_id_str, target_date), as_dict=True)

        actual_date = latest_date_row[0].get("d") if (latest_date_row and latest_date_row[0].get("d")) else None

        if not actual_date:
            # Fallback: check any latest date available for this SOL ID
            latest_date_row = frappe.db.sql("""
                SELECT MAX(date) as d FROM `tabProduct Wise Report`
                WHERE sol_id = %s
            """, (sol_id_str,), as_dict=True)
            actual_date = latest_date_row[0].get("d") if (latest_date_row and latest_date_row[0].get("d")) else None

        if not actual_date:
            # Fallback: check general latest date in doctype
            latest_date_row = frappe.db.sql("""
                SELECT MAX(date) as d FROM `tabProduct Wise Report`
            """, as_dict=True)
            actual_date = latest_date_row[0].get("d") if (latest_date_row and latest_date_row[0].get("d")) else getdate(target_date)

        # 2. Fetch Product amounts on actual_date for this sol_id
        products_data = frappe.db.sql("""
            SELECT product, COALESCE(SUM(amount), 0) as total_amount
            FROM `tabProduct Wise Report`
            WHERE sol_id = %s AND date = %s
            GROUP BY product
        """, (sol_id_str, actual_date), as_dict=True)

        product_amounts = {row["product"]: flt(row["total_amount"]) for row in products_data if row.get("product")}
        dd_amount = flt(product_amounts.get("DD", 0.0))
        rd_amount = flt(product_amounts.get("RD", 0.0))
        smbg_amount = flt(product_amounts.get("SMBG", 0.0))
        bdo_amount = rd_amount + smbg_amount

        # Fetch CASA amount for RO (excluding scheme_code IN ('1104', '1011'))
        casa_data = frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0) as total_amount
            FROM `tabProduct Wise Report`
            WHERE sol_id = %s 
              AND date = %s 
              AND product = 'CASA'
              AND (scheme_code NOT IN ('1104', '1011') OR scheme_code IS NULL)
        """, (sol_id_str, actual_date), as_dict=True)
        casa_amount = flt(casa_data[0].get("total_amount") or 0.0) if casa_data else 0.0
        ro_amount = casa_amount

        # 3. Fetch Manpower Counts for BDE, BDO, RO
        possible_branch_values = get_possible_branch_values(sol_id_str)

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
        bde_count = int(counts[0].get("bde_count") or 0) if counts else 0
        bdo_count = int(counts[0].get("bdo_count") or 0) if counts else 0
        ro_count = int(counts[0].get("ro_count") or 0) if counts else 0

        # Fallback from Branch Profile Data if Employee count returns 0
        if bde_count == 0 or bdo_count == 0 or ro_count == 0:
            bpd = frappe.db.get_value("Branch Profile Data", {"sol_id": sol_id_str}, ["bde", "bdo", "ro"], as_dict=True)
            if bpd:
                if bde_count == 0 and bpd.get("bde"):
                    bde_count = cint(bpd.get("bde") or 0)
                if bdo_count == 0 and bpd.get("bdo"):
                    bdo_count = cint(bpd.get("bdo") or 0)
                if ro_count == 0 and bpd.get("ro"):
                    ro_count = cint(bpd.get("ro") or 0)

        # 4. Calculate Productivity
        bde_productivity = (dd_amount / bde_count) if bde_count > 0 else 0.0
        bdo_productivity = (bdo_amount / bdo_count) if bdo_count > 0 else 0.0
        ro_productivity = (ro_amount / ro_count) if ro_count > 0 else 0.0
        total_productivity = bde_productivity + bdo_productivity + ro_productivity

        dt_obj = getdate(actual_date) if actual_date else getdate(today())
        as_of_month = dt_obj.strftime("%B").upper() if dt_obj else "—"

        return {
            "status": "success",
            "sol_id": sol_id_str,
            "date": str(actual_date) if actual_date else "",
            "month": as_of_month,
            "dd_amount": dd_amount,
            "rd_amount": rd_amount,
            "smbg_amount": smbg_amount,
            "bdo_amount": bdo_amount,
            "casa_amount": casa_amount,
            "ro_amount": ro_amount,
            "bde_count": bde_count,
            "bdo_count": bdo_count,
            "ro_count": ro_count,
            "bde_productivity": bde_productivity,
            "bdo_productivity": bdo_productivity,
            "ro_productivity": ro_productivity,
            "total_productivity": total_productivity
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Productivity Details Error")
        return {
            "status": "error",
            "message": str(e),
            "date": "",
            "month": "—",
            "dd_amount": 0.0,
            "bde_count": 0,
            "bdo_count": 0,
            "ro_count": 0,
            "bde_productivity": 0.0,
            "bdo_productivity": 0.0,
            "ro_productivity": 0.0,
            "total_productivity": 0.0
        }


@frappe.whitelist()
def get_bm_details_from_employee(sol_id: str):
    """
    Fetch Branch Manager (BM) details for a given SOL ID from Employee DocType.
    Filters employees by sahayog_branch matching sol_id or branch name, and designation LIKE '%Branch Manager%'.
    Also fetches Reporting Person details from Employee.reports_to via single SQL JOIN.
    """
    if not sol_id:
        return {"status": "error", "message": "SOL ID is required", "data": []}

    sol_id_str = str(sol_id).strip()
    possible_branch_values = get_possible_branch_values(sol_id_str)

    conditions = [
        "emp.status = 'Active'",
        "emp.designation LIKE %(bm_desig)s",
        "emp.designation NOT LIKE %(excl_assist)s",
        "emp.designation NOT LIKE %(excl_jll)s",
    ]

    params = {
        "bm_desig": "%Branch Manager%",
        "excl_assist": "%Assistant%",
        "excl_jll": "%JLL%",
        "branches": possible_branch_values,
    }
    conditions.append("(emp.sahayog_branch IN %(branches)s OR emp.sol_id IN %(branches)s OR emp.branch IN %(branches)s)")

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT
            emp.name,
            emp.employee_name,
            emp.employee_number,
            emp.designation,
            emp.cell_number,
            emp.date_of_joining,
            emp.reports_to,
            emp.image,
            emp.user_id,
            emp.sahayog_branch,
            emp.status,
            rep.name AS rep_name,
            rep.employee_name AS rep_employee_name,
            rep.employee_number AS rep_employee_number,
            rep.designation AS rep_designation,
            rep.cell_number AS rep_cell_number
        FROM `tabEmployee` emp
        LEFT JOIN `tabEmployee` rep ON emp.reports_to = rep.name
        WHERE {where_clause}
        ORDER BY (emp.status = 'Active') DESC, emp.date_of_joining ASC
    """

    bm_employees = frappe.db.sql(query, params, as_dict=True)

    result = []
    for emp in bm_employees:
        rep_name = emp.get("rep_name")
        if rep_name:
            reporting_person = {
                "name": rep_name,
                "employee_name": emp.get("rep_employee_name") or "--",
                "employee_number": emp.get("rep_employee_number") or rep_name,
                "designation": emp.get("rep_designation") or "--",
                "cell_number": emp.get("rep_cell_number") or "--",
            }
        else:
            reporting_person = {
                "name": "",
                "employee_name": "--",
                "designation": "--",
                "cell_number": "--",
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
def get_book_position_months(sol_id: str):
    """
    List available distinct dates for the branch's Book Position and Account Details data.
    """
    if not sol_id:
        return []
    rows = frappe.db.sql("""
        SELECT DISTINCT `date`
        FROM `tabBook Position and Account Details`
        WHERE sol_id = %s
        ORDER BY `date` DESC
    """, (sol_id,))
    return [str(r[0]) for r in rows]


def get_smbg_demand_collection_from_dr(sol_id: str, date_str: str = None):
    if not date_str:
        from datetime import datetime
        date_str = datetime.today().strftime('%Y-%m-%d')
    try:
        from datetime import datetime
        dt = datetime.strptime(str(date_str), '%Y-%m-%d')
        start_date = dt.replace(day=1).strftime('%Y-%m-%d')
        end_date = date_str
    except Exception:
        start_date = "2026-08-01"
        end_date = "2026-08-18"

    from custom_report.db_connection import get_dr_connection
    from frappe.utils import flt

    query = """
WITH account_data AS (
    SELECT
        d.rm_id,
        g.cif_id,
        g.acct_opn_date,
        g.acct_cls_date,
        a2.relationshipopeningdate AS cif_id_opening_date,
        g2.emp_name AS rm_name,
        d2.operacc,
        g.foracid,
        g.sol_id,  
        sol.sol_desc,  
        g.schm_code  
    FROM
        custom.dsamap AS d
    LEFT JOIN
        tbaadm.gam AS g ON g.foracid = d.account_number
            AND g.schm_code BETWEEN '2005' AND '2006'
            AND g.sol_id = %s
    LEFT JOIN
        crmuser.accounts AS a2 ON g.cif_id = a2.orgkey
    LEFT JOIN
        custom.dsaauth AS d2 ON UPPER(d.rm_id) = UPPER(d2.user_id)
    LEFT JOIN
        tbaadm.get AS g2 ON UPPER(d2.user_id) = UPPER(g2.emp_id)
    LEFT JOIN
        tbaadm.sol AS sol ON g.sol_id = sol.sol_id
    WHERE
        g.foracid IS NOT NULL
),
flow_data AS (
    SELECT
        g.foracid,
        SUM(tdt.flow_amt) AS total_flow_amount
    FROM
        tbaadm.gam AS g
    JOIN
        tbaadm.tdt AS tdt ON tdt.acid = g.acid
            AND tdt.flow_code = 'NI'
            AND tdt.flow_date BETWEEN %s AND %s
    WHERE
        g.schm_code BETWEEN '2005' AND '2006'
        AND g.sol_id = %s
    GROUP BY
        g.foracid
),
tran_data AS (
    SELECT
        g.foracid,
        SUM(dtt.tran_amt) AS total_tran_amt
    FROM
        tbaadm.gam AS g
    JOIN
        tbaadm.dtt AS dtt ON dtt.acid = g.acid
            AND dtt.flow_code = 'NI'
            AND dtt.value_date BETWEEN %s AND %s
    WHERE
        g.schm_code BETWEEN '2005' AND '2006'
        AND g.sol_id = %s
    GROUP BY
        g.foracid
),
reference_data AS (
    SELECT
        ed.referencenumber AS pan_number,
        da.user_id AS rm_id
    FROM
        crmuser.entitydocument AS ed
    JOIN
        tbaadm.gam AS g ON ed.orgkey = g.cif_id
            AND g.sol_id = %s
    JOIN
        custom.dsaauth AS da ON g.foracid = da.operacc
    WHERE
        ed.doccode = 'PAN'
)
SELECT
    COALESCE(SUM(
        CASE
            WHEN ad.acct_cls_date IS NOT NULL
                 AND ad.acct_cls_date < %s
            THEN 0
            ELSE COALESCE(fd.total_flow_amount, 0)
        END
    ), 0) AS total_demand,
    COALESCE(SUM(COALESCE(td.total_tran_amt, 0)), 0) AS total_collection
FROM
    account_data AS ad
LEFT JOIN
    flow_data AS fd ON ad.foracid = fd.foracid
LEFT JOIN
    tran_data AS td ON ad.foracid = td.foracid
LEFT JOIN
    reference_data AS rd ON ad.rm_id = rd.rm_id
LEFT JOIN
    tbaadm.gam AS g ON ad.foracid = g.foracid
LEFT JOIN
    tbaadm.gsp AS gsp ON g.schm_code = gsp.schm_code;
    """

    total_demand = 0.0
    total_collection = 0.0

    try:
        conn = get_dr_connection()
        with conn.cursor() as cur:
            cur.execute(query, (
                sol_id,
                start_date,
                end_date,
                sol_id,
                start_date,
                end_date,
                sol_id,
                sol_id,
                start_date
            ))
            row = cur.fetchone()
            if row:
                total_demand = flt(row[0] or 0)
                total_collection = flt(row[1] or 0)
        conn.close()
    except Exception as e:
        frappe.log_error(f"Failed to fetch SMBG Demand/Collection from DR for {sol_id}: {str(e)}", "SMBG Demand Collection DR Fetch")

    return total_demand, total_collection


def get_rd_demand_collection_from_dr(sol_id: str, date_str: str = None):
    if not date_str:
        from datetime import datetime
        date_str = datetime.today().strftime('%Y-%m-%d')
    try:
        from datetime import datetime
        dt = datetime.strptime(str(date_str), '%Y-%m-%d')
        start_date = dt.replace(day=1).strftime('%Y-%m-%d')
        end_date = date_str
    except Exception:
        start_date = "2026-08-01"
        end_date = "2026-08-19"

    from custom_report.db_connection import get_dr_connection
    from frappe.utils import flt

    query = """
WITH account_data AS (
    SELECT
        d.rm_id,
        g2.emp_name AS rm_name,
        d2.operacc,
        g.cif_id,
        g.acct_opn_date,
        g.acct_cls_date,
        a2.relationshipopeningdate AS CIF_ID_Opening_Date,
        g.foracid,  
        g.sol_id,  
        sol.sol_desc,  
        g.schm_code AS scheme_code,  
        gsp.schm_desc  
    FROM custom.dsamap AS d
    INNER JOIN tbaadm.gam AS g
        ON g.foracid = d.account_number
        AND g.schm_code BETWEEN '2010' AND '2016'
        AND g.sol_id = %s
    LEFT JOIN crmuser.accounts AS a2
        ON g.cif_id = a2.orgkey       
    LEFT JOIN tbaadm.sol AS sol
        ON g.sol_id = sol.sol_id  
    LEFT JOIN tbaadm.gsp AS gsp
        ON g.schm_code = gsp.schm_code  
    LEFT JOIN custom.dsaauth AS d2
        ON d.rm_id = d2.user_id
    LEFT JOIN tbaadm.get AS g2
        ON d2.user_id = g2.emp_id
),
flow_data AS (
    SELECT
        d.rm_id,
        g.foracid,  
        g.schm_code,  
        SUM(tdt.flow_amt) AS total_flow_amount
    FROM custom.dsamap AS d
    INNER JOIN tbaadm.gam AS g
        ON g.foracid = d.account_number
        AND g.schm_code BETWEEN '2010' AND '2016'
        AND g.sol_id = %s
    INNER JOIN tbaadm.tdt AS tdt
        ON tdt.acid = g.acid
        AND tdt.flow_code = 'NI'
    WHERE tdt.flow_date BETWEEN %s AND %s
    GROUP BY
        d.rm_id,
        g.foracid,
        g.schm_code
    HAVING SUM(tdt.flow_amt) > 0
),
tran_data AS (
    SELECT
        d.rm_id,
        g.foracid,  
        g.schm_code,  
        SUM(dtt.tran_amt) AS total_tran_amt
    FROM custom.dsamap AS d
    INNER JOIN tbaadm.gam AS g
        ON g.foracid = d.account_number
        AND g.schm_code BETWEEN '2010' AND '2016'
        AND g.sol_id = %s
    INNER JOIN tbaadm.dtt AS dtt
        ON dtt.acid = g.acid
        AND dtt.flow_code = 'NI'
    WHERE dtt.value_date BETWEEN %s AND %s
    GROUP BY
        d.rm_id,
        g.foracid,
        g.schm_code
    HAVING SUM(dtt.tran_amt) > 0
),
reference_data AS (
    SELECT
        ed.referencenumber,
        da.user_id AS rm_id
    FROM crmuser.entitydocument AS ed
    INNER JOIN tbaadm.gam AS g
        ON ed.orgkey = g.cif_id
        AND g.sol_id = %s
    INNER JOIN custom.dsaauth AS da
        ON g.foracid = da.operacc
    WHERE ed.doccode = 'PAN'
)
SELECT
    COALESCE(SUM(
        CASE
            WHEN ad.acct_cls_date IS NOT NULL
                 AND ad.acct_cls_date < %s
            THEN 0
            ELSE COALESCE(fd.total_flow_amount, 0)
        END
    ), 0) AS total_demand,
    COALESCE(SUM(COALESCE(td.total_tran_amt, 0)), 0) AS total_collection
FROM account_data AS ad
LEFT JOIN flow_data AS fd
    ON ad.rm_id = fd.rm_id
    AND ad.foracid = fd.foracid
    AND ad.scheme_code = fd.schm_code
LEFT JOIN tran_data AS td
    ON ad.rm_id = td.rm_id
    AND ad.foracid = td.foracid
    AND ad.scheme_code = td.schm_code
LEFT JOIN reference_data AS rd
    ON ad.rm_id = rd.rm_id
    AND (fd.total_flow_amount > 0 OR td.total_tran_amt > 0);
    """
    
    total_demand = 0.0
    total_collection = 0.0
    
    try:
        conn = get_dr_connection()
        with conn.cursor() as cur:
            cur.execute(query, (
                sol_id,
                sol_id,
                start_date,
                end_date,
                sol_id,
                start_date,
                end_date,
                sol_id,
                start_date
            ))
            row = cur.fetchone()
            if row:
                total_demand = flt(row[0] or 0)
                total_collection = flt(row[1] or 0)
        conn.close()
    except Exception as e:
        frappe.log_error(f"Failed to fetch RD Demand/Collection from DR for {sol_id}: {str(e)}", "RD Demand Collection DR Fetch")
        
    return total_demand, total_collection


@frappe.whitelist()
def get_book_position_details(sol_id: str = None, selected_date: str = None):
    """
    Fetch Book Position data from 'Book Position and Account Details' doctype.
    Sums up closing_balance for specific group_name and group_subname.
    """
    if not sol_id:
        return {}

    # Get the latest date for this sol_id
    if selected_date:
        latest_date = selected_date
    else:
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
        "total_accounts_opened": 0, "total_accounts_total": 0,
        
        "rd_demand": 0.0, "rd_collection": 0.0, "rd_smbg_collection": 0.0,
        "smbg_demand": 0.0, "smbg_collection": 0.0, "smbg_demand_vs_collection": 0.0,
        "rd_smbg_pending": 0.0
    }

    if not latest_date:
        rd_demand_val, rd_collection_val = get_rd_demand_collection_from_dr(sol_id, None)
        result["rd_demand"] = rd_demand_val
        result["rd_collection"] = rd_collection_val

        smbg_demand_val, smbg_collection_val = get_smbg_demand_collection_from_dr(sol_id, None)
        result["smbg_demand"] = smbg_demand_val
        result["smbg_collection"] = smbg_collection_val
        result["smbg_demand_vs_collection"] = (smbg_collection_val / smbg_demand_val * 100.0) if smbg_demand_val > 0 else 0.0
        
        result["rd_smbg_collection"] = rd_collection_val + smbg_collection_val

        # Query yesterday's RD & SMBG Pending sum
        from datetime import date, timedelta
        target_date = date.today() - timedelta(days=1)
        target_date_str = target_date.strftime('%Y-%m-%d')
        pending_sum = frappe.db.get_value(
            "RD and SMBG Pending",
            {"sol_id": sol_id, "date": target_date_str},
            "sum(pending_amount)"
        ) or 0.0
        result["rd_smbg_pending"] = float(pending_sum)
        result["latest_month"] = ""
        return result

    data = frappe.db.get_list(
        "Book Position and Account Details",
        filters={"sol_id": sol_id, "date": latest_date},
        fields=["group_name", "group_subname", "closing_balance", "account_opened", "closing_no_of_accounts"],
        ignore_permissions=True,
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
            fields=["monthly_demand", "monthly_collection"],
            ignore_permissions=True,
        )
        for r in dd_records:
            dds_demand += flt(r.monthly_demand)
            dds_collection += flt(r.monthly_collection)

    result["dds_demand"] = dds_demand
    result["dds_collection"] = dds_collection
    result["dds_demand_vs_collection"] = (dds_collection / dds_demand * 100.0) if dds_demand > 0 else 0.0

    # Overwrite RD demand and collection from Finacle/DR DB
    rd_demand_val, rd_collection_val = get_rd_demand_collection_from_dr(sol_id, latest_date)
    result["rd_demand"] = rd_demand_val
    result["rd_collection"] = rd_collection_val

    # Overwrite SMBG demand and collection from Finacle/DR DB
    smbg_demand_val, smbg_collection_val = get_smbg_demand_collection_from_dr(sol_id, latest_date)
    result["smbg_demand"] = smbg_demand_val
    result["smbg_collection"] = smbg_collection_val
    result["smbg_demand_vs_collection"] = (smbg_collection_val / smbg_demand_val * 100.0) if smbg_demand_val > 0 else 0.0

    result["rd_smbg_collection"] = rd_collection_val + smbg_collection_val

    # Query yesterday's RD & SMBG Pending sum
    from datetime import date, timedelta
    target_date = date.today() - timedelta(days=1)
    target_date_str = target_date.strftime('%Y-%m-%d')
    pending_sum = frappe.db.get_value(
        "RD and SMBG Pending",
        {"sol_id": sol_id, "date": target_date_str},
        "sum(pending_amount)"
    ) or 0.0
    result["rd_smbg_pending"] = float(pending_sum)

    if latest_date:
        from frappe.utils import getdate
        dt = getdate(latest_date)
        result["latest_month"] = dt.strftime("%B").upper()
    else:
        result["latest_month"] = ""

    return result



# ============================================================================
# PERFORMANCE DATA API (Note: Implementation moved to the bottom of the file)
# ============================================================================




# ============================================================================
# Employee DATA API
# ============================================================================

import frappe
from frappe.query_builder import DocType, functions as fn, Case
from frappe.utils import get_first_day, get_last_day, getdate

@frappe.whitelist()
def get_employee_details_by_sol(sol_id: str, month: str = None, selected_date: str = None, date: str = None):
    """
    Fetch comprehensive employee details including lead generation 
    and conversion performance metrics filtered by SOL ID.
    If selected_date/date (YYYY-MM-DD) is provided, filters leads by that day;
    else if month (YYYY-MM) is provided, filters leads by that month; otherwise all-time.
    
    Args:
        sol_id (str): The Branch/Service Outlet ID to filter employees.
        month (str, optional): YYYY-MM to filter leads by creation month.
        selected_date (str, optional): YYYY-MM-DD to filter leads by specific date.
        date (str, optional): alias for selected_date.
        
    Returns:
        dict: Success status, record count, and data containing employee info 
              plus lead analytics (Total, Converted, and Ratio).
    """
    if not sol_id:
        return {"status": "error", "message": "SOL ID is required"}

    try:
        sol_id_str = str(sol_id).strip()
        possible_branch_values = get_possible_branch_values(sol_id_str)

        # 1. Fetch only branch employees first (superfast indexed query, returns ~5-30 rows in ~2ms)
        employees = frappe.db.sql("""
            SELECT
                sol_id,
                employee_name,
                employee_number,
                user_id,
                designation,
                cell_number,
                date_of_joining,
                pip_status,
                COALESCE(monthly_business, 0) as monthly_business,
                COALESCE(yearly_business, 0) as yearly_business
            FROM `tabEmployee`
            WHERE (sol_id IN %(branches)s OR sahayog_branch IN %(branches)s OR branch IN %(branches)s)
            ORDER BY employee_name ASC
        """, {"branches": possible_branch_values}, as_dict=True)

        if not employees:
            return {"status": "success", "count": 0, "data": []}

        # 2. Get user_ids for targeted leads aggregation
        user_ids = [emp.user_id for emp in employees if emp.get("user_id")]
        leads_map = {}

        if user_ids:
            # Optional month filter for calendar (YYYY-MM)
            month_filter_sql = ""
            sql_params = {"user_ids": user_ids}
            # prioritize specific date over month
            effective_date = selected_date or date
            if effective_date:
                try:
                    dt = getdate(effective_date)
                    month_filter_sql = " AND creation >= %(start_date)s AND creation <= %(end_date)s"
                    sql_params["start_date"] = f"{dt} 00:00:00"
                    sql_params["end_date"] = f"{dt} 23:59:59"
                except Exception:
                    pass
            elif month:
                try:
                    # month is YYYY-MM, build first/last day range
                    dt = getdate(f"{month}-01")
                    start_date = get_first_day(dt)
                    end_date = get_last_day(dt)
                    month_filter_sql = " AND creation >= %(start_date)s AND creation <= %(end_date)s"
                    sql_params["start_date"] = f"{start_date} 00:00:00"
                    sql_params["end_date"] = f"{end_date} 23:59:59"
                except Exception:
                    pass  # ignore invalid month, fallback to all-time

            lead_stats = frappe.db.sql(f"""
                SELECT
                    lead_owner,
                    COUNT(*) as total_leads,
                    SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) as total_converted
                FROM `tabLead`
                WHERE lead_owner IN %(user_ids)s{month_filter_sql}
                GROUP BY lead_owner
            """, sql_params, as_dict=True)

            for ls in lead_stats:
                leads_map[ls.lead_owner] = {
                    "total_leads": int(ls.get("total_leads") or 0),
                    "total_converted": int(ls.get("total_converted") or 0)
                }

        # 3. Assemble results in memory (O(N) in ~0.1ms)
        for record in employees:
            u_id = record.get("user_id")
            stats = leads_map.get(u_id, {"total_leads": 0, "total_converted": 0})
            total = stats["total_leads"]
            converted = stats["total_converted"]

            record["total_leads"] = total
            record["total_converted"] = converted

            if total > 0:
                record["conversion_ratio"] = f"{(converted / total) * 100:.2f}%"
            else:
                record["conversion_ratio"] = "0.00%"

        return {
            "status": "success",
            "count": len(employees),
            "data": employees
        }

    except Exception as e:
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
        sol_id_str = str(sol_id).strip()

        # Get current active employee count for this sol_id
        active_count = frappe.db.count("Employee", filters={"sol_id": sol_id_str, "status": "Active"})
        if active_count == 0:
            staff_count_str = frappe.db.get_value("Branch Profile Data", {"sol_id": sol_id_str}, "staff_count")
            active_count = frappe.utils.cint(staff_count_str) or 0

        d3 = add_months(current_today, -3)
        d6 = add_months(current_today, -6)
        d12 = add_months(current_today, -12)

        # Single combined query for 3, 6, and 12 months
        left_row = frappe.db.sql("""
            SELECT
                SUM(CASE WHEN (
                    (relieving_date IS NOT NULL AND relieving_date >= %(d3)s)
                    OR (resignation_letter_date IS NOT NULL AND resignation_letter_date >= %(d3)s)
                    OR (status != 'Active' AND status IS NOT NULL AND modified >= %(d3)s)
                ) THEN 1 ELSE 0 END) AS left_3,
                SUM(CASE WHEN (
                    (relieving_date IS NOT NULL AND relieving_date >= %(d6)s)
                    OR (resignation_letter_date IS NOT NULL AND resignation_letter_date >= %(d6)s)
                    OR (status != 'Active' AND status IS NOT NULL AND modified >= %(d6)s)
                ) THEN 1 ELSE 0 END) AS left_6,
                SUM(CASE WHEN (
                    (relieving_date IS NOT NULL AND relieving_date >= %(d12)s)
                    OR (resignation_letter_date IS NOT NULL AND resignation_letter_date >= %(d12)s)
                    OR (status != 'Active' AND status IS NOT NULL AND modified >= %(d12)s)
                ) THEN 1 ELSE 0 END) AS left_12
            FROM `tabEmployee`
            WHERE sol_id = %(sol_id)s
        """, {"sol_id": sol_id_str, "d3": d3, "d6": d6, "d12": d12}, as_dict=True)

        left_map = {
            "3": int(left_row[0].get("left_3") or 0) if left_row else 0,
            "6": int(left_row[0].get("left_6") or 0) if left_row else 0,
            "12": int(left_row[0].get("left_12") or 0) if left_row else 0,
        }

        rates = {}
        counts = {}
        for p_str in ["3", "6", "12"]:
            l_cnt = left_map[p_str]
            h_cnt = active_count + l_cnt
            rate = round((l_cnt / h_cnt * 100), 1) if h_cnt > 0 else 0.0
            rates[p_str] = rate
            counts[p_str] = {
                "left": l_cnt,
                "headcount": h_cnt,
                "active": active_count
            }

        return {
            "status": "success",
            "sol_id": sol_id_str,
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