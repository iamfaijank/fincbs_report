import calendar
from datetime import date
import frappe
from frappe.utils import add_days, today, getdate, flt


MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


@frappe.whitelist()
def get_sol_product_wise_collection(sol_id, zone, financial_year="2026-2027", report_date=None, mode="month", month=None):
    """
    Fetch product wise collection (ACH) from 'Product Wise Report' doctype.
    mode='ytd'   -> Sum of value from 01-04-(FY start) till yesterday (today - 1).
    mode='month' -> Chosen month from 01 till month end (or if current month, from 01 till today - 1).
    """
    mode = (mode or "month").lower()
    if mode not in ("month", "ytd"):
        mode = "month"

    today_dt = getdate(today())
    yesterday_dt = add_days(today_dt, -1)
    current_month = today_dt.strftime('%b').upper()

    # Determine financial year start year
    if today_dt.month >= 4:
        current_fy_start_year = today_dt.year
    else:
        current_fy_start_year = today_dt.year - 1
    current_fy = f"{current_fy_start_year}-{current_fy_start_year + 1}"
    fy = financial_year or current_fy

    if mode == "ytd":
        # FY Start: 01-04-YYYY till yesterday
        fy_start_year = int(fy.split("-")[0])
        start_date = f"{fy_start_year}-04-01"
        end_date = str(yesterday_dt)
        period_label = f"01 Apr {fy_start_year} – {yesterday_dt.strftime('%d %b %Y')}"
        actual_date = yesterday_dt
        sel_month = None

        # YTD Collection Query (Sum from 01-04-YYYY till yesterday)
        data = frappe.db.sql("""
            SELECT product, SUM(amount) as total_amount
            FROM `tabProduct Wise Report`
            WHERE sol_id = %s AND date >= %s AND date <= %s
            GROUP BY product
        """, (sol_id, start_date, end_date), as_dict=True)

        collections = _aggregate_collections(data)

        # Overall target (YTD)
        overall = frappe.db.sql("""
            SELECT target FROM `tabTarget Vs Achivement`
            WHERE sol_id = %s AND type = 'YTD' AND financial_year = %s
        """, (sol_id, fy), as_dict=True)

    else:
        # MONTH mode
        clean_m = (month or "").strip().upper() if month else ""
        if clean_m and clean_m in MONTH_MAP:
            sel_month = clean_m
        else:
            sel_month = current_month

        mnum = MONTH_MAP[sel_month]
        fy_start_year = int(fy.split("-")[0])
        cal_year = fy_start_year if mnum >= 4 else fy_start_year + 1
        start_date = f"{cal_year}-{mnum:02d}-01"

        is_current_month = (mnum == today_dt.month and cal_year == today_dt.year)
        if is_current_month:
            # 01 till today - 1 (yesterday)
            end_date = str(yesterday_dt)
            end_date_obj = yesterday_dt
        else:
            # 01 till that month end
            last_day = calendar.monthrange(cal_year, mnum)[1]
            end_date = f"{cal_year}-{mnum:02d}-{last_day:02d}"
            end_date_obj = getdate(end_date)

        if not (month and month.strip()) or start_date == end_date:
            period_label = f"As of: {end_date_obj.strftime('%d/%m/%Y')}"
        else:
            period_label = f"01 {sel_month.title()} {cal_year} – {end_date_obj.strftime('%d %b %Y')}"
        actual_date = end_date_obj

        # Month Collection Query (Sum from 01 till end_date)
        data = frappe.db.sql("""
            SELECT product, SUM(amount) as total_amount
            FROM `tabProduct Wise Report`
            WHERE sol_id = %s AND date >= %s AND date <= %s
            GROUP BY product
        """, (sol_id, start_date, end_date), as_dict=True)

        collections = _aggregate_collections(data)

        # Overall target (Monthly)
        overall = frappe.db.sql("""
            SELECT target FROM `tabTarget Vs Achivement`
            WHERE sol_id = %s AND type = 'Monthly' AND month = %s AND financial_year = %s
        """, (sol_id, sel_month, fy), as_dict=True)

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
        """, (zone, fy), as_dict=True)
        if target_data:
            t = target_data[0]
            for p in targets:
                targets[p] = flt(t.get(p.lower(), 0.0))

    overall_target = flt(overall[0].get('target')) if overall else 0.0
    target_amounts = {p: (overall_target * targets[p]) / 100 for p in targets}
    target_amounts["TOTAL TARGET"] = overall_target

    return {
        "status": "success",
        "sol_id": sol_id,
        "zone": zone,
        "financial_year": fy,
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
    cache_key = f"pwr_last_date_{month_num}_{year}"
    cached = frappe.cache().get_value(cache_key)
    if cached is not None:
        return cached

    dates = frappe.db.sql("""
        SELECT MAX(date) as d FROM `tabProduct Wise Report`
        WHERE MONTH(date) = %s AND YEAR(date) = %s
    """, (month_num, year), as_dict=True)
    
    val = str(getdate(dates[0].d)) if dates and dates[0].get("d") else None
    frappe.cache().set_value(cache_key, val, expires_in_sec=1800)
    return val


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
