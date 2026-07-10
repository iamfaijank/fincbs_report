# ===========================================
# COMPLETE SAHAYOG DASHBOARD API - UPDATED
# Copy-Paste Ready - Frappe/ERPNext
# Zone Breakdown Added in Category Wise
# ===========================================


import frappe
from frappe import _
from frappe.utils import getdate, formatdate
import json
import re
from collections import defaultdict
from datetime import datetime


CATEGORY_ORDER = ["Pinnacle", "Master", "Accelerator", "Starter", "Learner", "Zero Level"]


def get_user_report_permissions(user):
    """
    Fetches permissions from 'Report Preference' for the current user.
    Returns restricted lists for zones, regions, and sol_data (sol_id + branch_name).
    """
    permissions = {
        "zones": [],
        "regions": [],
        "sol_data": [],
        "sol_ids": [],
        "is_restricted": False,
        "all_regions": False,
        "zone_ids": [],
        "region_ids": [],
        "has_access": True
    }

    pref_name = frappe.db.get_value("Report Preference", {"user": user}, "name")
    if not pref_name:
        if "System Manager" in frappe.get_roles(user):
            return permissions
        permissions["has_access"] = False
        return permissions

    doc = frappe.get_doc("Report Preference", pref_name)
    permissions["pref_name"] = pref_name
    permissions["is_restricted"] = True
    permissions["all_regions"] = doc.all_regions
    
    # Query child tables directly (avoids ORM caching issues)
    permissions["zones"] = frappe.db.get_all("Zone Items", filters={"parent": pref_name, "parentfield": "zone"}, pluck="zone") or []
    permissions["zone_ids"] = [re.sub(r"\D", "", z) for z in permissions["zones"] if re.sub(r"\D", "", z)]
    
    permissions["regions"] = frappe.db.get_all("Region Items", filters={"parent": pref_name, "parentfield": "region"}, pluck="region") or []
    permissions["region_ids"] = [re.sub(r"\D", "", r) for r in permissions["regions"] if re.sub(r"\D", "", r)]
    
    permissions["sol_ids"] = frappe.db.get_all("Sol Items", filters={"parent": pref_name, "parentfield": "sol_id"}, pluck="sol_id") or []

    # Fetch branch names from Sahayog Branch for permitted sol_ids
    if permissions["sol_ids"]:
        branches = frappe.get_all(
            "Sahayog Branch",
            filters={"name": ["in", permissions["sol_ids"]]},
            fields=["name as sol_id", "branch as branch_name"]
        )
        permissions["sol_data"] = branches
    
    return permissions


def calculate_category(achievement_pct):
    """Runtime category calculation based on Target vs Achievement %."""
    if achievement_pct >= 100: return "Pinnacle"
    elif achievement_pct >= 80: return "Master"
    elif achievement_pct >= 60: return "Accelerator"
    elif achievement_pct >= 40: return "Starter"
    elif achievement_pct >= 20: return "Learner"
    else: return "Zero Level"


def get_last_available_date_for_month(month_num, year):
    dates = frappe.db.sql("""
        SELECT DISTINCT date 
        FROM `tabBranch Category Report` 
        WHERE MONTH(date) = %s AND YEAR(date) = %s
        ORDER BY date DESC
    """, (month_num, year), as_dict=True)
    
    for d in dates:
        date_obj = getdate(d.date)
        if date_obj.weekday() != 6:
            return str(date_obj)
    return None


def get_previous_available_date(current_date):
    dates = frappe.db.sql("""
        SELECT DISTINCT date 
        FROM `tabBranch Category Report` 
        WHERE date < %s
        ORDER BY date DESC
        LIMIT 10
    """, (current_date,), as_dict=True)
    
    for d in dates:
        date_obj = getdate(d.date)
        if date_obj.weekday() != 6:
            return str(date_obj)
    return None


def normalize_target_type(target_type):
    if target_type in ("Monthly", "YTD", "Yearly"):
        return target_type
    return "Monthly"


def get_matching_location_values(doctype, fieldname, values):
    allowed_fields = {"zone", "region"}
    if fieldname not in allowed_fields or not values:
        return values

    numeric_ids = [re.sub(r"\D", "", str(value)) for value in values if re.sub(r"\D", "", str(value))]
    if not numeric_ids:
        return values

    regex_pattern = f"({'|'.join(re.escape(num) for num in numeric_ids)})"
    return frappe.db.sql(
        f"""
        SELECT DISTINCT `{fieldname}`
        FROM `tab{doctype}`
        WHERE `{fieldname}` REGEXP %s
        """,
        (regex_pattern,),
        pluck=True,
    )


def get_fy_months_with_dates(financial_year, view="Monthly", selected_date=None, target_type="Monthly"):
    start_year = int(financial_year.split("-")[0])
    
    all_months = [
        ("APR", 4, start_year), ("MAY", 5, start_year), ("JUN", 6, start_year),
        ("JUL", 7, start_year), ("AUG", 8, start_year), ("SEP", 9, start_year),
        ("OCT", 10, start_year), ("NOV", 11, start_year), ("DEC", 12, start_year),
        ("JAN", 1, start_year + 1), ("FEB", 2, start_year + 1), ("MAR", 3, start_year + 1)
    ]
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    result_months = []
    selected_date_obj = getdate(selected_date) if selected_date else None

    if view == "Monthly":
        ref_date = selected_date_obj if selected_date_obj else datetime.now()
        ref_month = ref_date.month
        ref_year = ref_date.year
        for m in all_months:
            if m[1] == ref_month and m[2] == ref_year:
                if selected_date_obj and selected_date_obj.month == ref_month and selected_date_obj.year == ref_year:
                    if selected_date_obj.weekday() != 6:
                        exists = frappe.db.exists("Branch Category Report", {"date": selected_date_obj})
                        if exists:
                            result_months.append((m[0], m[1], m[2], str(selected_date_obj)))
                            break
                last_date = get_last_available_date_for_month(m[1], m[2])
                if last_date:
                    result_months.append((m[0], m[1], m[2], last_date))
                break
    
    elif view in ("Quarterly", "Yearly"):
        for m in all_months:
            last_date = get_last_available_date_for_month(m[1], m[2])
            if not last_date:
                # Fallback to a default date for the month if no data exists yet (e.g. first day of the month)
                last_date = f"{m[2]}-{m[1]:02d}-01"
            result_months.append((m[0], m[1], m[2], last_date))
    
    return result_months


def get_branch_categories_for_date(date, targets_map, month_key, target_type="Monthly"):
    """Get all branches with their categories for a specific date with target_type support."""
    branch_data = frappe.get_all(
        "Branch Category Report",
        filters={"date": date},
        fields=["sol_id", "branch", "zone", "region", "achievement", "yearly_achievement"]
    )
    
    result = {}
    for row in branch_data:
        sol_id = str(row.get("sol_id") or "")
        
        if target_type == "Monthly":
            ach = float(row.get("achievement") or 0)
        else:
            ach = float(row.get("yearly_achievement") or 0)
        
        tgt = targets_map[sol_id][month_key]
        pct = (ach / tgt * 100) if tgt > 0 else 0
        cat = calculate_category(pct)
        
        result[sol_id] = {
            "branch": row.get("branch") or "Unknown",
            "zone": row.get("zone") or "Unknown",
            "region": row.get("region") or "Unknown",
            "category": cat,
            "achievement": round(ach, 2),
            "target": round(tgt, 2),
            "percentage": round(pct, 2)
        }
    
    return result


def calculate_category_changes(current_date_data, previous_date_data):
    changes = {cat: {"increased": [], "decreased": []} for cat in CATEGORY_ORDER}
    
    for sol_id, curr_data in current_date_data.items():
        curr_cat = curr_data["category"]
        
        if sol_id in previous_date_data:
            prev_data = previous_date_data[sol_id]
            prev_cat = prev_data["category"]
            
            ach_diff = round(curr_data["achievement"] - prev_data["achievement"], 2)
            pct_diff = round(curr_data["percentage"] - prev_data["percentage"], 2)
            
            if curr_cat != prev_cat:
                curr_idx = CATEGORY_ORDER.index(curr_cat)
                prev_idx = CATEGORY_ORDER.index(prev_cat)
                
                change_record = {
                    "sol_id": sol_id,
                    "branch": curr_data["branch"],
                    "zone": curr_data["zone"],
                    "region": curr_data["region"],
                    "previous_category": prev_cat,
                    "current_category": curr_cat,
                    "previous_achievement": prev_data["achievement"],
                    "previous_target": prev_data["target"],
                    "previous_percentage": prev_data["percentage"],
                    "current_achievement": curr_data["achievement"],
                    "current_target": curr_data["target"],
                    "current_percentage": curr_data["percentage"],
                    "achievement_diff": ach_diff,
                    "percentage_diff": pct_diff
                }
                
                if curr_idx < prev_idx:
                    changes[curr_cat]["increased"].append(change_record)
                else:
                    changes[curr_cat]["decreased"].append(change_record)
        else:
            changes[curr_cat]["increased"].append({
                "sol_id": sol_id,
                "branch": curr_data["branch"],
                "zone": curr_data["zone"],
                "region": curr_data["region"],
                "previous_category": "New Entry",
                "current_category": curr_cat,
                "previous_achievement": 0,
                "previous_target": 0,
                "previous_percentage": 0,
                "current_achievement": curr_data["achievement"],
                "current_target": curr_data["target"],
                "current_percentage": curr_data["percentage"],
                "achievement_diff": curr_data["achievement"],
                "percentage_diff": curr_data["percentage"]
            })
    
    for sol_id, prev_data in previous_date_data.items():
        if sol_id not in current_date_data:
            prev_cat = prev_data["category"]
            changes[prev_cat]["decreased"].append({
                "sol_id": sol_id,
                "branch": prev_data["branch"],
                "zone": prev_data["zone"],
                "region": prev_data["region"],
                "previous_category": prev_cat,
                "current_category": "Not Available",
                "previous_achievement": prev_data["achievement"],
                "previous_target": prev_data["target"],
                "previous_percentage": prev_data["percentage"],
                "current_achievement": 0,
                "current_target": 0,
                "current_percentage": 0,
                "achievement_diff": -prev_data["achievement"],
                "percentage_diff": -prev_data["percentage"]
            })
    
    return changes


@frappe.whitelist(allow_guest=True)
def get_latest_branch_category_report_date():
    """Returns the latest available date from 'Branch Category Report' doctype."""
    latest_date = frappe.db.get_value("Branch Category Report", {}, "date", order_by="date desc")
    if latest_date:
        return str(latest_date)[:10]
    return None


@frappe.whitelist(allow_guest=True)
def get_latest_product_report_date():
    """Returns the latest available date from 'Product Wise Report' doctype."""
    latest_date = frappe.db.get_value("Product Wise Report", {}, "date", order_by="date desc")
    if latest_date:
        return str(latest_date)[:10]
    return None


@frappe.whitelist(allow_guest=True)
def get_latest_agent_report_date():
    """Returns the latest available date from 'Agent  Wise Report' doctype."""
    latest_date = frappe.db.get_value("Agent  Wise Report", {}, "date", order_by="date desc")
    if latest_date:
        # Return only date portion (yyyy-mm-dd), strip time
        return str(latest_date)[:10]
    return None


@frappe.whitelist(allow_guest=True)
def get_available_financial_years():
    """Returns dynamically generated Indian financial years (current and past two)."""
    import datetime
    today = datetime.date.today()
    
    if today.month >= 4:
        current_fy_start = today.year
    else:
        current_fy_start = today.year - 1
        
    fy_list = []
    for i in range(3):
        start_year = current_fy_start - i
        end_year = start_year + 1
        fy_list.append(f"{start_year}-{end_year}")
        
    return fy_list


@frappe.whitelist(allow_guest=True)
def get_sahayog_dashboard(
    financial_year=None,
    view="Monthly",
    target_type="Monthly",
    filters=None,
    selected_date=None
):
    user = frappe.session.user
    perms = get_user_report_permissions(user)
    target_type = normalize_target_type(target_type)
    
    if not financial_year:
        import datetime
        today = datetime.date.today()
        current_fy_start = today.year if today.month >= 4 else today.year - 1
        financial_year = f"{current_fy_start}-{current_fy_start + 1}"
    
    months = get_fy_months_with_dates(financial_year, view, selected_date, target_type)
    if not months:
        return {
            "financial_year": financial_year,
            "view": view,
            "target_type": target_type,
            "selected_date": str(selected_date) if selected_date else None,
            "months": [],
            "zone_wise": [],
            "category_wise": [],
            "branch_wise": [],
            "permissions": perms
        }
    
    month_keys = [m[0] for m in months]
    
    # Merge UI filters with User Permissions (Simplified Logic)
    combined_filters = {}
    if perms["is_restricted"]:
        # Priority 1: Specific SOL IDs (if provided, they take precedence)
        if perms["sol_ids"]:
            combined_filters["sol_id"] = ["in", perms["sol_ids"]]
        
        # Priority 2: Zone & Region (if no specific SOL IDs provided)
        else:
            # 🛡️ Numeric Matching Logic for Zones
            if perms["zone_ids"]:
                if len(perms["zone_ids"]) > 1:
                    regex_pattern = f"({'|'.join(perms['zone_ids'])})"
                    matched_zones = frappe.db.sql("""
                        SELECT DISTINCT zone FROM `tabSahayog Branch` 
                        WHERE zone REGEXP %s
                    """, (regex_pattern), pluck=True)
                    combined_filters["zone"] = ["in", matched_zones] if matched_zones else ["in", ["_NONE_"]]
                else:
                    combined_filters["zone"] = ["like", f"%{perms['zone_ids'][0]}"]
            
            # 🛡️ Numeric Matching Logic for Regions
            if not perms["all_regions"] and perms["region_ids"]:
                if len(perms["region_ids"]) > 1:
                    regex_pattern = f"({'|'.join(perms['region_ids'])})"
                    matched_regions = frappe.db.sql("""
                        SELECT DISTINCT region FROM `tabSahayog Branch` 
                        WHERE region REGEXP %s
                    """, (regex_pattern), pluck=True)
                    combined_filters["region"] = ["in", matched_regions] if matched_regions else ["in", ["_NONE_"]]
                else:
                    combined_filters["region"] = ["like", f"%{perms['region_ids'][0]}"]
            
            # If everything is empty but restricted, show nothing
            if not perms["zone_ids"] and not perms["region_ids"] and not perms["all_regions"]:
                combined_filters["sol_id"] = ["in", ["_NONE_"]]

    if filters:
        try:
            f_dict = json.loads(filters)
            ui_zones = f_dict.get("zones", [])
            if ui_zones and "all" not in ui_zones:
                matched_ui_zones = get_matching_location_values(
                    "Branch Category Report", "zone", ui_zones
                )
                # Intersect UI filter with permissions if restricted
                if perms["is_restricted"] and perms["zones"]:
                    allowed_ui_zones = [
                        z for z in matched_ui_zones if re.sub(r"\D", "", z or "") in perms["zone_ids"]
                    ]
                    combined_filters["zone"] = ["in", allowed_ui_zones] if allowed_ui_zones else ["in", ["_NONE_"]]
                else:
                    combined_filters["zone"] = ["in", matched_ui_zones] if matched_ui_zones else ["in", ["_NONE_"]]
        except:
            pass
    
    # Filter targets map to only include allowed sol_ids
    allowed_sol_ids = None
    if perms["is_restricted"] and perms["sol_ids"]:
        allowed_sol_ids = perms["sol_ids"]
        
    targets_map = get_targets_map(financial_year, target_type, month_keys, allowed_sol_ids)
    
    all_branch_data = []
    for month_key, month_num, year, eff_date in months:
        branch_filters = {"date": eff_date}
        # Apply combined permissions and UI filters
        branch_filters.update(combined_filters)
        
        month_data = frappe.get_all(
            "Branch Category Report",
            filters=branch_filters,
            fields=["date", "sol_id", "branch", "zone", "region", "achievement", "yearly_achievement"]
        )
        for rec in month_data:
            rec["month_key"] = month_key
        all_branch_data.extend(month_data)
    
    zone_wise = build_zone_wise(all_branch_data, targets_map, target_type)
    product_wise_result, all_products = build_product_wise(all_branch_data, targets_map, target_type, selected_date)
    category_wise = build_category_wise(all_branch_data, targets_map, months, target_type)
    branch_wise = build_branch_wise(all_branch_data, targets_map, months, target_type)
    agent_wise = build_agent_wise(selected_date)

    return {
        "financial_year": financial_year,
        "view": view,
        "target_type": target_type,
        "selected_date": str(selected_date) if selected_date else None,
        "months": [{"key": m[0], "display": f"{m[0]}-{str(m[2])[-2:]}", "date": m[3]} for m in months],
        "zone_wise": zone_wise,
        "product_wise": product_wise_result,
        "all_products": all_products,
        "category_wise": category_wise,
        "branch_wise": branch_wise,
        "agent_wise": agent_wise,
        "permissions": perms
    }


def get_targets_map(financial_year, target_type, month_keys, allowed_sol_ids=None):
    targets_map = defaultdict(lambda: defaultdict(float))
    
    base_filters = {"financial_year": financial_year}
    if allowed_sol_ids:
        base_filters["sol_id"] = ["in", allowed_sol_ids]

    if target_type == "Monthly":
        monthly_targets = frappe.get_all(
            "Target Vs Achivement",
            filters={**base_filters, "type": "Monthly", "month": ["in", month_keys]},
            fields=["sol_id", "target", "month"]
        )
        for t in monthly_targets:
            sol_id = str(t.sol_id or "")
            month_key = str(t.month or "").strip().upper()
            targets_map[sol_id][month_key] += float(t.target or 0)
    
    elif target_type == "YTD":
        ytd_targets = frappe.get_all(
            "Target Vs Achivement",
            filters={**base_filters, "type": "YTD"},
            fields=["sol_id", "target"]
        )
        for t in ytd_targets:
            sol_id = str(t.sol_id or "")
            val = float(t.target or 0)
            for mk in month_keys:
                targets_map[sol_id][mk] = val
    
    else:  # Yearly
        yearly_targets = frappe.get_all(
            "Target Vs Achivement",
            filters={**base_filters, "type": "Yearly"},
            fields=["sol_id", "target"]
        )
        for t in yearly_targets:
            sol_id = str(t.sol_id or "")
            val = float(t.target or 0)
            for mk in month_keys:
                targets_map[sol_id][mk] = val
    
    return targets_map


def build_zone_wise(branch_data, targets_map, target_type):
    zone_hierarchy = defaultdict(lambda: defaultdict(lambda: {"zone": "", "region": "", "months": {}}))
    
    for row in branch_data:
        zone = row.get("zone") or "Unknown"
        region = row.get("region") or "Unknown"
        sol_id = str(row.get("sol_id") or "")
        month_key = row.get("month_key")
        if not month_key: continue
        
        if region not in zone_hierarchy[zone]:
            zone_hierarchy[zone][region] = {"zone": zone, "region": region, "months": {}}
        
        if month_key not in zone_hierarchy[zone][region]["months"]:
            zone_hierarchy[zone][region]["months"][month_key] = {"branches": set(), "target": 0.0, "achievement": 0.0}
        
        ach = float(row.get("achievement") or 0) if target_type == "Monthly" else float(row.get("yearly_achievement") or 0)
        tgt = targets_map[sol_id][month_key]
        
        zrm = zone_hierarchy[zone][region]["months"][month_key]
        zrm["branches"].add(sol_id)
        zrm["target"] += tgt
        zrm["achievement"] += ach
    
    zone_wise = []
    def zone_sort_key(z):
        if z.startswith("ZONE-"):
            try: return (0, int(z.split("-")[1]))
            except: return (1, z)
        return (2, z)
    
    for zone in sorted(zone_hierarchy.keys(), key=zone_sort_key):
        zone_total = {"zone": zone, "region": zone, "months": {}}
        
        for region in sorted(zone_hierarchy[zone].keys()):
            reg = zone_hierarchy[zone][region]
            for mk, mdata in reg["months"].items():
                branch_count = len(mdata["branches"])
                target = mdata["target"]
                ach = mdata["achievement"]
                pct = round((ach / target) * 100, 2) if target > 0 else 0.0
                mdata["branches"] = branch_count
                mdata["percentage"] = pct
                
                if mk not in zone_total["months"]:
                    zone_total["months"][mk] = {"branches": 0, "target": 0.0, "achievement": 0.0, "percentage": 0.0}
                ztm = zone_total["months"][mk]
                ztm["branches"] += branch_count
                ztm["target"] += target
                ztm["achievement"] += ach
        
        for mk, mdata in zone_total["months"].items():
            mdata["percentage"] = round((mdata["achievement"] / mdata["target"]) * 100, 2) if mdata["target"] > 0 else 0.0
        
        zone_wise.append(zone_total)
        for region in sorted(zone_hierarchy[zone].keys()):
            zone_wise.append(zone_hierarchy[zone][region])
    
    return zone_wise


def build_product_wise(branch_data, targets_map, target_type, selected_date=None):
    # Determine the effective date: use selected_date or default to the last available date
    if not selected_date:
        selected_date = frappe.db.get_value("Product Wise Report", {}, "date", order_by="date desc")

    if not selected_date:
        return [], []

    # 1. Server-side query with GROUP BY for performance - Filtered by date
    data = frappe.db.sql("""
        SELECT
            zone,
            region,
            COUNT(*) as record_count,
            SUM(amount) as total_amount
        FROM `tabProduct Wise Report`
        WHERE zone IS NOT NULL AND region IS NOT NULL AND zone != '' AND region != ''
        AND date = %s
        GROUP BY zone, region
        ORDER BY zone, region
    """, (selected_date,), as_dict=True)

    # Fetch individual product details for each zone/region - Filtered by date
    product_details = frappe.db.sql("""
        SELECT
            zone,
            region,
            product,
            SUM(amount) as amount
        FROM `tabProduct Wise Report`
        WHERE zone IS NOT NULL AND region IS NOT NULL AND zone != '' AND region != ''
        AND date = %s
        GROUP BY zone, region, product
        ORDER BY zone, region, amount DESC
    """, (selected_date,), as_dict=True)

    if not data:
        return [], []

    # Get all unique products for dynamic column generation
    all_products = sorted(set(row.product for row in product_details))

    # Build a lookup for product details: {(zone, region): {product: amount, ...}}
    product_lookup = defaultdict(dict)
    for row in product_details:
        key = (row.zone, row.region)
        product_lookup[key][row.product] = row.amount

    # Calculate zone-wise product totals
    zone_product_totals = defaultdict(lambda: defaultdict(float))
    for row in product_details:
        zone_product_totals[row.zone][row.product] += row.amount

    # 2. Process into a hierarchical structure for the frontend
    zone_summary = defaultdict(lambda: {'count': 0, 'amount': 0.0})
    for row in data:
        zone_summary[row.zone]['count'] += row.record_count
        zone_summary[row.zone]['amount'] += (row.total_amount or 0)

    # 3. Build the final flat list with parent (Zone) and child (Region) rows
    result = []
    for zone, summary in sorted(zone_summary.items()):
        # Add Zone Group Row with product totals
        result.append({
            "name": zone,
            "parent": None,
            "count": summary['count'],
            "amount": summary['amount'],
            "is_group": True,
            "products": dict(zone_product_totals.get(zone, {}))  # Product-wise totals for zone
        })
        # Add corresponding Region Rows
        for row in data:
            if row.zone == zone:
                result.append({
                    "name": row.region,
                    "parent": zone,
                    "count": row.record_count,
                    "amount": row.total_amount or 0,
                    "is_group": False,
                    "products": product_lookup.get((zone, row.region), {})
                })
    
    return result, all_products


# 🚀 NEW FUNCTION: Zone breakdown for each category
def build_category_wise(branch_data, targets_map, months, target_type):
    category_counts = {cat: {} for cat in CATEGORY_ORDER}
    
    for month_key, month_num, year, current_date in months:
        previous_date = get_previous_available_date(current_date)
        
        current_categories = {}
        # 🚀 NEW: Zone breakdown tracking
        zone_breakdown = {cat: defaultdict(int) for cat in CATEGORY_ORDER}
        
        for row in branch_data:
            if row.get("month_key") == month_key:
                sol_id = str(row.get("sol_id") or "")
                zone = row.get("zone") or "Unknown"
                
                ach = float(row.get("achievement") or 0) if target_type == "Monthly" else float(row.get("yearly_achievement") or 0)
                tgt = targets_map[sol_id][month_key]
                pct = (ach / tgt * 100) if tgt > 0 else 0
                cat = calculate_category(pct)
                
                current_categories[sol_id] = {
                    "branch": row.get("branch") or "Unknown",
                    "zone": zone,
                    "region": row.get("region") or "Unknown",
                    "category": cat,
                    "achievement": round(ach, 2),
                    "target": round(tgt, 2),
                    "percentage": round(pct, 2)
                }
                
                # 🚀 Track zone breakdown count
                zone_breakdown[cat][zone] += 1
                
                category_counts.setdefault(cat, {})
                category_counts[cat].setdefault(month_key, {"count": 0, "zone_breakdown": {}, "changes": None})
                category_counts[cat][month_key]["count"] += 1
        
        # 🚀 Add zone breakdown to category data
        for cat in CATEGORY_ORDER:
            if month_key in category_counts.get(cat, {}):
                category_counts[cat][month_key]["zone_breakdown"] = dict(zone_breakdown[cat])
        
        if previous_date:
            previous_categories = get_branch_categories_for_date(previous_date, targets_map, month_key, target_type)
            changes = calculate_category_changes(current_categories, previous_categories)
            
            for cat in CATEGORY_ORDER:
                if month_key in category_counts.get(cat, {}):
                    category_counts[cat][month_key]["changes"] = changes[cat]
                    category_counts[cat][month_key]["previous_date"] = previous_date
                    category_counts[cat][month_key]["current_date"] = current_date
    
    out = []
    for i, cat in enumerate(CATEGORY_ORDER, 1):
        out.append({"sr_no": i, "category": cat, "months": category_counts.get(cat, {})})
    
    return out


def build_branch_wise(branch_data, targets_map, months, target_type):
    branch_map = defaultdict(lambda: {"branch": "", "zone": "", "region": "", "months": {}})
    
    for month_key, month_num, year, current_date in months:
        previous_date = get_previous_available_date(current_date)
        previous_data = {}
        if previous_date:
            previous_data = get_branch_categories_for_date(previous_date, targets_map, month_key, target_type)
        
        for row in branch_data:
            if row.get("month_key") != month_key: continue
                
            sol_id = str(row.get("sol_id") or "")
            branch = row.get("branch") or "Unknown"
            zone = row.get("zone") or "Unknown"
            region = row.get("region") or "Unknown"
            ach = float(row.get("achievement") or 0) if target_type == "Monthly" else float(row.get("yearly_achievement") or 0)
            tgt = targets_map[sol_id][month_key]
            pct = (ach / tgt * 100) if tgt > 0 else 0
            cat = calculate_category(pct)
            
            branch_map[sol_id]["branch"] = branch
            branch_map[sol_id]["zone"] = zone
            branch_map[sol_id]["region"] = region
            
            month_data = {
                "category": cat,
                "target": round(tgt, 2),
                "achievement": round(ach, 2),
                "percentage": round(pct, 2)
            }
            
            if sol_id in previous_data:
                prev = previous_data[sol_id]
                month_data["previous_date"] = previous_date
                month_data["current_date"] = current_date
                month_data["previous_category"] = prev["category"]
                month_data["previous_achievement"] = prev["achievement"]
                month_data["previous_target"] = prev["target"]
                month_data["previous_percentage"] = prev["percentage"]
                month_data["achievement_diff"] = round(ach - prev["achievement"], 2)
                month_data["percentage_diff"] = round(pct - prev["percentage"], 2)
                
                if cat != prev["category"]:
                    curr_idx = CATEGORY_ORDER.index(cat)
                    prev_idx = CATEGORY_ORDER.index(prev["category"])
                    month_data["status"] = "improved" if curr_idx < prev_idx else "declined"
                elif month_data["percentage_diff"] > 0:
                    month_data["status"] = "increased"
                elif month_data["percentage_diff"] < 0:
                    month_data["status"] = "decreased"
                else:
                    month_data["status"] = "unchanged"
            else:
                month_data["status"] = "new"
                month_data["previous_date"] = previous_date if previous_date else None
                month_data["current_date"] = current_date
            
            branch_map[sol_id]["months"][month_key] = month_data
    
    out = []
    for i, (sol_id, data) in enumerate(branch_map.items(), 1):
        out.append({
            "sr_no": i,
            "sol_id": sol_id,
            "branch": data["branch"],
            "zone": data["zone"],
            "region": data["region"],
            "months": data["months"]
        })

    return out


def build_agent_wise(selected_date=None):
    """
    Build Agent Wise report from 'Agent  Wise Report' doctype.
    Groups by Zone and Region, aggregates target and achievement.
    Uses 'date' field as the date filter.
    """
    if not selected_date:
        selected_date = frappe.utils.today()
        
    # Fetch data from Agent  Wise Report doctype
    agent_data = frappe.get_all(
        "Agent  Wise Report",
        fields=["zone", "region", "target", "achievement", "ss_target", "ss_achievement", "ss_active", "ss_inactive", "active", "inactive"],
        filters={
            "zone": ["!=", ""], 
            "region": ["!=", ""],
            "date": ["between", [f"{selected_date} 00:00:00", f"{selected_date} 23:59:59"]]
        },
        limit_page_length=1000
    )
    
    # Group by zone and region
    agent_map = defaultdict(lambda: {
        "zone": "", 
        "region": "", 
        "target": 0.0, 
        "achievement": 0.0, 
        "ss_target": 0.0, 
        "ss_achievement": 0.0,
        "ss_active": 0.0,
        "ss_inactive": 0.0,
        "active": 0.0,
        "inactive": 0.0
    })
    
    for row in agent_data:
        zone = row.get("zone") or "Unknown"
        region = row.get("region") or "Unknown"
        
        # Convert to float (handle string values)
        try:
            tgt = float(row.get("target") or 0)
            ach = float(row.get("achievement") or 0)
            ss_tgt = float(row.get("ss_target") or 0)
            ss_ach = float(row.get("ss_achievement") or 0)
            ss_act = float(row.get("ss_active") or 0)
            ss_inact = float(row.get("ss_inactive") or 0)
            act = float(row.get("active") or 0)
            inact = float(row.get("inactive") or 0)
        except (ValueError, TypeError):
            tgt = 0
            ach = 0
            ss_tgt = 0
            ss_ach = 0
            ss_act = 0
            ss_inact = 0
            act = 0
            inact = 0
        
        key = f"{zone}||{region}"
        agent_map[key]["zone"] = zone
        agent_map[key]["region"] = region
        agent_map[key]["target"] += tgt
        agent_map[key]["achievement"] += ach
        agent_map[key]["ss_target"] += ss_tgt
        agent_map[key]["ss_achievement"] += ss_ach
        agent_map[key]["ss_active"] += ss_act
        agent_map[key]["ss_inactive"] += ss_inact
        agent_map[key]["active"] += act
        agent_map[key]["inactive"] += inact
    
    # Convert to list format
    result = []
    for key, data in agent_map.items():
        # Calculate shortfalls (target - achievement)
        ss_shortfall = data["ss_target"] - data["ss_achievement"]
        agent_shortfall = data["target"] - data["achievement"]

        # Format date as yyyy-mm-dd (strip time portion)
        date_str = str(data["date"])[:10] if data.get("date") else selected_date

        result.append({
            "zone": data["zone"],
            "region": data["region"],
            "date": date_str,
            "ss_target": round(data["ss_target"], 2),
            "ss_achievement": round(data["ss_achievement"], 2),
            "ss_shortfall": round(ss_shortfall, 2),
            "ss_active": round(data["ss_active"], 2),
            "ss_inactive": round(data["ss_inactive"], 2),
            "target": round(data["target"], 2),
            "achievement": round(data["achievement"], 2),
            "agent_shortfall": round(agent_shortfall, 2),
            "active": round(data["active"], 2),
            "inactive": round(data["inactive"], 2)
        })

    return result


@frappe.whitelist()
def get_rd_smbg_pending_table_data():
    from custom_report.db_connection import get_dr_connection
    import json

    query = """
    WITH main_data AS (
        SELECT g.acid, g.sol_id, s.sol_desc, t.maturity_date, t.last_repayment_date,
               s.division_name, s.region_name, s.circle_office_name
        FROM tbaadm.gam g
        JOIN tbaadm.tam t ON g.acid = t.acid
        JOIN tbaadm.sol s ON g.sol_id = s.sol_id
        WHERE g.schm_code IN ('2005','2010','2011','2012','2013','2014','2015','2016')
            AND g.entity_cre_flg = 'Y'
            AND g.del_flg = 'N'
            AND g.acct_cls_flg = 'N'
            AND t.maturity_date >= CURRENT_DATE
    ),
    tdt_summary AS (
        SELECT acid,
               COALESCE(SUM(tran_amt), 0) AS total_instalment_paid,
               COALESCE(SUM(flow_amt) - SUM(tran_amt), 0) AS pending_amount,
               COUNT(CASE WHEN flow_amt > 0 THEN 1 END) - COUNT(CASE WHEN tran_amt > 0 THEN 1 END) AS pending_instalments
        FROM tbaadm.tdt
        WHERE flow_code = 'NI'
            AND (flow_amt > 0 OR tran_amt > 0)
            AND flow_date <= CURRENT_DATE
        GROUP BY acid
    )
    SELECT m.sol_id, m.sol_desc, m.division_name, m.region_name, m.circle_office_name,
           COUNT(*) AS total_accounts,
           COALESCE(SUM(t.total_instalment_paid), 0) AS total_collection,
           COALESCE(SUM(CASE WHEN t.pending_amount > 0 THEN 1 ELSE 0 END), 0) AS pending_accounts,
           COALESCE(SUM(t.pending_amount), 0) AS pending_amount,
           COALESCE(SUM(t.pending_instalments), 0) AS pending_instalments
    FROM main_data m
    LEFT JOIN tdt_summary t ON m.acid = t.acid
    WHERE NOT (
        COALESCE(t.pending_instalments, 0) > 24
        AND m.last_repayment_date < (CURRENT_DATE - INTERVAL '1 year')
    )
    GROUP BY m.sol_id, m.sol_desc, m.division_name, m.region_name, m.circle_office_name
    ORDER BY m.sol_id
    """

    conn = get_dr_connection()
    if not conn:
        frappe.log_error("Failed to connect to DR database", "RD SMBG Table API")
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        sol_ids_found = [str(r[0]) for r in rows] if rows else []
        branch_map = {}
        if sol_ids_found:
            sb_data = frappe.get_all(
                "Sahayog Branch",
                filters={"name": ["in", sol_ids_found]},
                fields=["name as sol_id", "zone", "region", "district", "branch"]
            )
            for b in sb_data:
                branch_map[b.sol_id] = {
                    "zone": b.zone or "",
                    "region": b.region or "",
                    "district": b.district or "",
                    "branch_name": b.branch or ""
                }

        result = []
        for row in rows:
            sid = str(row[0])
            sb = branch_map.get(sid, {})
            result.append({
                "sol_id": sid,
                "sol_desc": row[1] or "",
                "zone": sb.get("zone", ""),
                "region": sb.get("region", ""),
                "district": sb.get("district", ""),
                "branch_name": sb.get("branch_name", ""),
                "total_accounts": row[5] or 0,
                "total_collection": float(row[6]) if row[6] else 0,
                "pending_accounts": row[7] or 0,
                "pending_amount": float(row[8]) if row[8] else 0,
                "pending_instalments": row[9] or 0
            })
        return result
    except Exception as e:
        frappe.log_error(f"Error executing RD/SMBG table query: {str(e)}", "RD SMBG Table API")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


@frappe.whitelist()
def get_mis_filter_options():
    user = frappe.session.user
    perms = get_user_report_permissions(user)
    
    zones = []
    regions = []
    districts = []

    # Apply same permission logic as Drishti (get_sahayog_dashboard)
    if perms.get("is_restricted"):
        allowed_zones = perms.get("zones", [])
        allowed_regions = perms.get("regions", [])
        # If zone permissions exist, use zones as primary filter — ignore sol_ids for data scope
        if allowed_zones:
            zones = [r[0] for r in frappe.db.sql("SELECT DISTINCT zone FROM `tabSahayog Branch` WHERE zone IS NOT NULL AND zone != ''")]
            # Normalize: uppercase, remove spaces/dashes/hyphens for matching
            allowed_norm = [re.sub(r"[\s\-]+", "", z or "").upper() for z in allowed_zones]
            zones = [z for z in zones if re.sub(r"[\s\-]+", "", z or "").upper() in allowed_norm]
            regions = [r[0] for r in frappe.db.sql("SELECT DISTINCT region FROM `tabSahayog Branch` WHERE region IS NOT NULL AND region != ''")]
            if allowed_regions:
                allowed_reg_norm = [re.sub(r"[\s\-]+", "", r or "").upper() for r in allowed_regions]
                regions = [r for r in regions if re.sub(r"[\s\-]+", "", r or "").upper() in allowed_reg_norm]
            districts = [r[0] for r in frappe.db.sql("SELECT DISTINCT district FROM `tabSahayog Branch` WHERE district IS NOT NULL AND district != ''")]
        elif perms["sol_ids"]:
            # No zone permissions — restrict by sol_ids
            branch_data = frappe.get_all(
                "Sahayog Branch",
                filters={"name": ["in", perms["sol_ids"]]},
                fields=["zone", "region", "district"]
            )
            zones = sorted(set(b.zone for b in branch_data if b.zone))
            regions = sorted(set(b.region for b in branch_data if b.region))
            districts = sorted(set(b.district for b in branch_data if b.district))
        else:
            zones = [r[0] for r in frappe.db.sql("SELECT DISTINCT zone FROM `tabSahayog Branch` WHERE zone IS NOT NULL AND zone != ''")]
            regions = [r[0] for r in frappe.db.sql("SELECT DISTINCT region FROM `tabSahayog Branch` WHERE region IS NOT NULL AND region != ''")]
            districts = [r[0] for r in frappe.db.sql("SELECT DISTINCT district FROM `tabSahayog Branch` WHERE district IS NOT NULL AND district != ''")]

    else:
        # No restrictions — show all
        zones = [r[0] for r in frappe.db.sql("SELECT DISTINCT zone FROM `tabSahayog Branch` WHERE zone IS NOT NULL AND zone != ''")]
        regions = [r[0] for r in frappe.db.sql("SELECT DISTINCT region FROM `tabSahayog Branch` WHERE region IS NOT NULL AND region != ''")]
        districts = [r[0] for r in frappe.db.sql("SELECT DISTINCT district FROM `tabSahayog Branch` WHERE district IS NOT NULL AND district != ''")]

    fixed_sol_id = None
    allowed_sol_ids = perms.get("sol_ids", [])
    
    # If zone permissions exist, don't use sol_ids (zones are the primary filter)
    if perms.get("is_restricted") and perms.get("zones"):
        allowed_sol_ids = []
        perms["sol_data"] = []
    else:
        # Fallback: if no sol_ids from Report Preference, check Employee sahayog_branch
        if not allowed_sol_ids:
            employee_sol = frappe.db.get_value("Employee", {"user_id": user}, "sahayog_branch")
            if employee_sol:
                allowed_sol_ids = [employee_sol]
                fixed_sol_id = employee_sol
        
        # If exactly one sol_id from report pref, also treat as fixed
        if not fixed_sol_id and len(allowed_sol_ids) == 1:
            fixed_sol_id = allowed_sol_ids[0]
    
    # Build sol_data: branch names from Sahayog Branch
    sol_data = perms.get("sol_data", [])
    if not sol_data and allowed_sol_ids:
        sol_data = frappe.get_all(
            "Sahayog Branch",
            filters={"name": ["in", allowed_sol_ids]},
            fields=["name as sol_id", "branch as branch_name"],
            order_by="name asc"
        )
    elif not sol_data:
        sol_data = frappe.get_all(
            "Sahayog Branch",
            fields=["name as sol_id", "branch as branch_name"],
            order_by="name asc"
        )
    
    return {
        "zones": sorted(zones),
        "regions": sorted(regions),
        "districts": sorted(districts),
        "sol_data": sol_data,
        "permissions": {
            "is_restricted": perms.get("is_restricted", False),
            "allowed_zones": perms.get("zones", []),
            "allowed_regions": perms.get("regions", []),
            "allowed_sol_ids": allowed_sol_ids,
            "fixed_sol_id": fixed_sol_id
        }
    }


@frappe.whitelist()
def get_daily_account_opening_data(selected_date=None):
    from custom_report.db_connection import get_dr_connection
    from frappe.utils import getdate
    import datetime

    if not selected_date:
        # Default to latest date from database or yesterday
        latest = get_latest_branch_category_report_date()
        if latest:
            selected_date = latest
        else:
            selected_date = str(datetime.date.today() - datetime.timedelta(days=1))

    try:
        dt = getdate(selected_date)
        start_date_str = dt.replace(day=1).strftime("%Y-%m-%d")
        end_date_str = dt.strftime("%Y-%m-%d")
    except Exception:
        start_date_str = "2026-07-01"
        end_date_str = "2026-07-09"

    # Fetch local Product mapping to categorize scheme codes
    try:
        products = frappe.get_all(
            "Product",
            fields=["name", "product_name", "group_name", "group_subname", "product_type"]
        )
    except Exception:
        products = []

    product_map = {}
    for p in products:
        code = p.name
        pname = (p.product_name or "").upper()
        gname = (p.group_name or "").upper()
        gsub = (p.group_subname or "").upper()
        ptype = (p.product_type or "").upper()
        
        category = "FD"  # Default fallback
        
        if gname == "CASA":
            if gsub == "SA":
                category = "SA"
            elif gsub == "CA":
                category = "CA"
            elif gsub == "TASC":
                category = "TASC"
            else:
                # Fallback within CASA group if group_subname is not set
                if "TASC" in pname:
                    category = "TASC"
                elif ptype == "CAA":
                    category = "CA"
                else:
                    category = "SA"
        elif gname == "RD":
            category = "RD"
        elif gname == "SMBG":
            category = "SMBG"
        elif gname == "DD":
            category = "DD"
        elif gname in ("FD", "DAM"):
            category = "FD"
        else:
            # Fallback heuristics for unmapped schemes
            if gsub == "SA" or code.startswith("SB") or "SAVING" in pname:
                category = "SA"
            elif gsub == "CA" or code.startswith("CA") or "CURRENT" in pname:
                category = "CA"
            elif gsub == "TASC" or "TASC" in pname:
                category = "TASC"
            elif code.startswith("RD") or "RECURRING" in pname:
                category = "RD"
            elif code.startswith("DD") or "DAILY" in pname:
                category = "DD"
            else:
                category = "FD"
                
        product_map[code] = category

    query = """
    WITH base_schemes AS (
        SELECT DISTINCT
            gam.schm_code,
            gsp.schm_desc
        FROM tbaadm.gam gam
        JOIN tbaadm.gsp gsp
            ON gam.schm_code = gsp.schm_code
        WHERE gam.schm_type NOT IN ('OAB','OAP')
    ),
    base_sol AS (
        SELECT
            sol.sol_id,
            sol.region_name,
            sol.division_name,
            sol.circle_office_name
        FROM tbaadm.sol sol
        JOIN tbaadm.sst sst
            ON sst.sol_id = sol.sol_id
        WHERE sst.set_id BETWEEN '1001' AND '1255'
    )
    SELECT
        bs.schm_code,
        bs.schm_desc,
        s.sol_id,
        s.region_name,
        s.division_name,
        s.circle_office_name,
        COUNT(DISTINCT gam.foracid) AS account_opened
    FROM base_sol s
    CROSS JOIN base_schemes bs
    LEFT JOIN tbaadm.gam gam
           ON gam.sol_id = s.sol_id
          AND gam.schm_code = bs.schm_code
          AND gam.acct_opn_date BETWEEN CAST(%s AS DATE) AND CAST(%s AS DATE)
          AND gam.entity_cre_flg = 'Y'
          AND gam.schm_type NOT IN ('OAB','OAP')
    GROUP BY
        bs.schm_code,
        bs.schm_desc,
        s.sol_id,
        s.region_name,
        s.division_name,
        s.circle_office_name
    ORDER BY
        s.sol_id,
        bs.schm_code
    """

    conn = get_dr_connection()
    if not conn:
        frappe.log_error("Failed to connect to DR database", "Daily Account Opening API")
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(query, (start_date_str, end_date_str))
        rows = cursor.fetchall()
        
        # Look up zones / regions from local Sahayog Branch
        sol_ids_found = [str(r[2]) for r in rows] if rows else []
        branch_map = {}
        if sol_ids_found:
            sb_data = frappe.get_all(
                "Sahayog Branch",
                filters={"name": ["in", sol_ids_found]},
                fields=["name as sol_id", "zone", "region", "district", "branch"]
            )
            for b in sb_data:
                branch_map[b.sol_id] = {
                    "zone": b.zone or "",
                    "region": b.region or "",
                    "district": b.district or "",
                    "branch_name": b.branch or ""
                }

        # Group and aggregate raw records by branch
        branch_aggregates = {}
        for row in rows:
            schm_code = row[0] or ""
            sid = str(row[2])
            region_name = row[3]
            circle_office_name = row[5]
            count = int(row[6]) if row[6] is not None else 0
            
            sb = branch_map.get(sid, {})
            zone = sb.get("zone", circle_office_name or "Unknown Zone")
            region = sb.get("region", region_name or "Unknown Region")
            branch_name = sb.get("branch_name", f"Branch {sid}")
            
            if sid not in branch_aggregates:
                branch_aggregates[sid] = {
                    "sol_id": sid,
                    "branch_name": branch_name,
                    "zone": zone,
                    "region": region,
                    "ca": 0,
                    "sa": 0,
                    "tasc": 0,
                    "rd": 0,
                    "smbg": 0,
                    "dd": 0,
                    "fd": 0,
                    "total": 0
                }
                
            cat = product_map.get(schm_code, "FD")
            if cat == "CA":
                branch_aggregates[sid]["ca"] += count
            elif cat == "SA":
                branch_aggregates[sid]["sa"] += count
            elif cat == "TASC":
                branch_aggregates[sid]["tasc"] += count
            elif cat == "RD":
                branch_aggregates[sid]["rd"] += count
            elif cat == "SMBG":
                branch_aggregates[sid]["smbg"] += count
            elif cat == "DD":
                branch_aggregates[sid]["dd"] += count
            elif cat == "FD":
                branch_aggregates[sid]["fd"] += count
                
            branch_aggregates[sid]["total"] += count
            
        return list(branch_aggregates.values())
        
    except Exception as e:
        frappe.log_error(f"Error executing Daily Account Opening query: {str(e)}", "Daily Account Opening API")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass
