// Copyright (c) 2026, talib and contributors
// For license information, please see license.txt

frappe.listview_settings['Branch Category Report'] = {
	hide_name_column: true,
	hide_name_filter: true,
	onload(listview) {
		listview.can_create = false;
		const sync_btn = listview.page.add_inner_button(__('Sync Achievement Data'), () => {
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
							refresh_sync_status();
							listview.refresh();
						}
					}
				});
			}, __('Select Date'), __('Sync'));
		});

		// Create dynamic status widget next to Sync button
		const badge = $(`
			<div class="dropdown d-inline-block" id="sync-status-dropdown-container" style="margin-left: 8px; vertical-align: middle; display: inline-block;">
				<button class="btn btn-default btn-xs dropdown-toggle" id="sync-status-badge" style="border-radius: 6px; padding: 4px 10px; font-weight: 600; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); gap: 6px; border: 1px solid #cbd5e1; background-color: #f8fafc; color: #334155; font-size: 11px; height: 26px; cursor: pointer;">
					<span class="indicator-dot" style="width: 8px; height: 8px; border-radius: 50%; background-color: #cbd5e1; display: inline-block;"></span>
					<span class="sync-text">Checking status...</span>
				</button>
				<div class="dropdown-menu dropdown-menu-right" id="sync-status-menu" style="min-width: 250px; max-height: 380px; overflow-y: auto; padding: 12px; border-radius: 8px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin-top: 6px; background-color: #ffffff; z-index: 1000; position: absolute; display: none;">
					<div class="dropdown-header-custom" style="font-weight: 700; padding: 0 4px 10px 4px; border-bottom: 1px solid #f1f5f9; color: #0f172a; font-size: 13px; display: flex; justify-content: space-between; align-items: center;">
						<span>Month Sync Status</span>
						<span class="month-label" style="font-size: 11px; font-weight: 500; color: #64748b;">Loading...</span>
					</div>
					<div class="dates-list" style="margin-top: 10px; display: flex; flex-direction: column; gap: 6px;">
						<!-- Loaded dynamically -->
					</div>
				</div>
			</div>
		`);

		if (sync_btn) {
			sync_btn.after(badge);
		}

		// Manual Dropdown Toggle handler
		badge.find('#sync-status-badge').on('click', function(e) {
			e.preventDefault();
			const parent = badge;
			const menu = badge.find('#sync-status-menu');
			const isOpen = menu.is(':visible');
			
			// Close all other dropdowns
			$('.dropdown-menu').not(menu).hide();
			$('.dropdown').removeClass('open show');
			
			if (!isOpen) {
				parent.addClass('open show');
				menu.show();
			} else {
				parent.removeClass('open show');
				menu.hide();
			}
			e.stopPropagation();
		});
		
		$(document).on('click', function(e) {
			if (!$(e.target).closest('#sync-status-dropdown-container').length) {
				badge.removeClass('open show');
				badge.find('#sync-status-menu').hide();
			}
		});

		function refresh_sync_status() {
			frappe.call({
				method: 'custom_report.custom_report.page.sahayog_dashboard.achievement.get_current_month_sync_status',
				callback(r) {
					if (r.message) {
						const { dates_status, synced_count, total_days } = r.message;
						
						const badge_btn = badge.find('#sync-status-badge');
						const dot = badge_btn.find('.indicator-dot');
						const text_span = badge_btn.find('.sync-text');
						
						text_span.text(`${synced_count}/${total_days} Days Synced`);
						
						if (synced_count === total_days && total_days > 0) {
							dot.css('background-color', '#22c55e');
							badge_btn.css({
								'border-color': '#bbf7d0',
								'background-color': '#f0fdf4',
								'color': '#15803d'
							});
						} else if (synced_count > 0) {
							dot.css('background-color', '#eab308');
							badge_btn.css({
								'border-color': '#fef08a',
								'background-color': '#fefce8',
								'color': '#a16207'
							});
						} else {
							dot.css('background-color', '#ef4444');
							badge_btn.css({
								'border-color': '#fecaca',
								'background-color': '#fef2f2',
								'color': '#b91c1c'
							});
						}
						
						const list_container = badge.find('.dates-list');
						list_container.empty();
						
						if (dates_status && dates_status.length > 0) {
							const first_date = new Date(dates_status[0].date);
							const month_name = first_date.toLocaleString('default', { month: 'long', year: 'numeric' });
							badge.find('.month-label').text(month_name);

							dates_status.forEach(item => {
								let status_indicator = '';
								let text_color = '#334155';
								let bg_color = 'transparent';
								let status_label = '';
								let cursor_style = 'pointer';
								
								if (item.is_sunday) {
									status_indicator = `<span style="width: 8px; height: 8px; border-radius: 50%; background-color: #94a3b8; display: inline-block;"></span>`;
									text_color = '#94a3b8';
									status_label = '<span style="font-size: 10px; color: #94a3b8; font-weight: 500; margin-left: auto;">Sunday</span>';
								} else if (item.has_data) {
									status_indicator = `<span style="width: 8px; height: 8px; border-radius: 50%; background-color: #22c55e; display: inline-block; box-shadow: 0 0 4px #22c55e;"></span>`;
									text_color = '#15803d';
									bg_color = '#f0fdf4';
									status_label = '<span style="font-size: 10px; color: #16a34a; font-weight: 600; margin-left: auto;">Synced</span>';
								} else {
									status_indicator = `<span style="width: 8px; height: 8px; border-radius: 50%; background-color: #ef4444; display: inline-block; box-shadow: 0 0 4px #ef4444;"></span>`;
									text_color = '#b91c1c';
									bg_color = '#fef2f2';
									status_label = '<span style="font-size: 10px; color: #dc2626; font-weight: 600; margin-left: auto;">Missing</span>';
								}
								
								const row = $(`<div style="display: flex; align-items: center; padding: 6px 10px; border-radius: 6px; gap: 8px; background-color: ${bg_color}; border: 1px solid ${bg_color !== 'transparent' ? 'transparent' : '#f1f5f9'}; cursor: ${cursor_style}; transition: transform 0.1s ease;">
									${status_indicator}
									<span style="font-size: 12px; font-weight: 600; color: ${text_color};">${item.formatted_date} (${item.day_name})</span>
									${status_label}
								</div>`);

								// Hover effect
								row.hover(
									function() { $(this).css('transform', 'scale(1.02)'); },
									function() { $(this).css('transform', 'scale(1)'); }
								);

								// Apply filter on click
								row.on('click', function(e) {
									e.preventDefault();
									listview.filter_area.clear();
									listview.filter_area.add(listview.doctype, 'date', '=', item.date);
									
									// Close dropdown
									badge.removeClass('open show');
									badge.find('#sync-status-menu').hide();
								});

								list_container.append(row);
							});
						} else {
							list_container.append('<div style="text-align: center; color: #64748b; font-size: 12px; padding: 10px;">No data found</div>');
						}
					}
				}
			});
		}

		// Initial load
		refresh_sync_status();
	}
};
