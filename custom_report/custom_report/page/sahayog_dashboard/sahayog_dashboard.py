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


def sahayog_cache(ttl=86400):
    def decorator(func):
        def wrapper(*args, **kwargs):
            import json
            import hashlib
            import inspect

            # Filter args and kwargs based on target function's signature
            sig = inspect.signature(func)
            has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            has_args = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in sig.parameters.values())
            
            if has_kwargs:
                filtered_kwargs = kwargs
            else:
                filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
                
            if has_args:
                filtered_args = args
            else:
                pos_params = [p for p in sig.parameters.values() if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
                filtered_args = args[:len(pos_params)]

            # Generate deterministic cache key based on function name and filtered arguments
            args_str = f"{filtered_args}_{json.dumps(filtered_kwargs, sort_keys=True, default=str)}"
            key_hash = hashlib.md5(args_str.encode('utf-8')).hexdigest()
            cache_key = f"sahayog_cache|{func.__name__}|{key_hash}"
            
            cached_data = frappe.cache.get_value(cache_key)
            if cached_data is not None:
                return cached_data
                
            result = func(*filtered_args, **filtered_kwargs)
            
            # ONLY cache if result is truthy (non-empty list, non-empty dict, non-None)
            if result:
                frappe.cache.set_value(cache_key, result, expires_in_sec=ttl)
            return result
            
        def clear_cache():
            frappe.cache.delete_keys(f"sahayog_cache|{func.__name__}|*")
            
        wrapper.clear_cache = clear_cache
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


CATEGORY_ORDER = ["Pinnacle", "Master", "Accelerator", "Starter", "Learner", "Zero Level"]


def get_products_cached():
    """Fetches all Product records and caches them in Redis."""
    cache_key = "sahayog_products_list"
    cached_data = frappe.cache.get_value(cache_key)
    if cached_data:
        return cached_data
    products = frappe.get_all(
        "Product",
        fields=["name", "product_name", "group_name", "group_subname", "product_type"]
    )
    frappe.cache.set_value(cache_key, products, expires_in_sec=86400)
    return products


def get_product_group_map_cached():
    """Fetches name to group_name mapping for Products and caches them in Redis."""
    cache_key = "sahayog_product_group_map"
    cached_data = frappe.cache.get_value(cache_key)
    if cached_data:
        return cached_data
    products = frappe.get_all("Product", fields=["name", "group_name"])
    group_map = {p.name: p.group_name for p in products}
    frappe.cache.set_value(cache_key, group_map, expires_in_sec=86400)
    return group_map


def get_products_map_cached():
    """Returns a map of product name to product doc fields."""
    cache_key = "sahayog_products_map"
    cached_data = frappe.cache.get_value(cache_key)
    if cached_data:
        return cached_data
    products = frappe.get_all(
        "Product",
        fields=["name", "product_name", "group_name", "group_subname", "group_subname_category", "product_type"]
    )
    prod_map = {p.name: p for p in products}
    frappe.cache.set_value(cache_key, prod_map, expires_in_sec=86400)
    return prod_map


def clear_products_cache(doc=None, method=None):
    """Clears product-related caches from Redis."""
    frappe.cache.delete_value("sahayog_products_list")
    frappe.cache.delete_value("sahayog_product_group_map")
    frappe.cache.delete_value("sahayog_products_map")


def get_sahayog_branches_cached():
    """
    Fetches all Sahayog Branch records, caches them in Redis (using frappe.cache),
    and returns a dictionary mapped by sol_id (name).
    """
    cache_key = "sahayog_branches_map"
    cached_data = frappe.cache.get_value(cache_key)
    
    if cached_data:
        return cached_data
        
    branches = frappe.get_all(
        "Sahayog Branch",
        fields=["name as sol_id", "branch as branch_name", "zone", "region", "district"]
    )
    
    branches_map = {}
    for b in branches:
        sol_id = str(b.sol_id or "")
        branches_map[sol_id] = {
            "sol_id": sol_id,
            "branch_name": b.branch_name or "",
            "zone": b.zone or "",
            "region": b.region or "",
            "district": b.district or ""
        }
        
    # Cache for 24 hours
    frappe.cache.set_value(cache_key, branches_map, expires_in_sec=86400)
    return branches_map


def clear_sahayog_branches_cache(doc=None, method=None):
    """Clears the cached Sahayog Branch map from Redis."""
    frappe.cache.delete_value("sahayog_branches_map")


def clear_user_permissions_cache(doc=None, method=None):
    """Clears the cached report permissions from Redis."""
    get_user_report_permissions.clear_cache()


def clear_targets_cache(doc=None, method=None):
    """Clears the cached targets map from Redis."""
    frappe.cache.delete_keys("targets_map|*")


def clear_branch_category_report_cache(doc=None, method=None):
    """Clears cache related to Branch Category Report."""
    get_last_available_date_for_month.clear_cache()
    get_previous_available_date.clear_cache()


@sahayog_cache(ttl=86400)
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
        branches_map = get_sahayog_branches_cached()
        permissions["sol_data"] = [
            {"sol_id": sid, "branch_name": branches_map[sid]["branch_name"]}
            for sid in permissions["sol_ids"]
            if sid in branches_map
        ]
    
    return permissions


def calculate_category(achievement_pct):
    """Runtime category calculation based on Target vs Achievement %."""
    if achievement_pct >= 100: return "Pinnacle"
    elif achievement_pct >= 80: return "Master"
    elif achievement_pct >= 60: return "Accelerator"
    elif achievement_pct >= 40: return "Starter"
    elif achievement_pct >= 20: return "Learner"
    else: return "Zero Level"


@sahayog_cache(ttl=86400)
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


@sahayog_cache(ttl=86400)
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
            branches_map = get_sahayog_branches_cached()
            # 🛡️ Numeric Matching Logic for Zones
            if perms["zone_ids"]:
                all_zones = set(b["zone"] for b in branches_map.values() if b["zone"])
                if len(perms["zone_ids"]) > 1:
                    zone_pattern = re.compile(f"({'|'.join(re.escape(zid) for zid in perms['zone_ids'])})")
                    matched_zones = [z for z in all_zones if zone_pattern.search(z)]
                    combined_filters["zone"] = ["in", matched_zones] if matched_zones else ["in", ["_NONE_"]]
                else:
                    combined_filters["zone"] = ["like", f"%{perms['zone_ids'][0]}"]
            
            # 🛡️ Numeric Matching Logic for Regions
            if not perms["all_regions"] and perms["region_ids"]:
                all_regions = set(b["region"] for b in branches_map.values() if b["region"])
                if len(perms["region_ids"]) > 1:
                    region_pattern = re.compile(f"({'|'.join(re.escape(rid) for rid in perms['region_ids'])})")
                    matched_regions = [r for r in all_regions if region_pattern.search(r)]
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
    
    # Build sol_id -> district mapping from Sahayog Branch
    branches_map = get_sahayog_branches_cached()
    district_map = {sid: b["district"] or "Unknown District" for sid, b in branches_map.items()}
    
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
    
    zone_wise = build_zone_wise(all_branch_data, targets_map, target_type, district_map)
    product_wise_result, all_products = build_product_wise(all_branch_data, targets_map, target_type, selected_date)
    category_wise = build_category_wise(all_branch_data, targets_map, months, target_type)
    branch_wise = build_branch_wise(all_branch_data, targets_map, months, target_type, district_map)
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
    # Convert lists/tuples to sorted tuples for deterministic cache key
    m_keys_tuple = tuple(sorted(month_keys)) if month_keys else ()
    sol_ids_tuple = tuple(sorted(allowed_sol_ids)) if allowed_sol_ids else ()
    
    cache_key = f"targets_map|{financial_year}|{target_type}|{m_keys_tuple}|{sol_ids_tuple}"
    cached_data = frappe.cache.get_value(cache_key)
    
    if cached_data:
        reconstructed = defaultdict(lambda: defaultdict(float))
        for sol_id, months in cached_data.items():
            for m_key, val in months.items():
                reconstructed[sol_id][m_key] = val
        return reconstructed

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
                
    # Store standard dict in Redis (so lambda doesn't break pickling)
    standard_targets_map = {}
    for sol_id, months in targets_map.items():
        standard_targets_map[sol_id] = dict(months)
    frappe.cache.set_value(cache_key, standard_targets_map, expires_in_sec=86400)
    
    return targets_map


def build_zone_wise(branch_data, targets_map, target_type, district_map=None):
    if district_map is None:
        district_map = {}
    zone_hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"zone": "", "region": "", "district": "", "months": {}})))
    
    for row in branch_data:
        zone = row.get("zone") or "Unknown"
        region = row.get("region") or "Unknown"
        sol_id = str(row.get("sol_id") or "")
        district = district_map.get(sol_id, "Unknown District")
        month_key = row.get("month_key")
        if not month_key: continue
        
        if district not in zone_hierarchy[zone][region]:
            zone_hierarchy[zone][region][district] = {"zone": zone, "region": region, "district": district, "months": {}}
        
        zrd = zone_hierarchy[zone][region][district]["months"]
        if month_key not in zrd:
            zrd[month_key] = {"branches": set(), "target": 0.0, "achievement": 0.0}
        
        ach = float(row.get("achievement") or 0) if target_type == "Monthly" else float(row.get("yearly_achievement") or 0)
        tgt = targets_map[sol_id][month_key]
        
        zrm = zrd[month_key]
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
        zone_total = {"zone": zone, "region": zone, "months": {}, "isZoneTotal": True}
        
        for region in sorted(zone_hierarchy[zone].keys()):
            region_total = {"zone": zone, "region": region, "months": {}, "isZoneTotal": False, "isRegionTotal": True}
            
            for district in sorted(zone_hierarchy[zone][region].keys()):
                dist = zone_hierarchy[zone][region][district]
                for mk, mdata in dist["months"].items():
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
                    
                    if mk not in region_total["months"]:
                        region_total["months"][mk] = {"branches": 0, "target": 0.0, "achievement": 0.0, "percentage": 0.0}
                    rtm = region_total["months"][mk]
                    rtm["branches"] += branch_count
                    rtm["target"] += target
                    rtm["achievement"] += ach
            
            for mk, mdata in region_total["months"].items():
                mdata["percentage"] = round((mdata["achievement"] / mdata["target"]) * 100, 2) if mdata["target"] > 0 else 0.0
            
            for mk, mdata in zone_total["months"].items():
                mdata["percentage"] = round((mdata["achievement"] / mdata["target"]) * 100, 2) if mdata["target"] > 0 else 0.0
        
        zone_wise.append(zone_total)
        for region in sorted(zone_hierarchy[zone].keys()):
            # Add region aggregate row first
            region_total = {"zone": zone, "region": region, "months": {}, "isZoneTotal": False, "isRegionTotal": True}
            for district in sorted(zone_hierarchy[zone][region].keys()):
                dist = zone_hierarchy[zone][region][district]
                for mk, mdata in dist["months"].items():
                    pct = round((mdata["achievement"] / mdata["target"]) * 100, 2) if mdata["target"] > 0 else 0.0
                    mdata["percentage"] = pct
                    
                    if mk not in region_total["months"]:
                        region_total["months"][mk] = {"branches": 0, "target": 0.0, "achievement": 0.0, "percentage": 0.0}
                    rtm = region_total["months"][mk]
                    rtm["branches"] += mdata["branches"]
                    rtm["target"] += mdata["target"]
                    rtm["achievement"] += mdata["achievement"]
            
            for mk, mdata in region_total["months"].items():
                mdata["percentage"] = round((mdata["achievement"] / mdata["target"]) * 100, 2) if mdata["target"] > 0 else 0.0
            
            zone_wise.append(region_total)
            for district in sorted(zone_hierarchy[zone][region].keys()):
                zone_wise.append(zone_hierarchy[zone][region][district])
    
    return zone_wise


def build_product_wise(branch_data, targets_map, target_type, selected_date=None):
    if not selected_date:
        selected_date = frappe.db.get_value("Product Wise Report", {}, "date", order_by="date desc")

    if not selected_date:
        return [], []

    raw_data_db = frappe.db.sql("""
        SELECT
            zone,
            region,
            sol_id,
            product,
            SUM(amount) as amount
        FROM `tabProduct Wise Report`
        WHERE date = %s
        GROUP BY zone, region, sol_id, product
    """, (selected_date,), as_dict=True)

    branches_map = get_sahayog_branches_cached()
    raw_data = []
    
    # We want to group by the resolved values to combine amounts if multiple rows map to the same values
    grouped_map = defaultdict(float)
    
    for row in raw_data_db:
        sid = str(row.sol_id or "").strip()
        b = branches_map.get(sid, {})
        
        zone = b.get("zone") or row.zone or ""
        region = b.get("region") or row.region or ""
        district = b.get("district") or "Unknown District"
        branch_name = b.get("branch_name") or ""
        
        if not zone or not region:
            continue
            
        key = (zone, region, district, sid, branch_name, row.product)
        grouped_map[key] += float(row.amount or 0)
        
    for key, amount in grouped_map.items():
        zone, region, district, sid, branch_name, product = key
        raw_data.append(frappe._dict({
            "zone": zone,
            "region": region,
            "district": district,
            "sol_id": sid,
            "branch_name": branch_name,
            "product": product,
            "amount": amount
        }))
        
    raw_data.sort(key=lambda x: (x.zone, x.region, x.district, x.sol_id))

    if not raw_data:
        return [], []

    all_products = sorted(set(row.product for row in raw_data))

    hierarchy = {}
    for row in raw_data:
        z = row.zone
        r = row.region
        d = row.district
        s = row.sol_id
        bname = row.branch_name
        prod = row.product
        amt = row.amount or 0.0

        if z not in hierarchy:
            hierarchy[z] = {}
        if r not in hierarchy[z]:
            hierarchy[z][r] = {}
        if d not in hierarchy[z][r]:
            hierarchy[z][r][d] = {}
        if s not in hierarchy[z][r][d]:
            hierarchy[z][r][d][s] = {
                "branch_name": bname,
                "products": defaultdict(float),
                "total_amount": 0.0
            }
        hierarchy[z][r][d][s]["products"][prod] += amt
        hierarchy[z][r][d][s]["total_amount"] += amt

    result = []
    for zone in sorted(hierarchy.keys()):
        zone_products = defaultdict(float)
        zone_amount = 0.0
        zone_rows = []

        for region in sorted(hierarchy[zone].keys()):
            region_products = defaultdict(float)
            region_amount = 0.0
            region_rows = []

            for district in sorted(hierarchy[zone][region].keys()):
                district_products = defaultdict(float)
                district_amount = 0.0
                district_rows = []

                for sol_id in sorted(hierarchy[zone][region][district].keys()):
                    sol_info = hierarchy[zone][region][district][sol_id]
                    sol_amt = sol_info["total_amount"]
                    sol_prods = sol_info["products"]

                    district_amount += sol_amt
                    for prod, amt in sol_prods.items():
                        district_products[prod] += amt

                    sol_display_name = f"{sol_id} - {sol_info['branch_name']}" if sol_info['branch_name'] else sol_id
                    district_rows.append({
                        "type": "sol",
                        "name": sol_display_name,
                        "path": f"{zone}/{region}/{district}/{sol_id}",
                        "parent_district": f"{zone}/{region}/{district}",
                        "parent_region": f"{zone}/{region}",
                        "parent_zone": zone,
                        "amount": sol_amt,
                        "products": dict(sol_prods),
                        "is_group": False
                    })

                region_amount += district_amount
                for prod, amt in district_products.items():
                    region_products[prod] += amt

                region_rows.append({
                    "type": "district",
                    "name": district,
                    "path": f"{zone}/{region}/{district}",
                    "parent_region": f"{zone}/{region}",
                    "parent_zone": zone,
                    "amount": district_amount,
                    "products": dict(district_products),
                    "is_group": True,
                    "children": district_rows
                })

            zone_amount += region_amount
            for prod, amt in region_products.items():
                zone_products[prod] += amt

            zone_rows.append({
                "type": "region",
                "name": region,
                "path": f"{zone}/{region}",
                "parent_zone": zone,
                "amount": region_amount,
                "products": dict(region_products),
                "is_group": True,
                "children": region_rows
            })

        result.append({
            "type": "zone",
            "name": zone,
            "path": zone,
            "parent_zone": None,
            "amount": zone_amount,
            "products": dict(zone_products),
            "is_group": True
        })

        for r_row in zone_rows:
            d_rows = r_row.pop("children")
            result.append(r_row)
            for d_row in d_rows:
                s_rows = d_row.pop("children")
                result.append(d_row)
                result.extend(s_rows)

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


def build_branch_wise(branch_data, targets_map, months, target_type, district_map=None):
    if district_map is None:
        district_map = {}
    branch_map = defaultdict(lambda: {"branch": "", "zone": "", "region": "", "district": "", "months": {}})
    
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
            branch_map[sol_id]["district"] = district_map.get(sol_id, "Unknown District")
            
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
            "district": data["district"],
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
@sahayog_cache(ttl=86400)
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
            AND t.maturity_date >= DATE '{ref_date}'
    ),
    tdt_summary AS (
        SELECT acid,
               COALESCE(SUM(tran_amt), 0) AS total_instalment_paid,
               COALESCE(SUM(flow_amt) - SUM(tran_amt), 0) AS pending_amount,
               COUNT(CASE WHEN flow_amt > 0 THEN 1 END) - COUNT(CASE WHEN tran_amt > 0 THEN 1 END) AS pending_instalments
        FROM tbaadm.tdt
        WHERE flow_code = 'NI'
            AND (flow_amt > 0 OR tran_amt > 0)
            AND flow_date <= DATE '{ref_date}'
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
        AND m.last_repayment_date < (DATE '{ref_date}' - INTERVAL '1 year')
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
            branches_map = get_sahayog_branches_cached()
            for sid in sol_ids_found:
                if sid in branches_map:
                    b = branches_map[sid]
                    branch_map[sid] = {
                        "zone": b.get("zone") or "",
                        "region": b.get("region") or "",
                        "district": b.get("district") or "",
                        "branch_name": b.get("branch_name") or ""
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

    branches_map = get_sahayog_branches_cached()
    all_zones = sorted(list(set(b["zone"] for b in branches_map.values() if b["zone"])))
    all_regions = sorted(list(set(b["region"] for b in branches_map.values() if b["region"])))
    all_districts = sorted(list(set(b["district"] for b in branches_map.values() if b["district"])))

    # Apply same permission logic as Drishti (get_sahayog_dashboard)
    if perms.get("is_restricted"):
        allowed_zones = perms.get("zones", [])
        allowed_regions = perms.get("regions", [])
        # If zone permissions exist, use zones as primary filter — ignore sol_ids for data scope
        if allowed_zones:
            # Normalize: uppercase, remove spaces/dashes/hyphens for matching
            allowed_norm = [re.sub(r"[\s\-]+", "", z or "").upper() for z in allowed_zones]
            zones = [z for z in all_zones if re.sub(r"[\s\-]+", "", z or "").upper() in allowed_norm]
            regions = all_regions
            if allowed_regions:
                allowed_reg_norm = [re.sub(r"[\s\-]+", "", r or "").upper() for r in allowed_regions]
                regions = [r for r in all_regions if re.sub(r"[\s\-]+", "", r or "").upper() in allowed_reg_norm]
            districts = all_districts
        elif perms["sol_ids"]:
            # No zone permissions — restrict by sol_ids
            sol_branches = [branches_map[sid] for sid in perms["sol_ids"] if sid in branches_map]
            zones = sorted(list(set(b["zone"] for b in sol_branches if b["zone"])))
            regions = sorted(list(set(b["region"] for b in sol_branches if b["region"])))
            districts = sorted(list(set(b["district"] for b in sol_branches if b["district"])))
        else:
            zones = all_zones
            regions = all_regions
            districts = all_districts

    else:
        # No restrictions — show all
        zones = all_zones
        regions = all_regions
        districts = all_districts

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
    if not sol_data:
        if allowed_sol_ids:
            sol_data = [
                {"sol_id": sid, "branch_name": branches_map[sid]["branch_name"]}
                for sid in sorted(allowed_sol_ids)
                if sid in branches_map
            ]
        else:
            sol_data = [
                {"sol_id": sid, "branch_name": branches_map[sid]["branch_name"]}
                for sid in sorted(branches_map.keys())
            ]
    
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
@sahayog_cache(ttl=86400)
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
        products = get_products_cached()
    except Exception:
        products = []

    product_map = {}
    for p in products:
        code = (p.name or "").strip()
        gname = (p.group_name or "").upper()
        gsub = (p.group_subname or "").upper()
        
        category = None

        if gname == "CASA":
            if gsub == "SA":
                category = "SA"
            elif gsub == "CA":
                category = "CA"
            elif gsub == "TASC":
                category = "TASC"
        elif gname == "RD":
            category = "RD"
        elif gname == "SMBG":
            category = "SMBG"
        elif gname == "DD":
            category = "DD"
        elif gname == "FD":
            category = "FD"

        if category:
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
        sol_ids_found = [str(r[2]).strip() for r in rows] if rows else []
        branch_map = {}
        if sol_ids_found:
            branches_map = get_sahayog_branches_cached()
            for sid in sol_ids_found:
                if sid in branches_map:
                    b = branches_map[sid]
                    branch_map[sid] = {
                        "zone": b.get("zone") or "",
                        "region": b.get("region") or "",
                        "district": b.get("district") or "",
                        "branch_name": b.get("branch_name") or ""
                    }

        # Group and aggregate raw records by branch
        branch_aggregates = {}
        for row in rows:
            schm_code = (row[0] or "").strip()
            sid = str(row[2]).strip()
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
                
            cat = product_map.get(schm_code)
            if not cat:
                code_upper = schm_code.upper()
                if code_upper.startswith("SB"):
                    cat = "SA"
                elif code_upper.startswith("CA"):
                    cat = "CA"
                elif code_upper.startswith("RD"):
                    cat = "RD"
                elif code_upper.startswith("DD"):
                    cat = "DD"
                    
            if cat == "CA":
                branch_aggregates[sid]["ca"] += count
                branch_aggregates[sid]["total"] += count
            elif cat == "SA":
                branch_aggregates[sid]["sa"] += count
                branch_aggregates[sid]["total"] += count
            elif cat == "TASC":
                branch_aggregates[sid]["tasc"] += count
                branch_aggregates[sid]["total"] += count
            elif cat == "RD":
                branch_aggregates[sid]["rd"] += count
                branch_aggregates[sid]["total"] += count
            elif cat == "SMBG":
                branch_aggregates[sid]["smbg"] += count
                branch_aggregates[sid]["total"] += count
            elif cat == "DD":
                branch_aggregates[sid]["dd"] += count
                branch_aggregates[sid]["total"] += count
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


@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_ntb_evr_data(selected_date=None):
    from custom_report.db_connection import get_dr_connection
    from frappe.utils import getdate, get_last_day, add_months
    import datetime

    if not selected_date:
        selected_date = str(datetime.date.today())

    dt = getdate(selected_date)
    report_end = dt
    report_start = dt.replace(day=1)
    prev_month_end = add_months(report_start, -1)
    prev_month_start = prev_month_end.replace(day=1)

    if dt.month >= 4:
        fy_start_year = dt.year
    else:
        fy_start_year = dt.year - 1
    fy_april = f"{fy_start_year}-04-01"

    report_start_str = str(report_start)
    report_end_str = str(report_end)
    opening_start_str = str(prev_month_start)
    opening_end_str = str(prev_month_end)

    query = f"""
    WITH excluded_accts AS (
        SELECT column_value AS account_number
        FROM (VALUES
            ('100110020002993'),
            ('100110020101562'),
            ('100111020003840'),
            ('100144590010496'),
            ('110544207002485')
        ) t(column_value)
    ),
    opening_period AS (
        SELECT
            DATE '{opening_start_str}' AS opening_start_date,
            DATE '{opening_end_str}' AS opening_end_date
    ),
    sol_gl_transferred_accts AS (
        SELECT DISTINCT acid
        FROM tbaadm.htd
        WHERE (tran_particular ILIKE '%Ac xfr from Sol%'
               OR tran_particular ILIKE '%Ac xfr from gl%')
          AND tran_date >= DATE '{report_start_str}'
          AND tran_date <= DATE '{report_end_str}'
    ),
    balance_duration AS (
        SELECT
            gam.acid, gam.foracid, gam.sol_id, s.sol_desc, gam.schm_code,
            gam.acct_name, gam.cif_id, gam.acct_opn_date, gam.acct_cls_flg,
            gam.acct_cls_date, a.relationshipopeningdate AS CIF_ID_Opening_Date,
            eab.tran_date_bal AS balance, eab.tran_date_bal, eab.eod_date, gam.clr_bal_amt,
            EXTRACT(DAY FROM (
                LEAST(
                    CASE WHEN eab.end_eod_date = DATE '2099-12-31' THEN DATE '{report_end_str}' ELSE eab.end_eod_date END,
                    DATE '{report_end_str}'
                ) - GREATEST(eab.eod_date, DATE '{report_start_str}')
            )) + 1 AS active_days
        FROM tbaadm.gam gam
        INNER JOIN tbaadm.eab eab ON gam.acid = eab.acid
        INNER JOIN tbaadm.sol s ON s.sol_id = gam.sol_id
        LEFT JOIN crmuser.accounts a ON a.orgkey = gam.cif_id
        WHERE gam.schm_code IN ('1002','1102','1103','1104','1011')
          AND NOT EXISTS (SELECT 1 FROM excluded_accts x WHERE x.account_number = gam.foracid)
          AND eab.eod_date <= DATE '{report_end_str}'
          AND (CASE WHEN eab.end_eod_date = DATE '2099-12-31' THEN DATE '{report_end_str}' ELSE eab.end_eod_date END) >= DATE '{report_start_str}'
          AND (gam.acct_cls_date IS NULL OR (gam.acct_cls_date >= DATE '{report_start_str}' AND gam.acct_cls_date < DATE '{ref_date}'))
    ),
    weighted_balances AS (
        SELECT bd.*, t.deposit_amount, (bd.balance * bd.active_days) AS weighted_balance
        FROM balance_duration bd
        LEFT JOIN tbaadm.tam t ON bd.acid = t.acid
    ),
    closing_calc_raw AS (
        SELECT wb.foracid, SUM(wb.weighted_balance) AS total_weighted_balance,
            ((DATE '{report_end_str}' - DATE '{report_start_str}') + 1) AS total_days,
            SUM(wb.weighted_balance)::numeric / NULLIF(((DATE '{report_end_str}' - DATE '{report_start_str}') + 1), 0) AS raw_avg
        FROM weighted_balances wb GROUP BY wb.foracid
    ),
    closing_calc AS (
        SELECT foracid, total_weighted_balance, total_days,
            CASE WHEN raw_avg - FLOOR(raw_avg) = 0.5 THEN
                CASE WHEN MOD(FLOOR(raw_avg)::bigint, 2) = 0 THEN FLOOR(raw_avg) ELSE FLOOR(raw_avg) + 1 END
            ELSE ROUND(raw_avg, 0) END AS closing_mab
        FROM closing_calc_raw
    ),
    opening_balance_duration AS (
        SELECT gam.foracid, eab.tran_date_bal,
            EXTRACT(DAY FROM (
                LEAST(
                    CASE WHEN eab.end_eod_date = DATE '2099-12-31' THEN op.opening_end_date ELSE eab.end_eod_date END,
                    op.opening_end_date
                ) - GREATEST(eab.eod_date, op.opening_start_date)
            )) + 1 AS active_days
        FROM tbaadm.gam gam
        JOIN tbaadm.eab eab ON gam.acid = eab.acid
        CROSS JOIN opening_period op
        WHERE gam.schm_code IN ('1002','1102','1103','1104','1011')
          AND NOT EXISTS (SELECT 1 FROM excluded_accts x WHERE x.account_number = gam.foracid)
          AND eab.eod_date <= op.opening_end_date
          AND (CASE WHEN eab.end_eod_date = DATE '2099-12-31' THEN op.opening_end_date ELSE eab.end_eod_date END) >= op.opening_start_date
          AND (gam.acct_cls_date IS NULL OR gam.acct_cls_date >= op.opening_start_date)
    ),
    opening_calc_raw AS (
        SELECT ob.foracid,
            SUM(ob.tran_date_bal * ob.active_days)::numeric / NULLIF((SELECT (opening_end_date - opening_start_date) + 1 FROM opening_period), 0) AS raw_avg
        FROM opening_balance_duration ob GROUP BY ob.foracid
    ),
    opening_mab_calc AS (
        SELECT foracid,
            CASE WHEN raw_avg - FLOOR(raw_avg) = 0.5 THEN
                CASE WHEN MOD(FLOOR(raw_avg)::bigint, 2) = 0 THEN FLOOR(raw_avg) ELSE FLOOR(raw_avg) + 1 END
            ELSE ROUND(raw_avg, 0) END AS opening_mab
        FROM opening_calc_raw
    )
    SELECT
        s.circle_office_name AS zone,
        s.region_name AS region,
        wb.sol_id,
        s.sol_desc AS branch_name,
        wb.schm_code,
        CASE
            WHEN wb.CIF_ID_Opening_Date IS NULL THEN 'NTB'
            WHEN wb.CIF_ID_Opening_Date < DATE '{fy_april}' THEN 'EVR'
            ELSE 'NTB'
        END AS cif_status,
        COUNT(DISTINCT wb.foracid) AS account_count
    FROM weighted_balances wb
    INNER JOIN closing_calc cc ON cc.foracid = wb.foracid
    INNER JOIN tbaadm.sol s ON s.sol_id = wb.sol_id
    LEFT JOIN sol_gl_transferred_accts sgt ON sgt.acid = wb.acid
    LEFT JOIN opening_mab_calc om ON om.foracid = wb.foracid
    LEFT JOIN custom.dsamap dsamap ON dsamap.account_number = wb.foracid
    LEFT JOIN tbaadm.get get ON dsamap.rm_id = get.emp_id
    GROUP BY s.circle_office_name, s.region_name, wb.sol_id, s.sol_desc, wb.schm_code, cif_status
    ORDER BY s.circle_office_name, s.region_name, wb.sol_id, wb.schm_code, cif_status
    """

    conn = get_dr_connection()
    if not conn:
        frappe.log_error("Failed to connect to DR database", "NTB EVR API")
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        branch_map = {}
        for row in rows:
            raw_zone = row[0] or "Unknown"
            region = row[1] or "Unknown"
            sol_id = str(row[2]) if row[2] else ""
            branch_name = row[3] or sol_id
            schema = row[4] or ""
            status = row[5] or ""
            count = int(row[6]) if row[6] else 0

            normalized_zone = re.sub(r"[\s\-]+", "", raw_zone).upper()
            # Extract number from zone name for display
            zone_num = re.sub(r"[^0-9]", "", normalized_zone)
            display_zone = f"ZONE-{zone_num}" if zone_num else normalized_zone

            normalized_region = re.sub(r"[\s\-]+", "", region).upper()
            # Fix common typos like RIGION -> REGION
            normalized_region = normalized_region.replace("RIGION", "REGION")
            # Extract number from region name for display
            region_num = re.sub(r"[^0-9]", "", normalized_region)
            display_region = f"REGION-{region_num}" if region_num else normalized_region

            if sol_id not in branch_map:
                branch_map[sol_id] = {
                    "zone": display_zone, "region": display_region, "sol_id": sol_id,
                    "branch_name": branch_name, "ntb": 0, "evr": 0
                }
            if status == "NTB":
                branch_map[sol_id]["ntb"] += count
            elif status == "EVR":
                branch_map[sol_id]["evr"] += count

        result = list(branch_map.values())
        result.sort(key=lambda x: (x["zone"], x["region"], x["sol_id"]))
        return {"total_rows": len(rows), "data": result}

    except Exception as e:
        frappe.log_error(f"Error executing NTB EVR query: {str(e)}", "NTB EVR API")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_cust_wise_avg_balance(selected_date=None, limit=500, offset=0):
    from custom_report.db_connection import get_dr_connection
    from frappe.utils import getdate, add_months
    import datetime

    limit = int(limit)
    offset = int(offset)

    if not selected_date:
        selected_date = str(datetime.date.today())

    dt = getdate(selected_date)
    report_end = dt
    report_start = dt.replace(day=1)
    prev_month_end = add_months(report_start, -1)
    prev_month_start = prev_month_end.replace(day=1)

    report_start_str = str(report_start)
    report_end_str = str(report_end)
    opening_start_str = str(prev_month_start)
    opening_end_str = str(prev_month_end)

    if dt.month >= 4:
        fy_start_year = dt.year
    else:
        fy_start_year = dt.year - 1
    fy_april_str = f"{fy_start_year}-04-01"

    query = f"""
    WITH excluded_accts AS (
        SELECT column_value AS account_number
        FROM (VALUES
            ('100110020002993'),
            ('100110020101562'),
            ('100111020003840'),
            ('100144590010496'),
            ('110544207002485')
        ) t(column_value)
    ),
    opening_period AS (
        SELECT
            DATE '{opening_start_str}' AS opening_start_date,
            DATE '{opening_end_str}' AS opening_end_date
    ),
    sol_gl_transferred_accts AS (
        SELECT DISTINCT acid
        FROM tbaadm.htd
        WHERE (tran_particular ILIKE '%Ac xfr from Sol%'
               OR tran_particular ILIKE '%Ac xfr from gl%')
          AND tran_date >= DATE '{report_start_str}'
          AND tran_date <= DATE '{report_end_str}'
    ),
    balance_duration AS (
        SELECT
            gam.acid, gam.foracid, gam.sol_id, s.sol_desc, gam.schm_code,
            gam.acct_name, gam.cif_id, gam.acct_opn_date, gam.acct_cls_flg,
            gam.acct_cls_date, a.relationshipopeningdate AS CIF_ID_Opening_Date,
            eab.tran_date_bal AS balance, eab.tran_date_bal, eab.eod_date, gam.clr_bal_amt,
            EXTRACT(DAY FROM (
                LEAST(
                    CASE WHEN eab.end_eod_date = DATE '2099-12-31' THEN DATE '{report_end_str}' ELSE eab.end_eod_date END,
                    DATE '{report_end_str}'
                ) - GREATEST(eab.eod_date, DATE '{report_start_str}')
            )) + 1 AS active_days
        FROM tbaadm.gam gam
        INNER JOIN tbaadm.eab eab ON gam.acid = eab.acid
        INNER JOIN tbaadm.sol s ON s.sol_id = gam.sol_id
        LEFT JOIN crmuser.accounts a ON a.orgkey = gam.cif_id
        WHERE gam.schm_code IN ('1002','1102','1103','1104','1011')
          AND NOT EXISTS (SELECT 1 FROM excluded_accts x WHERE x.account_number = gam.foracid)
          AND eab.eod_date <= DATE '{report_end_str}'
          AND (CASE WHEN eab.end_eod_date = DATE '2099-12-31' THEN DATE '{report_end_str}' ELSE eab.end_eod_date END) >= DATE '{report_start_str}'
          AND (gam.acct_cls_date IS NULL OR (gam.acct_cls_date >= DATE '{report_start_str}' AND gam.acct_cls_date < DATE '{ref_date}'))
    ),
    weighted_balances AS (
        SELECT bd.*, t.deposit_amount, (bd.balance * bd.active_days) AS weighted_balance
        FROM balance_duration bd
        LEFT JOIN tbaadm.tam t ON bd.acid = t.acid
    ),
    closing_calc_raw AS (
        SELECT wb.foracid, SUM(wb.weighted_balance) AS total_weighted_balance,
            ((DATE '{report_end_str}' - DATE '{report_start_str}') + 1) AS total_days,
            SUM(wb.weighted_balance)::numeric / NULLIF(((DATE '{report_end_str}' - DATE '{report_start_str}') + 1), 0) AS raw_avg
        FROM weighted_balances wb GROUP BY wb.foracid
    ),
    closing_calc AS (
        SELECT foracid, total_weighted_balance, total_days,
            CASE WHEN raw_avg - FLOOR(raw_avg) = 0.5 THEN
                CASE WHEN MOD(FLOOR(raw_avg)::bigint, 2) = 0 THEN FLOOR(raw_avg) ELSE FLOOR(raw_avg) + 1 END
            ELSE ROUND(raw_avg, 0) END AS closing_mab
        FROM closing_calc_raw
    ),
    opening_balance_duration AS (
        SELECT gam.foracid, eab.tran_date_bal,
            EXTRACT(DAY FROM (
                LEAST(
                    CASE WHEN eab.end_eod_date = DATE '2099-12-31' THEN op.opening_end_date ELSE eab.end_eod_date END,
                    op.opening_end_date
                ) - GREATEST(eab.eod_date, op.opening_start_date)
            )) + 1 AS active_days
        FROM tbaadm.gam gam
        JOIN tbaadm.eab eab ON gam.acid = eab.acid
        CROSS JOIN opening_period op
        WHERE gam.schm_code IN ('1002','1102','1103','1104','1011')
          AND NOT EXISTS (SELECT 1 FROM excluded_accts x WHERE x.account_number = gam.foracid)
          AND eab.eod_date <= op.opening_end_date
          AND (CASE WHEN eab.end_eod_date = DATE '2099-12-31' THEN op.opening_end_date ELSE eab.end_eod_date END) >= op.opening_start_date
          AND (gam.acct_cls_date IS NULL OR gam.acct_cls_date >= op.opening_start_date)
    ),
    opening_calc_raw AS (
        SELECT ob.foracid,
            SUM(ob.tran_date_bal * ob.active_days)::numeric / NULLIF((SELECT (opening_end_date - opening_start_date) + 1 FROM opening_period), 0) AS raw_avg
        FROM opening_balance_duration ob GROUP BY ob.foracid
    ),
    opening_mab_calc AS (
        SELECT foracid,
            CASE WHEN raw_avg - FLOOR(raw_avg) = 0.5 THEN
                CASE WHEN MOD(FLOOR(raw_avg)::bigint, 2) = 0 THEN FLOOR(raw_avg) ELSE FLOOR(raw_avg) + 1 END
            ELSE ROUND(raw_avg, 0) END AS opening_mab
        FROM opening_calc_raw
    )
    SELECT
        wb.foracid,
        wb.sol_id,
        wb.sol_desc,
        wb.schm_code,
        wb.acct_name,
        wb.cif_id,
        wb.acct_opn_date,
        wb.acct_cls_flg,
        wb.acct_cls_date,
        wb.CIF_ID_Opening_Date,
        CASE
            WHEN wb.CIF_ID_Opening_Date IS NULL THEN 'NTB'
            WHEN wb.CIF_ID_Opening_Date < DATE '{fy_april_str}' THEN 'EVR'
            ELSE 'NTB'
        END AS cif_status,
        (ARRAY_AGG(wb.tran_date_bal ORDER BY wb.eod_date DESC))[1] AS tran_date_bal,
        wb.clr_bal_amt,
        wb.deposit_amount,
        cc.total_weighted_balance,
        cc.total_days,
        cc.closing_mab AS average_balance,
        cc.closing_mab,
        CASE
            WHEN sgt.acid IS NOT NULL THEN 0
            ELSE COALESCE(om.opening_mab, 0)
        END AS opening_mab,
        cc.closing_mab - CASE
                              WHEN sgt.acid IS NOT NULL THEN 0
                              ELSE COALESCE(om.opening_mab, 0)
                          END AS inc_mab,
        CASE
            WHEN wb.schm_code = '1102' AND cc.closing_mab >= 2000 THEN 'MAB'
            WHEN wb.schm_code IN ('1002','1011') AND cc.closing_mab >= 1000 THEN 'MAB'
            WHEN wb.schm_code IN ('1103','1104') AND cc.closing_mab >= 4000 THEN 'MAB'
            WHEN DATE_TRUNC('month', wb.acct_opn_date) = DATE_TRUNC('month', DATE '{report_start_str}')
                 AND (
                        (wb.schm_code = '1102' AND wb.clr_bal_amt >= 2000)
                     OR (wb.schm_code IN ('1002','1011') AND wb.clr_bal_amt >= 1000)
                     OR (wb.schm_code IN ('1103','1104') AND wb.clr_bal_amt >= 4000)
                     )
                THEN 'MAB'
            ELSE 'NMAB'
        END AS STATUS,
        CASE WHEN sgt.acid IS NOT NULL THEN 'Y' ELSE 'N' END AS sol_gl_transferred_flag,
        dsamap.rm_id,
        get.emp_name,
        s.division_name,
        s.region_name,
        s.circle_office_name
    FROM weighted_balances wb
    INNER JOIN closing_calc cc ON cc.foracid = wb.foracid
    LEFT JOIN custom.dsamap dsamap ON dsamap.account_number = wb.foracid
    LEFT JOIN tbaadm.get get ON dsamap.rm_id = get.emp_id
    INNER JOIN tbaadm.sol s ON s.sol_id = wb.sol_id
    LEFT JOIN opening_mab_calc om ON om.foracid = wb.foracid
    LEFT JOIN sol_gl_transferred_accts sgt ON sgt.acid = wb.acid
    GROUP BY
        wb.foracid, wb.sol_id, wb.sol_desc, wb.schm_code, wb.acct_name, wb.cif_id,
        wb.acct_opn_date, wb.acct_cls_flg, wb.acct_cls_date, wb.CIF_ID_Opening_Date,
        wb.clr_bal_amt, wb.deposit_amount, cc.total_weighted_balance, cc.total_days, cc.closing_mab,
        dsamap.rm_id, get.emp_id, get.emp_name,
        s.division_name, s.region_name, s.circle_office_name, om.opening_mab, sgt.acid
    ORDER BY s.circle_office_name, s.region_name, wb.sol_id
    """

    count_query = f"SELECT COUNT(*) FROM ({query}) sub"
    paginated_query = f"{query} LIMIT {limit} OFFSET {offset}"

    conn = get_dr_connection()
    if not conn:
        frappe.log_error("Failed to connect to DR database", "Cust Wise AVG Balance API")
        return {"total_rows": 0, "data": []}

    try:
        cursor = conn.cursor()
        cursor.execute(count_query)
        total_rows = cursor.fetchone()[0]

        cursor.execute(paginated_query)
        rows = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]

        result = []
        for row in rows:
            row_dict = {}
            for i, val in enumerate(row):
                col = headers[i]
                if val is None:
                    row_dict[col] = None
                elif isinstance(val, (int, float)):
                    row_dict[col] = val
                elif hasattr(val, 'isoformat'):
                    row_dict[col] = str(val)[:10]
                else:
                    row_dict[col] = str(val)
            result.append(row_dict)

        return {"total_rows": total_rows, "data": result}

    except Exception as e:
        frappe.log_error(f"Error executing Cust Wise AVG Balance query: {str(e)}", "Cust Wise AVG Balance API")
        return {"total_rows": 0, "data": []}
    finally:
        try:
            conn.close()
        except Exception:
            pass

def clean_zone_region(value, prefix):
    if not value:
        return "Unknown"
    
    value_str = str(value).strip().upper()
    
    # Extract all digits
    import re
    digits = re.sub(r"[^0-9]", "", value_str)
    
    if digits:
        return f"{prefix}-{digits}"
    else:
        # If no digits, clean spaces and return uppercase
        normalized = re.sub(r"[\s\-]+", " ", value_str).strip()
        return normalized


@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_product_wise_casa(selected_date=None):
    from custom_report.db_connection import get_dr_connection
    from frappe.utils import getdate
    import datetime

    # Validate that selected_date is not today or in the future
    if not selected_date:
        selected_date = str(datetime.date.today() - datetime.timedelta(days=1))
    
    dt = getdate(selected_date)
    today = datetime.date.today()
    if dt >= today:
        frappe.throw("Today's date and future dates cannot be selected. Please select a past date.")

    # Calculate dynamic dates
    report_start = dt.replace(day=1)
    report_start_str = report_start.strftime("%Y-%m-%d")
    report_end = dt
    report_end_str = report_end.strftime("%Y-%m-%d")
    
    # Last month dates:
    prev_month_end = dt.replace(day=1) - datetime.timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    
    opening_start_str = prev_month_start.strftime("%Y-%m-%d")
    opening_end_str = prev_month_end.strftime("%Y-%m-%d")
    
    # Financial year start (April 1st)
    if dt.month >= 4:
        fy_start_year = dt.year
    else:
        fy_start_year = dt.year - 1
    fy_april = f"{fy_start_year}-04-01"

    report_start_str = str(report_start)
    report_end_str = str(report_end)
    opening_start_str = str(prev_month_start)
    opening_end_str = str(prev_month_end)
    fy_april_str = f"{fy_start_year}-04-01"

    print(f"CASA Sync - Selected Date: {selected_date}", flush=True)
    print(f"CASA Sync - Report Month Start Date: {report_start_str}", flush=True)
    print(f"CASA Sync - Report Month End Date: {report_end_str}", flush=True)
    print(f"CASA Sync - Last Month Start Date: {opening_start_str}", flush=True)
    print(f"CASA Sync - Last Month End Date: {opening_end_str}", flush=True)
    print(f"CASA Sync - Financial Year Start: {fy_april_str}", flush=True)

    query = f'''
WITH excluded_accts AS (
    SELECT column_value AS account_number
    FROM (VALUES
        ('100110020002993'),
        ('100110020101562'),
        ('100111020003840'),
        ('100144590010496'),
        ('110544207002485')
    ) t(column_value)
),
/* ===================== OPENING (PREVIOUS) MONTH DATE RANGE ===================== */
opening_period AS (
    SELECT
        DATE '{opening_start_str}' AS opening_start_date,  ---LAST MONTH START DATE 
        DATE '{opening_end_str}' AS opening_end_date     ---LAST MONTH END DATE
),
/* ===================== ACCOUNTS WITH SOL/GL TRANSFER IN CURRENT PERIOD ===================== */
sol_gl_transferred_accts AS (
    SELECT DISTINCT acid
    FROM tbaadm.htd
    WHERE (tran_particular ILIKE '%Ac xfr from Sol%'
           OR tran_particular ILIKE '%Ac xfr from gl%')
      AND tran_date >= DATE '{report_start_str}'   ---REPORT MONTH START DATE
      AND tran_date <= DATE '{report_end_str}'   ---REPORT MONTH END DATE
),
/* ===================== CLOSING (CURRENT) PERIOD ===================== */
balance_duration AS (
    SELECT
        gam.acid,
        gam.foracid,
        gam.sol_id,
        s.sol_desc,
        gam.schm_code,
        gam.acct_name,
        gam.cif_id,
        gam.acct_opn_date,
        gam.acct_cls_flg,
        gam.acct_cls_date,
        a.relationshipopeningdate AS CIF_ID_Opening_Date,
        eab.tran_date_bal AS balance,
        eab.tran_date_bal,
        eab.eod_date,
        gam.clr_bal_amt,
        EXTRACT(
            DAY FROM (
                LEAST(
                    CASE
                        WHEN eab.end_eod_date = DATE '2099-12-31'
                            THEN DATE '{report_end_str}'   ---REPORT MONTH END DATE
                        ELSE eab.end_eod_date
                    END,
                    DATE '{report_end_str}'   ---REPORT MONTH END DATE
                )
                -
                GREATEST(eab.eod_date, DATE '{report_start_str}')   ---REPORT MONTH START DATE
            )
        ) + 1 AS active_days
    FROM
        tbaadm.gam gam
    INNER JOIN
        tbaadm.eab eab ON gam.acid = eab.acid
    INNER JOIN
        tbaadm.sol s ON s.sol_id = gam.sol_id
    LEFT JOIN
        crmuser.accounts a ON a.orgkey = gam.cif_id
    WHERE
        gam.schm_code IN ('1002','1102','1103','1104','1011')
        AND NOT EXISTS (
            SELECT 1 FROM excluded_accts x
            WHERE x.account_number = gam.foracid
        )
        AND eab.eod_date <= DATE '{report_end_str}'   ---REPORT MONTH END DATE
        AND (
            CASE
                WHEN eab.end_eod_date = DATE '2099-12-31'  ---FIXED DATE NO CHANGE
                    THEN DATE '{report_end_str}'  ---REPORT MONTH END DATE
                ELSE eab.end_eod_date
            END
        ) >= DATE '{report_start_str}'   ---REPORT MONTH START DATE
        AND (
            gam.acct_cls_date IS NULL
            OR (
                gam.acct_cls_date >= DATE '{report_start_str}'   ---REPORT MONTH START DATE
                AND gam.acct_cls_date < DATE '{ref_date}'
            )
        )
),
weighted_balances AS (
    SELECT
        bd.*,
        t.deposit_amount,
        (bd.balance * bd.active_days) AS weighted_balance
    FROM balance_duration bd
    LEFT JOIN tbaadm.tam t ON bd.acid = t.acid
),
/* ===================== CLOSING MAB — RAW SUM PER FORACID ===================== */
closing_calc_raw AS (
    SELECT
        wb.foracid,
        SUM(wb.weighted_balance) AS total_weighted_balance,
        ((DATE '{report_end_str}' - DATE '{report_start_str}') + 1) AS total_days,    ---REPORT MONTH START & END DATE
        SUM(wb.weighted_balance)::numeric
            / NULLIF(((DATE '{report_end_str}' - DATE '{report_start_str}') + 1), 0) AS raw_avg   ---REPORT MONTH START & END DATE
    FROM weighted_balances wb
    GROUP BY wb.foracid
),
/* ===================== CLOSING MAB — BANKER'S ROUNDING APPLIED ===================== */
closing_calc AS (
    SELECT
        foracid,
        total_weighted_balance,
        total_days,
        CASE
            WHEN raw_avg - FLOOR(raw_avg) = 0.5 THEN
                CASE
                    WHEN MOD(FLOOR(raw_avg)::bigint, 2) = 0 THEN FLOOR(raw_avg)
                    ELSE FLOOR(raw_avg) + 1
                END
            ELSE ROUND(raw_avg, 0)
        END AS closing_mab
    FROM closing_calc_raw
),
/* ===================== OPENING MONTH MAB ===================== */
opening_balance_duration AS (
    SELECT
        gam.foracid,
        eab.tran_date_bal,
        EXTRACT(
            DAY FROM (
                LEAST(
                    CASE
                        WHEN eab.end_eod_date = DATE '2099-12-31' ---FIXED DATE NO CHANGE
                            THEN op.opening_end_date
                        ELSE eab.end_eod_date
                    END,
                    op.opening_end_date
                )
                -
                GREATEST(eab.eod_date, op.opening_start_date)
            )
        ) + 1 AS active_days
    FROM tbaadm.gam gam
    JOIN tbaadm.eab eab ON gam.acid = eab.acid
    CROSS JOIN opening_period op
    WHERE
        gam.schm_code IN ('1002','1102','1103','1104','1011')
        AND NOT EXISTS (
            SELECT 1 FROM excluded_accts x
            WHERE x.account_number = gam.foracid
        )
        AND eab.eod_date <= op.opening_end_date
        AND (
            CASE
                WHEN eab.end_eod_date = DATE '2099-12-31'  ---FIXED DATE NO CHANGE
                    THEN op.opening_end_date
                ELSE eab.end_eod_date
            END
        ) >= op.opening_start_date
        AND (
            gam.acct_cls_date IS NULL
            OR gam.acct_cls_date >= op.opening_start_date
        )
),
/* ===================== OPENING MAB — RAW SUM PER FORACID ===================== */
opening_calc_raw AS (
    SELECT
        ob.foracid,
        SUM(ob.tran_date_bal * ob.active_days)::numeric
            / NULLIF((SELECT (opening_end_date - opening_start_date) + 1 FROM opening_period), 0) AS raw_avg
    FROM opening_balance_duration ob
    GROUP BY ob.foracid
),
/* ===================== OPENING MAB — BANKER'S ROUNDING APPLIED ===================== */
opening_mab_calc AS (
    SELECT
        foracid,
        CASE
            WHEN raw_avg - FLOOR(raw_avg) = 0.5 THEN
                CASE
                    WHEN MOD(FLOOR(raw_avg)::bigint, 2) = 0 THEN FLOOR(raw_avg)
                    ELSE FLOOR(raw_avg) + 1
                END
            ELSE ROUND(raw_avg, 0)
        END AS opening_mab
    FROM opening_calc_raw
)
/* ===================== FINAL OUTPUT ===================== */
SELECT
    wb.foracid,
    wb.sol_id,
    wb.sol_desc,
    wb.schm_code,
    wb.acct_name,
    wb.cif_id,
    wb.acct_opn_date,
    wb.acct_cls_flg,
    wb.acct_cls_date,
    wb.CIF_ID_Opening_Date,
    CASE
        WHEN wb.CIF_ID_Opening_Date IS NULL THEN 'NTB'
        WHEN wb.CIF_ID_Opening_Date < DATE '{fy_april_str}'   ---YE EVERY FINACIAL YEAR ME CHANGE HOGI NEXT YEAR '2027-04-01' HO JAYEGI
        THEN 'EVR'
        ELSE 'NTB'
    END AS cif_status,
    (ARRAY_AGG(wb.tran_date_bal ORDER BY wb.eod_date DESC))[1] AS tran_date_bal,
    wb.clr_bal_amt,
    wb.deposit_amount,
    cc.total_weighted_balance,
    cc.total_days,
    cc.closing_mab AS average_balance,
    cc.closing_mab,
    -- opening_mab: force 0 for SOL/GL transferred accounts, else banker's-rounded value
    CASE
        WHEN sgt.acid IS NOT NULL THEN 0
        ELSE COALESCE(om.opening_mab, 0)
    END AS opening_mab,
    cc.closing_mab - CASE
                          WHEN sgt.acid IS NOT NULL THEN 0
                          ELSE COALESCE(om.opening_mab, 0)
                      END AS inc_mab,
    CASE
        WHEN wb.schm_code = '1102' AND cc.closing_mab >= 2000 THEN 'MAB'
        WHEN wb.schm_code IN ('1002','1011') AND cc.closing_mab >= 1000 THEN 'MAB'
        WHEN wb.schm_code IN ('1103','1104') AND cc.closing_mab >= 4000 THEN 'MAB'
        WHEN DATE_TRUNC('month', wb.acct_opn_date) = DATE_TRUNC('month', DATE '{report_start_str}')
             AND (
                    (wb.schm_code = '1102' AND wb.clr_bal_amt >= 2000)
                 OR (wb.schm_code IN ('1002','1011') AND wb.clr_bal_amt >= 1000)
                 OR (wb.schm_code IN ('1103','1104') AND wb.clr_bal_amt >= 4000)
                 )
            THEN 'MAB'
        ELSE 'NMAB'
    END AS STATUS,
    CASE WHEN sgt.acid IS NOT NULL THEN 'Y' ELSE 'N' END AS sol_gl_transferred_flag,
    dsamap.rm_id,
    get.emp_name,
    s.division_name,
    s.region_name,
    s.circle_office_name
FROM
    weighted_balances wb
INNER JOIN closing_calc cc ON cc.foracid = wb.foracid
LEFT JOIN custom.dsamap dsamap ON dsamap.account_number = wb.foracid
LEFT JOIN tbaadm.get get ON dsamap.rm_id = get.emp_id
INNER JOIN tbaadm.sol s ON s.sol_id = wb.sol_id
LEFT JOIN opening_mab_calc om ON om.foracid = wb.foracid
LEFT JOIN sol_gl_transferred_accts sgt ON sgt.acid = wb.acid
GROUP BY
    wb.foracid, wb.sol_id, wb.sol_desc, wb.schm_code, wb.acct_name, wb.cif_id,
    wb.acct_opn_date, wb.acct_cls_flg, wb.acct_cls_date, wb.CIF_ID_Opening_Date,
    wb.clr_bal_amt, wb.deposit_amount, cc.total_weighted_balance, cc.total_days, cc.closing_mab,
    dsamap.rm_id, get.emp_id, get.emp_name,
    s.division_name, s.region_name, s.circle_office_name, om.opening_mab, sgt.acid;'''

    conn = get_dr_connection()
    if not conn:
        frappe.throw("Failed to connect to DR database. Please check your Finacle DR DB credentials.")

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"CASA Sync - Total rows fetched from DB: {len(rows)}", flush=True)
        
        from frappe.utils import now_datetime

        processed_date = dt.strftime("%Y-%m-%d")
        now_time = now_datetime()
        bulk_data = []
        
        # Pre-fetch product group_name mappings from DB to emulate Fetch From
        product_map = get_product_group_map_cached()

        for row in rows:
            sol_id = str(row[1]).strip()
            schm_code = str(row[3]).strip()
            inc_mab = float(row[19] or 0)
            
            final_zone = clean_zone_region(row[26] or row[24], "ZONE")
            final_region = clean_zone_region(row[25], "REGION")
            
            product_group = product_map.get(schm_code)
            
            name = frappe.generate_hash(length=16)
            bulk_data.append((
                name,
                now_time,
                now_time,
                "Administrator",
                "Administrator",
                0,
                0,
                final_zone,
                final_region,
                product_group or "CASA",
                inc_mab,
                processed_date,
                sol_id,
                schm_code
            ))

        # Deleting old records for this date and CASA products to prevent duplicates
        frappe.db.delete("Product Wise Report", {
            "date": processed_date,
            "product": "CASA"
        })

        print(f"CASA Sync - Starting bulk insertion of {len(bulk_data)} records into Product Wise Report...", flush=True)
        
        fields = [
            "name", "creation", "modified", "modified_by", "owner", 
            "docstatus", "idx", "zone", "region", "product", "amount", 
            "date", "sol_id", "scheme_code"
        ]
        
        frappe.db.bulk_insert("Product Wise Report", fields, bulk_data)
        frappe.db.commit()
        
        print(f"CASA Sync - Successfully synced and committed {len(bulk_data)} records.", flush=True)
        return len(bulk_data)
        
    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Product Wise CASA Sync Failed")
        raise e
    finally:
        try:
            conn.close()
        except Exception:
            pass



@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_product_wise_tda(selected_date=None):
    from custom_report.db_connection import get_dr_connection
    from frappe.utils import getdate, now_datetime
    import datetime

    # Validate that selected_date is not today or in the future
    if not selected_date:
        selected_date = str(datetime.date.today() - datetime.timedelta(days=1))
    
    dt = getdate(selected_date)
    today = datetime.date.today()
    if dt >= today:
        frappe.throw("Today's date and future dates cannot be selected. Please select a past date.")

    # Calculate dynamic dates
    report_start = dt.replace(day=1)
    report_start_str = report_start.strftime("%Y-%m-%d")
    report_end = dt
    report_end_str = report_end.strftime("%Y-%m-%d")
    processed_date = report_end_str
    
    # Last month dates:
    prev_month_end = dt.replace(day=1) - datetime.timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    
    opening_start_str = prev_month_start.strftime("%Y-%m-%d")
    opening_end_str = prev_month_end.strftime("%Y-%m-%d")
    
    total_days_till_date = (dt - dt.replace(day=1)).days + 1
    last_month_total_days = prev_month_end.day

    print(f"TDA Sync - Selected Date: {selected_date}", flush=True)
    print(f"TDA Sync - Report Month Start Date: {report_start_str}", flush=True)
    print(f"TDA Sync - Report Month End Date: {report_end_str}", flush=True)
    print(f"TDA Sync - Last Month Start Date: {opening_start_str}", flush=True)
    print(f"TDA Sync - Last Month End Date: {opening_end_str}", flush=True)
    print(f"TDA Sync - Total days till date: {total_days_till_date}", flush=True)
    print(f"TDA Sync - Last month total days: {last_month_total_days}", flush=True)

    query = f'''WITH excluded_accts AS (
    SELECT column_value AS account_number
    FROM (VALUES
        ('100110020002993'),
        ('100110020101562'),
        ('100111020003840'),
        ('100144590010496'),
        ('110544207002485')
    ) t(column_value)
),
/* ================= FLOW DATA (SCHM_CODE LEVEL) ================= */
flow_data AS (
    SELECT
        g.sol_id,
        g.schm_code,
        s.sol_desc,
        s.region_name,
        s.division_name,
        s.circle_office_name,
        SUM(tdt.flow_amt) AS total_flow_amount
    FROM custom.dsamap d
    INNER JOIN tbaadm.gam g
        ON g.foracid = d.account_number
       AND g.schm_type = 'TDA'
    INNER JOIN tbaadm.sol s
        ON s.sol_id = g.sol_id
    INNER JOIN tbaadm.tdt tdt
        ON tdt.acid = g.acid
       AND tdt.flow_code IN ('PI','NI')
    WHERE tdt.flow_date BETWEEN DATE '{report_start_str}' AND DATE '{report_end_str}'  ---REPORT MONTH START & END DATE
      -- ✅ FIX: FD scheme codes ke closed accounts exclude karo
      --         Agar account FD scheme ka hai AUR closed hai toh mat lo
      AND NOT (
                g.schm_code IN ('2001','2002','2003','2008','2009',
        '2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030','2031','2032','2033',
        '2101','2102','2103','2104','2105','2106',
        '2201','2202','2203')
                AND g.acct_cls_flg != 'N'
              )
    GROUP BY
        g.sol_id,
        g.schm_code,
        s.sol_desc,
        s.region_name,
        s.division_name,
        s.circle_office_name
),
/* ================= TRAN DATA (SCHM_CODE LEVEL) ================= */
tran_data AS (
    SELECT
        g.sol_id,
        g.schm_code,
        SUM(dtt.tran_amt) AS total_tran_amt
    FROM custom.dsamap d
    INNER JOIN tbaadm.gam g
        ON g.foracid = d.account_number
       AND g.schm_type = 'TDA'
    INNER JOIN tbaadm.dtt dtt
        ON dtt.acid = g.acid
       AND dtt.flow_code IN ('PI','NI')
    WHERE dtt.value_date BETWEEN DATE '{report_start_str}' AND DATE '{report_end_str}'   ---REPORT MONTH START & END DATE
      -- ✅ FIX: FD scheme codes ke closed accounts exclude karo
      --         Agar account FD scheme ka hai AUR closed hai toh mat lo
      AND NOT (
                g.schm_code IN ('2001','2002','2003','2008','2009',
        '2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030','2031','2032','2033',
        '2101','2102','2103','2104','2105','2106',
        '2201','2202','2203')
                AND g.acct_cls_flg != 'N'
              )
    GROUP BY
        g.sol_id,
        g.schm_code
),
/* ================= NEW: TRAN DATA FOR SCHM_CODE '1007' (HTD TABLE) ================= */
tran_data_1007 AS (
    SELECT
        g.sol_id,
        '1007' AS schm_code,
        SUM(h.tran_amt) AS total_tran_amt
    FROM tbaadm.htd h
    JOIN tbaadm.gam g
        ON g.acid = h.acid
    WHERE h.tran_date BETWEEN DATE '{report_start_str}' AND DATE '{report_end_str}'  ---REPORT MONTH START & END DATE
      AND g.schm_code = '1007'
      AND h.part_tran_type = 'C'
      AND h.tran_sub_type = 'CI'
    GROUP BY g.sol_id
),
/* ================= FINAL DATA ================= */
final_data AS (
    SELECT
        COALESCE(f.sol_id, t.sol_id) AS sol_id,
        COALESCE(f.schm_code, t.schm_code) AS schm_code,
        COALESCE(f.sol_desc, s.sol_desc) AS sol_desc,
        COALESCE(f.region_name, s.region_name) AS region_name,
        COALESCE(f.division_name, s.division_name) AS division_name,
        COALESCE(f.circle_office_name, s.circle_office_name) AS circle_office_name,
        COALESCE(f.total_flow_amount, 0) AS total_flow_amount,
        COALESCE(t.total_tran_amt, 0) AS total_tran_amt
    FROM flow_data f
    FULL OUTER JOIN tran_data t
        ON f.sol_id = t.sol_id
       AND f.schm_code = t.schm_code
    LEFT JOIN tbaadm.sol s
        ON s.sol_id = COALESCE(f.sol_id, t.sol_id)
    UNION ALL
    -- ✅ NEW: schm_code '1007' ka data yaha merge kiya gaya hai (flow_amount hamesha 0 rahega,
    --         kyunki 1007 ke liye sirf tran_amt ka logic diya gaya hai)
    SELECT
        t7.sol_id,
        t7.schm_code,
        s.sol_desc,
        s.region_name,
        s.division_name,
        s.circle_office_name,
        0 AS total_flow_amount,
        t7.total_tran_amt
    FROM tran_data_1007 t7
    LEFT JOIN tbaadm.sol s
        ON s.sol_id = t7.sol_id
),
/* ================= JUNE DATA (SCHM_CODE LEVEL) ================= */
june_data AS (
    SELECT
        g.sol_id,
        g.schm_code,
        e.tran_date_bal,
        (
            EXTRACT(
                DAY FROM (
                    LEAST(
                        CASE
                            WHEN e.end_eod_date = DATE '2099-12-31'
                                THEN DATE '{report_end_str}'   ---REPORT MONTH END DATE
                            ELSE e.end_eod_date
                        END,
                        DATE '{report_end_str}'  ---REPORT MONTH END DATE
                    )
                    -
                    GREATEST(e.eod_date, DATE '{report_start_str}') ---REPORT MONTH START DATE
                )
            ) + 1
        ) AS active_days
    FROM tbaadm.gam g
    JOIN tbaadm.eab e
        ON g.acid = e.acid
    WHERE g.schm_code IN (
        '2001','2002','2003','2004','2005','2006','2007','2008','2009','2010',
        '2011','2012','2013','2014','2015','2016','2018','2019','2020','2021',
        '2022','2023','2024','2025','2026','2027','2028','2029','2030','2031',
        '2032','2033','2034','2035',
        '2101','2102','2103','2104','2105','2106',
        '2201','2202','2203',
        '9001','9002'
    )
      AND NOT EXISTS (
        SELECT 1 FROM excluded_accts x
        WHERE x.account_number = g.foracid
      )
      AND (
            g.acct_cls_date IS NULL
            OR g.acct_cls_date BETWEEN DATE '{report_start_str}' AND DATE '{report_end_str}'  ---REPORT MONTH START & END DATE
          )
      AND e.eod_date <= DATE '{report_end_str}'  ---REPORT MONTH END DATE
      AND (
            CASE
                WHEN e.end_eod_date = DATE '2099-12-31'
                    THEN DATE '{report_end_str}'  ---REPORT MONTH END DATE
                ELSE e.end_eod_date
            END
          ) >= DATE '{report_start_str}'  ---REPORT MONTH START DATE
      -- ✅ FIX: FD scheme codes ke closed accounts exclude karo
      --         Agar account FD scheme ka hai AUR closed hai toh mat lo
      AND NOT (
                g.schm_code IN ('2001','2002','2003','2008','2009',
        '2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030','2031','2032','2033',
        '2101','2102','2103','2104','2105','2106',
        '2201','2202','2203')
                AND g.acct_cls_flg != 'N'
              )
),
/* ================= JUNE MAB ================= */
june_mab AS (
    SELECT
        sol_id,
        schm_code,
        SUM(tran_date_bal * active_days) / {total_days_till_date} AS closing_mab  --TOTAL DAYS OF CURRENT MONTH AS PER REPORT DATE RANGE
    FROM june_data
    GROUP BY sol_id, schm_code
),
/* ================= MAY DATA ================= */
may_data AS (
    SELECT
        g.sol_id,
        g.schm_code,
        e.tran_date_bal,
        (
            EXTRACT(
                DAY FROM (
                    LEAST(
                        CASE
                            WHEN e.end_eod_date = DATE '2099-12-31'
                                THEN DATE '{opening_end_str}'  ---LAST MONTH END DATE
                            ELSE e.end_eod_date
                        END,
                        DATE '{opening_end_str}'  ---LAST MONTH END DATE
                    )
                    -
                    GREATEST(e.eod_date, DATE '{opening_start_str}') ---LAST MONTH START DATE
                )
            ) + 1
        ) AS active_days
    FROM tbaadm.gam g
    JOIN tbaadm.eab e
        ON g.acid = e.acid
    WHERE g.schm_code IN (
        '2001','2002','2003','2004','2005','2006','2007','2008','2009','2010',
        '2011','2012','2013','2014','2015','2016','2018','2019','2020','2021',
        '2022','2023','2024','2025','2026','2027','2028','2029','2030','2031',
        '2032','2033','2034','2035',
        '2101','2102','2103','2104','2105','2106',
        '2201','2202','2203',
        '9001','9002'
    )
      AND NOT EXISTS (
        SELECT 1 FROM excluded_accts x
        WHERE x.account_number = g.foracid
      )
      AND (
            g.acct_cls_date IS NULL
            OR g.acct_cls_date BETWEEN DATE '{report_start_str}' AND DATE '{report_end_str}'  ---REPORT MONTH START & END DATE
          )
      AND e.eod_date <= DATE '{opening_end_str}' ---LAST MONTH END DATE
      AND (
            CASE
                WHEN e.end_eod_date = DATE '2099-12-31'
                    THEN DATE '{opening_end_str}' ---LAST MONTH END DATE
                ELSE e.end_eod_date
            END
          ) >= DATE '{opening_start_str}' ---LAST MONTH START DATE
      -- ✅ FIX: FD scheme codes ke closed accounts exclude karo
      --         Agar account FD scheme ka hai AUR closed hai toh mat lo
      AND NOT (
                g.schm_code IN ('2001','2002','2003','2008','2009',
        '2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030','2031','2032','2033',
        '2101','2102','2103','2104','2105','2106',
        '2201','2202','2203')
                AND g.acct_cls_flg != 'N'
              )
),
/* ================= MAY MAB ================= */
may_mab AS (
    SELECT
        sol_id,
        schm_code,
        SUM(tran_date_bal * active_days) / {last_month_total_days} AS opening_mab  ---TOTAL DAYS OF MONTH TOTAL
    FROM may_data
    GROUP BY sol_id, schm_code
),
/* ================= JUNE BALANCE ================= */
june_balance AS (
    SELECT
        g.sol_id,
        g.schm_code,
        SUM(e.tran_date_bal) AS closing_balance
    FROM tbaadm.gam g
    JOIN tbaadm.eab e
        ON g.acid = e.acid
    WHERE g.schm_code IN (
        '2001','2002','2003','2004','2005','2006','2007','2008','2009','2010',
        '2011','2012','2013','2014','2015','2016','2018','2019','2020','2021',
        '2022','2023','2024','2025','2026','2027','2028','2029','2030','2031',
        '2032','2033','2034','2035',
        '2101','2102','2103','2104','2105','2106',
        '2201','2202','2203',
        '9001','9002'
    )
      AND NOT EXISTS (
        SELECT 1 FROM excluded_accts x
        WHERE x.account_number = g.foracid
      )
      AND DATE '{report_end_str}' BETWEEN e.eod_date  ---REPORT MONTH END DATE
      AND CASE
            WHEN e.end_eod_date = DATE '2099-12-31'
                THEN DATE '{report_end_str}' ---REPORT MONTH END DATE
            ELSE e.end_eod_date
          END
      -- ✅ FIX: FD scheme codes ke closed accounts exclude karo
      --         Agar account FD scheme ka hai AUR closed hai toh mat lo
      AND NOT (
                g.schm_code IN ('2001','2002','2003','2008','2009',
        '2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030','2031','2032','2033',
        '2101','2102','2103','2104','2105','2106',
        '2201','2202','2203')
                AND g.acct_cls_flg != 'N'
              )
    GROUP BY g.sol_id, g.schm_code
),
/* ================= MAY BALANCE ================= */
may_balance AS (
    SELECT
        g.sol_id,
        g.schm_code,
        SUM(e.tran_date_bal) AS opening_balance
    FROM tbaadm.gam g
    JOIN tbaadm.eab e
        ON g.acid = e.acid
    WHERE g.schm_code IN (
        '2001','2002','2003','2004','2005','2006','2007','2008','2009','2010',
        '2011','2012','2013','2014','2015','2016','2018','2019','2020','2021',
        '2022','2023','2024','2025','2026','2027','2028','2029','2030','2031',
        '2032','2033','2034','2035',
        '2101','2102','2103','2104','2105','2106',
        '2201','2202','2203',
        '9001','9002'
    )
      AND NOT EXISTS (
        SELECT 1 FROM excluded_accts x
        WHERE x.account_number = g.foracid
      )
      AND DATE '{opening_end_str}' BETWEEN e.eod_date  ---LAST MONTH END DATE
      AND CASE
            WHEN e.end_eod_date = DATE '2099-12-31'
                THEN DATE '{opening_end_str}'  ---LAST MONTH END DATE
            ELSE e.end_eod_date
          END
      -- ✅ FIX: FD scheme codes ke closed accounts exclude karo
      --         Agar account FD scheme ka hai AUR closed hai toh mat lo
      AND NOT (
                g.schm_code IN ('2001','2002','2003','2008','2009',
        '2018','2019','2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030','2031','2032','2033',
        '2101','2102','2103','2104','2105','2106',
        '2201','2202','2203')
                AND g.acct_cls_flg != 'N'
              )
    GROUP BY g.sol_id, g.schm_code
),
/* ================= MAB FINAL ================= */
mab_final AS (
    SELECT
        m.sol_id,
        m.schm_code,
        ab.opening_balance,
        mb.closing_balance,
--        COALESCE(a.opening_mab, 0) AS opening_mab,
--        COALESCE(m.closing_mab, 0) AS closing_mab,
--        ROUND(COALESCE(m.closing_mab,0) - COALESCE(a.opening_mab,0),0) AS inc_mab
        ROUND(COALESCE(a.opening_mab, 0), 0)                        AS opening_mab,
        ROUND(m.closing_mab, 0)                                      AS closing_mab,
        --ROUND(m.closing_mab - COALESCE(a.opening_mab, 0), 0)        AS inc_mab
        ROUND(m.closing_mab, 0) - ROUND(COALESCE(a.opening_mab, 0), 0) AS inc_mab
    FROM june_mab m
    LEFT JOIN may_mab a
        ON m.sol_id = a.sol_id
       AND m.schm_code = a.schm_code
    LEFT JOIN june_balance mb
        ON m.sol_id = mb.sol_id
       AND m.schm_code = mb.schm_code
    LEFT JOIN may_balance ab
        ON m.sol_id = ab.sol_id
       AND m.schm_code = ab.schm_code
),
schema_driver AS (
    SELECT
        s.sol_id,
        x.schm_code
    FROM tbaadm.sol s
    CROSS JOIN (
        SELECT '1007' AS schm_code UNION ALL     -- ✅ NEW: added so schm_code 1007 also appears in final output
        SELECT '2001' UNION ALL SELECT '2002' UNION ALL SELECT '2003'
        UNION ALL SELECT '2004' UNION ALL SELECT '2005' UNION ALL SELECT '2006'
        UNION ALL SELECT '2007' UNION ALL SELECT '2008' UNION ALL SELECT '2009'
        UNION ALL SELECT '2010' UNION ALL SELECT '2011' UNION ALL SELECT '2012'
        UNION ALL SELECT '2013' UNION ALL SELECT '2014' UNION ALL SELECT '2015'
        UNION ALL SELECT '2016' UNION ALL SELECT '2018' UNION ALL SELECT '2019'
        UNION ALL SELECT '2020' UNION ALL SELECT '2021' UNION ALL SELECT '2022'
        UNION ALL SELECT '2023' UNION ALL SELECT '2024' UNION ALL SELECT '2025'
        UNION ALL SELECT '2026' UNION ALL SELECT '2027' UNION ALL SELECT '2028'
        UNION ALL SELECT '2029' UNION ALL SELECT '2030' UNION ALL SELECT '2031'
        UNION ALL SELECT '2032' UNION ALL SELECT '2033' UNION ALL SELECT '2034'
        UNION ALL SELECT '2035'
        UNION ALL SELECT '2101' UNION ALL SELECT '2102' UNION ALL SELECT '2103'
        UNION ALL SELECT '2104' UNION ALL SELECT '2105' UNION ALL SELECT '2106'
        UNION ALL SELECT '2201' UNION ALL SELECT '2202' UNION ALL SELECT '2203'
        UNION ALL SELECT '9001' UNION ALL SELECT '9002'
    ) x
)
/* ================= FINAL OUTPUT ================= */
SELECT
    sd.sol_id,
    sd.schm_code,
    s.sol_desc,
    s.region_name,
    s.division_name,
    s.circle_office_name,
--   sd.schm_code,
    f.schm_code,
    COALESCE(f.total_flow_amount, 0) AS total_flow_amount,
    COALESCE(f.total_tran_amt, 0) AS total_tran_amt,
--    COALESCE(m.opening_balance, 0) AS opening_balance,
--    COALESCE(m.closing_balance, 0) AS closing_balance,
    COALESCE(CEIL(m.opening_balance), 0) AS opening_balance,
    COALESCE(CEIL(m.closing_balance), 0) AS closing_balance,
    COALESCE(CEIL(m.opening_mab), 0) AS opening_mab,
    COALESCE(CEIL(m.closing_mab), 0) AS closing_mab,
    COALESCE(m.inc_mab, 0) AS inc_mab,
    COALESCE(f.total_tran_amt, 0)
        + COALESCE(m.inc_mab, 0) AS achivment
FROM schema_driver sd
LEFT JOIN tbaadm.sol s
    ON s.sol_id = sd.sol_id
LEFT JOIN final_data f
    ON sd.sol_id = f.sol_id
   AND sd.schm_code = f.schm_code
LEFT JOIN mab_final m
    ON sd.sol_id = m.sol_id
   AND sd.schm_code = m.schm_code   -- ✅ CHANGED: schm_code condition moved from WHERE into ON,
                                     --            taki 1007 (jiske paas MAB/balance data nahi hai)
                                     --            LEFT JOIN se drop na ho. Purane schm_codes ke
                                     --            result par koi asar nahi padta.
WHERE sd.sol_id NOT IN ('1000','1031','1059','1081','1104');   ---EXCLUDE THESE SOL_ID FROM FINAL OUTPUT'''

    conn = get_dr_connection()
    if not conn:
        frappe.throw("Failed to connect to DR database. Please check your Finacle DR DB credentials.")

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"TDA Sync - Total rows fetched from DB: {len(rows)}", flush=True)

        now_time = now_datetime()
        bulk_data = []
        
        # Pre-fetch product group_name mappings from DB to emulate Fetch From
        product_map = get_product_group_map_cached()

        for row in rows:
            sol_id = str(row[0]).strip()
            schm_code = str(row[1]).strip()
            achievement = float(row[8] or 0)
            
            final_zone = clean_zone_region(row[5] or row[4], "ZONE")
            final_region = clean_zone_region(row[3], "REGION")
            
            product_group = product_map.get(schm_code)
            
            name = frappe.generate_hash(length=16)
            bulk_data.append((
                name,
                now_time,
                now_time,
                "Administrator",
                "Administrator",
                0,
                0,
                final_zone,
                final_region,
                product_group or "TDA",
                achievement,
                processed_date,
                sol_id,
                schm_code
            ))

        # Deleting old records for this date and TDA products to prevent duplicates
        frappe.db.delete("Product Wise Report", {
            "date": processed_date,
            "product": "TDA"
        })

        print(f"TDA Sync - Starting bulk insertion of {len(bulk_data)} records into Product Wise Report...", flush=True)
        
        fields = [
            "name", "creation", "modified", "modified_by", "owner", 
            "docstatus", "idx", "zone", "region", "product", "amount", 
            "date", "sol_id", "scheme_code"
        ]
        
        frappe.db.bulk_insert("Product Wise Report", fields, bulk_data)
        frappe.db.commit()
        
        print(f"TDA Sync - Successfully synced and committed {len(bulk_data)} records.", flush=True)
        return len(bulk_data)

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Product Wise TDA Sync Failed")
        raise e
    finally:
        try:
            conn.close()
        except Exception:
            pass

@frappe.whitelist(allow_guest=True)
@sahayog_cache(ttl=86400)
def get_gl_wise_ch_report_data(selected_date=None):
    """
    Returns the GL Wise CH Report data with hierarchical grouping:
    Zone -> Region -> District -> Sol (Branch Sol ID)
    """
    if not selected_date:
        selected_date = frappe.db.get_value("Product Wise Report", {}, "date", order_by="date desc")

    if not selected_date:
        return {"product_wise": [], "all_products": []}

    # Fetch raw product wise report data without joins
    raw_data_db = frappe.db.sql("""
        SELECT
            zone,
            region,
            sol_id,
            product,
            scheme_code,
            SUM(amount) as amount
        FROM `tabProduct Wise Report`
        WHERE date = %s
        GROUP BY zone, region, sol_id, product, scheme_code
    """, (selected_date,), as_dict=True)

    prod_map = get_products_map_cached()
    branches_map = get_sahayog_branches_cached()
    
    raw_data = []
    grouped_map = defaultdict(float)
    
    for row in raw_data_db:
        sid = str(row.sol_id or "").strip()
        b = branches_map.get(sid, {})
        
        zone = b.get("zone") or row.zone or ""
        region = b.get("region") or row.region or ""
        district = b.get("district") or "Unknown District"
        branch_name = b.get("branch_name") or ""
        
        if not zone or not region:
            continue
            
        pr = prod_map.get(row.scheme_code)
        
        product = row.product
        if pr:
            group_name = pr.group_name
            group_subname = pr.group_subname
            group_subname_category = pr.group_subname_category
            
            if row.product == 'RD' and group_subname == 'JLL RD' and not group_subname_category:
                product = 'JLL RD'
            elif row.product == 'RD' and not group_subname and not group_subname_category:
                product = 'RD'
            elif row.product == 'SMBG' and group_subname == 'SKBG' and not group_subname_category:
                product = 'SKBG'
            elif row.product == 'SMBG' and not group_subname and not group_subname_category:
                product = 'SMBG'
            elif group_name == 'CASA' and group_subname == 'TASC' and group_subname_category == 'TASKSILVER':
                product = 'TASKSILVER'
            elif group_name == 'CASA' and group_subname == 'TASC' and group_subname_category == 'TASKWEALTH':
                product = 'TASKWEALTH'
            elif group_name == 'CASA' and group_subname == 'SA' and group_subname_category == 'SAVSIL':
                product = 'SAVSIL'
            elif group_name == 'CASA' and group_subname == 'CA' and group_subname_category == 'CUGOLD':
                product = 'CUGOLD'
            elif group_name == 'CASA' and group_subname == 'CA' and group_subname_category == 'CUWEALTH':
                product = 'CUWEALTH'
                
        key = (zone, region, district, sid, branch_name, product)
        grouped_map[key] += float(row.amount or 0)
        
    for key, amount in grouped_map.items():
        zone, region, district, sid, branch_name, product = key
        raw_data.append(frappe._dict({
            "zone": zone,
            "region": region,
            "district": district,
            "sol_id": sid,
            "branch_name": branch_name,
            "product": product,
            "amount": amount
        }))
        
    raw_data.sort(key=lambda x: (x.zone, x.region, x.district, x.sol_id))

    if not raw_data:
        return {"product_wise": [], "all_products": []}

    # Get all unique products for dynamic column generation
    all_products = sorted(list(set(row.product for row in raw_data)))

    # Build nested hierarchy dictionary: zone -> region -> district -> sol_id
    hierarchy = {}
    for row in raw_data:
        z = row.zone
        r = row.region
        d = row.district
        s = row.sol_id
        bname = row.branch_name
        prod = row.product
        amt = row.amount or 0.0

        if z not in hierarchy:
            hierarchy[z] = {}
        if r not in hierarchy[z]:
            hierarchy[z][r] = {}
        if d not in hierarchy[z][r]:
            hierarchy[z][r][d] = {}
        if s not in hierarchy[z][r][d]:
            hierarchy[z][r][d][s] = {
                "branch_name": bname,
                "products": defaultdict(float),
                "total_amount": 0.0
            }
        
        hierarchy[z][r][d][s]["products"][prod] += amt
        hierarchy[z][r][d][s]["total_amount"] += amt

    # Process into a flat list with clear parents for UI rendering
    result = []
    
    for zone in sorted(hierarchy.keys()):
        zone_products = defaultdict(float)
        zone_amount = 0.0
        zone_rows = []

        for region in sorted(hierarchy[zone].keys()):
            region_products = defaultdict(float)
            region_amount = 0.0
            region_rows = []

            for district in sorted(hierarchy[zone][region].keys()):
                district_products = defaultdict(float)
                district_amount = 0.0
                district_rows = []

                for sol_id in sorted(hierarchy[zone][region][district].keys()):
                    sol_info = hierarchy[zone][region][district][sol_id]
                    sol_amt = sol_info["total_amount"]
                    sol_prods = sol_info["products"]

                    # Accumulate for District
                    district_amount += sol_amt
                    for prod, amt in sol_prods.items():
                        district_products[prod] += amt

                    sol_display_name = f"{sol_id} - {sol_info['branch_name']}" if sol_info['branch_name'] else sol_id
                    district_rows.append({
                        "type": "sol",
                        "name": sol_display_name,
                        "path": f"{zone}/{region}/{district}/{sol_id}",
                        "parent_district": f"{zone}/{region}/{district}",
                        "parent_region": f"{zone}/{region}",
                        "parent_zone": zone,
                        "amount": sol_amt,
                        "products": dict(sol_prods),
                        "is_group": False
                    })

                # Accumulate for Region
                region_amount += district_amount
                for prod, amt in district_products.items():
                    region_products[prod] += amt

                region_rows.append({
                    "type": "district",
                    "name": district,
                    "path": f"{zone}/{region}/{district}",
                    "parent_region": f"{zone}/{region}",
                    "parent_zone": zone,
                    "amount": district_amount,
                    "products": dict(district_products),
                    "is_group": True,
                    "children": district_rows
                })

            # Accumulate for Zone
            zone_amount += region_amount
            for prod, amt in region_products.items():
                zone_products[prod] += amt

            zone_rows.append({
                "type": "region",
                "name": region,
                "path": f"{zone}/{region}",
                "parent_zone": zone,
                "amount": region_amount,
                "products": dict(region_products),
                "is_group": True,
                "children": region_rows
            })

        # Add Zone Group Row
        result.append({
            "type": "zone",
            "name": zone,
            "path": zone,
            "parent_zone": None,
            "amount": zone_amount,
            "products": dict(zone_products),
            "is_group": True
        })

        # Flatten the structure
        for r_row in zone_rows:
            d_rows = r_row.pop("children")
            result.append(r_row)
            for d_row in d_rows:
                s_rows = d_row.pop("children")
                result.append(d_row)
                result.extend(s_rows)

    return {
        "product_wise": result,
        "all_products": all_products
    }

  
@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_bucket_wise_account_mis_data_old(selected_date=None):
    from custom_report.db_connection import get_dr_connection
    from frappe.utils import getdate
    import datetime

    if not selected_date:
        selected_date = str(datetime.date.today())

    dt = getdate(selected_date)
    month_start = dt.replace(day=1).strftime("%Y-%m-%d")
    ref_date = dt.strftime("%Y-%m-%d")

    query = f"""
    WITH account_data AS (
        SELECT
            d.rm_id,
            g2.emp_name AS rm_name,
            d2.operacc,
            d2.auth_id,
            d2.auth_role_id,
            g.cif_id,
            g.acct_opn_date,
            a2.relationshipopeningdate AS cif_id_opening_date,
            g.foracid,
            g.clr_bal_amt,
            tam.deposit_period_mths,
            tam.deposit_period_days,
            tam.deposit_amount,
            tam.maturity_amount,
            tam.maturity_date,
            g.sol_id,
            sol.sol_desc,
            g.schm_code,
            gsp.schm_desc,
            g.acct_cls_date,
            g.acct_cls_flg
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        LEFT JOIN
            crmuser.accounts AS a2 ON g.cif_id = a2.orgkey
        LEFT JOIN
            tbaadm.sol AS sol ON g.sol_id = sol.sol_id
        LEFT JOIN
            tbaadm.gsp AS gsp ON g.schm_code = gsp.schm_code
        LEFT JOIN
            custom.dsaauth AS d2 ON d.rm_id = d2.user_id
        LEFT JOIN
            tbaadm.get AS g2 ON d2.user_id = g2.emp_id
        LEFT JOIN
            tbaadm.tam AS tam ON g.acid = tam.acid    
        WHERE
            g.acct_cls_flg <> 'Y'
            OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
    ),
    -- === NEW CTE ADD  (Step 1) ===
    demand_data AS (
        SELECT
            ad.foracid,
            ad.schm_code,
            CASE
                -- Condition 1: ac opened before current month AND maturity after current month
                WHEN ad.acct_opn_date::DATE < DATE_TRUNC('month', DATE '{ref_date}')::DATE
              AND ad.maturity_date::DATE >
             (DATE_TRUNC('month', DATE '{ref_date}')
              + INTERVAL '1 month'
              - INTERVAL '1 day')::DATE
               THEN ad.deposit_amount * (
            (
              DATE_TRUNC('month', DATE '{ref_date}')
              + INTERVAL '1 month'
              - INTERVAL '1 day'
            )::DATE
            - DATE_TRUNC('month', DATE '{ref_date}')::DATE
            + 1
           )
               -- Condition 2: maturity falls within current month -> demand till one day before maturity
                WHEN ad.maturity_date::DATE >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            AND ad.maturity_date::DATE <= (
             DATE_TRUNC('month', DATE '{ref_date}')
             + INTERVAL '1 month'
             - INTERVAL '1 day'
           )::DATE
                THEN ad.deposit_amount * (
            ad.maturity_date::DATE
            - DATE_TRUNC('month', DATE '{ref_date}')::DATE
           )
               -- Condition 3: ac opened during current month -> ac age for current month
               -- Condition 3: account opened in current month
               WHEN ad.acct_opn_date::DATE >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
                AND ad.acct_opn_date::DATE <= (
                DATE_TRUNC('month', DATE '{ref_date}')
               + INTERVAL '1 month'
                 - INTERVAL '1 day'
             )::DATE
           THEN ad.deposit_amount * (
        ad.acct_opn_date::DATE
        - DATE_TRUNC('month', DATE '{ref_date}')::DATE
        + 1
    )
    ELSE 0
    END AS demand_amount
    FROM
        account_data AS ad
    ),
    -- === YAHAN TAK NAYA CTE KHATAM ===
    flow_data AS (
        SELECT
            d.rm_id,
            g.foracid,
            g.schm_code,
            SUM(tdt.flow_amt) AS total_flow_amount
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        INNER JOIN
            tbaadm.tdt AS tdt ON tdt.acid = g.acid AND tdt.flow_code = 'NI'
        WHERE
            tdt.flow_date BETWEEN '{month_start}' AND DATE '{ref_date}'
            AND (
                g.acct_cls_flg <> 'Y'
                OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            )
        GROUP BY
            d.rm_id, g.foracid, g.schm_code
        HAVING
            SUM(tdt.flow_amt) > 0
    ),
    tran_data AS (
        SELECT
            d.rm_id,
            g.foracid,
            g.schm_code,
            SUM(dtt.tran_amt) AS total_tran_amt
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        INNER JOIN
            tbaadm.dtt AS dtt ON dtt.acid = g.acid AND dtt.flow_code = 'NI'
        WHERE
            dtt.value_date BETWEEN '{month_start}' AND DATE '{ref_date}'
            AND (
                g.acct_cls_flg <> 'Y'
                OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            )
        GROUP BY
            d.rm_id, g.foracid, g.schm_code
        HAVING
            SUM(dtt.tran_amt) > 0
    ),
    reference_data AS (
        SELECT
            ed.referencenumber,
            da.user_id AS rm_id
        FROM
            crmuser.entitydocument AS ed
        INNER JOIN
            tbaadm.gam AS g ON ed.orgkey = g.cif_id
        INNER JOIN
            custom.dsaauth AS da ON g.foracid = da.operacc
        WHERE
            ed.doccode = 'PAN'
    )
    SELECT
        ad.rm_id,
        ad.rm_name,
        ad.operacc,
        ad.auth_id,
        ad.auth_role_id AS auth_name,
        ad.cif_id,
        ad.acct_opn_date,
        ad.cif_id_opening_date,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) AS account_age,
        ad.foracid,
        ad.schm_code,
        ad.schm_desc,
        ad.sol_id,
        ad.sol_desc,
        ad.deposit_period_mths,
        ad.deposit_period_days,
        ad.deposit_amount,
        ad.maturity_amount,
        ad.maturity_date,
        ad.acct_cls_date,
        ad.acct_cls_flg,
        COALESCE(fd.total_flow_amount, 0) AS total_flow_amount,
        COALESCE(td.total_tran_amt, 0) AS total_tran_amt,
        COALESCE(dd.demand_amount, 0) AS monthly_demand_amount,   -- === NEW COLUMN ADDED (Step 3) ===
        COALESCE(td.total_tran_amt, 0) AS monthly_collection,
        LEAST(
        ROUND(
            COALESCE(dd.demand_amount, 0) / NULLIF(ad.deposit_amount, 0),2),365) AS monthly_demand_days,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount AS ytd_demand_amount,
        COALESCE(ad.clr_bal_amt, 0) AS ytd_collection,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) AS ytd_demand_days,
        CASE
        WHEN (LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount) = 0
        THEN 0
        ELSE ROUND(
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        )
    END AS ytd_coll_pct,
    CASE
        WHEN (LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount) = 0
        THEN 'DEFAULT'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 100 THEN 'Excess'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 75 THEN 'A'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 50 THEN 'B'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 25 THEN 'C'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 0 THEN 'D'
        ELSE 'DEFAULT'
    END AS colle_category,
        ROUND(
            CASE
                WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 100000 THEN
                    0.035 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
                WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) > 100000
                     AND LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 200000 THEN
                    0.04 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
                ELSE
                    0.05 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
            END
        ) AS commission,
        COALESCE(rd.referencenumber, 'N/A') AS referencenumber
    FROM
        account_data AS ad
    LEFT JOIN
        flow_data AS fd ON ad.rm_id = fd.rm_id AND ad.foracid = fd.foracid AND ad.schm_code = fd.schm_code
    LEFT JOIN
        tran_data AS td ON ad.rm_id = td.rm_id AND ad.foracid = td.foracid AND ad.schm_code = td.schm_code
    LEFT JOIN
        demand_data AS dd ON ad.foracid = dd.foracid AND ad.schm_code = dd.schm_code   -- === NEW JOIN (Step 2) ===
    LEFT JOIN
        reference_data AS rd ON ad.rm_id = rd.rm_id
    WHERE
        (fd.total_flow_amount > 0 OR td.total_tran_amt > 0)
    ORDER BY
        ad.foracid, ad.rm_id, ad.schm_code;
    """

    import time
    max_attempts = 3
    for attempt in range(max_attempts):
        conn = get_dr_connection()
        if not conn:
            frappe.log_error("Failed to connect to DR database", "Bucket Wise Account MIS API")
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout TO '180000'")
            cursor.execute(query)
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]

            raw_data = []
            for row in rows:
                row_dict = {}
                for i, val in enumerate(row):
                    col = headers[i]
                    if val is None:
                        row_dict[col] = None
                    elif isinstance(val, (int, float)):
                        row_dict[col] = val
                    elif hasattr(val, 'isoformat'):
                        row_dict[col] = str(val)[:10]
                    else:
                        row_dict[col] = str(val)
                raw_data.append(row_dict)

            sol_ids = list(set(r["sol_id"] for r in raw_data if r.get("sol_id")))
            branch_map = {}
            if sol_ids:
                branches_map = get_sahayog_branches_cached()
                for sid in sol_ids:
                    if sid in branches_map:
                        b = branches_map[sid]
                        branch_map[sid] = {
                            "zone": b.get("zone") or "Unknown",
                            "region": b.get("region") or "Unknown",
                            "district": b.get("district") or "Unknown",
                            "branch_name": b.get("branch_name") or sid
                        }
                    else:
                        branch_map[sid] = {
                            "zone": "Unknown",
                            "region": "Unknown",
                            "district": "Unknown",
                            "branch_name": sid
                        }

            summary = {}
            for r in raw_data:
                sid = r.get("sol_id")
                if not sid:
                    continue
                br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
                key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}"
                if key not in summary:
                    summary[key] = {
                        "zone": br["zone"],
                        "region": br["region"],
                        "district": br["district"],
                        "sol_id": sid,
                        "sol_desc": br["branch_name"],
                        "A": 0, "B": 0, "C": 0, "D": 0, "DEFAULT": 0, "Excess": 0,
                        "grand_total": 0
                    }
                cat = r.get("colle_category", "DEFAULT")
                if cat in summary[key]:
                    summary[key][cat] += 1
                summary[key]["grand_total"] += 1

            result = sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))

            return {
                "summary": result,
                "total_records": len(raw_data)
            }
        except Exception as e:
            frappe.log_error(f"Error executing Bucket Wise Account MIS query (attempt {attempt+1}): {str(e)}", "Bucket Wise Account MIS API")
            conn.close()
            if attempt < max_attempts - 1:
                time.sleep(2)
            else:
                return []


@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_new_account_report_data_old(selected_date=None):
    from custom_report.db_connection import get_dr_connection
    from frappe.utils import getdate
    import datetime
    import time

    if not selected_date:
        selected_date = str(datetime.date.today())

    dt = getdate(selected_date)
    month_start = dt.replace(day=1).strftime("%Y-%m-%d")
    ref_date = dt.strftime("%Y-%m-%d")

    # Use the same backend query
    query = f"""
    WITH account_data AS (
        SELECT
            d.rm_id,
            g2.emp_name AS rm_name,
            d2.operacc,
            d2.auth_id,
            d2.auth_role_id,
            g.cif_id,
            g.acct_opn_date,
            a2.relationshipopeningdate AS cif_id_opening_date,
            g.foracid,
            g.clr_bal_amt,
            tam.deposit_period_mths,
            tam.deposit_period_days,
            tam.deposit_amount,
            tam.maturity_amount,
            tam.maturity_date,
            g.sol_id,
            sol.sol_desc,
            g.schm_code,
            gsp.schm_desc,
            g.acct_cls_date,
            g.acct_cls_flg
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        LEFT JOIN
            crmuser.accounts AS a2 ON g.cif_id = a2.orgkey
        LEFT JOIN
            tbaadm.sol AS sol ON g.sol_id = sol.sol_id
        LEFT JOIN
            tbaadm.gsp AS gsp ON g.schm_code = gsp.schm_code
        LEFT JOIN
            custom.dsaauth AS d2 ON d.rm_id = d2.user_id
        LEFT JOIN
            tbaadm.get AS g2 ON d2.user_id = g2.emp_id
        LEFT JOIN
            tbaadm.tam AS tam ON g.acid = tam.acid    
        WHERE
            g.acct_cls_flg <> 'Y'
            OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
    ),
    -- === NEW CTE ADD  (Step 1) ===
    demand_data AS (
        SELECT
            ad.foracid,
            ad.schm_code,
            CASE
                -- Condition 1: ac opened before current month AND maturity after current month
                WHEN ad.acct_opn_date::DATE < DATE_TRUNC('month', DATE '{ref_date}')::DATE
              AND ad.maturity_date::DATE >
             (DATE_TRUNC('month', DATE '{ref_date}')
              + INTERVAL '1 month'
              - INTERVAL '1 day')::DATE
               THEN ad.deposit_amount * (
            (
              DATE_TRUNC('month', DATE '{ref_date}')
              + INTERVAL '1 month'
              - INTERVAL '1 day'
            )::DATE
            - DATE_TRUNC('month', DATE '{ref_date}')::DATE
            + 1
           )
               -- Condition 2: maturity falls within current month -> demand till one day before maturity
                WHEN ad.maturity_date::DATE >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            AND ad.maturity_date::DATE <= (
             DATE_TRUNC('month', DATE '{ref_date}')
             + INTERVAL '1 month'
             - INTERVAL '1 day'
           )::DATE
                THEN ad.deposit_amount * (
            ad.maturity_date::DATE
            - DATE_TRUNC('month', DATE '{ref_date}')::DATE
           )
               -- Condition 3: ac opened during current month -> ac age for current month
               -- Condition 3: account opened in current month
               WHEN ad.acct_opn_date::DATE >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
                AND ad.acct_opn_date::DATE <= (
                DATE_TRUNC('month', DATE '{ref_date}')
               + INTERVAL '1 month'
                 - INTERVAL '1 day'
             )::DATE
           THEN ad.deposit_amount * (
        ad.acct_opn_date::DATE
        - DATE_TRUNC('month', DATE '{ref_date}')::DATE
        + 1
    )
    ELSE 0
    END AS demand_amount
    FROM
        account_data AS ad
    ),
    -- === YAHAN TAK NAYA CTE KHATAM ===
    flow_data AS (
        SELECT
            d.rm_id,
            g.foracid,
            g.schm_code,
            SUM(tdt.flow_amt) AS total_flow_amount
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        INNER JOIN
            tbaadm.tdt AS tdt ON tdt.acid = g.acid AND tdt.flow_code = 'NI'
        WHERE
            tdt.flow_date BETWEEN '{month_start}' AND DATE '{ref_date}'
            AND (
                g.acct_cls_flg <> 'Y'
                OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            )
        GROUP BY
            d.rm_id, g.foracid, g.schm_code
        HAVING
            SUM(tdt.flow_amt) > 0
    ),
    tran_data AS (
        SELECT
            d.rm_id,
            g.foracid,
            g.schm_code,
            SUM(dtt.tran_amt) AS total_tran_amt
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        INNER JOIN
            tbaadm.dtt AS dtt ON dtt.acid = g.acid AND dtt.flow_code = 'NI'
        WHERE
            dtt.value_date BETWEEN '{month_start}' AND DATE '{ref_date}'
            AND (
                g.acct_cls_flg <> 'Y'
                OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            )
        GROUP BY
            d.rm_id, g.foracid, g.schm_code
        HAVING
            SUM(dtt.tran_amt) > 0
    ),
    reference_data AS (
        SELECT
            ed.referencenumber,
            da.user_id AS rm_id
        FROM
            crmuser.entitydocument AS ed
        INNER JOIN
            tbaadm.gam AS g ON ed.orgkey = g.cif_id
        INNER JOIN
            custom.dsaauth AS da ON g.foracid = da.operacc
        WHERE
            ed.doccode = 'PAN'
    )
    SELECT
        ad.rm_id,
        ad.rm_name,
        ad.operacc,
        ad.auth_id,
        ad.auth_role_id AS auth_name,
        ad.cif_id,
        ad.acct_opn_date,
        ad.cif_id_opening_date,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) AS account_age,
        ad.foracid,
        ad.schm_code,
        ad.schm_desc,
        ad.sol_id,
        ad.sol_desc,
        ad.deposit_period_mths,
        ad.deposit_period_days,
        ad.deposit_amount,
        ad.maturity_amount,
        ad.maturity_date,
        ad.acct_cls_date,
        ad.acct_cls_flg,
        COALESCE(fd.total_flow_amount, 0) AS total_flow_amount,
        COALESCE(td.total_tran_amt, 0) AS total_tran_amt,
        COALESCE(dd.demand_amount, 0) AS monthly_demand_amount,   -- === NEW COLUMN ADDED (Step 3) ===
        COALESCE(td.total_tran_amt, 0) AS monthly_collection,
        LEAST(
        ROUND(
            COALESCE(dd.demand_amount, 0) / NULLIF(ad.deposit_amount, 0),2),365) AS monthly_demand_days,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount AS ytd_demand_amount,
        COALESCE(ad.clr_bal_amt, 0) AS ytd_collection,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) AS ytd_demand_days,
        CASE
        WHEN (LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount) = 0
        THEN 0
        ELSE ROUND(
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        )
    END AS ytd_coll_pct,
    CASE
        WHEN (LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount) = 0
        THEN 'DEFAULT'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 100 THEN 'Excess'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 75 THEN 'A'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 50 THEN 'B'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 25 THEN 'C'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 0 THEN 'D'
        ELSE 'DEFAULT'
    END AS colle_category,
        ROUND(
            CASE
                WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 100000 THEN
                    0.035 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
                WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) > 100000
                     AND LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 200000 THEN
                    0.04 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
                ELSE
                    0.05 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
            END
        ) AS commission,
        COALESCE(rd.referencenumber, 'N/A') AS referencenumber
    FROM
        account_data AS ad
    LEFT JOIN
        flow_data AS fd ON ad.rm_id = fd.rm_id AND ad.foracid = fd.foracid AND ad.schm_code = fd.schm_code
    LEFT JOIN
        tran_data AS td ON ad.rm_id = td.rm_id AND ad.foracid = td.foracid AND ad.schm_code = td.schm_code
    LEFT JOIN
        demand_data AS dd ON ad.foracid = dd.foracid AND ad.schm_code = dd.schm_code   -- === NEW JOIN (Step 2) ===
    LEFT JOIN
        reference_data AS rd ON ad.rm_id = rd.rm_id
    WHERE
        (fd.total_flow_amount > 0 OR td.total_tran_amt > 0)
    ORDER BY
        ad.foracid, ad.rm_id, ad.schm_code;
    """

    max_attempts = 3
    for attempt in range(max_attempts):
        conn = get_dr_connection()
        if not conn:
            frappe.log_error("Failed to connect to DR database", "New Account Report API")
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout TO '180000'")
            cursor.execute(query)
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]

            raw_data = []
            for row in rows:
                row_dict = {}
                for i, val in enumerate(row):
                    col = headers[i]
                    if val is None:
                        row_dict[col] = None
                    elif isinstance(val, (int, float)):
                        row_dict[col] = val
                    elif hasattr(val, 'isoformat'):
                        row_dict[col] = str(val)[:10]
                    else:
                        row_dict[col] = str(val)
                raw_data.append(row_dict)

            sol_ids = list(set(r["sol_id"] for r in raw_data if r.get("sol_id")))
            branch_map = {}
            if sol_ids:
                branches_map = get_sahayog_branches_cached()
                for sid in sol_ids:
                    if sid in branches_map:
                        b = branches_map[sid]
                        branch_map[sid] = {
                            "zone": b.get("zone") or "Unknown",
                            "region": b.get("region") or "Unknown",
                            "district": b.get("district") or "Unknown",
                            "branch_name": b.get("branch_name") or sid
                        }
                    else:
                        branch_map[sid] = {
                            "zone": "Unknown",
                            "region": "Unknown",
                            "district": "Unknown",
                            "branch_name": sid
                        }

            # Fetch designations for all unique employee IDs in bulk
            emp_ids = set()
            for r in raw_data:
                auth_id = r.get("auth_id")
                if auth_id and auth_id != "Unknown":
                    digits = re.findall(r'\d+', auth_id)
                    if digits:
                        try:
                            emp_id = str(int(''.join(digits)))
                            emp_ids.add(emp_id)
                        except ValueError:
                            pass
            
            designation_map = {}
            if emp_ids:
                employees = frappe.get_all(
                    "Employee",
                    filters={"name": ["in", list(emp_ids)]},
                    fields=["name", "designation"]
                )
                for emp in employees:
                    designation_map[emp.name] = emp.designation or ""

            summary = {}
            for r in raw_data:
                sid = r.get("sol_id")
                if not sid:
                    continue

                # Check if account opening date is in the current month
                acct_opn_date_str = r.get("acct_opn_date")
                is_new = False
                if acct_opn_date_str:
                    try:
                        opn_dt = getdate(acct_opn_date_str)
                        if opn_dt.month == dt.month and opn_dt.year == dt.year:
                            is_new = True
                    except Exception:
                        pass

                if not is_new:
                    continue

                br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
                auth_id = r.get("auth_id") or "Unknown"
                auth_name = r.get("auth_name") or "Unknown"

                designation = ""
                if auth_id and auth_id != "Unknown":
                    digits = re.findall(r'\d+', auth_id)
                    if digits:
                        try:
                            emp_id = str(int(''.join(digits)))
                            designation = designation_map.get(emp_id) or ""
                        except ValueError:
                            pass

                key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}||{auth_id}||{auth_name}||{designation}"
                if key not in summary:
                    summary[key] = {
                        "zone": br["zone"],
                        "region": br["region"],
                        "district": br["district"],
                        "sol_id": sid,
                        "sol_desc": br["branch_name"],
                        "auth_id": auth_id,
                        "auth_name": auth_name,
                        "designation": designation,
                        "new_ac": 0,
                        "deposit_amount": 0.0
                    }

                summary[key]["new_ac"] += 1
                summary[key]["deposit_amount"] += float(r.get("deposit_amount") or 0)

            result = sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))
            return result
        except Exception as e:
            frappe.log_error(f"Error executing New Account Report query (attempt {attempt+1}): {str(e)}", "New Account Report API")
            conn.close()
            if attempt < max_attempts - 1:
                time.sleep(2)
            else:
                return []


@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_staff_wise_demand_collection_data_old(selected_date=None):
    from custom_report.db_connection import get_dr_connection
    from frappe.utils import getdate
    import datetime
    import time

    if not selected_date:
        selected_date = str(datetime.date.today())

    dt = getdate(selected_date)
    month_start = dt.replace(day=1).strftime("%Y-%m-%d")
    ref_date = dt.strftime("%Y-%m-%d")

    print(f"DEBUG [STAFF WISE]: selected_date passed = {selected_date}", flush=True)
    print(f"DEBUG [STAFF WISE]: month_start calculated = {month_start}", flush=True)
    print(f"DEBUG [STAFF WISE]: ref_date calculated = {ref_date}", flush=True)

    # Wahi query: Bucket Wise / New Account SQL but including demand and collection
    query = f"""
    WITH account_data AS (
        SELECT
            d.rm_id,
            g2.emp_name AS rm_name,
            d2.operacc,
            d2.auth_id,
            d2.auth_role_id,
            g.cif_id,
            g.acct_opn_date,
            a2.relationshipopeningdate AS cif_id_opening_date,
            g.foracid,
            g.clr_bal_amt,
            tam.deposit_period_mths,
            tam.deposit_period_days,
            tam.deposit_amount,
            tam.maturity_amount,
            tam.maturity_date,
            g.sol_id,
            sol.sol_desc,
            g.schm_code,
            gsp.schm_desc,
            g.acct_cls_date,
            g.acct_cls_flg
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        LEFT JOIN
            crmuser.accounts AS a2 ON g.cif_id = a2.orgkey
        LEFT JOIN
            tbaadm.sol AS sol ON g.sol_id = sol.sol_id
        LEFT JOIN
            tbaadm.gsp AS gsp ON g.schm_code = gsp.schm_code
        LEFT JOIN
            custom.dsaauth AS d2 ON d.rm_id = d2.user_id
        LEFT JOIN
            tbaadm.get AS g2 ON d2.user_id = g2.emp_id
        LEFT JOIN
            tbaadm.tam AS tam ON g.acid = tam.acid    
        WHERE
            g.acct_cls_flg <> 'Y'
            OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
    ),
    -- === NEW CTE ADD  (Step 1) ===
    demand_data AS (
        SELECT
            ad.foracid,
            ad.schm_code,
            CASE
                -- Condition 1: ac opened before current month AND maturity after current month
                WHEN ad.acct_opn_date::DATE < DATE_TRUNC('month', DATE '{ref_date}')::DATE
              AND ad.maturity_date::DATE >
             (DATE_TRUNC('month', DATE '{ref_date}')
              + INTERVAL '1 month'
              - INTERVAL '1 day')::DATE
               THEN ad.deposit_amount * (
            (
              DATE_TRUNC('month', DATE '{ref_date}')
              + INTERVAL '1 month'
              - INTERVAL '1 day'
            )::DATE
            - DATE_TRUNC('month', DATE '{ref_date}')::DATE
            + 1
           )
               -- Condition 2: maturity falls within current month -> demand till one day before maturity
                WHEN ad.maturity_date::DATE >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            AND ad.maturity_date::DATE <= (
             DATE_TRUNC('month', DATE '{ref_date}')
             + INTERVAL '1 month'
             - INTERVAL '1 day'
           )::DATE
                THEN ad.deposit_amount * (
            ad.maturity_date::DATE
            - DATE_TRUNC('month', DATE '{ref_date}')::DATE
           )
               -- Condition 3: ac opened during current month -> ac age for current month
               -- Condition 3: account opened in current month
               WHEN ad.acct_opn_date::DATE >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
                AND ad.acct_opn_date::DATE <= (
                DATE_TRUNC('month', DATE '{ref_date}')
               + INTERVAL '1 month'
                 - INTERVAL '1 day'
             )::DATE
           THEN ad.deposit_amount * (
        ad.acct_opn_date::DATE
        - DATE_TRUNC('month', DATE '{ref_date}')::DATE
        + 1
    )
    ELSE 0
    END AS demand_amount
    FROM
        account_data AS ad
    ),
    -- === YAHAN TAK NAYA CTE KHATAM ===
    flow_data AS (
        SELECT
            d.rm_id,
            g.foracid,
            g.schm_code,
            SUM(tdt.flow_amt) AS total_flow_amount
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        INNER JOIN
            tbaadm.tdt AS tdt ON tdt.acid = g.acid AND tdt.flow_code = 'NI'
        WHERE
            tdt.flow_date BETWEEN '{month_start}' AND DATE '{ref_date}'
            AND (
                g.acct_cls_flg <> 'Y'
                OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            )
        GROUP BY
            d.rm_id, g.foracid, g.schm_code
        HAVING
            SUM(tdt.flow_amt) > 0
    ),
    tran_data AS (
        SELECT
            d.rm_id,
            g.foracid,
            g.schm_code,
            SUM(dtt.tran_amt) AS total_tran_amt
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        INNER JOIN
            tbaadm.dtt AS dtt ON dtt.acid = g.acid AND dtt.flow_code = 'NI'
        WHERE
            dtt.value_date BETWEEN '{month_start}' AND DATE '{ref_date}'
            AND (
                g.acct_cls_flg <> 'Y'
                OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            )
        GROUP BY
            d.rm_id, g.foracid, g.schm_code
        HAVING
            SUM(dtt.tran_amt) > 0
    ),
    reference_data AS (
        SELECT
            ed.referencenumber,
            da.user_id AS rm_id
        FROM
            crmuser.entitydocument AS ed
        INNER JOIN
            tbaadm.gam AS g ON ed.orgkey = g.cif_id
        INNER JOIN
            custom.dsaauth AS da ON g.foracid = da.operacc
        WHERE
            ed.doccode = 'PAN'
    )
    SELECT
        ad.rm_id,
        ad.rm_name,
        ad.operacc,
        ad.auth_id,
        ad.auth_role_id AS auth_name,
        ad.cif_id,
        ad.acct_opn_date,
        ad.cif_id_opening_date,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) AS account_age,
        ad.foracid,
        ad.schm_code,
        ad.schm_desc,
        ad.sol_id,
        ad.sol_desc,
        ad.deposit_period_mths,
        ad.deposit_period_days,
        ad.deposit_amount,
        ad.maturity_amount,
        ad.maturity_date,
        ad.acct_cls_date,
        ad.acct_cls_flg,
        COALESCE(fd.total_flow_amount, 0) AS total_flow_amount,
        COALESCE(td.total_tran_amt, 0) AS total_tran_amt,
        COALESCE(dd.demand_amount, 0) AS monthly_demand_amount,   -- === NEW COLUMN ADDED (Step 3) ===
        COALESCE(td.total_tran_amt, 0) AS monthly_collection,
        LEAST(
        ROUND(
            COALESCE(dd.demand_amount, 0) / NULLIF(ad.deposit_amount, 0),2),365) AS monthly_demand_days,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount AS ytd_demand_amount,
        COALESCE(ad.clr_bal_amt, 0) AS ytd_collection,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) AS ytd_demand_days,
        CASE
        WHEN (LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount) = 0
        THEN 0
        ELSE ROUND(
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        )
    END AS ytd_coll_pct,
    CASE
        WHEN (LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount) = 0
        THEN 'DEFAULT'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 100 THEN 'Excess'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 75 THEN 'A'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 50 THEN 'B'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 25 THEN 'C'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 0 THEN 'D'
        ELSE 'DEFAULT'
    END AS colle_category,
        ROUND(
            CASE
                WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 100000 THEN
                    0.035 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
                WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) > 100000
                     AND LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 200000 THEN
                    0.04 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
                ELSE
                    0.05 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
            END
        ) AS commission,
        COALESCE(rd.referencenumber, 'N/A') AS referencenumber
    FROM
        account_data AS ad
    LEFT JOIN
        flow_data AS fd ON ad.rm_id = fd.rm_id AND ad.foracid = fd.foracid AND ad.schm_code = fd.schm_code
    LEFT JOIN
        tran_data AS td ON ad.rm_id = td.rm_id AND ad.foracid = td.foracid AND ad.schm_code = td.schm_code
    LEFT JOIN
        demand_data AS dd ON ad.foracid = dd.foracid AND ad.schm_code = dd.schm_code   -- === NEW JOIN (Step 2) ===
    LEFT JOIN
        reference_data AS rd ON ad.rm_id = rd.rm_id
    WHERE
        (fd.total_flow_amount > 0 OR td.total_tran_amt > 0)
    ORDER BY
        ad.foracid, ad.rm_id, ad.schm_code;
    """

    max_attempts = 3
    for attempt in range(max_attempts):
        conn = get_dr_connection()
        if not conn:
            frappe.log_error("Failed to connect to DR database", "Staff Demand Collection API")
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout TO '180000'")
            cursor.execute(query)
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]

            raw_data = []
            for row in rows:
                row_dict = {}
                for i, val in enumerate(row):
                    col = headers[i]
                    if val is None:
                        row_dict[col] = None
                    elif isinstance(val, (int, float)):
                        row_dict[col] = val
                    elif hasattr(val, 'isoformat'):
                        row_dict[col] = str(val)[:10]
                    else:
                        row_dict[col] = str(val)
                raw_data.append(row_dict)

            print(f"DEBUG [STAFF WISE]: Total records fetched = {len(raw_data)}", flush=True)
            sol_ids = list(set(r["sol_id"] for r in raw_data if r.get("sol_id")))
            branch_map = {}
            if sol_ids:
                branches_map = get_sahayog_branches_cached()
                for sid in sol_ids:
                    if sid in branches_map:
                        b = branches_map[sid]
                        branch_map[sid] = {
                            "zone": b.get("zone") or "Unknown",
                            "region": b.get("region") or "Unknown",
                            "district": b.get("district") or "Unknown",
                            "branch_name": b.get("branch_name") or sid
                        }
                    else:
                        branch_map[sid] = {
                            "zone": "Unknown",
                            "region": "Unknown",
                            "district": "Unknown",
                            "branch_name": sid
                        }

            # Fetch designations for all unique employee IDs in bulk
            emp_ids = set()
            for r in raw_data:
                auth_id = r.get("auth_id")
                if auth_id and auth_id != "Unknown":
                    digits = re.findall(r'\d+', auth_id)
                    if digits:
                        try:
                            emp_id = str(int(''.join(digits)))
                            emp_ids.add(emp_id)
                        except ValueError:
                            pass
            
            designation_map = {}
            if emp_ids:
                employees = frappe.get_all(
                    "Employee",
                    filters={"name": ["in", list(emp_ids)]},
                    fields=["name", "designation"]
                )
                for emp in employees:
                    designation_map[emp.name] = emp.designation or ""

            summary = {}
            for r in raw_data:
                sid = r.get("sol_id")
                if not sid:
                    continue

                br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
                auth_id = r.get("auth_id") or "Unknown"
                auth_name = r.get("auth_name") or "Unknown"

                designation = ""
                if auth_id and auth_id != "Unknown":
                    digits = re.findall(r'\d+', auth_id)
                    if digits:
                        try:
                            emp_id = str(int(''.join(digits)))
                            designation = designation_map.get(emp_id) or ""
                        except ValueError:
                            pass

                key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}||{auth_id}||{auth_name}||{designation}"
                if key not in summary:
                    summary[key] = {
                        "zone": br["zone"],
                        "region": br["region"],
                        "district": br["district"],
                        "sol_id": sid,
                        "sol_desc": br["branch_name"],
                        "auth_id": auth_id,
                        "auth_name": auth_name,
                        "designation": designation,
                        "monthly_demand_amount": 0.0,
                        "monthly_collection": 0.0
                    }

                summary[key]["monthly_demand_amount"] += float(r.get("monthly_demand_amount") or 0)
                summary[key]["monthly_collection"] += float(r.get("monthly_collection") or 0)

            result = sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))
            return result
        except Exception as e:
            frappe.log_error(f"Error executing Staff Demand Collection query (attempt {attempt+1}): {str(e)}", "Staff Demand Collection API")
            conn.close()
            if attempt < max_attempts - 1:
                time.sleep(2)
            else:
                return []


@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_agent_wise_demand_collection_data_old(selected_date=None):
    from custom_report.db_connection import get_dr_connection
    from frappe.utils import getdate
    import datetime
    import time

    if not selected_date:
        selected_date = str(datetime.date.today())

    dt = getdate(selected_date)
    month_start = dt.replace(day=1).strftime("%Y-%m-%d")
    ref_date = dt.strftime("%Y-%m-%d")

    print(f"DEBUG [AGENT WISE]: selected_date passed = {selected_date}", flush=True)
    print(f"DEBUG [AGENT WISE]: month_start calculated = {month_start}", flush=True)
    print(f"DEBUG [AGENT WISE]: ref_date calculated = {ref_date}", flush=True)

    # SQL query uses month_start and ref_date
    query = f"""
    WITH account_data AS (
        SELECT
            d.rm_id,
            g2.emp_name AS rm_name,
            d2.operacc,
            d2.auth_id,
            d2.auth_role_id,
            g.cif_id,
            g.acct_opn_date,
            a2.relationshipopeningdate AS cif_id_opening_date,
            g.foracid,
            g.clr_bal_amt,
            tam.deposit_period_mths,
            tam.deposit_period_days,
            tam.deposit_amount,
            tam.maturity_amount,
            tam.maturity_date,
            g.sol_id,
            sol.sol_desc,
            g.schm_code,
            gsp.schm_desc,
            g.acct_cls_date,
            g.acct_cls_flg
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        LEFT JOIN
            crmuser.accounts AS a2 ON g.cif_id = a2.orgkey
        LEFT JOIN
            tbaadm.sol AS sol ON g.sol_id = sol.sol_id
        LEFT JOIN
            tbaadm.gsp AS gsp ON g.schm_code = gsp.schm_code
        LEFT JOIN
            custom.dsaauth AS d2 ON d.rm_id = d2.user_id
        LEFT JOIN
            tbaadm.get AS g2 ON d2.user_id = g2.emp_id
        LEFT JOIN
            tbaadm.tam AS tam ON g.acid = tam.acid    
        WHERE
            g.acct_cls_flg <> 'Y'
            OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
    ),
    -- === NEW CTE ADD  (Step 1) ===
    demand_data AS (
        SELECT
            ad.foracid,
            ad.schm_code,
            CASE
                -- Condition 1: ac opened before current month AND maturity after current month
                WHEN ad.acct_opn_date::DATE < DATE_TRUNC('month', DATE '{ref_date}')::DATE
              AND ad.maturity_date::DATE >
             (DATE_TRUNC('month', DATE '{ref_date}')
              + INTERVAL '1 month'
              - INTERVAL '1 day')::DATE
               THEN ad.deposit_amount * (
            (
              DATE_TRUNC('month', DATE '{ref_date}')
              + INTERVAL '1 month'
              - INTERVAL '1 day'
            )::DATE
            - DATE_TRUNC('month', DATE '{ref_date}')::DATE
            + 1
           )
               -- Condition 2: maturity falls within current month -> demand till one day before maturity
                WHEN ad.maturity_date::DATE >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            AND ad.maturity_date::DATE <= (
             DATE_TRUNC('month', DATE '{ref_date}')
             + INTERVAL '1 month'
             - INTERVAL '1 day'
           )::DATE
                THEN ad.deposit_amount * (
            ad.maturity_date::DATE
            - DATE_TRUNC('month', DATE '{ref_date}')::DATE
           )
               -- Condition 3: ac opened during current month -> ac age for current month
               -- Condition 3: account opened in current month
               WHEN ad.acct_opn_date::DATE >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
                AND ad.acct_opn_date::DATE <= (
                DATE_TRUNC('month', DATE '{ref_date}')
               + INTERVAL '1 month'
                 - INTERVAL '1 day'
             )::DATE
           THEN ad.deposit_amount * (
        ad.acct_opn_date::DATE
        - DATE_TRUNC('month', DATE '{ref_date}')::DATE
        + 1
    )
    ELSE 0
    END AS demand_amount
    FROM
        account_data AS ad
    ),
    -- === YAHAN TAK NAYA CTE KHATAM ===
    flow_data AS (
        SELECT
            d.rm_id,
            g.foracid,
            g.schm_code,
            SUM(tdt.flow_amt) AS total_flow_amount
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        INNER JOIN
            tbaadm.tdt AS tdt ON tdt.acid = g.acid AND tdt.flow_code = 'NI'
        WHERE
            tdt.flow_date BETWEEN '{month_start}' AND DATE '{ref_date}'
            AND (
                g.acct_cls_flg <> 'Y'
                OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            )
        GROUP BY
            d.rm_id, g.foracid, g.schm_code
        HAVING
            SUM(tdt.flow_amt) > 0
    ),
    tran_data AS (
        SELECT
            d.rm_id,
            g.foracid,
            g.schm_code,
            SUM(dtt.tran_amt) AS total_tran_amt
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        INNER JOIN
            tbaadm.dtt AS dtt ON dtt.acid = g.acid AND dtt.flow_code = 'NI'
        WHERE
            dtt.value_date BETWEEN '{month_start}' AND DATE '{ref_date}'
            AND (
                g.acct_cls_flg <> 'Y'
                OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            )
        GROUP BY
            d.rm_id, g.foracid, g.schm_code
        HAVING
            SUM(dtt.tran_amt) > 0
    ),
    reference_data AS (
        SELECT
            ed.referencenumber,
            da.user_id AS rm_id
        FROM
            crmuser.entitydocument AS ed
        INNER JOIN
            tbaadm.gam AS g ON ed.orgkey = g.cif_id
        INNER JOIN
            custom.dsaauth AS da ON g.foracid = da.operacc
        WHERE
            ed.doccode = 'PAN'
    )
    SELECT
        ad.rm_id,
        ad.rm_name,
        ad.operacc,
        ad.auth_id,
        ad.auth_role_id AS auth_name,
        ad.cif_id,
        ad.acct_opn_date,
        ad.cif_id_opening_date,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) AS account_age,
        ad.foracid,
        ad.schm_code,
        ad.schm_desc,
        ad.sol_id,
        ad.sol_desc,
        ad.deposit_period_mths,
        ad.deposit_period_days,
        ad.deposit_amount,
        ad.maturity_amount,
        ad.maturity_date,
        ad.acct_cls_date,
        ad.acct_cls_flg,
        COALESCE(fd.total_flow_amount, 0) AS total_flow_amount,
        COALESCE(td.total_tran_amt, 0) AS total_tran_amt,
        COALESCE(dd.demand_amount, 0) AS monthly_demand_amount,   -- === NEW COLUMN ADDED (Step 3) ===
        COALESCE(td.total_tran_amt, 0) AS monthly_collection,
        LEAST(
        ROUND(
            COALESCE(dd.demand_amount, 0) / NULLIF(ad.deposit_amount, 0),2),365) AS monthly_demand_days,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount AS ytd_demand_amount,
        COALESCE(ad.clr_bal_amt, 0) AS ytd_collection,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) AS ytd_demand_days,
        CASE
        WHEN (LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount) = 0
        THEN 0
        ELSE ROUND(
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        )
    END AS ytd_coll_pct,
    CASE
        WHEN (LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount) = 0
        THEN 'DEFAULT'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 100 THEN 'Excess'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 75 THEN 'A'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 50 THEN 'B'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 25 THEN 'C'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 0 THEN 'D'
        ELSE 'DEFAULT'
    END AS colle_category,
        ROUND(
            CASE
                WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 100000 THEN
                    0.035 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
                WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) > 100000
                     AND LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 200000 THEN
                    0.04 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
                ELSE
                    0.05 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
            END
        ) AS commission,
        COALESCE(rd.referencenumber, 'N/A') AS referencenumber
    FROM
        account_data AS ad
    LEFT JOIN
        flow_data AS fd ON ad.rm_id = fd.rm_id AND ad.foracid = fd.foracid AND ad.schm_code = fd.schm_code
    LEFT JOIN
        tran_data AS td ON ad.rm_id = td.rm_id AND ad.foracid = td.foracid AND ad.schm_code = td.schm_code
    LEFT JOIN
        demand_data AS dd ON ad.foracid = dd.foracid AND ad.schm_code = dd.schm_code   -- === NEW JOIN (Step 2) ===
    LEFT JOIN
        reference_data AS rd ON ad.rm_id = rd.rm_id
    WHERE
        (fd.total_flow_amount > 0 OR td.total_tran_amt > 0)
    ORDER BY
        ad.foracid, ad.rm_id, ad.schm_code;
    """

    max_attempts = 3
    for attempt in range(max_attempts):
        conn = get_dr_connection()
        if not conn:
            frappe.log_error("Failed to connect to DR database", "Agent Demand Collection API")
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout TO '180000'")
            cursor.execute(query)
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]

            raw_data = []
            for row in rows:
                row_dict = {}
                for i, val in enumerate(row):
                    col = headers[i]
                    if val is None:
                        row_dict[col] = None
                    elif isinstance(val, (int, float)):
                        row_dict[col] = val
                    elif hasattr(val, 'isoformat'):
                        row_dict[col] = str(val)[:10]
                    else:
                        row_dict[col] = str(val)
                raw_data.append(row_dict)

            print(f"DEBUG [AGENT WISE]: Total records fetched = {len(raw_data)}", flush=True)
            sol_ids = list(set(r["sol_id"] for r in raw_data if r.get("sol_id")))
            branch_map = {}
            if sol_ids:
                branches_map = get_sahayog_branches_cached()
                for sid in sol_ids:
                    if sid in branches_map:
                        b = branches_map[sid]
                        branch_map[sid] = {
                            "zone": b.get("zone") or "Unknown",
                            "region": b.get("region") or "Unknown",
                            "district": b.get("district") or "Unknown",
                            "branch_name": b.get("branch_name") or sid
                        }
                    else:
                        branch_map[sid] = {
                            "zone": "Unknown",
                            "region": "Unknown",
                            "district": "Unknown",
                            "branch_name": sid
                        }

            # Fetch designations for all unique employee IDs in bulk
            emp_ids = set()
            for r in raw_data:
                auth_id = r.get("auth_id")
                if auth_id and auth_id != "Unknown":
                    digits = re.findall(r'\d+', auth_id)
                    if digits:
                        try:
                            emp_id = str(int(''.join(digits)))
                            emp_ids.add(emp_id)
                        except ValueError:
                            pass
            
            designation_map = {}
            if emp_ids:
                employees = frappe.get_all(
                    "Employee",
                    filters={"name": ["in", list(emp_ids)]},
                    fields=["name", "designation"]
                )
                for emp in employees:
                    designation_map[emp.name] = emp.designation or ""

            summary = {}
            for r in raw_data:
                sid = r.get("sol_id")
                if not sid:
                    continue

                br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
                rm_id = r.get("rm_id") or "Unknown"
                rm_name = r.get("rm_name") or "Unknown"
                auth_id = r.get("auth_id") or "Unknown"
                auth_name = r.get("auth_name") or "Unknown"

                designation = ""
                if auth_id and auth_id != "Unknown":
                    digits = re.findall(r'\d+', auth_id)
                    if digits:
                        try:
                            emp_id = str(int(''.join(digits)))
                            designation = designation_map.get(emp_id) or ""
                        except ValueError:
                            pass

                key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}||{rm_id}||{rm_name}||{auth_id}||{auth_name}||{designation}"
                if key not in summary:
                    summary[key] = {
                        "zone": br["zone"],
                        "region": br["region"],
                        "district": br["district"],
                        "sol_id": sid,
                        "sol_desc": br["branch_name"],
                        "rm_id": rm_id,
                        "rm_name": rm_name,
                        "auth_id": auth_id,
                        "auth_name": auth_name,
                        "designation": designation,
                        "monthly_demand_amount": 0.0,
                        "monthly_collection": 0.0
                    }

                summary[key]["monthly_demand_amount"] += float(r.get("monthly_demand_amount") or 0)
                summary[key]["monthly_collection"] += float(r.get("monthly_collection") or 0)

            result = sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))
            return result
        except Exception as e:
            frappe.log_error(f"Error executing Agent Demand Collection query (attempt {attempt+1}): {str(e)}", "Agent Demand Collection API")
            conn.close()
            if attempt < max_attempts - 1:
                time.sleep(2)
            else:
                return []


@frappe.whitelist()
def clear_product_wise_report():
    try:
        frappe.db.sql("DELETE FROM `tabProduct Wise Report`")
        frappe.db.commit()
        return True
    except Exception as e:
        frappe.log_error(f"Error truncating Product Wise Report: {str(e)}", "Clear Product Wise Report API")
        return False


def daily_tda_sync():
    import datetime
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    
    try:
        count = get_product_wise_tda(date_str)
        subject = f"Daily TDA Sync Report - {date_str}"
        message = f"Daily TDA Sync completed successfully for date {date_str}.<br>Total records synced: {count}"
    except Exception as e:
        subject = f"Daily TDA Sync Failed - {date_str}"
        message = f"Daily TDA Sync failed for date {date_str}.<br>Error: {str(e)}"
        frappe.log_error(message=frappe.get_traceback(), title="Daily TDA Sync Scheduler Failed")
        
    frappe.sendmail(
        recipients=["talib.s@sahayogmultistate.com", "atul.n@sahayogmultistate.com"],
        subject=subject,
        message=message,
        delayed=False
    )


def daily_casa_sync():
    import datetime
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    
    try:
        count = get_product_wise_casa(date_str)
        subject = f"Daily CASA Sync Report - {date_str}"
        message = f"Daily CASA Sync completed successfully for date {date_str}.<br>Total records synced: {count}"
    except Exception as e:
        subject = f"Daily CASA Sync Failed - {date_str}"
        message = f"Daily CASA Sync failed for date {date_str}.<br>Error: {str(e)}"
        frappe.log_error(message=frappe.get_traceback(), title="Daily CASA Sync Scheduler Failed")
        
    frappe.sendmail(
        recipients=["talib.s@sahayogmultistate.com", "atul.n@sahayogmultistate.com"],
        subject=subject,
        message=message,
        delayed=False
    )

@frappe.whitelist()
def get_raw_demand_collection_data(selected_date=None):
    from custom_report.db_connection import get_dr_connection
    from frappe.utils import getdate
    import datetime
    import time
    
    if not selected_date:
        selected_date = str(datetime.date.today())

    dt = getdate(selected_date)
    month_start = dt.replace(day=1).strftime("%Y-%m-%d")
    ref_date = dt.strftime("%Y-%m-%d")

    query = f"""
    WITH account_data AS (
        SELECT
            d.rm_id,
            g2.emp_name AS rm_name,
            d2.operacc,
            d2.auth_id,
            d2.auth_role_id,
            g.cif_id,
            g.acct_opn_date,
            a2.relationshipopeningdate AS cif_id_opening_date,
            g.foracid,
            g.clr_bal_amt,
            tam.deposit_period_mths,
            tam.deposit_period_days,
            tam.deposit_amount,
            tam.maturity_amount,
            tam.maturity_date,
            g.sol_id,
            sol.sol_desc,
            g.schm_code,
            gsp.schm_desc,
            g.acct_cls_date,
            g.acct_cls_flg
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        LEFT JOIN
            crmuser.accounts AS a2 ON g.cif_id = a2.orgkey
        LEFT JOIN
            tbaadm.sol AS sol ON g.sol_id = sol.sol_id
        LEFT JOIN
            tbaadm.gsp AS gsp ON g.schm_code = gsp.schm_code
        LEFT JOIN
            custom.dsaauth AS d2 ON d.rm_id = d2.user_id
        LEFT JOIN
            tbaadm.get AS g2 ON d2.user_id = g2.emp_id
        LEFT JOIN
            tbaadm.tam AS tam ON g.acid = tam.acid    
        WHERE
            g.acct_cls_flg <> 'Y'
            OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
    ),
    -- === NEW CTE ADD  (Step 1) ===
    demand_data AS (
        SELECT
            ad.foracid,
            ad.schm_code,
            CASE
                -- Condition 1: ac opened before current month AND maturity after current month
                WHEN ad.acct_opn_date::DATE < DATE_TRUNC('month', DATE '{ref_date}')::DATE
              AND ad.maturity_date::DATE >
             (DATE_TRUNC('month', DATE '{ref_date}')
              + INTERVAL '1 month'
              - INTERVAL '1 day')::DATE
               THEN ad.deposit_amount * (
            (
              DATE_TRUNC('month', DATE '{ref_date}')
              + INTERVAL '1 month'
              - INTERVAL '1 day'
            )::DATE
            - DATE_TRUNC('month', DATE '{ref_date}')::DATE
            + 1
           )
               -- Condition 2: maturity falls within current month -> demand till one day before maturity
                WHEN ad.maturity_date::DATE >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            AND ad.maturity_date::DATE <= (
             DATE_TRUNC('month', DATE '{ref_date}')
             + INTERVAL '1 month'
             - INTERVAL '1 day'
           )::DATE
                THEN ad.deposit_amount * (
            ad.maturity_date::DATE
            - DATE_TRUNC('month', DATE '{ref_date}')::DATE
           )
               -- Condition 3: ac opened during current month -> ac age for current month
               -- Condition 3: account opened in current month
               WHEN ad.acct_opn_date::DATE >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
                AND ad.acct_opn_date::DATE <= (
                DATE_TRUNC('month', DATE '{ref_date}')
               + INTERVAL '1 month'
                 - INTERVAL '1 day'
             )::DATE
           THEN ad.deposit_amount * (
        ad.acct_opn_date::DATE
        - DATE_TRUNC('month', DATE '{ref_date}')::DATE
        + 1
    )
    ELSE 0
    END AS demand_amount
    FROM
        account_data AS ad
    ),
    -- === YAHAN TAK NAYA CTE KHATAM ===
    flow_data AS (
        SELECT
            d.rm_id,
            g.foracid,
            g.schm_code,
            SUM(tdt.flow_amt) AS total_flow_amount
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        INNER JOIN
            tbaadm.tdt AS tdt ON tdt.acid = g.acid AND tdt.flow_code = 'NI'
        WHERE
            tdt.flow_date BETWEEN '{month_start}' AND DATE '{ref_date}'
            AND (
                g.acct_cls_flg <> 'Y'
                OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            )
        GROUP BY
            d.rm_id, g.foracid, g.schm_code
        HAVING
            SUM(tdt.flow_amt) > 0
    ),
    tran_data AS (
        SELECT
            d.rm_id,
            g.foracid,
            g.schm_code,
            SUM(dtt.tran_amt) AS total_tran_amt
        FROM
            custom.dsamap AS d
        INNER JOIN
            tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
        INNER JOIN
            tbaadm.dtt AS dtt ON dtt.acid = g.acid AND dtt.flow_code = 'NI'
        WHERE
            dtt.value_date BETWEEN '{month_start}' AND DATE '{ref_date}'
            AND (
                g.acct_cls_flg <> 'Y'
                OR g.acct_cls_date >= DATE_TRUNC('month', DATE '{ref_date}')::DATE
            )
        GROUP BY
            d.rm_id, g.foracid, g.schm_code
        HAVING
            SUM(dtt.tran_amt) > 0
    ),
    reference_data AS (
        SELECT
            ed.referencenumber,
            da.user_id AS rm_id
        FROM
            crmuser.entitydocument AS ed
        INNER JOIN
            tbaadm.gam AS g ON ed.orgkey = g.cif_id
        INNER JOIN
            custom.dsaauth AS da ON g.foracid = da.operacc
        WHERE
            ed.doccode = 'PAN'
    )
    SELECT
        ad.rm_id,
        ad.rm_name,
        ad.operacc,
        ad.auth_id,
        ad.auth_role_id AS auth_name,
        ad.cif_id,
        ad.acct_opn_date,
        ad.cif_id_opening_date,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) AS account_age,
        ad.foracid,
        ad.schm_code,
        ad.schm_desc,
        ad.sol_id,
        ad.sol_desc,
        ad.deposit_period_mths,
        ad.deposit_period_days,
        ad.deposit_amount,
        ad.maturity_amount,
        ad.maturity_date,
        ad.acct_cls_date,
        ad.acct_cls_flg,
        COALESCE(fd.total_flow_amount, 0) AS total_flow_amount,
        COALESCE(td.total_tran_amt, 0) AS total_tran_amt,
        COALESCE(dd.demand_amount, 0) AS monthly_demand_amount,   -- === NEW COLUMN ADDED (Step 3) ===
        COALESCE(td.total_tran_amt, 0) AS monthly_collection,
        LEAST(
        ROUND(
            COALESCE(dd.demand_amount, 0) / NULLIF(ad.deposit_amount, 0),2),365) AS monthly_demand_days,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount AS ytd_demand_amount,
        COALESCE(ad.clr_bal_amt, 0) AS ytd_collection,
        LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) AS ytd_demand_days,
        CASE
        WHEN (LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount) = 0
        THEN 0
        ELSE ROUND(
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        )
    END AS ytd_coll_pct,
    CASE
        WHEN (LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365) * ad.deposit_amount) = 0
        THEN 'DEFAULT'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 100 THEN 'Excess'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 75 THEN 'A'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 50 THEN 'B'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 25 THEN 'C'
        WHEN (
            (
                COALESCE(ad.clr_bal_amt,0)::NUMERIC
                /
                (
                    LEAST(GREATEST(DATE '{ref_date}' - ad.acct_opn_date::DATE,0),365)
                    * ad.deposit_amount
                )
            ) * 100
        ) > 0 THEN 'D'
        ELSE 'DEFAULT'
    END AS colle_category,
        ROUND(
            CASE
                WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 100000 THEN
                    0.035 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
                WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) > 100000
                     AND LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 200000 THEN
                    0.04 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
                ELSE
                    0.05 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
            END
        ) AS commission,
        COALESCE(rd.referencenumber, 'N/A') AS referencenumber
    FROM
        account_data AS ad
    LEFT JOIN
        flow_data AS fd ON ad.rm_id = fd.rm_id AND ad.foracid = fd.foracid AND ad.schm_code = fd.schm_code
    LEFT JOIN
        tran_data AS td ON ad.rm_id = td.rm_id AND ad.foracid = td.foracid AND ad.schm_code = td.schm_code
    LEFT JOIN
        demand_data AS dd ON ad.foracid = dd.foracid AND ad.schm_code = dd.schm_code   -- === NEW JOIN (Step 2) ===
    LEFT JOIN
        reference_data AS rd ON ad.rm_id = rd.rm_id
    WHERE
        (fd.total_flow_amount > 0 OR td.total_tran_amt > 0)
    ORDER BY
        ad.foracid, ad.rm_id, ad.schm_code;
    """
    
    max_attempts = 3
    for attempt in range(max_attempts):
        conn = get_dr_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("SET statement_timeout TO '180000'")
            cursor.execute(query)
            rows = cursor.fetchall()
            headers = [desc[0] for desc in cursor.description]

            raw_data = []
            for row in rows:
                row_dict = {}
                for i, val in enumerate(row):
                    col = headers[i]
                    if val is None:
                        row_dict[col] = None
                    elif isinstance(val, (int, float)):
                        row_dict[col] = val
                    elif hasattr(val, 'isoformat'):
                        row_dict[col] = str(val)[:10]
                    else:
                        row_dict[col] = str(val)
                raw_data.append(row_dict)

            return raw_data
        except Exception as e:
            frappe.log_error(f"Error executing raw demand collection (attempt {attempt+1}): {str(e)}")
            conn.close()
            if attempt < max_attempts - 1:
                time.sleep(2)
            else:
                return []

@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_agent_wise_demand_collection_data(selected_date=None):
    import datetime
    if not selected_date:
        selected_date = str(datetime.date.today())

    records = frappe.db.get_all("DD Tracker Report", filters={"date": selected_date}, fields=["sol_id", "agent_code", "agent_name", "monthly_demand", "monthly_collection"])
    
    if not records:
        return []

    sol_ids = list(set(r.sol_id for r in records if r.sol_id))
    branches_map = get_sahayog_branches_cached()
    branch_map = {}
    for sid in sol_ids:
        b = branches_map.get(sid, {})
        branch_map[sid] = {
            "zone": b.get("zone", "Unknown"),
            "region": b.get("region", "Unknown"),
            "district": b.get("district", "Unknown"),
            "branch_name": b.get("branch_name", sid)
        }

    summary = {}
    for r in records:
        sid = r.sol_id
        if not sid:
            continue
        br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
        rm_id = r.agent_code or "Unknown"
        rm_name = r.agent_name or "Unknown"

        key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}||{rm_id}||{rm_name}"
        if key not in summary:
            summary[key] = {
                "zone": br["zone"],
                "region": br["region"],
                "district": br["district"],
                "sol_id": sid,
                "sol_desc": br["branch_name"],
                "rm_id": rm_id,
                "rm_name": rm_name,
                "monthly_demand_amount": 0.0,
                "monthly_collection": 0.0
            }

        summary[key]["monthly_demand_amount"] += float(r.monthly_demand or 0)
        summary[key]["monthly_collection"] += float(r.monthly_collection or 0)

    result = sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))
    return result

@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_staff_wise_demand_collection_data(selected_date=None):
    import datetime
    import re
    if not selected_date:
        selected_date = str(datetime.date.today())

    records = frappe.db.get_all("DD Tracker Report", filters={"date": selected_date}, fields=["sol_id", "auth_id", "auth_name", "monthly_demand", "monthly_collection"])
    
    if not records:
        return []

    sol_ids = list(set(r.sol_id for r in records if r.sol_id))
    branches_map = get_sahayog_branches_cached()
    branch_map = {}
    for sid in sol_ids:
        b = branches_map.get(sid, {})
        branch_map[sid] = {
            "zone": b.get("zone", "Unknown"),
            "region": b.get("region", "Unknown"),
            "district": b.get("district", "Unknown"),
            "branch_name": b.get("branch_name", sid)
        }

    emp_ids = set()
    for r in records:
        auth_id = r.auth_id
        if auth_id and auth_id != "Unknown":
            digits = re.findall(r'\d+', auth_id)
            if digits:
                try:
                    emp_id = str(int(''.join(digits)))
                    emp_ids.add(emp_id)
                except ValueError:
                    pass
    
    designation_map = {}
    if emp_ids:
        employees = frappe.get_all("Employee", filters={"name": ["in", list(emp_ids)]}, fields=["name", "designation"])
        for emp in employees:
            designation_map[emp.name] = emp.designation or ""

    summary = {}
    for r in records:
        sid = r.sol_id
        if not sid:
            continue
        br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
        auth_id = r.auth_id or "Unknown"
        auth_name = r.auth_name or "Unknown"

        designation = ""
        if auth_id and auth_id != "Unknown":
            digits = re.findall(r'\d+', auth_id)
            if digits:
                try:
                    emp_id = str(int(''.join(digits)))
                    designation = designation_map.get(emp_id) or ""
                except ValueError:
                    pass

        key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}||{auth_id}||{auth_name}||{designation}"
        if key not in summary:
            summary[key] = {
                "zone": br["zone"],
                "region": br["region"],
                "district": br["district"],
                "sol_id": sid,
                "sol_desc": br["branch_name"],
                "auth_id": auth_id,
                "auth_name": auth_name,
                "designation": designation,
                "monthly_demand_amount": 0.0,
                "monthly_collection": 0.0
            }

        summary[key]["monthly_demand_amount"] += float(r.monthly_demand or 0)
        summary[key]["monthly_collection"] += float(r.monthly_collection or 0)

    result = sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))
    return result

@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_bucket_wise_account_mis_data(selected_date=None):
    import datetime
    if not selected_date:
        selected_date = str(datetime.date.today())

    records = frappe.db.get_all("DD Tracker Report", filters={"date": selected_date}, fields=["sol_id", "regular_count", "sma0_count", "sma1_count", "sma2_count", "npa_count", "total_count"])
    
    if not records:
        return {"summary": [], "total_records": 0}

    sol_ids = list(set(r.sol_id for r in records if r.sol_id))
    branches_map = get_sahayog_branches_cached()
    branch_map = {}
    for sid in sol_ids:
        b = branches_map.get(sid, {})
        branch_map[sid] = {
            "zone": b.get("zone", "Unknown"),
            "region": b.get("region", "Unknown"),
            "district": b.get("district", "Unknown"),
            "branch_name": b.get("branch_name", sid)
        }

    summary = {}
    total_recs = 0
    for r in records:
        sid = r.sol_id
        if not sid:
            continue
        br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
        
        key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}"
        if key not in summary:
            summary[key] = {
                "zone": br["zone"],
                "region": br["region"],
                "district": br["district"],
                "sol_id": sid,
                "sol_desc": br["branch_name"],
                "Excess": 0, "A": 0, "B": 0, "C": 0, "D": 0, "DEFAULT": 0,
                "grand_total": 0
            }

        summary[key]["A"] += r.sma0_count or 0
        summary[key]["B"] += r.sma1_count or 0
        summary[key]["C"] += r.sma2_count or 0
        summary[key]["D"] += r.npa_count or 0
        summary[key]["grand_total"] += 1
        total_recs += 1

    result = sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))
    return {"summary": result, "total_records": total_recs}

@frappe.whitelist()
@sahayog_cache(ttl=86400)
def get_new_account_report_data(selected_date=None):
    from frappe.utils import getdate
    import datetime
    import re
    if not selected_date:
        selected_date = str(datetime.date.today())

    dt = getdate(selected_date)

    records = frappe.db.get_all("DD Tracker Report", filters={"date": selected_date}, fields=["sol_id", "auth_id", "auth_name", "amount", "opening_date"])
    
    if not records:
        return []

    sol_ids = list(set(r.sol_id for r in records if r.sol_id))
    branches_map = get_sahayog_branches_cached()
    branch_map = {}
    for sid in sol_ids:
        b = branches_map.get(sid, {})
        branch_map[sid] = {
            "zone": b.get("zone", "Unknown"),
            "region": b.get("region", "Unknown"),
            "district": b.get("district", "Unknown"),
            "branch_name": b.get("branch_name", sid)
        }

    emp_ids = set()
    for r in records:
        auth_id = r.auth_id
        if auth_id and auth_id != "Unknown":
            digits = re.findall(r'\d+', auth_id)
            if digits:
                try:
                    emp_id = str(int(''.join(digits)))
                    emp_ids.add(emp_id)
                except ValueError:
                    pass
    
    designation_map = {}
    if emp_ids:
        employees = frappe.get_all("Employee", filters={"name": ["in", list(emp_ids)]}, fields=["name", "designation"])
        for emp in employees:
            designation_map[emp.name] = emp.designation or ""

    summary = {}
    for r in records:
        sid = r.sol_id
        if not sid:
            continue
            
        opn_dt_str = r.opening_date
        is_new = False
        if opn_dt_str:
            try:
                opn_dt = getdate(opn_dt_str)
                if opn_dt.month == dt.month and opn_dt.year == dt.year:
                    is_new = True
            except Exception:
                pass
                
        if not is_new:
            continue
            
        br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
        auth_id = r.auth_id or "Unknown"
        auth_name = r.auth_name or "Unknown"

        designation = ""
        if auth_id and auth_id != "Unknown":
            digits = re.findall(r'\d+', auth_id)
            if digits:
                try:
                    emp_id = str(int(''.join(digits)))
                    designation = designation_map.get(emp_id) or ""
                except ValueError:
                    pass

        key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}||{auth_id}||{auth_name}||{designation}"
        if key not in summary:
            summary[key] = {
                "zone": br["zone"],
                "region": br["region"],
                "district": br["district"],
                "sol_id": sid,
                "sol_desc": br["branch_name"],
                "auth_id": auth_id,
                "auth_name": auth_name,
                "designation": designation,
                "new_ac": 0,
                "deposit_amount": 0.0
            }

        summary[key]["new_ac"] += 1
        summary[key]["deposit_amount"] += float(r.amount or 0)

    result = sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))
    return result
