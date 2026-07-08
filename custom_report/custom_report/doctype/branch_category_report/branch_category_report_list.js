// Copyright (c) 2026, talib and contributors
// For license information, please see license.txt

frappe.listview_settings['Branch Category Report'] = {
	hide_name_column: true,
	hide_name_filter: true,
	onload(listview) {
		listview.can_create = false;
		listview.default_filter_applied = false;
	},

	refresh(listview) {
		// Ensure can_create is false to hide Add button
		listview.can_create = false;
		if (listview.page.btn_primary) {
			listview.page.btn_primary.hide();
		}
		listview.page.wrapper.find('.primary-action').hide();

		// Get JQuery actions wrapper safely
		const actions_wrapper = listview.page.actions ? $(listview.page.actions) : listview.page.wrapper.find('.page-actions');

		// Find or add Sync button
		let sync_btn = actions_wrapper.find('button:contains("Sync Achievement Data")');
		if (!sync_btn.length) {
			sync_btn = listview.page.wrapper.find('.page-actions button:contains("Sync Achievement Data")');
		}

		if (!sync_btn.length) {
			listview.page.add_inner_button(__('Sync Achievement Data'), () => {
				let d = new frappe.ui.Dialog({
					title: __('Select Date'),
					fields: [
						{
							label: __('Date'),
							fieldname: 'date',
							fieldtype: 'Date',
							default: frappe.datetime.add_days(frappe.datetime.get_today(), -1),
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
						frappe.call({
							method: 'custom_report.custom_report.page.sahayog_dashboard.achievement.generate_and_save_branch_category_report',
							args: {
								input_date: selected_date
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
					}
				});
				d.show();
			});

			// Fetch again
			sync_btn = actions_wrapper.find('button:contains("Sync Achievement Data")');
			if (!sync_btn.length) {
				sync_btn = listview.page.wrapper.find('.page-actions button:contains("Sync Achievement Data")');
			}
		}

		// Find or add Calendar button natively
		let calendar_btn = actions_wrapper.find('button:contains("Synced")');
		if (!calendar_btn.length) {
			calendar_btn = actions_wrapper.find('button:contains("Checking")');
		}
		if (!calendar_btn.length) {
			calendar_btn = listview.page.wrapper.find('.page-actions button:contains("Synced")');
		}
		if (!calendar_btn.length) {
			calendar_btn = listview.page.wrapper.find('.page-actions button:contains("Checking")');
		}

		if (!calendar_btn.length) {
			calendar_btn = listview.page.add_inner_button(__('Checking status...'), () => {
				const menu = $('#sync-status-menu');
				const isOpen = menu.is(':visible');
				$('.dropdown-menu').not(menu).hide();
				if (!isOpen) {
					const offset = calendar_btn.offset();
					menu.css({
						top: (offset.top + calendar_btn.outerHeight() + 5) + 'px',
						left: (offset.left + calendar_btn.outerWidth() - menu.outerWidth()) + 'px',
						position: 'absolute',
						zIndex: 1050
					}).show();
				} else {
					menu.hide();
				}
			});

			// Add styling to make it look premium
			calendar_btn.css({
				'border-radius': '6px',
				'padding': '4px 10px',
				'font-weight': '600',
				'display': 'inline-flex',
				'align-items': 'center',
				'justify-content': 'center',
				'box-shadow': '0 1px 2px rgba(0, 0, 0, 0.05)',
				'gap': '6px',
				'height': '26px',
				'vertical-align': 'middle'
			});
		}

		// Create global dropdown menu on body if not exists
		let menu = $('#sync-status-menu');
		if (!menu.length) {
			menu = $(`
				<div id="sync-status-menu" style="width: 220px; padding: 12px; border-radius: 8px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; background-color: #ffffff; z-index: 1050; position: absolute; display: none;">
					<div class="dropdown-header-custom" style="font-weight: 700; padding: 0 4px 8px 4px; border-bottom: 1px solid #f1f5f9; color: #0f172a; font-size: 12px; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; letter-spacing: 0.5px;">
						<span>Sync Status</span>
						<span class="month-label" style="font-size: 11px; font-weight: 600; color: #64748b;">Loading...</span>
					</div>
					
					<!-- Calendar Grid -->
					<div class="calendar-grid" style="margin-top: 8px;">
						<!-- Weekdays Header -->
						<div class="weekdays-header" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; text-align: center; font-size: 9px; font-weight: 800; color: #94a3b8; margin-bottom: 6px;">
							<div>M</div><div>T</div><div>W</div><div>T</div><div>F</div><div>S</div><div style="color: #ef4444;">S</div>
						</div>
						<!-- Days Grid -->
						<div class="days-grid" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; justify-items: center; align-items: center;">
							<!-- Loaded dynamically -->
						</div>
					</div>
				</div>
			`);
			$('body').append(menu);

			// Document global click to close dropdown
			$(document).off('click.sync-status-dropdown').on('click.sync-status-dropdown', function(e) {
				if (!$(e.target).closest(calendar_btn).length && !$(e.target).closest('#sync-status-menu').length) {
					$('#sync-status-menu').hide();
				}
			});
		}

		// Fetch and update status
		frappe.call({
			method: 'custom_report.custom_report.page.sahayog_dashboard.achievement.get_current_month_sync_status',
			callback(r) {
				if (r.message) {
					const { dates_status, synced_count, total_days } = r.message;
					
					// Update Button Badge Status content
					let dot_color = '#cbd5e1';
					if (synced_count === total_days && total_days > 0) {
						dot_color = '#22c55e';
						calendar_btn.css({
							'border-color': '#bbf7d0',
							'background-color': '#f0fdf4',
							'color': '#15803d'
						});
					} else if (synced_count > 0) {
						dot_color = '#eab308';
						calendar_btn.css({
							'border-color': '#fef08a',
							'background-color': '#fefce8',
							'color': '#a16207'
						});
					} else {
						dot_color = '#ef4444';
						calendar_btn.css({
							'border-color': '#fecaca',
							'background-color': '#fef2f2',
							'color': '#b91c1c'
						});
					}

					calendar_btn.html(`
						<span class="indicator-dot" style="width: 8px; height: 8px; border-radius: 50%; background-color: ${dot_color}; display: inline-block; margin-right: 6px;"></span>
						<span>${synced_count}/${total_days} Synced</span>
					`);

					const days_container = menu.find('.days-grid');
					days_container.empty();
					
					if (dates_status && dates_status.length > 0) {
						// Chronological order (left to right)
						const chronological_dates = dates_status.slice().reverse();
						
						const first_date = new Date(chronological_dates[0].date);
						const month_name = first_date.toLocaleString('default', { month: 'short', year: '2-digit' });
						menu.find('.month-label').text(month_name);

						// Find active filter date
						const current_filters = listview.filter_area.get();
						const active_date_filter = current_filters.find(f => f[1] === 'date' && f[2] === '=');
						const active_date = active_date_filter ? active_date_filter[3] : null;

						// Auto-set latest synced date on first load if no filters are active
						if (!listview.default_filter_applied && current_filters.length === 0) {
							const latest_synced = dates_status.find(item => item.has_data && !item.is_sunday);
							if (latest_synced) {
								listview.default_filter_applied = true;
								listview.filter_area.add(listview.doctype, 'date', '=', latest_synced.date);
								return;
							}
						}

						// Render empty placeholders for days before the 1st
						let start_day_index = first_date.getDay() - 1; // Sunday is 0, Mon is 1
						if (start_day_index < 0) start_day_index = 6;

						for (let i = 0; i < start_day_index; i++) {
							days_container.append('<div style="width: 22px; height: 22px;"></div>');
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
							let is_clickable = true;
							
							if (item.is_future) {
								bg_color = '#f8fafc';
								hover_bg = '#f8fafc';
								text_color = '#cbd5e1';
								border_style = '1px dashed #cbd5e1';
								status_text = 'Future Date';
								is_clickable = false;
								scale_style = 'scale(1)';
							} else if (item.is_sunday) {
								bg_color = '#cbd5e1';
								hover_bg = '#94a3b8';
								text_color = '#475569';
								status_text = 'Sunday';
							} else if (item.has_data) {
								bg_color = '#22c55e';
								hover_bg = '#16a34a';
								text_color = '#ffffff';
								status_text = 'Synced';
							}
							
							const cursor_style = is_clickable ? 'pointer' : 'not-allowed';
							
							const capsule = $(`
								<div class="day-capsule" 
									title="${item.formatted_date} (${item.day_name}) - ${status_text}"
									style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 6px; font-size: 10px; font-weight: 800; cursor: ${cursor_style}; user-select: none; transition: all 0.15s ease; background-color: ${bg_color}; color: ${text_color}; border: ${border_style}; transform: ${scale_style}; box-shadow: ${item.is_future ? 'none' : '0 1px 2px rgba(0,0,0,0.08)'};"
								>
									${day_num}
								</div>
							`);
							
							if (is_clickable) {
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
								
								capsule.on('click', function(e) {
									e.preventDefault();
									
									// Clear existing filters and natively add new filter to filter area
									listview.filter_area.clear();
									listview.filter_area.add(listview.doctype, 'date', '=', item.date);
									
									$('#sync-status-menu').hide();
								});
							}
							
							days_container.append(capsule);
						});
					} else {
						days_container.append('<div style="grid-column: span 7; text-align: center; color: #64748b; font-size: 10px; padding: 4px;">No data</div>');
					}
				}
			}
		});
	}
};
