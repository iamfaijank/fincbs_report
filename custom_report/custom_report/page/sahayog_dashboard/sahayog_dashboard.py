# sahayog_dashboard.py
# Backend for Sahayog MIS Dashboard with hardcoded category order and proper filtering

import frappe
from frappe import _
from frappe.utils import getdate, formatdate, add_days
import json


@frappe.whitelist()
def get_available_dates():
    """
    Get list of unique dates from Branch Category Report.
    Excludes Sundays and returns last 30 days.
    """
    dates = frappe.db.sql(
        """
        SELECT DISTINCT date 
        FROM `tabBranch Category Report` 
        WHERE date IS NOT NULL 
        ORDER BY date DESC 
        LIMIT 30
        """,
        as_dict=True,
    )

    available_dates = []
    for row in dates:
        date_obj = getdate(row["date"])
        # Exclude Sundays (weekday 6)
        if date_obj.weekday() != 6:
            available_dates.append(
                {
                    "date": str(date_obj),
                    "display": formatdate(date_obj, "EEE dd"),
                    "display_full": formatdate(date_obj, "dd MMM yyyy"),
                    "day_name": formatdate(date_obj, "EEE"),
                    "day_num": date_obj.day,
                    "month": date_obj.month,
                    "year": date_obj.year,
                }
            )

    return available_dates


@frappe.whitelist()
def get_dashboard_data(selected_date=None, filters=None):
    """
    Get dashboard data for selected date with hardcoded category order.
    """
    settings = frappe.get_single("Report Settings")

    if not settings.is_active:
        frappe.throw(_("Data source is not active"))

    # Parse filters if provided
    zone_filter = []
    category_filter = []
    
    if filters:
        try:
            filter_dict = json.loads(filters)
            zone_filter = filter_dict.get("zones", [])
            category_filter = filter_dict.get("categories", [])
        except:
            pass

    # Get latest date if not provided
    if not selected_date:
        dates = get_available_dates()
        if dates:
            selected_date = dates[0]["date"]
        else:
            return []

    selected_date_obj = getdate(selected_date)
    doctype_name = settings.master_doctype or "Branch Category Report"

    # Build filters for branch data
    branch_filters = {"date": selected_date}
    
    # Apply zone filter if specified
    if zone_filter and "all" not in zone_filter:
        branch_filters["zone"] = ["in", zone_filter]
    
    # Apply category filter if specified
    if category_filter and "all" not in category_filter:
        branch_filters["branch_score"] = ["in", category_filter]

    # Fetch data for selected date with filters
    branch_data = frappe.get_all(
        doctype_name,
        filters=branch_filters,
        fields=[
            "zone",
            "region",
            "district",
            "branch",
            "sol_id",
            "achievement",
            "branch_score",
            "branch_category",
            "date",
        ],
    )

    # Get monthly targets
    financial_year = get_financial_year(selected_date)
    monthly_targets = get_monthly_targets(financial_year)

    # Aggregate with hardcoded order
    aggregated = aggregate_with_hardcoded_order(
        branch_data, monthly_targets, selected_date_obj
    )

    return aggregated


def aggregate_with_hardcoded_order(data, monthly_targets, selected_date_obj):
    """
    Aggregate data with hardcoded category order.
    Categories: Pinacle, Master, Accelerator, Starter, Learner, Zero Level
    """
    zone_map = {}
    
    # Hardcoded category order
    CATEGORY_ORDER = [
        "Pinacle",
        "Master", 
        "Accelerator",
        "Starter",
        "Learner",
        "Zero Level"
    ]
    
    # Month mapping
    month_number_to_key = {
        12: "dec",  # December
        1: "jan",   # January
        2: "feb",   # February
        3: "mar",   # March
    }
    
    selected_month = selected_date_obj.month
    current_month_key = month_number_to_key.get(selected_month)

    # Initialize all zones and categories with proper order
    all_zones = sorted(set([row.get("zone") or "Unknown" for row in data]))
    
    for zone_name in all_zones:
        if zone_name not in zone_map:
            zone_map[zone_name] = {}
            
        # Initialize all categories for this zone (even if no data)
        for category in CATEGORY_ORDER:
            zone_map[zone_name][category] = {
                "zone": zone_name,
                "category": category,
                "branch_count": 0,
                "dec": {"tgt": 0.0, "ach": 0.0, "available": False},
                "jan": {"tgt": 0.0, "ach": 0.0, "available": False},
                "feb": {"tgt": 0.0, "ach": 0.0, "available": False},
                "mar": {"tgt": 0.0, "ach": 0.0, "available": False},
                "total": {"tgt": 0.0, "ach": 0.0},
            }

    # Process actual data
    for row in data:
        zone_name = row.get("zone") or "Unknown"
        category = row.get("branch_score") or "Unknown"
        sol_id = str(row.get("sol_id")) if row.get("sol_id") else None

        # Skip if category not in our hardcoded list
        if category not in CATEGORY_ORDER:
            continue

        # Total achievement from selected date record
        total_ach = float(row.get("achievement") or 0)

        # Update category aggregation
        cat_data = zone_map[zone_name][category]
        cat_data["branch_count"] += 1
        cat_data["total"]["ach"] += total_ach

        # Set monthly targets
        for month_key in ["dec", "jan", "feb", "mar"]:
            monthly_tgt = get_monthly_target(sol_id, month_key, monthly_targets)
            cat_data[month_key]["tgt"] += monthly_tgt
            cat_data["total"]["tgt"] += monthly_tgt

        # Set achievement ONLY for current month
        if current_month_key:
            cat_data[current_month_key]["ach"] += total_ach
            cat_data[current_month_key]["available"] = True

    # Flatten to list in proper order
    result = []
    
    # Sort zones: ZONE-1, ZONE-2, ..., ZONE-6, then others
    def zone_sort_key(zone_name):
        if zone_name.startswith("ZONE-"):
            try:
                zone_num = int(zone_name.split("-")[1])
                return (0, zone_num)  # Zones with numbers first
            except:
                return (1, zone_name)
        else:
            return (2, zone_name)  # Other zones last
    
    sorted_zones = sorted(zone_map.keys(), key=zone_sort_key)
    
    for zone_name in sorted_zones:
        for category in CATEGORY_ORDER:
            cat_data = zone_map[zone_name][category]
            # Only include if there's data or branch_count > 0
            if cat_data["branch_count"] > 0 or cat_data["total"]["tgt"] > 0 or cat_data["total"]["ach"] > 0:
                result.append(cat_data)

    return result


@frappe.whitelist()
def get_drill_down_data(zone, category, selected_date=None, filters=None):
    """
    Get branch-level drill-down data with enhanced performance segments.
    Returns branches sorted by achievement and divided into 4 segments.
    """
    settings = frappe.get_single("Report Settings")
    doctype_name = settings.master_doctype or "Branch Category Report"

    if not selected_date:
        dates = get_available_dates()
        if dates:
            selected_date = dates[0]["date"]

    selected_date_obj = getdate(selected_date)

    # Parse filters if provided
    zone_filter = []
    category_filter = []
    
    if filters:
        try:
            filter_dict = json.loads(filters)
            zone_filter = filter_dict.get("zones", [])
            category_filter = filter_dict.get("categories", [])
        except:
            pass

    # Build filters
    filters_dict = {"date": selected_date}
    
    if zone == "ALL":
        filters_dict["branch_score"] = category
    else:
        filters_dict["zone"] = zone
        filters_dict["branch_score"] = category
    
    # Apply additional filters if specified
    if zone_filter and "all" not in zone_filter:
        filters_dict["zone"] = ["in", zone_filter]
    
    if category_filter and "all" not in category_filter:
        filters_dict["branch_score"] = ["in", category_filter]

    # Get branch data
    branches = frappe.get_all(
        doctype_name,
        filters=filters_dict,
        fields=[
            "branch",
            "sol_id",
            "region",
            "district",
            "zone",
            "achievement",
            "branch_score",
            "branch_category",
            "date",
        ],
        order_by="zone asc, branch asc",
    )

    # Get monthly targets
    financial_year = get_financial_year(selected_date)
    monthly_targets = get_monthly_targets(financial_year)

    # Enhance branch data
    month_number_to_key = {12: "dec", 1: "jan", 2: "feb", 3: "mar"}
    selected_month = selected_date_obj.month
    current_month_key = month_number_to_key.get(selected_month)

    branch_list = []
    total_achievement = 0
    total_target = 0
    
    for branch in branches:
        sol_id = str(branch.get("sol_id")) if branch.get("sol_id") else None
        total_ach = float(branch.get("achievement") or 0)

        # Get monthly targets
        dec_tgt = get_monthly_target(sol_id, "dec", monthly_targets)
        jan_tgt = get_monthly_target(sol_id, "jan", monthly_targets)
        feb_tgt = get_monthly_target(sol_id, "feb", monthly_targets)
        mar_tgt = get_monthly_target(sol_id, "mar", monthly_targets)
        
        total_tgt = dec_tgt + jan_tgt + feb_tgt + mar_tgt
        ach_pct = round((total_ach / total_tgt * 100), 2) if total_tgt > 0 else 0
        
        total_achievement += total_ach
        total_target += total_tgt

        # Build branch object
        branch_data = {
            "branch_name": branch.get("branch"),
            "branch": branch.get("branch"),
            "sol_id": sol_id,
            "region": branch.get("region"),
            "district": branch.get("district"),
            "zone": branch.get("zone"),
            "category": branch.get("branch_score"),
            "total_ach": total_ach,
            "yearly_target": total_tgt,
            "ach_pct": ach_pct,
            "dec": {
                "tgt": dec_tgt,
                "ach": total_ach if current_month_key == "dec" else 0,
                "available": current_month_key == "dec",
            },
            "jan": {
                "tgt": jan_tgt,
                "ach": total_ach if current_month_key == "jan" else 0,
                "available": current_month_key == "jan",
            },
            "feb": {
                "tgt": feb_tgt,
                "ach": total_ach if current_month_key == "feb" else 0,
                "available": current_month_key == "feb",
            },
            "mar": {
                "tgt": mar_tgt,
                "ach": total_ach if current_month_key == "mar" else 0,
                "available": current_month_key == "mar",
            },
            "total": {
                "tgt": total_tgt,
                "ach": total_ach,
                "available": True,
            }
        }
        
        branch_list.append(branch_data)

    # Sort branches by achievement percentage (descending)
    branch_list.sort(key=lambda x: x["ach_pct"], reverse=True)
    
    # Calculate segments (Top 25%, Next 25%, Mid 25%, Bottom 25%)
    total_branches = len(branch_list)
    
    # Handle edge cases
    if total_branches == 0:
        segment_size = 0
    elif total_branches <= 4:
        segment_size = 1  # Each segment gets at least 1 branch
    else:
        segment_size = total_branches // 4
    
    # Calculate boundaries with better distribution
    boundaries = []
    remaining = total_branches
    
    for i in range(4):
        if i == 3:  # Last segment gets all remaining branches
            start_idx = sum([b[1] - b[0] for b in boundaries])
            end_idx = total_branches
        else:
            start_idx = i * segment_size
            end_idx = min(start_idx + segment_size, total_branches)
        
        boundaries.append((start_idx, end_idx))
    
    # Calculate segment-wise totals
    segments_data = []
    segment_names = ["TOP 25%", "NEXT 25%", "MID 25%", "BOTTOM 25%"]
    segment_descriptions = [
        "Highest performing branches",
        "Above average performers", 
        "Average performers",
        "Branches needing attention"
    ]
    
    for idx, (start, end) in enumerate(boundaries):
        segment_branches = branch_list[start:end]
        
        # Calculate segment totals
        segment_achievement = sum(b["total_ach"] for b in segment_branches)
        segment_target = sum(b["yearly_target"] for b in segment_branches)
        segment_avg_pct = round(sum(b["ach_pct"] for b in segment_branches) / len(segment_branches), 1) if segment_branches else 0
        
        segments_data.append({
            "segment_name": segment_names[idx],
            "description": segment_descriptions[idx],
            "start_index": start,
            "end_index": end,
            "branch_count": end - start,
            "total_achievement": segment_achievement,
            "total_target": segment_target,
            "avg_achievement_pct": segment_avg_pct,
            "branches": segment_branches
        })
    
    # Calculate overall stats
    overall_avg_pct = round(total_achievement / total_target * 100, 1) if total_target > 0 else 0
    
    # Determine drill-down type
    drill_type = "CATEGORY" if zone == "ALL" else "ZONE"
    drill_title = f"{category} - All Zones" if zone == "ALL" else f"{zone} - {category}"
    
    response = {
        "branches": branch_list,
        "segments": segments_data,
        "metadata": {
            "total_branches": total_branches,
            "total_achievement": total_achievement,
            "total_target": total_target,
            "avg_achievement_pct": overall_avg_pct,
            "selected_category": category,
            "selected_zone": zone if zone != "ALL" else "All Zones",
            "drill_type": drill_type,
            "drill_title": drill_title,
            "selected_date": selected_date,
            "segment_size": segment_size
        }
    }
    
    return response

@frappe.whitelist()
def get_available_zones():
    """Get distinct zones sorted properly (ZONE-1 to ZONE-6 then others)"""
    zones = frappe.db.sql(
        """
        SELECT DISTINCT zone 
        FROM `tabBranch Category Report` 
        WHERE zone IS NOT NULL AND zone != ''
        ORDER BY zone
        """,
        as_dict=True,
    )
    
    # Extract zone names
    zone_list = [z["zone"] for z in zones if z["zone"]]
    
    # Custom sort: ZONE-1, ZONE-2, ..., then others
    def zone_sorter(zone_name):
        if zone_name.startswith("ZONE-"):
            try:
                zone_num = int(zone_name.split("-")[1])
                return (0, zone_num)
            except:
                return (1, zone_name)
        else:
            return (2, zone_name)
    
    return sorted(zone_list, key=zone_sorter)


@frappe.whitelist()
def get_available_categories():
    """Return hardcoded categories in specific order"""
    return [
        "Pinacle",
        "Master", 
        "Accelerator",
        "Starter",
        "Learner",
        "Zero Level"
    ]


def get_financial_year(date_str=None):
    """Get financial year string from date."""
    if not date_str:
        date = getdate()
    else:
        date = getdate(date_str)

    if date.month > 3:
        return f"{date.year}-{date.year + 1}"
    else:
        return f"{date.year - 1}-{date.year}"


def get_monthly_targets(financial_year):
    """Fetch only monthly targets from Target Vs Achivement."""
    monthly = frappe.get_all(
        "Target Vs Achivement",
        filters={"type": "Monthly", "financial_year": financial_year},
        fields=["sol_id", "month", "target"],
    )

    monthly_map = {}
    for m in monthly:
        sol_id = str(m.sol_id) if m.sol_id else None
        month = str(m.month).strip().lower() if m.month else None
        if sol_id and month:
            if sol_id not in monthly_map:
                monthly_map[sol_id] = {}
            monthly_map[sol_id][month] = float(m.target or 0)

    return monthly_map


def get_monthly_target(sol_id, month_key, monthly_targets_map):
    """Get monthly target for a specific sol_id and month."""
    sol_id_str = str(sol_id) if sol_id else None
    mk = str(month_key).strip().lower() if month_key else None

    if sol_id_str and sol_id_str in monthly_targets_map:
        if mk in monthly_targets_map[sol_id_str]:
            return float(monthly_targets_map[sol_id_str][mk])

    return 0.0


@frappe.whitelist()
def get_branch_targets(selected_date=None):
    """Get yearly targets for Branch Targets tab."""
    financial_year = get_financial_year(selected_date)

    targets = frappe.get_all(
        "Target Vs Achivement",
        filters={"type": "Yearly", "financial_year": financial_year},
        fields=["sol_id", "target", "financial_year", "type"],
        order_by="sol_id asc",
        limit=1000,
    )

    return targets


@frappe.whitelist()
def get_summary_stats(selected_date=None, filters=None):
    """Get summary statistics for the dashboard."""
    settings = frappe.get_single("Report Settings")
    
    if not selected_date:
        dates = get_available_dates()
        if dates:
            selected_date = dates[0]["date"]
        else:
            return {}
    
    # Parse filters
    zone_filter = []
    category_filter = []
    
    if filters:
        try:
            filter_dict = json.loads(filters)
            zone_filter = filter_dict.get("zones", [])
            category_filter = filter_dict.get("categories", [])
        except:
            pass
    
    # Get dashboard data
    data = get_dashboard_data(selected_date, filters)
    
    if not data:
        return {}
    
    # Calculate summary stats
    total_branches = 0
    total_target = 0
    total_achievement = 0
    
    for row in data:
        total_branches += row.get("branch_count", 0)
        total_target += row.get("total", {}).get("tgt", 0)
        total_achievement += row.get("total", {}).get("ach", 0)
    
    achievement_percentage = round((total_achievement / total_target * 100), 2) if total_target > 0 else 0
    
    return {
        "total_branches": total_branches,
        "total_target": total_target,
        "total_achievement": total_achievement,
        "achievement_percentage": achievement_percentage,
        "date": selected_date
    }

@frappe.whitelist()
def get_comparison_data(current_date=None, comparison_date=None, mode="daily", filters=None):
    """
    Get comparison data between `current_date` and a computed previous date.

    mode: one of "daily", "weekly", "monthly".
    - daily: previous day
    - weekly: 7 days back
    - monthly: ~30 days back

    Returns merged rows with branch count diffs and indicators (▲/▼/→).
    Works with existing `filters` (zones, categories) passed through to `get_dashboard_data`.
    """
    settings = frappe.get_single("Report Settings")

    if not settings.is_active:
        frappe.throw(_("Data source is not active"))

    # Normalize mode
    mode = (mode or "daily").strip().lower()

    # Determine current date (use latest if not provided)
    if not current_date:
        dates = get_available_dates()
        if dates:
            current_date = dates[0]["date"]
        else:
            frappe.throw(_("No available dates to compare"))

    current_date_obj = getdate(current_date)

    # Compute comparison_date if not provided
    if not comparison_date:
        if mode == "weekly":
            comp_obj = getdate(add_days(current_date_obj, -7))
        elif mode == "monthly":
            comp_obj = getdate(add_days(current_date_obj, -30))
        else:  # default to daily
            comp_obj = getdate(add_days(current_date_obj, -1))

        comparison_date = str(comp_obj)
    else:
        comparison_date = comparison_date

    # Fetch aggregated dashboard data for both dates (keeps filter handling inside)
    current_data = get_dashboard_data(current_date, filters) or []
    comparison_data = get_dashboard_data(comparison_date, filters) or []

    # Build maps keyed by (zone, category)
    def _key(row):
        zone = row.get("zone") or "Unknown"
        category = row.get("category") or row.get("branch_score") or "Unknown"
        return (zone, category)

    current_map = { _key(r): r for r in current_data }
    comp_map = { _key(r): r for r in comparison_data }

    # Union of keys
    all_keys = set(list(current_map.keys()) + list(comp_map.keys()))

    comparison_rows = []
    total_current_branches = 0
    total_previous_branches = 0

    for zone, category in sorted(all_keys, key=lambda x: (x[0] or "", x[1] or "")):
        cur = current_map.get((zone, category))
        prev = comp_map.get((zone, category))

        cur_count = int(cur.get("branch_count", 0)) if cur else 0
        prev_count = int(prev.get("branch_count", 0)) if prev else 0

        diff = cur_count - prev_count
        if diff > 0:
            indicator = "▲"
            diff_display = f"+{diff}"
            color = "green"
        elif diff < 0:
            indicator = "▼"
            diff_display = str(diff)
            color = "red"
        else:
            indicator = "→"
            diff_display = "0"
            color = "grey"

        row = {
            "zone": zone,
            "category": category,
            "current_branch_count": cur_count,
            "previous_branch_count": prev_count,
            "difference": diff,
            "difference_display": diff_display,
            "indicator": indicator,
            "indicator_color": color,
            # carry through totals if available for richer UI usage
            "current_total_tgt": cur.get("total", {}).get("tgt", 0) if cur else 0,
            "current_total_ach": cur.get("total", {}).get("ach", 0) if cur else 0,
            "previous_total_tgt": prev.get("total", {}).get("tgt", 0) if prev else 0,
            "previous_total_ach": prev.get("total", {}).get("ach", 0) if prev else 0,
        }

        comparison_rows.append(row)

        total_current_branches += cur_count
        total_previous_branches += prev_count

    total_diff = total_current_branches - total_previous_branches
    if total_diff > 0:
        overall_indicator = "▲"
        overall_color = "green"
    elif total_diff < 0:
        overall_indicator = "▼"
        overall_color = "red"
    else:
        overall_indicator = "→"
        overall_color = "grey"

    response = {
        "current_date": str(current_date_obj),
        "comparison_date": comparison_date,
        "comparison_mode": mode,
        "current_data": current_data,
        "comparison_data": comparison_data,
        "comparison_rows": comparison_rows,
        "summary": {
            "total_current_branches": total_current_branches,
            "total_previous_branches": total_previous_branches,
            "total_difference": total_diff,
            "overall_indicator": overall_indicator,
            "overall_indicator_color": overall_color,
        }
    }

    return response
@frappe.whitelist()
def get_branch_comparison_detail(current_date=None, comparison_date=None, mode="daily",
                                 zone=None, category=None, filters=None):
    """
    For a given zone+category, return only the *difference* branches (branch-name based):
    - added_branches  : branches present in current_date but not in comparison_date
    - removed_branches: branches present in comparison_date but not in current_date

    Branch identity = only branch name (sol_id change ignore).
    """
    settings = frappe.get_single("Report Settings")
    if not settings.is_active:
        frappe.throw(_("Data source is not active"))

    # --- Normalise mode / dates ---
    mode = (mode or "daily").strip().lower()

    # Current date (latest if not passed)
    if not current_date:
        dates = get_available_dates()
        if dates:
            current_date = dates[0]["date"]
        else:
            frappe.throw(_("No available dates to compare"))

    current_date_obj = getdate(current_date)

    # Comparison date auto-calc if not given
    if not comparison_date:
        if mode == "weekly":
            comp_obj = getdate(add_days(current_date_obj, -7))
        elif mode == "monthly":
            comp_obj = getdate(add_days(current_date_obj, -30))
        else:  # daily
            comp_obj = getdate(add_days(current_date_obj, -1))
        comparison_date = str(comp_obj)

    # --- Parse global filters ---
    zone_filter = []
    category_filter = []
    if filters:
        try:
            filter_dict = json.loads(filters)
            zone_filter = filter_dict.get("zones", []) or []
            category_filter = filter_dict.get("categories", []) or []
        except Exception:
            pass

    doctype_name = settings.master_doctype or "Branch Category Report"

    # Base filters
    current_filters = {"date": current_date}
    comp_filters = {"date": comparison_date}

    # Global zone/category filters (chips)
    if zone_filter and "all" not in [z.lower() for z in zone_filter]:
        current_filters["zone"] = ["in", zone_filter]
        comp_filters["zone"] = ["in", zone_filter]

    if category_filter and "all" not in [c.lower() for c in category_filter]:
        current_filters["branch_score"] = ["in", category_filter]
        comp_filters["branch_score"] = ["in", category_filter]

    # Specific zone / category (indicator click)
    if zone:
        current_filters["zone"] = zone
        comp_filters["zone"] = zone

    if category:
        current_filters["branch_score"] = category
        comp_filters["branch_score"] = category

    # --- Fetch branch data for both dates (same filters, different dates) ---
    # Field names: branch, zone, branch_score, sol_id
    current_branches = frappe.get_all(
        doctype_name,
        filters=current_filters,
        fields=["branch", "zone", "branch_score", "sol_id"],
        order_by="branch asc, sol_id asc",
    )

    comp_branches = frappe.get_all(
        doctype_name,
        filters=comp_filters,
        fields=["branch", "zone", "branch_score", "sol_id"],
        order_by="branch asc, sol_id asc",
    )

    # --- Helper: unique key ONLY by branch name (case-insensitive) ---
    def key_by_branch(row):
        return (row.get("branch") or "").strip().lower()

    # Latest record per branch for display
    current_map = {}
    for row in current_branches:
        k = key_by_branch(row)
        if not k:
            continue
        # keep first or last, doesn't matter much – we just need one row per branch
        current_map[k] = row

    comp_map = {}
    for row in comp_branches:
        k = key_by_branch(row)
        if not k:
            continue
        comp_map[k] = row

    current_keys = set(current_map.keys())
    comp_keys = set(comp_map.keys())

    # Branch-name based differences
    added_keys = current_keys - comp_keys     # branch in current only
    removed_keys = comp_keys - current_keys   # branch in previous only

    # --- Build final lists ---
    added_branches = []
    for k in sorted(added_keys):
        row = current_map[k]
        added_branches.append({
            "sol_id": row.get("sol_id") or "",
            "branch": row.get("branch") or "Unknown",
            "zone": row.get("zone") or "Unknown",
            "category": row.get("branch_score") or "Unknown",
        })

    removed_branches = []
    for k in sorted(removed_keys):
        row = comp_map[k]
        removed_branches.append({
            "sol_id": row.get("sol_id") or "",
            "branch": row.get("branch") or "Unknown",
            "zone": row.get("zone") or "Unknown",
            "category": row.get("branch_score") or "Unknown",
        })

    return {
        "current_date": str(current_date_obj),
        "comparison_date": comparison_date,
        "comparison_mode": mode,
        "zone": zone or "All",
        "category": category or "All",
        "added_branches": added_branches,
        "removed_branches": removed_branches,
        "added_count": len(added_branches),
        "removed_count": len(removed_branches),
        "net_change": len(added_branches) - len(removed_branches),
    }
