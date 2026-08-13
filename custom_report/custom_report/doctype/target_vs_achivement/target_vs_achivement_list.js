// Copyright (c) 2025, Your Organization and contributors
// For license information, please see license.txt

frappe.listview_settings["Target Vs Achivement"] = {
	onload: function (listview) {
		listview.page.add_inner_button(__("Missing Target"), function () {
			show_missing_target_dialog(listview);
		});
	},
};

function show_missing_target_dialog(listview) {
	let selected_fy = null;
	let missing_matrix_data = null;
	let current_filter = "all"; // 'all' or 'missing_only'

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
		"margin-top": "20px",
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
				.missing-target-controls { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0; }
				.missing-target-summary { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
				.missing-summary-card { flex: 1; min-width: 140px; background: #ffffff; padding: 10px 14px; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
				.missing-summary-card .label { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; }
				.missing-summary-card .val { font-size: 20px; font-weight: 800; margin-top: 2px; }
				.missing-table-scroll { max-height: 60vh; overflow: auto; border: 1px solid #cbd5e1; border-radius: 8px; background: #fff; }
				.missing-matrix-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 11px; }
				.missing-matrix-table th { position: sticky; top: 0; z-index: 10; background: #346569; color: #ffffff; padding: 6px 4px; font-weight: 700; text-align: center; white-space: nowrap; border-bottom: 1px solid #264a4d; border-right: 1px solid rgba(255,255,255,0.1); }
				.missing-matrix-table td { padding: 5px 4px; border-bottom: 1px solid #e2e8f0; border-right: 1px solid #f1f5f9; text-align: center; vertical-align: middle; white-space: nowrap; }
				.missing-matrix-table tbody tr:hover { background-color: #f0fdf4 !important; }
				.target-cell-badge { display: inline-block; padding: 2px 5px; border-radius: 4px; font-size: 10px; font-weight: 700; cursor: pointer; text-decoration: none; transition: transform 0.15s; }
				.target-cell-badge:hover { transform: scale(1.05); }
				.target-cell-badge.stored { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
				.target-cell-badge.missing { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
				.filter-pill-btn { padding: 5px 12px; font-size: 12px; font-weight: 600; border-radius: 9999px; border: 1px solid #cbd5e1; background: #fff; color: #475569; cursor: pointer; transition: all 0.2s; }
				.filter-pill-btn.active { background: #417d81; color: #fff; border-color: #417d81; }
			</style>

			<div class="missing-target-modal">
				<div class="missing-target-controls">
					<div style="display: flex; align-items: center; gap: 6px;">
						<span style="font-weight: 700; font-size: 13px; color: #334155;">Financial Year:</span>
						<select id="missing-fy-select" style="padding: 5px 10px; border-radius: 6px; border: 1px solid #cbd5e1; font-weight: 700; color: #417d81; background: white;">
							${fy_options}
						</select>
					</div>

					<div style="display: flex; align-items: center; gap: 6px; margin-left: 8px;">
						<input type="text" id="missing-search-input" placeholder="Search SOL ID, Branch, Zone, Region..." style="padding: 5px 12px; border: 1px solid #cbd5e1; border-radius: 6px; min-width: 240px; font-size: 12px; outline: none;">
					</div>

					<div style="display: flex; align-items: center; gap: 6px; margin-left: auto;">
						<button class="filter-pill-btn ${current_filter === "all" ? "active" : ""}" data-filter="all">All Branches (${d.matrix.length})</button>
						<button class="filter-pill-btn ${current_filter === "missing_only" ? "active" : ""}" data-filter="missing_only">Has Missing Targets (${d.matrix.filter((r) => r.missing_count > 0).length})</button>
						<button id="missing-refresh-btn" style="background: #e2e8f0; color: #334155; border: none; padding: 5px 10px; border-radius: 6px; font-weight: 700; font-size: 12px; cursor: pointer; margin-left: 6px;">⟳ Refresh</button>
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
								<th rowspan="2" style="width: 35px;">Sr</th>
								<th rowspan="2" style="text-align: left; padding-left: 10px;">SOL & Branch</th>
								<th rowspan="2">Zone / Region</th>
								<th colspan="12" style="background: #2b5558;">Monthly Targets (Apr - Mar)</th>
								<th colspan="12" style="background: #3e6b6e;">YTD Targets (Apr - Mar)</th>
								<th rowspan="2" style="background: #264a4d;">Yearly</th>
								<th rowspan="2" style="background: #991b1b; color: #fff;">Missing</th>
							</tr>
							<tr>
								${months.map((m) => `<th style="background: #346569;">${m}</th>`).join("")}
								${months.map((m) => `<th style="background: #417d81;">${m}</th>`).join("")}
							</tr>
						</thead>
						<tbody id="missing-matrix-tbody">
							${render_matrix_rows(d.matrix)}
						</tbody>
					</table>
				</div>
			</div>
		`;

		$container.html(html);
		attach_events();
	}

	function render_matrix_rows(matrix_list) {
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

		if (filtered.length === 0) {
			return `<tr><td colspan="30" style="padding: 30px; color: #64748b; font-weight: 600;">No branches match the current search / filter.</td></tr>`;
		}

		const format_val = (val) => {
			if (!val) return "0";
			if (val >= 10000000) return (val / 10000000).toFixed(1) + "Cr";
			if (val >= 100000) return (val / 100000).toFixed(1) + "L";
			if (val >= 1000) return (val / 1000).toFixed(1) + "K";
			return val;
		};

		return filtered
			.map((row, i) => {
				let month_tds = missing_matrix_data.months
					.map((m) => {
						const cell = row.months[m];
						if (cell && cell.stored) {
							return `<td><a class="target-cell-badge stored" href="/app/target-vs-achivement/${cell.name}" target="_blank" title="View Monthly Target Record: ${cell.name}">✓ ${format_val(cell.target)}</a></td>`;
						} else {
							return `<td><span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="Monthly" data-month="${m}" title="Click to Add Monthly Target for ${m}">✕</span></td>`;
						}
					})
					.join("");

				let ytd_month_tds = missing_matrix_data.months
					.map((m) => {
						const cell = row.ytd_months ? row.ytd_months[m] : null;
						if (cell && cell.stored) {
							return `<td><a class="target-cell-badge stored" href="/app/target-vs-achivement/${cell.name}" target="_blank" title="View YTD Target Record: ${cell.name}">✓ ${format_val(cell.target)}</a></td>`;
						} else {
							return `<td><span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="YTD" data-month="${m}" title="Click to Add YTD Target for ${m}">✕</span></td>`;
						}
					})
					.join("");

				let yearly_td = row.yearly && row.yearly.stored
					? `<td><a class="target-cell-badge stored" href="/app/target-vs-achivement/${row.yearly.name}" target="_blank" title="View Yearly Target">✓ ${format_val(row.yearly.target)}</a></td>`
					: `<td><span class="target-cell-badge missing" data-sol="${row.sol_id}" data-type="Yearly" data-month="" title="Click to Add Yearly Target">✕</span></td>`;

				let missing_badge =
					row.missing_count > 0
						? `<span style="background: #fef2f2; color: #ef4444; font-weight: 800; padding: 2px 8px; border-radius: 9999px; font-size: 11px;">${row.missing_count}</span>`
						: `<span style="background: #f0fdf4; color: #166534; font-weight: 800; padding: 2px 8px; border-radius: 9999px; font-size: 11px;">0</span>`;

				return `
				<tr>
					<td>${i + 1}</td>
					<td style="text-align: left; padding-left: 10px; font-weight: 700; color: #0f172a;">${row.sol_id} - ${row.branch_name}</td>
					<td style="color: #64748b; font-weight: 500;">${row.zone} / ${row.region}</td>
					${month_tds}
					${ytd_month_tds}
					${yearly_td}
					<td>${missing_badge}</td>
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
			$container.find("#missing-matrix-tbody").html(render_matrix_rows(missing_matrix_data.matrix));
		});

		$container.find(".filter-pill-btn").on("click", function () {
			current_filter = $(this).data("filter");
			$container.find(".filter-pill-btn").removeClass("active");
			$(this).addClass("active");
			$container.find("#missing-matrix-tbody").html(render_matrix_rows(missing_matrix_data.matrix));
		});

		$container.find("#missing-refresh-btn").on("click", function () {
			load_matrix_data(selected_fy);
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
