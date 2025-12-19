# sahayog_dashboard.py

import frappe
from frappe import _
from frappe.utils import getdate


@frappe.whitelist()
def get_dashboard_data(time_period="daily", from_date=None, to_date=None):
    """
    Fetch dashboard data with Yearly targets from Target Vs Achievement
    Returns: List of zone-wise and category-wise aggregated data
    """
    settings = frappe.get_single("Report Settings")

    if not settings.is_active:
        frappe.throw(_("Data source is not active"))

    # Build filters
    filters = {}

    if from_date and to_date:
        filters['date'] = ['between', [from_date, to_date]]

    # Fetch branch data from Branch Category Report
    doctype_name = settings.master_doctype or "Branch Category Report"
    branch_data = frappe.get_all(
        doctype_name,
        filters=filters,
        fields=[
            'zone', 'region', 'district', 'branches', 'sol',
            'ytd_target', 'ytd', 'ytd_achi', 'branch_score', 'date'
        ]
    )

    # Get Yearly targets for the relevant financial year
    financial_year = get_financial_year(to_date)
    yearly_targets = get_yearly_targets(financial_year)

    # Aggregate data
    aggregated = aggregate_with_targets(branch_data, yearly_targets)

    return aggregated


def get_financial_year(date_str=None):
    """
    Get financial year from date.
    Example: 2025-2026
    """
    if not date_str:
        date = getdate()
    else:
        date = getdate(date_str)

    if date.month > 3:
        return f"{date.year}-{date.year + 1}"
    else:
        return f"{date.year - 1}-{date.year}"


def get_yearly_targets(financial_year):
    """
    Fetch Yearly targets from Target Vs Achievement
    For a specific financial year
    Returns: {sol_id: target_amount}
    """
    targets = frappe.get_all(
        "Target Vs Achivement",
        filters={
            'type': 'Yearly',
            'financial_year': financial_year
        },
        fields=['sol_id', 'target']
    )

    targets_map = {}
    for t in targets:
        # Convert sol_id to string for consistent matching
        sol_id = str(t.sol_id) if t.sol_id else None
        if sol_id:
            targets_map[sol_id] = float(t.target or 0)

    return targets_map


def aggregate_with_targets(data, yearly_targets):
    """
    Aggregate by Zone → Category
    Total target: From Target Vs Achievement (Yearly)
    Returns: Flattened list for frontend consumption
    """
    zone_map = {}

    for row in data:
        zone_name = row.get('zone', 'Unknown')
        category = row.get('branch_score', 'Unknown')
        sol_id = str(row.get('sol', '')) if row.get('sol') else None

        # Initialize zone
        if zone_name not in zone_map:
            zone_map[zone_name] = {}

        # Initialize category within zone
        if category not in zone_map[zone_name]:
            zone_map[zone_name][category] = {
                'zone': zone_name,
                'category': category,
                'branch_count': 0,
                'loan_target': 0,
                'dep_target': 0,
                'loan_ach': 0,
                'dep_ach': 0,
            }

        # Get yearly target from Target Vs Achievement using sol_id
        yearly_target = 0
        if sol_id and sol_id in yearly_targets:
            yearly_target = yearly_targets[sol_id]

        # Total achievement from Branch Category Report (ytd field)
        total_ach = float(row.get('ytd') or 0)

        # Split target equally between loan and deposit (assumption)
        # You can modify this logic based on your business rules
        loan_target = yearly_target * 0.5
        dep_target = yearly_target * 0.5
        loan_ach = total_ach * 0.5
        dep_ach = total_ach * 0.5

        # Update category aggregation
        cat_data = zone_map[zone_name][category]
        cat_data['branch_count'] += 1
        cat_data['loan_target'] += loan_target
        cat_data['dep_target'] += dep_target
        cat_data['loan_ach'] += loan_ach
        cat_data['dep_ach'] += dep_ach

    # Flatten the nested dictionary into a list
    result = []
    for zone_name, categories in zone_map.items():
        for category, cat_data in categories.items():
            result.append(cat_data)

    return result


@frappe.whitelist()
def get_drill_down_data(zone, category, time_period="daily", from_date=None, to_date=None):
    """
    Drill down with branch-level data
    Target from Target Vs Achievement (matched by sol_id)

    NEW: If zone="ALL", fetch data from all zones for the given category
    """
    settings = frappe.get_single("Report Settings")
    doctype_name = settings.master_doctype or "Branch Category Report"

    # Build filters based on zone parameter
    if zone == "ALL":
        # Fetch all zones for the category
        filters = {'branch_score': category}
    else:
        # Existing functionality: specific zone + category
        filters = {'zone': zone, 'branch_score': category}

    if from_date and to_date:
        filters['date'] = ['between', [from_date, to_date]]

    branches = frappe.get_all(
        doctype_name,
        filters=filters,
        fields=[
            'branches', 'sol', 'region', 'district', 'zone',
            'ytd_target', 'ytd', 'ytd_achi', 'date'
        ],
        order_by='zone asc, branches asc'
    )

    # Get yearly targets for these branches
    sol_ids = [str(b.get('sol')) for b in branches if b.get('sol')]
    yearly_targets = {}
    financial_year = get_financial_year(to_date)

    if sol_ids:
        targets = frappe.get_all(
            "Target Vs Achivement",
            filters={
                'sol_id': ['in', sol_ids],
                'type': 'Yearly',
                'financial_year': financial_year
            },
            fields=['sol_id', 'target']
        )

        for t in targets:
            sol_id = str(t.sol_id) if t.sol_id else None
            if sol_id:
                yearly_targets[sol_id] = float(t.target or 0)

    # Enhance branch data
    for branch in branches:
        sol_id = str(branch.get('sol', '')) if branch.get('sol') else None

        # Get yearly target from Target Vs Achievement
        yearly_target = 0
        if sol_id and sol_id in yearly_targets:
            yearly_target = yearly_targets[sol_id]

        # Split targets (assumption: 50-50)
        loan_target = yearly_target * 0.5
        dep_target = yearly_target * 0.5

        # Achievement (from ytd field)
        total_ach = float(branch.get('ytd') or 0)
        loan_ach = total_ach * 0.5
        dep_ach = total_ach * 0.5

        # Add to branch data
        branch['category'] = category
        branch['branch'] = branch.get('branches', '')
        branch['loan_target'] = loan_target
        branch['dep_target'] = dep_target
        branch['loan_ach'] = loan_ach
        branch['dep_ach'] = dep_ach
        branch['ytd_achi_pct'] = round(float(branch.get('ytd_achi') or 0) * 100, 2)

    return branches


@frappe.whitelist()
def get_branch_targets(from_date=None, to_date=None):
    """
    Branch Targets tab - show all targets (filtered by Yearly for now)
    """
    financial_year = get_financial_year(to_date)
    targets = frappe.get_all(
        "Target Vs Achivement",
        filters={
            'type': 'Yearly',
            'financial_year': financial_year
        },
        fields=['sol_id', 'target', 'financial_year', 'type'],
        order_by='sol_id asc',
        limit=1000
    )

    return targets