# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    summary = get_summary(data)
    
    return columns, data, None, None, summary


def get_columns():
    return [
        {
            "label": _("Log ID"),
            "fieldname": "log_id",
            "fieldtype": "Link",
            "options": "Report Log",
            "width": 120
        },
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
            "label": _("Resolved"),
            "fieldname": "resolved",
            "fieldtype": "Check",
            "width": 80
        },
        {
            "label": _("Action"),
            "fieldname": "action",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Employee"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Report Title"),
            "fieldname": "report_title",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Report ID"),
            "fieldname": "report_name",
            "fieldtype": "Link",
            "options": "Finacle Report",
            "width": 100
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
        conditions.append("DATE(rl.date_time) >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("DATE(rl.date_time) <= %(to_date)s")
    if filters.get("employee"):
        conditions.append("rl.employee = %(employee)s")
    if filters.get("report_name"):
        conditions.append("rl.report_name = %(report_name)s")
    if filters.get("status"):
        conditions.append("rl.status = %(status)s")
    if filters.get("sol_id"):
        conditions.append("rl.sol_id = %(sol_id)s")

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    return frappe.db.sql(f"""
        SELECT 
            rl.name as log_id,
            rl.date_time, rl.status, rl.resolved, rl.employee_name, 
            fr.report_name as report_title,
            rl.report_name, rl.sol_id, rl.start_date, 
            rl.end_date, rl.selected_sol_ids, rl.error_message
        FROM `tabReport Log` rl
        LEFT JOIN `tabFinacle Report` fr ON rl.report_name = fr.name
        {where_clause}
        ORDER BY rl.date_time DESC
    """, filters, as_dict=True)


def get_summary(data):
    if not data:
        return []

    total = len(data)
    success = len([d for d in data if d.status == "Success"])
    failed = total - success
    success_rate = int(success / total * 100) if total > 0 else 0

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
            "value": f"{success_rate}%",
            "indicator": "Green" if success_rate > 80 else "Orange",
            "label": _("Success Rate"),
            "datatype": "Data",
        }
    ]


