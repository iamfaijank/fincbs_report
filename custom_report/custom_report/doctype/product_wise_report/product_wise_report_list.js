// Copyright (c) 2026, talib and contributors
// For license information, please see license.txt

frappe.listview_settings['Product Wise Report'] = {
	refresh(listview) {
		// Avoid adding duplicate buttons on refresh
		const actions_wrapper = listview.page.actions ? $(listview.page.actions) : listview.page.wrapper.find('.page-actions');
		
		// 1. Sync Button
		let sync_btn = actions_wrapper.find('button:contains("Sync")');
		if (!sync_btn.length) {
			sync_btn = listview.page.wrapper.find('.page-actions button:contains("Sync")');
		}

		if (!sync_btn.length) {
			listview.page.add_inner_button(__('Sync'), () => {
				let d = new frappe.ui.Dialog({
					title: __('Sync Data'),
					fields: [
						{
							label: __('Select Option'),
							fieldname: 'sync_option',
							fieldtype: 'Select',
							options: '\nCASA\nTDA',
							reqd: 1
						},
						{
							label: __('Date'),
							fieldname: 'date',
							fieldtype: 'Date',
							depends_on: 'eval:doc.sync_option',
							reqd: 1
						}
					],
					primary_action_label: __('Sync'),
					primary_action(values) {
						const selected_date = values.date;
						const today = frappe.datetime.get_today();
						if (selected_date >= today) {
							frappe.msgprint(__('Today\'s date and future dates cannot be selected. Please select a past date.'));
							return;
						}
						
						d.hide();
						
						if (values.sync_option === 'CASA') {
							frappe.call({
								method: 'custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_product_wise_casa',
								args: {
									selected_date: selected_date
								},
								freeze: true,
								freeze_message: __('Syncing CASA Product Wise Report Data...'),
								callback(r) {
									if (!r.exc) {
										frappe.show_alert({
											message: __('Successfully synced {0} CASA records.', [r.message || 0]),
											indicator: 'green'
										});
										listview.refresh();
									}
								}
							});
						} else if (values.sync_option === 'TDA') {
							frappe.call({
								method: 'custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_product_wise_tda',
								args: {
									selected_date: selected_date
								},
								freeze: true,
								freeze_message: __('Syncing TDA Product Wise Report Data...'),
								callback(r) {
									if (!r.exc) {
										frappe.show_alert({
											message: __('Successfully synced {0} TDA records.', [r.message || 0]),
											indicator: 'green'
										});
										listview.refresh();
									}
								}
							});
						}
					}
				});
				d.show();
			});
		}
	}
};
