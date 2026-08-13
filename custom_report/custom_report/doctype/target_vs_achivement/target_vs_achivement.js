// Copyright (c) 2025, Your Organization and contributors
// For license information, please see license.txt

frappe.ui.form.on("Target Vs Achivement", {
	type: function (frm) {
		if (frm.doc.type === "Monthly") {
			if (!frm.doc.month) {
				const current_month = moment().format("MMM").toUpperCase();
				frm.set_value("month", current_month);
			}
		} else {
			frm.set_value("month", "");
		}
	},
});
