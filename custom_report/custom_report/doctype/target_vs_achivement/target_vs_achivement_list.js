// Copyright (c) 2025, Your Organization and contributors
// For license information, please see license.txt

frappe.listview_settings["Target Vs Achivement"] = {
	onload: function (listview) {
		listview.page.add_inner_button(__("Missing Target"), function () {
			show_missing_target_dialog(listview);
		});

		listview.page.add_inner_button(__("Bulk Upload"), function () {
			frappe.new_doc("Data Import", {
				reference_doctype: "Target Vs Achivement",
				import_type: "Insert New Records",
			});
		});
	},
};

function show_missing_target_dialog(listview) {
	let selected_fy = null;
	let missing_matrix_data = null;
	let current_filter = "all"; // 'all' or 'missing_only'
	let active_group_by = "branch"; // 'branch' or 'zone'
	let collapsed_zones = {}; // zone_name -> boolean

	const dialog = new frappe.ui.Dialog({
		title: '<span style="font-weight: 800; color: #417d81; font-size: 18px;">Target Gap Finder - Missing Targets</span>',
		size: "extra-large",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "widget_html",
			},
		],
	});

	dialog.show();
	dialog.$wrapper.find(".modal-dialog").css({
		"max-width": "96vw",
		"margin-top": "15px",
	});

	// Inject backdrop blur styling
	dialog.$wrapper.css({
		"backdrop-filter": "blur(8px)",
		"background-color": "rgba(15, 23, 42, 0.45)",
	});

	const $container = dialog.get_field("widget_html").$wrapper;

	function load_matrix_data(fy) {
		$container.html(`
			<div style="padding: 40px; text-align: center; font-family: 'Inter', sans-serif;">
				<div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem; color: #417d81 !important;"></div>
				<div style="margin-top: 12px; font-weight: 600; color: #475569;">Fetching missing targets matrix...</div>
			</div>
		`);

		frappe.call({
			method: "custom_report.custom_report.doctype.target_vs_achivement.target_vs_achivement.get_missing_targets_matrix",
			args: { financial_year: fy },
			callback: function (r) {
				if (r.message) {
					missing_matrix_data = r.message;
					selected_fy = r.message.financial_year;
					render_widget_html();
				}
			},
		});
	}

	function render_widget_html() {
		if (!missing_matrix_data) return;

		const d = missing_matrix_data;
		const fy_options = d.available_fys
			.map(
				(f) =>
					`<option value="${f}" ${f === d.financial_year ? "selected" : ""}>${f}</option>`,
			)
			.join("");

		const months = d.months;

		const html = `
			<style>
				.missing-target-modal { font-family: 'Inter', sans-serif; color: #1e293b; }
				.missing-target-controls { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 12px; background: #f8fafc; padding: 10px 14px; border-radius: 8px; border: 1px solid #e2e8f0; }
				.missing-target-summary { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
				.missing-summary-card { flex: 1; min-width: 140px; background: #ffffff; padding: 8px 14px; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease; }
				.missing-summary-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
				.missing-summary-card .label { font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; }
				.missing-summary-card .val { font-size: 18px; font-weight: 800; margin-top: 2px; }
				
				.missing-table-scroll { max-height: 65vh; overflow: auto; border: 1px solid #cbd5e1; border-radius: 8px; background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.03); }
				.missing-matrix-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11px; }
				.missing-matrix-table th { position: sticky; top: 0; z-index: 10; background: #346569; color: #ffffff; padding: 8px 5px; font-weight: 700; text-align: center; white-space: nowrap; border-bottom: 2px solid #264a4d; border-right: 1px solid rgba(255,255,255,0.1); }
				.missing-matrix-table td { padding: 6px 5px; border-bottom: 1px solid #e2e8f0; border-right: 1px solid #f1f5f9; text-align: center; vertical-align: middle; white-space: nowrap; transition: background-color 0.15s ease; }
				
				.missing-matrix-table tbody tr { transition: background-color 0.15s ease; }
				.missing-matrix-table tbody tr:hover { background-color: #f0f9ff !important; }
				.missing-matrix-table tbody tr:hover td { background-color: #f0f9ff !important; }
				.missing-matrix-table tbody td:hover { background-color: #bae6fd !important; }
				
				.target-cell-badge { display: inline-flex; align-items: center; justify-content: center; padding: 3px 8px; border-radius: 5px; font-size: 10px; font-weight: 700; cursor: pointer; text-decoration: none; transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
				.target-cell-badge.stored { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
				.target-cell-badge.stored:hover { background: #16a34a !important; color: #ffffff !important; border-color: #15803d !important; transform: translateY(-1px) scale(1.12); box-shadow: 0 3px 8px rgba(22, 163, 74, 0.35); }
				.target-cell-badge.missing { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
				.target-cell-badge.missing:hover { background: #dc2626 !important; color: #ffffff !important; border-color: #b91c1c !important; transform: translateY(-1px) scale(1.15); box-shadow: 0 3px 8px rgba(220, 38, 38, 0.4); }
				
				.filter-pill-btn { padding: 4px 10px; font-size: 11px; font-weight: 600; border-radius: 9999px; border: 1px solid #cbd5e1; background: #fff; color: #475569; cursor: pointer; transition: all 0.2s; }
				.filter-pill-btn.active { background: #417d81; color: #fff; border-color: #417d81; }
				.group-view-btn { padding: 4px 10px; font-size: 11px; font-weight: 600; border-radius: 6px; border: 1px solid #cbd5e1; background: #fff; color: #475569; cursor: pointer; transition: all 0.2s; }
				.group-view-btn.active { background: #334155; color: #fff; border-color: #334155; }
				.zone-group-header-row:hover { background: #264a4d !important; }
			</style>

			<div class="missing-target-modal">
				<div class="missing-target-controls">
					<div style="display: flex; align-items: center; gap: 6px;">
						<span style="font-weight: 700; font-size: 12px; color: #334155;">FY:</span>
						<select id="missing-fy-select" style="padding: 4px 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-weight: 700; color: #417d81; background: white; font-size: 12px;">
							${fy_options}
						</select>
					</div>

					<div style="display: flex; align-items: center; gap: 6px; margin-left: 4px;">
						<input type="text" id="missing-search-input" placeholder="Search SOL ID, Branch, Zone..." style="padding: 4px 10px; border: 1px solid #cbd5e1; border-radius: 6px; min-width: 200px; font-size: 12px; outline: none;">
					</div>

					<div style="display: flex; align-items: center; gap: 4px; margin-left: 6px;">
						<span style="font-weight: 700; font-size: 11px; color: #64748b;">View By:</span>
						<button class="group-view-btn ${active_group_by === "branch" ? "active" : ""}" data-group="branch">Branch Wise</button>
						<button class="group-view-btn ${active_group_by === "zone" ? "active" : ""}" data-group="zone">Zone Wise</button>
					</div>

					<div style="display: flex; align-items: center; gap: 6px; margin-left: auto;">
						<button class="filter-pill-btn ${current_filter === "all" ? "active" : ""}" data-filter="all">All (${d.matrix.length})</button>
						<button class="filter-pill-btn ${current_filter === "missing_only" ? "active" : ""}" data-filter="missing_only">Has Missing (${d.matrix.filter((r) => r.missing_count > 0).length})</button>
						<button id="missing-refresh-btn" style="background: #e2e8f0; color: #334155; border: none; padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; cursor: pointer; margin-left: 2px;">⟳ Refresh</button>
						<button id="missing-bulk-upload-btn" style="background: #417d81; color: #ffffff; border: none; padding: 4px 10px; border-radius: 9999px; font-weight: 700; font-size: 11px; cursor: pointer; margin-left: 2px;">📥 Bulk Upload</button>
					</div>
				</div>

				<div class="missing-target-summary">
					<div class="missing-summary-card" style="border-left: 4px solid #3b82f6;">
						<div class="label">Total Branches</div>
						<div class="val" style="color: #1e3a8a;">${d.summary.total_branches}</div>
					</div>
					<div class="missing-summary-card" style="border-left: 4px solid #10b981;">
						<div class="label">Stored Targets</div>
						<div class="val" style="color: #065f46;">${d.summary.total_stored}</div>
					</div>
					<div class="missing-summary-card" style="border-left: 4px solid #ef4444;">
						<div class="label">Missing Targets</div>
						<div class="val" style="color: #991b1b;">${d.summary.total_missing}</div>
					</div>
				</div>

				<div class="missing-table-scroll">
					<table class="missing-matrix-table">
						<thead>
							<tr>
								<th style="width: 35px;">Sr</th>
								<th style="text-align: left; padding-left: 10px; min-width: 160px;">SOL & Branch</th>
								<th style="min-width: 130px;">Zone / Region</th>
								<th style="width: 70px;">Type</th>
								${months.map((m) => `<th>${m}</th>`).join("")}
								<th style="background: #264a4d;">Yearly</th>
								<th style="background: #991b1b; color: #fff;">Missing</th>
							</tr>
						</thead>
						<tbody id="missing-matrix-tbody">
							${render_matrix_tbody_content(d.matrix)}
						</tbody>
					</table>
				</div>
			</div>
		`;

		$container.html(html);
		attach_events();
	}

	function format_val(val) {
		if (!val) return "0";
		if (val >= 10000000) return (val / 10000000).toFixed(1) + "Cr";
		if (val >= 100000) return (val / 100000).toFixed(1) + "L";
		if (val >= 1000) return (val / 1000).toFixed(1) + "K";
		return val;
	}

	function get_filtered_matrix(matrix_list) {
		let filtered = matrix_list;
		const search_term = ($container.find("#missing-search-input").val() || "")
			.toLowerCase()
			.trim();

		if (current_filter === "missing_only") {
			filtered = filtered.filter((r) => r.missing_count > 0);
		}

		if (search_term) {
			filtered = filtered.filter(
				(r) =>
					r.sol_id.toLowerCase().includes(search_term) ||
					r.branch_name.toLowerCase().includes(search_term) ||
					r.zone.toLowerCase().includes(search_term) ||
					r.region.toLowerCase().includes(search_term),
			);
		}
		return filtered;
	}

	function render_matrix_tbody_content(matrix_list) {
		const filtered = get_filtered_matrix(matrix_list);
		if (filtered.length === 0) {
			return `<tr><td colspan="18" style="padding: 30px; color: #64748b; font-weight: 600;">No branches match current search / filter.</td></tr>`;
		}

		if (active_group_by === "zone") {
			return render_zone_wise_tbody(filtered);
		} else {
			return render_branch_rows_html(filtered);
		}
	}

	function render_zone_wise_tbody(filtered_branches) {
		const months = missing_matrix_data.months;
		const zone_map = {};

		filtered_branches.forEach((b) => {
			const z = b.zone || "Unassigned Zone";
			if (!zone_map[z]) {
				zone_map[z] = {
					zone_name: z,
					branches: [],
					missing_count: 0,
					stored_count: 0,
				};
			}
			zone_map[z].branches.push(b);
			zone_map[z].missing_count += b.missing_count;
			zone_map[z].stored_count += b.stored_count;
		});

		let html = "";
		Object.keys(zone_map).forEach((z_name) => {
			const z_data = zone_map[z_name];
			const is_collapsed = !!collapsed_zones[z_name];
			const icon = is_collapsed ? "►" : "▼";
			const row_display = is_collapsed ? "display: none;" : "";

			// Calculate Zone Totals
			const zone_monthly_totals = {};
			const zone_ytd_totals = {};
			let zone_yearly_total = 0;

			months.forEach((m) => {
				zone_monthly_totals[m] = 0;
				zone_ytd_totals[m] = 0;
			});

			z_data.branches.forEach((b) => {
				months.forEach((m) => {
					if (b.months && b.months[m] && b.months[m].stored) {
						zone_monthly_totals[m] += b.months[m].target || 0;
					}
					if (b.ytd_months && b.ytd_months[m] && b.ytd_months[m].stored) {
						zone_ytd_totals[m] += b.ytd_months[m].target || 0;
					}
				});
				if (b.yearly && b.yearly.stored) {
					zone_yearly_total += b.yearly.target || 0;
				}
			});

			const badge = z_data.missing_count > 0
				? `<span style="float: right; background: #fee2e2; color: #991b1b; padding: 2px 10px; border-radius: 9999px; font-size: 10px; font-weight: 800;">${z_data.missing_count} Missing</span>`
				: `<span style="float: right; background: #dcfce7; color: #166534; padding: 2px 10px; border-radius: 9999px; font-size: 10px; font-weight: 800;">Complete</span>`;

			// Zone Collapsible Header
			html += `
				<tr class="zone-group-header-row" data-zone="${z_name}" style="background: #2b5558; color: #ffffff; cursor: pointer; font-weight: 800; border-top: 2px solid #1e3a8a;">
					<td colspan="18" style="text-align: left; padding: 8px 12px; font-size: 12px; background: #2b5558; color: #ffffff;">
						<span class="zone-icon" style="display: inline-block; width: 14px;">${icon}</span>
						<span>📍 ${z_name}</span>
						<span style="font-weight: 500; font-size: 11px; opacity: 0.85; margin-left: 8px;">(${z_data.branches.length} Branches | Yearly Total: ₹${format_val(zone_yearly_total)})</span>
						${badge}
					</td>
				</tr>
			`;

			// Zone Total Summary Row
			const monthly_sums_html = months
				.map((m) => `<td style="font-weight: 800; color: #166534; background: #f0fdf4;">₹${format_val(zone_monthly_totals[m])}</td>`)
				.join("");

			const ytd_sums_html = months
				.map((m) => `<td style="font-weight: 800; color: #1e40af; background: #eff6ff;">₹${format_val(zone_ytd_totals[m])}</td>`)
				.join("");

			html += `
				<tr data-zone-row="${z_name}" style="${row_display} background: #e2e8f0; border-bottom: 2px solid #94a3b8;">
					<td rowspan="2" colspan="3" style="text-align: left; padding-left: 12px; font-weight: 800; color: #0f172a; background: #e2e8f0; vertical-align: middle;">
						📊 ZONE TARGET TOTALS (${z_name})
					</td>
					<td style="font-weight: 800; color: #15803d; background: #dcfce7;">Monthly Sum</td>
					${monthly_sums_html}
					<td rowspan="2" style="font-weight: 800; color: #0f172a; background: #cbd5e1; vertical-align: middle;">₹${format_val(zone_yearly_total)}</td>
					<td rowspan="2" style="background: #e2e8f0; vertical-align: middle;">${badge}</td>
				</tr>
				<tr data-zone-row="${z_name}" style="${row_display} background: #e2e8f0; border-bottom: 2px solid #94a3b8;">
					<td style="font-weight: 800; color: #1d4ed8; background: #dbeafe;">YTD Sum</td>
					${ytd_sums_html}
				</tr>
			`;

			// Individual Branch Rows
			const branches_html = render_branch_rows_html(z_data.branches, z_name, row_display);
			html += branches_html;
		});

		return html;
	}

	function render_branch_rows_html(branches_list, zone_attr, row_style) {
		const months = missing_matrix_data.months;
		const style_attr = row_style ? `style="${row_style}"` : "";
		const data_attr = zone_attr ? `data-zone-row="${zone_attr}"` : "";

		return branches_list
			.map((row, i) => {
				let month_tds = months
					.map((m) => {
						const cell = row.months[m];
						if (cell && cell.stored) {
							return `<td><a class="target-cell-badge stored" href="/app/target-vs-achivement/${cell.name}" target="_blank" title="View Monthly Target: ${cell.name}">✓ ${format_val(cell.target)}</a></td>`;
						} else {
							return `<td><span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="Monthly" data-month="${m}" title="Click to Add Monthly Target for ${m}">✕ Missing</span></td>`;
						}
					})
					.join("");

				let ytd_tds = months
					.map((m) => {
						const cell = row.ytd_months ? row.ytd_months[m] : null;
						if (cell && cell.stored) {
							return `<td><a class="target-cell-badge stored" href="/app/target-vs-achivement/${cell.name}" target="_blank" title="View YTD Target: ${cell.name}">✓ ${format_val(cell.target)}</a></td>`;
						} else {
							return `<td><span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="YTD" data-month="${m}" title="Click to Add YTD Target for ${m}">✕ Missing</span></td>`;
						}
					})
					.join("");

				let yearly_td = row.yearly && row.yearly.stored
					? `<a class="target-cell-badge stored" href="/app/target-vs-achivement/${row.yearly.name}" target="_blank" title="View Yearly Target">✓ ${format_val(row.yearly.target)}</a>`
					: `<span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="Yearly" data-month="" title="Click to Add Yearly Target">✕ Missing</span>`;

				let missing_badge =
					row.missing_count > 0
						? `<span style="background: #fef2f2; color: #ef4444; font-weight: 800; padding: 3px 8px; border-radius: 9999px; font-size: 11px;">${row.missing_count} Missing</span>`
						: `<span style="background: #f0fdf4; color: #166534; font-weight: 800; padding: 3px 8px; border-radius: 9999px; font-size: 11px;">Complete</span>`;

				return `
					<tr ${data_attr} ${style_attr} style="border-top: 2px solid #cbd5e1; background: #ffffff;">
						<td rowspan="2" style="vertical-align: middle; font-weight: 700; background: #f8fafc; border-right: 1px solid #e2e8f0;">${i + 1}</td>
						<td rowspan="2" style="text-align: left; padding-left: 10px; font-weight: 700; color: #0f172a; vertical-align: middle; background: #f8fafc; border-right: 1px solid #e2e8f0;">${row.sol_id} - ${row.branch_name}</td>
						<td rowspan="2" style="color: #64748b; font-weight: 500; vertical-align: middle; background: #f8fafc; border-right: 1px solid #e2e8f0;">${row.zone} / ${row.region}</td>
						<td style="font-weight: 800; color: #417d81; background: #f0fdf4; border-right: 1px solid #e2e8f0;">Monthly</td>
						${month_tds}
						<td rowspan="2" style="vertical-align: middle; background: #f8fafc; border-right: 1px solid #e2e8f0;">${yearly_td}</td>
						<td rowspan="2" style="vertical-align: middle; background: #f8fafc;">${missing_badge}</td>
					</tr>
					<tr ${data_attr} ${style_attr} style="background: #ffffff; border-bottom: 1px solid #cbd5e1;">
						<td style="font-weight: 800; color: #1e3a8a; background: #eff6ff; border-right: 1px solid #e2e8f0;">YTD</td>
						${ytd_tds}
					</tr>
				`;
			})
			.join("");
	}

	function attach_events() {
		$container.find("#missing-fy-select").on("change", function () {
			load_matrix_data($(this).val());
		});

		$container.find("#missing-search-input").on("input", function () {
			$container.find("#missing-matrix-tbody").html(render_matrix_tbody_content(missing_matrix_data.matrix));
		});

		$container.find(".filter-pill-btn").on("click", function () {
			current_filter = $(this).data("filter");
			$container.find(".filter-pill-btn").removeClass("active");
			$(this).addClass("active");
			$container.find("#missing-matrix-tbody").html(render_matrix_tbody_content(missing_matrix_data.matrix));
		});

		$container.find(".group-view-btn").on("click", function () {
			active_group_by = $(this).data("group");
			$container.find(".group-view-btn").removeClass("active");
			$(this).addClass("active");
			$container.find("#missing-matrix-tbody").html(render_matrix_tbody_content(missing_matrix_data.matrix));
		});

		$container.find("#missing-refresh-btn").on("click", function () {
			load_matrix_data(selected_fy);
		});

		$container.find("#missing-bulk-upload-btn").on("click", function () {
			dialog.hide();
			frappe.new_doc("Data Import", {
				reference_doctype: "Target Vs Achivement",
				import_type: "Insert New Records",
			});
		});

		// Zone Accordion Collapse / Expand Toggle
		$container.off("click", ".zone-group-header-row").on("click", ".zone-group-header-row", function () {
			const zone_name = $(this).data("zone");
			collapsed_zones[zone_name] = !collapsed_zones[zone_name];
			const $rows = $container.find(`tr[data-zone-row="${zone_name}"]`);
			const $icon = $(this).find(".zone-icon");

			if (collapsed_zones[zone_name]) {
				$rows.hide();
				$icon.text("►");
			} else {
				$rows.show();
				$icon.text("▼");
			}
		});

		// Click missing badge to quickly add target
		$container.off("click", ".target-cell-badge.missing").on("click", ".target-cell-badge.missing", function () {
			const sol_id = $(this).data("sol");
			const type = $(this).data("type");
			const month = $(this).data("month");

			const new_doc_args = {
				sol_id: sol_id,
				financial_year: selected_fy,
				type: type,
			};
			if ((type === "Monthly" || type === "YTD") && month) {
				new_doc_args.month = month;
			}

			frappe.new_doc("Target Vs Achivement", new_doc_args);
		});
	}

	// Initial Load
	load_matrix_data(null);
}
