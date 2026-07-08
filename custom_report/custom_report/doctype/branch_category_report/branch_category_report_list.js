// Copyright (c) 2026, talib and contributors
// For license information, please see license.txt

frappe.listview_settings['Branch Category Report'] = {
	hide_name_column: true,
	hide_name_filter: true,
	onload(listview) {
		listview.page.add_inner_button(__('Sync Achievement Data'), () => {
			frappe.prompt([
				{
					label: __('Date'),
					fieldname: 'date',
					fieldtype: 'Date',
					default: frappe.datetime.get_today(),
					reqd: 1
				}
			], (values) => {
				frappe.call({
					method: 'custom_report.custom_report.page.sahayog_dashboard.achievement.generate_and_save_branch_category_report',
					args: {
						input_date: values.date
					},
					freeze: true,
					freeze_message: __('Syncing Achievement Data...'),
					callback(r) {
						if (!r.exc) {
							if (r.message && r.message > 0) {
								frappe.show_alert({
									message: __('Successfully saved {0} records.', [r.message]),
									indicator: 'green'
								});
							} else {
								frappe.show_alert({
									message: __('No new records were saved.'),
									indicator: 'orange'
								});
							}
							listview.refresh();
						}
					}
				});
			}, __('Select Date'), __('Sync'));
		});
	}
};
