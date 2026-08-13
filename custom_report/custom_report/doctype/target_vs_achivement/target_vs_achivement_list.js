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
	let active_view_block = "all"; // 'all', 'monthly', 'ytd', 'yearly'

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
		"max-width": "95vw",
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

		const html = `
			<style>
				.missing-target-modal { font-family: 'Inter', sans-serif; color: #1e293b; }
				.missing-target-controls { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 12px; background: #f8fafc; padding: 10px 14px; border-radius: 8px; border: 1px solid #e2e8f0; }
				.missing-target-summary { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
				.missing-summary-card { flex: 1; min-width: 140px; background: #ffffff; padding: 8px 14px; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: all 0.2s ease; }
				.missing-summary-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
				.missing-summary-card .label { font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; }
				.missing-summary-card .val { font-size: 18px; font-weight: 800; margin-top: 2px; }
				
				.missing-blocks-wrapper { max-height: 65vh; overflow-y: auto; padding-right: 4px; }
				.target-section-block { margin-bottom: 20px; border: 1px solid #cbd5e1; border-radius: 8px; background: #ffffff; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.03); }
				.target-section-header { padding: 10px 14px; color: #ffffff; font-weight: 800; font-size: 13px; display: flex; justify-content: space-between; align-items: center; }
				.target-section-header.monthly { background: linear-gradient(135deg, #2b5558 0%, #417d81 100%); }
				.target-section-header.ytd { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); }
				.target-section-header.yearly { background: linear-gradient(135deg, #334155 0%, #475569 100%); }
				
				.missing-matrix-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11px; }
				.missing-matrix-table th { position: sticky; top: 0; z-index: 5; background: #f1f5f9; color: #334155; padding: 7px 5px; font-weight: 700; text-align: center; white-space: nowrap; border-bottom: 2px solid #cbd5e1; border-right: 1px solid #e2e8f0; }
				.missing-matrix-table td { padding: 6px 5px; border-bottom: 1px solid #f1f5f9; border-right: 1px solid #f8fafc; text-align: center; vertical-align: middle; white-space: nowrap; transition: background-color 0.15s ease; }
				.missing-matrix-table tbody tr { transition: background-color 0.15s ease; }
				.missing-matrix-table tbody tr:hover { background-color: #e0f2fe !important; }
				.missing-matrix-table tbody tr:hover td { background-color: #e0f2fe !important; }
				.missing-matrix-table tbody td:hover { background-color: #bae6fd !important; }
				
				.target-cell-badge { display: inline-flex; align-items: center; justify-content: center; padding: 3px 8px; border-radius: 5px; font-size: 10px; font-weight: 700; cursor: pointer; text-decoration: none; transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
				.target-cell-badge.stored { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
				.target-cell-badge.stored:hover { background: #16a34a !important; color: #ffffff !important; border-color: #15803d !important; transform: translateY(-1px) scale(1.12); box-shadow: 0 3px 8px rgba(22, 163, 74, 0.35); }
				.target-cell-badge.missing { background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
				.target-cell-badge.missing:hover { background: #dc2626 !important; color: #ffffff !important; border-color: #b91c1c !important; transform: translateY(-1px) scale(1.15); box-shadow: 0 3px 8px rgba(220, 38, 38, 0.4); }
				
				.filter-pill-btn { padding: 4px 10px; font-size: 11px; font-weight: 600; border-radius: 9999px; border: 1px solid #cbd5e1; background: #fff; color: #475569; cursor: pointer; transition: all 0.2s; }
				.filter-pill-btn.active { background: #417d81; color: #fff; border-color: #417d81; }
				.block-view-btn { padding: 4px 10px; font-size: 11px; font-weight: 600; border-radius: 6px; border: 1px solid #cbd5e1; background: #fff; color: #475569; cursor: pointer; transition: all 0.2s; }
				.block-view-btn.active { background: #334155; color: #fff; border-color: #334155; }
			</style>

			<div class="missing-target-modal">
				<div class="missing-target-controls">
					<div style="display: flex; align-items: center; gap: 6px;">
						<span style="font-weight: 700; font-size: 12px; color: #334155;">FY:</span>
						<select id="missing-fy-select" style="padding: 4px 8px; border-radius: 6px; border: 1px solid #cbd5e1; font-weight: 700; color: #417d81; background: white; font-size: 12px;">
							${fy_options}
						</select>
					</div>

					<div style="display: flex; align-items: center; gap: 6px; margin-left: 6px;">
						<input type="text" id="missing-search-input" placeholder="Search SOL ID, Branch, Zone, Region..." style="padding: 4px 10px; border: 1px solid #cbd5e1; border-radius: 6px; min-width: 220px; font-size: 12px; outline: none;">
					</div>

					<div style="display: flex; align-items: center; gap: 4px; margin-left: 8px;">
						<span style="font-weight: 700; font-size: 11px; color: #64748b;">Block:</span>
						<button class="block-view-btn ${active_view_block === "all" ? "active" : ""}" data-block="all">All Stacked</button>
						<button class="block-view-btn ${active_view_block === "monthly" ? "active" : ""}" data-block="monthly">Monthly</button>
						<button class="block-view-btn ${active_view_block === "ytd" ? "active" : ""}" data-block="ytd">YTD</button>
						<button class="block-view-btn ${active_view_block === "yearly" ? "active" : ""}" data-block="yearly">Yearly</button>
					</div>

					<div style="display: flex; align-items: center; gap: 6px; margin-left: auto;">
						<button class="filter-pill-btn ${current_filter === "all" ? "active" : ""}" data-filter="all">All (${d.matrix.length})</button>
						<button class="filter-pill-btn ${current_filter === "missing_only" ? "active" : ""}" data-filter="missing_only">Has Missing (${d.matrix.filter((r) => r.missing_count > 0).length})</button>
						<button id="missing-refresh-btn" style="background: #e2e8f0; color: #334155; border: none; padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; cursor: pointer; margin-left: 4px;">⟳ Refresh</button>
						<button id="missing-bulk-upload-btn" style="background: #417d81; color: #ffffff; border: none; padding: 4px 10px; border-radius: 9999px; font-weight: 700; font-size: 11px; cursor: pointer; margin-left: 4px;">📥 Bulk Upload</button>
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

				<div class="missing-blocks-wrapper" id="missing-blocks-container">
					${render_all_blocks()}
				</div>
			</div>
		`;

		$container.html(html);
		attach_events();
	}

	function get_filtered_matrix() {
		let filtered = missing_matrix_data.matrix;
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

	function format_val(val) {
		if (!val) return "0";
		if (val >= 10000000) return (val / 10000000).toFixed(1) + "Cr";
		if (val >= 100000) return (val / 100000).toFixed(1) + "L";
		if (val >= 1000) return (val / 1000).toFixed(1) + "K";
		return val;
	}

	function render_all_blocks() {
		let html = "";
		if (active_view_block === "all" || active_view_block === "monthly") {
			html += render_monthly_block();
		}
		if (active_view_block === "all" || active_view_block === "ytd") {
			html += render_ytd_block();
		}
		if (active_view_block === "all" || active_view_block === "yearly") {
			html += render_yearly_block();
		}
		return html;
	}

	function render_monthly_block() {
		const filtered = get_filtered_matrix();
		const months = missing_matrix_data.months;

		const rows_html = filtered.length === 0
			? `<tr><td colspan="16" style="padding: 20px; color: #64748b;">No branches match search / filter.</td></tr>`
			: filtered.map((row, i) => {
				let month_tds = months.map((m) => {
					const cell = row.months[m];
					if (cell && cell.stored) {
						return `<td><a class="target-cell-badge stored" href="/app/target-vs-achivement/${cell.name}" target="_blank" title="View Monthly Target: ${cell.name}">✓ ${format_val(cell.target)}</a></td>`;
					} else {
						return `<td><span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="Monthly" data-month="${m}" title="Add Monthly Target for ${m}">✕ Missing</span></td>`;
					}
				}).join("");

				let missing_cnt = months.filter(m => !row.months[m] || !row.months[m].stored).length;
				let badge = missing_cnt > 0
					? `<span style="background: #fef2f2; color: #ef4444; font-weight: 800; padding: 2px 8px; border-radius: 9999px; font-size: 10px;">${missing_cnt} Missing</span>`
					: `<span style="background: #f0fdf4; color: #166534; font-weight: 800; padding: 2px 8px; border-radius: 9999px; font-size: 10px;">Complete</span>`;

				return `
					<tr>
						<td>${i + 1}</td>
						<td style="text-align: left; padding-left: 10px; font-weight: 700; color: #0f172a;">${row.sol_id} - ${row.branch_name}</td>
						<td style="color: #64748b; font-weight: 500;">${row.zone} / ${row.region}</td>
						${month_tds}
						<td>${badge}</td>
					</tr>
				`;
			}).join("");

		return `
			<div class="target-section-block">
				<div class="target-section-header monthly">
					<span>📅 Block 1: Monthly Targets (Apr - Mar)</span>
					<span style="font-size: 11px; opacity: 0.9;">12 Monthly Targets per Branch</span>
				</div>
				<div style="overflow-x: auto;">
					<table class="missing-matrix-table">
						<thead>
							<tr>
								<th style="width: 35px;">Sr</th>
								<th style="text-align: left; padding-left: 10px;">SOL & Branch</th>
								<th>Zone / Region</th>
								${months.map((m) => `<th>${m}</th>`).join("")}
								<th style="background: #991b1b; color: #fff;">Status</th>
							</tr>
						</thead>
						<tbody>${rows_html}</tbody>
					</table>
				</div>
			</div>
		`;
	}

	function render_ytd_block() {
		const filtered = get_filtered_matrix();
		const months = missing_matrix_data.months;

		const rows_html = filtered.length === 0
			? `<tr><td colspan="16" style="padding: 20px; color: #64748b;">No branches match search / filter.</td></tr>`
			: filtered.map((row, i) => {
				let ytd_tds = months.map((m) => {
					const cell = row.ytd_months ? row.ytd_months[m] : null;
					if (cell && cell.stored) {
						return `<td><a class="target-cell-badge stored" href="/app/target-vs-achivement/${cell.name}" target="_blank" title="View YTD Target: ${cell.name}">✓ ${format_val(cell.target)}</a></td>`;
					} else {
						return `<td><span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="YTD" data-month="${m}" title="Add YTD Target for ${m}">✕ Missing</span></td>`;
					}
				}).join("");

				let missing_cnt = months.filter(m => !row.ytd_months || !row.ytd_months[m] || !row.ytd_months[m].stored).length;
				let badge = missing_cnt > 0
					? `<span style="background: #fef2f2; color: #ef4444; font-weight: 800; padding: 2px 8px; border-radius: 9999px; font-size: 10px;">${missing_cnt} Missing</span>`
					: `<span style="background: #f0fdf4; color: #166534; font-weight: 800; padding: 2px 8px; border-radius: 9999px; font-size: 10px;">Complete</span>`;

				return `
					<tr>
						<td>${i + 1}</td>
						<td style="text-align: left; padding-left: 10px; font-weight: 700; color: #0f172a;">${row.sol_id} - ${row.branch_name}</td>
						<td style="color: #64748b; font-weight: 500;">${row.zone} / ${row.region}</td>
						${ytd_tds}
						<td>${badge}</td>
					</tr>
				`;
			}).join("");

		return `
			<div class="target-section-block">
				<div class="target-section-header ytd">
					<span>📊 Block 2: YTD Targets (Apr - Mar)</span>
					<span style="font-size: 11px; opacity: 0.9;">12 YTD Monthly Targets per Branch</span>
				</div>
				<div style="overflow-x: auto;">
					<table class="missing-matrix-table">
						<thead>
							<tr>
								<th style="width: 35px;">Sr</th>
								<th style="text-align: left; padding-left: 10px;">SOL & Branch</th>
								<th>Zone / Region</th>
								${months.map((m) => `<th style="background: #1e3a8a; color: #fff;">${m}</th>`).join("")}
								<th style="background: #991b1b; color: #fff;">Status</th>
							</tr>
						</thead>
						<tbody>${rows_html}</tbody>
					</table>
				</div>
			</div>
		`;
	}

	function render_yearly_block() {
		const filtered = get_filtered_matrix();

		const rows_html = filtered.length === 0
			? `<tr><td colspan="5" style="padding: 20px; color: #64748b;">No branches match search / filter.</td></tr>`
			: filtered.map((row, i) => {
				let yearly_td = row.yearly && row.yearly.stored
					? `<td><a class="target-cell-badge stored" href="/app/target-vs-achivement/${row.yearly.name}" target="_blank" title="View Yearly Target">✓ ${format_val(row.yearly.target)}</a></td>`
					: `<td><span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="Yearly" data-month="" title="Add Yearly Target">✕ Missing</span></td>`;

				let badge = row.yearly && row.yearly.stored
					? `<span style="background: #f0fdf4; color: #166534; font-weight: 800; padding: 2px 8px; border-radius: 9999px; font-size: 10px;">Stored</span>`
					: `<span style="background: #fef2f2; color: #ef4444; font-weight: 800; padding: 2px 8px; border-radius: 9999px; font-size: 10px;">1 Missing</span>`;

				return `
					<tr>
						<td>${i + 1}</td>
						<td style="text-align: left; padding-left: 10px; font-weight: 700; color: #0f172a;">${row.sol_id} - ${row.branch_name}</td>
						<td style="color: #64748b; font-weight: 500;">${row.zone} / ${row.region}</td>
						${yearly_td}
						<td>${badge}</td>
					</tr>
				`;
			}).join("");

		return `
			<div class="target-section-block">
				<div class="target-section-header yearly">
					<span>🎯 Block 3: Yearly Targets</span>
					<span style="font-size: 11px; opacity: 0.9;">1 Yearly Target per Branch</span>
				</div>
				<div style="overflow-x: auto;">
					<table class="missing-matrix-table">
						<thead>
							<tr>
								<th style="width: 35px;">Sr</th>
								<th style="text-align: left; padding-left: 10px;">SOL & Branch</th>
								<th>Zone / Region</th>
								<th style="background: #334155; color: #fff;">Yearly Target</th>
								<th style="background: #991b1b; color: #fff;">Status</th>
							</tr>
						</thead>
						<tbody>${rows_html}</tbody>
					</table>
				</div>
			</div>
		`;
	}

	function attach_events() {
		$container.find("#missing-fy-select").on("change", function () {
			load_matrix_data($(this).val());
		});

		$container.find("#missing-search-input").on("input", function () {
			$container.find("#missing-blocks-container").html(render_all_blocks());
		});

		$container.find(".filter-pill-btn").on("click", function () {
			current_filter = $(this).data("filter");
			$container.find(".filter-pill-btn").removeClass("active");
			$(this).addClass("active");
			$container.find("#missing-blocks-container").html(render_all_blocks());
		});

		$container.find(".block-view-btn").on("click", function () {
			active_view_block = $(this).data("block");
			$container.find(".block-view-btn").removeClass("active");
			$(this).addClass("active");
			$container.find("#missing-blocks-container").html(render_all_blocks());
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
