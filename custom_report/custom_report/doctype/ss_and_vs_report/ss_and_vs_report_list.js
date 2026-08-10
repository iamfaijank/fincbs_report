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
		// Render top Month Availability Widget
		this.renderMonthWidget(listview);

		// Add the Sync button to the page actions
		listview.page.add_inner_button(__('Sync Data'), () => {
			let d = new frappe.ui.Dialog({
				title: __('Sync SS & VS Report'),
				fields: [
					{
						label: __('Report Type'),
						fieldname: 'report_type',
						fieldtype: 'Select',
						options: 'All Reports\nDD SAV\nDD TDA\nRD\nSMBG\nFD 1\nDAM\nFD\nSHARE',
						default: 'All Reports',
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

		// Add Cleanup button under Actions menu
		listview.page.add_inner_button(__('Cleanup Monthly Records'), () => {
			frappe.confirm(
				__('This will retain ONLY the last date records for each month and delete all prior daily dates. Do you want to proceed?'),
				() => {
					frappe.call({
						method: 'custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.cleanup_ss_vs_old_monthly_records',
						freeze: true,
						freeze_message: __('Cleaning up old daily records...'),
						callback(r) {
							if (r.message && r.message.status === 'success') {
								frappe.msgprint({
									title: __('Cleanup Completed'),
									indicator: 'green',
									message: r.message.message
								});
								listview.refresh();
							}
						}
					});
				}
			);
		}, __('Actions'));
	},

	renderMonthWidget(listview) {
		const currentYear = new Date().getFullYear();
		if (!listview._selectedYear) listview._selectedYear = currentYear;

		let $wrapper = listview.page.main.find('.ss-vs-month-widget-wrapper');
		if (!$wrapper.length) {
			$wrapper = $(`
				<div class="ss-vs-month-widget-wrapper" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 10px 14px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);">
					<div class="ss-vs-month-widget-header" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
						<div style="font-size: 13px; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 8px;">
							<span>📅 Monthly Data Availability</span>
							<select class="ss-vs-year-select" style="font-size: 12px; font-weight: 600; padding: 2px 6px; border-radius: 4px; border: 1px solid #cbd5e1; outline: none; background: #f8fafc; cursor: pointer; color: #1e293b;">
								<option value="${currentYear}">${currentYear}</option>
								<option value="${currentYear - 1}">${currentYear - 1}</option>
								<option value="${currentYear - 2}">${currentYear - 2}</option>
							</select>
						</div>
						<button type="button" class="btn btn-xs ss-vs-widget-refresh" style="background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; padding: 2px 8px; font-size: 11px; font-weight: 600; border-radius: 4px; cursor: pointer;">⟳ Refresh</button>
					</div>
					<div class="ss-vs-month-grid" style="display: grid; grid-template-columns: repeat(12, 1fr); gap: 6px;">
						<div style="grid-column: span 12; color: #94a3b8; font-size: 11px; text-align: center; padding: 8px;">Loading month cards...</div>
					</div>
					<div class="ss-vs-selected-month-info" style="display: none; margin-top: 8px; padding: 6px 12px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; font-size: 12px; font-weight: 600; color: #166534; justify-content: space-between; align-items: center;">
						<span class="info-text"></span>
						<button type="button" class="btn btn-xs clear-month-filter" style="background: #ffffff; border: 1px solid #86efac; color: #15803d; padding: 2px 8px; font-size: 11px; font-weight: 600; border-radius: 4px; cursor: pointer;">Clear Filter</button>
					</div>
				</div>
			`);
			
			if (listview.page.main.find('.frappe-list').length) {
				listview.page.main.find('.frappe-list').before($wrapper);
			} else {
				listview.page.main.prepend($wrapper);
			}

			$wrapper.on('change', '.ss-vs-year-select', function() {
				listview._selectedYear = parseInt($(this).val());
				listview.renderMonthWidget(listview);
			});

			$wrapper.on('click', '.ss-vs-widget-refresh', function() {
				listview.renderMonthWidget(listview);
			});

			$wrapper.on('click', '.clear-month-filter', function() {
				$wrapper.find('.ss-vs-month-card').removeClass('active-card').css({ boxShadow: 'none', transform: 'none' });
				$wrapper.find('.month-count-tag').hide();
				$wrapper.find('.ss-vs-selected-month-info').hide();
				listview.filter_area.remove('date');
			});
		}

		frappe.call({
			method: 'custom_report.custom_report.doctype.ss_and_vs_report.ss_vs_sync.get_monthly_status',
			args: { year: listview._selectedYear },
			callback: function(r) {
				if (r.message && r.message.months) {
					const months = r.message.months;
					const fmtNum = (val) => new Intl.NumberFormat("en-IN").format(val || 0);

					let cardsHtml = "";
					months.forEach(m => {
						const isGreen = m.has_data;
						cardsHtml += `
							<div class="ss-vs-month-card ${isGreen ? 'has-data' : 'no-data'}" 
								data-month="${m.month_num}" 
								data-name="${m.month_name}"
								data-count="${m.record_count}"
								data-latest="${m.latest_date || ''}"
								data-has-data="${isGreen ? '1' : '0'}"
								title="${isGreen ? `✓ ${m.month_name} ${listview._selectedYear} (Data Available - Click to view count & filter)` : `No data for ${m.month_name} ${listview._selectedYear}`}"
								style="border-radius: 6px; padding: 8px 4px; text-align: center; font-size: 12px; font-weight: 700; cursor: pointer; transition: all 0.15s ease-in-out; display: flex; flex-direction: column; align-items: center; justify-content: center; ${isGreen ? 'background: #dcfce7; border: 1px solid #86efac; color: #15803d;' : 'background: #f8fafc; border: 1px solid #e2e8f0; color: #94a3b8;'}">
								<span>${isGreen ? '✓ ' : ''}${m.month_name}</span>
								<span class="month-count-tag" style="font-size: 9px; font-weight: 700; margin-top: 3px; background: #166534; color: #ffffff; padding: 1px 5px; border-radius: 10px; display: none;"></span>
							</div>
						`;
					});

					$wrapper.find('.ss-vs-month-grid').html(cardsHtml);

					// Click on month card to show count and filter listview
					$wrapper.off('click', '.ss-vs-month-card').on('click', '.ss-vs-month-card', function() {
						const $card = $(this);
						const monthNum = parseInt($card.data('month'));
						const monthName = $card.data('name');
						const count = parseInt($card.data('count') || 0);
						const latestDate = $card.data('latest');
						const hasData = $card.data('has-data') === 1 || $card.data('has-data') === '1';
						const year = listview._selectedYear;

						// Reset previous active card styles & count tags
						$wrapper.find('.ss-vs-month-card').removeClass('active-card').css({ boxShadow: 'none', transform: 'none' });
						$wrapper.find('.month-count-tag').hide();

						// Apply active highlight to clicked card & show its count tag
						$card.addClass('active-card').css({
							boxShadow: '0 0 0 2px #16a34a',
							transform: 'scale(1.04)'
						});

						if (hasData) {
							$card.find('.month-count-tag').text(fmtNum(count)).show();
							$wrapper.find('.ss-vs-selected-month-info').css('display', 'flex').find('.info-text').html(
								`📊 <strong>${monthName} ${year}</strong> — <strong>${fmtNum(count)}</strong> Records Available ` +
								(latestDate ? `<span style="font-weight: 500; color: #047857; margin-left: 6px;">(Latest: ${latestDate})</span>` : '')
							);
						} else {
							$card.find('.month-count-tag').text("0").show();
							$wrapper.find('.ss-vs-selected-month-info').css('display', 'flex').find('.info-text').html(
								`ℹ️ <strong>${monthName} ${year}</strong> — No Data Records Found`
							);
						}

						const startDate = `${year}-${String(monthNum).padStart(2, '0')}-01`;
						const lastDay = new Date(year, monthNum, 0).getDate();
						const endDate = `${year}-${String(monthNum).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;

						listview.filter_area.remove('date');
						listview.filter_area.add([['SS and VS Report', 'date', 'Between', [startDate, endDate]]]);
					});
				}
			}
		});
	}
};
