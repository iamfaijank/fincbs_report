frappe.query_reports["Target Vs Achivement"] = {
	filters: [
		{ fieldname: "zone", label: "Zone", fieldtype: "Data" },
		{ fieldname: "region", label: "Region", fieldtype: "Data" },
		{ fieldname: "district", label: "District", fieldtype: "Data" },
		{ fieldname: "branch", label: "Branch", fieldtype: "Data" },
		{
			fieldname: "type",
			label: "Target Type",
			fieldtype: "Select",
			options: "\nMonthly\nYearly\nYTD",
		},
		{
			fieldname: "date",
			label: "Date",
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "compare_type",
			label: "Compare",
			fieldtype: "Select",
			options: "\nDaily\nMonthly\nYearly",
			// default: "Daily",
		},
		{
			fieldname: "sort_mode",
			label: "Sort By",
			fieldtype: "Select",
			options: "\nZone-wise Category\nOverall Category",
			default: "Zone-wise Category",
		},
	],
};
