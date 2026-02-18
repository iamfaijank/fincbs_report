// Copyright (c) 2026, atul and contributors
// For license information, please see license.txt

frappe.query_reports["Finacle CBS Report Audit"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "report_name",
			"label": __("Report Name"),
			"fieldtype": "Link",
			"options": "Finacle Report"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nSuccess\nFailed"
		},
		{
			"fieldname": "sol_id",
			"label": __("Primary SOL ID"),
			"fieldtype": "Data"
		}
	],
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "status") {
            if (data.status === "Success") {
                value = `<span style="color:green; font-weight:bold;">${value}</span>`;
            } else if (data.status === "Failed") {
                value = `<span style="color:red; font-weight:bold;">${value}</span>`;
            }
        }

        return value;
    }
};
