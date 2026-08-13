// Copyright (c) 2025, Your Organization and contributors
// For license information, please see license.txt

frappe.listview_settings["Target Vs Achivement"] = {
	onload: function (listview) {
		const allowed_roles = ["MIS Admin", "System Manager"];
		const has_access = allowed_roles.some((role) => frappe.user.has_role(role));

		if (has_access) {
			listview.page.add_inner_button(__("Missing Target"), function () {
				show_missing_target_dialog(listview);
			});

			listview.page.add_inner_button(__("Bulk Upload"), function () {
				frappe.new_doc("Data Import", {
					reference_doctype: "Target Vs Achivement",
					import_type: "Insert New Records",
				});
			});
		}
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
				.missing-matrix-table th { position: sticky; top: 0; z-index: 10; background: #346569; color: #ffffff; padding: 8px 5px; font-weight: 700; text-align: center; white-space: nowrap; border-bottom: 2px solid #264a4d; border-right: 1px solid rgba(255,255,255,0.1); transition: all 0.15s ease; }
				.missing-matrix-table td { padding: 6px 5px; border-bottom: 1px solid #e2e8f0; border-right: 1px solid #f1f5f9; text-align: center; vertical-align: middle; white-space: nowrap; transition: background-color 0.15s ease; }
				
				/* Row Background Highlights - Vibrant Pre-Applied Alternating Colors */
				.missing-matrix-table tbody tr.monthly-row { background-color: #d1fae5 !important; }
				.missing-matrix-table tbody tr.monthly-row td { background-color: #d1fae5 !important; border-bottom: 1px solid #cbd5e1; }
				.missing-matrix-table tbody tr.monthly-row:hover td { background-color: #a7f3d0 !important; }
				
				.missing-matrix-table tbody tr.ytd-row { background-color: #dbeafe !important; border-bottom: 3px solid #64748b !important; }
				.missing-matrix-table tbody tr.ytd-row td { background-color: #dbeafe !important; border-bottom: 3px solid #64748b !important; }
				.missing-matrix-table tbody tr.ytd-row:hover td { background-color: #bfdbfe !important; }

				/* Excel Row Highlight: applied to tr[data-branch-sol] */
				.missing-matrix-table tbody tr.branch-hover-highlight td {
					background-color: #bae6fd !important;
				}
				.missing-matrix-table tbody tr.branch-hover-highlight td.branch-name-td {
					background-color: #38bdf8 !important;
					color: #0c4a6e !important;
					font-weight: 800 !important;
				}

				/* Excel-Style Crosshair Column Header Highlight */
				.excel-col-header-highlight {
					background-color: #0284c7 !important;
					color: #ffffff !important;
					font-weight: 900 !important;
					font-size: 12px !important;
					box-shadow: 0 4px 12px rgba(2, 132, 199, 0.45) !important;
					border-bottom: 3px solid #0369a1 !important;
				}

				/* Excel-Style Crosshair Column Cells Light Highlight */
				.excel-col-cells-highlight {
					background-color: #7dd3fc !important;
				}

				/* Active Hovered Cell Intense Outline */
				.excel-active-cell-highlight {
					outline: 2px solid #0284c7 !important;
					outline-offset: -1px;
					background-color: #38bdf8 !important;
					z-index: 15;
				}

				/* Type Capsule Badges - High Visibility Solid Capsules */
				.type-capsule { display: inline-flex; align-items: center; justify-content: center; padding: 3px 9px; border-radius: 9999px; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
				.type-capsule.monthly { background: #15803d; color: #ffffff; border: 1px solid #166534; }
				.type-capsule.ytd { background: #1d4ed8; color: #ffffff; border: 1px solid #1e40af; }
				
				/* Target Cell Badges: Stored vs Missing Font & Color Differentiation */
				.target-cell-badge { display: inline-flex; align-items: center; justify-content: center; padding: 3px 8px; border-radius: 5px; font-size: 10px; font-weight: 800; cursor: pointer; text-decoration: none; transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
				
				/* Stored Target: Bold Dark Green on Soft Emerald Background */
				.target-cell-badge.stored { background: #dcfce7; color: #14532d; border: 1px solid #86efac; font-weight: 800; }
				.target-cell-badge.stored:hover { background: #16a34a !important; color: #ffffff !important; border-color: #15803d !important; transform: translateY(-1px) scale(1.12); box-shadow: 0 3px 8px rgba(22, 163, 74, 0.35); }
				
				/* Missing Target: High-Contrast Crimson Red Badge */
				.target-cell-badge.missing { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; font-weight: 800; letter-spacing: 0.2px; }
				.target-cell-badge.missing:hover { background: #dc2626 !important; color: #ffffff !important; border-color: #b91c1c !important; transform: translateY(-1px) scale(1.15); box-shadow: 0 3px 8px rgba(220, 38, 38, 0.4); }
				
				.filter-pill-btn { padding: 4px 10px; font-size: 11px; font-weight: 600; border-radius: 9999px; border: 1px solid #cbd5e1; background: #fff; color: #475569; cursor: pointer; transition: all 0.2s; }
				.filter-pill-btn.active { background: #417d81; color: #fff; border-color: #417d81; }
				.group-view-btn { padding: 4px 10px; font-size: 11px; font-weight: 600; border-radius: 6px; border: 1px solid #cbd5e1; background: #fff; color: #475569; cursor: pointer; transition: all 0.2s; }
				.group-view-btn.active { background: #334155; color: #fff; border-color: #334155; }
				.zone-summary-row:hover td { background-color: #e2e8f0 !important; }
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

				<div class="missing-target-summary" id="missing-summary-cards-container">
					${render_summary_cards_html()}
				</div>

				<div class="missing-table-scroll">
					<table class="missing-matrix-table">
						<thead>
							<tr>
								<th style="width: 35px;">Sr</th>
								<th style="text-align: left; padding-left: 10px; min-width: 160px;">SOL & Branch</th>
								<th style="min-width: 130px;">Zone / Region</th>
								<th style="width: 75px;">Type</th>
								${months.map((m) => `<th data-month-col="${m}">${m}</th>`).join("")}
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

	function render_summary_cards_html() {
		if (!missing_matrix_data || !missing_matrix_data.summary) return "";
		const s = missing_matrix_data.summary;
		const is_zone = active_group_by === "zone";

		return `
			<div class="missing-summary-card" style="border-left: 4px solid #3b82f6;">
				<div class="label">${is_zone ? "Total Zones" : "Total Branches"}</div>
				<div class="val" style="color: #1e3a8a;">${is_zone ? `${s.total_zones} Zones` : `${s.total_branches} Branches`}</div>
			</div>
			<div class="missing-summary-card" style="border-left: 4px solid #8b5cf6;">
				<div class="label">Total Target Sum</div>
				<div class="val" style="color: #5b21b6;">₹${format_val(s.total_target_amount || 0)}</div>
			</div>
		`;
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
		Object.keys(zone_map).forEach((z_name, idx) => {
			const z_data = zone_map[z_name];
			const is_collapsed = collapsed_zones[z_name] !== false;
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
				? `<span style="background: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 9999px; font-size: 10px; font-weight: 800;">${z_data.missing_count} Missing</span>`
				: `<span style="background: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 9999px; font-size: 10px; font-weight: 800;">Complete</span>`;

			const monthly_sums_tds = months
				.map((m) => `<td data-month-col="${m}" style="font-weight: 800; color: #166534; background: #d1fae5;">₹${format_val(zone_monthly_totals[m])}</td>`)
				.join("");

			const ytd_sums_tds = months
				.map((m) => `<td data-month-col="${m}" style="font-weight: 800; color: #1e40af; background: #dbeafe;">₹${format_val(zone_ytd_totals[m])}</td>`)
				.join("");

			// Zone Merged 2-Row Summary (Row 1: Monthly Total, Row 2: YTD Total)
			html += `
				<tr class="zone-group-header-row zone-summary-row monthly-row" data-zone="${z_name}" style="border-top: 3px solid #346569; background: #d1fae5; cursor: pointer;">
					<td rowspan="2" style="vertical-align: middle; font-weight: 800; background: #e2e8f0; border-right: 1px solid #cbd5e1;">${idx + 1}</td>
					<td rowspan="2" style="text-align: left; padding-left: 10px; font-weight: 800; color: #0f172a; vertical-align: middle; background: #e2e8f0; border-right: 1px solid #cbd5e1;">
						<span class="zone-icon" style="display: inline-block; width: 14px; font-weight: 900;">${icon}</span>
						<span>📍 ${z_name}</span>
						<span style="font-weight: 600; font-size: 10px; color: #64748b; display: block; margin-top: 2px;">(${z_data.branches.length} Branches)</span>
					</td>
					<td rowspan="2" style="color: #475569; font-weight: 700; vertical-align: middle; background: #e2e8f0; border-right: 1px solid #cbd5e1;">Zone Total</td>
					<td style="background: #d1fae5; border-right: 1px solid #cbd5e1;"><span class="type-capsule monthly">Monthly</span></td>
					${monthly_sums_tds}
					<td rowspan="2" style="vertical-align: middle; font-weight: 800; color: #0f172a; background: #e2e8f0; border-right: 1px solid #cbd5e1;">₹${format_val(zone_yearly_total)}</td>
					<td rowspan="2" style="vertical-align: middle; background: #e2e8f0;">${badge}</td>
				</tr>
				<tr class="zone-group-header-row zone-summary-row ytd-row" data-zone="${z_name}" style="background: #dbeafe; cursor: pointer; border-bottom: 2px solid #cbd5e1;">
					<td style="background: #dbeafe; border-right: 1px solid #cbd5e1;"><span class="type-capsule ytd">YTD</span></td>
					${ytd_sums_tds}
				</tr>
			`;

			// Individual Branch Rows for this Zone (Collapsible)
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
							return `<td data-month-col="${m}" style="background: #d1fae5;"><a class="target-cell-badge stored" data-sol="${row.sol_id}" data-type="Monthly" data-month="${m}" data-target="${cell.target}" href="/app/target-vs-achivement/${cell.name}" target="_blank" title="Click to edit Target: ${cell.name}">✓ ${format_val(cell.target)}</a></td>`;
						} else {
							return `<td data-month-col="${m}" style="background: #d1fae5;"><span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="Monthly" data-month="${m}" title="Click to Add Monthly Target for ${m}">✕ Missing</span></td>`;
						}
					})
					.join("");

				let ytd_tds = months
					.map((m) => {
						const cell = row.ytd_months ? row.ytd_months[m] : null;
						if (cell && cell.stored) {
							return `<td data-month-col="${m}" style="background: #dbeafe;"><a class="target-cell-badge stored" data-sol="${row.sol_id}" data-type="YTD" data-month="${m}" data-target="${cell.target}" href="/app/target-vs-achivement/${cell.name}" target="_blank" title="Click to edit YTD Target: ${cell.name}">✓ ${format_val(cell.target)}</a></td>`;
						} else {
							return `<td data-month-col="${m}" style="background: #dbeafe;"><span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="YTD" data-month="${m}" title="Click to Add YTD Target for ${m}">✕ Missing</span></td>`;
						}
					})
					.join("");

				let yearly_td = row.yearly && row.yearly.stored
					? `<a class="target-cell-badge stored" data-sol="${row.sol_id}" data-type="Yearly" data-month="" data-target="${row.yearly.target}" href="/app/target-vs-achivement/${row.yearly.name}" target="_blank" title="Click to edit Yearly Target">✓ ${format_val(row.yearly.target)}</a>`
					: `<span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="Yearly" data-month="" title="Click to Add Yearly Target">✕ Missing</span>`;

				let missing_badge =
					row.missing_count > 0
						? `<span style="background: #fee2e2; color: #ef4444; font-weight: 800; padding: 3px 8px; border-radius: 9999px; font-size: 11px;">${row.missing_count} Missing</span>`
						: `<span style="background: #f0fdf4; color: #166534; font-weight: 800; padding: 3px 8px; border-radius: 9999px; font-size: 11px;">Complete</span>`;

				return `
					<tr ${data_attr} ${style_attr} class="monthly-row branch-group-row" data-branch-sol="${row.sol_id}" style="border-top: 2px solid #94a3b8; background: #d1fae5;">
						<td rowspan="2" class="branch-merged-cell" style="vertical-align: middle; font-weight: 700; background: #f8fafc; border-right: 1px solid #cbd5e1; border-bottom: 3px solid #64748b !important;">${i + 1}</td>
						<td rowspan="2" class="branch-merged-cell branch-name-td" style="text-align: left; padding-left: 10px; font-weight: 700; color: #0f172a; vertical-align: middle; background: #f8fafc; border-right: 1px solid #cbd5e1; border-bottom: 3px solid #64748b !important;">${row.sol_id} - ${row.branch_name}</td>
						<td rowspan="2" class="branch-merged-cell" style="color: #64748b; font-weight: 500; vertical-align: middle; background: #f8fafc; border-right: 1px solid #cbd5e1; border-bottom: 3px solid #64748b !important;">${row.zone} / ${row.region}</td>
						<td style="background: #d1fae5; border-right: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1;"><span class="type-capsule monthly">Monthly</span></td>
						${month_tds}
						<td rowspan="2" class="branch-merged-cell" style="vertical-align: middle; background: #f8fafc; border-right: 1px solid #cbd5e1; border-bottom: 3px solid #64748b !important;">${yearly_td}</td>
						<td rowspan="2" class="branch-merged-cell" style="vertical-align: middle; background: #f8fafc; border-bottom: 3px solid #64748b !important;">${missing_badge}</td>
					</tr>
					<tr ${data_attr} ${style_attr} class="ytd-row branch-group-row" data-branch-sol="${row.sol_id}" style="background: #dbeafe; border-bottom: 3px solid #64748b !important;">
						<td style="background: #dbeafe; border-right: 1px solid #cbd5e1; border-bottom: 3px solid #64748b !important;"><span class="type-capsule ytd">YTD</span></td>
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
			$container.find("#missing-summary-cards-container").html(render_summary_cards_html());
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
			const currently_collapsed = collapsed_zones[zone_name] !== false;
			collapsed_zones[zone_name] = !currently_collapsed;
			const $rows = $container.find(`tr[data-zone-row="${zone_name}"]`);
			const $icon = $container.find(`tr[data-zone="${zone_name}"]`).find(".zone-icon");

			if (collapsed_zones[zone_name]) {
				$rows.hide();
				$icon.text("►");
			} else {
				$rows.show();
				$icon.text("▼");
			}
		});

		// Excel-Style Crosshair Hover (Pure CSS Class Delegation - Zero Flicker)
		$container.off("mouseenter mouseleave", "td").on({
			mouseenter: function () {
				const $td = $(this);
				const $row = $td.closest("tr");
				const sol_id = $row.attr("data-branch-sol");
				const month = $td.attr("data-month-col");
				const zone = $row.attr("data-zone");

				// Clear previous highlights
				$container.find(".branch-hover-highlight").removeClass("branch-hover-highlight");
				$container.find(".excel-col-header-highlight").removeClass("excel-col-header-highlight");
				$container.find(".excel-col-cells-highlight").removeClass("excel-col-cells-highlight");
				$container.find(".excel-active-cell-highlight").removeClass("excel-active-cell-highlight");

				// 1. Highlight Row Group & Branch Name Cell
				if (sol_id) {
					$container.find(`tr[data-branch-sol="${sol_id}"]`).addClass("branch-hover-highlight");
				} else if (zone) {
					$container.find(`tr[data-zone="${zone}"]`).addClass("branch-hover-highlight");
				}

				// 2. Highlight Month Column Header & Column Cells
				if (month) {
					$container.find(`th[data-month-col="${month}"]`).addClass("excel-col-header-highlight");
					$container.find(`td[data-month-col="${month}"]`).addClass("excel-col-cells-highlight");
				}

				// 3. Highlight active cell
				$td.addClass("excel-active-cell-highlight");
			},
			mouseleave: function () {
				$container.find(".branch-hover-highlight").removeClass("branch-hover-highlight");
				$container.find(".excel-col-header-highlight").removeClass("excel-col-header-highlight");
				$container.find(".excel-col-cells-highlight").removeClass("excel-col-cells-highlight");
				$container.find(".excel-active-cell-highlight").removeClass("excel-active-cell-highlight");
			},
		}, "td");

		// Click target badge (missing or stored) to open quick entry popup modal
		$container.off("click", ".target-cell-badge").on("click", ".target-cell-badge", function (e) {
			if (e.ctrlKey || e.metaKey) return; // Allow opening in new tab if ctrl/cmd clicked
			e.preventDefault();

			const $badge = $(this);
			const sol_id = $badge.data("sol");
			const type = $badge.data("type");
			const month = $badge.data("month") || "";
			const current_target = $badge.data("target") || "";

			const branch_obj = missing_matrix_data.matrix.find((b) => b.sol_id === sol_id);
			const branch_title = branch_obj ? `${sol_id} - ${branch_obj.branch_name}` : sol_id;

			const quick_dialog = new frappe.ui.Dialog({
				title: `<span style="font-weight: 800; color: #417d81; font-size: 16px;">Quick Set Target</span>`,
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "info_html",
						options: `
							<div style="background: #f8fafc; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 12px; border: 1px solid #e2e8f0;">
								<div style="margin-bottom: 4px;"><strong>Branch:</strong> <span style="color: #0f172a; font-weight: 700;">${branch_title}</span></div>
								<div style="margin-bottom: 4px;"><strong>Financial Year:</strong> <span style="color: #417d81; font-weight: 700;">${selected_fy}</span></div>
								<div><strong>Target Type:</strong> <span style="color: #3b82f6; font-weight: 700;">${type} ${month ? `(${month})` : ""}</span></div>
							</div>
						`,
					},
					{
						label: __("Target Amount (₹)"),
						fieldname: "target_amount",
						fieldtype: "Currency",
						default: current_target,
						reqd: 1,
					},
				],
				primary_action_label: __("Save Target"),
				primary_action: function (values) {
					const val = flt(values.target_amount);
					if (!val || val <= 0) {
						frappe.msgprint(__("Please enter a valid target amount greater than 0."));
						return;
					}

					quick_dialog.get_primary_btn().prop("disabled", true).text(__("Saving..."));

					frappe.call({
						method: "custom_report.custom_report.doctype.target_vs_achivement.target_vs_achivement.save_quick_target",
						args: {
							sol_id: sol_id,
							financial_year: selected_fy,
							type: type,
							month: month,
							target: val,
						},
						callback: function (r) {
							quick_dialog.hide();
							if (r.message && r.message.status === "success") {
								frappe.show_alert({
									message: __("Target saved successfully!"),
									indicator: "green",
								});
								// Instantly reload matrix data to update cell to Green
								load_matrix_data(selected_fy);
							}
						},
						error: function () {
							quick_dialog.get_primary_btn().prop("disabled", false).text(__("Save Target"));
						},
					});
				},
			});

			quick_dialog.show();
			quick_dialog.$wrapper.find(".modal-dialog").css({
				"max-width": "420px",
				"margin-top": "120px",
			});
		});
	}

	// Initial Load
	load_matrix_data(null);
}
