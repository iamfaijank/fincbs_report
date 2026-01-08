// ============================================================================
// DRISHTI PERFORMANCE DASHBOARD - SIMPLIFIED BRANCH TABLE
// Version: 4.8.0 | Mokopi-style Clean UI with Row Borders
// ============================================================================

frappe.pages["sahayog_dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "DRISHTI",
		single_column: true,
	});

	new DrishtiDashboardV4(page);
};

class DrishtiDashboardV4 {
	constructor(page) {
		this.page = page;
		this.state = {
			financialYear: "2025-2026",
			activeTab: "category",
			formatMode: "number",
			selectedDate: null,
			selectedCategories: [],
			selectedZones: [],
			selectedRegion: "",
			branchSearchTerm: "",
			selectedMonth: null,
			drillDownActive: false,
		};
		this.data = null;
		this.availableFilters = {
			categories: ["Pinnacle", "Master", "Accelerator", "Starter", "Learner", "Zero Level"],
			zones: [],
			regions: [],
			branches: [],
		};
		this.categoryCounts = {};
		this.zoneCounts = {};

		this.init();
	}

	init() {
		this.setupStyles();
		this.createControls();
		this.createFilterTags();
		this.createTabsAndContainer();
		this.loadData();
	}

	// ========================================================================
	// DRILL-DOWN FUNCTIONALITY
	// ========================================================================
	drillDownToCategory(category) {
		console.log(`🔍 Drilling down to Category: ${category}`);
		this.state.selectedCategories = [category];
		this.state.drillDownActive = true;
		this.updateFilterTagsUI();
		this.switchTab("branch");
	}

	drillDownToZone(category, zone) {
		console.log(`🔍 Drilling down to Category: ${category}, Zone: ${zone}`);
		this.state.selectedCategories = [category];
		this.state.selectedZones = [zone];
		this.state.drillDownActive = true;
		this.updateFilterTagsUI();
		this.switchTab("branch");
	}

	clearDrillDown() {
		if (this.state.drillDownActive) {
			console.log("🔄 Clearing drill-down filters");
			this.state.drillDownActive = false;
			this.clearAllFilters();
		}
	}

	drillDownToCategoryMonth(category, month) {
		console.log(`🔍 Drilling down to Category: ${category}, Month: ${month}`);
		this.state.selectedCategories = [category];
		this.state.selectedMonth = month;
		this.state.drillDownActive = true;
		this.updateFilterTagsUI();
		this.switchTab("branch");
	}

	drillDownToZoneMonth(category, zone, month) {
		console.log(`🔍 Drilling down to Category: ${category}, Zone: ${zone}, Month: ${month}`);
		this.state.selectedCategories = [category];
		this.state.selectedZones = [zone];
		this.state.selectedMonth = month;
		this.state.drillDownActive = true;
		this.updateFilterTagsUI();
		this.switchTab("branch");
	}

	// ========================================================================
	// BASIC CONTROLS
	// ========================================================================
	createControls() {
		const html = `
            <div style="margin-bottom: 15px; padding: 15px; border: 1px solid #778da9; background: #e0e1dd; border-radius: 6px;">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">Financial Year:</label>
                        <select id="fy-selector" style="padding: 6px 12px; border: 1px solid #778da9; border-radius: 4px; margin-left: 8px; background: white; color: #1b263b;">
                            <option value="2025-2026">2025-2026</option>
                            <option value="2026-2027">2026-2027</option>
                        </select>
                    </div>

                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">Date:</label>
                        <input type="date" id="date-selector" style="padding: 6px 12px; border: 1px solid #778da9; border-radius: 4px; margin-left: 8px; background: white; color: #1b263b;" />
                    </div>

                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">Region:</label>
                        <select id="region-selector" style="padding: 6px 12px; border: 1px solid #778da9; border-radius: 4px; margin-left: 8px; min-width: 150px; background: white; color: #1b263b;">
                            <option value="">All Regions</option>
                        </select>
                    </div>

                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">Branch:</label>
                        <input type="text" id="branch-search" placeholder="Search branch..." 
                               style="padding: 6px 12px; border: 1px solid #778da9; border-radius: 4px; margin-left: 8px; min-width: 200px; background: white; color: #1b263b;" />
                    </div>

                    <div style="margin-left: auto;">
                        <button id="format-toggle" class="btn btn-primary btn-sm" style="background: #415a77; border-color: #415a77; color: white;">
                            Show in Words
                        </button>
                        <button id="clear-filters" class="btn btn-secondary btn-sm" style="background: #778da9; border-color: #778da9; color: white; margin-left: 8px;">
                            🔄 Clear Filters
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

		this.page.main.find("#date-selector").on("change", function () {
			self.state.selectedDate = $(this).val();
			self.render();
		});

		this.page.main.find("#format-toggle").on("click", function () {
			self.toggleFormat();
		});

		this.page.main.find("#region-selector").on("change", function () {
			self.state.selectedRegion = $(this).val() || "";
			self.updateCounts();
			self.updateFilterTagsUI();
			self.render();
		});

		let searchTimeout;
		this.page.main.find("#branch-search").on("input", function () {
			clearTimeout(searchTimeout);
							searchTimeout = setTimeout(function () {
							self.state.branchSearchTerm = self.page.main.find("#branch-search").val() || "";
							self.render();
							if (self.state.branchSearchTerm) {
								self.switchTab("branch");
							}
						}, 500);		});

		this.page.main.find("#clear-filters").on("click", function () {
			self.clearAllFilters();
		});
	}

	clearAllFilters() {
		this.state.selectedDate = null;
		this.state.selectedCategories = [];
		this.state.selectedZones = [];
		this.state.selectedRegion = "";
		this.state.branchSearchTerm = "";
		this.state.selectedMonth = null;
		this.state.drillDownActive = false;

		this.page.main.find("#date-selector").val("");
		this.page.main.find("#region-selector").val("");
		this.page.main.find("#branch-search").val("");

		this.updateCounts();
		this.updateFilterTagsUI();
		this.render();
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
	// FILTER TAGS
	// ========================================================================
	createFilterTags() {
		const html = `
            <div class="filter-tags-container">
                <!-- Zone Selection -->
                <div class="filter-section">
                    <label class="filter-section-label">ZONE SELECTION</label>
                    <div class="filter-tags" id="zone-tags"></div>
                </div>

                <!-- Performance Categories -->
                <div class="filter-section">
                    <label class="filter-section-label">PERFORMANCE CATEGORIES</label>
                    <div class="filter-tags" id="category-tags"></div>
                </div>
            </div>
        `;

		$(html).appendTo(this.page.main);
		this.populateFilterTags();
	}

	populateFilterTags() {
		this.updateZoneTags();
		this.updateCategoryTags();
	}

	updateZoneTags() {
		const container = this.page.main.find("#zone-tags");
		container.empty();

		const allZonesCount = this.zoneCounts["all"] || 0;
		const allZonesActive = this.state.selectedZones.length === 0;
		container.append(`
            <button class="filter-tag zone-tag ${allZonesActive ? "active" : ""}" data-zone="all">
                All Zones
                <span class="filter-tag-count">${allZonesCount}</span>
            </button>
        `);

		this.availableFilters.zones.forEach((zone) => {
			const count = this.zoneCounts[zone] || 0;
			const isActive = this.state.selectedZones.includes(zone);
			const zoneNum = zone.match(/\d+/);
			const displayName = zoneNum ? `Zone ${zoneNum[0]}` : zone;

			container.append(`
                <button class="filter-tag zone-tag ${
					isActive ? "active" : ""
				}" data-zone="${zone}">
                    ${displayName}
                    <span class="filter-tag-count">${count}</span>
                </button>
            `);
		});

		this.attachZoneTagEvents();
	}

	updateCategoryTags() {
		const container = this.page.main.find("#category-tags");
		container.empty();

		const categoryColors = {
			Pinnacle: "#10b981",
			Master: "#14b8a6",
			Accelerator: "#3b82f6",
			Starter: "#f59e0b",
			Learner: "#ef4444",
			"Zero Level": "#dc2626",
		};

		const allCategoriesCount = this.categoryCounts["all"] || 0;
		const allCategoriesActive = this.state.selectedCategories.length === 0;
		const totalPct = this.calculateCategoryPercentage("all");

		container.append(`
            <button class="filter-tag category-tag all-tag ${
				allCategoriesActive ? "active" : ""
			}" data-category="all">
                All
                <span class="filter-tag-count">${allCategoriesCount}</span>
                <span class="filter-tag-pct">${totalPct}%</span>
            </button>
        `);

		this.availableFilters.categories.forEach((category) => {
			const count = this.categoryCounts[category] || 0;
			const isActive = this.state.selectedCategories.includes(category);
			const color = categoryColors[category] || "#778da9";
			const pct = this.calculateCategoryPercentage(category);

			container.append(`
                <button class="filter-tag category-tag ${isActive ? "active" : ""}" 
                        data-category="${category}" 
                        style="border-left: 3px solid ${color};">
                    ${category}
                    <span class="filter-tag-count">${count}</span>
                    <span class="filter-tag-pct">${pct}%</span>
                </button>
            `);
		});

		this.attachCategoryTagEvents();
	}

	calculateCategoryPercentage(category) {
		const total = this.categoryCounts["all"] || 0;
		if (total === 0) return "0.0";

		if (category === "all") {
			return "100.0";
		}

		const count = this.categoryCounts[category] || 0;
		return ((count / total) * 100).toFixed(1);
	}

	attachZoneTagEvents() {
		const self = this;

		this.page.main
			.find(".zone-tag")
			.off("click")
			.on("click", function () {
				const zone = $(this).data("zone");

				if (zone === "all") {
					self.state.selectedZones = [];
				} else {
					const index = self.state.selectedZones.indexOf(zone);
					if (index > -1) {
						self.state.selectedZones.splice(index, 1);
					} else {
						self.state.selectedZones.push(zone);
					}

					if (self.state.selectedZones.length === 0) {
						self.state.selectedZones = [];
					}
				}

				self.updateFilterTagsUI();
				self.render();
			});
	}

	attachCategoryTagEvents() {
		const self = this;

		this.page.main
			.find(".category-tag")
			.off("click")
			.on("click", function () {
				const category = $(this).data("category");

				if (category === "all") {
					self.state.selectedCategories = [];
				} else {
					const index = self.state.selectedCategories.indexOf(category);
					if (index > -1) {
						self.state.selectedCategories.splice(index, 1);
					} else {
						self.state.selectedCategories.push(category);
					}

					if (self.state.selectedCategories.length === 0) {
						self.state.selectedCategories = [];
					}
				}

				self.updateFilterTagsUI();
				self.render();
			});
	}

	updateFilterTagsUI() {
		this.page.main.find(".zone-tag").removeClass("active");
		if (this.state.selectedZones.length === 0) {
			this.page.main.find(".zone-tag[data-zone='all']").addClass("active");
		} else {
			this.state.selectedZones.forEach((zone) => {
				this.page.main.find(`.zone-tag[data-zone="${zone}"]`).addClass("active");
			});
		}

		this.page.main.find(".category-tag").removeClass("active");
		if (this.state.selectedCategories.length === 0) {
			this.page.main.find(".category-tag[data-category='all']").addClass("active");
		} else {
			this.state.selectedCategories.forEach((category) => {
				this.page.main
					.find(`.category-tag[data-category="${category}"]`)
					.addClass("active");
			});
		}
	}

	updateCounts() {
		if (!this.data || !this.data.consolidated_branches) return;

		let branches = this.data.consolidated_branches;

		if (this.state.selectedRegion) {
			branches = branches.filter((b) => b.region === this.state.selectedRegion);
		}

		this.categoryCounts = { all: branches.length };
		this.availableFilters.categories.forEach((cat) => {
			this.categoryCounts[cat] = branches.filter((b) => b.latest_category === cat).length;
		});

		this.zoneCounts = { all: branches.length };
		this.availableFilters.zones.forEach((zone) => {
			this.zoneCounts[zone] = branches.filter((b) => b.zone === zone).length;
		});
	}

	// ========================================================================
	// TABS
	// ========================================================================
	createTabsAndContainer() {
		const html = `
            <div style="border: 1px solid #778da9; padding: 12px; background: #fff; border-radius: 6px; margin-top: 15px;">
                <div id="tab-buttons" style="display: flex; gap: 5px; margin-bottom: 15px; border-bottom: 2px solid #778da9;">
                    <button class="tab-btn ${
						this.state.activeTab === "category" ? "active" : ""
					}" data-tab="category">
                        Category Wise
                    </button>
                    <button class="tab-btn ${
						this.state.activeTab === "branch" ? "active" : ""
					}" data-tab="branch">
                        Branch Wise
                    </button>
                </div>

                <div id="error-message" style="color: #0d1b2a; display: none; padding: 10px; background: #ffebee; border-radius: 4px;"></div>

                <div id="tab-content" style="overflow-x: auto;">
                    <div id="data-container" style="transition: opacity 0.2s ease-in-out;"></div>
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

					this.extractAvailableFilters();
					this.updateRegionOptions();
					this.updateCounts();
					this.populateFilterTags();

					this.render();
				} else {
					this.showError("Failed to load data");
				}
			},
			error: () => this.showError("Connection error"),
		});
	}

	extractAvailableFilters() {
		const zones = new Set();
		const regions = new Set();

		if (this.data.consolidated_branches) {
			this.data.consolidated_branches.forEach((branch) => {
				if (branch.zone) zones.add(branch.zone);
				if (branch.region) regions.add(branch.region);
			});
		}

		this.availableFilters.zones = Array.from(zones).sort((a, b) => {
			const aMatch = a.match(/ZONE-(\d+)/);
			const bMatch = b.match(/ZONE-(\d+)/);
			if (aMatch && bMatch) {
				return parseInt(aMatch[1]) - parseInt(bMatch[1]);
			}
			return a.localeCompare(b);
		});

		this.availableFilters.regions = Array.from(regions).sort();
	}

	updateRegionOptions() {
		const regionSelector = this.page.main.find("#region-selector");
		regionSelector.empty();
		regionSelector.append('<option value="">All Regions</option>');

		this.availableFilters.regions.forEach((region) => {
			regionSelector.append(`<option value="${region}">${region}</option>`);
		});
	}

	showError(message) {
		this.page.main.find("#error-message").text(message).show();
		this.page.main.find("#data-container").css("opacity", 0); // Hide content immediately on error
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
		const dataContainer = this.page.main.find("#data-container");

		// Fade out current content
		dataContainer.css("opacity", 0);

		// Wait for fade-out, then update content and fade in
		setTimeout(() => {
			let htmlContent = "";

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
				htmlContent = this.buildBranchTable(this.applyFiltersToData(this.data.consolidated_branches || []), months);
			} else {
				// Use the new HTML generator for category view
				htmlContent = this.getCategoryViewHtml(months);
			}

			dataContainer.html(htmlContent); // Update content

            if (this.state.activeTab === "category") {
                this.attachCategoryCollapseHandlers();
                this.attachDrillDownHandlers();
            }

			dataContainer.css("opacity", 1); // Fade in new content
		}, 200); // Match this duration with the CSS transition duration
	}

	applyFiltersToData(data) {
		let filtered = [...data];

		if (this.state.selectedCategories.length > 0) {
			filtered = filtered.filter((item) => {
				if (this.state.selectedMonth) {
					const monthData = item.monthly_data?.[this.state.selectedMonth];
					return monthData && this.state.selectedCategories.includes(monthData.category);
				} else {
					return this.state.selectedCategories.includes(item.latest_category);
				}
			});
		}

		if (this.state.selectedZones.length > 0) {
			filtered = filtered.filter((item) => this.state.selectedZones.includes(item.zone));
		}

		if (this.state.selectedRegion) {
			filtered = filtered.filter((item) => item.region === this.state.selectedRegion);
		}

		if (this.state.branchSearchTerm) {
			const searchTerm = this.state.branchSearchTerm.toLowerCase().trim();
			filtered = filtered.filter((item) => {
				const branchName = (item.branch_name || "").toString().toLowerCase();
				const branchCode = (item.branch_code || "").toString().toLowerCase();
				return branchName.includes(searchTerm) || branchCode.includes(searchTerm);
			});
		}

		return filtered;
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

		months.forEach((month) => {
			const monthData = categoryData[month];
			if (!monthData || !monthData.grouped_by_category) return;

			const categoryZones = monthData.grouped_by_category[category] || {};

			let zonesToProcess = Object.keys(categoryZones);
			if (this.state.selectedZones.length > 0) {
				zonesToProcess = zonesToProcess.filter((zone) =>
					this.state.selectedZones.includes(zone)
				);
			}

			zonesToProcess.forEach((zone) => {
				const zoneData = categoryZones[zone];
				const branchCount = zoneData.branch_count || 0;
				const target = zoneData.target || 0;
				const achievement = zoneData.achievement || 0;

				totals.monthlyData[month].branches += branchCount;
				totals.monthlyData[month].target += target;
				totals.monthlyData[month].achievement += achievement;

				totals.totalTarget += target;
				totals.totalAchievement += achievement;
			});

			// Only update totalBranches if it's the max count across all months processed so far.
			// This prevents double-counting branches that might appear in multiple months
			// but belong to the same category.
			totals.totalBranches = Math.max(
				totals.totalBranches,
				totals.monthlyData[month].branches
			);
		});

		return totals;
	}

	getZonesForCategory(category, months, categoryData) {
		const zoneSet = new Set();

		months.forEach((month) => {
			const monthData = categoryData[month];
			const categoryZones = monthData?.grouped_by_category?.[category] || {};
			Object.keys(categoryZones).forEach((zone) => zoneSet.add(zone));
		});

		return Array.from(zoneSet).sort((a, b) => {
			const aMatch = a.match(/ZONE-(\d+)/);
			const bMatch = b.match(/ZONE-(\d+)/);
			if (aMatch && bMatch) {
				return parseInt(aMatch[1]) - parseInt(bMatch[1]);
			}
			return a.localeCompare(b);
		});
	}

	attachDrillDownHandlers() {
		const self = this;

		// Attach to elements in the category table view
		this.page.main
			.find(".category-header .drill-category, .zone-detail .drill-zone")
			.off("click")
			.on("click", function (e) {
				e.stopPropagation();
				const category = $(this).data("category");
				const zone = $(this).data("zone"); // Might be undefined for category drill-down
				const month = $(this).data("month");

				if (zone) {
					self.drillDownToZoneMonth(category, zone, month);
				} else if (month) {
					self.drillDownToCategoryMonth(category, month);
				} else {
					self.drillDownToCategory(category);
				}
			});
		
		// Attach to elements in the branch table view
		this.page.main
			.find(".branch-table .drill-category, .branch-table .drill-zone")
			.off("click")
			.on("click", function (e) {
				e.stopPropagation();
				const category = $(this).data("category");
				const zone = $(this).data("zone"); // Might be undefined
				const month = $(this).data("month");

				if (zone) {
					self.drillDownToZoneMonth(category, zone, month);
				} else if (month) {
					self.drillDownToCategoryMonth(category, month);
				} else {
					self.drillDownToCategory(category);
				}
			});
	}

	// ========================================================================
	// CATEGORY VIEW (Table-based) - HTML GENERATOR
	// ========================================================================
	getCategoryViewHtml(months) {
		const categoryData = this.data.months || {};

		if (!categoryData || Object.keys(categoryData).length === 0) {
			this.showError("No category data available");
			return `<div style="text-align: center; padding: 50px; color: #778da9; font-size: 16px;">
                        <div style="font-size: 48px; margin-bottom: 15px;">📭</div>
                        <div style="font-weight: 600; margin-bottom: 8px;">No category data found</div>
                        <div style="font-size: 13px;">Try adjusting your filters or checking data sources</div>
                    </div>`;
		}

		const categoryOrder = [
			"Pinnacle",
			"Master",
			"Accelerator",
			"Starter",
			"Learner",
			"Zero Level",
		];

		const filteredCategories =
			this.state.selectedCategories.length > 0
				? categoryOrder.filter((cat) => this.state.selectedCategories.includes(cat))
				: categoryOrder;

		let html = `
            <table border="1" cellpadding="10" cellspacing="0" style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>${this.buildCategoryTableHeader(months)}</thead>
                <tbody>${this.buildCategoryTableBody(
					months,
					filteredCategories,
					categoryData
				)}</tbody>
                <tfoot>${this.buildCategoryTableFooter(
					months,
					categoryData,
					filteredCategories
				)}</tfoot>
            </table>
        `;

		return html;
	}

	buildCategoryTableHeader(months) {
		let html = `
            <tr class="category-table-header">
                <th style="min-width: 80px; padding: 12px;">Sr No.</th>
                <th style="min-width: 200px; padding: 12px;">Category</th>
        `;

		months.forEach((month) => {
			html += `<th style="text-align: center; min-width: 120px; padding: 12px;">${month}-2025</th>`;
		});

		html += `</tr>`;
		return html;
	}

	buildCategoryTableBody(months, categoryOrder, categoryData) {
		let html = "";
		let srNo = 1;

		categoryOrder.forEach((category) => {
			const categoryTotals = this.aggregateCategoryData(category, months, categoryData);

			if (categoryTotals.totalBranches === 0) {
				return;
			}

			html += this.buildCategoryHeaderRow(category, categoryTotals, months, srNo);
			html += this.buildCategoryZoneRows(category, months, categoryData);
			srNo++;
		});

		return html;
	}

	buildCategoryHeaderRow(category, categoryTotals, months, srNo) {
		const badge = this.getCategoryBadge(category, "normal");

		let html = `
        <tr class="category-header" data-category="${category}" 
            style="background: #e0e1dd; font-weight: 600; cursor: pointer; border-bottom: 1px solid #778da9;">
            <td style="padding: 12px; text-align: center; color: #0d1b2a;">${srNo}</td>
            <td style="padding: 12px; color: #0d1b2a;">
                <span class="category-toggle">▼</span>
                ${badge}
            </td>
    `;

		months.forEach((month) => {
			const md = categoryTotals.monthlyData[month];
			html += `
            <td style="text-align: center; padding: 12px;">
                <span class="drill-category" data-category="${category}" data-month="${month}"
                      style="cursor: pointer; color: #415a77; text-decoration: underline; font-weight: 600; font-size: 16px;"
                      title="Click to drill down to ${month} branches">
                    ${md.branches}
                </span>
            </td>
        `;
		});

		html += `</tr>`;
		return html;
	}

	buildCategoryZoneRows(category, months, categoryData) {
		let html = "";
		const zones = this.getZonesForCategory(category, months, categoryData);

		let filteredZones = zones;
		if (this.state.selectedZones.length > 0) {
			filteredZones = zones.filter((zone) => this.state.selectedZones.includes(zone));
		}

		filteredZones.forEach((zone) => {
			html += `
            <tr class="zone-detail" data-category="${category}" 
                style="display: none; background: #fff; border-left: 33px solid #415a77;">
                <td></td>
                <td style="padding: 12px 12px 12px 40px; color: #1b263b; font-size: 13px;">${zone}</td>
        `;

			months.forEach((month) => {
				const monthData = categoryData[month];
				const zoneData = monthData?.grouped_by_category?.[category]?.[zone] || {};
				const branches = zoneData.branch_count || 0;

				html += `
                <td style="text-align: center; padding: 12px;">
                    ${
						branches > 0
							? `<span class="drill-zone" data-category="${category}" data-zone="${zone}" data-month="${month}"
                          style="cursor: pointer; color: #415a77; text-decoration: underline; font-size: 14px;"
                          title="Click to drill down to ${month} branches in ${zone}">
                        ${branches}
                    </span>`
							: `<span style="color: #778da9;">-</span>`
					}
                </td>
            `;
			});

			html += `</tr>`;
		});

		return html;
	}

	buildCategoryTableFooter(months, categoryData, filteredCategories) {
		const grandTotal = { branches: 0, monthlyData: {} };

		months.forEach((month) => {
			grandTotal.monthlyData[month] = { branches: 0 };
		});

		filteredCategories.forEach((category) => {
			const categoryTotals = this.aggregateCategoryData(category, months, categoryData);

			months.forEach((month) => {
				const md = categoryTotals.monthlyData[month];
				grandTotal.monthlyData[month].branches += md.branches;
			});

			grandTotal.branches = Math.max(grandTotal.branches, categoryTotals.totalBranches);
		});

		let html = `
            <tr style="background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%); color: #e0e1dd; font-weight: bold;">
                <td colspan="2" style="text-align: center; padding: 14px;">GRAND TOTAL</td>
        `;

		months.forEach((month) => {
			const md = grandTotal.monthlyData[month];
			html += `<td style="text-align: center; padding: 14px; font-size: 16px;">${md.branches}</td>`;
		});

		html += `</tr>`;
		return html;
	}

	attachCategoryCollapseHandlers() {
		const self = this;

		this.page.main
			.find(".category-header")
			.off("click")
			.on("click", function (e) {
				if ($(e.target).hasClass("drill-category")) {
					return;
				}

				const category = $(this).data("category");
				const zoneRows = self.page.main.find(`.zone-detail[data-category="${category}"]`);
				const toggle = $(this).find(".category-toggle");

				if (zoneRows.first().is(":visible")) {
					zoneRows.hide();
					toggle.text("▶");
				} else {
					zoneRows.show();
					toggle.text("▼");
				}
			});
	}

	// ========================================================================
	// BRANCH VIEW - HTML TABLE
	// ========================================================================
	renderBranchView(months) {
		let branchData = this.data.consolidated_branches || [];
		branchData = this.applyFiltersToData(branchData);

		if (branchData.length === 0) {
			this.page.main.find("#data-container").html(`
                <div style="text-align: center; padding: 50px; color: #778da9; font-size: 16px;">
                    <div style="font-size: 48px; margin-bottom: 15px;">📭</div>
                    <div style="font-weight: 600; margin-bottom: 8px;">No branches found</div>
                    <div style="font-size: 13px;">Try adjusting your filters</div>
                </div>
            `);
			return;
		}

		let displayMonths = months;
		if (this.state.selectedMonth) {
			displayMonths = months.filter((m) => m === this.state.selectedMonth);
		}

		let html = this.buildBranchTable(branchData, displayMonths);
		this.page.main.find("#data-container").html(html);
	}

	buildBranchTable(branchData, months) {
		const header = this.buildBranchTableHeader(months);
		const body = branchData
			.map((branch, index) => this.buildBranchTableRow(branch, months, index + 1))
			.join("");
		const footer = this.buildBranchTableFooter(branchData, months);

		return `
            <table class="branch-table">
                ${header}
                <tbody>${body}</tbody>
                ${footer}
            </table>
        `;
	}

	buildBranchTableHeader(months) {
		let header = `
            <thead>
                <tr class="branch-table-header">
                    <th rowspan="2" class="sr-col">Sr. No.</th>
                    <th rowspan="2" class="branch-col">Branch</th>
        `;

		months.forEach((month) => {
			header += `<th colspan="4" class="month-col">${month} 2025</th>`;
		});

		header += `</tr><tr class="branch-table-subheader">`;

		months.forEach((month) => {
			header += `
                <th>Category</th>
                <th>Target</th>
                <th>Ach.</th>
                <th>%</th>
            `;
		});

		header += `</tr></thead>`;
		return header;
	}

	buildBranchTableRow(branch, months, serialNo) {
		let row = `
            <tr class="branch-table-row">
                <td class="sr-col">${serialNo}</td>
                <td class="branch-col">
                    <div class="branch-info">
                        <div class="branch-code-name">
                            <a href="/app/branch-profile?sol_id=${
								branch.branch_code
							}" class="branch-code-link">${branch.branch_code || ""}</a>
                            <span class="branch-name">${branch.branch_name || ""}</span>
                        </div>
                        <div class="branch-zone-region">
                            <span class="zone-badge">${branch.zone || ""}</span>
                            <span class="region-label">${branch.region || ""}</span>
                        </div>
                    </div>
                </td>
        `;

		months.forEach((month) => {
			const md = branch.monthly_data?.[month] || {};
			const category = md.category || "N/A";
			const tgt = md.target || 0;
			const ach = md.achievement || 0;
			const pct = md.achievement_pct || this.calcPct(ach, tgt);

			row += `
                <td class="metric-cell category-cell">${this.getCategoryBadge(
					category,
					"small"
				)}</td>
                <td class="metric-cell amount-cell">${this.formatCurrency(tgt)}</td>
                <td class="metric-cell amount-cell">${this.formatCurrency(ach)}</td>
                <td class="metric-cell pct-cell" style="color: ${this.getPctColor(
					pct
				)};">${pct}%</td>
            `;
		});

		row += `</tr>`;
		return row;
	}

	buildBranchTableFooter(branchData, months) {
		const grandTotal = { monthlyData: {} };
		months.forEach((month) => {
			grandTotal.monthlyData[month] = { tgt: 0, ach: 0 };
		});

		branchData.forEach((branch) => {
			months.forEach((month) => {
				const md = branch.monthly_data?.[month] || {};
				grandTotal.monthlyData[month].tgt += md.target || 0;
				grandTotal.monthlyData[month].ach += md.achievement || 0;
			});
		});

		let footer = `
            <tfoot class="branch-table-footer">
                <tr>
                    <td colspan="2">GRAND TOTAL (${branchData.length} Branches)</td>
        `;

		months.forEach((month) => {
			const md = grandTotal.monthlyData[month];
			const pct = this.calcPct(md.ach, md.tgt);
			footer += `
                <td class="metric-cell">&nbsp;</td>
                <td class="metric-cell amount-cell">${this.formatCurrency(md.tgt)}</td>
                <td class="metric-cell amount-cell">${this.formatCurrency(md.ach)}</td>
                <td class="metric-cell pct-cell">${pct}%</td>
            `;
		});

		footer += `</tr></tfoot>`;
		return footer;
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
		const padding = size === "small" ? "2px 6px" : "5px 10px";

		return `<span class="category-badge-span" style="
            background: ${color};
            color: white;
            font-size: ${fontSize};
            font-weight: 700;
            padding: ${padding};
            border-radius: 10px;
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
		if (pct >= 100) return "#22c55e";
		if (pct >= 80) return "#f59e0b";
		return "#ef4444";
	}

	// ========================================================================
	// STYLES - MOKOPI INSPIRED
	// ========================================================================
	setupStyles() {
		$(`<style>
            /* Tab Buttons */
            .tab-btn {
                padding: 10px 20px;
                background: #e0e1dd; /* Lighter background for inactive */
                color: #778da9; /* Greyer text for inactive */
                border: none;
                cursor: pointer;
                font-weight: bold; /* Bold font for all */
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                transition: all 0.3s ease; /* Smooth transition */
            }

            .tab-btn:hover {
                background: #c5c7c6; /* Slightly darker on hover for inactive */
                color: #415a77;
            }

            .tab-btn.active {
                background: #1b263b; /* Dark background for active */
                color: #e0e1dd;
                border-bottom: 3px solid #0d1b2a; /* Stronger highlight */
            }

            /* Filter Tags */
            .filter-tags-container {
                margin-bottom: 15px;
                padding: 15px;
                background: white;
                border: 1px solid #778da9;
                border-radius: 6px;
            }

            .filter-section {
                margin-bottom: 15px;
            }

            .filter-section:last-child {
                margin-bottom: 0;
            }

            .filter-section-label {
                display: block;
                font-size: 11px;
                font-weight: 700;
                color: #1b263b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 10px;
            }

            .filter-tags {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }

            .filter-tag {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 8px 14px;
                background: white;
                border: 1.5px solid #e0e1dd;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 600;
                color: #1b263b;
                transition: all 0.2s ease;
            }

            .filter-tag:hover {
                border-color: #415a77;
                background: rgba(65, 90, 119, 0.05);
            }

            .filter-tag.active {
                background: #415a77;
                border-color: #415a77;
                color: white;
            }

            .filter-tag-count {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-width: 24px;
                height: 20px;
                padding: 0 6px;
                background: rgba(0, 0, 0, 0.08);
                border-radius: 10px;
                font-size: 11px;
                font-weight: 700;
            }

            .filter-tag.active .filter-tag-count {
                background: rgba(255, 255, 255, 0.25);
                color: white;
            }

            .filter-tag-pct {
                display: inline-flex;
                align-items: center;
                font-size: 11px;
                font-weight: 600;
                color: #778da9;
            }

            .filter-tag.active .filter-tag-pct {
                color: rgba(255, 255, 255, 0.85);
            }

            .all-tag {
                background: #1b263b;
                border-color: #1b263b;
                color: white;
            }

            .all-tag:hover {
                background: #0d1b2a;
                border-color: #0d1b2a;
            }

            .all-tag.active {
                background: #0d1b2a;
                border-color: #0d1b2a;
            }

            .all-tag .filter-tag-count,
            .all-tag .filter-tag-pct {
                color: rgba(255, 255, 255, 0.85);
            }

            /* Category Table Styles */
            .category-header {
                transition: background 0.2s;
            }

            .category-header:hover {
                background: rgba(65, 90, 119, 0.15) !important;
            }

            .category-toggle {
                display: inline-block;
                width: 22px;
                font-weight: bold;
                color: #415a77;
                margin-right: 8px;
            }

            .zone-detail {
                transition: all 0.3s ease;
            }

            .drill-category:hover,
            .drill-zone:hover {
                color: #0d1b2a !important;
                font-weight: 700 !important;
            }


            /* ============================================ */
            /* BRANCH TABLE - HTML TABLE STYLE             */
            /* ============================================ */

            .branch-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 13px;
                background: white;
            }

            .branch-table th, .branch-table td {
                padding: 10px;
                border: 1px solid #e0e1dd;
                text-align: center;
                vertical-align: middle;
            }

            /* Header */
            .branch-table-header th, .branch-table-subheader th {
                background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
                color: #e0e1dd;
                position: sticky;
                top: 0;
                z-index: 10;
                font-weight: 600;
            }
            .branch-table-subheader th {
                font-size: 11px;
                font-weight: 500;
            }
            
            .sr-col { width: 50px; }
            .branch-col { width: 280px; text-align: left !important; }
            .month-col { font-weight: 700; }

            /* Body */
            .branch-table-row:hover {
                background: rgba(119, 141, 169, 0.05);
            }
            
            .metric-cell {
                font-size: 13px;
            }
            .amount-cell {
                font-family: monospace;
                font-weight: 500;
            }
            .pct-cell {
                font-weight: 700;
            }
            .category-cell .category-badge-span {
                margin: 0;
            }


            /* Branch Info */
            .branch-info {
                display: flex;
                flex-direction: column;
                gap: 6px;
                text-align: left;
            }

            .branch-code-name {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .branch-code-link {
                color: #415a77;
                font-weight: 700;
                text-decoration: none;
                padding: 2px 6px;
                background: rgba(65, 90, 119, 0.08);
                border-radius: 4px;
            }

            .branch-code-link:hover {
                background: rgba(65, 90, 119, 0.15);
                color: #0d1b2a;
            }

            .branch-name {
                color: #0d1b2a;
                font-weight: 600;
            }

            .branch-zone-region {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 11px;
            }

            .zone-badge {
                background: #778da9;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-weight: 600;
                font-size: 10px;
                text-transform: uppercase;
            }

            .region-label {
                color: #778da9;
                font-weight: 500;
            }
            
            /* Footer */
            .branch-table-footer td {
                background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
                color: #e0e1dd;
                font-weight: 700;
                text-align: center;
            }
            .branch-table-footer td:first-child {
                text-align: left;
            }

        </style>`).appendTo("head");
	}
}
