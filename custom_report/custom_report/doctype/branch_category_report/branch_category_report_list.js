// Copyright (c) 2026, talib and contributors
// For license information, please see license.txt

frappe.listview_settings['Branch Category Report'] = {
	hide_name_column: true,
	hide_name_filter: true,
	onload(listview) {
		listview.can_create = false;
		listview.default_filter_applied = false;

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
							listview.refresh();
						}
					}
				});
			}, __('Select Date'), __('Sync'));
		});

		// Create dynamic horizontal capsules container next to Sync button
		const capsules_container = $(`
			<div id="sync-status-capsules-container" style="display: inline-flex; align-items: center; gap: 4px; margin-left: 12px; vertical-align: middle; flex-wrap: nowrap; background-color: #f8fafc; padding: 3px 6px; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: inset 0 1px 2px rgba(0,0,0,0.02); max-width: 650px; overflow-x: auto; scrollbar-width: none; -ms-overflow-style: none;">
				<span class="month-label" style="font-size: 10px; font-weight: 700; color: #64748b; margin-right: 4px; text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap;">Loading...</span>
				<div class="capsules-list" style="display: inline-flex; gap: 4px; align-items: center;">
					<!-- Loaded dynamically -->
				</div>
				<style>
					#sync-status-capsules-container::-webkit-scrollbar {
						display: none;
					}
				</style>
			</div>
		`);

		if (sync_btn) {
			sync_btn.after(capsules_container);
		}
		
		listview.capsules_container = capsules_container;
	},

	refresh(listview) {
		if (listview.capsules_container) {
			frappe.call({
				method: 'custom_report.custom_report.page.sahayog_dashboard.achievement.get_current_month_sync_status',
				callback(r) {
					if (r.message) {
						const { dates_status } = r.message;
						const list_container = listview.capsules_container.find('.capsules-list');
						list_container.empty();
						
						if (dates_status && dates_status.length > 0) {
							// Chronological order (left to right)
							const chronological_dates = dates_status.slice().reverse();
							
							const first_date = new Date(chronological_dates[0].date);
							const month_name = first_date.toLocaleString('default', { month: 'short' });
							listview.capsules_container.find('.month-label').text(`${month_name}:`);

							// Find active filter date
							const current_filters = listview.filter_area.get();
							const active_date_filter = current_filters.find(f => f[1] === 'date' && f[2] === '=');
							const active_date = active_date_filter ? active_date_filter[3] : null;

							// Auto-set latest synced date on first load if no filters are active
							if (!listview.default_filter_applied && current_filters.length === 0) {
								const latest_synced = dates_status.find(item => item.has_data && !item.is_sunday);
								if (latest_synced) {
									listview.default_filter_applied = true;
									listview.filter_area.add_filter('date', '=', latest_synced.date);
									listview.refresh();
									return;
								}
							}

							chronological_dates.forEach(item => {
								const date_obj = new Date(item.date);
								const day_num = date_obj.getDate();
								
								let bg_color = '#ef4444'; // Missing (Red)
								let hover_bg = '#dc2626';
								let text_color = '#ffffff';
								let status_text = 'Missing';
								let is_active = item.date === active_date;
								let border_style = is_active ? '2px solid #0f172a' : '1px solid transparent';
								let scale_style = is_active ? 'scale(1.1)' : 'scale(1)';
								
								if (item.is_sunday) {
									bg_color = '#cbd5e1'; // Sunday (Light Grey)
									hover_bg = '#94a3b8';
									text_color = '#475569';
									status_text = 'Sunday';
								} else if (item.has_data) {
									bg_color = '#22c55e'; // Synced (Green)
									hover_bg = '#16a34a';
									text_color = '#ffffff';
									status_text = 'Synced';
								}
								
								const capsule = $(`
									<div class="day-capsule" 
										title="${item.formatted_date} (${item.day_name}) - ${status_text}"
										style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 6px; font-size: 10px; font-weight: 800; cursor: pointer; user-select: none; transition: all 0.15s ease; background-color: ${bg_color}; color: ${text_color}; border: ${border_style}; transform: ${scale_style}; box-shadow: 0 1px 2px rgba(0,0,0,0.08);"
									>
										${day_num}
									</div>
								`);
								
								// Hover effects
								capsule.hover(
									function() {
										$(this).css({
											'background-color': hover_bg,
											'transform': is_active ? 'scale(1.15) translateY(-1px)' : 'scale(1.05) translateY(-1px)',
											'box-shadow': '0 3px 6px rgba(0,0,0,0.15)'
										});
									},
									function() {
										$(this).css({
											'background-color': bg_color,
											'transform': scale_style,
											'box-shadow': '0 1px 2px rgba(0,0,0,0.08)'
										});
									}
								);
								
								// Click to filter
								capsule.on('click', function(e) {
									e.preventDefault();
									listview.filter_area.clear();
									listview.filter_area.add_filter('date', '=', item.date);
									listview.refresh();
								});
								
								list_container.append(capsule);
							});
						} else {
							list_container.append('<div style="text-align: center; color: #64748b; font-size: 10px; padding: 4px;">No data</div>');
						}
					}
				}
			});
		}
	}
};
