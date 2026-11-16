frappe.listview_settings["Book Position and Account Details"] = {
	onload: function(listview) {
		listview.page.add_inner_button(__("Sync"), function() {
			frappe.prompt(
				[
					{
						fieldname: "sync_date",
						fieldtype: "Date",
						label: __("Select Date"),
						reqd: 1,
						description: __("Date must be in the past. Today and future dates are not allowed.")
					}
				],
				function(values) {
					const selected_date = values.sync_date;
					const today = frappe.datetime.get_today();

					if (selected_date >= today) {
						frappe.throw(__("You can only select a past date. Today or future dates are not allowed."));
						return;
					}

					frappe.call({
						method: "custom_report.custom_report.doctype.book_position_and_account_details.book_position_and_account_details.sync_data",
						args: {
							sync_date: selected_date
						},
						freeze: true,
						freeze_message: __("Syncing data from DR DB..."),
						callback: function(r) {
							if (!r.exc) {
								frappe.show_alert({message: __("Data Synced Successfully"), indicator: "green"});
								listview.refresh();
							}
						}
					});
				},
				__("Sync Book Position and Account Details"),
				__("Start Sync")
			);
		});
	}
};
