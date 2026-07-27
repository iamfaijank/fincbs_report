// Copyright (c) 2026, talib and contributors
// For license information, please see license.txt

frappe.listview_settings['SS and VS Report'] = {
	onload(listview) {
		// Apply modern popup styling with backdrop blur
		if (!$('#ss-vs-dialog-style').length) {
			$('head').append(`
				<style id="ss-vs-dialog-style">
					.modal-backdrop.show {
						backdrop-filter: blur(8px) !important;
						background-color: rgba(15, 23, 42, 0.4) !important;
						transition: all 0.3s ease;
					}
					.ss-vs-modern-dialog .modal-content {
						border-radius: 12px !important;
						box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04) !important;
						border: 1px solid #e2e8f0 !important;
						overflow: hidden;
					}
					.ss-vs-modern-dialog .modal-header {
						background: #f8fafc;
						border-bottom: 1px solid #e2e8f0 !important;
						padding: 16px 20px !important;
					}
					.ss-vs-modern-dialog .modal-title {
						font-weight: 700;
						color: #0f172a;
					}
					.ss-vs-modern-dialog .modal-footer {
						background: #f8fafc;
						border-top: 1px solid #e2e8f0 !important;
						padding: 12px 20px !important;
					}
					.ss-vs-sync-summary {
						margin-top: 12px;
						padding: 12px;
						background: #f8fafc;
						border: 1px solid #e2e8f0;
						border-radius: 8px;
						font-size: 13px;
					}
					.ss-vs-summary-item {
						display: flex;
						justify-content: space-between;
						padding: 4px 0;
						border-bottom: 1px dashed #e2e8f0;
					}
					.ss-vs-summary-item:last-child {
						border-bottom: none;
					}
					.ss-vs-summary-label {
						font-weight: 600;
						color: #475569;
					}
					.ss-vs-summary-value {
						font-weight: 700;
					}
				</style>
			`);
		}
	},

	refresh(listview) {
		// Add the Sync button to the page actions
		listview.page.add_inner_button(__('Sync Data'), () => {
			let d = new frappe.ui.Dialog({
				title: __('Sync SS & VS Report'),
				fields: [
					{
						label: __('Report Type'),
						fieldname: 'report_type',
						fieldtype: 'Select',
						options: 'DD SAV\nDD TDA\nRD\nSMBG\nFD 1\nDAM\nFD\nSHARE',
						default: 'DD SAV',
						reqd: 1
					},
					{
						label: __('Date'),
						fieldname: 'date',
						fieldtype: 'Date',
						default: frappe.datetime.add_days(frappe.datetime.get_today(), -1),
						reqd: 1
					}
				],
				primary_action_label: __('Sync Now'),
				primary_action(values) {
					const selected_date = values.date;
					const report_type = values.report_type;
					const today = frappe.datetime.get_today();
					
					if (selected_date > today) {
						frappe.msgprint(__('Future dates cannot be selected for synchronization. Please select a valid date.'));
						return;
					}
					
					d.hide();
					
					frappe.call({
						method: 'custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.sync_report',
						args: {
							report_type: report_type,
							sync_date: selected_date
						},
						freeze: true,
						freeze_message: __('Syncing {0} data for {1}...', [report_type, selected_date]),
						callback(r) {
							if (!r.exc && r.message) {
								const summary = r.message;
								
								// Show detailed response message
								const summary_html = `
									<div class="ss-vs-sync-summary">
										<div class="ss-vs-summary-item">
											<span class="ss-vs-summary-label">Processed (PG Rows):</span>
											<span class="ss-vs-summary-value" style="color: #3b82f6;">${summary.processed}</span>
										</div>
										<div class="ss-vs-summary-item">
											<span class="ss-vs-summary-label">Inserted:</span>
											<span class="ss-vs-summary-value" style="color: #22c55e;">${summary.inserted}</span>
										</div>
										<div class="ss-vs-summary-item">
											<span class="ss-vs-summary-label">Updated:</span>
											<span class="ss-vs-summary-value" style="color: #eab308;">${summary.updated}</span>
										</div>
										<div class="ss-vs-summary-item">
											<span class="ss-vs-summary-label">Skipped:</span>
											<span class="ss-vs-summary-value" style="color: #64748b;">${summary.skipped}</span>
										</div>
										<div class="ss-vs-summary-item" style="border-bottom: none;">
											<span class="ss-vs-summary-label">Failed:</span>
											<span class="ss-vs-summary-value" style="color: #ef4444;">${summary.failed}</span>
										</div>
									</div>
								`;
								
								frappe.msgprint({
									title: __('Sync Summary: {0}', [report_type]),
									message: summary_html,
									indicator: summary.failed > 0 ? 'orange' : 'green'
								});
								
								listview.refresh();
							}
						}
					});
				}
			});
			
			// Apply css_class to the dialog wrapper modal
			d.$wrapper.addClass('ss-vs-modern-dialog');
			d.show();
		});
	}
};
