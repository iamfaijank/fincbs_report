import frappe
from frappe.utils import add_days, today, getdate

@frappe.whitelist()
def get_sol_product_wise_collection(sol_id, zone, financial_year="2026-2027", report_date=None):
    """
    Fetch product wise collection (ACH) from 'Product Wise Report' doctype for today - 1 day.
    """
    if not report_date:
        target_date = add_days(today(), -1)
    else:
        target_date = report_date

    # Fetch data for today - 1 day (or latest date <= today - 1 day if exact date not present)
    data = frappe.db.sql("""
        SELECT product, SUM(amount) as total_amount
        FROM `tabProduct Wise Report`
        WHERE sol_id = %s AND date = %s
        GROUP BY product
    """, (sol_id, target_date), as_dict=True)
    
    actual_date = target_date
    if not data:
        latest_date_query = frappe.db.sql("""
            SELECT MAX(date) as latest_date
            FROM `tabProduct Wise Report`
            WHERE sol_id = %s AND date <= %s
        """, (sol_id, target_date), as_dict=True)
        latest_date = latest_date_query[0].get('latest_date') if latest_date_query else None
        if latest_date:
            actual_date = latest_date
            data = frappe.db.sql("""
                SELECT product, SUM(amount) as total_amount
                FROM `tabProduct Wise Report`
                WHERE sol_id = %s AND date = %s
                GROUP BY product
            """, (sol_id, actual_date), as_dict=True)
        else:
            data = []
    
    collections = {
        "CASA": 0.0,
        "DAM": 0.0,
        "DD": 0.0,
        "FD": 0.0,
        "RD": 0.0,
        "SMBG": 0.0
    }
    
    for row in data:
        product_name = row.get("product")
        if product_name in collections:
            collections[product_name] = row.get("total_amount") or 0.0
            
    collections["TOTAL TARGET"] = sum(collections.values())

    # Fetch Target Percentages based on zone and financial year
    targets = {
        "CASA": 0.0,
        "DAM": 0.0,
        "DD": 0.0,
        "FD": 0.0,
        "RD": 0.0,
        "SMBG": 0.0
    }
    
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
            targets["CASA"] = t.get("casa", 0.0)
            targets["DAM"] = t.get("dam", 0.0)
            targets["DD"] = t.get("dd", 0.0)
            targets["FD"] = t.get("fd", 0.0)
            targets["RD"] = t.get("rd", 0.0)
            targets["SMBG"] = t.get("smbg", 0.0)

    # Calculate overall target from Target Vs Achivement based on current date
    from datetime import date
    today_dt = date.today()
    current_month = today_dt.strftime('%b').upper()
    
    if today_dt.month >= 4:
        fy = f"{today_dt.year}-{today_dt.year + 1}"
    else:
        fy = f"{today_dt.year - 1}-{today_dt.year}"

    target_vs_ach_data = frappe.db.sql("""
        SELECT target
        FROM `tabTarget Vs Achivement`
        WHERE sol_id = %s AND type = 'Monthly' AND month = %s AND financial_year = %s
    """, (sol_id, current_month, fy), as_dict=True)
    
    overall_target = target_vs_ach_data[0].get('target') if target_vs_ach_data else 0.0

    target_amounts = {
        "CASA": (overall_target * targets["CASA"]) / 100,
        "DAM": (overall_target * targets["DAM"]) / 100,
        "DD": (overall_target * targets["DD"]) / 100,
        "FD": (overall_target * targets["FD"]) / 100,
        "RD": (overall_target * targets["RD"]) / 100,
        "SMBG": (overall_target * targets["SMBG"]) / 100,
        "TOTAL TARGET": overall_target
    }

    return {
        "status": "success",
        "sol_id": sol_id,
        "zone": zone,
        "financial_year": financial_year,
        "current_month": current_month,
        "report_date": str(actual_date),
        "collections": collections,
        "targets": targets,
        "target_amounts": target_amounts
    }
