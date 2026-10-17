// Copyright (c) 2026, atul and contributors
// For license information, please see license.txt

frappe.listview_settings["Profit and Loss Report"] = {
	onload: function (listview) {
		listview.page.add_inner_button(__("Sync"), function () {
			let d = new frappe.ui.Dialog({
				title: __("Sync Profit and Loss Report"),
				fields: [
					{
						fieldname: "sync_date",
						label: __("Date"),
						fieldtype: "Date",
						reqd: 1,
						default: frappe.datetime.add_days(frappe.datetime.get_today(), -1),
					},
				],
				primary_action_label: __("Get"),
				primary_action(values) {
					if (!values.sync_date) {
						frappe.msgprint(__("Please select a date"));
						return;
					}
					d.hide();
					frappe.dom.freeze(__("Syncing data for {0}...", [values.sync_date]));
					frappe.call({
						method: "custom_report.custom_report.doctype.profit_and_loss_report.profit_and_loss_report.sync_profit_and_loss_data",
						args: { sync_date: values.sync_date },
						callback: function (r) {
							frappe.dom.unfreeze();
							if (r.message === "Success" || !r.exc) {
								frappe.msgprint(
									__("Sync completed for {0}. Refreshing list...", [values.sync_date])
								);
								listview.refresh();
							}
						},
						error: function () {
							frappe.dom.unfreeze();
						},
					});
				},
			});
			d.show();
		});
	},
};
