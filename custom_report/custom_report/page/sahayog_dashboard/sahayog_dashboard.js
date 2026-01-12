// ============================================================================
// DRISHTI PERFORMANCE DASHBOARD - COMPLETE FUNCTIONAL VERSION
// Version: 6.0.0 | All Issues Fixed
// ============================================================================

frappe.pages["sahayog_dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "DRISHTI",
		single_column: true,
	});

	new DrishtiDashboard(page);
};

class DrishtiDashboard {
	constructor(page) {
		this.page = page;
		this.state = {
			financialYear: "2025-2026",
			activeTab: "zone",
			viewType: "Monthly",
			targetType: "Monthly",
			formatMode: "number",
			selectedDate: null,
			selectedCategories: [],
			selectedZones: [],
			selectedRegion: "",
			branchSearchTerm: "",
			selectedMonth: null,
			drillDownActive: false,
			expandedZones: {}, // Track expanded/collapsed zones
			selectedSegment: "all",
		};
		this.data = null;
		this.availableFilters = {
			categories: ["Pinnacle", "Master", "Accelerator", "Starter", "Learner", "Zero Level"],
			zones: [],
			regions: [],
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

	processNewApiResponse() {
		const data = this.data;

		// Extract months
		this.months = data.months.map((m) => ({
			key: m.key,
			display: m.display,
			date: m.date,
		}));

		// Direct mapping
		this.zoneData = data.zone_wise;
		this.categoryData = data.category_wise;
		this.branchData = data.branch_wise;

		// Extract zones from zone_wise data
		const zonesSet = new Set();
		this.zoneData.forEach((item) => {
			if (item.zone === item.region) {
				zonesSet.add(item.zone);
			}
		});

		this.availableFilters.zones = Array.from(zonesSet).sort((a, b) => {
			const aNum = a.match(/ZONE-(\d+)/)?.[1];
			const bNum = b.match(/ZONE-(\d+)/)?.[1];
			return aNum && bNum ? parseInt(aNum) - parseInt(bNum) : a.localeCompare(b);
		});

		// Category counts from first month
		const firstMonth = this.months[0]?.key;
		if (firstMonth) {
			this.categoryCounts = {};
			this.categoryData.forEach((cat) => {
				this.categoryCounts[cat.category] = cat.months[firstMonth]?.count || 0;
			});
			this.categoryCounts.all = this.branchData.length;
		}

		// Zone counts
		this.zoneCounts = {};
		this.availableFilters.zones.forEach((zone) => {
			this.zoneCounts[zone] = this.branchData.filter((b) => b.zone === zone).length;
		});
		this.zoneCounts.all = this.branchData.length;

		// Update region options
		this.updateRegionOptions();
	}

	// ========================================================================
	// CONTROLS - View, Target, FY, Date, Region, Branch, Format
	// ========================================================================
	createControls() {
		// All controls have been moved to createTabsAndContainer
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

		this.updateFilterCounts();
		this.updateFilterTagsUI();
		this.loadData();
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
	// FILTER TAGS - Zone & Category Selection
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
				}

				self.updateFilterTagsUI();
				self.loadData();
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
				}

				self.updateFilterTagsUI();
				self.render();
			});
	}

	updateFilterTagsUI() {
		// Zone tags
		this.page.main.find(".zone-tag").removeClass("active");
		if (this.state.selectedZones.length === 0) {
			this.page.main.find(".zone-tag[data-zone='all']").addClass("active");
		} else {
			this.state.selectedZones.forEach((zone) => {
				this.page.main.find(`.zone-tag[data-zone="${zone}"]`).addClass("active");
			});
		}

		// Category tags
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

	updateFilterCounts() {
		if (!this.branchData) return;

		let filteredBranches = this.branchData;

		// Apply zone filter
		if (this.state.selectedZones.length > 0) {
			filteredBranches = filteredBranches.filter((b) =>
				this.state.selectedZones.includes(b.zone)
			);
		}

		// Apply region filter
		if (this.state.selectedRegion) {
			filteredBranches = filteredBranches.filter(
				(b) => b.region === this.state.selectedRegion
			);
		}

		this.categoryCounts.all = filteredBranches.length;
		this.zoneCounts.all = filteredBranches.length;

		const firstMonth = this.months[0]?.key;
		if (firstMonth) {
			this.availableFilters.categories.forEach((catName) => {
				this.categoryCounts[catName] = filteredBranches.filter(
					(b) => b.months[firstMonth]?.category === catName
				).length;
			});
		}

		this.availableFilters.zones.forEach((zone) => {
			this.zoneCounts[zone] = this.branchData.filter((b) => b.zone === zone).length;
		});

		this.populateFilterTags();
	}

	// ========================================================================
	// TABS - Zone Wise, Category Wise, Branch Wise
	// ========================================================================
	createTabsAndContainer() {
		const html = `
            <div style="border: 1px solid #778da9; padding: 12px; background: #fff; border-radius: 6px; margin-top: 15px;">
                <!-- Filters Row -->
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #ddd;">
                    <!-- Financial Year -->
                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">FY:</label>
                        <select id="fy-selector" style="padding: 6px 12px; border: 1px solid #778da9; border-radius: 4px; margin-left: 8px; background: white; color: #1b263b;">
                            <option value="2025-2026">2025-2026</option>
                            <option value="2026-2027">2026-2027</option>
                        </select>
                    </div>

                    <!-- View Toggle Buttons -->
                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">View:</label>
                        <div class="btn-group" role="group" style="margin-left: 8px;">
                            <button type="button" class="btn btn-sm view-toggle-btn active" data-view="Monthly">Monthly</button>
                            <button type="button" class="btn btn-sm view-toggle-btn" data-view="Quarterly">Quarterly</button>
                            <button type="button" class="btn btn-sm view-toggle-btn" data-view="Yearly">Yearly</button>
                        </div>
                    </div>

                    <!-- Target Toggle Buttons -->
                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">Target:</label>
                        <div class="btn-group" role="group" style="margin-left: 8px;">
                            <button type="button" class="btn btn-sm target-toggle-btn active" data-target="Monthly">Monthly</button>
                            <button type="button" class="btn btn-sm target-toggle-btn" data-target="YTD">YTD</button>
                            <button type="button" class="btn btn-sm target-toggle-btn" data-target="Yearly">Yearly</button>
                        </div>
                    </div>

                    <!-- Date Selector -->
                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">Date:</label>
                        <input type="date" id="date-selector" style="padding: 6px 12px; border: 1px solid #778da9; border-radius: 4px; margin-left: 8px; background: white; color: #1b263b;" />
                    </div>

                    <!-- Format Toggle Buttons -->
                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">Format:</label>
                        <div class="btn-group" role="group" style="margin-left: 8px;">
                            <button type="button" class="btn btn-sm format-toggle-btn active" data-format="number">Numbers</button>
                            <button type="button" class="btn btn-sm format-toggle-btn" data-format="words">Words</button>
                        </div>
                    </div>

                    <!-- Region Filter -->
                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">Region:</label>
                        <select id="region-selector" style="padding: 6px 12px; border: 1px solid #778da9; border-radius: 4px; margin-left: 8px; min-width: 150px; background: white; color: #1b263b;">
                            <option value="">All Regions</option>
                        </select>
                    </div>
                </div>

                <div id="tab-buttons" style="display: flex; align-items: center; gap: 5px; margin-bottom: 15px; border-bottom: 2px solid #778da9;">
                    <button class="tab-btn ${
						this.state.activeTab === "zone" ? "active" : ""
					}" data-tab="zone">
                        Zone Wise
                    </button>
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

                    <!-- Search and Clear Actions -->
                    <div style="margin-left: auto; display: flex; align-items: center; gap: 10px;">
						<select id="segment-filter" style="padding: 6px 12px; border: 1px solid #778da9; border-radius: 4px; background: white; color: #1b263b;">
							<option value="all">All Segments</option>
							<option value="Top 25%">Top 25%</option>
							<option value="Next 25%">Next 25%</option>
							<option value="Mid 25%">Mid 25%</option>
							<option value="Bottom 25%">Bottom 25%</option>
						</select>
                        <input type="text" id="branch-search" placeholder="Search branch..." 
                               style="padding: 6px 12px; border: 1px solid #778da9; border-radius: 4px; min-width: 200px; background: white; color: #1b263b;" />
                        <button id="clear-filters" class="btn btn-secondary btn-sm" style="background: #778da9; border-color: #778da9; color: white;">
                            🔄 Clear Filters
                        </button>
                    </div>
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

		// Tab buttons
		this.page.main.find(".tab-btn").on("click", function () {
			const tabId = $(this).data("tab");
			self.switchTab(tabId);
		});

		// Branch Search with debounce
		let searchTimeout;
		this.page.main.find("#branch-search").on("input", function () {
			clearTimeout(searchTimeout);
			searchTimeout = setTimeout(() => {
				self.state.branchSearchTerm = $(this).val() || "";
				self.loadData();
				if (self.state.branchSearchTerm) {
					self.switchTab("branch");
				}
			}, 500);
		});

		// Financial Year
		this.page.main.find("#fy-selector").on("change", function () {
			self.state.financialYear = $(this).val();
			self.loadData();
		});

		// View Toggle Buttons
		this.page.main.find(".view-toggle-btn").on("click", function () {
			self.page.main.find(".view-toggle-btn").removeClass("active");
			$(this).addClass("active");
			self.state.viewType = $(this).data("view");
			self.loadData();
		});

		// Target Toggle Buttons
		this.page.main.find(".target-toggle-btn").on("click", function () {
			self.page.main.find(".target-toggle-btn").removeClass("active");
			$(this).addClass("active");
			self.state.targetType = $(this).data("target");
			self.loadData();
		});

		// Date Selector
		this.page.main.find("#date-selector").on("change", function () {
			self.state.selectedDate = $(this).val();
			self.loadData();
		});

		// Format Toggle
		this.page.main.find(".format-toggle-btn").on("click", function () {
			self.page.main.find(".format-toggle-btn").removeClass("active");
			$(this).addClass("active");
			self.state.formatMode = $(this).data("format");
			self.render();
		});

		// Region Filter
		this.page.main.find("#region-selector").on("change", function () {
			self.state.selectedRegion = $(this).val() || "";
			self.loadData();
		});

		// Clear Filters
		this.page.main.find("#clear-filters").on("click", function () {
			self.clearAllFilters();
		});

		// Segment Filter
		this.page.main.find("#segment-filter").on("change", function () {
			self.state.selectedSegment = $(this).val();
			self.render();
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
		const self = this;

		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_sahayog_dashboard",
			args: {
				financial_year: this.state.financialYear,
				view: this.state.viewType,
				target_type: this.state.targetType,
				filters: JSON.stringify({
					zones: this.state.selectedZones.length > 0 ? this.state.selectedZones : [],
				}),
				selected_date: this.state.selectedDate,
			},
			callback: (r) => {
				if (r.message) {
					self.data = r.message;
					self.processNewApiResponse();
					self.updateFilterCounts();
					self.render();
				}
			},
		});
	}

	updateRegionOptions() {
		const regionSet = new Set();
		this.zoneData.forEach((item) => {
			if (item.zone !== item.region) {
				regionSet.add(item.region);
			}
		});

		this.availableFilters.regions = Array.from(regionSet).sort();

		const regionSelector = this.page.main.find("#region-selector");
		regionSelector.empty();
		regionSelector.append('<option value="">All Regions</option>');

		this.availableFilters.regions.forEach((region) => {
			regionSelector.append(`<option value="${region}">${region}</option>`);
		});
	}

	showError(message) {
		this.page.main.find("#error-message").text(message).show();
		this.page.main.find("#data-container").css("opacity", 0);
	}

	// ========================================================================
	// RENDERING - Main Render Function
	// ========================================================================
	render() {
		if (!this.data) {
			this.showError("No data available");
			return;
		}

		this.page.main.find("#error-message").hide();
		const dataContainer = this.page.main.find("#data-container");

		dataContainer.css("opacity", 0);

		setTimeout(() => {
			let htmlContent = "";

			if (!this.months || this.months.length === 0) {
				this.showError("No months found");
				return;
			}

			if (this.state.activeTab === "zone") {
				htmlContent = this.renderZoneTable();
			} else if (this.state.activeTab === "category") {
				htmlContent = this.renderCategoryTable();
			} else if (this.state.activeTab === "branch") {
				htmlContent = this.buildBranchTable(
					this.applyFiltersToData(this.branchData || []),
					this.months
				);
			}

			dataContainer.html(htmlContent);

			// Attach handlers after rendering

			if (this.state.activeTab === "zone") {
				this.attachZoneExpandHandlers();
			} else if (this.state.activeTab === "category") {
				this.attachMovementPopupHandlers();

				this.attachCategoryExpandHandlers();

				this.attachDrillHandlers();

				this.attachZoneDrillHandlers();
			}

			dataContainer.css("opacity", 1);
		}, 200);
	}

	// ========================================================================

	// ZONE WISE VIEW - Expandable/Collapsible

	// ========================================================================

	renderZoneTable() {
		const months = this.months;

		let html = `

			    <table class="table table-bordered zone-wise-table">

			        <thead>

			            <tr class="zone-table-header">

			                <th rowspan="2">Sr</th>

			                <th rowspan="2">Zone/Region</th>

			                <th rowspan="2">Branches</th>

			    `;

		months.forEach((month) => {
			html += `<th colspan="3">${month.display}</th>`;
		});

		html += '</tr><tr class="zone-table-subheader">';

		months.forEach(() => {
			html += "<th>Target</th><th>Ach</th><th>%</th>";
		});

		html += "</tr></thead><tbody>";

		// Group data by zone

		const zoneGroups = {};

		this.zoneData.forEach((item) => {
			if (item.zone === item.region) {
				// Zone total row

				if (!zoneGroups[item.zone]) {
					zoneGroups[item.zone] = { total: item, regions: [] };
				} else {
					zoneGroups[item.zone].total = item;
				}
			} else {
				// Region row

				if (!zoneGroups[item.zone]) {
					zoneGroups[item.zone] = { total: null, regions: [] };
				}

				zoneGroups[item.zone].regions.push(item);
			}
		});

		let sr = 1;

		Object.keys(zoneGroups)

			.sort((a, b) => {
				const aNum = a.match(/ZONE-(\d+)/)?.[1];

				const bNum = b.match(/ZONE-(\d+)/)?.[1];

				return aNum && bNum ? parseInt(aNum) - parseInt(bNum) : a.localeCompare(b);
			})

			.forEach((zoneName) => {
				const zoneGroup = zoneGroups[zoneName];

				const isExpanded = this.state.expandedZones[zoneName] || false;

				// Zone Total Row

				if (zoneGroup.total) {
					html += this.buildZoneRow(zoneGroup.total, sr++, true, zoneName, isExpanded);
				}

				// Region Rows (hidden by default)

				zoneGroup.regions.forEach((regionItem) => {
					html += this.buildRegionRow(regionItem, "", zoneName, isExpanded);
				});
			});

		html += "</tbody></table>";

		return html;
	}

	buildZoneRow(zoneItem, sr, isZoneTotal, zoneName, isExpanded) {
		const months = this.months;

		const firstMonthData = zoneItem.months[months[0].key];

		const branchCount = firstMonthData?.branches || 0;

		let html = `<tr class="zone-total-row" data-zone="${zoneName}" style="background-color: #e0e1dd; font-weight: bold; cursor: pointer;">`;

		html += `<td>${sr}</td>`;

		html += `<td><span class="zone-toggle">${isExpanded ? "▼" : "▶"}</span> ${zoneName}</td>`;

		html += `<td>${branchCount}</td>`;

		months.forEach((month) => {
			const mdata = zoneItem.months[month.key];

			if (mdata) {
				html += `

			                <td>${this.formatNumber(mdata.target)}</td>

			                <td>${this.formatNumber(mdata.achievement)}</td>

			                <td style="color: ${this.getPctColor(
								mdata.percentage
							)}">${mdata.percentage?.toFixed(1)}%</td>

			            `;
			} else {
				html += "<td>-</td><td>-</td><td>-</td>";
			}
		});

		return html + "</tr>";
	}

	buildRegionRow(regionItem, sr, zoneName, isExpanded) {
		const months = this.months;

		const firstMonthData = regionItem.months[months[0].key];

		const branchCount = firstMonthData?.branches || 0;

		let html = `<tr class="region-detail-row" data-zone="${zoneName}" style="display: ${
			isExpanded ? "table-row" : "none"
		}; border-left: 4px solid #415a77;">`;

		html += `<td>${sr}</td>`;

		html += `<td style="padding-left: 30px;">${regionItem.region}</td>`;

		html += `<td>${branchCount}</td>`;

		months.forEach((month) => {
			const mdata = regionItem.months[month.key];

			if (mdata) {
				html += `

			                <td>${this.formatNumber(mdata.target)}</td>

			                <td>${this.formatNumber(mdata.achievement)}</td>

			                <td style="color: ${this.getPctColor(
								mdata.percentage
							)}">${mdata.percentage?.toFixed(1)}%</td>

			            `;
			} else {
				html += "<td>-</td><td>-</td><td>-</td>";
			}
		});

		return html + "</tr>";
	}

	attachZoneExpandHandlers() {
		const self = this;

		this.page.main

			.find(".zone-total-row")

			.off("click")

			.on("click", function () {
				const zoneName = $(this).data("zone");

				self.state.expandedZones[zoneName] = !self.state.expandedZones[zoneName];

				self.render();
			});
	}

	// ========================================================================

	// CATEGORY WISE VIEW - With Zone Breakdown

	// ========================================================================

	renderCategoryTable() {
		const months = this.months;

		const latestMonthKey = months[0]?.key;

		if (!latestMonthKey) return "<div>No data available for the selected period.</div>";

		const categoryConfig = {
			Pinnacle: { grade: "A+", range: ">100%", color: "#10b981", health: "Excellent" },

			Master: { grade: "A", range: "80-100%", color: "#14b8a6", health: "Good" },

			Accelerator: { grade: "B", range: "60-80%", color: "#3b82f6", health: "Improving" },

			Starter: { grade: "C", range: "40-60%", color: "#f59e0b", health: "Needs Attention" },

			Learner: { grade: "D", range: "20-40%", color: "#ef4444", health: "At Risk" },

			"Zero Level": { grade: "E", range: "0-20%", color: "#dc2626", health: "Critical" },
		};

		const categoryOrder = Object.keys(categoryConfig);

		let html = `

			    <table class="table table-bordered category-table-redesigned">

			        <thead>

			            <tr>

			                <th style="width: 25%;">Category</th>

			                <th style="width: 15%;">Performance Band</th>

			                <th style="width: 15%;">Branch Count</th>

			                <th style="width: 20%;">Movement (vs Prev. Day)</th>

			                <th style="width: 25%;">Health Status</th>

			            </tr>

			        </thead>

			        <tbody>

			    `;

		categoryOrder.forEach((catName) => {
			const config = categoryConfig[catName];

			const catData = this.categoryData.find((c) => c.category === catName);

			const monthData = catData?.months[latestMonthKey];

			const count = monthData?.count || 0;

			const changes = monthData?.changes || { increased: [], decreased: [] };

			const upCount = changes.increased.length;

			const downCount = changes.decreased.length;

			const isExpanded = this.state.expandedZones[`cat_${catName}`] || false;

			html += `

			            <tr class="category-row-redesigned" data-category="${catName}" style="border-left: 5px solid ${
				config.color
			};">

			                <td class="cat-name-cell">

			                    <span class="category-toggle">${isExpanded ? "▼" : "▶"}</span>

			                    <span class="cat-grade" style="background-color: ${config.color};">${
				config.grade
			}</span>

			                    <span>${catName}</span>

			                </td>

			                <td class="perf-band-cell">${config.range}</td>

			                <td class="count-cell drill-cell" data-category="${catName}" data-month="${latestMonthKey}">

			                    <span class="drill-link">${count}</span>

			                </td>

			                <td class="movement-cell" data-changes='${JSON.stringify(changes)}'>

			                    <div class="movement-summary">

			                        ${upCount > 0 ? `<span class="mov-up">↑ ${upCount}</span>` : ""}

			                        ${downCount > 0 ? `<span class="mov-down">↓ ${downCount}</span>` : ""}

			                        ${
										upCount === 0 && downCount === 0
											? `<span class="mov-neutral">-</span>`
											: ""
									}

			                    </div>

			                </td>

			                <td class="health-cell">

			                    <span class="health-indicator" style="background-color: ${
									config.color
								};"></span>

			                    ${config.health}

			                </td>

			            </tr>

			        `;

			// Zone Breakdown Rows

			if (isExpanded) {
				html += `

			                <tr class="zone-breakdown-row-redesigned" data-category-parent="${catName}">

			                    <td colspan="5">

			                        <div class="zone-breakdown-container">

			                            <div class="zone-breakdown-cards-container">

			                                ${this.availableFilters.zones

												.map((zone) => {
													const zoneCount =
														monthData?.zone_breakdown[zone] || 0;

													const isDisabled = zoneCount === 0;

													return `

													                                        <div class="zone-card ${
																								isDisabled
																									? "disabled-zone-card"
																									: ""
																							}">

													                                            <div class="zone-card-name">${zone}</div>

													                                            <div class="zone-card-count">

													                                                ${
																										isDisabled
																											? `<span>${zoneCount}</span>`
																											: `<span class="zone-drill-link" data-category="${catName}" data-month="${latestMonthKey}" data-zone="${zone}">

													                                                        ${zoneCount}

													                                                    </span>`
																									}

													                                            </div>

													                                        </div>

													                                        `;
												})

												.join("")}

			                            </div>

			                        </div>

			                    </td>

			                </tr>

			                `;
			}
		});

		html += "</tbody></table>";

		return html;
	}

	attachMovementPopupHandlers() {
		const self = this;

		this.page.main

			.find(".movement-cell")

			.on("mouseenter", function (e) {
				// Clean up any existing popups

				$(".movement-popup").remove();

				const changesData = $(this).data("changes");

				if (!changesData) return;

				const { increased, decreased } = changesData;

				if (increased.length === 0 && decreased.length === 0) return;

				let popupContent = "";

				if (increased.length > 0) {
					popupContent += `<div class="popup-section improved">`;

					popupContent += `<h6>Upgraded Branches (${increased.length})</h6>`;

					increased.forEach((item) => {
						popupContent += `

			                        <div class="popup-item">

			                            <div class="item-header">

			                                <span class="branch-name">${item.branch} (${item.zone})</span>

			                                <span class="cat-change">${item.previous_category} → ${
							item.current_category
						}</span>

			                            </div>

			                            <div class="item-body">

			                                <span class="pct-change">${item.previous_percentage.toFixed(
												2
											)}% → ${item.current_percentage.toFixed(2)}%</span>

			                                <span class="diff-change">+₹${self.formatCurrency(
												item.achievement_diff
											)} | +${item.percentage_diff.toFixed(2)}%</span>

			                            </div>

			                        </div>

			                    `;
					});

					popupContent += `</div>`;
				}

				if (decreased.length > 0) {
					popupContent += `<div class="popup-section declined">`;

					popupContent += `<h6>Downgraded Branches (${decreased.length})</h6>`;

					decreased.forEach((item) => {
						popupContent += `

			                        <div class="popup-item">

			                            <div class="item-header">

			                                <span class="branch-name">${item.branch} (${item.zone})</span>

			                                <span class="cat-change">${item.previous_category} → ${
							item.current_category
						}</span>

			                            </div>

			                            <div class="item-body">

			                                <span class="pct-change">${item.previous_percentage.toFixed(
												2
											)}% → ${item.current_percentage.toFixed(2)}%</span>

			                                <span class="diff-change">-₹${self.formatCurrency(
												Math.abs(item.achievement_diff)
											)} | ${item.percentage_diff.toFixed(2)}%</span>

			                            </div>

			                        </div>

			                    `;
					});

					popupContent += `</div>`;
				}

				const popup = $(`<div class="movement-popup">${popupContent}</div>`).appendTo(
					"body"
				);

				// Viewport-aware positioning logic
				const popupHeight = popup.outerHeight();
				const popupWidth = popup.outerWidth();
				const windowHeight = $(window).height();
				const scrollY = $(window).scrollTop();
				const cursorY = e.pageY;

				let top, left;

				// Position horizontally
				left = e.pageX - popupWidth / 2;

				// Check vertical space
				if (cursorY + popupHeight + 20 > windowHeight + scrollY) {
					// Not enough space below, position above cursor
					top = cursorY - popupHeight - 15;
				} else {
					// Enough space below, position below cursor
					top = cursorY + 15;
				}

				// Apply final position
				popup.css({ top: `${top}px`, left: `${left}px` });
			})

			.on("mouseleave", function () {
				$(".movement-popup").remove();
			});
	}

	attachCategoryExpandHandlers() {
		const self = this;

		this.page.main

			.find(".category-row-redesigned")

			.off("click")

			.on("click", function (e) {
				// Stop if a drill-link or movement cell was clicked

				if ($(e.target).closest(".drill-cell, .movement-cell, .zone-drill-link").length) {
					return;
				}

				const catName = $(this).data("category");

				self.state.expandedZones[`cat_${catName}`] =
					!self.state.expandedZones[`cat_${catName}`];

				self.render();
			});
	}

	getChangesBadge(catData) {
		const monthKey = this.months[0]?.key;

		const changes = catData.months[monthKey]?.changes;

		if (!changes) return "—";

		const up = changes.increased?.length || 0;

		const down = changes.decreased?.length || 0;

		if (up === 0 && down === 0) return '<span class="changes-badge">—</span>';

		return `<span class="changes-badge">↑${up} ↓${down}</span>`;
	}

	// ========================================================================

	// DRILL-DOWN FUNCTIONALITY

	// ========================================================================

	attachDrillHandlers() {
		const self = this;

		this.page.main.find(".drill-cell").on("click", function (e) {
			e.stopPropagation();

			const category = $(this).data("category");

			const month = $(this).data("month");

			self.drillDownToCategoryMonth(category, month);
		});
	}

	attachZoneDrillHandlers() {
		const self = this;

		this.page.main.find(".zone-drill-link").on("click", function (e) {
			e.stopPropagation();

			const category = $(this).data("category");

			const month = $(this).data("month");

			const zone = $(this).data("zone");

			self.drillDownToZoneCategoryMonth(category, zone, month);
		});
	}

	drillDownToCategoryMonth(category, month) {
		console.log(`🔍 Drilling down to Category: ${category}, Month: ${month}`);

		this.state.selectedCategories = [category];

		this.state.selectedZones = []; // Clear zone filter

		this.state.selectedMonth = month;

		this.state.drillDownActive = true;

		this.updateFilterTagsUI();

		this.switchTab("branch");
	}

	drillDownToZoneCategoryMonth(category, zone, month) {
		console.log(`🔍 Drilling down to Category: ${category}, Zone: ${zone}, Month: ${month}`);

		this.state.selectedCategories = [category];

		this.state.selectedZones = [zone];

		this.state.selectedMonth = month;

		this.state.drillDownActive = true;

		this.updateFilterTagsUI();

		this.switchTab("branch");
	}

	// ========================================================================

	// BRANCH VIEW - Filtered Table

	// ========================================================================

	applyFiltersToData(data) {
		let filtered = [...data];

		if (this.state.selectedCategories.length > 0) {
			const filterMonth = this.state.selectedMonth || this.months[0]?.key;
			if (filterMonth) {
				filtered = filtered.filter((branch) => {
					const monthData = branch.months[filterMonth];
					return monthData && this.state.selectedCategories.includes(monthData.category);
				});
			}
		}

		if (this.state.selectedZones.length > 0) {
			filtered = filtered.filter((branch) => this.state.selectedZones.includes(branch.zone));
		}

		if (this.state.selectedRegion) {
			filtered = filtered.filter((branch) => branch.region === this.state.selectedRegion);
		}

		if (this.state.branchSearchTerm) {
			const searchTerm = this.state.branchSearchTerm.toLowerCase().trim();
			filtered = filtered.filter((branch) => {
				const branchName = (branch.branch || "").toLowerCase();
				const solId = (branch.sol_id || "").toLowerCase();
				return branchName.includes(searchTerm) || solId.includes(searchTerm);
			});
		}

		return filtered;
	}

	buildBranchTable(branchData, months) {
		if (branchData.length === 0) {
			return `
                <div style="text-align: center; padding: 50px; color: #778da9; font-size: 16px;">
                    <div style="font-size: 48px; margin-bottom: 15px;">📭</div>
                    <div style="font-weight: 600; margin-bottom: 8px;">No branches found</div>
                    <div style="font-size: 13px;">Try adjusting your filters</div>
                </div>
            `;
		}

		let displayMonths = months;
		if (this.state.selectedMonth) {
			displayMonths = months.filter((m) => m.key === this.state.selectedMonth);
		}

		// 1. Determine sort key
		const sortMonthKey =
			this.state.selectedMonth || (months.length > 0 ? months[months.length - 1].key : null);

		// 2. Sort data
		if (sortMonthKey) {
			branchData.sort((a, b) => {
				const aPct = a.months[sortMonthKey]?.percentage || 0;
				const bPct = b.months[sortMonthKey]?.percentage || 0;
				return bPct - aPct; // Descending
			});
		}

		// 3. Assign Segments and Row Styles to each branch
		const total = branchData.length;
		branchData.forEach((branch, index) => {
			let segment, color;
			if (total < 4) {
				segment = "N/A";
				color = "transparent";
			} else {
				const top25_index = Math.floor(total * 0.25);
				const next25_index = Math.floor(total * 0.5);
				const mid25_index = Math.floor(total * 0.75);

				if (index < top25_index) {
					segment = "Top 25%";
					color = "#d4edda";
				} else if (index < next25_index) {
					segment = "Next 25%";
					color = "#cce5ff";
				} else if (index < mid25_index) {
					segment = "Mid 25%";
					color = "#fff3cd";
				} else {
					segment = "Bottom 25%";
					color = "#f8d7da";
				}
			}
			branch.performanceSegment = segment;
			branch.rowStyle = `background-color: ${color};`;
		});

		// 4. Filter by selected segment
		let filteredBranchData = branchData;
		if (this.state.selectedSegment && this.state.selectedSegment !== "all") {
			filteredBranchData = branchData.filter(
				(branch) => branch.performanceSegment === this.state.selectedSegment
			);
		}

		const header = this.buildBranchTableHeader(displayMonths);
		const body = filteredBranchData
			.map((branch, index) =>
				this.buildBranchTableRow(
					branch,
					displayMonths,
					index + 1,
					branch.rowStyle,
					branch.performanceSegment
				)
			)
			.join("");

		return `
            <table class="branch-table">
                ${header}
                <tbody>${body}</tbody>
            </table>
        `;
	}

	buildBranchTableHeader(months) {
		let header = `
            <thead>
                <tr class="branch-table-header">
                    <th rowspan="2" class="sr-col">Sr. No.</th>
                    <th rowspan="2" class="branch-col">Branch</th>
					<th rowspan="2" >Performance Segments</th>
        `;

		months.forEach((month) => {
			header += `<th colspan="4" class="month-col">${month.display}</th>`;
		});

		header += `</tr><tr class="branch-table-subheader">`;

		months.forEach(() => {
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

	buildBranchTableRow(branch, months, serialNo, rowStyle = "", segmentName = "") {
		let html = `<tr class="branch-table-row" data-sol-id="${branch.sol_id}" style="${rowStyle}">`;
		html += `<td>${serialNo}</td>`;
		html += `<td>
			<div class="branch-info">
				<div class="branch-code-name">
					<a href="/app/branch-profile?sol_id=${branch.sol_id}" class="branch-code-link">${branch.sol_id}</a>
					<span class="branch-name">${branch.branch}</span>
				</div>
				<div class="branch-zone-region">
					<span class="zone-badge">${branch.zone}</span>
					<span class="region-label">${branch.region}</span>
				</div>
			</div>
		</td>`;
		html += `<td>${segmentName}</td>`;

		months.forEach((month) => {
			const mdata = branch.months[month.key];
			if (mdata) {
				const pct = mdata.percentage || 0;
				const status = mdata.status || "";
				const diff = mdata.percentage_diff || 0;

				html += `
                <td class="metric-cell category-cell">${this.getCategoryBadge(
					mdata.category,
					"small"
				)}</td>
                <td class="metric-cell amount-cell">${this.formatNumber(mdata.target)}</td>
                <td class="metric-cell amount-cell">${this.formatNumber(mdata.achievement)}</td>
                <td class="metric-cell pct-cell" style="color:${this.getPctColor(pct)}">
                    ${pct.toFixed(1)}%
                    ${
						status
							? `<span class="status-badge ${status}">${this.getStatusIcon(
									status
							  )} ${
									diff > 0 ? `+${diff.toFixed(1)}%` : `${diff.toFixed(1)}%`
							  }</span>`
							: ""
					}
                </td>
            `;
			} else {
				html += "<td>-</td><td>-</td><td>-</td><td>-</td>";
			}
		});

		return html + "</tr>";
	}

	// ========================================================================
	// UTILITY FUNCTIONS
	// ========================================================================
	formatNumber(value) {
		return this.formatCurrency(value);
	}

	formatCurrency(value) {
		if (!value || value === 0) return "-";
		const numValue = Math.round(value);

		if (this.state.formatMode === "words") {
			if (numValue >= 1000000000) {
				// 100+ Crore
				return `${(numValue / 10000000).toFixed(2)} Cr`;
			}
			if (numValue >= 10000000) {
				// 1+ Crore
				return `${(numValue / 10000000).toFixed(2)} Cr`;
			}
			if (numValue >= 100000) {
				// 1+ Lakh
				return `${(numValue / 100000).toFixed(2)} L`;
			}
			if (numValue >= 1000) {
				// 1+ Thousand
				return `${(numValue / 1000).toFixed(2)} K`;
			}
			return numValue.toString();
		} else {
			return new Intl.NumberFormat("en-IN").format(numValue);
		}
	}

	getPctColor(pct) {
		if (pct >= 100) return "#10b981";
		if (pct >= 80) return "#14b8a6";
		if (pct >= 60) return "#3b82f6";
		if (pct >= 40) return "#f59e0b";
		if (pct >= 20) return "#ef4444";
		return "#dc2626";
	}

	getStatusIcon(status) {
		const icons = {
			improved: "🟢",
			declined: "🔴",
			increased: "🟡↑",
			decreased: "🟠↓",
			unchanged: "⚪",
			new: "✨",
		};
		return icons[status] || "";
	}

	getCategoryBadge(category, size = "normal") {
		const colors = {
			Pinnacle: "#10b981",
			Master: "#14b8a6",
			Accelerator: "#3b82f6",
			Starter: "#f59e0b",
			Learner: "#ef4444",
			"Zero Level": "#dc2626",
		};
		const color = colors[category] || "#778da9";
		const fontSize = size === "small" ? "10px" : "12px";
		return `<span class="category-badge" style="background:${color};color:white;padding:4px 8px;border-radius:4px;font-size:${fontSize};font-weight:600;display:inline-block;">${category}</span>`;
	}

	getStatusIcon(status) {
		const icons = {
			improved: "🟢",
			declined: "🔴",
			increased: "🟡↑",
			decreased: "🟠↓",
			unchanged: "⚪",
			new: "✨",
		};
		return icons[status] || "";
	}

	getCategoryBadge(category, size = "normal") {
		const colors = {
			Pinnacle: "#10b981",
			Master: "#14b8a6",
			Accelerator: "#3b82f6",
			Starter: "#f59e0b",
			Learner: "#ef4444",
			"Zero Level": "#dc2626",
		};
		const color = colors[category] || "#778da9";
		const fontSize = size === "small" ? "10px" : "12px";
		return `<span class="category-badge" style="background:${color};color:white;padding:4px 8px;border-radius:4px;font-size:${fontSize};font-weight:600;display:inline-block;">${category}</span>`;
	}

	// ========================================================================
	// STYLES
	// ========================================================================
	setupStyles() {
		const styles = `
            <style>
                /* Filter Tags Styles */
                .filter-tags-container {
                    margin-bottom: 15px;
                    padding: 15px;
                    background: #fff;
                    border: 1px solid #778da9;
                    border-radius: 6px;
                }

                .filter-section {
                    margin-bottom: 12px;
                }

                .filter-section:last-child {
                    margin-bottom: 0;
                }

                .filter-section-label {
                    display: block;
                    font-size: 11px;
                    font-weight: 700;
                    color: #0d1b2a;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 8px;
                }

                .filter-tags {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                }

                .filter-tag {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    padding: 6px 12px;
                    background: #fff;
                    border: 2px solid #778da9;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 600;
                    color: #1b263b;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .filter-tag:hover {
                    background: #f8f9fa;
                    border-color: #415a77;
                    transform: translateY(-1px);
                }

                .filter-tag.active {
                    background: #415a77;
                    border-color: #415a77;
                    color: #e0e1dd;
                }

                .filter-tag-count {
                    background: rgba(255, 255, 255, 0.2);
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 700;
                }

                .filter-tag.active .filter-tag-count {
                    background: rgba(255, 255, 255, 0.3);
                }

                .filter-tag-pct {
                    font-size: 11px;
                    opacity: 0.8;
                }

                /* Toggle Button Styles */
                .btn-group .btn {
                    background: #fff;
                    border: 1px solid #778da9;
                    color: #1b263b;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }

                .btn-group .btn:hover {
                    background: #f8f9fa;
                    border-color: #415a77;
                }

                .btn-group .btn.active {
                    background: #415a77;
                    border-color: #415a77;
                    color: #e0e1dd;
                }

                /* Tab Styles */
                .tab-btn {
                    padding: 10px 20px;
                    background: #fff;
                    border: none;
                    border-bottom: 3px solid transparent;
                    color: #1b263b;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .tab-btn:hover {
                    background: #f8f9fa;
                    color: #415a77;
                }

                .tab-btn.active {
                    border-bottom-color: #415a77;
                    color: #415a77;
                    background: #e0e1dd;
                }

                /* Zone Table Styles */
                .zone-wise-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12px;
                }

                .zone-table-header th {
                    background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
                    color: #e0e1dd;
                    padding: 12px 8px;
                    text-align: center;
                    font-weight: 600;
                    border: 1px solid #778da9;
                }

                .zone-table-subheader th {
                    background: #1b263b;
                    color: #e0e1dd;
                    padding: 8px;
                    font-size: 11px;
                    border: 1px solid #778da9;
                }

                .zone-wise-table td {
                    padding: 10px 8px;
                    border: 1px solid #778da9;
                    text-align: center;
                }

                .zone-total-row {
                    background-color: #e0e1dd !important;
                    font-weight: bold;
                    cursor: pointer;
                }

                .zone-total-row:hover {
                    background-color: #d4d5d1 !important;
                }

                .zone-toggle, .category-toggle {
                    display: inline-block;
                    width: 20px;
                    margin-right: 8px;
                    transition: transform 0.2s ease;
                }

                .region-detail-row {
                    background: #fff;
                    border-left: 4px solid #415a77;
                }

                /* Category Table Styles */
                .category-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12px;
                }

                .category-table-header th {
                    background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
                    color: #e0e1dd;
                    padding: 12px 8px;
                    font-weight: 600;
                    border: 1px solid #778da9;
                    text-align: center;
                }

                .category-table-subheader th {
                    background: #1b263b;
                    color: #e0e1dd;
                    padding: 8px;
                    font-size: 11px;
                    border: 1px solid #778da9;
                }

                .category-table td {
                    padding: 10px 8px;
                    border: 1px solid #778da9;
                    text-align: center;
                }

                .category-header-row {
                    background: #e0e1dd;
                    font-weight: 600;
                    cursor: pointer;
                }

                .category-header-row:hover {
                    background: #d4d5d1;
                }

                .zone-breakdown-row {
                    background: #fff;
                    border-left: 4px solid #415a77;
                }

                .drill-cell {
                    cursor: pointer;
                }

                .drill-link {
                    color: #415a77;
                    text-decoration: underline;
                }

                .drill-link:hover {
                    color: #0d1b2a;
                    font-weight: bold;
                }

                .changes-badge {
                    display: inline-block;
                    margin-left: 10px;
                    font-size: 12px;
                    font-weight: bold;
                    color: #415a77;
                }

                /* Branch Table Styles */
                .branch-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12px;
                }

                .branch-table-header th {
                    background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
                    color: #e0e1dd;
                    padding: 12px 8px;
                    text-align: center;
                    font-weight: 600;
                    border: 1px solid #778da9;
                }

                .branch-table-subheader th {
                    background: #1b263b;
                    color: #e0e1dd;
                    padding: 8px;
                    font-size: 11px;
                    border: 1px solid #778da9;
                }

                .branch-table-row {
                    border-bottom: 1px solid #e0e1dd;
                }

                .branch-table-row:hover {
                    background: #f8f9fa;
                }

                .branch-table td {
                    padding: 10px 8px;
                    border: 1px solid #778da9;
                }

                .sr-col {
                    width: 60px;
                    text-align: center;
                }

                .branch-col {
                    min-width: 200px;
                }

                .branch-info {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                }

                .branch-code-name {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }

                .branch-code-link {
                    color: #415a77;
                    font-weight: 600;
                    text-decoration: none;
                    font-size: 13px;
                }

                .branch-code-link:hover {
                    text-decoration: underline;
                }

                .branch-name {
                    color: #1b263b;
                    font-size: 12px;
                }

                .branch-zone-region {
                    display: flex;
                    gap: 8px;
                    align-items: center;
                }

                .zone-badge {
                    background: #415a77;
                    color: #e0e1dd;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: 600;
                }

                .region-label {
                    color: #778da9;
                    font-size: 11px;
                }

                .metric-cell {
                    text-align: center;
                }

                .category-cell {
                    min-width: 100px;
                }

                .amount-cell {
                    min-width: 90px;
                    font-weight: 500;
                }

                .pct-cell {
                    min-width: 80px;
                    font-weight: 600;
                }

                .status-badge {
                    display: inline-block;
                    margin-left: 8px;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 6px;
                    border-radius: 4px;
                    color: #fff;
                }
                .status-badge.improved { background-color: #10b981; }
                .status-badge.declined { background-color: #dc2626; }
                .status-badge.increased { background-color: #f59e0b; }
                .status-badge.decreased { background-color: #ef4444; }
                .status-badge.unchanged { background-color: #778da9; }
                .status-badge.new { background-color: #3b82f6; }

                /* Redesigned Category Table */
                .category-table-redesigned {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 14px;
                    border: 1px solid #dee2e6;
                }
                .category-table-redesigned th {
                    background-color: #f8f9fa;
                    font-weight: 600;
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 2px solid #dee2e6;
                    color: #495057;
                }
                .category-table-redesigned td {
                    padding: 15px;
                    border-bottom: 1px solid #dee2e6;
                    vertical-align: middle;
                }
                .cat-name-cell {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-weight: 600;
                }
                .cat-grade {
                    flex-shrink: 0;
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    color: white;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 16px;
                    font-weight: 700;
                }
                .perf-band-cell {
                    font-family: 'monospace';
                    font-weight: 600;
                    color: #495057;
                }
                .count-cell {
                    font-weight: 700;
                    font-size: 18px;
                    text-align: center;
                }
                .movement-cell {
                    cursor: pointer;
                }
                .movement-summary {
                    display: flex;
                    gap: 15px;
                    font-weight: 700;
                    font-size: 16px;
                    justify-content: center;
                }
                .mov-up { color: #10b981; }
                .mov-down { color: #dc2626; }
                .mov-neutral { color: #6c757d; }
                .health-cell {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-weight: 600;
                    color: #495057;
                }
                .health-indicator {
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                }

                /* Movement Popup */
                .movement-popup {
                    position: absolute;
                    background-color: #fff;
                    border: 1px solid #ccc;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.15);
                    border-radius: 8px;
                    padding: 12px;
                    z-index: 1000;
                    width: 420px;
                    font-size: 13px;
                }
                .popup-section { margin-bottom: 10px; }
                .popup-section:last-child { margin-bottom: 0; }
                .popup-section h6 {
                    font-weight: 700;
                    margin: 0 0 8px 0;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #eee;
                }
                .popup-section.improved h6 { color: #10b981; }
                .popup-section.declined h6 { color: #dc2626; }
                .popup-item {
                    padding: 8px;
                    border-radius: 4px;
                    margin-bottom: 6px;
                }
                .popup-section.improved .popup-item { background-color: #f0fff4; }
                .popup-section.declined .popup-item { background-color: #fff5f5; }
                .item-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 4px;
                }
                .item-header .branch-name { font-weight: 600; color: #333; }
                .item-header .cat-change { font-weight: 600; font-size: 12px; }
                .item-body {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 12px;
                    color: #555;
                }
                .item-body .pct-change { font-family: monospace; }
                .item-body .diff-change { font-weight: 600; }
                .popup-section.improved .diff-change { color: #10b981; }
                .popup-section.declined .diff-change { color: #dc2626; }

                /* Category Row Expansion & Drilldown */
                .category-row-redesigned {
                    cursor: pointer;
                }
                .category-row-redesigned:hover {
                    background-color: #f8f9fa;
                }
                .count-cell .drill-link {
                    color: #007bff;
                    text-decoration: underline;
                    font-weight: 700;
                }
                .count-cell .drill-link:hover {
                    color: #0056b3;
                }

                /* Zone Breakdown */
                .zone-breakdown-row-redesigned td {
                    padding: 0 !important;
                    background-color: #f8f9fa;
                }
                .zone-breakdown-container {
                    padding: 15px 25px;
                }
                .zone-breakdown-container table {
                    width: 100%;
                    text-align: center;
                    border-collapse: collapse;
                }
                .zone-breakdown-container th {
                    font-weight: 600;
                    font-size: 12px;
                    color: #495057;
                    padding-bottom: 8px;
                }
                .zone-breakdown-container td {
                    font-size: 14px;
                    font-weight: 700;
                    padding: 8px;
                    border: none;
                }

                /* Zone Breakdown Cards */
                .zone-breakdown-cards-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                    padding: 10px 5px;
                }
                .zone-card {
                    background: #fff;
                    border: 1px solid #e0e1dd;
                    border-radius: 6px;
                    padding: 8px 12px;
                    text-align: center;
                    flex-grow: 1;
                    min-width: 90px;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
                }
                .zone-card-name {
                    font-size: 11px;
                    font-weight: 600;
                    color: #778da9;
                    margin-bottom: 2px;
                }
                .zone-card-count {
                    font-size: 18px;
                    font-weight: 700;
                    color: #1b263b;
                }
                .zone-drill-link {
                    cursor: pointer;
                    color: #007bff;
                }
                .zone-drill-link:hover {
                    text-decoration: underline;
                    color: #0056b3;
                }

                /* Disabled Zone Card */
                .disabled-zone-card {
                    background-color: #f8f9fa;
                    color: #adb5bd;
                    cursor: not-allowed;
                    opacity: 0.7;
                }
                .disabled-zone-card .zone-card-name {
                    color: #adb5bd;
                }
                .disabled-zone-card .zone-card-count span {
                    color: #adb5bd;
                    text-decoration: none;
                    cursor: not-allowed;
                }
            </style>
        `;

		$("head").append(styles);
	}
}
