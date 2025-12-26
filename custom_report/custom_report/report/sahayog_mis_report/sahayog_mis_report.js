frappe.query_reports["Sahayog MIS Report"] = {
	filters: [
		{
			fieldname: "date",
			label: __("Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "target_period",
			label: __("Target Period"),
			fieldtype: "Select",
			options: ["Monthly", "YTD", "Yearly"],
			default: "Monthly",
			reqd: 1,
		},
		{
			fieldname: "zone",
			label: __("Zone"),
			fieldtype: "Link",
			options: "Zone",
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) return value;

		// --- Category Coloring (row background) ---
		if (column.fieldname === "category") {
			let color = "";
			switch (data.category) {
				case "Pinnacle":
					color = "#FFD700"; // Gold
					break;
				case "Master":
					color = "#C0C0C0"; // Silver
					break;
				case "Accelerator":
					color = "#00BFFF"; // DeepSkyBlue
					break;
				case "Starter":
					color = "#90EE90"; // LightGreen
					break;
				case "Learner":
					color = "#FFB6C1"; // LightPink
					break;
				case "Zero Level":
					color = "#D3D3D3"; // LightGray
					break;
			}
			value = `<div style="background-color:${color};padding:2px 4px;">${value}</div>`;
		}

		// --- Achievement % Coloring ---
		if (column.fieldname === "achievement_pct") {
			const pct = data.achievement_pct || 0;
			const color =
				pct > 100
					? "#16a34a"
					: pct >= 80
					? "#0d9488"
					: pct >= 60
					? "#0284c7"
					: pct >= 40
					? "#d97706"
					: pct >= 20
					? "#ea580c"
					: "#dc2626";

			value = `<b style="color:${color}">${pct.toFixed(2)}%</b>`;
		}

		// --- Grade Styling ---
		if (column.fieldname === "grade" && data.grade) {
			value = `<span class="indicator-pill">${data.grade}</span>`;
		}

		// --- Shortfall Coloring ---
		if (column.fieldname === "shortfall") {
			value =
				data.shortfall > 0
					? `<span style="color:#dc2626;font-weight:600">${value}</span>`
					: `<span style="color:#16a34a;font-weight:600">✓ Achieved</span>`;
		}

		// --- Achievement Diff Coloring ---
		if (column.fieldname === "achievement_diff") {
			const diff = data.achievement_diff || 0;
			const color = diff >= 0 ? "#16a34a" : "#dc2626";
			value = `<b style="color:${color}">${diff >= 0 ? "+" : ""}${diff}</b>`;
		}

		// --- Category Diff Coloring ---
		if (column.fieldname === "category_diff") {
			const diff = data.category_diff || 0;
			if (diff > 0) {
				value = `<b style="color:#16a34a">+${diff}</b>`;
			} else if (diff < 0) {
				value = `<b style="color:#dc2626">${diff}</b>`;
			} else {
				value = `<span style="color:#6b7280">0</span>`; // Gray for no change
			}
		}

		return value;
	},
};
