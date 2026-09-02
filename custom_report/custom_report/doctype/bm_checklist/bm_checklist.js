frappe.ui.form.on("BM checklist", {
	onload(frm) {
		set_bm_employee_from_context(frm);
	},
	refresh(frm) {
		set_bm_employee_from_context(frm);
	}
});

function set_bm_employee_from_context(frm) {
	if (!frm.is_new() || frm.doc.bm_employee_id) return;

	const urlParams = new URLSearchParams(window.location.search);
	let raw_emp = urlParams.get("bm_employee_id")
		|| (frappe.route_options && frappe.route_options.bm_employee_id)
		|| sessionStorage.getItem("bm_checklist_employee_id")
		|| localStorage.getItem("bm_checklist_employee_id");

	if (!raw_emp) {
		const sol_id = urlParams.get("sol_id")
			|| (frappe.route_options && frappe.route_options.sol_id)
			|| sessionStorage.getItem("bm_checklist_sol_id")
			|| localStorage.getItem("bm_checklist_sol_id");
		if (sol_id) {
			raw_emp = sol_id;
		}
	}

	if (!raw_emp) return;

	// Clear temporary storage
	try {
		sessionStorage.removeItem("bm_checklist_employee_id");
		localStorage.removeItem("bm_checklist_employee_id");
		sessionStorage.removeItem("bm_checklist_sol_id");
		localStorage.removeItem("bm_checklist_sol_id");
	} catch (e) {}

	// 1. Direct Employee Link match
	frappe.db.get_value("Employee", { name: raw_emp }, "name").then((r) => {
		if (r && r.message && r.message.name) {
			frm.set_value("bm_employee_id", r.message.name);
		} else {
			// 2. Lookup by numeric employee_number
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Employee",
					filters: [
						["status", "=", "Active"],
						["employee_number", "=", raw_emp]
					],
					fields: ["name"],
					limit: 1
				},
				callback: function(res) {
					if (res.message && res.message.length > 0) {
						frm.set_value("bm_employee_id", res.message[0].name);
					} else {
						// 3. Lookup by sol_id & Branch Manager designation
						frappe.call({
							method: "frappe.client.get_list",
							args: {
								doctype: "Employee",
								filters: [
									["status", "=", "Active"],
									["sol_id", "=", raw_emp],
									["designation", "like", "%Branch Manager%"]
								],
								fields: ["name"],
								limit: 1
							},
							callback: function(res2) {
								if (res2.message && res2.message.length > 0) {
									frm.set_value("bm_employee_id", res2.message[0].name);
								} else {
									frm.set_value("bm_employee_id", raw_emp);
								}
							}
						});
					}
				}
			});
		}
	});
}


