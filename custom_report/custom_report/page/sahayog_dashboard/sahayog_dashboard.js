// ============================================================================
// DRISHTI PERFORMANCE DASHBOARD - MONTH-WISE CATEGORY VERSION
// Version: 4.4.0 | With Drill-Down from Category to Branch View
// ============================================================================

frappe.pages["sahayog_dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "DRISHTI v4.4 - With Drill-Down",
		single_column: true,
	});

	new DrishtiDashboardV4(page);
};

class DrishtiDashboardV4 {
	constructor(page) {
		this.page = page;
		this.state = {
			financialYear: "2025-2026",
			activeTab: "category", // category | branch
			formatMode: "number", // number | words
			selectedDate: null,
			selectedCategories: [],
			selectedZones: [],
			selectedRegion: "",
			branchSearchTerm: "",
			drillDownActive: false, // Track if drill-down is active
		};
		this.data = null;
		this.availableFilters = {
			categories: ["Pinnacle", "Master", "Accelerator", "Starter", "Learner", "Zero Level"],
			zones: [],
			regions: [],
			branches: [],
		};

		this.init();
	}

	init() {
		this.setupStyles();
		this.createControls();
		this.createTabsAndContainer();
		this.loadData();
	}

	// ========================================================================
	// DRILL-DOWN FUNCTIONALITY
	// ========================================================================
	drillDownToCategory(category) {
		console.log(`🔍 Drilling down to Category: ${category}`);

		// Set filter to only this category
		this.state.selectedCategories = [category];
		this.state.drillDownActive = true;

		// Update UI - uncheck all, then check only this category
		this.page.main.find(".category-checkbox").prop("checked", false);
		this.page.main.find(`.category-checkbox[value="${category}"]`).prop("checked", true);
		this.updateFilterButtonLabel("category");

		// Switch to Branch view
		this.switchTab("branch");
	}

	drillDownToZone(category, zone) {
		console.log(`🔍 Drilling down to Category: ${category}, Zone: ${zone}`);

		// Set filters
		this.state.selectedCategories = [category];
		this.state.selectedZones = [zone];
		this.state.drillDownActive = true;

		// Update category UI
		this.page.main.find(".category-checkbox").prop("checked", false);
		this.page.main.find(`.category-checkbox[value="${category}"]`).prop("checked", true);
		this.updateFilterButtonLabel("category");

		// Update zone UI
		this.page.main.find(".zone-checkbox").prop("checked", false);
		this.page.main.find(`.zone-checkbox[value="${zone}"]`).prop("checked", true);
		this.updateFilterButtonLabel("zone");

		// Switch to Branch view
		this.switchTab("branch");
	}

	clearDrillDown() {
		if (this.state.drillDownActive) {
			console.log("🔄 Clearing drill-down filters");
			this.state.drillDownActive = false;
			this.clearAllFilters();
		}
	}

	// ========================================================================
	// CONTROLS WITH ADVANCED FILTERS
	// ========================================================================
	createControls() {
		const html = `
            <div style="margin-bottom: 15px; padding: 15px; border: 1px solid #ddd; background: #f9f9f9; border-radius: 6px;">
                <!-- Row 1: Main Filters -->
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap; margin-bottom: 12px;">
                    <div>
                        <label style="font-weight: bold; color: #333;">Financial Year:</label>
                        <select id="fy-selector" style="padding: 6px 12px; border: 1px solid #ccc; border-radius: 4px; margin-left: 8px;">
                            <option value="2025-2026">2025-2026</option>
                            <option value="2026-2027">2026-2027</option>
                        </select>
                    </div>

                    <div>
                        <label style="font-weight: bold; color: #333;">Date:</label>
                        <input type="date" id="date-selector" style="padding: 6px 12px; border: 1px solid #ccc; border-radius: 4px; margin-left: 8px;" />
                    </div>

                    <div style="margin-left: auto;">
                        <button id="format-toggle" class="btn btn-primary btn-sm">
                            Show in Words
                        </button>
                    </div>
                </div>

                <!-- Row 2: Advanced Filters -->
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap; padding-top: 12px; border-top: 1px solid #ddd;">
                    <div class="filter-dropdown-container">
                        <label style="font-weight: bold; color: #333;">Category:</label>
                        <button id="category-filter-btn" class="filter-dropdown-btn">
                            <span class="filter-label">All Categories</span>
                            <span class="filter-arrow">▼</span>
                        </button>
                        <div id="category-filter-dropdown" class="filter-dropdown-menu" style="display: none;">
                            <div style="padding: 8px; border-bottom: 1px solid #ddd;">
                                <label style="cursor: pointer; font-weight: 600;">
                                    <input type="checkbox" id="category-select-all" checked> Select All
                                </label>
                            </div>
                            <div id="category-options" style="max-height: 200px; overflow-y: auto;"></div>
                        </div>
                    </div>

                    <div class="filter-dropdown-container">
                        <label style="font-weight: bold; color: #333;">Zone:</label>
                        <button id="zone-filter-btn" class="filter-dropdown-btn">
                            <span class="filter-label">All Zones</span>
                            <span class="filter-arrow">▼</span>
                        </button>
                        <div id="zone-filter-dropdown" class="filter-dropdown-menu" style="display: none;">
                            <div style="padding: 8px; border-bottom: 1px solid #ddd;">
                                <label style="cursor: pointer; font-weight: 600;">
                                    <input type="checkbox" id="zone-select-all" checked> Select All
                                </label>
                            </div>
                            <div id="zone-options" style="max-height: 200px; overflow-y: auto;"></div>
                        </div>
                    </div>

                    <div>
                        <label style="font-weight: bold; color: #333;">Region:</label>
                        <select id="region-selector" style="padding: 6px 12px; border: 1px solid #ccc; border-radius: 4px; margin-left: 8px; min-width: 150px;">
                            <option value="">All Regions</option>
                        </select>
                    </div>

                    <div>
                        <label style="font-weight: bold; color: #333;">Branch:</label>
                        <input type="text" id="branch-search" placeholder="Search branch..." 
                               style="padding: 6px 12px; border: 1px solid #ccc; border-radius: 4px; margin-left: 8px; min-width: 200px;" />
                    </div>

                    <div style="margin-left: auto;">
                        <button id="clear-filters" class="btn btn-secondary btn-sm">
                            🔄 Clear Filters
                        </button>
                    </div>
                </div>
            </div>
        `;

		$(html).appendTo(this.page.main);
		this.attachControlEvents();
		this.populateFilterOptions();
	}

	populateFilterOptions() {
		const categoryContainer = this.page.main.find("#category-options");
		this.availableFilters.categories.forEach((cat) => {
			categoryContainer.append(`
                <div style="padding: 6px 8px;">
                    <label style="cursor: pointer; display: block;">
                        <input type="checkbox" class="category-checkbox" value="${cat}" checked>
                        ${cat}
                    </label>
                </div>
            `);
		});

		this.updateZoneOptions();
	}

	updateZoneOptions() {
		const zoneContainer = this.page.main.find("#zone-options");
		zoneContainer.empty();

		this.availableFilters.zones.forEach((zone) => {
			zoneContainer.append(`
                <div style="padding: 6px 8px;">
                    <label style="cursor: pointer; display: block;">
                        <input type="checkbox" class="zone-checkbox" value="${zone}" checked>
                        ${zone}
                    </label>
                </div>
            `);
		});
	}

	updateRegionOptions() {
		const regionSelector = this.page.main.find("#region-selector");
		regionSelector.empty();
		regionSelector.append('<option value="">All Regions</option>');

		this.availableFilters.regions.forEach((region) => {
			regionSelector.append(`<option value="${region}">${region}</option>`);
		});
	}

	attachControlEvents() {
		const self = this;

		this.page.main.find("#fy-selector").on("change", function () {
			self.state.financialYear = $(this).val();
			self.loadData();
		});

		this.page.main.find("#date-selector").on("change", function () {
			self.state.selectedDate = $(this).val();
			self.applyFiltersAndRender();
		});

		this.page.main.find("#format-toggle").on("click", function () {
			self.toggleFormat();
		});

		this.page.main.find("#category-filter-btn").on("click", function (e) {
			e.stopPropagation();
			self.toggleFilterDropdown("#category-filter-dropdown");
		});

		this.page.main.find("#zone-filter-btn").on("click", function (e) {
			e.stopPropagation();
			self.toggleFilterDropdown("#zone-filter-dropdown");
		});

		this.page.main.find("#category-select-all").on("change", function () {
			const checked = $(this).prop("checked");
			self.page.main.find(".category-checkbox").prop("checked", checked);
			self.updateFilterButtonLabel("category");
			self.applyFiltersAndRender();
		});

		this.page.main.find("#zone-select-all").on("change", function () {
			const checked = $(this).prop("checked");
			self.page.main.find(".zone-checkbox").prop("checked", checked);
			self.updateFilterButtonLabel("zone");
			self.applyFiltersAndRender();
		});

		this.page.main.on("change", ".category-checkbox", function () {
			self.updateFilterButtonLabel("category");
			self.applyFiltersAndRender();
		});

		this.page.main.on("change", ".zone-checkbox", function () {
			self.updateFilterButtonLabel("zone");
			self.applyFiltersAndRender();
		});

		this.page.main.find("#region-selector").on("change", function () {
			self.state.selectedRegion = $(this).val() || "";
			self.applyFiltersAndRender();
		});

		let searchTimeout;
		this.page.main.find("#branch-search").on("input", function () {
			clearTimeout(searchTimeout);
			searchTimeout = setTimeout(function () {
				self.state.branchSearchTerm = self.page.main.find("#branch-search").val() || "";
				self.applyFiltersAndRender();
			}, 500);
		});

		this.page.main.find("#branch-search").on("keypress", function (e) {
			if (e.which === 13) {
				clearTimeout(searchTimeout);
				self.state.branchSearchTerm = $(this).val() || "";
				self.applyFiltersAndRender();
			}
		});

		this.page.main.find("#clear-filters").on("click", function () {
			self.clearAllFilters();
		});

		$(document).on("click", function () {
			self.page.main.find(".filter-dropdown-menu").hide();
		});

		this.page.main.find(".filter-dropdown-menu").on("click", function (e) {
			e.stopPropagation();
		});
	}

	toggleFilterDropdown(selector) {
		const dropdown = this.page.main.find(selector);
		const isVisible = dropdown.is(":visible");

		this.page.main.find(".filter-dropdown-menu").hide();

		if (!isVisible) {
			dropdown.show();
		}
	}

	updateFilterButtonLabel(filterType) {
		if (filterType === "category") {
			const checkedBoxes = this.page.main.find(".category-checkbox:checked");
			const totalBoxes = this.page.main.find(".category-checkbox");
			const label = this.page.main.find("#category-filter-btn .filter-label");

			if (checkedBoxes.length === 0) {
				label.text("No Categories");
			} else if (checkedBoxes.length === totalBoxes.length) {
				label.text("All Categories");
			} else if (checkedBoxes.length === 1) {
				label.text($(checkedBoxes[0]).attr("value"));
			} else {
				label.text(`${checkedBoxes.length} Categories`);
			}
		} else if (filterType === "zone") {
			const checkedBoxes = this.page.main.find(".zone-checkbox:checked");
			const totalBoxes = this.page.main.find(".zone-checkbox");
			const label = this.page.main.find("#zone-filter-btn .filter-label");

			if (checkedBoxes.length === 0) {
				label.text("No Zones");
			} else if (checkedBoxes.length === totalBoxes.length) {
				label.text("All Zones");
			} else if (checkedBoxes.length === 1) {
				label.text($(checkedBoxes[0]).attr("value"));
			} else {
				label.text(`${checkedBoxes.length} Zones`);
			}
		}
	}

	applyFiltersAndRender() {
		const self = this;

		this.state.selectedCategories = [];
		const categoryCheckboxes = this.page.main.find(".category-checkbox:checked");
		categoryCheckboxes.each(function () {
			const domElement = this;
			const val = domElement.getAttribute("value");
			if (val) {
				self.state.selectedCategories.push(val);
			}
		});

		this.state.selectedZones = [];
		const zoneCheckboxes = this.page.main.find(".zone-checkbox:checked");
		zoneCheckboxes.each(function () {
			const domElement = this;
			const val = domElement.getAttribute("value");
			if (val) {
				self.state.selectedZones.push(val);
			}
		});

		console.log("🔍 Filters Applied:", {
			categories: this.state.selectedCategories,
			zones: this.state.selectedZones,
			region: this.state.selectedRegion,
			branch: this.state.branchSearchTerm,
		});

		this.render();

		this.page.main.find(".filter-dropdown-menu").hide();
	}

	clearAllFilters() {
		this.state.selectedDate = null;
		this.state.selectedCategories = [];
		this.state.selectedZones = [];
		this.state.selectedRegion = "";
		this.state.branchSearchTerm = "";
		this.state.drillDownActive = false;

		this.page.main.find("#date-selector").val("");
		this.page.main.find("#region-selector").val("");
		this.page.main.find("#branch-search").val("");
		this.page.main.find(".category-checkbox").prop("checked", true);
		this.page.main.find(".zone-checkbox").prop("checked", true);
		this.page.main.find("#category-select-all").prop("checked", true);
		this.page.main.find("#zone-select-all").prop("checked", true);

		this.updateFilterButtonLabel("category");
		this.updateFilterButtonLabel("zone");

		console.log("🔄 Filters Cleared");

		this.applyFiltersAndRender();
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

                <div id="filter-summary" style="margin-bottom: 10px; padding: 8px; background: #e8f4f8; border-radius: 4px; font-size: 12px; display: none;">
                    <strong>Active Filters:</strong> <span id="filter-summary-text"></span>
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

					this.extractAvailableFilters();
					this.updateZoneOptions();
					this.updateRegionOptions();

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
		const branches = new Set();

		if (this.data.consolidated_branches) {
			this.data.consolidated_branches.forEach((branch) => {
				if (branch.zone) zones.add(branch.zone);
				if (branch.region) regions.add(branch.region);
				if (branch.branch_name) branches.add(branch.branch_name);
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
		this.availableFilters.branches = Array.from(branches).sort();
	}

	showError(message) {
		this.page.main.find("#error-message").text(message).show();
		this.page.main.find("#data-table").hide();
	}

	// ========================================================================
	// RENDERING WITH FILTERS
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

		this.updateFilterSummary();

		if (this.state.activeTab === "branch") {
			this.renderBranchView(months);
		} else {
			this.renderCategoryView(months);
		}
	}

	updateFilterSummary() {
		const filters = [];

		if (this.state.selectedDate) {
			filters.push(`Date: ${this.state.selectedDate}`);
		}

		if (
			this.state.selectedCategories.length > 0 &&
			this.state.selectedCategories.length < this.availableFilters.categories.length
		) {
			filters.push(`Categories: ${this.state.selectedCategories.join(", ")}`);
		}

		if (
			this.state.selectedZones.length > 0 &&
			this.state.selectedZones.length < this.availableFilters.zones.length
		) {
			filters.push(`Zones: ${this.state.selectedZones.join(", ")}`);
		}

		if (this.state.selectedRegion) {
			filters.push(`Region: ${this.state.selectedRegion}`);
		}

		if (this.state.branchSearchTerm) {
			filters.push(`Branch: "${this.state.branchSearchTerm}"`);
		}

		if (filters.length > 0) {
			this.page.main.find("#filter-summary").show();
			this.page.main.find("#filter-summary-text").text(filters.join(" | "));
		} else {
			this.page.main.find("#filter-summary").hide();
		}
	}

	applyFiltersToData(data) {
		let filtered = [...data];

		if (
			this.state.selectedCategories.length > 0 &&
			this.state.selectedCategories.length < this.availableFilters.categories.length
		) {
			filtered = filtered.filter((item) =>
				this.state.selectedCategories.includes(item.latest_category)
			);
		}

		if (
			this.state.selectedZones.length > 0 &&
			this.state.selectedZones.length < this.availableFilters.zones.length
		) {
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

	// ========================================================================
	// CATEGORY VIEW WITH DRILL-DOWN
	// ========================================================================
	renderCategoryView(months) {
		const categoryData = this.data.months || {};

		if (!categoryData || Object.keys(categoryData).length === 0) {
			this.showError("No category data available");
			return;
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
			this.state.selectedCategories.length > 0 &&
			this.state.selectedCategories.length < this.availableFilters.categories.length
				? categoryOrder.filter((cat) => this.state.selectedCategories.includes(cat))
				: categoryOrder;

		let headerHtml = this.buildCategoryTableHeader(months);
		this.page.main.find("#table-head").html(headerHtml);

		let bodyHtml = this.buildCategoryTableBody(months, filteredCategories, categoryData);
		this.page.main.find("#table-body").html(bodyHtml);

		let footerHtml = this.buildCategoryTableFooter(months, categoryData, filteredCategories);
		this.page.main.find("#table-foot").html(footerHtml);

		this.attachCategoryCollapseHandlers();
		this.attachDrillDownHandlers(); // NEW: Attach drill-down click handlers
	}

	// NEW: Attach drill-down click handlers
	attachDrillDownHandlers() {
		const self = this;

		// Category row drill-down - click on branch count
		this.page.main
			.find(".drill-category")
			.off("click")
			.on("click", function (e) {
				e.stopPropagation(); // Prevent row collapse
				const category = $(this).data("category");
				self.drillDownToCategory(category);
			});

		// Zone row drill-down - click on branch count
		this.page.main
			.find(".drill-zone")
			.off("click")
			.on("click", function (e) {
				e.stopPropagation();
				const category = $(this).data("category");
				const zone = $(this).data("zone");
				self.drillDownToZone(category, zone);
			});
	}

	buildCategoryTableHeader(months) {
		let html = `
            <tr style="background: #000; color: #fff;">
                <th style="min-width: 180px;">Category</th>
        `;

		months.forEach((month) => {
			html += `
                <th style="text-align: center; min-width: 140px;" colspan="3">
                    ${month} 2025/26
                </th>
            `;
		});

		html += `<th style="text-align: center; min-width: 140px;" colspan="3">TOTAL</th></tr>`;
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
			const categoryTotals = this.aggregateCategoryData(category, months, categoryData);

			if (
				categoryTotals.totalBranches === 0 &&
				categoryTotals.totalTarget === 0 &&
				categoryTotals.totalAchievement === 0
			) {
				return;
			}

			html += this.buildCategoryHeaderRow(category, categoryTotals, months);
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

		months.forEach((month) => {
			const monthData = categoryData[month];
			if (!monthData || !monthData.grouped_by_category) return;

			const categoryZones = monthData.grouped_by_category[category] || {};

			let zonesToProcess = Object.keys(categoryZones);
			if (
				this.state.selectedZones.length > 0 &&
				this.state.selectedZones.length < this.availableFilters.zones.length
			) {
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

		months.forEach((month) => {
			const md = categoryTotals.monthlyData[month];
			const pct = this.calcPct(md.achievement, md.target);

			html += `
                <td style="text-align: center; padding: 10px;">
                    <span class="drill-category" data-category="${category}" 
                          style="cursor: pointer; color: #0066cc; text-decoration: underline; font-weight: 600;"
                          title="Click to drill down to branches">
                        ${md.branches}
                    </span>
                </td>
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

		html += `
            <td style="text-align: center; padding: 10px; background: #fff;">
                <span class="drill-category" data-category="${category}" 
                      style="cursor: pointer; color: #0066cc; text-decoration: underline; font-weight: 600;"
                      title="Click to drill down to branches">
                    ${categoryTotals.totalBranches}
                </span>
            </td>
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

		let filteredZones = zones;
		if (
			this.state.selectedZones.length > 0 &&
			this.state.selectedZones.length < this.availableFilters.zones.length
		) {
			filteredZones = zones.filter((zone) => this.state.selectedZones.includes(zone));
		}

		filteredZones.forEach((zone) => {
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
                    <td style="text-align: center; padding: 10px;">
                        ${
							branches > 0
								? `<span class="drill-zone" data-category="${category}" data-zone="${zone}" 
                              style="cursor: pointer; color: #0066cc; text-decoration: underline;"
                              title="Click to drill down to branches">
                            ${branches}
                        </span>`
								: "-"
						}
                    </td>
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
                <td style="text-align: center; padding: 10px; background: #fafafa;">
                    <span class="drill-zone" data-category="${category}" data-zone="${zone}" 
                          style="cursor: pointer; color: #0066cc; text-decoration: underline;"
                          title="Click to drill down to branches">
                        ${maxBranches}
                    </span>
                </td>
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

		const categoryTotals = this.aggregateCategoryData(category, months, categoryData);

		html += `
            <tr class="zone-detail zone-sum-check" data-category="${category}" 
                style="display: none; background: #e8f4f8; border-bottom: 2px solid #000; font-weight: 600;">
                <td style="padding: 10px 10px 10px 40px;">SUM CHECK:</td>
        `;

		months.forEach((month) => {
			const md = categoryTotals.monthlyData[month];

			html += `
                <td style="text-align: center; padding: 10px;">${md.branches}</td>
                <td style="text-align: right; padding: 10px;">${this.formatCurrency(
					md.target
				)} ✅</td>
                <td style="text-align: right; padding: 10px;">${this.formatCurrency(
					md.achievement
				)}</td>
            `;
		});

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

		return Array.from(zoneSet).sort((a, b) => {
			const aMatch = a.match(/ZONE-(\d+)/);
			const bMatch = b.match(/ZONE-(\d+)/);

			if (aMatch && bMatch) {
				return parseInt(aMatch[1]) - parseInt(bMatch[1]);
			}
			return a.localeCompare(b);
		});
	}

	buildCategoryTableFooter(months, categoryData, filteredCategories) {
		const grandTotal = { branches: 0, target: 0, achievement: 0, monthlyData: {} };

		months.forEach((month) => {
			grandTotal.monthlyData[month] = { branches: 0, target: 0, achievement: 0 };
		});

		filteredCategories.forEach((category) => {
			const categoryTotals = this.aggregateCategoryData(category, months, categoryData);

			months.forEach((month) => {
				const md = categoryTotals.monthlyData[month];
				grandTotal.monthlyData[month].branches += md.branches;
				grandTotal.monthlyData[month].target += md.target;
				grandTotal.monthlyData[month].achievement += md.achievement;
			});

			grandTotal.target += categoryTotals.totalTarget;
			grandTotal.achievement += categoryTotals.totalAchievement;
			grandTotal.branches = Math.max(grandTotal.branches, categoryTotals.totalBranches);
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
			.on("click", function (e) {
				// Don't collapse if clicking on drill-down link
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

	// [REST OF THE CODE REMAINS SAME - Branch View, Utility Functions, Styles]
	// Continuing from previous file...

	renderBranchView(months) {
		let branchData = this.data.consolidated_branches || [];

		branchData = this.applyFiltersToData(branchData);

		if (branchData.length === 0) {
			this.page.main.find("#table-head").html("");
			this.page.main.find("#table-body").html(`
                <tr><td colspan="100" style="text-align: center; padding: 30px; color: #999;">
                    No branch data available with current filters
                </td></tr>
            `);
			this.page.main.find("#table-foot").html("");
			return;
		}

		let headerHtml = `
            <tr style="background: #000; color: #fff;">
                <th style="min-width: 60px;">Sr.No.</th>
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

		const bodyRows = branchData.map((branch, index) =>
			this.buildBranchRow(branch, months, index + 1)
		);
		this.page.main.find("#table-body").html(bodyRows.join(""));

		const footerHtml = this.buildBranchFooter(branchData, months);
		this.page.main.find("#table-foot").html(footerHtml);
	}

	buildBranchRow(branch, months, serialNo) {
		let html = `
            <tr style="background: #fff; border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 10px; text-align: center; font-weight: 600;">${serialNo}</td>
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
			const monthCategory = md.category || branch.latest_category || "Unknown";

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

            /* Drill-down links */
            .drill-category:hover,
            .drill-zone:hover {
                color: #004499 !important;
                font-weight: 700 !important;
            }

            /* Filter Dropdown Styles */
            .filter-dropdown-container {
                position: relative;
                display: inline-block;
            }

            .filter-dropdown-btn {
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                cursor: pointer;
                margin-left: 8px;
                min-width: 180px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 8px;
                font-size: 13px;
            }

            .filter-dropdown-btn:hover {
                background: #f5f5f5;
                border-color: #999;
            }

            .filter-dropdown-menu {
                position: absolute;
                top: 100%;
                left: 0;
                margin-top: 4px;
                background: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                z-index: 1000;
                min-width: 200px;
            }

            .filter-arrow {
                color: #666;
                font-size: 10px;
            }

            .filter-label {
                flex: 1;
                text-align: left;
            }
        </style>`).appendTo("head");
	}
}
