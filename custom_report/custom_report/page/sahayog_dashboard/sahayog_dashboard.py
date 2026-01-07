# sahayog_dashboard.py
# Backend for Sahayog MIS Dashboard with dynamic category calculation and target type support

import frappe
from frappe import _
from frappe.utils import getdate, formatdate, add_days
import json


# ============================================================================
# CATEGORY CALCULATION LOGIC (Runtime) - Independent Function
# ============================================================================
def calculate_category(achievement_pct):
    """
    Calculate category based on achievement percentage.
    Pinnacle: >100%
    Master: 80-100%
    Accelerator: 60-80%
    Starter: 40-60%
    Learner: 20-40%
    Zero Level: 0-20%
    """
    if achievement_pct > 100:
        return "Pinnacle"
    elif achievement_pct >= 80:
        return "Master"
    elif achievement_pct >= 60:
        return "Accelerator"
    elif achievement_pct >= 40:
        return "Starter"
    elif achievement_pct >= 20:
        return "Learner"
    else:
        return "Zero Level"


# ============================================================================
# TARGET TYPE HANDLING
# ============================================================================
def get_achievement_field_for_type(target_type):
    """
    Return correct achievement field name based on target type.
    Monthly -> achievement
    Yearly/YTD -> yearly_achievement
    """
    if target_type == "Monthly":
        return "achievement"
    else:  # Yearly or YTD
        return "yearly_achievement"


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
def get_dashboard_data(selected_date=None, filters=None, target_type="Monthly"):
    """
    Get dashboard data for selected date with dynamic category calculation.
    
    Args:
        selected_date: Date to fetch data for
        filters: JSON string with zone and category filters
        target_type: "Monthly" | "Yearly" | "YTD"
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

    # Fetch data for selected date with filters
    # Get both achievement fields
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
            "yearly_achievement",
            "date",
        ],
    )

    # Get targets based on target_type
    financial_year = "2025-2026"
    targets_map = get_targets_by_type(financial_year, target_type, selected_date_obj)

    # Aggregate with dynamic category calculation
    aggregated = aggregate_with_dynamic_categories(
        branch_data, targets_map, selected_date_obj, target_type, category_filter
    )

    return aggregated


def aggregate_with_dynamic_categories(data, targets_map, selected_date_obj, target_type, category_filter=None):
    """
    Aggregate data with runtime category calculation based on achievement %.
    Categories are calculated dynamically based on target vs achievement.
    
    ENHANCED WITH DETAILED CONSOLE LOGGING FOR DEBUGGING
    """
    zone_map = {}
    
    # Hardcoded category order for display
    CATEGORY_ORDER = [
        "Pinnacle",
        "Master", 
        "Accelerator",
        "Starter",
        "Learner",
        "Zero Level"
    ]
    
    # Month mapping for display
    month_number_to_key = {
        12: "dec",
        1: "jan",
        2: "feb",
        3: "mar",
    }
    
    selected_month = selected_date_obj.month
    current_month_key = month_number_to_key.get(selected_month)

    # Initialize all zones
    all_zones = sorted(set([row.get("zone") or "Unknown" for row in data]))
    
    for zone_name in all_zones:
        if zone_name not in zone_map:
            zone_map[zone_name] = {}
            
        # Initialize all categories for this zone
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

    # ========================================================================
    # PROCESS DATA WITH DETAILED LOGGING
    # ========================================================================
    
    category_distribution = {}
    category_branch_details = {}  # Store branch details per category
    branches_without_targets = []
    sample_calculations = []
    
    # Initialize category counters
    for cat in CATEGORY_ORDER:
        category_distribution[cat] = 0
        category_branch_details[cat] = []
    
    for idx, row in enumerate(data):
        zone_name = row.get("zone") or "Unknown"
        sol_id = str(row.get("sol_id")) if row.get("sol_id") else "N/A"
        branch_name = row.get("branch") or "Unknown"

        # Get achievement based on target type
        if target_type == "Monthly":
            total_ach = float(row.get("achievement") or 0)
        else:  # Yearly or YTD
            total_ach = float(row.get("yearly_achievement") or 0)

        # Get target for this branch
        target_data = targets_map.get(sol_id, {})
        total_tgt = target_data.get("total", 0.0)

        # Calculate achievement percentage
        ach_pct = (total_ach / total_tgt * 100) if total_tgt > 0 else 0

        # Calculate category dynamically based on achievement % using our function
        category = calculate_category(ach_pct)
        
        # Track category distribution
        category_distribution[category] += 1
        category_branch_details[category].append({
            "sol_id": sol_id,
            "branch": branch_name,
            "zone": zone_name,
            "target": total_tgt,
            "achievement": total_ach,
            "ach_pct": round(ach_pct, 2)
        })
        
        # Track branches without targets
        if total_tgt == 0:
            branches_without_targets.append({
                "sol_id": sol_id,
                "branch": branch_name,
                "zone": zone_name,
                "achievement": total_ach
            })
        
        # Collect sample calculations (first 3 branches per zone)
        if len([s for s in sample_calculations if s["zone"] == zone_name]) < 3:
            sample_calculations.append({
                "zone": zone_name,
                "sol_id": sol_id,
                "branch": branch_name,
                "target": total_tgt,
                "achievement": total_ach,
                "ach_pct": round(ach_pct, 2),
                "category": category
            })

        # Apply category filter if specified
        if category_filter and "all" not in category_filter and category not in category_filter:
            continue

        # Update category aggregation
        cat_data = zone_map[zone_name][category]
        cat_data["branch_count"] += 1
        cat_data["total"]["ach"] += total_ach
        cat_data["total"]["tgt"] += total_tgt

        # Set monthly breakdown from targets
        for month_key in ["dec", "jan", "feb", "mar"]:
            monthly_tgt = target_data.get(month_key, 0.0)
            cat_data[month_key]["tgt"] += monthly_tgt

        # Set achievement for current month only
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
                return (0, zone_num)
            except:
                return (1, zone_name)
        else:
            return (2, zone_name)
    
    sorted_zones = sorted(zone_map.keys(), key=zone_sort_key)
    
    for zone_name in sorted_zones:
        for category in CATEGORY_ORDER:
            cat_data = zone_map[zone_name][category]
            # Only include if there's data
            if cat_data["branch_count"] > 0 or cat_data["total"]["tgt"] > 0 or cat_data["total"]["ach"] > 0:
                result.append(cat_data)

    return result


def get_targets_by_type(financial_year, target_type, selected_date_obj):
    """
    Fetch targets based on type (Monthly, Yearly, YTD).
    Returns a map: sol_id -> {dec, jan, feb, mar, total}
    
    For Monthly: Month-wise targets
    For Yearly/YTD: Total target shown in current month only
    """
    targets_map = {}
    
    # Get current month key
    month_number_to_key = {12: "dec", 1: "jan", 2: "feb", 3: "mar"}
    current_month_key = month_number_to_key.get(selected_date_obj.month)
    
    if target_type == "Monthly":
        # Fetch monthly targets and aggregate them
        monthly_targets = frappe.get_all(
            "Target Vs Achivement",
            filters={"type": "Monthly", "financial_year": financial_year},
            fields=["sol_id", "target", "month"],
        )
        
        for t in monthly_targets:
            sol_id = str(t.sol_id) if t.sol_id else None
            if not sol_id:
                continue
                
            if sol_id not in targets_map:
                targets_map[sol_id] = {
                    "dec": 0.0,
                    "jan": 0.0,
                    "feb": 0.0,
                    "mar": 0.0,
                    "total": 0.0,
                }

            target_value = float(t.target or 0)
            month = str(t.month).strip().upper() if t.month else None
            
            # Map month to key
            month_map = {"DEC": "dec", "JAN": "jan", "FEB": "feb", "MAR": "mar"}
            
            if month and month in month_map:
                month_key = month_map[month]
                targets_map[sol_id][month_key] = target_value
                targets_map[sol_id]["total"] += target_value
                
    else:
        # Fetch Yearly or YTD targets
        yearly_targets = frappe.get_all(
            "Target Vs Achivement",
            filters={"type": target_type, "financial_year": financial_year},
            fields=["sol_id", "target"],
        )
        
        for t in yearly_targets:
            sol_id = str(t.sol_id) if t.sol_id else None
            if not sol_id:
                continue
                
            if sol_id not in targets_map:
                targets_map[sol_id] = {
                    "dec": 0.0,
                    "jan": 0.0,
                    "feb": 0.0,
                    "mar": 0.0,
                    "total": 0.0,
                }

            target_value = float(t.target or 0)
            targets_map[sol_id]["total"] = target_value
            
            # For Yearly/YTD: Show total target in current month column only
            if current_month_key:
                targets_map[sol_id][current_month_key] = target_value

    return targets_map


# [CONTINUATION OF sahayog_dashboard.py]

@frappe.whitelist()
def get_drill_down_data(zone, category, selected_date=None, filters=None, target_type="Monthly"):
    """
    Get branch-level drill-down data with dynamic category calculation.
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
    
    if zone != "ALL":
        filters_dict["zone"] = zone
    
    # Apply additional filters if specified
    if zone_filter and "all" not in zone_filter:
        filters_dict["zone"] = ["in", zone_filter]

    # Get branch data with both achievement fields
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
            "yearly_achievement",
            "date",
        ],
        order_by="zone asc, branch asc",
    )

    # Get targets based on type
    financial_year = get_financial_year(selected_date)
    targets_map = get_targets_by_type(financial_year, target_type, selected_date_obj)

    # Month mapping
    month_number_to_key = {12: "dec", 1: "jan", 2: "feb", 3: "mar"}
    selected_month = selected_date_obj.month
    current_month_key = month_number_to_key.get(selected_month)

    branch_list = []
    total_achievement = 0
    total_target = 0
    
    for branch in branches:
        sol_id = str(branch.get("sol_id")) if branch.get("sol_id") else None
        
        # Get achievement based on target type
        if target_type == "Monthly":
            total_ach = float(branch.get("achievement") or 0)
        else:  # Yearly or YTD
            total_ach = float(branch.get("yearly_achievement") or 0)

        # Get targets
        target_data = targets_map.get(sol_id, {})
        total_tgt = target_data.get("total", 0.0)
        
        # Calculate achievement percentage
        ach_pct = round((total_ach / total_tgt * 100), 2) if total_tgt > 0 else 0
        
        # Calculate category dynamically using our function
        branch_category = calculate_category(ach_pct)

        # Filter by category if drilling down by category
        if category != "ALL" and branch_category != category:
            continue
        
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
            "category": branch_category,
            "total_ach": total_ach,
            "yearly_target": total_tgt,
            "ach_pct": ach_pct,
            "dec": {
                "tgt": target_data.get("dec", 0.0),
                "ach": total_ach if current_month_key == "dec" else 0,
                "available": current_month_key == "dec",
            },
            "jan": {
                "tgt": target_data.get("jan", 0.0),
                "ach": total_ach if current_month_key == "jan" else 0,
                "available": current_month_key == "jan",
            },
            "feb": {
                "tgt": target_data.get("feb", 0.0),
                "ach": total_ach if current_month_key == "feb" else 0,
                "available": current_month_key == "feb",
            },
            "mar": {
                "tgt": target_data.get("mar", 0.0),
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
    
    if total_branches == 0:
        segment_size = 0
    elif total_branches <= 4:
        segment_size = 1
    else:
        segment_size = total_branches // 4
    
    boundaries = []
    for i in range(4):
        if i == 3:
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
    
    overall_avg_pct = round(total_achievement / total_target * 100, 1) if total_target > 0 else 0
    
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
            "segment_size": segment_size,
            "target_type": target_type,
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
    
    zone_list = [z["zone"] for z in zones if z["zone"]]
    
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
        "Pinnacle",
        "Master", 
        "Accelerator",
        "Starter",
        "Learner",
        "Zero Level"
    ]


def get_financial_year(date_str=None):
    """Get financial year string (hardcoded to 2025-2026)."""
    # Hardcoded for current financial year
    return "2025-2026"


@frappe.whitelist()
def get_summary_stats(selected_date=None, filters=None, target_type="Monthly"):
    """Get summary statistics for the dashboard."""
    if not selected_date:
        dates = get_available_dates()
        if dates:
            selected_date = dates[0]["date"]
        else:
            return {}
    
    # Get dashboard data with target type
    data = get_dashboard_data(selected_date, filters, target_type)
    
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
        "date": selected_date,
        "target_type": target_type,
    }


# ============================================================================
# ENHANCED COMPARISON FUNCTIONS WITH DETAILED DEBUGGING
# ============================================================================

@frappe.whitelist()
def get_comparison_data(current_date=None, comparison_date=None, mode="daily", filters=None, target_type="Monthly"):
    """
    Get comparison data between dates with ENHANCED DEBUGGING.
    """
    settings = frappe.get_single("Report Settings")

    if not settings.is_active:
        frappe.throw(_("Data source is not active"))

    mode = (mode or "daily").strip().lower()

    # Get available dates to ensure we only compare against valid, existing data points
    available_rows = get_available_dates()
    available_dates = [d["date"] for d in available_rows] if available_rows else []

    if not available_dates:
        frappe.throw(_("No available dates to compare"))

    # Ensure current_date is a valid, available date
    if not current_date or current_date not in available_dates:
        current_date = available_dates[0]

    # Calculate a valid comparison_date using the list of available dates
    if not comparison_date:
        try:
            current_idx = available_dates.index(current_date)
        except ValueError:
            current_idx = 0

        steps = 1
        if mode == "weekly":
            steps = 7
        elif mode == "monthly":
            # Approximate a month as 30 steps, but ensure we don't go out of bounds
            steps = 30
        
        # available_dates is sorted DESC, so adding to index goes back in time
        comp_idx = min(current_idx + steps, len(available_dates) - 1)
        comparison_date = available_dates[comp_idx]

    current_date_obj = getdate(current_date)

    # Fetch data with target type
    current_data = get_dashboard_data(current_date, filters, target_type) or []
    
    comparison_data = get_dashboard_data(comparison_date, filters, target_type) or []

    def _key(row):
        zone = row.get("zone") or "Unknown"
        category = row.get("category") or "Unknown"
        return (zone, category)

    current_map = {_key(r): r for r in current_data}
    comp_map = {_key(r): r for r in comparison_data}

    current_category_totals = {}
    for (zone, category), row in sorted(current_map.items()):
        count = row.get("branch_count", 0)
        if category not in current_category_totals:
            current_category_totals[category] = 0
        current_category_totals[category] += count
    
    comp_category_totals = {}
    for (zone, category), row in sorted(comp_map.items()):
        count = row.get("branch_count", 0)
        if category not in comp_category_totals:
            comp_category_totals[category] = 0
        comp_category_totals[category] += count

    CATEGORY_ORDER = ["Pinnacle", "Master", "Accelerator", "Starter", "Learner", "Zero Level"]
    emoji_map = {
        "Pinnacle": "🏆",
        "Master": "⭐",
        "Accelerator": "🚀",
        "Starter": "🌱",
        "Learner": "📚",
        "Zero Level": "⚠️"
    }
    
    all_keys = set(list(current_map.keys()) + list(comp_map.keys()))

    comparison_rows = []
    total_current_branches = 0
    total_previous_branches = 0

    for zone, category in sorted(all_keys):
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

    return {
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
        },
        "target_type": target_type,
    }


@frappe.whitelist()
def get_branch_comparison_detail(
    current_date=None,
    comparison_date=None,
    mode="daily",
    zone=None,
    category=None,
    filters=None,
    target_type="Monthly",
):
    """
    Returns branches equal to net_change count with their previous categories.
    """
    settings = frappe.get_single("Report Settings")
    if not settings.is_active:
        frappe.throw("Data source is not active")

    mode = (mode or "daily").strip().lower()
    doctype_name = settings.master_doctype or "Branch Category Report"

    available_rows = get_available_dates()
    available_dates = [d["date"] for d in available_rows] if available_rows else []
    if not available_dates:
        frappe.throw("No available dates to compare")

    if not current_date:
        current_date = available_dates[0]
    
    current_date_obj = getdate(current_date)

    # Calculate comparison date
    if not comparison_date:
        def find_index_for_date(date_str: str) -> int:
            if date_str in available_dates:
                return available_dates.index(date_str)
            return 0

        steps = 1
        if mode == "weekly":
            steps = 7
        elif mode == "monthly":
            steps = 30

        cur_idx = find_index_for_date(current_date)
        comp_idx = min(cur_idx + steps, len(available_dates) - 1)
        comparison_date = available_dates[comp_idx]

    comparison_date_obj = getdate(comparison_date)

    # Helper: Build branch map with categories
    def build_branch_map(rows, date_obj_for_map):
        branch_map = {}
        financial_year = get_financial_year(date_obj_for_map.strftime("%Y-%m-%d"))
        targets_map = get_targets_by_type(financial_year, target_type, date_obj_for_map)
        
        for r in rows:
            sol_id = str(r.get("sol_id")) if r.get("sol_id") else None
            
            if target_type == "Monthly":
                total_ach = float(r.get("achievement") or 0)
            else:
                total_ach = float(r.get("yearly_achievement") or 0)
            
            target_data = targets_map.get(sol_id, {})
            total_tgt = target_data.get("total", 0.0)
            ach_pct = (total_ach / total_tgt * 100) if total_tgt > 0 else 0
            branch_category = calculate_category(ach_pct)
            
            branch_key = (r.get("branch") or "").strip().lower()
            if not branch_key:
                continue
            
            branch_map[branch_key] = {
                "sol_id": sol_id,
                "branch": r.get("branch"),
                "zone": r.get("zone"),
                "category": branch_category,
            }
        
        return branch_map

    # Build filters
    def build_filters(base_date: str) -> dict:
        flt = {"date": base_date}
        if zone and zone != "ALL":
            flt["zone"] = zone
        return flt

    fields = ["branch", "zone", "sol_id", "achievement", "yearly_achievement"]

    current_rows = frappe.get_all(doctype_name, filters=build_filters(current_date), fields=fields)
    comp_rows = frappe.get_all(doctype_name, filters=build_filters(comparison_date), fields=fields)

    # Build maps with ALL branches (not filtered by category yet)
    current_map_all = build_branch_map(current_rows, current_date_obj)
    comp_map_all = build_branch_map(comp_rows, comparison_date_obj)

    # Filter by selected category
    if category and category != "ALL":
        current_in_category = {k: v for k, v in current_map_all.items() if v["category"] == category}
        comp_in_category = {k: v for k, v in comp_map_all.items() if v["category"] == category}
    else:
        current_in_category = current_map_all
        comp_in_category = comp_map_all

    # Calculate net change
    net_change = len(current_in_category) - len(comp_in_category)
    
    # ============================================================
    # BUILD RESULT: Return branches with previous category info
    # ============================================================
    result_branches = []
    
    if net_change > 0:
        # More branches now - show ADDED ones
        current_keys = set(current_in_category.keys())
        comp_keys = set(comp_in_category.keys())
        added_keys = current_keys - comp_keys
        
        for key in sorted(added_keys):
            current_branch = current_in_category[key]
            
            # Check if branch existed in previous date (but in different category)
            previous_category = "Not in category"
            if key in comp_map_all:
                previous_category = comp_map_all[key]["category"]
            
            result_branches.append({
                "sol_id": current_branch["sol_id"],
                "branch": current_branch["branch"],
                "zone": current_branch["zone"],
                "current_category": current_branch["category"],
                "previous_category": previous_category,
                "change_type": "added",
            })
    
    elif net_change < 0:
        # Fewer branches now - show REMOVED ones
        current_keys = set(current_in_category.keys())
        comp_keys = set(comp_in_category.keys())
        removed_keys = comp_keys - current_keys
        
        for key in sorted(removed_keys):
            previous_branch = comp_in_category[key]
            
            # Check if branch still exists (but in different category)
            current_category = "Left category"
            if key in current_map_all:
                current_category = current_map_all[key]["category"]
            
            result_branches.append({
                "sol_id": previous_branch["sol_id"],
                "branch": previous_branch["branch"],
                "zone": previous_branch["zone"],
                "previous_category": previous_branch["category"],
                "current_category": current_category,
                "change_type": "removed",
            })
    
    return {
        "branches": result_branches,
        "count": len(result_branches),
        "net_change": net_change,
        "target_type": target_type,
    }

@frappe.whitelist()
def get_branch_targets(selected_date=None):
    """Get all targets for Branch Targets tab - shows all types."""
    financial_year = get_financial_year(selected_date)

    targets = frappe.get_all(
        "Target Vs Achivement",
        filters={"financial_year": financial_year},
        fields=["sol_id", "target", "financial_year", "type", "month"],
        order_by="sol_id asc, type asc",
        limit=5000,
    )

    return targets

@frappe.whitelist()
def get_branch_profile(sol_id, selected_date=None):
    """
    Get complete branch profile using sol_id.
    
    Data Sources:
    1. Sahayog Branch → branch basic details
    2. Branch Category Report → achievement, yearly_achievement
    3. Target Vs Achivement → targets (Monthly, Yearly, YTD)
    
    Also calculates performance category based on achievement %.
    """
    
    if not sol_id:
        frappe.throw("SOL ID is required")
    
    # =====================================================
    # 1. Get Branch Master Data (Sahayog Branch)
    # =====================================================
    branch_master = frappe.db.get_value(
        "Sahayog Branch",
        {"sol_id": sol_id},
        ["branch", "zone", "region", "district", "state"],
        as_dict=True
    )
    
    if not branch_master:
        frappe.throw(f"Branch with SOL ID {sol_id} not found in Sahayog Branch")
    
    # =====================================================
    # 2. Get Selected Date
    # =====================================================
    if not selected_date:
        dates = get_available_dates()
        selected_date = dates[0]["date"] if dates else None
    
    selected_date_obj = getdate(selected_date)
    
    # =====================================================
    # 3. Get Achievement Data (Branch Category Report)
    # =====================================================
    achievement_data = frappe.db.get_value(
        "Branch Category Report",
        filters={"sol_id": sol_id, "date": selected_date},
        fieldname=["achievement", "yearly_achievement", "branch_score"],
        as_dict=True
    )
    
    current_achievement = float(achievement_data.get("achievement") or 0) if achievement_data else 0
    yearly_achievement = float(achievement_data.get("yearly_achievement") or 0) if achievement_data else 0
    stored_category = achievement_data.get("branch_score") if achievement_data else "Unknown"
    
    # =====================================================
    # 4. Get Financial Year
    # =====================================================
    financial_year = get_financial_year(selected_date)
    
    # =====================================================
    # 5. Get ALL Targets from Target Vs Achivement
    # =====================================================
    target_records = frappe.get_all(
        "Target Vs Achivement",
        filters={
            "sol_id": sol_id,
            "financial_year": financial_year
        },
        fields=["type", "month", "target"],
        order_by="type, month"
    )
    
    # =====================================================
    # 6. Parse Target Records by Type
    # =====================================================
    monthly_targets_map = {}
    yearly_target = 0.0
    ytd_target = 0.0
    
    for rec in target_records:
        rec_type = rec.get("type", "").strip()
        
        if rec_type == "Monthly":
            month_name = rec.get("month", "").strip()
            target_val = float(rec.get("target") or 0)
            monthly_targets_map[month_name.upper()] = target_val
        
        elif rec_type == "Yearly":
            yearly_target = float(rec.get("target") or 0)
        
        elif rec_type == "YTD":
            ytd_target = float(rec.get("target") or 0)
    
    # =====================================================
    # 7. Build Monthly Data Structure
    # =====================================================
    month_data = {
        "dec": {"tgt": monthly_targets_map.get("DECEMBER", 0), "ach": 0},
        "jan": {"tgt": monthly_targets_map.get("JANUARY", 0), "ach": 0},
        "feb": {"tgt": monthly_targets_map.get("FEBRUARY", 0), "ach": 0},
        "mar": {"tgt": monthly_targets_map.get("MARCH", 0), "ach": 0}
    }
    
    # Set achievement for current month only
    month_number_to_key = {12: "dec", 1: "jan", 2: "feb", 3: "mar"}
    current_month_key = month_number_to_key.get(selected_date_obj.month)
    
    if current_month_key:
        month_data[current_month_key]["ach"] = current_achievement
    
    # =====================================================
    # 8. Calculate Percentages
    # =====================================================
    yearly_pct = round((yearly_achievement / yearly_target * 100), 2) if yearly_target > 0 else 0
    ytd_pct = round((yearly_achievement / ytd_target * 100), 2) if ytd_target > 0 else 0
    
    # Current month percentage
    current_month_target = month_data.get(current_month_key, {}).get("tgt", 0) if current_month_key else 0
    current_month_pct = round((current_achievement / current_month_target * 100), 2) if current_month_target > 0 else 0
    
    # =====================================================
    # 9. Calculate Performance Category
    # =====================================================
    # Based on yearly achievement percentage
    calculated_category = calculate_performance_category(yearly_pct)
    
    # =====================================================
    # 10. Build Response
    # =====================================================
    return {
        "sol_id": sol_id,
        "branch": branch_master.get("branch"),
        "zone": branch_master.get("zone"),
        "region": branch_master.get("region"),
        "district": branch_master.get("district"),
        "state": branch_master.get("state"),
        "category": stored_category,  # Original category from Branch Category Report
        "calculated_category": calculated_category,  # Calculated based on performance
        "selected_date": selected_date,
        
        # Monthly breakdown
        "monthly": month_data,
        
        # Current month summary
        "current_month": {
            "month": current_month_key.upper() if current_month_key else "N/A",
            "target": current_month_target,
            "achievement": current_achievement,
            "percentage": current_month_pct
        },
        
        # Yearly data
        "yearly": {
            "target": yearly_target,
            "achievement": yearly_achievement,
            "percentage": yearly_pct
        },
        
        # YTD data
        "ytd": {
            "target": ytd_target,
            "achievement": yearly_achievement,
            "percentage": ytd_pct
        }
    }


def calculate_performance_category(percentage):
    """
    Calculate performance category based on achievement percentage.
    
    Categories:
    - Pinacle: >= 100%
    - Master: 75% - 99%
    - Accelerator: 50% - 74%
    - Starter: 25% - 49%
    - Learner: 10% - 24%
    - Zero Level: < 10%
    """
    if percentage >= 100:
        return "Pinacle"
    elif percentage >= 75:
        return "Master"
    elif percentage >= 50:
        return "Accelerator"
    elif percentage >= 25:
        return "Starter"
    elif percentage >= 10:
        return "Learner"
    else:
        return "Zero Level"
    



@frappe.whitelist(allow_guest=True)
def get_fy_master_data_dummy(financial_year="2025-2026"):
    """
    DUMMY API for testing FY data structure.
    Returns sample nested data: FY → Month → Date → Branches

    Test URL: 
    http://localhost:8000/api/method/custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_fy_master_data_dummy?financial_year=2025-2026
    """

    # Dummy branch data generator
    def generate_dummy_branches(date_str, count=10):
        """Generate dummy branch data for testing"""
        branches = []
        zones = ["ZONE-1", "ZONE-2", "ZONE-3", "ZONE-4", "ZONE-5", "ZONE-6"]
        categories = ["Pinnacle", "Master", "Accelerator", "Starter", "Learner", "Zero Level"]

        for i in range(1, count + 1):
            zone_idx = (i - 1) % len(zones)
            cat_idx = (i - 1) % len(categories)

            monthly_target = 100000 + (i * 10000)
            monthly_achievement = int(monthly_target * (0.6 + (i % 5) * 0.08))
            ach_pct = round((monthly_achievement / monthly_target * 100), 2)

            branches.append({
                "sol_id": f"00{i:03d}",
                "branch": f"Branch {i:03d}",
                "zone": zones[zone_idx],
                "region": f"Region {zone_idx + 1}",
                "district": f"District {zone_idx + 1}",
                "monthly_target": monthly_target,
                "monthly_achievement": monthly_achievement,
                "yearly_target": monthly_target * 12,
                "yearly_achievement": monthly_achievement * 6,
                "ach_pct": ach_pct,
                "category": categories[cat_idx]
            })

        return branches

    # Generate dummy months data
    months_data = {}

    # Parse FY
    fy_parts = financial_year.split("-")
    start_year = int(fy_parts[0])
    end_year = int(fy_parts[1])

    # Only generate data for DEC and JAN (for testing)
    month_configs = [
        ("DEC", 12, start_year, 25),  # 25 dates in December
        ("JAN", 1, end_year, 5),       # 5 dates in January (current month)
    ]

    for month_name, month_num, year, total_dates in month_configs:
        dates_data = {}

        # Generate dates for this month
        for day in range(1, total_dates + 1):
            date_str = f"{year}-{month_num:02d}-{day:02d}"

            # Generate 150 dummy branches for each date
            branches = generate_dummy_branches(date_str, count=150)
            dates_data[date_str] = branches

        # Calculate month summary (using last date)
        last_date = f"{year}-{month_num:02d}-{total_dates:02d}"
        last_date_branches = dates_data[last_date]

        # Category distribution
        category_distribution = {
            "Pinnacle": 0,
            "Master": 0,
            "Accelerator": 0,
            "Starter": 0,
            "Learner": 0,
            "Zero Level": 0
        }

        total_target = 0
        total_achievement = 0

        for branch in last_date_branches:
            cat = branch["category"]
            category_distribution[cat] += 1
            total_target += branch["monthly_target"]
            total_achievement += branch["monthly_achievement"]

        avg_ach_pct = round((total_achievement / total_target * 100), 2) if total_target > 0 else 0

        # Store month data
        months_data[month_name] = {
            "month_name": month_name,
            "month_num": month_num,
            "year": year,
            "dates": dates_data,
            "summary": {
                "total_dates": total_dates,
                "total_branches": len(last_date_branches),
                "total_target": total_target,
                "total_achievement": total_achievement,
                "avg_ach_pct": avg_ach_pct,
                "last_date": last_date,
                "category_distribution": category_distribution
            }
        }

    # FY summary
    total_branches_fy = 150
    overall_ach_pct = sum([m["summary"]["avg_ach_pct"] for m in months_data.values()]) / len(months_data)

    # Final response
    return {
        "status": "success",
        "financial_year": financial_year,
        "months": months_data,
        "fy_summary": {
            "total_months": len(months_data),
            "total_branches": total_branches_fy,
            "overall_achievement_pct": round(overall_ach_pct, 2)
        }
    }
# ============================================================================
# SAHAYOG DASHBOARD API - WITH MONTH-WISE CATEGORY TRACKING
# Version: 3.0.0 | Added: Month-wise category calculation for each branch
# ============================================================================


import frappe
from frappe import _
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


@frappe.whitelist(allow_guest=True)
def get_fy_master_data_actual(
    financial_year: str = "2025-2026",
    filters: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get FY Master Data with DUAL GROUPING + MONTH-WISE BRANCH DETAILS.

    Returns:
    1. grouped_by_zone: {"ZONE-1": {"Pinnacle": {...}}}
    2. grouped_by_category: {"Pinnacle": {"ZONE-1": {...}}}
    3. branch_details: [{branch_code, zone, region, monthly_data: {APR: {category, target, ach}}}]

    ✨ NEW: Each month has its own category for each branch
    """

    start_time = datetime.now()

    try:
        # Validation
        validated_fy = _validate_financial_year(financial_year)
        parsed_filters = _parse_and_validate_filters(filters)
        _check_user_permissions()

        # Configuration
        settings = _get_validated_settings()
        doctype_name = settings.master_doctype or "Branch Category Report"

        # Get FY structure
        start_year, end_year = validated_fy
        fy_months = _get_fy_month_structure(start_year, end_year)

        # Get all targets (optimized)
        targets_map = _fetch_all_targets_optimized(f"{start_year}-{end_year}")

        # ✨ Build months data with MONTH-WISE CATEGORY TRACKING
        months_data, consolidated_branches = _build_months_data_with_category_tracking(
            fy_months=fy_months,
            doctype_name=doctype_name,
            targets_map=targets_map,
            zone_filter=parsed_filters["zones"],
            category_filter=parsed_filters["categories"]
        )

        # Calculate FY summary
        fy_summary = _calculate_fy_summary(months_data)

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        response = {
            "status": "success",
            "data": {
                "financial_year": f"{start_year}-{end_year}",
                "months": months_data,
                "consolidated_branches": consolidated_branches,  # ✨ NEW
                "fy_summary": fy_summary
            },
            "meta": {
                "total_records": len(consolidated_branches),
                "execution_time_ms": round(execution_time, 2),
                "timestamp": datetime.now().isoformat(),
                "api_version": "3.0.0"
            }
        }

        logger.info(
            f"API Success: FY={validated_fy}, Time={execution_time:.2f}ms, "
            f"Branches={len(consolidated_branches)}, User={frappe.session.user}"
        )

        return response

    except frappe.ValidationError as e:
        logger.warning(f"Validation Error: {str(e)}")
        return _error_response(400, "ValidationError", str(e))

    except frappe.PermissionError as e:
        logger.warning(f"Permission Denied: User={frappe.session.user}")
        return _error_response(403, "PermissionError", 
            _("Access denied. Insufficient permissions."))

    except frappe.DoesNotExistError as e:
        logger.error(f"Configuration Error: {str(e)}")
        return _error_response(404, "ConfigurationError", 
            _("Required configuration not found."))

    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}", exc_info=True)
        return _error_response(500, "InternalServerError", 
            _("An unexpected error occurred. Please contact support."))


# ============================================================================
# ✨ CORE DATA BUILDING - WITH MONTH-WISE CATEGORY TRACKING
# ============================================================================


def _build_months_data_with_category_tracking(
    fy_months: List[Tuple[str, int, int]],
    doctype_name: str,
    targets_map: Dict,
    zone_filter: List[str],
    category_filter: List[str]
) -> Tuple[Dict[str, Any], List[Dict]]:
    """
    Build month data with:
    1. Zone-wise grouping (current month category)
    2. Category-wise grouping (current month category)
    3. ✨ Consolidated branch list with month-wise category tracking

    Returns:
        (months_data, consolidated_branches)
    """
    months_data = {}
    category_order = ["Pinnacle", "Master", "Accelerator", "Starter", "Learner", "Zero Level"]

    # ✨ Track all branches across months
    branch_tracker = {}  # {sol_id: {branch_name, zone, region, monthly_data}}

    for month_name, month_num, year in fy_months:

        # Get last date for this month
        last_date_result = frappe.db.sql("""
            SELECT DISTINCT date 
            FROM `tabBranch Category Report` 
            WHERE MONTH(date) = %s AND YEAR(date) = %s
            ORDER BY date DESC
            LIMIT 1
        """, (month_num, year), as_dict=True)

        if not last_date_result:
            continue

        last_date = str(last_date_result[0]["date"])

        # Build filters
        date_filters = {"date": last_date}
        if zone_filter and "all" not in [z.lower() for z in zone_filter]:
            date_filters["zone"] = ["in", zone_filter]

        # Fetch branches with REGION field
        branches = frappe.get_all(
            doctype_name,
            filters=date_filters,
            fields=["branch", "sol_id", "zone", "region", "achievement", "yearly_achievement"],
            order_by="zone asc, region asc, branch asc"
        )

        # Initialize month structures
        raw_data = {}  # For zone grouping
        branch_details_current_month = []  # For current month's branch_details

        for branch in branches:
            sol_id = str(branch.get("sol_id")) if branch.get("sol_id") else None
            if not sol_id:
                continue

            zone = branch.get("zone") or "Unknown"
            region = branch.get("region") or "Unknown"
            branch_name = branch.get("branch") or "Unknown Branch"

            # Get target and achievement
            branch_targets = targets_map.get(sol_id, {})
            monthly_target = branch_targets.get(month_name, 0.0)
            monthly_achievement = float(branch.get("achievement") or 0)

            # Calculate achievement percentage
            ach_pct = (
                (monthly_achievement / monthly_target * 100) 
                if monthly_target > 0 else 0
            )

            # ✨ Determine category FOR THIS MONTH
            category = _calculate_category(ach_pct)

            # Apply category filter (use current month's category)
            if category_filter and "all" not in [c.lower() for c in category_filter]:
                if category not in category_filter:
                    continue

            # ================================================================
            # ✨ TRACK BRANCH ACROSS MONTHS
            # ================================================================
            if sol_id not in branch_tracker:
                branch_tracker[sol_id] = {
                    "branch_code": sol_id,
                    "branch_name": branch_name,
                    "zone": zone,
                    "region": region,
                    "monthly_data": {}
                }

            # ✨ Store month-wise data WITH CATEGORY
            branch_tracker[sol_id]["monthly_data"][month_name] = {
                "target": round(monthly_target, 2),
                "achievement": round(monthly_achievement, 2),
                "achievement_pct": round(ach_pct, 2),
                "category": category  # ✨ Month-specific category
            }

            # ================================================================
            # Store for current month's branch_details (for backward compatibility)
            # ================================================================
            branch_details_current_month.append({
                "branch_code": sol_id,
                "branch_name": branch_name,
                "zone": zone,
                "region": region,
                "category": category,
                "target": round(monthly_target, 2),
                "achievement": round(monthly_achievement, 2),
                "achievement_pct": round(ach_pct, 2)
            })

            # ================================================================
            # Aggregate for zone grouping (existing logic)
            # ================================================================
            if zone not in raw_data:
                raw_data[zone] = {}
                for cat in category_order:
                    raw_data[zone][cat] = {
                        "branch_count": 0,
                        "target": 0.0,
                        "achievement": 0.0,
                        "ach_pct": 0.0
                    }

            # Aggregate
            raw_data[zone][category]["branch_count"] += 1
            raw_data[zone][category]["target"] += monthly_target
            raw_data[zone][category]["achievement"] += monthly_achievement

        # Calculate achievement percentages for aggregated data
        for zone in raw_data:
            for category in raw_data[zone]:
                cat_data = raw_data[zone][category]
                if cat_data["target"] > 0:
                    cat_data["ach_pct"] = round(
                        (cat_data["achievement"] / cat_data["target"]) * 100, 2
                    )
                cat_data["target"] = round(cat_data["target"], 2)
                cat_data["achievement"] = round(cat_data["achievement"], 2)

        # Create dual grouping
        grouped_by_zone = raw_data
        grouped_by_category = _transform_to_category_grouping(raw_data, category_order)

        # Calculate summary
        summary = _calculate_month_summary(raw_data, category_order)

        # ✨ Sort branch_details by Category → Zone → Region → Branch Name
        branch_details_sorted = _sort_branch_details(branch_details_current_month, category_order)

        # Store month data
        months_data[month_name] = {
            "month_name": month_name,
            "month_num": month_num,
            "year": year,
            "last_date": last_date,
            "grouped_by_zone": grouped_by_zone,
            "grouped_by_category": grouped_by_category,
            "branch_details": branch_details_sorted,  # Current month snapshot
            "summary": summary
        }

    # ================================================================
    # ✨ BUILD CONSOLIDATED BRANCH LIST
    # ================================================================
    consolidated_branches = _build_consolidated_branch_list(
        branch_tracker, 
        category_order
    )

    return months_data, consolidated_branches


# ============================================================================
# ✨ NEW: Build Consolidated Branch List with Month-wise Categories
# ============================================================================


def _build_consolidated_branch_list(
    branch_tracker: Dict,
    category_order: List[str]
) -> List[Dict]:
    """
    Build consolidated branch list sorted by latest month's category.

    Returns:
        [{
            branch_code, branch_name, zone, region,
            latest_category,  # For sorting
            monthly_data: {
                'APR': {category, target, achievement, achievement_pct},
                'MAY': {category, target, achievement, achievement_pct},
                ...
            }
        }]
    """
    consolidated = []

    # Month order for determining latest
    month_order = ["MAR", "FEB", "JAN", "DEC", "NOV", "OCT", 
                   "SEP", "AUG", "JUL", "JUN", "MAY", "APR"]

    for sol_id, branch_data in branch_tracker.items():
        # Determine latest category (from most recent month with data)
        latest_category = "Unknown"
        for month in month_order:
            if month in branch_data["monthly_data"]:
                latest_category = branch_data["monthly_data"][month]["category"]
                break

        # Calculate total target and achievement across all months
        total_target = sum(
            m.get("target", 0) 
            for m in branch_data["monthly_data"].values()
        )
        total_achievement = sum(
            m.get("achievement", 0) 
            for m in branch_data["monthly_data"].values()
        )

        consolidated.append({
            "branch_code": branch_data["branch_code"],
            "branch_name": branch_data["branch_name"],
            "zone": branch_data["zone"],
            "region": branch_data["region"],
            "latest_category": latest_category,
            "total_target": round(total_target, 2),
            "total_achievement": round(total_achievement, 2),
            "monthly_data": branch_data["monthly_data"]
        })

    # ✨ Sort by Latest Category → Zone → Region → Branch Name
    def get_category_index(category: str) -> int:
        try:
            return category_order.index(category)
        except ValueError:
            return len(category_order)

    consolidated_sorted = sorted(
        consolidated,
        key=lambda x: (
            get_category_index(x.get("latest_category", "")),
            x.get("zone", ""),
            x.get("region", ""),
            x.get("branch_name", "")
        )
    )

    return consolidated_sorted


# ============================================================================
# HELPER FUNCTIONS (Unchanged)
# ============================================================================


def _sort_branch_details(
    branch_details: List[Dict],
    category_order: List[str]
) -> List[Dict]:
    """Sort branch details by Category → Zone → Region → Branch Name"""
    def get_category_index(category: str) -> int:
        try:
            return category_order.index(category)
        except ValueError:
            return len(category_order)

    return sorted(
        branch_details,
        key=lambda x: (
            get_category_index(x.get("category", "")),
            x.get("zone", ""),
            x.get("region", ""),
            x.get("branch_name", "")
        )
    )


def _transform_to_category_grouping(
    zone_data: Dict,
    category_order: List[str]
) -> Dict[str, Dict[str, Dict]]:
    """Transform Zone→Category to Category→Zone grouping"""
    category_data = {}

    for category in category_order:
        category_data[category] = {}

    for zone, categories in zone_data.items():
        for category, metrics in categories.items():
            if metrics["branch_count"] > 0:
                category_data[category][zone] = metrics.copy()

    return category_data


# ============================================================================
# VALIDATION FUNCTIONS (Unchanged)
# ============================================================================


def _validate_financial_year(fy: str) -> Tuple[int, int]:
    """Validate and parse financial year."""
    try:
        parts = fy.split("-")
        if len(parts) != 2:
            raise ValueError("Invalid format")

        start_year = int(parts[0])
        end_year = int(parts[1])

        if end_year != start_year + 1:
            raise ValueError("End year must be start_year + 1")

        if not (2000 <= start_year <= 2100):
            raise ValueError("Year out of reasonable range")

        return (start_year, end_year)

    except (ValueError, IndexError):
        frappe.throw(
            _(f"Invalid financial year format: {fy}. Expected: YYYY-YYYY"),
            frappe.ValidationError
        )


def _parse_and_validate_filters(filters: Optional[str]) -> Dict[str, List[str]]:
    """Parse and validate filter JSON."""
    default_filters = {"zones": [], "categories": []}

    if not filters:
        return default_filters

    try:
        if isinstance(filters, str):
            filter_dict = json.loads(filters)
        else:
            filter_dict = filters

        zones = filter_dict.get("zones", [])
        categories = filter_dict.get("categories", [])

        if not isinstance(zones, list) or not isinstance(categories, list):
            raise ValueError("Filters must contain lists")

        return {
            "zones": [str(z).strip() for z in zones],
            "categories": [str(c).strip() for c in categories]
        }

    except (json.JSONDecodeError, ValueError, TypeError):
        logger.warning(f"Invalid filters: {filters}. Using defaults.")
        return default_filters


def _check_user_permissions():
    """Check user permissions."""
    required_roles = ["System Manager","MIS Admin"]
    user_roles = frappe.get_roles(frappe.session.user)

    if not any(role in user_roles for role in required_roles):
        frappe.throw(
            _("You do not have permission to access this resource."),
            frappe.PermissionError
        )


def _get_validated_settings():
    """Get and validate Report Settings."""
    try:
        settings = frappe.get_single("Report Settings")

        if not settings.is_active:
            frappe.throw(
                _("Report data source is currently inactive."),
                frappe.DoesNotExistError
            )

        return settings

    except frappe.DoesNotExistError:
        frappe.throw(
            _("Report Settings not configured."),
            frappe.DoesNotExistError
        )


# ============================================================================
# DATA FETCHING FUNCTIONS (Unchanged)
# ============================================================================


def _get_fy_month_structure(start_year: int, end_year: int) -> List[Tuple[str, int, int]]:
    """Get FY month structure (APR to MAR)."""
    return [
        ("APR", 4, start_year), ("MAY", 5, start_year), ("JUN", 6, start_year),
        ("JUL", 7, start_year), ("AUG", 8, start_year), ("SEP", 9, start_year),
        ("OCT", 10, start_year), ("NOV", 11, start_year), ("DEC", 12, start_year),
        ("JAN", 1, end_year), ("FEB", 2, end_year), ("MAR", 3, end_year),
    ]


def _fetch_all_targets_optimized(financial_year: str) -> Dict[str, Dict[str, float]]:
    """Fetch all targets in single query."""
    targets_map = {}

    targets = frappe.get_all(
        "Target Vs Achivement",
        filters={"financial_year": financial_year},
        fields=["sol_id", "target", "type", "month"],
        limit_page_length=0
    )

    month_mapping = {
        "JANUARY": "JAN", "FEBRUARY": "FEB", "MARCH": "MAR",
        "APRIL": "APR", "MAY": "MAY", "JUNE": "JUN",
        "JULY": "JUL", "AUGUST": "AUG", "SEPTEMBER": "SEP",
        "OCTOBER": "OCT", "NOVEMBER": "NOV", "DECEMBER": "DEC"
    }

    for target in targets:
        sol_id = str(target.sol_id) if target.sol_id else None
        if not sol_id:
            continue

        if sol_id not in targets_map:
            targets_map[sol_id] = {}

        target_value = float(target.target or 0)

        if target.type == "Monthly" and target.month:
            month_key = str(target.month).strip().upper()
            month_key = month_mapping.get(month_key, month_key[:3])
            targets_map[sol_id][month_key] = target_value

        elif target.type == "Yearly":
            targets_map[sol_id]["YEARLY"] = target_value

    return targets_map


def _calculate_month_summary(grouped_data: Dict, category_order: List[str]) -> Dict[str, Any]:
    """Calculate month summary statistics."""
    category_distribution = {cat: 0 for cat in category_order}
    total_branches = 0
    total_target = 0.0
    total_achievement = 0.0

    for zone in grouped_data:
        for category in grouped_data[zone]:
            cat_data = grouped_data[zone][category]

            if cat_data["branch_count"] > 0:
                category_distribution[category] += cat_data["branch_count"]
                total_branches += cat_data["branch_count"]
                total_target += cat_data["target"]
                total_achievement += cat_data["achievement"]

    avg_ach_pct = (
        (total_achievement / total_target * 100) 
        if total_target > 0 else 0
    )

    return {
        "total_branches": total_branches,
        "total_target": round(total_target, 2),
        "total_achievement": round(total_achievement, 2),
        "avg_ach_pct": round(avg_ach_pct, 2),
        "category_distribution": category_distribution
    }


def _calculate_fy_summary(months_data: Dict) -> Dict[str, Any]:
    """Calculate FY summary."""
    total_branches_fy = 0
    overall_ach_list = []

    for month_data in months_data.values():
        summary = month_data.get("summary", {})
        total_branches_fy = max(total_branches_fy, summary.get("total_branches", 0))
        overall_ach_list.append(summary.get("avg_ach_pct", 0))

    overall_ach_pct = (
        sum(overall_ach_list) / len(overall_ach_list) 
        if overall_ach_list else 0
    )

    return {
        "total_months": len(months_data),
        "total_branches": total_branches_fy,
        "overall_achievement_pct": round(overall_ach_pct, 2)
    }


def _calculate_category(ach_pct: float) -> str:
    """Calculate performance category based on achievement percentage."""
    if ach_pct > 100:
        return "Pinnacle"
    elif ach_pct >= 80:
        return "Master"
    elif ach_pct >= 60:
        return "Accelerator"
    elif ach_pct >= 40:
        return "Starter"
    elif ach_pct >= 20:
        return "Learner"
    else:
        return "Zero Level"


# ============================================================================
# ERROR HANDLING (Unchanged)
# ============================================================================


def _error_response(status_code: int, error_type: str, message: str) -> Dict[str, Any]:
    """Construct error response."""
    frappe.response["http_status_code"] = status_code

    return {
        "status": "error",
        "error": {
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    }