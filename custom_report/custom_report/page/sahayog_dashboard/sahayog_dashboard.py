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
    Returns restricted lists for zones, regions, and sol_ids.
    Numeric values are extracted for zones and regions to avoid string matching issues.
    """
    permissions = {
        "zones": [],
        "regions": [],
        "sol_ids": [],
        "is_restricted": False,
        "all_regions": False,
        "zone_ids": [], # Numeric IDs
        "region_ids": [] # Numeric IDs
    }

    # System Manager usually sees everything
    if "System Manager" in frappe.get_roles(user):
        return permissions

    pref_name = frappe.db.get_value("Report Preference", {"user": user}, "name")
    if not pref_name:
        return permissions

    doc = frappe.get_doc("Report Preference", pref_name)
    permissions["pref_name"] = pref_name
    permissions["is_restricted"] = True
    permissions["all_regions"] = doc.all_regions
    
    if hasattr(doc, "zone"):
        permissions["zones"] = [d.zone for d in doc.zone if d.zone]
        # Extract numbers: "ZONE-1" or "Zone - 1" -> "1"
        permissions["zone_ids"] = [re.sub(r"\D", "", d.zone) for d in doc.zone if d.zone and re.sub(r"\D", "", d.zone)]
    
    if hasattr(doc, "region"):
        permissions["regions"] = [d.region for d in doc.region if d.region]
        permissions["region_ids"] = [re.sub(r"\D", "", d.region) for d in doc.region if d.region and re.sub(r"\D", "", d.region)]
        
    if hasattr(doc, "sol_id"):
        permissions["sol_ids"] = [d.sol_id for d in doc.sol_id if d.sol_id]
        
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

    if target_type in ["Yearly", "YTD"]:
        current_m_idx = None
        for idx, m in enumerate(all_months):
            if m[1] == current_month and m[2] == current_year:
                current_m_idx = idx
                break
        
        if current_m_idx is not None:
            current_month_date = get_last_available_date_for_month(current_month, current_year)
            if current_month_date:
                result_months.append((all_months[current_m_idx][0], current_month, current_year, current_month_date))
            
            prev_m_idx = current_m_idx - 1
            if prev_m_idx >= 0:
                prev_m = all_months[prev_m_idx]
                prev_month_date = get_last_available_date_for_month(prev_m[1], prev_m[2])
                if prev_month_date:
                    result_months.append((prev_m[0], prev_m[1], prev_m[2], prev_month_date))
        
        return result_months

    if view == "Monthly":
        for m in all_months:
            if m[1] == current_month and m[2] == current_year:
                if selected_date_obj and selected_date_obj.month == current_month and selected_date_obj.year == current_year:
                    if selected_date_obj.weekday() != 6:
                        exists = frappe.db.exists("Branch Category Report", {"date": selected_date_obj})
                        if exists:
                            result_months.append((m[0], m[1], m[2], str(selected_date_obj)))
                            break
                last_date = get_last_available_date_for_month(m[1], m[2])
                if last_date:
                    result_months.append((m[0], m[1], m[2], last_date))
                break
    
    elif view == "Quarterly":
        current_idx = next((idx for idx, m in enumerate(all_months) if m[1] == current_month and m[2] == current_year), None)
        if current_idx is not None:
            for i in range(2, -1, -1):
                idx = current_idx - i
                if idx >= 0:
                    m = all_months[idx]
                    last_date = get_last_available_date_for_month(m[1], m[2])
                    if last_date:
                        result_months.append((m[0], m[1], m[2], last_date))
    else:  # Yearly
        for m in all_months:
            last_date = get_last_available_date_for_month(m[1], m[2])
            if last_date:
                result_months.append((m[0], m[1], m[2], last_date))
            if m[1] == current_month and m[2] == current_year:
                break
    
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
def get_sahayog_dashboard(
    financial_year="2025-2026",
    view="Monthly",
    target_type="Monthly",
    filters=None,
    selected_date=None
):
    user = frappe.session.user
    perms = get_user_report_permissions(user)
    
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
                # Match "ZONE-1", "Zone 1", etc. using numeric suffix
                zone_conditions = []
                for zid in perms["zone_ids"]:
                    zone_conditions.append(f"%{zid}")
                combined_filters["zone"] = ["like", zone_conditions] if len(zone_conditions) == 1 else ["in", perms["zones"]]
                
                # If multiple zone IDs, we fetch actual names from DB to use IN
                if len(perms["zone_ids"]) > 1:
                    regex_pattern = f"({'|'.join(perms['zone_ids'])})"
                    matched_zones = frappe.db.sql("""
                        SELECT DISTINCT zone FROM `tabSahayog Branch` 
                        WHERE zone REGEXP %s
                    """, (regex_pattern), pluck=True)
                    combined_filters["zone"] = ["in", matched_zones] if matched_zones else ["in", ["_NONE_"]]
            
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
                # Intersect UI filter with permissions if restricted
                if perms["is_restricted"] and perms["zones"]:
                    allowed_ui_zones = [z for z in ui_zones if z in perms["zones"]]
                    combined_filters["zone"] = ["in", allowed_ui_zones] if allowed_ui_zones else ["in", ["_NONE_"]]
                else:
                    combined_filters["zone"] = ["in", ui_zones]
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
    category_wise = build_category_wise(all_branch_data, targets_map, months, target_type)
    branch_wise = build_branch_wise(all_branch_data, targets_map, months, target_type)
    
    return {
        "financial_year": financial_year,
        "view": view,
        "target_type": target_type,
        "selected_date": str(selected_date) if selected_date else None,
        "months": [{"key": m[0], "display": f"{m[0]}-{str(m[2])[-2:]}", "date": m[3]} for m in months],
        "zone_wise": zone_wise,
        "category_wise": category_wise,
        "branch_wise": branch_wise,
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
