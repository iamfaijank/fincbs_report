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

		// 2. Superfast Import Button
		let import_btn = actions_wrapper.find('button:contains("Import")');
		if (!import_btn.length) {
			import_btn = listview.page.wrapper.find('.page-actions button:contains("Import")');
		}

		if (!import_btn.length) {
			listview.page.add_inner_button(__('⚡ Fast Import'), () => {
				const d = new frappe.ui.Dialog({
					title: __('⚡ Superfast Import - Product Wise Report'),
					fields: [
						{
							fieldtype: 'HTML',
							fieldname: 'instructions',
							options: `
								<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 15px; font-size: 12px; color: #475569;">
									<div style="font-weight: 700; color: #1e293b; margin-bottom: 6px;">Supported Columns (Header Labels or Fieldnames):</div>
									<div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;">
										<span style="background: #e2e8f0; padding: 2px 8px; border-radius: 4px; font-weight: 600; color: #0f172a;">Date (Required)</span>
										<span style="background: #e2e8f0; padding: 2px 8px; border-radius: 4px; font-weight: 600; color: #0f172a;">Sol ID</span>
										<span style="background: #e2e8f0; padding: 2px 8px; border-radius: 4px; font-weight: 600; color: #0f172a;">Zone</span>
										<span style="background: #e2e8f0; padding: 2px 8px; border-radius: 4px; font-weight: 600; color: #0f172a;">Region</span>
										<span style="background: #e2e8f0; padding: 2px 8px; border-radius: 4px; font-weight: 600; color: #0f172a;">Scheme Code</span>
										<span style="background: #e2e8f0; padding: 2px 8px; border-radius: 4px; font-weight: 600; color: #0f172a;">Product</span>
										<span style="background: #e2e8f0; padding: 2px 8px; border-radius: 4px; font-weight: 600; color: #0f172a;">Total Tran Amount / Amount</span>
									</div>
									<div style="color: #64748b; font-size: 11px;">* Auto-maps Zone/Region from Sol ID & Product Group from Scheme Code if left blank. Direct SQL bulk insertion for maximum speed.</div>
								</div>
							`
						},
						{
							label: __('Attach File (.csv, .xlsx)'),
							fieldname: 'attach_file',
							fieldtype: 'Attach',
							reqd: 1
						}
					],
					primary_action_label: __('Start Fast Import'),
					primary_action(values) {
						if (!values.attach_file) {
							frappe.msgprint(__('Please attach a CSV or Excel file.'));
							return;
						}

						d.hide();
						frappe.show_alert({
							message: __('Processing superfast import...'),
							indicator: 'blue'
						});

						frappe.call({
							method: 'custom_report.custom_report.doctype.product_wise_report.product_wise_report.fast_import_product_wise_report',
							args: {
								file_url: values.attach_file
							},
							freeze: true,
							freeze_message: __('🚀 Importing records directly into database...'),
							callback(r) {
								if (!r.exc) {
									const count = r.message || 0;
									frappe.msgprint({
										title: __('Import Successful'),
										indicator: 'green',
										message: __('🚀 Successfully imported <b>{0}</b> records in lightning speed!', [count])
									});
									listview.refresh();
								}
							}
						});
					}
				});
				d.show();
			});
		}
	}
};

