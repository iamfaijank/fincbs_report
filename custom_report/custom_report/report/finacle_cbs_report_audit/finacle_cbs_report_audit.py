# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    summary = get_summary(data)
    chart = get_chart(data)
    
    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "label": _("Date & Time"),
            "fieldname": "date_time",
            "fieldtype": "Datetime",
            "width": 160
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Select",
            "width": 100
        },
        {
            "label": _("Employee"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Report Name"),
            "fieldname": "report_name",
            "fieldtype": "Link",
            "options": "Finacle Report",
            "width": 180
        },
        {
            "label": _("Primary SOL"),
            "fieldname": "sol_id",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Start Date"),
            "fieldname": "start_date",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "label": _("End Date"),
            "fieldname": "end_date",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "label": _("Selected SOL IDs"),
            "fieldname": "selected_sol_ids",
            "fieldtype": "Small Text",
            "width": 200
        },
        {
            "label": _("Error Message"),
            "fieldname": "error_message",
            "fieldtype": "Small Text",
            "width": 250
        }
    ]


def get_data(filters):
    conditions = []
    if filters.get("from_date"):
        conditions.append("date_time >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("date_time <= %(to_date)s")
    if filters.get("employee"):
        conditions.append("employee = %(employee)s")
    if filters.get("report_name"):
        conditions.append("report_name = %(report_name)s")
    if filters.get("status"):
        conditions.append("status = %(status)s")
    if filters.get("sol_id"):
        conditions.append("sol_id = %(sol_id)s")

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    return frappe.db.sql(f"""
        SELECT 
            date_time, status, employee_name, report_name, 
            sol_id, start_date, end_date, selected_sol_ids, error_message
        FROM `tabReport Log`
        {where_clause}
        ORDER BY date_time DESC
    """, filters, as_dict=True)


def get_summary(data):
    if not data:
        return []

    total = len(data)
    success = len([d for d in data if d.status == "Success"])
    failed = total - success
    success_rate = (success / total * 100) if total > 0 else 0

    return [
        {
            "value": total,
            "indicator": "Blue",
            "label": _("Total Downloads"),
            "datatype": "Int",
        },
        {
            "value": success,
            "indicator": "Green",
            "label": _("Successful"),
            "datatype": "Int",
        },
        {
            "value": failed,
            "indicator": "Red",
            "label": _("Failed"),
            "datatype": "Int",
        },
        {
            "value": f"{success_rate:.1f}%",
            "indicator": "Green" if success_rate > 80 else "Orange",
            "label": _("Success Rate"),
            "datatype": "Percent",
        }
    ]


def get_chart(data):
    if not data:
        return None

    # Group by date for chart
    dates = {}
    for d in data:
        date_str = d.date_time.strftime("%Y-%m-%d")
        if date_str not in dates:
            dates[date_str] = {"success": 0, "failed": 0}
        
        if d.status == "Success":
            dates[date_str]["success"] += 1
        else:
            dates[date_str]["failed"] += 1

    sorted_dates = sorted(dates.keys())
    
    return {
        "data": {
            "labels": sorted_dates,
            "datasets": [
                {
                    "name": _("Success"),
                    "values": [dates[date]["success"] for date in sorted_dates]
                },
                {
                    "name": _("Failed"),
                    "values": [dates[date]["failed"] for date in sorted_dates]
                }
            ]
        },
        "type": "line", # or 'bar'
        "colors": ["green", "red"]
    }
