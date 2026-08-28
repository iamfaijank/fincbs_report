import frappe
from frappe.utils import add_days, today, getdate, flt
from datetime import date


MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


@frappe.whitelist()
def get_sol_product_wise_collection(sol_id, zone, financial_year="2026-2027", report_date=None, mode="month", month=None):
    """
    Fetch product wise collection (ACH) from 'Product Wise Report' doctype.
    mode='month' -> compare against the chosen month's Monthly target (default current month).
    mode='ytd'   -> compare against the YTD target and sum month-end ACH
                    snapshots across the financial year (Apr -> current month).
    """
    if not report_date:
        target_date = add_days(today(), -1)
    else:
        target_date = getdate(report_date)

    mode = (mode or "month").lower()
    if mode not in ("month", "ytd"):
        mode = "month"

    today_dt = date.today()
    current_month = today_dt.strftime('%b').upper()

    # ---- Resolve which FY + month we are looking at ----
    if mode == "ytd":
        sel_month = None
    else:
        sel_month = (month or current_month).upper()
        if sel_month not in MONTH_MAP:
            sel_month = current_month
    fy = _fy_for_month(sel_month or current_month, today_dt)

    # ---- Collections ----
    if mode == "ytd":
        collections = _get_ytd_collections(sol_id, target_date)
        period_label = _get_ytd_period_label(target_date)
        actual_date = _get_latest_pwr_date(sol_id, target_date) or target_date
    else:
        mnum = MONTH_MAP[sel_month]
        cal_year = int(fy.split("-")[0]) + (0 if mnum >= 4 else 1)
        last_date = _get_last_available_date_for_month(mnum, cal_year)
        if last_date:
            data = frappe.db.sql("""
                SELECT product, SUM(amount) as total_amount
                FROM `tabProduct Wise Report`
                WHERE sol_id = %s AND date = %s
                GROUP BY product
            """, (sol_id, last_date), as_dict=True)
            actual_date = last_date
        else:
            data = frappe.db.sql("""
                SELECT product, SUM(amount) as total_amount
                FROM `tabProduct Wise Report`
                WHERE sol_id = %s AND date = %s
                GROUP BY product
            """, (sol_id, target_date), as_dict=True)
            actual_date = target_date
            if not data:
                latest = _get_latest_pwr_date(sol_id, target_date)
                if latest:
                    actual_date = latest
                    data = frappe.db.sql("""
                        SELECT product, SUM(amount) as total_amount
                        FROM `tabProduct Wise Report`
                        WHERE sol_id = %s AND date = %s
                        GROUP BY product
                    """, (sol_id, actual_date), as_dict=True)
                else:
                    data = []
        collections = _aggregate_collections(data)
        period_label = None

    collections["TOTAL TARGET"] = sum(collections.values())

    # ---- Zone based target split percentages ----
    targets = {p: 0.0 for p in ("CASA", "DAM", "DD", "FD", "RD", "SMBG")}
    if zone:
        target_data = frappe.db.sql("""
            SELECT a.casa, a.dam, a.dd, a.fd, a.rd, a.smbg
            FROM `tabGL Wise Target Allocation` a
            JOIN `tabGL Wise Target` p ON a.parent = p.name
            WHERE a.zone = %s AND p.financial_year = %s
            ORDER BY a.modified DESC LIMIT 1
        """, (zone, financial_year), as_dict=True)
        if target_data:
            t = target_data[0]
            for p in targets:
                targets[p] = flt(t.get(p.lower(), 0.0))

    # ---- Overall target (Monthly vs YTD) ----
    if mode == "ytd":
        overall = frappe.db.sql("""
            SELECT target FROM `tabTarget Vs Achivement`
            WHERE sol_id = %s AND type = 'YTD' AND financial_year = %s
        """, (sol_id, fy), as_dict=True)
    else:
        overall = frappe.db.sql("""
            SELECT target FROM `tabTarget Vs Achivement`
            WHERE sol_id = %s AND type = 'Monthly' AND month = %s AND financial_year = %s
        """, (sol_id, sel_month, fy), as_dict=True)

    overall_target = flt(overall[0].get('target')) if overall else 0.0

    target_amounts = {p: (overall_target * targets[p]) / 100 for p in targets}
    target_amounts["TOTAL TARGET"] = overall_target

    return {
        "status": "success",
        "sol_id": sol_id,
        "zone": zone,
        "financial_year": financial_year,
        "mode": mode,
        "month": sel_month,
        "current_month": current_month,
        "report_date": str(actual_date),
        "period_label": period_label,
        "collections": collections,
        "targets": targets,
        "target_amounts": target_amounts
    }


def _fy_for_month(month_code, today_dt):
    mnum = MONTH_MAP.get(month_code, today_dt.month) if month_code else today_dt.month
    if mnum >= 4:
        fy_start = today_dt.year if today_dt.month >= 4 else today_dt.year - 1
        return f"{fy_start}-{fy_start + 1}"
    else:
        fy_end = today_dt.year if today_dt.month < 4 else today_dt.year + 1
        return f"{fy_end - 1}-{fy_end}"


def _aggregate_collections(data):
    collections = {p: 0.0 for p in ("CASA", "DAM", "DD", "FD", "RD", "SMBG")}
    for row in data:
        product_name = row.get("product")
        if product_name in collections:
            collections[product_name] = flt(row.get("total_amount") or 0.0)
    return collections


def _get_latest_pwr_date(sol_id, before_date):
    res = frappe.db.sql("""
        SELECT MAX(date) as d FROM `tabProduct Wise Report`
        WHERE sol_id = %s AND date <= %s
    """, (sol_id, before_date), as_dict=True)
    return res[0].get("d") if res and res[0].get("d") else None


def _get_last_available_date_for_month(month_num, year):
    dates = frappe.db.sql("""
        SELECT DISTINCT date FROM `tabProduct Wise Report`
        WHERE MONTH(date) = %s AND YEAR(date) = %s
        ORDER BY date DESC
    """, (month_num, year), as_dict=True)
    for d in dates:
        return str(getdate(d.date))
    return None


def _get_ytd_collections(sol_id, target_date):
    dt = target_date if isinstance(target_date, date) else getdate(target_date)
    if dt.month >= 4:
        fy_start_year = dt.year
        months_up_to = [(m, fy_start_year) for m in range(4, dt.month + 1)]
    else:
        fy_start_year = dt.year - 1
        months_up_to = [(m, fy_start_year + 1) for m in range(1, dt.month + 1)]

    collections = {p: 0.0 for p in ("CASA", "DAM", "DD", "FD", "RD", "SMBG")}
    for (m, y) in months_up_to:
        last_date = _get_last_available_date_for_month(m, y)
        if not last_date:
            continue
        rows = frappe.db.sql("""
            SELECT product, SUM(amount) as total_amount
            FROM `tabProduct Wise Report`
            WHERE sol_id = %s AND date = %s
            GROUP BY product
        """, (sol_id, last_date), as_dict=True)
        for row in rows:
            p = row.get("product")
            if p in collections:
                collections[p] += flt(row.get("total_amount") or 0.0)
    return collections


def _get_ytd_period_label(target_date):
    dt = target_date if isinstance(target_date, date) else getdate(target_date)
    if dt.month >= 4:
        fy_start_year = dt.year
    else:
        fy_start_year = dt.year - 1
    return f"YTD Apr {fy_start_year} – {dt.strftime('%b %Y')}"
