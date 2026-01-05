// ============================================================================
// DRISHTI PERFORMANCE DASHBOARD - MONTH-WISE CATEGORY VERSION
// Version: 4.0.0 | Complete Code with Month-wise Category Display
// ============================================================================

frappe.pages["sahayog_dashboard_v4"].on_page_load = function (wrapper) {
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
                        Category Wise
                    </button>
                    <button class="tab-btn ${
						this.state.activeTab === "branch" ? "active" : ""
					}" data-tab="branch">
                        ✨ Branch Wise (Month-wise Categories)
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
	// CATEGORY VIEW (Simplified)
	// ========================================================================
	renderCategoryView(months) {
		this.page.main.find("#table-body").html(`
            <tr><td colspan="100" style="text-align: center; padding: 30px;">
                Category view implementation pending
            </td></tr>
        `);
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
        </style>`).appendTo("head");
	}
}
