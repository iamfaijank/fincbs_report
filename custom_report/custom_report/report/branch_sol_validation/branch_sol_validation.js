frappe.query_reports["Branch Sol Validation"] = {
	filters: [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
		},
		{
			fieldname: "status",
			label: "Status",
			fieldtype: "Select",
			options: "\nAll\nExact Match\nProbable Same\nHigh Risk Mismatch\nSol Not Found",
			default: "All",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) {
			return value;
		}

		// soft colors
		let green_bg = "rgba(0, 176, 80, 0.12)"; // soft green
		let red_bg = "rgba(255, 0, 0, 0.10)"; // soft red

		if (data.match_flag === "Matched") {
			value = `<span style="background-color: ${green_bg}; display: block; width: 100%; height: 100%;">${value}</span>`;
		} else if (data.match_flag === "Not Matched") {
			value = `<span style="background-color: ${red_bg}; display: block; width: 100%; height: 100%;">${value}</span>`;
		}

		return value;
	},
};
