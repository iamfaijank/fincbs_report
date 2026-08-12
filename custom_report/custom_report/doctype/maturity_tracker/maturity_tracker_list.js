frappe.listview_settings['Maturity Tracker'] = {
	onload: function(listview) {
		listview.page.add_inner_button(__('Sync Data'), function() {
			let yesterday = frappe.datetime.add_days(frappe.datetime.get_today(), -1);
			let d = new frappe.ui.Dialog({
				title: __('Sync Maturity Tracker Data'),
				fields: [
					{
						label: __('Select Date'),
						fieldname: 'sync_date',
						fieldtype: 'Date',
						reqd: 1,
						default: yesterday,
						description: __('Data will be automatically synced from the 1st of that month to the selected date. Today and future dates are disabled.')
					}
				],
				primary_action_label: __('Sync Now'),
				primary_action(values) {
					let today = frappe.datetime.get_today();
					if (values.sync_date >= today) {
						frappe.msgprint({
							title: __('Invalid Date'),
							indicator: 'red',
							message: __('Today and future dates cannot be selected. Please select past dates only.')
						});
						return;
					}

					d.hide();
					frappe.call({
						method: 'custom_report.custom_report.doctype.maturity_tracker.maturity_tracker.sync_maturity_tracker',
						args: {
							sync_date: values.sync_date
						},
						freeze: true,
						freeze_message: __('Connecting to DR Database & Syncing Month Data...'),
						callback: function(r) {
							if (!r.exc) {
								frappe.msgprint({
									title: __('Sync Successful'),
									indicator: 'green',
									message: r.message || __('Maturity Tracker data synced successfully!')
								});
								listview.refresh();
							}
						}
					});
				}
			});
			d.show();
		}).addClass('btn-primary');
	}
};
