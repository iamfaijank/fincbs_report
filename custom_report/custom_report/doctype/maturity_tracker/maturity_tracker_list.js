frappe.listview_settings['Maturity Tracker'] = {
	onload: function(listview) {
		listview.page.add_inner_button(__('Sync Data'), function() {
			let yesterday = frappe.datetime.add_days(frappe.datetime.get_today(), -1);
			let d = new frappe.ui.Dialog({
				title: __('Sync Maturity Tracker Data'),
				fields: [
					{
						label: __('From Date'),
						fieldname: 'from_date',
						fieldtype: 'Date',
						reqd: 1,
						default: yesterday
					},
					{
						label: __('To Date'),
						fieldname: 'to_date',
						fieldtype: 'Date',
						reqd: 1,
						default: yesterday
					}
				],
				primary_action_label: __('Sync Now'),
				primary_action(values) {
					let today = frappe.datetime.get_today();
					if (values.from_date >= today || values.to_date >= today) {
						frappe.msgprint({
							title: __('Invalid Date'),
							indicator: 'red',
							message: __('Today and future dates cannot be selected. Please select past dates only.')
						});
						return;
					}
					if (values.from_date > values.to_date) {
						frappe.msgprint({
							title: __('Invalid Date Range'),
							indicator: 'red',
							message: __('From Date cannot be greater than To Date.')
						});
						return;
					}

					d.hide();
					frappe.call({
						method: 'custom_report.custom_report.doctype.maturity_tracker.maturity_tracker.sync_maturity_tracker',
						args: {
							from_date: values.from_date,
							to_date: values.to_date
						},
						freeze: true,
						freeze_message: __('Connecting to DR Database & Syncing Maturity Tracker...'),
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
