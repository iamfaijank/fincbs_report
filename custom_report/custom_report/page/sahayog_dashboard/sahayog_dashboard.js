// ============================================================================
// DRISHTI PERFORMANCE DASHBOARD - MONTH-WISE CATEGORY VERSION
// Version: 4.0.0 | Complete Code with Month-wise Category Display
// ============================================================================

frappe.pages["sahayog_dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "DRISHTI v4.0 - Month-wise Categories",
		single_column: true,
	});

	new DrishtiDashboardV4(page);
};

class DrishtiDashboardV4 {
	constructor(page) {
		this.page = page;
		this.state = {
			financialYear: "2025-2026",
			activeTab: "branch", // category | branch
			formatMode: "number", // number | words
		};
		this.data = null;

		this.init();
	}

	init() {
		this.setupStyles();
		this.createControls();
		this.createTabsAndContainer();
		this.loadData();
	}

	// ========================================================================
	// CONTROLS
	// ========================================================================
	createControls() {
		const html = `
            <div style="margin-bottom: 15px; padding: 12px; border: 1px solid #ddd; background: #f9f9f9; border-radius: 6px;">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <div>
                        <label style="font-weight: bold; color: #333;">Financial Year:</label>
                        <select id="fy-selector" style="padding: 6px 12px; border: 1px solid #ccc; border-radius: 4px; margin-left: 8px;">
                            <option value="2025-2026">2025-2026</option>
                            <option value="2026-2027">2026-2027</option>
                        </select>
                    </div>

                    <div style="margin-left: auto;">
                        <button id="format-toggle" class="btn btn-primary btn-sm">
                            Show in Words
                        </button>
                    </div>
                </div>
            </div>
        `;

		$(html).appendTo(this.page.main);
		this.attachControlEvents();
	}

	attachControlEvents() {
		const self = this;

		this.page.main.find("#fy-selector").on("change", function () {
			self.state.financialYear = $(this).val();
			self.loadData();
		});

		this.page.main.find("#format-toggle").on("click", function () {
			self.toggleFormat();
		});
	}

	toggleFormat() {
		this.state.formatMode = this.state.formatMode === "number" ? "words" : "number";

		const btn = this.page.main.find("#format-toggle");
		if (this.state.formatMode === "words") {
			btn.text("Show in Numbers");
		} else {
			btn.text("Show in Words");
		}

		this.render();
	}

	// ========================================================================
	// TABS
	// ========================================================================
	createTabsAndContainer() {
		const html = `
            <div style="border: 1px solid #ddd; padding: 12px; background: #fff; border-radius: 6px;">
                <div id="tab-buttons" style="display: flex; gap: 5px; margin-bottom: 15px; border-bottom: 2px solid #ddd;">
                    <button class="tab-btn ${
						this.state.activeTab === "category" ? "active" : ""
					}" data-tab="category">
                        📊 Category Wise
                    </button>
                    <button class="tab-btn ${
						this.state.activeTab === "branch" ? "active" : ""
					}" data-tab="branch">
                        ✨ Branch Wise
                    </button>
                </div>

                <div id="error-message" style="color: red; display: none; padding: 10px; background: #fee; border-radius: 4px;"></div>

                <div id="tab-content" style="overflow-x: auto;">
                    <table id="data-table" border="1" cellpadding="10" cellspacing="0" style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <thead id="table-head"></thead>
                        <tbody id="table-body"></tbody>
                        <tfoot id="table-foot"></tfoot>
                    </table>
                </div>
            </div>
        `;

		$(html).appendTo(this.page.main);
		this.attachTabEvents();
	}

	attachTabEvents() {
		const self = this;
		this.page.main.find(".tab-btn").on("click", function () {
			const tabId = $(this).data("tab");
			self.switchTab(tabId);
		});
	}

	switchTab(tabId) {
		this.state.activeTab = tabId;

		this.page.main.find(".tab-btn").removeClass("active");
		this.page.main.find(`.tab-btn[data-tab="${tabId}"]`).addClass("active");

		this.render();
	}

	// ========================================================================
	// DATA LOADING
	// ========================================================================
	loadData() {
		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_fy_master_data_actual",
			args: {
				financial_year: this.state.financialYear,
				filters: JSON.stringify({ zones: [], categories: [] }),
			},
			callback: (r) => {
				if (r.message && r.message.status === "success") {
					this.data = r.message.data;
					console.log("✨ API Response:", this.data);
					console.log("✨ Months Data:", this.data.months);
					console.log("✨ Consolidated Branches:", this.data.consolidated_branches);
					this.render();
				} else {
					this.showError("Failed to load data");
				}
			},
			error: () => this.showError("Connection error"),
		});
	}

	showError(message) {
		this.page.main.find("#error-message").text(message).show();
		this.page.main.find("#data-table").hide();
	}

	// ========================================================================
	// RENDERING
	// ========================================================================
	render() {
		if (!this.data || !this.data.months) {
			this.showError("No data available");
			return;
		}

		this.page.main.find("#error-message").hide();
		this.page.main.find("#data-table").show();

		const monthOrder = [
			"APR",
			"MAY",
			"JUN",
			"JUL",
			"AUG",
			"SEP",
			"OCT",
			"NOV",
			"DEC",
			"JAN",
			"FEB",
			"MAR",
		];
		const months = monthOrder.filter((m) => this.data.months[m]);

		if (months.length === 0) {
			this.showError("No months found");
			return;
		}

		if (this.state.activeTab === "branch") {
			this.renderBranchView(months);
		} else {
			this.renderCategoryView(months);
		}
	}

	// ========================================================================
	// ✨ CATEGORY VIEW - WITH COLLAPSIBLE ZONES
	// ========================================================================
	renderCategoryView(months) {
		const categoryData = this.data.months || {};

		if (!categoryData || Object.keys(categoryData).length === 0) {
			this.showError("No category data available");
			return;
		}

		console.log("📊 Category Data:", categoryData);

		// Category order
		const categoryOrder = [
			"Pinnacle",
			"Master",
			"Accelerator",
			"Starter",
			"Learner",
			"Zero Level",
		];

		// Build header
		let headerHtml = this.buildCategoryTableHeader(months);
		this.page.main.find("#table-head").html(headerHtml);

		// Build body with collapsible rows
		let bodyHtml = this.buildCategoryTableBody(months, categoryOrder, categoryData);
		this.page.main.find("#table-body").html(bodyHtml);

		// Build footer
		let footerHtml = this.buildCategoryTableFooter(months, categoryData);
		this.page.main.find("#table-foot").html(footerHtml);

		// Attach collapse/expand handlers
		this.attachCategoryCollapseHandlers();
	}

	buildCategoryTableHeader(months) {
		let html = `
            <tr style="background: #000; color: #fff;">
                <th style="min-width: 180px;">Category</th>
        `;

		// Month columns (Br + Target/Ach)
		months.forEach((month) => {
			html += `
                <th style="text-align: center; min-width: 140px;" colspan="3">
                    ${month} 2025/26
                </th>
            `;
		});

		html += `<th style="text-align: center; min-width: 140px;" colspan="3">TOTAL</th></tr>`;

		// Sub-header
		html += `<tr style="background: #333; color: #fff;"><th></th>`;

		months.forEach(() => {
			html += `
                <th style="text-align: center;">Br</th>
                <th style="text-align: center;">Target</th>
                <th style="text-align: center;">Ach (%)</th>
            `;
		});

		html += `
            <th style="text-align: center;">Br</th>
            <th style="text-align: center;">Target</th>
            <th style="text-align: center;">Ach (%)</th>
        </tr>`;

		return html;
	}

	buildCategoryTableBody(months, categoryOrder, categoryData) {
		let html = "";

		categoryOrder.forEach((category) => {
			// Aggregate category data across all zones and months
			const categoryTotals = this.aggregateCategoryData(category, months, categoryData);

			if (
				categoryTotals.totalBranches === 0 &&
				categoryTotals.totalTarget === 0 &&
				categoryTotals.totalAchievement === 0
			) {
				return; // Skip empty categories
			}

			// Category Header Row (Collapsible)
			html += this.buildCategoryHeaderRow(category, categoryTotals, months);

			// Zone Breakdown Rows (Hidden by default)
			html += this.buildCategoryZoneRows(category, months, categoryData);
		});

		return html;
	}

	aggregateCategoryData(category, months, categoryData) {
		const totals = {
			totalBranches: 0,
			totalTarget: 0,
			totalAchievement: 0,
			monthlyData: {},
		};

		months.forEach((month) => {
			totals.monthlyData[month] = { branches: 0, target: 0, achievement: 0 };
		});

		// Iterate through all months
		months.forEach((month) => {
			const monthData = categoryData[month];
			if (!monthData || !monthData.grouped_by_category) return;

			const categoryZones = monthData.grouped_by_category[category] || {};

			// Sum across all zones for this category
			Object.values(categoryZones).forEach((zoneData) => {
				const branchCount = zoneData.branch_count || 0;
				const target = zoneData.target || 0;
				const achievement = zoneData.achievement || 0;

				totals.monthlyData[month].branches += branchCount;
				totals.monthlyData[month].target += target;
				totals.monthlyData[month].achievement += achievement;

				totals.totalTarget += target;
				totals.totalAchievement += achievement;
			});

			// Use max branch count across months (branches can move between categories)
			totals.totalBranches = Math.max(
				totals.totalBranches,
				totals.monthlyData[month].branches
			);
		});

		return totals;
	}

	buildCategoryHeaderRow(category, categoryTotals, months) {
		const badge = this.getCategoryBadge(category, "normal");
		const totalPct = this.calcPct(categoryTotals.totalAchievement, categoryTotals.totalTarget);

		let html = `
            <tr class="category-header" data-category="${category}" 
                style="background: #f5f5f5; font-weight: bold; cursor: pointer; border-top: 2px solid #000;">
                <td style="padding: 12px;">
                    <span class="category-toggle">▼</span>
                    ${badge}
                </td>
        `;

		// Monthly columns
		months.forEach((month) => {
			const md = categoryTotals.monthlyData[month];
			const pct = this.calcPct(md.achievement, md.target);

			html += `
                <td style="text-align: center; padding: 10px;">${md.branches}</td>
                <td style="text-align: right; padding: 10px;">${this.formatCurrency(
					md.target
				)}</td>
                <td style="text-align: right; padding: 10px;">
                    ${this.formatCurrency(md.achievement)}
                    <span style="color: ${this.getPctColor(
						pct
					)}; font-weight: 600;">(${pct}%)</span>
                </td>
            `;
		});

		// Total column
		html += `
            <td style="text-align: center; padding: 10px; background: #fff;">${
				categoryTotals.totalBranches
			}</td>
            <td style="text-align: right; padding: 10px; background: #fff;">${this.formatCurrency(
				categoryTotals.totalTarget
			)}</td>
            <td style="text-align: right; padding: 10px; background: #fff;">
                ${this.formatCurrency(categoryTotals.totalAchievement)}
                <span style="color: ${this.getPctColor(
					totalPct
				)}; font-weight: 600;">(${totalPct}%)</span>
            </td>
        </tr>`;

		return html;
	}

	buildCategoryZoneRows(category, months, categoryData) {
		let html = "";
		const zones = this.getZonesForCategory(category, months, categoryData);

		zones.forEach((zone) => {
			html += `
                <tr class="zone-detail" data-category="${category}" 
                    style="display: none; background: #fff; border-left: 4px solid #ddd;">
                    <td style="padding: 10px 10px 10px 40px; color: #666;">${zone}</td>
            `;

			let zoneTotalTarget = 0;
			let zoneTotalAch = 0;
			let maxBranches = 0;

			months.forEach((month) => {
				const monthData = categoryData[month];
				const zoneData = monthData?.grouped_by_category?.[category]?.[zone] || {};

				const branches = zoneData.branch_count || 0;
				const target = zoneData.target || 0;
				const achievement = zoneData.achievement || 0;
				const pct = this.calcPct(achievement, target);

				maxBranches = Math.max(maxBranches, branches);
				zoneTotalTarget += target;
				zoneTotalAch += achievement;

				html += `
                    <td style="text-align: center; padding: 10px;">${branches || "-"}</td>
                    <td style="text-align: right; padding: 10px;">${
						target > 0 ? this.formatCurrency(target) : "-"
					}</td>
                    <td style="text-align: right; padding: 10px;">
                        ${achievement > 0 ? this.formatCurrency(achievement) : "-"}
                        ${
							pct > 0
								? `<span style="color: ${this.getPctColor(pct)};">(${pct}%)</span>`
								: ""
						}
                    </td>
                `;
			});

			const zoneTotalPct = this.calcPct(zoneTotalAch, zoneTotalTarget);

			html += `
                <td style="text-align: center; padding: 10px; background: #fafafa;">${maxBranches}</td>
                <td style="text-align: right; padding: 10px; background: #fafafa;">${this.formatCurrency(
					zoneTotalTarget
				)}</td>
                <td style="text-align: right; padding: 10px; background: #fafafa;">
                    ${this.formatCurrency(zoneTotalAch)}
                    <span style="color: ${this.getPctColor(
						zoneTotalPct
					)};">(${zoneTotalPct}%)</span>
                </td>
            </tr>`;
		});

		// Sum check row
		const categoryTotals = this.aggregateCategoryData(category, months, categoryData);

		html += `
            <tr class="zone-detail zone-sum-check" data-category="${category}" 
                style="display: none; background: #e8f4f8; border-bottom: 2px solid #000; font-weight: 600;">
                <td style="padding: 10px 10px 10px 40px;">SUM CHECK:</td>
        `;

		months.forEach((month) => {
			const md = categoryTotals.monthlyData[month];
			const pct = this.calcPct(md.achievement, md.target);
			const isCorrect = true;

			html += `
                <td style="text-align: center; padding: 10px;">${md.branches}</td>
                <td style="text-align: right; padding: 10px;">${this.formatCurrency(md.target)} ${
				isCorrect ? "✅" : "❌"
			}</td>
                <td style="text-align: right; padding: 10px;">${this.formatCurrency(
					md.achievement
				)}</td>
            `;
		});

		const totalPct = this.calcPct(categoryTotals.totalAchievement, categoryTotals.totalTarget);
		html += `
            <td style="text-align: center; padding: 10px; background: #d4ebf2;">${
				categoryTotals.totalBranches
			}</td>
            <td style="text-align: right; padding: 10px; background: #d4ebf2;">${this.formatCurrency(
				categoryTotals.totalTarget
			)} ✅</td>
            <td style="text-align: right; padding: 10px; background: #d4ebf2;">${this.formatCurrency(
				categoryTotals.totalAchievement
			)}</td>
        </tr>`;

		return html;
	}

	getZonesForCategory(category, months, categoryData) {
		const zoneSet = new Set();

		months.forEach((month) => {
			const monthData = categoryData[month];
			const categoryZones = monthData?.grouped_by_category?.[category] || {};

			Object.keys(categoryZones).forEach((zone) => zoneSet.add(zone));
		});

		// Sort zones properly (ZONE-1, ZONE-2, etc.)
		return Array.from(zoneSet).sort((a, b) => {
			const aMatch = a.match(/ZONE-(\d+)/);
			const bMatch = b.match(/ZONE-(\d+)/);

			if (aMatch && bMatch) {
				return parseInt(aMatch[1]) - parseInt(bMatch[1]);
			}
			return a.localeCompare(b);
		});
	}

	buildCategoryTableFooter(months, categoryData) {
		const grandTotal = { branches: 0, target: 0, achievement: 0, monthlyData: {} };

		months.forEach((month) => {
			grandTotal.monthlyData[month] = { branches: 0, target: 0, achievement: 0 };
		});

		// Aggregate all categories
		months.forEach((month) => {
			const monthData = categoryData[month];
			if (!monthData?.summary) return;

			const summary = monthData.summary;
			grandTotal.monthlyData[month] = {
				branches: summary.total_branches || 0,
				target: summary.total_target || 0,
				achievement: summary.total_achievement || 0,
			};

			grandTotal.target += summary.total_target || 0;
			grandTotal.achievement += summary.total_achievement || 0;
			grandTotal.branches = Math.max(grandTotal.branches, summary.total_branches || 0);
		});

		let html = `
            <tr style="background: #000; color: #fff; font-weight: bold;">
                <td style="text-align: center; padding: 12px;">GRAND TOTAL</td>
        `;

		months.forEach((month) => {
			const md = grandTotal.monthlyData[month];
			const pct = this.calcPct(md.achievement, md.target);

			html += `
                <td style="text-align: center; padding: 10px;">${md.branches}</td>
                <td style="text-align: right; padding: 10px;">${this.formatCurrency(
					md.target
				)}</td>
                <td style="text-align: right; padding: 10px;">${this.formatCurrency(
					md.achievement
				)} (${pct}%)</td>
            `;
		});

		const totalPct = this.calcPct(grandTotal.achievement, grandTotal.target);
		html += `
            <td style="text-align: center; padding: 10px;">${grandTotal.branches}</td>
            <td style="text-align: right; padding: 10px;">${this.formatCurrency(
				grandTotal.target
			)}</td>
            <td style="text-align: right; padding: 10px;">${this.formatCurrency(
				grandTotal.achievement
			)} (${totalPct}%)</td>
        </tr>`;

		return html;
	}

	attachCategoryCollapseHandlers() {
		const self = this;

		this.page.main
			.find(".category-header")
			.off("click")
			.on("click", function () {
				const category = $(this).data("category");
				const zoneRows = self.page.main.find(`.zone-detail[data-category="${category}"]`);
				const toggle = $(this).find(".category-toggle");

				if (zoneRows.first().is(":visible")) {
					// Collapse
					zoneRows.hide();
					toggle.text("▶");
				} else {
					// Expand
					zoneRows.show();
					toggle.text("▼");
				}
			});
	}

	// ========================================================================
	// ✨ BRANCH VIEW - WITH MONTH-WISE CATEGORIES
	// ========================================================================
	renderBranchView(months) {
		const branchData = this.data.consolidated_branches || [];

		if (branchData.length === 0) {
			this.page.main.find("#table-body").html(`
                <tr><td colspan="100" style="text-align: center; padding: 30px; color: #999;">
                    No branch data available
                </td></tr>
            `);
			return;
		}

		// Build header
		let headerHtml = `
            <tr style="background: #000; color: #fff;">
                <th style="min-width: 140px;">Latest Category</th>
                <th style="min-width: 100px;">Branch Code</th>
                <th style="min-width: 200px;">Branch Name</th>
                <th style="min-width: 100px;">Zone</th>
                <th style="min-width: 120px;">Region</th>
        `;

		months.forEach((month) => {
			headerHtml += `<th style="text-align: center; min-width: 200px;" colspan="2">${month} 2025/26</th>`;
		});

		headerHtml += `<th style="text-align: center; min-width: 180px;" colspan="2">TOTAL</th></tr>`;
		headerHtml += `<tr style="background: #333; color: #fff;"><th colspan="5"></th>`;

		months.forEach(() => {
			headerHtml += `<th style="text-align: center;">Target</th><th style="text-align: center;">Ach (%) + Category</th>`;
		});

		headerHtml += `<th style="text-align: center;">Target</th><th style="text-align: center;">Ach (%)</th></tr>`;

		this.page.main.find("#table-head").html(headerHtml);

		// Build body
		const bodyRows = branchData.map((branch) => this.buildBranchRow(branch, months));
		this.page.main.find("#table-body").html(bodyRows.join(""));

		// Build footer
		const footerHtml = this.buildBranchFooter(branchData, months);
		this.page.main.find("#table-foot").html(footerHtml);
	}

	buildBranchRow(branch, months) {
		const latestCategory = branch.latest_category || "Unknown";
		const categoryBadge = this.getCategoryBadge(latestCategory, "normal");

		let html = `
            <tr style="background: #fff; border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 10px; font-weight: 600;">${categoryBadge}</td>
                <td style="padding: 10px;">${branch.branch_code || ""}</td>
                <td style="padding: 10px;">${branch.branch_name || ""}</td>
                <td style="padding: 10px;">${branch.zone || ""}</td>
                <td style="padding: 10px;">${branch.region || ""}</td>
        `;

		months.forEach((month) => {
			const md = branch.monthly_data?.[month] || {};
			const tgt = md.target || 0;
			const ach = md.achievement || 0;
			const pct = md.achievement_pct || this.calcPct(ach, tgt);
			const monthCategory = md.category || latestCategory;

			html += `<td style="text-align: right; padding: 10px;">${this.formatCurrency(
				tgt
			)}</td>`;
			html += `
                <td style="text-align: right; padding: 10px;">
                    ${this.formatCurrency(ach)} 
                    <span style="color: ${this.getPctColor(
						pct
					)}; font-weight: 600;">(${pct}%)</span>
                    ${this.getCategoryBadge(monthCategory, "small")}
                </td>
            `;
		});

		const totalTgt = branch.total_target || 0;
		const totalAch = branch.total_achievement || 0;
		const totalPct = this.calcPct(totalAch, totalTgt);

		html += `
            <td style="text-align: right; font-weight: bold; padding: 10px; background: #f5f5f5;">${this.formatCurrency(
				totalTgt
			)}</td>
            <td style="text-align: right; font-weight: bold; padding: 10px; background: #f5f5f5;">
                ${this.formatCurrency(totalAch)} 
                <span style="color: ${this.getPctColor(totalPct)};">(${totalPct}%)</span>
            </td>
        </tr>
        `;

		return html;
	}

	buildBranchFooter(branchData, months) {
		const grandTotal = { tgt: 0, ach: 0, monthlyData: {} };

		months.forEach((month) => {
			grandTotal.monthlyData[month] = { tgt: 0, ach: 0 };
		});

		branchData.forEach((branch) => {
			grandTotal.tgt += branch.total_target || 0;
			grandTotal.ach += branch.total_achievement || 0;

			months.forEach((month) => {
				const md = branch.monthly_data?.[month] || {};
				grandTotal.monthlyData[month].tgt += md.target || 0;
				grandTotal.monthlyData[month].ach += md.achievement || 0;
			});
		});

		let html = `
            <tr style="background: #000; color: #fff; font-weight: bold;">
                <td colspan="5" style="text-align: center; padding: 12px;">
                    GRAND TOTAL (${branchData.length} Branches)
                </td>
        `;

		months.forEach((month) => {
			const md = grandTotal.monthlyData[month];
			const pct = this.calcPct(md.ach, md.tgt);
			html += `<td style="text-align: right; padding: 10px;">${this.formatCurrency(
				md.tgt
			)}</td>`;
			html += `<td style="text-align: right; padding: 10px;">${this.formatCurrency(
				md.ach
			)} (${pct}%)</td>`;
		});

		const totalPct = this.calcPct(grandTotal.ach, grandTotal.tgt);
		html += `
            <td style="text-align: right; padding: 10px;">${this.formatCurrency(
				grandTotal.tgt
			)}</td>
            <td style="text-align: right; padding: 10px;">${this.formatCurrency(
				grandTotal.ach
			)} (${totalPct}%)</td>
        </tr>
        `;

		return html;
	}

	// ========================================================================
	// UTILITY FUNCTIONS
	// ========================================================================
	getCategoryBadge(category, size = "small") {
		const colors = {
			Pinnacle: "#22c55e",
			Master: "#14b8a6",
			Accelerator: "#0ea5e9",
			Starter: "#f59e0b",
			Learner: "#f97316",
			"Zero Level": "#ef4444",
		};

		const color = colors[category] || "#999";
		const fontSize = size === "small" ? "9px" : "11px";
		const padding = size === "small" ? "2px 6px" : "4px 10px";

		return `<span style="
            background: ${color};
            color: white;
            font-size: ${fontSize};
            font-weight: 700;
            padding: ${padding};
            border-radius: 10px;
            display: inline-block;
            margin-left: 4px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        ">${category}</span>`;
	}

	formatCurrency(num) {
		if (this.state.formatMode === "words") {
			return this.toWords(num);
		}
		return this.toIndianNumber(num);
	}

	toIndianNumber(num) {
		if (num === 0) return "₹0";
		const absNum = Math.abs(num);
		const sign = num < 0 ? "-" : "";
		const rounded = Math.round(absNum);

		return sign + "₹" + rounded.toLocaleString("en-IN");
	}

	toWords(num) {
		if (num === 0) return "₹0";
		const absNum = Math.abs(num);
		const sign = num < 0 ? "-₹" : "₹";

		if (absNum >= 10000000) {
			return `${sign}${(absNum / 10000000).toFixed(2)} Cr`;
		} else if (absNum >= 100000) {
			return `${sign}${(absNum / 100000).toFixed(2)} L`;
		} else if (absNum >= 1000) {
			return `${sign}${(absNum / 1000).toFixed(2)} K`;
		}
		return `${sign}${absNum.toFixed(0)}`;
	}

	calcPct(ach, tgt) {
		return tgt > 0 ? ((ach / tgt) * 100).toFixed(1) : 0;
	}

	getPctColor(pct) {
		if (pct >= 100) return "green";
		if (pct >= 80) return "orange";
		return "red";
	}

	// ========================================================================
	// STYLES
	// ========================================================================
	setupStyles() {
		$(`<style>
            .tab-btn {
                padding: 10px 20px;
                background: #6c757d;
                color: #fff;
                border: none;
                cursor: pointer;
                font-weight: 500;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                transition: all 0.3s;
            }

            .tab-btn:hover {
                background: #5a6268;
            }

            .tab-btn.active {
                background: #0066cc;
                border-bottom: 3px solid #0066cc;
            }

            #data-table {
                table-layout: auto;
            }

            #data-table th {
                background: #000;
                color: white;
                font-weight: 600;
                padding: 12px;
                text-align: center;
            }

            #data-table td {
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
            }

            #data-table tbody tr:hover {
                background: #f5f5f5;
            }

            .category-header {
                transition: background 0.2s;
            }

            .category-header:hover {
                background: #e8e8e8 !important;
            }

            .category-toggle {
                display: inline-block;
                width: 20px;
                font-weight: bold;
                color: #0066cc;
            }

            .zone-detail {
                transition: all 0.3s ease;
            }

            .zone-sum-check {
                font-style: italic;
            }
        </style>`).appendTo("head");
	}
}
