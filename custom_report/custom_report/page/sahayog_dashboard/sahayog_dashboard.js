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
			financialYear: null,
			activeTab: "zone",
			viewType: "Monthly",
			targetType: "Monthly",
			formatMode: "words",
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
		// Store selected date per tab
		this.tabDates = {
			zone: null,
			category: null,
			product: null,
			agent: null,
			branch: null,
		};
		this.data = null;
		this.availableFilters = {
			categories: ["Pinnacle", "Master", "Accelerator", "Starter", "Learner", "Zero Level"],
			zones: [],
			regions: [],
		};
		this.categoryCounts = {};
		this.zoneCounts = {};
		this.productData = [];

		this.init();
	}

	init() {
		this.setupStyles();
		this.setupBranchProfilePopup();
		this.createControls();
		this.createFilterTags();
		this.createTabsAndContainer();
		this.updateStateFromUrl(); // Read from URL and update state
		this.updateUiFromState(); // Update UI from state
		this.loadFinancialYears();
	}

	setupBranchProfilePopup() {
		if (!window.showBranchProfilePopup) {
			window.showBranchProfilePopup = (sol_id) => {
				let d = new frappe.ui.Dialog({
					title: 'Branch Profile - ' + sol_id,
					size: 'extra-large',
					minimizable: true
				});

				d.$body.html(`
					<div id="iframe-loader-${sol_id}" style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 85vh; width: 100%;">
						<div class="spinner-border text-primary" role="status" style="margin-bottom: 15px; width: 3rem; height: 3rem; animation: spinner-border .75s linear infinite;"></div>
						<h4 style="color: #475569; font-weight: 600;">Branch Profile is Loading...</h4>
						<p style="color: #64748b;">Please wait</p>
					</div>
					<iframe id="iframe-content-${sol_id}" src="/branch_profile?sol_id=${sol_id}" style="width: 100%; height: 85vh; border: none; border-radius: 4px; display: none;"></iframe>
				`);

				d.$body.find(`#iframe-content-${sol_id}`).on('load', function() {
					d.$body.find(`#iframe-loader-${sol_id}`).fadeOut(200, function() {
						d.$body.find(`#iframe-content-${sol_id}`).fadeIn(200);
					});
				});

				d.$wrapper.css({
					'backdrop-filter': 'blur(5px)',
					'background-color': 'rgba(15, 23, 42, 0.6)'
				});

				// Increase the width of the modal
				d.$wrapper.find('.modal-dialog').css({
					'max-width': '80vw',
					'width': '80vw'
				});

				// Add Full Screen button before the close button
				const fullScreenBtn = $('<button class="btn btn-default btn-xs" style="margin-right: 12px; font-weight: 500; border-radius: 4px;"><i class="fa fa-external-link"></i> Full Screen</button>');
				fullScreenBtn.on('click', function() {
					window.location.href = '/branch_profile?sol_id=' + sol_id;
				});
				
				let actions = d.$wrapper.find('.modal-actions');
				if (actions.length > 0) {
					actions.prepend(fullScreenBtn);
				} else {
					// Fallback for older Frappe versions
					let closeBtn = d.$wrapper.find('.modal-header .btn-close, .modal-header .close');
					if (closeBtn.length > 0) {
						closeBtn.before(fullScreenBtn);
					}
				}

				// Some extra styling for the dialog to look modern and hide the default padding
				d.$body.css({
					'padding': '0',
					'overflow': 'hidden'
				});

				d.show();
			};
		}
	}

	loadFinancialYears() {
		const self = this;
		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_available_financial_years",
			callback: function (r) {
				if (r.message && r.message.length > 0) {
					self.populateFinancialYears(r.message);
					// Select the latest (first) available year if not already set
					if (!self.state.financialYear || !r.message.includes(self.state.financialYear)) {
						self.state.financialYear = r.message[0];
						self.page.main.find("#fy-selector").val(self.state.financialYear);
					}
					self.loadData();
				}
			},
		});
	}

	populateFinancialYears(fyList) {
		const selector = this.page.main.find("#fy-selector");
		selector.empty();
		fyList.forEach(function (fy) {
			selector.append(`<option value="${fy}">${fy}</option>`);
		});
		selector.val(this.state.financialYear);
	}

	isPreviousFinancialYear() {
		if (!this.state.financialYear) return false;

		const fyStartYear = parseInt(this.state.financialYear.split("-")[0], 10);
		const today = frappe.datetime.str_to_obj(frappe.datetime.get_today());
		const currentFyStartYear =
			today.getMonth() >= 3 ? today.getFullYear() : today.getFullYear() - 1;

		return fyStartYear < currentFyStartYear;
	}

	getPreviousFinancialYearDefaultDate() {
		if (!this.isPreviousFinancialYear()) return null;

		const fyParts = this.state.financialYear.split("-");
		return `${fyParts[1]}-03-31`;
	}

	applyPreviousFinancialYearDefaultDate() {
		const defaultDate = this.getPreviousFinancialYearDefaultDate();
		if (!defaultDate) return;

		this.state.selectedDate = defaultDate;
		this.page.main.find("#date-selector").val(defaultDate);
		if (this.state.activeTab && this.tabDates.hasOwnProperty(this.state.activeTab)) {
			this.tabDates[this.state.activeTab] = defaultDate;
		}
	}

	getDashboardViewForRequest() {
		if (
			this.isPreviousFinancialYear() &&
			(this.state.viewType === "Monthly" || this.state.viewType === "Quarterly")
		) {
			return "Yearly";
		}

		return this.state.viewType;
	}

	normalizeDashboardResponse(data) {
		if (!this.isPreviousFinancialYear()) return data;

		if (this.state.viewType === "Monthly") {
			data.months = (data.months || []).filter((month) => month.key === "MAR");
		} else if (this.state.viewType === "Quarterly") {
			data.months = (data.months || []).filter((month) =>
				["JAN", "FEB", "MAR"].includes(month.key),
			);
		}

		return data;
	}

	normalizeTargetType(targetType) {
		return ["Monthly", "YTD", "Yearly"].includes(targetType) ? targetType : "Monthly";
	}

	setupStyles() {
		// --- Font and Style Injection ---
		const fontLink = document.createElement("link");
		fontLink.href =
			"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap";
		fontLink.rel = "stylesheet";
		document.head.appendChild(fontLink);

		const style = `
            :root {
                --font-primary: 'Inter', sans-serif;
                --text-base: 14px;
                --line-height-base: 1.5;
            }
            .frappe-page .page-head, .frappe-page .page-content {
                font-family: var(--font-primary);
                font-size: var(--text-base);
                line-height: var(--line-height-base);
            }

            /* Section Titles (e.g., "DRISHTI") */
            .title-text {
                font-size: 18px !important;
                font-weight: 600 !important;
            }

            /* Sub-section Titles (e.g., "ZONE SELECTION") */
            .filter-section-label {
                font-size: 16px;
                font-weight: 500;
            }

            /* Top Filters / Pills */
            .filter-tag {
                font-size: 13px;
                font-weight: 500;
            }
            .filter-tag-count, .filter-tag-pct {
                font-size: 12px;
                font-weight: 600;
            }

            /* Table Headers */
            .table th {
                font-size: 13px;
                font-weight: 500;
                letter-spacing: 0.25px;
            }

            /* Table Body */
            .table td {
                font-size: 14px; /* Base for table body */
                font-weight: 400; /* Regular weight */
            }
            .table .zone-total-row > td:nth-child(2),
            .table .region-detail-row > td:nth-child(2) {
                font-weight: 600; /* Semibold for Zone/Region names */
            }
            .table td:first-child {
                font-size: 12px; /* Row index */
            }
            .table .amount-cell {
                font-weight: 500; /* Medium for Target/Achievement */
            }
            .pct-value { /* Class to be added to percentage span */
                font-size: 14px;
                font-weight: 600; /* Semibold for percentage values */
            }

            /* Total Row */
            tfoot tr td {
                font-size: 14px;
                font-weight: 700; /* Bold for label */
            }
            tfoot tr td:not(:first-child) {
                font-size: 15px;
                font-weight: 600; /* Semibold for numbers */
            }

            /* Meta / Status Text */
            .table th.month-col {
                font-size: 14px;
                font-weight: 500; /* Medium */
            }
            .days-left-indicator {
                font-size: 12px;
                font-weight: 400; /* Regular */
            }

			.movement-popup .popup-main-container {
				max-height: 400px; /* Default max-height */
				overflow-y: auto;
			}

			@keyframes viewControlBlink {
				0%, 100% {
					box-shadow: 0 0 0 0 rgba(245, 158, 11, 0);
					background: transparent;
				}
				50% {
					box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.35);
					background: rgba(245, 158, 11, 0.12);
				}
			}

			.view-change-highlight {
				border-radius: 6px;
				animation: viewControlBlink 1s ease-in-out 4;
			}

			@keyframes quarterlyLinkBlink {
				0%, 100% {
					color: #b45309;
					background: rgba(245, 158, 11, 0.12);
					box-shadow: 0 0 0 0 rgba(245, 158, 11, 0);
					transform: scale(1);
				}
				50% {
					color: #92400e;
					background: rgba(245, 158, 11, 0.28);
					box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.2);
					transform: scale(1.04);
				}
			}

			.quarterly-view-link {
				color: #b45309;
				font-weight: 700;
				text-decoration: underline;
				text-underline-offset: 2px;
				padding: 2px 8px;
				border-radius: 4px;
				background: rgba(245, 158, 11, 0.12);
				animation: quarterlyLinkBlink 1s ease-in-out infinite;
			}

			.view-change-panel {
				position: relative;
				margin-top: 12px;
				padding: 14px;
				border: 1px solid rgba(245, 158, 11, 0.45);
				border-radius: 12px;
				background: linear-gradient(135deg, #fffaf0 0%, #ffefc7 100%);
				box-shadow:
					0 10px 24px rgba(15, 23, 42, 0.12),
					inset 0 1px 0 rgba(255, 255, 255, 0.7);
				overflow: hidden;
			}

			.view-change-panel::before {
				content: "";
				position: absolute;
				inset: 0;
				background:
					linear-gradient(90deg, rgba(255, 255, 255, 0.18) 0, rgba(255, 255, 255, 0) 35%),
					repeating-linear-gradient(
						135deg,
						rgba(180, 83, 9, 0.06) 0,
						rgba(180, 83, 9, 0.06) 10px,
						transparent 10px,
						transparent 20px
					);
				pointer-events: none;
			}

			.view-change-panel-title {
				position: relative;
				font-size: 11px;
				font-weight: 700;
				color: #92400e;
				margin-bottom: 10px;
				letter-spacing: 0.9px;
				text-transform: uppercase;
			}

			.view-change-panel-body {
				position: relative;
				display: flex;
				align-items: center;
				justify-content: space-between;
				gap: 14px;
				flex-wrap: wrap;
			}

			.view-change-panel-copy {
				min-width: 180px;
				flex: 1 1 220px;
			}

			.view-change-panel-headline {
				color: #7c2d12;
				font-size: 18px;
				font-weight: 800;
				line-height: 1.1;
				margin-bottom: 4px;
				text-shadow: 0 1px 0 rgba(255, 255, 255, 0.7);
			}

			.view-change-panel-subtext {
				color: #9a3412;
				font-size: 12px;
				font-weight: 600;
			}

			.view-change-options {
				position: relative;
				display: flex;
				gap: 8px;
				flex-wrap: wrap;
			}

			.view-change-option {
				display: inline-flex;
				align-items: center;
				justify-content: center;
				padding: 9px 14px;
				border-radius: 10px;
				border: 1px solid #cbd5e1;
				background: linear-gradient(180deg, #ffffff 0%, #edf2f7 100%);
				color: #1b263b;
				font-weight: 600;
				text-decoration: none;
				box-shadow:
					inset 0 1px 0 rgba(255, 255, 255, 0.8),
					0 4px 0 rgba(148, 163, 184, 0.45),
					0 8px 18px rgba(15, 23, 42, 0.12);
				transform: translateY(0);
				transition:
					transform 0.12s ease,
					box-shadow 0.12s ease,
					background 0.12s ease;
			}

			.view-change-option:hover {
				text-decoration: none;
				color: #0d1b2a;
				transform: translateY(-1px);
				box-shadow:
					inset 0 1px 0 rgba(255, 255, 255, 0.85),
					0 5px 0 rgba(148, 163, 184, 0.45),
					0 10px 20px rgba(15, 23, 42, 0.16);
			}

			.view-change-option.is-recommended {
				color: #7c2d12;
				border-color: rgba(245, 158, 11, 0.45);
				background: linear-gradient(180deg, #ffe6a7 0%, #fbbf24 100%);
				box-shadow:
					inset 0 1px 0 rgba(255, 255, 255, 0.65),
					0 5px 0 rgba(180, 83, 9, 0.45),
					0 10px 24px rgba(245, 158, 11, 0.24);
				animation: quarterlyLinkBlink 1s ease-in-out infinite;
			}

			/* Product Wise Table - Column Layout */
			.product-wise-table th {
				text-align: center;
				vertical-align: middle;
				background: #f8f9fa;
			}
			.product-wise-table td {
				text-align: right;
				vertical-align: middle;
			}
			.product-wise-table td:nth-child(2) {
				text-align: left !important;
			}
		`;
		$(`<style>${style}</style>`).appendTo("head");
	}

	getQuarterFromDate(dateStr) {
		const date = new Date(dateStr || frappe.datetime.get_today());
		const month = date.getMonth(); // 0-indexed
		if (month >= 3 && month <= 5) return 'Q1';
		if (month >= 6 && month <= 8) return 'Q2';
		if (month >= 9 && month <= 11) return 'Q3';
		return 'Q4';
	}

	getQuarterDate(quarter, fy) {
		if (!fy) return frappe.datetime.get_today();
		const startYear = fy.split("-")[0];
		const endYear = fy.split("-")[1] ? ("20" + fy.split("-")[1]).replace("2020", "20") : (parseInt(startYear) + 1).toString();
		const endYearFull = endYear.length === 2 ? "20" + endYear : endYear;
		switch (quarter) {
			case 'Q1': return `${startYear}-06-30`;
			case 'Q2': return `${startYear}-09-30`;
			case 'Q3': return `${startYear}-12-31`;
			case 'Q4': return `${endYearFull}-03-31`;
			default: return frappe.datetime.get_today();
		}
	}

	processNewApiResponse() {
		const data = this.data;

		// Extract months
		this.months = data.months.map((m) => ({
			key: m.key,
			display: m.display,
			date: m.date,
		}));

		if (this.state.viewType === "Quarterly") {
			const startYear = this.state.financialYear ? this.state.financialYear.split("-")[0] : new Date().getFullYear().toString();
			let endYear = this.state.financialYear ? this.state.financialYear.split("-")[1] : (parseInt(startYear) + 1).toString();
			if (endYear && endYear.length === 2) endYear = "20" + endYear;
			
			const qMap = {
				'Q1': [{key:'APR', display:`APR-${startYear.slice(-2)}`, date:`${startYear}-04-01`}, {key:'MAY', display:`MAY-${startYear.slice(-2)}`, date:`${startYear}-05-01`}, {key:'JUN', display:`JUN-${startYear.slice(-2)}`, date:`${startYear}-06-01`}],
				'Q2': [{key:'JUL', display:`JUL-${startYear.slice(-2)}`, date:`${startYear}-07-01`}, {key:'AUG', display:`AUG-${startYear.slice(-2)}`, date:`${startYear}-08-01`}, {key:'SEP', display:`SEP-${startYear.slice(-2)}`, date:`${startYear}-09-01`}],
				'Q3': [{key:'OCT', display:`OCT-${startYear.slice(-2)}`, date:`${startYear}-10-01`}, {key:'NOV', display:`NOV-${startYear.slice(-2)}`, date:`${startYear}-11-01`}, {key:'DEC', display:`DEC-${startYear.slice(-2)}`, date:`${startYear}-12-01`}],
				'Q4': [{key:'JAN', display:`JAN-${endYear.slice(-2)}`, date:`${endYear}-01-01`}, {key:'FEB', display:`FEB-${endYear.slice(-2)}`, date:`${endYear}-02-01`}, {key:'MAR', display:`MAR-${endYear.slice(-2)}`, date:`${endYear}-03-01`}]
			};
			const quarter = this.state.selectedQuarter || this.getQuarterFromDate(this.state.selectedDate || frappe.datetime.get_today());
			this.months = qMap[quarter] || this.months;
		}

		// Direct mapping
		this.zoneData = data.zone_wise;
		this.productData = data.product_wise || [];
		this.allProducts = data.all_products || [];
		this.categoryData = data.category_wise;
		this.branchData = data.branch_wise;
		this.agentData = data.agent_wise || [];

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
	// URL STATE MANAGEMENT
	// ========================================================================

	updateStateFromUrl() {
		const urlParams = new URLSearchParams(window.location.search);
		const queryParams = {};
		for (const [key, value] of urlParams.entries()) {
			queryParams[key] = value;
		}

		if (Object.keys(queryParams).length > 0) {
			this.state.financialYear = queryParams.financialYear || this.state.financialYear;
			this.state.activeTab = queryParams.activeTab || this.state.activeTab;
			this.state.viewType = queryParams.viewType || this.state.viewType;
			this.state.targetType = this.normalizeTargetType(
				queryParams.targetType || this.state.targetType,
			);
			this.state.formatMode = queryParams.formatMode || this.state.formatMode;
			this.state.selectedDate = queryParams.selectedDate || this.state.selectedDate;
			this.state.selectedRegion = queryParams.selectedRegion || this.state.selectedRegion;
			this.state.branchSearchTerm =
				queryParams.branchSearchTerm || this.state.branchSearchTerm;
			this.state.selectedMonth = queryParams.selectedMonth || this.state.selectedMonth;
			this.state.selectedSegment = queryParams.selectedSegment || this.state.selectedSegment;
			this.state.selectedQuarter = queryParams.selectedQuarter || this.state.selectedQuarter;

			if (queryParams.selectedCategories) {
				this.state.selectedCategories = queryParams.selectedCategories
					.split(",")
					.filter(Boolean);
			}
			if (queryParams.selectedZones) {
				this.state.selectedZones = queryParams.selectedZones.split(",").filter(Boolean);
			}
		}
	}

	updateUrlFromState() {
		const newUrl = new URL(window.location);
		const newSearchParams = new URLSearchParams();

		const stateToParams = {
			financialYear: this.state.financialYear,
			activeTab: this.state.activeTab,
			viewType: this.state.viewType,
			targetType: this.state.targetType,
			formatMode: this.state.formatMode,
			selectedDate: this.state.selectedDate,
			selectedQuarter: this.state.selectedQuarter,
			selectedRegion: this.state.selectedRegion,
			branchSearchTerm: this.state.branchSearchTerm,
			selectedMonth: this.state.selectedMonth,
			selectedSegment: this.state.selectedSegment,
		};

		// Add non-empty simple string/number parameters
		for (const key in stateToParams) {
			const value = stateToParams[key];
			if (value !== null && value !== undefined && value !== "" && value !== "all") {
				newSearchParams.set(key, value);
			}
		}

		// Handle array parameters
		if (this.state.selectedCategories.length > 0) {
			newSearchParams.set("selectedCategories", this.state.selectedCategories.join(","));
		}
		if (this.state.selectedZones.length > 0) {
			newSearchParams.set("selectedZones", this.state.selectedZones.join(","));
		}

		newUrl.search = newSearchParams.toString();
		history.pushState({}, "", newUrl.toString());
	}

	updateUiFromState() {
		// Update FY selector
		this.page.main.find("#fy-selector").val(this.state.financialYear);

		// Update View toggle
		this.page.main.find(".view-toggle-btn").removeClass("active");
		this.page.main
			.find(`.view-toggle-btn[data-view="${this.state.viewType}"]`)
			.addClass("active");

		// Update Quarter toggle
		if (this.state.viewType === "Quarterly") {
			this.page.main.find("#quarter-selector-container").show();
			this.page.main.find(".quarter-toggle-btn").removeClass("active");
			const activeQ = this.state.selectedQuarter || this.getQuarterFromDate(this.state.selectedDate || frappe.datetime.get_today());
			this.page.main.find(`.quarter-toggle-btn[data-quarter="${activeQ}"]`).addClass("active");
		} else {
			this.page.main.find("#quarter-selector-container").hide();
		}

		// Update Target toggle
		this.page.main.find(".target-toggle-btn").removeClass("active");
		this.page.main
			.find(`.target-toggle-btn[data-target="${this.state.targetType}"]`)
			.addClass("active");

		// Update Format toggle
		this.page.main.find(".format-toggle-btn").removeClass("active");
		this.page.main
			.find(`.format-toggle-btn[data-format="${this.state.formatMode}"]`)
			.addClass("active");

		// Update Date selector
		this.page.main.find("#date-selector").val(this.state.selectedDate);

		// Update Region selector
		this.page.main.find("#region-selector").val(this.state.selectedRegion);

		// Update Branch search
		this.page.main.find("#branch-search").val(this.state.branchSearchTerm);

		// Update Segment filter
		this.page.main.find("#segment-filter").val(this.state.selectedSegment);

		// Update tabs
		this.page.main.find(".tab-btn").removeClass("active");
		this.page.main.find(`.tab-btn[data-tab="${this.state.activeTab}"]`).addClass("active");

		// Update filter tags for zones and categories
		this.updateFilterTagsUI();
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
		this.updateUrlFromState();
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
            <div id="summary-cards-container" class="summary-cards-container">
                <div class="summary-card">
                    <div class="summary-info">
                        <span class="summary-label">Total Branches</span>
                        <span class="summary-value" id="summary-total-branches">229</span>
                        <span class="summary-subtext success" id="summary-branches-trend">+12% from last month</span>
                    </div>
                    <div class="summary-icon-box">
                        <i class="fa fa-building"></i>
                    </div>
                </div>
                <div class="summary-card">
                    <div class="summary-info">
                        <span class="summary-label">Target Amount</span>
                        <span class="summary-value" id="summary-target-amount">₹163.04 Cr</span>
                        <span class="summary-subtext muted" id="summary-target-label">Monthly target</span>
                    </div>
                    <div class="summary-icon-box">
                        <i class="fa fa-bullseye"></i>
                    </div>
                </div>
                <div class="summary-card">
                    <div class="summary-info">
                        <span class="summary-label">Achievement</span>
                        <span class="summary-value" id="summary-achievement-amount">₹91.45 Cr</span>
                        <span class="summary-subtext danger" id="summary-achievement-pct">57.9% achieved</span>
                    </div>
                    <div class="summary-icon-box">
                        <i class="fa fa-line-chart"></i>
                    </div>
                </div>
                <div class="summary-card">
                    <div class="summary-info">
                        <span class="summary-label">Active Zones</span>
                        <span class="summary-value" id="summary-active-zones">6 Zones</span>
                        <span class="summary-subtext success">All zones operational</span>
                    </div>
                    <div class="summary-icon-box">
                        <i class="fa fa-users"></i>
                    </div>
                </div>
            </div>
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
		return ((count / total) * 100).toFixed(2);
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
				self.updateUrlFromState();
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
				}

				self.updateFilterTagsUI();
				self.updateUrlFromState();
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
				this.state.selectedZones.includes(b.zone),
			);
		}

		// Apply region filter
		if (this.state.selectedRegion) {
			filteredBranches = filteredBranches.filter(
				(b) => b.region === this.state.selectedRegion,
			);
		}

		this.categoryCounts.all = filteredBranches.length;
		this.zoneCounts.all = filteredBranches.length;

		const firstMonth = this.months[0]?.key;
		if (firstMonth) {
			this.availableFilters.categories.forEach((catName) => {
				this.categoryCounts[catName] = filteredBranches.filter(
					(b) => b.months[firstMonth]?.category === catName,
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
                        </select>
                    </div>

                    <!-- View Toggle Buttons -->
                    <div style="display: flex; align-items: center;">
                        <label style="font-weight: bold; color: #0d1b2a;">View:</label>
                        <div class="btn-group" id="view-controls" role="group" style="margin-left: 8px;">
                            <button type="button" class="btn btn-sm view-toggle-btn" data-view="Monthly">Monthly</button>
                            <button type="button" class="btn btn-sm view-toggle-btn" data-view="Quarterly">Quarterly</button>
                            <button type="button" class="btn btn-sm view-toggle-btn" data-view="Yearly">Yearly</button>
                        </div>

                        <!-- Quarter Selector (hidden by default) -->
                        <div id="quarter-selector-container" style="display: none; margin-left: 10px;">
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-sm quarter-toggle-btn" data-quarter="Q1">Q1</button>
                                <button type="button" class="btn btn-sm quarter-toggle-btn" data-quarter="Q2">Q2</button>
                                <button type="button" class="btn btn-sm quarter-toggle-btn" data-quarter="Q3">Q3</button>
                                <button type="button" class="btn btn-sm quarter-toggle-btn" data-quarter="Q4">Q4</button>
                            </div>
                        </div>
                    </div>

                    <!-- Target Toggle Buttons -->
                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">Target:</label>
                        <div class="btn-group" role="group" style="margin-left: 8px;">
                            <button type="button" class="btn btn-sm target-toggle-btn" data-target="Monthly">Monthly</button>
                            <button type="button" class="btn btn-sm target-toggle-btn" data-target="YTD">YTD</button>
                            <button type="button" class="btn btn-sm target-toggle-btn" data-target="Yearly">Yearly</button>
                        </div>
                    </div>

                    <!-- Date Selector -->
                    <div id="date-selector-container">
                        <label style="font-weight: bold; color: #0d1b2a;">Date:</label>
                        <input type="date" id="date-selector" style="padding: 6px 12px; border: 1px solid #778da9; border-radius: 4px; margin-left: 8px; background: white; color: #1b263b;" />
                    </div>

                    <!-- Format Toggle Buttons -->
                    <div>
                        <label style="font-weight: bold; color: #0d1b2a;">Format:</label>
                        <div class="btn-group" role="group" style="margin-left: 8px;">
                            <button type="button" class="btn btn-sm format-toggle-btn" data-format="number">Numbers</button>
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
                    <button class="tab-btn" data-tab="zone">
                        Zone Wise
                    </button>
                    <button class="tab-btn" data-tab="category">
                        Category Wise
                    </button>
                    <button class="tab-btn" data-tab="product">
                        Product Wise
                    </button>	
                    <button class="tab-btn" data-tab="agent">
                        Agent Wise
                    </button>									
                    <button class="tab-btn" data-tab="branch">
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
                        <button id="clear-filters" class="btn btn-secondary btn-sm" 
                                style="background: #417d81; border-color: #1b263b; color: white; font-weight: 600;"
                                title="Resets all filters to their default state and refreshes the dashboard.">
                            🔄 Reset & Refresh
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
				self.updateUrlFromState();
				self.loadData();
				if (self.state.branchSearchTerm) {
					self.switchTab("branch");
				}
			}, 500);
		});

		// Financial Year
		this.page.main.find("#fy-selector").on("change", function () {
			self.state.financialYear = $(this).val();
			self.applyPreviousFinancialYearDefaultDate();
			self.updateUrlFromState();
			self.loadData();
		});

		// View Toggle Buttons
		this.page.main.find(".view-toggle-btn").on("click", function () {
			self.page.main.find(".view-toggle-btn").removeClass("active");
			$(this).addClass("active");
			self.clearViewControlsHighlight();
			self.state.viewType = $(this).data("view");
			self.applyPreviousFinancialYearDefaultDate();
			self.updateUrlFromState();
			self.updateUiFromState();
			self.loadData();
		});

		this.page.main.find("#error-message").on("click", ".view-change-option-link", function (e) {
			e.preventDefault();
			const view = $(this).data("view");
			self.page.main.find(`.view-toggle-btn[data-view="${view}"]`).trigger("click");
		});

		// Quarter Toggle Buttons
		this.page.main.find(".quarter-toggle-btn").on("click", function () {
			self.state.selectedQuarter = $(this).data("quarter");
			self.state.selectedDate = self.getQuarterDate(self.state.selectedQuarter, self.state.financialYear);
			self.updateUrlFromState();
			self.updateUiFromState();
			self.loadData();
		});

		// Target Toggle Buttons
		this.page.main.find(".target-toggle-btn").on("click", function () {
			self.page.main.find(".target-toggle-btn").removeClass("active");
			$(this).addClass("active");
			self.state.targetType = self.normalizeTargetType($(this).data("target"));
			self.updateUrlFromState();
			self.loadData();
		});

		// Date Selector
		this.page.main.find("#date-selector").on("change", function () {
			const newDate = $(this).val();
			self.state.selectedDate = newDate;
			// Save date for current tab
			if (self.state.activeTab && self.tabDates.hasOwnProperty(self.state.activeTab)) {
				self.tabDates[self.state.activeTab] = newDate;
			}
			self.updateUrlFromState();
			self.loadData();
		});

		// Format Toggle
		this.page.main.find(".format-toggle-btn").on("click", function () {
			self.page.main.find(".format-toggle-btn").removeClass("active");
			$(this).addClass("active");
			self.state.formatMode = $(this).data("format");
			self.updateUrlFromState();
			self.render();
		});

		// Region Filter
		this.page.main.find("#region-selector").on("change", function () {
			self.state.selectedRegion = $(this).val() || "";
			self.updateUrlFromState();
			self.loadData();
		});

		// Clear Filters
		this.page.main.find("#clear-filters").on("click", function () {
			history.pushState({}, "", window.location.pathname);
			location.reload(true);
		});

		// Segment Filter
		this.page.main.find("#segment-filter").on("change", function () {
			self.state.selectedSegment = $(this).val();
			self.updateUrlFromState();
			self.render();
		});
	}

	switchTab(tabId) {
		// Save current tab's date before switching
		if (this.state.activeTab && this.tabDates.hasOwnProperty(this.state.activeTab)) {
			this.tabDates[this.state.activeTab] = this.state.selectedDate;
		}

		this.state.activeTab = tabId;

		// Update tab button UI immediately to show the tab as active
		this.page.main.find(".tab-btn").removeClass("active");
		this.page.main.find(`.tab-btn[data-tab="${tabId}"]`).addClass("active");

		// Restore the target tab's previously selected date
		const savedDate = this.tabDates[tabId] || null;

		// SPECIAL CASE: For Agent and Product Wise tabs, default to LATEST AVAILABLE DATE
		if (tabId === "agent" || tabId === "product") {
			const self = this;
			const method = tabId === "agent" 
				? "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_latest_agent_report_date"
				: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_latest_product_report_date";

			frappe.call({
				method: method,
				callback: (r) => {
					let dateStr = r.message;
					if (!dateStr) {
						// Fallback to yesterday if no data exists
						const d = new Date();
						d.setDate(d.getDate() - 1);
						dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
					}

					// Use saved date if available, otherwise use latest date from server
					self.state.selectedDate = savedDate || dateStr;

					// Update date control properly
					if (self.dateControl) {
						self.isRefreshingDate = true;
						self.dateControl.set_value(self.state.selectedDate);
						self.isRefreshingDate = false;
					}

					self.updateUiFromState();
					self.updateUrlFromState();
					self.loadData();
				},
			});
			return;
		}

		// For other tabs, restore saved date or use today's date for data loading
		if (savedDate) {
			this.state.selectedDate = savedDate;
			if (this.dateControl) {
				this.isRefreshingDate = true;
				this.dateControl.set_value(savedDate);
				this.isRefreshingDate = false;
			}
			// Load data with restored date
			this.loadData();
		} else {
			// Clear date selector (show blank DD/MM/YY) but use today's date for API
			this.state.selectedDate = null;
			if (this.dateControl) {
				this.isRefreshingDate = true;
				this.dateControl.set_value(null);
				this.isRefreshingDate = false;
			}
			// Load data with today's date (default) - but don't show it in selector
			this.loadDataWithDate(frappe.datetime.get_today());
		}

		this.updateUiFromState();
		this.updateUrlFromState();
		// Don't call render() here - loadData() callback will call it
	}

	// Helper to load data with a specific date (for internal use)
	loadDataWithDate(dateStr) {
		const self = this;
		const apiDate =
			dateStr ||
			this.state.selectedDate ||
			this.getPreviousFinancialYearDefaultDate() ||
			frappe.datetime.get_today();

		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_sahayog_dashboard",
			args: {
				financial_year: this.state.financialYear,
				view: this.getDashboardViewForRequest(),
				target_type: this.normalizeTargetType(this.state.targetType),
				filters: JSON.stringify({
					zones: [],
				}),
				selected_date: apiDate,
			},
			callback: (r) => {
				if (r.message) {
					self.normalizeDashboardResponse(r.message);
					self.data = r.message;
					self.permissions = r.message.permissions;

					// Check if data is empty (all zeros) - if so, try to get latest available date
					if (self.branchData && self.branchData.length > 0) {
						const firstBranch = self.branchData[0];
						const firstMonthKey = self.months?.[0]?.key;
						const monthData = firstBranch.months?.[firstMonthKey];
						
						if (monthData && monthData.target === 0 && monthData.achievement === 0) {
							self.loadLatestAvailableDate();
							return;
						}
					}

					if (self.permissions && self.permissions.has_access === false) {
						self.page.main.html(`
							<div style="text-align: center; padding: 100px 20px;">
								<div style="font-size: 60px; margin-bottom: 20px;">🚫</div>
								<h2 style="color: #d32f2f;">Access Denied</h2>
								<p style="font-size: 16px; color: #666;">
									You do not have a <b>Report Preference</b> set up. <br>
									Please contact your administrator to grant access.
								</p>
							</div>
						`);
						return;
					}

					self.processNewApiResponse();
					self.updateFilterCounts();
					self.render();
				}
			},
			error: (err) => {
				self.isLoadingData = false;
				console.error("Error loading dashboard data:", err);
				self.showError("Failed to load data. Please refresh the page.");
			}
		});
	}

	// Load latest available date from backend
	loadLatestAvailableDate() {
		const self = this;
		
		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_latest_agent_report_date",
			callback: (r) => {
				let dateStr = r.message;
				if (!dateStr) {
					// Fallback to yesterday if no data exists
					const d = new Date();
					d.setDate(d.getDate() - 1);
					dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
				}
				
				// Update state and UI
				self.state.selectedDate = dateStr;
				self.tabDates[self.state.activeTab] = dateStr;
				
				if (self.dateControl) {
					self.isRefreshingDate = true;
					self.dateControl.set_value(dateStr);
					self.isRefreshingDate = false;
				}
				
				// Reload data with latest date
				self.loadData();
			}
		});
	}

	// ========================================================================
	// DATA LOADING
	// ========================================================================
	loadData() {
		const self = this;

		// Use state.selectedDate for API call (this is what the date selector shows)
		// Fallback to today's date if no date selected
		const apiDate =
			this.state.selectedDate ||
			this.getPreviousFinancialYearDefaultDate() ||
			frappe.datetime.get_today();

		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_sahayog_dashboard",
			args: {
				financial_year: this.state.financialYear,
				view: this.getDashboardViewForRequest(),
				target_type: this.normalizeTargetType(this.state.targetType),
				filters: JSON.stringify({
					zones: [],
				}),
				selected_date: apiDate,
			},
			callback: (r) => {
				if (r.message) {
					self.normalizeDashboardResponse(r.message);
					self.data = r.message;
					self.permissions = r.message.permissions;
					console.log("🛡️ Sahayog Dashboard Permissions:", self.permissions);
					console.log(`[loadData callback] Data received. branchData length: ${self.branchData?.length || 0}`);

					if (self.permissions && self.permissions.has_access === false) {
						self.page.main.html(`
							<div style="text-align: center; padding: 100px 20px;">
								<div style="font-size: 60px; margin-bottom: 20px;">🚫</div>
								<h2 style="color: #d32f2f;">Access Denied</h2>
								<p style="font-size: 16px; color: #666;">
									You do not have a <b>Report Preference</b> set up. <br>
									Please contact your administrator to grant access.
								</p>
							</div>
						`);
						return;
					}

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

	showQuarterlyViewSuggestion() {
		this.stopQuarterlyPromptBlink();
		this.page.main
			.find("#error-message")
			.html(
				`<div style="position: relative; overflow: hidden; margin-top: 8px; padding: 16px; border: 1px solid rgba(245, 158, 11, 0.45); border-radius: 14px; background: linear-gradient(135deg, #fffaf0 0%, #ffefc7 100%); box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12), inset 0 1px 0 rgba(255,255,255,0.75);">
					<div style="position: absolute; inset: 0; background: linear-gradient(90deg, rgba(255,255,255,0.18) 0, rgba(255,255,255,0) 35%), repeating-linear-gradient(135deg, rgba(180, 83, 9, 0.06) 0, rgba(180, 83, 9, 0.06) 10px, transparent 10px, transparent 20px); pointer-events: none;"></div>
					<div style="position: relative; display: flex; align-items: flex-start; gap: 12px; flex-wrap: wrap;">
						<div style="width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; background: linear-gradient(180deg, #fbbf24 0%, #f59e0b 100%); color: #7c2d12; font-size: 20px; font-weight: 700; box-shadow: inset 0 1px 0 rgba(255,255,255,0.55), 0 6px 14px rgba(245, 158, 11, 0.25);">!</div>
						<div style="flex: 1 1 320px; min-width: 240px;">
							<div style="font-size: 11px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #92400e; margin-bottom: 6px;">Suggested Action</div>
							<div style="font-size: 22px; line-height: 1.1; font-weight: 800; color: #7c2d12; margin-bottom: 6px;">Switch View Mode</div>
							<div style="font-size: 13px; line-height: 1.5; color: #9a3412; margin-bottom: 12px;">
								No data is currently available for this month in the system. Change the View to continue, for example
								<a href="#" class="quarterly-view-link view-change-option-link" data-view="Quarterly" style="display: inline-block; margin-left: 4px; color: #7c2d12; font-weight: 800; text-decoration: underline; text-underline-offset: 2px; padding: 3px 10px; border-radius: 999px; background: rgba(245, 158, 11, 0.18); border: 1px solid rgba(245, 158, 11, 0.35); box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.10);">Quarterly</a>.
							</div>
							<div style="display: flex; gap: 10px; flex-wrap: wrap;">
								<a href="#" class="view-change-option view-change-option-link" data-view="Monthly" style="display: inline-flex; align-items: center; justify-content: center; min-width: 104px; padding: 10px 14px; border-radius: 10px; border: 1px solid #cbd5e1; background: linear-gradient(180deg, #ffffff 0%, #edf2f7 100%); color: #1b263b; font-weight: 700; text-decoration: none; box-shadow: inset 0 1px 0 rgba(255,255,255,0.85), 0 4px 0 rgba(148,163,184,0.45), 0 8px 18px rgba(15,23,42,0.12);">Monthly</a>
								<a href="#" class="view-change-option view-change-option-link is-recommended" data-view="Quarterly" style="display: inline-flex; align-items: center; justify-content: center; min-width: 104px; padding: 10px 14px; border-radius: 10px; border: 1px solid rgba(245, 158, 11, 0.45); background: linear-gradient(180deg, #ffe6a7 0%, #fbbf24 100%); color: #7c2d12; font-weight: 800; text-decoration: none; box-shadow: inset 0 1px 0 rgba(255,255,255,0.7), 0 5px 0 rgba(180,83,9,0.45), 0 10px 24px rgba(245,158,11,0.24); animation: quarterlyLinkBlink 1s ease-in-out infinite;">Quarterly</a>
								<a href="#" class="view-change-option view-change-option-link" data-view="Yearly" style="display: inline-flex; align-items: center; justify-content: center; min-width: 104px; padding: 10px 14px; border-radius: 10px; border: 1px solid #cbd5e1; background: linear-gradient(180deg, #ffffff 0%, #edf2f7 100%); color: #1b263b; font-weight: 700; text-decoration: none; box-shadow: inset 0 1px 0 rgba(255,255,255,0.85), 0 4px 0 rgba(148,163,184,0.45), 0 8px 18px rgba(15,23,42,0.12);">Yearly</a>
							</div>
						</div>
					</div>
				</div>`
			)
			.show();
		this.page.main.find("#data-container").css("opacity", 0);
		this.startQuarterlyPromptBlink();
	}

	startQuarterlyPromptBlink() {
		this.stopQuarterlyPromptBlink();
		const button = this.page.main.find(
			'#error-message .view-change-option-link.is-recommended[data-view="Quarterly"]',
		);
		if (!button.length) return;

		let isDimmed = false;
		this.quarterlyPromptBlinkInterval = setInterval(() => {
			isDimmed = !isDimmed;
			button.css({
				opacity: isDimmed ? "0.65" : "1",
				transform: isDimmed ? "scale(0.98)" : "scale(1.05)",
				boxShadow: isDimmed
					? "inset 0 1px 0 rgba(255,255,255,0.7), 0 3px 0 rgba(180,83,9,0.35), 0 6px 14px rgba(245,158,11,0.18)"
					: "inset 0 1px 0 rgba(255,255,255,0.7), 0 6px 0 rgba(180,83,9,0.5), 0 12px 28px rgba(245,158,11,0.3)",
			});
		}, 450);
	}

	stopQuarterlyPromptBlink() {
		if (this.quarterlyPromptBlinkInterval) {
			clearInterval(this.quarterlyPromptBlinkInterval);
			this.quarterlyPromptBlinkInterval = null;
		}
	}

	highlightViewControls() {
		const viewControls = this.page.main.find("#view-controls");
		viewControls.removeClass("view-change-highlight");
		void viewControls[0]?.offsetWidth;
		viewControls.addClass("view-change-highlight");
	}

	clearViewControlsHighlight() {
		this.page.main.find("#view-controls").removeClass("view-change-highlight");
		this.stopQuarterlyPromptBlink();
	}

	getLocationIdentifier(value) {
		const text = cstr(value || "").trim();
		const numericMatch = text.match(/\d+/);
		return numericMatch ? numericMatch[0] : text.toLowerCase();
	}

	// ========================================================================
	// DATA FILTERING AND AGGREGATION UTILITIES
	// ========================================================================

	getFilteredBranches() {
		let filtered = this.branchData ? [...this.branchData] : [];

		const filterMonthKey =
			this.state.selectedMonth ||
			(this.months && this.months.length > 0 ? this.months[0].key : null);

		// 1. Category filter (applied for the selected/latest month)
		if (this.state.selectedCategories.length > 0 && filterMonthKey) {
			filtered = filtered.filter((branch) => {
				const monthData = branch.months[filterMonthKey];
				return monthData && this.state.selectedCategories.includes(monthData.category);
			});
		}

		// 2. Zone filter
		if (this.state.selectedZones.length > 0) {
			filtered = filtered.filter((branch) =>
				this.state.selectedZones.some(
					(zone) => this.getLocationIdentifier(zone) === this.getLocationIdentifier(branch.zone),
				),
			);
		}

		// 3. Region filter
		if (this.state.selectedRegion) {
			filtered = filtered.filter(
				(branch) =>
					this.getLocationIdentifier(branch.region) ===
					this.getLocationIdentifier(this.state.selectedRegion),
			);
		}

		// 4. Branch search term filter
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

	reaggregateZoneData(branches) {
		if (!branches || !this.months || this.months.length === 0) return [];

		const aggregatedMap = new Map(); // Key: zoneName or regionName, Value: aggregated object

		// Group branches into top-level zones and regions
		const groupedData = {}; // { "ZONE-1": { totalBranches: [], regionBranches: { "REGION-A": [] } } }

		branches.forEach((branch) => {
			const zoneName = branch.zone;
			const regionName = branch.region;

			if (!groupedData[zoneName]) {
				groupedData[zoneName] = { totalBranches: [], regionBranches: {} };
			}

			// Add to total zone branches
			groupedData[zoneName].totalBranches.push(branch);

			// Add to region branches if it's a specific region
			if (regionName && regionName !== zoneName) {
				if (!groupedData[zoneName].regionBranches[regionName]) {
					groupedData[zoneName].regionBranches[regionName] = [];
				}
				groupedData[zoneName].regionBranches[regionName].push(branch);
			}
		});

		const result = [];
		const sortedZoneNames = Object.keys(groupedData).sort((a, b) => {
			const aNum = a.match(/ZONE-(\d+)/)?.[1];
			const bNum = b.match(/ZONE-(\d+)/)?.[1];
			return aNum && bNum ? parseInt(aNum) - parseInt(bNum) : a.localeCompare(b);
		});

		sortedZoneNames.forEach((zoneName) => {
			const zoneGroup = groupedData[zoneName];

			// Aggregate for the top-level zone
			const zoneAgg = {
				zone: zoneName,
				region: zoneName,
				months: Object.fromEntries(
					this.months.map((m) => [
						m.key,
						{ target: 0, achievement: 0, percentage: 0, branches: 0 },
					]),
				),
				isZoneTotal: true,
			};
			
			zoneGroup.totalBranches.forEach((branch) => {
				this.months.forEach((m) => {
					const monthData = branch.months[m.key];
					if (monthData) {
						zoneAgg.months[m.key].target += monthData.target || 0;
						zoneAgg.months[m.key].achievement += monthData.achievement || 0;
					}
				});
			});
			zoneAgg.months[this.months[0].key].branches = zoneGroup.totalBranches.length; // Count branches for the first month
			this.months.forEach((m) => {
				const monthAgg = zoneAgg.months[m.key];
				monthAgg.percentage =
					monthAgg.target > 0 ? (monthAgg.achievement / monthAgg.target) * 100 : 0;
			});
			result.push(zoneAgg);

			// Aggregate for regions within this zone
			const sortedRegionNames = Object.keys(zoneGroup.regionBranches).sort();
			sortedRegionNames.forEach((regionName) => {
				const regionBranches = zoneGroup.regionBranches[regionName];
				const regionAgg = {
					zone: zoneName,
					region: regionName,
					months: Object.fromEntries(
						this.months.map((m) => [
							m.key,
							{ target: 0, achievement: 0, percentage: 0, branches: 0 },
						]),
					),
					isZoneTotal: false,
				};
				regionBranches.forEach((branch) => {
					this.months.forEach((m) => {
						const monthData = branch.months[m.key];
						if (monthData) {
							regionAgg.months[m.key].target += monthData.target || 0;
							regionAgg.months[m.key].achievement += monthData.achievement || 0;
						}
					});
				});
				regionAgg.months[this.months[0].key].branches = regionBranches.length; // Count branches for the first month
				this.months.forEach((m) => {
					const monthAgg = regionAgg.months[m.key];
					monthAgg.percentage =
						monthAgg.target > 0 ? (monthAgg.achievement / monthAgg.target) * 100 : 0;
				});
				result.push(regionAgg);
			});
		});

		return result;
	}

	reaggregateCategoryData(branches) {
		if (!branches || !this.months || this.months.length === 0) return [];

		const latestMonthKey = this.months[0].key;
		const aggregatedCategories = {};

		this.availableFilters.categories.forEach((cat) => {
			aggregatedCategories[cat] = {
				category: cat,
				months: {
					[latestMonthKey]: {
						count: 0,
						changes: { increased: [], decreased: [] }, // No previous day data for reaggregation
						zone_breakdown: {},
					},
				},
			};
		});

		branches.forEach((branch) => {
			const monthData = branch.months[latestMonthKey];
			if (monthData && aggregatedCategories[monthData.category]) {
				const catAgg = aggregatedCategories[monthData.category].months[latestMonthKey];
				catAgg.count += 1;
				catAgg.zone_breakdown[branch.zone] = (catAgg.zone_breakdown[branch.zone] || 0) + 1;
			}
		});

		return Object.values(aggregatedCategories);
	}

	filterMovementData(changes) {
		if (!changes) return { increased: [], decreased: [] };

		let { increased, decreased } = changes;

		// Get a set of branch names that are in the current filtered view
		const filteredBranches = this.getFilteredBranches();
		const filteredBranchNames = new Set(filteredBranches.map((b) => b.branch));

		// Filter the increased and decreased arrays
		increased = increased.filter((item) => filteredBranchNames.has(item.branch));
		decreased = decreased.filter((item) => filteredBranchNames.has(item.branch));

		return { increased, decreased };
	}

	// ========================================================================
	// RENDERING - Main Render Function
	// ========================================================================
	render() {
		if (!this.data) {
			this.clearViewControlsHighlight();
			this.showError("No data available");
			return;
		}

		this.clearViewControlsHighlight();
		this.page.main.find("#error-message").hide();
		const dataContainer = this.page.main.find("#data-container");

		dataContainer.css("opacity", 0);

		const filteredBranches = this.getFilteredBranches();

		const reaggregatedZoneData = this.reaggregateZoneData(filteredBranches);
		const reaggregatedCategoryData = this.reaggregateCategoryData(filteredBranches);

		if (!this.months || this.months.length === 0) {
			this.page.main.find("#summary-cards-container").hide();
			this.highlightViewControls();
			this.showQuarterlyViewSuggestion();
			return;
		}

		this.page.main.find("#summary-cards-container").show();
		this.updateSummaryCards(filteredBranches, reaggregatedZoneData);

		setTimeout(() => {
			let htmlContent = "";

			if (this.state.activeTab === "zone") {
				htmlContent = this.renderZoneTable(reaggregatedZoneData);
			} else if (this.state.activeTab === "category") {
				htmlContent = this.renderCategoryTable(reaggregatedCategoryData);
			} else if (this.state.activeTab === "product") {
				htmlContent = this.renderProductTable(this.productData);
			} else if (this.state.activeTab === "agent") {
				htmlContent = this.renderAgentWiseTable(this.agentData);
			} else if (this.state.activeTab === "branch") {
				htmlContent = this.buildBranchTable(filteredBranches, this.months);
			}

			dataContainer.html(htmlContent);

			// Attach handlers after rendering

			if (this.state.activeTab === "zone") {
				this.attachZoneExpandHandlers();
				this.attachZoneDrilldownHandlers();
			} else if (this.state.activeTab === "product") {
				this.attachProductExpandHandlers();
				this.attachProductDrilldownHandlers();
			} else if (this.state.activeTab === "category") {
				this.attachMovementPopupHandlers();
				this.attachCategoryExpandHandlers();
				this.attachDrillHandlers();
				this.attachZoneDrillHandlers();
				this.attachTotalMovementPopupHandler();
			} else if (this.state.activeTab === "agent") {
				this.attachAgentExpandHandlers();
			}

			dataContainer.css("opacity", 1);
		}, 200);
	}

	// ========================================================================

	// ZONE WISE VIEW - Expandable/Collapsible

	// ========================================================================

	renderZoneTable(zoneData) {
		const months = this.months;

		let html = `
			    <table class="table table-bordered zone-wise-table">
			        <thead>
			            <tr class="zone-table-header">
			                <th rowspan="2">Sr</th>
			                <th rowspan="2">Zone/Region</th>
			                <th rowspan="2">Branches</th>
			    `;

		const today = new Date();
		const currentMonth = today.getMonth();
		const currentYear = today.getFullYear();

		months.forEach((month) => {
			const monthDate = new Date(month.date);
			const monthIndex = monthDate.getMonth();
			const monthYear = monthDate.getFullYear();

			const monthName = month.display.split("-")[0];
			const displayYear = `${monthName}-${monthYear}`;

			let daysLeftIndicator = "";
			if (monthIndex === currentMonth && monthYear === currentYear) {
				const lastDayOfMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
				const currentDay = today.getDate();
				const remainingDays = lastDayOfMonth - currentDay + 1;

				if (remainingDays >= 0) {
					daysLeftIndicator = `
						<br>
						<span class="days-left-indicator">
							${remainingDays} Day${remainingDays !== 1 ? "s" : ""} Left
						</span>
					`;
				}
			}

			html += `<th colspan="3">${displayYear}${daysLeftIndicator}</th>`;
		});

		html += '</tr><tr class="zone-table-subheader">';

		months.forEach(() => {
			html += "<th>Target</th><th>Ach</th><th>%</th>";
		});

		html += "</tr></thead><tbody>";

		const styleId = "days-left-indicator-style";
		if (!document.getElementById(styleId)) {
			const style = document.createElement("style");
			style.id = styleId;
			style.innerHTML = `
                @keyframes smooth-blink {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.3; }
                }
                .days-left-indicator {
                    color: red;
                    font-weight: bold;
                    animation: smooth-blink 1.5s infinite;
                    font-size: 12px;
                }
            `;
			document.head.appendChild(style);
		}

		const grandTotals = {
			branches: 0,
		};
		months.forEach((month) => {
			grandTotals[month.key] = { target: 0, achievement: 0 };
		});

		// Accumulate grand totals only from zone total items (isZoneTotal === true)
		zoneData.forEach((item) => {
			if (item.isZoneTotal) {
				// Only sum from the main zone aggregates to avoid double-counting regions
				const firstMonthData = item.months[months[0].key];
				grandTotals.branches += firstMonthData?.branches || 0;

				months.forEach((month) => {
					const mdata = item.months[month.key];
					if (mdata) {
						grandTotals[month.key].target += mdata.target || 0;
						grandTotals[month.key].achievement += mdata.achievement || 0;
					}
				});
			}
		});

		// Group data by zone from the reaggregated data
		const zoneGroups = {};

		zoneData.forEach((item) => {
			const isZoneTotal = item.isZoneTotal; // Use the flag from reaggregated data

			if (isZoneTotal) {
				if (!zoneGroups[item.zone]) {
					zoneGroups[item.zone] = { total: item, regions: [] };
				} else {
					zoneGroups[item.zone].total = item;
				}
			} else {
				if (!zoneGroups[item.zone]) {
					// Ensure a total object exists for zones that only have regions in the filtered data
					zoneGroups[item.zone] = { total: null, regions: [] };
				}
				zoneGroups[item.zone].regions.push(item);
			}
		});

		let sr = 1;

		// Sort by zone name then regions
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

		html += "</tbody>";

		// Grand Total Row
		html += `<tfoot style="background-color: #264a4d; color: #ffffff; font-weight: bold; border-top: 2px solid #3d7579;">`;
		html += `<tr style="height: 40px;">`;
		html += `<td colspan="2" style="text-align: left; padding-left: 12px; text-transform: uppercase; letter-spacing: 1px;">TOTAL</td>`;
		html += `<td style="text-align: center;">${grandTotals.branches}</td>`;

		months.forEach((month) => {
			const totalTarget = grandTotals[month.key].target;
			const totalAchievement = grandTotals[month.key].achievement;
			const overallPercentage = totalTarget > 0 ? (totalAchievement / totalTarget) * 100 : 0;

			html += `
                <td>${this.formatNumber(totalTarget)}</td>
                <td>${this.formatNumber(totalAchievement)}</td>
                <td>
					<div style="display: flex; align-items: center; gap: 8px; justify-content: center;">
						<span class="pct-value" style="min-width: 45px; text-align: right;">${overallPercentage.toFixed(2)}%</span>
						${this.renderProgressBar(overallPercentage)}
					</div>
				</td>
            `;
		});
		html += `</tr></tfoot>`;

		html += "</table>";

		return html;
	}

	buildZoneRow(zoneItem, sr, isZoneTotal, zoneName, isExpanded) {
		const months = this.months;

		const firstMonthData = zoneItem.months[months[0].key];

		const branchCount = firstMonthData?.branches || 0;

		let html = `<tr class="zone-total-row" data-zone="${zoneName}" style="background-color: #e0e1dd; font-weight: bold; cursor: pointer;">`;

		html += `<td>${sr}</td>`;

		html += `<td><span class="zone-toggle">${isExpanded ? "▼" : "▶"}</span> ${zoneName}</td>`;

		html += `<td class="branch-drilldown" data-zone="${zoneName}" title="Click to view branches in ${zoneName}">${branchCount}</td>`;

		months.forEach((month) => {
			const mdata = zoneItem.months[month.key];

			if (mdata) {
				html += `
			                <td>${this.formatNumber(mdata.target)}</td>
			                <td>${this.formatNumber(mdata.achievement)}</td>
			                <td>
								<div style="display: flex; align-items: center; gap: 8px; justify-content: center;">
									<span class="pct-value" style="color: ${this.getPctColor(
										mdata.percentage,
									)}; min-width: 45px; text-align: right;">${mdata.percentage?.toFixed(2)}%</span>
									${this.renderProgressBar(mdata.percentage)}
								</div>
							</td>
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
		}; border-left: 4px solid #417d81;">`;

		html += `<td>${sr}</td>`;

		html += `<td style="padding-left: 30px;">${regionItem.region}</td>`;

		html += `<td class="branch-drilldown" data-zone="${zoneName}" data-region="${regionItem.region}" title="Click to view branches in ${regionItem.region}">${branchCount}</td>`;

		months.forEach((month) => {
			const mdata = regionItem.months[month.key];

			if (mdata) {
				html += `
			                <td>${this.formatNumber(mdata.target)}</td>
			                <td>${this.formatNumber(mdata.achievement)}</td>
			                <td>
								<div style="display: flex; align-items: center; gap: 8px; justify-content: center;">
									<span class="pct-value" style="color: ${this.getPctColor(
										mdata.percentage,
									)}; min-width: 45px; text-align: right;">${mdata.percentage?.toFixed(2)}%</span>
									${this.renderProgressBar(mdata.percentage)}
								</div>
							</td>
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
	// PRODUCT WISE VIEW - Zone/Region Summary
	// ========================================================================

	renderProductTable(productData) {
		if (!productData || productData.length === 0) {
			return `
				<div style="text-align: center; padding: 50px; color: #778da9; font-size: 16px;">
					<div style="font-size: 48px; margin-bottom: 15px;">📭</div>
					<div style="font-weight: 600; margin-bottom: 8px;">No product data available</div>
				</div>
			`;
		}

		const allProducts = this.allProducts;

		// Build dynamic header with product columns
		let headerHtml = `
			<table class="table table-bordered product-wise-table">
				<thead>
					<tr class="zone-table-header">
						<th rowspan="2" style="width:60px;">SR</th>
						<th rowspan="2">ZONE/REGION</th>
		`;

		allProducts.forEach((product) => {
			headerHtml += `<th>${product}</th>`;
		});

		headerHtml += `
						<th rowspan="2" style="width:140px;">ACHIEVEMENT</th>
					</tr>
				</thead>
				<tbody>
		`;

		let html = headerHtml;

		let sr = 1;
		let zoneTotalAmount = 0;
		let zoneTotalCount = 0;
		let productTotals = {};

		// Initialize product totals
		allProducts.forEach((product) => {
			productTotals[product] = 0;
		});

		productData.forEach((item) => {
			if (item.is_group) {
				const isExpanded = this.state.expandedZones[item.name] || false;
				const products = item.products || {};

				html += `
					<tr class="zone-total-row product-total-row" data-zone="${item.name}" style="background-color: #e0e1dd; font-weight: bold; cursor: pointer;">
						<td>${sr++}</td>
						<td>
							<span class="product-toggle">${isExpanded ? "▼" : "▶"}</span>
							<strong>${item.name}</strong>
						</td>
				`;

				// Add a column for each product (zone totals) and accumulate totals
				allProducts.forEach((product) => {
					const amount = products[product] || 0;
					productTotals[product] += amount;
					html += `<td>${this.formatCurrency(amount)}</td>`;
				});

				html += `
						<td>${this.formatCurrency(item.amount)}</td>
					</tr>
				`;

				zoneTotalAmount += item.amount;
				zoneTotalCount += item.count;
			} else {
				const isExpanded = this.state.expandedZones[item.parent] || false;
				const products = item.products || {};

				html += `
					<tr class="region-detail-row product-detail-row" data-parent-zone="${item.parent}" data-region="${item.name}" style="display: ${isExpanded ? "table-row" : "none"}; cursor: pointer; background: #ffffff; border-left: 4px solid #417d81;">
						<td></td>
						<td style="padding-left: 40px; color: #097c80; font-weight: 500;">${item.name}</td>
				`;

				// Add a column for each product
				allProducts.forEach((product) => {
					const amount = products[product] || 0;
					html += `<td>${this.formatCurrency(amount)}</td>`;
				});

				html += `
						<td>${this.formatCurrency(item.amount)}</td>
					</tr>
				`;
			}
		});

		// Grand Total Row
		html += `
			</tbody>
			<tfoot style="background-color: #264a4d; color: #ffffff; font-weight: bold; border-top: 2px solid #3d7579;">
				<tr style="height: 40px;">
					<td colspan="2" style="text-align: left; padding-left: 12px; text-transform: uppercase; letter-spacing: 1px;">TOTAL</td>
		`;

		// Add product-wise totals for each product column
		allProducts.forEach((product) => {
			html += `<td>${this.formatCurrency(productTotals[product])}</td>`;
		});

		html += `
					<td>${this.formatCurrency(zoneTotalAmount)}</td>
				</tr>
			</tfoot>
		</table>`;

		return html;
	}

	attachProductExpandHandlers() {
		const self = this;

		// Handle Zone Expand/Collapse
		this.page.main
			.find(".product-total-row")
			.off("click")
			.on("click", function () {
				const zoneName = $(this).data("zone");
				self.state.expandedZones[zoneName] = !self.state.expandedZones[zoneName];
				self.render();
			});
	}

	attachProductDrilldownHandlers() {
		// No drilldown required for this view as per the new requirements.
	}

	// ========================================================================

	// AGENT WISE VIEW - Zone/Region Collapsible

	// ========================================================================

	renderAgentWiseTable(agentData) {
		if (!agentData || agentData.length === 0) {
			return `
				<div style="text-align: center; padding: 50px; color: #778da9; font-size: 16px;">
					<div style="font-size: 48px; margin-bottom: 15px;">📭</div>
					<div style="font-weight: 600; margin-bottom: 8px;">No agent data available</div>
				</div>
			`;
		}

		// Group by zone
		const grouped = {};
		agentData.forEach((row) => {
			if (!grouped[row.zone]) {
				grouped[row.zone] = [];
			}
			grouped[row.zone].push(row);
		});

		let sr = 1;
		let html = `
			<table class="agent-wise-table">
				<thead>
					<tr class="branch-table-header">
						<th rowspan="2" class="sr-col">SR</th>
						<th rowspan="2">ZONE / REGION</th>
						<th rowspan="2">SS TARGET</th>
						<th rowspan="2">SS ACHIEVEMENT</th>
						<th rowspan="2">SS SHORTFALL</th>
						<th rowspan="2">SS ACTIVE</th>
						<th rowspan="2">SS INACTIVE</th>
						<th rowspan="2">DD TARGET</th>
						<th rowspan="2">DD ACHIEVEMENT</th>
						<th rowspan="2">DD SHORTFALL</th>
						<th rowspan="2">DD ACTIVE</th>
						<th rowspan="2">DD INACTIVE</th>
						<th rowspan="2">%</th>
					</tr>
					<tr class="branch-table-subheader">
					</tr>
				</thead>
				<tbody>
		`;

		// Sort zones
		const sortedZones = Object.keys(grouped).sort((a, b) => {
			const aNum = a.match(/ZONE-(\d+)/)?.[1];
			const bNum = b.match(/ZONE-(\d+)/)?.[1];
			return aNum && bNum ? parseInt(aNum) - parseInt(bNum) : a.localeCompare(b);
		});

		sortedZones.forEach((zone) => {
			const zoneRows = grouped[zone];

			// Calculate zone totals
			let zoneTarget = 0;
			let zoneAch = 0;
			let zoneSsTarget = 0;
			let zoneSsAch = 0;
			let zoneSsActive = 0;
			let zoneSsInactive = 0;
			let zoneActive = 0;
			let zoneInactive = 0;

			zoneRows.forEach((r) => {
				zoneTarget += parseFloat(r.target || 0);
				zoneAch += parseFloat(r.achievement || 0);
				zoneSsTarget += parseFloat(r.ss_target || 0);
				zoneSsAch += parseFloat(r.ss_achievement || 0);
				zoneSsActive += parseFloat(r.ss_active || 0);
				zoneSsInactive += parseFloat(r.ss_inactive || 0);
				zoneActive += parseFloat(r.active || 0);
				zoneInactive += parseFloat(r.inactive || 0);
			});

			const zoneSsShortfall = zoneSsTarget - zoneSsAch;
			const zoneAgentShortfall = zoneTarget - zoneAch;
			const zonePercent = zoneTarget > 0 ? ((zoneAch / zoneTarget) * 100).toFixed(2) : 0;
			const isExpanded = this.state.expandedZones[`agent_${zone}`] || false;
			const zoneDate =
				zoneRows[0]?.date || this.state.selectedDate || frappe.datetime.get_today();

			// Zone row
			html += `
				<tr class="agent-zone-row branch-table-row" data-zone="${zone}" data-date="${zoneDate}" style="background: #f8fafc; cursor: pointer;">
					<td class="sr-col">${sr++}</td>
					<td>
						<div class="branch-info" style="white-space: nowrap;">
							<div class="branch-code-name">
								<span class="agent-toggle" style="display: inline-block; width: 20px; margin-right: 8px; cursor: pointer;">${isExpanded ? "▼" : "▶"}</span>
								<strong style="vertical-align: middle;">${zone}</strong>
							</div>
						</div>
					</td>
					<td class="metric-cell amount-cell">${this.formatCurrency(zoneSsTarget)}</td>
					<td class="metric-cell amount-cell">${this.formatCurrency(zoneSsAch)}</td>
					<td class="metric-cell amount-cell" style="color: ${zoneSsShortfall > 0 ? "#ef4444" : "#10b981"}; font-weight: 600;">${this.formatCurrency(zoneSsShortfall)}</td>
					<td class="metric-cell amount-cell">${this.formatNumber(zoneSsActive)}</td>
					<td class="metric-cell amount-cell">${this.formatNumber(zoneSsInactive)}</td>
					<td class="metric-cell amount-cell">${this.formatCurrency(zoneTarget)}</td>
					<td class="metric-cell amount-cell">${this.formatCurrency(zoneAch)}</td>
					<td class="metric-cell amount-cell" style="color: ${zoneAgentShortfall > 0 ? "#ef4444" : "#10b981"}; font-weight: 600;">${this.formatCurrency(zoneAgentShortfall)}</td>
					<td class="metric-cell amount-cell">${this.formatNumber(zoneActive)}</td>
					<td class="metric-cell amount-cell">${this.formatNumber(zoneInactive)}</td>
					<td>${this.renderProgressBar(zonePercent)}</td>
				</tr>
			`;

			// Sort regions within the zone
			const sortedRegionRows = zoneRows.sort((a, b) => {
				const aNum = a.region.match(/REGION-(\d+)/)?.[1];
				const bNum = b.region.match(/REGION-(\d+)/)?.[1];
				return aNum && bNum
					? parseInt(aNum) - parseInt(bNum)
					: a.region.localeCompare(b.region);
			});

			// Region rows (hidden by default)
			sortedRegionRows.forEach((r) => {
				const rSsTarget = parseFloat(r.ss_target || 0);
				const rSsAch = parseFloat(r.ss_achievement || 0);
				const rTarget = parseFloat(r.target || 0);
				const rAch = parseFloat(r.achievement || 0);
				const rSsActive = parseFloat(r.ss_active || 0);
				const rSsInactive = parseFloat(r.ss_inactive || 0);
				const rActive = parseFloat(r.active || 0);
				const rInactive = parseFloat(r.inactive || 0);
				const rDate = r.date || zoneDate;

				const rSsShortfall = rSsTarget - rSsAch;
				const rAgentShortfall = rTarget - rAch;
				const rPercent = rTarget > 0 ? ((rAch / rTarget) * 100).toFixed(2) : 0;

				html += `
					<tr class="agent-region-row region-of-${zone} branch-table-row" data-region="${r.region}" data-date="${rDate}" style="display: ${isExpanded ? "table-row" : "none"}; background: #ffffff; cursor: pointer;">
						<td class="sr-col"></td>
						<td>
							<div class="branch-info" style="white-space: nowrap;">
								<div class="branch-code-name">
									<span style="display: inline-block; width: 20px; margin-right: 8px;"></span>
									<span style="padding-left: 40px; color: #097c80; font-weight: 500;">${r.region}</span>
								</div>
							</div>
						</td>
						<td class="metric-cell amount-cell">${this.formatCurrency(rSsTarget)}</td>
						<td class="metric-cell amount-cell">${this.formatCurrency(rSsAch)}</td>
						<td class="metric-cell amount-cell" style="color: ${rSsShortfall > 0 ? "#ef4444" : "#10b981"}; font-weight: 600;">${this.formatCurrency(rSsShortfall)}</td>
						<td class="metric-cell amount-cell">${this.formatNumber(rSsActive)}</td>
						<td class="metric-cell amount-cell">${this.formatNumber(rSsInactive)}</td>
						<td class="metric-cell amount-cell">${this.formatCurrency(rTarget)}</td>
						<td class="metric-cell amount-cell">${this.formatCurrency(rAch)}</td>
						<td class="metric-cell amount-cell" style="color: ${rAgentShortfall > 0 ? "#ef4444" : "#10b981"}; font-weight: 600;">${this.formatCurrency(rAgentShortfall)}</td>
						<td class="metric-cell amount-cell">${this.formatNumber(rActive)}</td>
						<td class="metric-cell amount-cell">${this.formatNumber(rInactive)}</td>
						<td>${this.renderProgressBar(rPercent)}</td>
					</tr>
				`;
			});
		});

		html += `</tbody></table>`;
		return html;
	}

	/**
	 * Set date in the Date selector field when clicking Agent Wise rows
	 * Converts date to yyyy-mm-dd format for the date input field
	 * Only works in Agent Wise tab
	 */
	setAgentWiseDate(date_value) {
		if (!date_value) return;

		// Strip time portion if present (handle "2026-03-18 00:00:00" format)
		let clean_date = String(date_value).split(" ")[0];

		// Convert to date object and back to ensure valid format
		let d = frappe.datetime.str_to_obj(clean_date);
		let formatted_for_input = frappe.datetime.obj_to_str(d); // gives yyyy-mm-dd

		// Update the date control
		if (this.dateControl) {
			this.isRefreshingDate = true;
			this.dateControl.set_value(formatted_for_input);
			this.isRefreshingDate = false;
		}

		// Update state and tab-specific date storage
		this.state.selectedDate = formatted_for_input;
		this.tabDates["agent"] = formatted_for_input;

		// Reload data with new date
		this.loadData();
	}

	attachAgentExpandHandlers() {
		const self = this;

		// Handle Zone Expand/Collapse and Date Sync
		this.page.main
			.find(".agent-zone-row")
			.off("click")
			.on("click", function () {
				const zone = $(this).data("zone");
				const rowDate = $(this).data("date");

				// Sync date to date selector (Agent Wise tab only)
				if (rowDate && self.state.activeTab === "agent") {
					self.setAgentWiseDate(rowDate);
				}

				// Toggle expanded state
				self.state.expandedZones[`agent_${zone}`] =
					!self.state.expandedZones[`agent_${zone}`];

				// Re-render to reflect changes
				self.render();
			});

		// Handle Region Row Click - Date Sync Only
		this.page.main
			.find(".agent-region-row")
			.off("click")
			.on("click", function () {
				const rowDate = $(this).data("date");

				// Sync date to date selector (Agent Wise tab only)
				if (rowDate && self.state.activeTab === "agent") {
					self.setAgentWiseDate(rowDate);
				}
			});
	}

	// ========================================================================

	// CATEGORY WISE VIEW - With Zone Breakdown

	// ========================================================================

	renderCategoryTable(reaggregatedCategoryData) {
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

		// Calculate Totals based on reaggregatedCategoryData
		let totalBranches = 0;
		reaggregatedCategoryData.forEach((catData) => {
			const monthData = catData.months[latestMonthKey];
			if (monthData) {
				totalBranches += monthData.count || 0;
			}
		});

		// Calculate total movements based on original data but filtered
		let totalIncreasedBranches = [];
		let totalDecreasedBranches = [];

		this.categoryData.forEach((catData) => {
			const monthData = catData.months[latestMonthKey];
			if (monthData && monthData.changes) {
				const filteredChanges = this.filterMovementData(monthData.changes);
				totalIncreasedBranches = totalIncreasedBranches.concat(filteredChanges.increased);
				totalDecreasedBranches = totalDecreasedBranches.concat(filteredChanges.decreased);
			}
		});
		const totalUp = totalIncreasedBranches.length;
		const totalDown = totalDecreasedBranches.length;

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

		// Filter categories to display
		let categoriesToDisplay = categoryOrder;
		if (this.state.selectedCategories.length > 0) {
			categoriesToDisplay = categoryOrder.filter((c) =>
				this.state.selectedCategories.includes(c),
			);
		}

		categoriesToDisplay.forEach((catName) => {
			const config = categoryConfig[catName];
			// Find data for this specific category
			const reaggCatData = reaggregatedCategoryData.find((c) => c.category === catName);
			const originalCatData = this.categoryData.find((c) => c.category === catName);

			const monthData = reaggCatData?.months[latestMonthKey];
			const originalMonthData = originalCatData?.months[latestMonthKey];

			const count = monthData?.count || 0;

			// Get original changes and filter them based on current filters
			const originalChanges = originalMonthData?.changes || { increased: [], decreased: [] };
			const filteredChanges = this.filterMovementData(originalChanges);
			const upCount = filteredChanges.increased.length;
			const downCount = filteredChanges.decreased.length;

			const isExpanded = this.state.expandedZones[`cat_${catName}`] || false;
			const percentage =
				totalBranches > 0 ? ((count / totalBranches) * 100).toFixed(2) : "0.00";

			html += `
            <tr class="category-row-redesigned" data-category="${catName}" style="border-left: 5px solid ${
				config.color
			};">
                <td class="cat-name-cell">
                    <span class="category-toggle">${isExpanded ? "▼" : "▶"}</span>
                    <span class="cat-grade" style="background-color: ${config.color};">${
						config.grade
					}</span>
                    <div class="cat-name-wrapper">
                        <span>${catName}</span>
                        <span class="category-percentage-share">• ${percentage}%</span>
                    </div>
                </td>
                <td class="perf-band-cell">${config.range}</td>
                <td class="count-cell drill-cell" data-category="${catName}" data-month="${latestMonthKey}">
                    <span class="drill-link">${count}</span>
                </td>
                <td class="movement-cell" data-changes='${JSON.stringify(filteredChanges)}'>
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
										const zoneCount = monthData?.zone_breakdown[zone] || 0; // Use reaggregated zone breakdown
										const isDisabled = zoneCount === 0;
										return `
                                        <div class="zone-card ${isDisabled ? "disabled-zone-card" : ""}">
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

		html += `
            </tbody>
            <tfoot>
                <tr class="category-total-row">
                    <td>Total</td>
                    <td></td>
                    <td class="count-cell">${totalBranches}</td>
                    <td class="total-movement-cell" data-totals='${JSON.stringify({ increased: totalIncreasedBranches, decreased: totalDecreasedBranches })}'>
                        <div class="movement-summary">
                            <span class="mov-up">↑ ${totalUp}</span>
                            <span class="mov-down">↓ ${totalDown}</span>
                        </div>
                    </td>
                    <td></td>
                </tr>
            </tfoot>
        </table>
        `;
		return html;
	}

	_buildMovementPopupContent(increased, decreased) {
		let leftContent = "",
			rightContent = "";

		if (decreased && decreased.length > 0) {
			leftContent += `<div class="popup-section declined">`;

			leftContent += `<h6>Downgraded (${decreased.length})</h6>`;

			decreased.forEach((item) => {
				leftContent += `

							<div class="popup-item">

								<div class="item-header">

									<span class="branch-name">${item.branch} (${item.zone})</span>

									<span class="cat-change">${item.previous_category} → ${item.current_category}</span>

								</div>

								<div class="item-body">

									<span class="pct-change">${item.previous_percentage.toFixed(2)}% → ${item.current_percentage.toFixed(2)}%</span>

									<span class="diff-change">-₹${this.formatCurrency(Math.abs(item.achievement_diff))} | ${item.percentage_diff.toFixed(2)}%</span>

								</div>

							</div>

						`;
			});

			leftContent += `</div>`;
		}

		if (increased && increased.length > 0) {
			rightContent += `<div class="popup-section improved">`;

			rightContent += `<h6>Upgraded (${increased.length})</h6>`;

			increased.forEach((item) => {
				rightContent += `

							<div class="popup-item">

								<div class="item-header">

									<span class="branch-name">${item.branch} (${item.zone})</span>

									<span class="cat-change">${item.previous_category} → ${item.current_category}</span>

								</div>

								<div class="item-body">

									<span class="pct-change">${item.previous_percentage.toFixed(2)}% → ${item.current_percentage.toFixed(2)}%</span>

									<span class="diff-change">+₹${this.formatCurrency(item.achievement_diff)} | +${item.percentage_diff.toFixed(2)}%</span>

								</div>

							</div>

						`;
			});

			rightContent += `</div>`;
		}

		if (!leftContent && !rightContent) return "";

		const leftColumnHTML = leftContent ? `<div class="popup-column">${leftContent}</div>` : "";

		const rightColumnHTML = rightContent
			? `<div class="popup-column">${rightContent}</div>`
			: "";

		return leftColumnHTML + rightColumnHTML;
	}

	attachMovementPopupHandlers() {
		const self = this;
		let popupTimer;

		const showPopup = function (target, data) {
			clearTimeout(popupTimer);
			$(".movement-popup").remove();

			const popupContent = self._buildMovementPopupContent(data.increased, data.decreased);
			if (!popupContent) return;

			const popup = $(
				`<div class="movement-popup"><div class="popup-main-container">${popupContent}</div></div>`,
			).appendTo("body");
			const popupInner = popup.find(".popup-main-container");

			const targetCell = $(target);
			const cellOffset = targetCell.offset();
			const cellHeight = targetCell.outerHeight();
			const cellWidth = targetCell.outerWidth();

			const windowHeight = $(window).height();
			const scrollY = $(window).scrollTop();
			const spaceAbove = cellOffset.top - scrollY;
			const spaceBelow = windowHeight - (cellOffset.top + cellHeight - scrollY);

			let top, left, maxHeight;
			const margin = 20;

			// Decide position and max-height
			if (spaceBelow > spaceAbove) {
				// Position below
				top = cellOffset.top + cellHeight + 10;
				maxHeight = spaceBelow - margin;
			} else {
				// Position above
				top = cellOffset.top - 10; // Initial top before adjusting for popup height
				maxHeight = spaceAbove - margin;
			}

			popupInner.css("max-height", `${maxHeight}px`);

			const popupHeight = popup.outerHeight();
			const popupWidth = popup.outerWidth();

			// Final position adjustment
			if (spaceBelow < spaceAbove) {
				top = cellOffset.top - popupHeight - 10;
			}

			// Boundary checks
			if (top < scrollY + margin / 2) {
				top = scrollY + margin / 2;
			}

			left = cellOffset.left + cellWidth / 2 - popupWidth / 2;
			if (left < 0) left = 5;
			if (left + popupWidth > $(window).width()) left = $(window).width() - popupWidth - 5;

			popup.css({ top: `${top}px`, left: `${left}px` });

			popup
				.on("mouseenter", function () {
					clearTimeout(popupTimer);
				})
				.on("mouseleave", function () {
					hidePopup();
				});
		};

		const hidePopup = function () {
			popupTimer = setTimeout(() => {
				$(".movement-popup").remove();
			}, 100);
		};

		this.page.main
			.find(".movement-cell .movement-summary")
			.on("mouseenter", function () {
				const changesData = $(this).parent().data("changes");
				if (
					changesData &&
					(changesData.increased.length > 0 || changesData.decreased.length > 0)
				) {
					showPopup(this, changesData);
				}
			})
			.on("mouseleave", function () {
				hidePopup();
			});
	}

	attachTotalMovementPopupHandler() {
		const self = this;
		let popupTimer;

		const showPopup = function (target, data) {
			clearTimeout(popupTimer);
			$(".movement-popup").remove();

			const popupContent = self._buildMovementPopupContent(data.increased, data.decreased);
			if (!popupContent) return;

			const popup = $(
				`<div class="movement-popup"><div class="popup-main-container">${popupContent}</div></div>`,
			).appendTo("body");
			const popupInner = popup.find(".popup-main-container");

			const targetCell = $(target);
			const cellOffset = targetCell.offset();
			const cellHeight = targetCell.outerHeight();
			const cellWidth = targetCell.outerWidth();

			const windowHeight = $(window).height();
			const scrollY = $(window).scrollTop();
			const spaceAbove = cellOffset.top - scrollY;
			const spaceBelow = windowHeight - (cellOffset.top + cellHeight - scrollY);

			let top, left, maxHeight;
			const margin = 20;

			// Decide position and max-height
			if (spaceBelow > spaceAbove) {
				// Position below
				top = cellOffset.top + cellHeight + 10;
				maxHeight = spaceBelow - margin;
			} else {
				// Position above
				top = cellOffset.top - 10; // Initial top before adjusting for popup height
				maxHeight = spaceAbove - margin;
			}

			popupInner.css("max-height", `${maxHeight}px`);

			const popupHeight = popup.outerHeight();
			const popupWidth = popup.outerWidth();

			// Final position adjustment
			if (spaceBelow < spaceAbove) {
				top = cellOffset.top - popupHeight - 10;
			}

			// Boundary checks
			if (top < scrollY + margin / 2) {
				top = scrollY + margin / 2;
			}

			left = cellOffset.left + cellWidth / 2 - popupWidth / 2;
			if (left < 0) left = 5;
			if (left + popupWidth > $(window).width()) left = $(window).width() - popupWidth - 5;

			popup.css({ top: `${top}px`, left: `${left}px` });

			popup
				.on("mouseenter", function () {
					clearTimeout(popupTimer);
				})
				.on("mouseleave", function () {
					hidePopup();
				});
		};

		const hidePopup = function () {
			popupTimer = setTimeout(() => {
				$(".movement-popup").remove();
			}, 100);
		};

		this.page.main
			.find(".total-movement-cell .movement-summary")
			.on("mouseenter", function () {
				const totals = $(this).parent().data("totals");
				if (totals && (totals.increased.length > 0 || totals.decreased.length > 0)) {
					showPopup(this, totals);
				}
			})
			.on("mouseleave", function () {
				hidePopup();
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

	attachZoneDrilldownHandlers() {
		const self = this;
		this.page.main.find(".zone-wise-table .branch-drilldown").on("click", function (e) {
			e.stopPropagation(); // Prevents the row's expand/collapse click handler from firing

			const zone = $(this).data("zone");
			const region = $(this).data("region"); // This will be undefined for the zone total row, which is fine

			self.drillDownToBranchView(zone, region);
		});
	}

	drillDownToBranchView(zone, region = null) {
		console.log(
			`Drilling down to Branch view for Zone: ${zone}` +
				(region ? `, Region: ${region}` : ""),
		);

		this.state.selectedZones = [zone];
		this.state.selectedRegion = region || "";
		this.state.drillDownActive = true;

		// Update filter UI elements to reflect the change
		this.page.main.find("#region-selector").val(this.state.selectedRegion);
		this.updateFilterTagsUI(); // this will highlight the correct zone

		this.switchTab("branch");
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

		// --- Correct Performance Segmentation Logic ---

		// 1. Determine the metric for sorting (latest month's percentage)
		const sortMonthKey =
			this.state.selectedMonth || (months.length > 0 ? months[months.length - 1].key : null);

		// 2. Create a safe copy of the filtered data and sort it by performance
		const sortedBranches = [...branchData].sort((a, b) => {
			const aPct = a.months[sortMonthKey]?.percentage || 0;
			const bPct = b.months[sortMonthKey]?.percentage || 0;
			return bPct - aPct; // Descending sort
		});

		// 3. Calculate quartile boundaries and assign segments to the sorted branches
		const total = sortedBranches.length;
		sortedBranches.forEach((branch, index) => {
			if (total < 4) {
				branch.performanceSegment = "N/A";
				branch.rowStyle = "transparent";
			} else {
				const top25_index = Math.floor(total * 0.25);
				const next25_index = Math.floor(total * 0.5);
				const mid25_index = Math.floor(total * 0.75);

				if (index < top25_index) {
					branch.performanceSegment = "Top 25%";
					branch.rowStyle = `background-color: #d4edda;`;
				} else if (index < next25_index) {
					branch.performanceSegment = "Next 25%";
					branch.rowStyle = `background-color: #cce5ff;`;
				} else if (index < mid25_index) {
					branch.performanceSegment = "Mid 25%";
					branch.rowStyle = `background-color: #fff3cd;`;
				} else {
					branch.performanceSegment = "Bottom 25%";
					branch.rowStyle = `background-color: #f8d7da;`;
				}
			}
		});

		// 4. Filter the now-segmented list based on the user's segment selection
		let filteredBranchData = sortedBranches;
		if (this.state.selectedSegment && this.state.selectedSegment !== "all") {
			filteredBranchData = sortedBranches.filter(
				(branch) => branch.performanceSegment === this.state.selectedSegment,
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
					branch.performanceSegment,
				),
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

		const today = new Date();
		const currentMonth = today.getMonth();
		const currentYear = today.getFullYear();

		months.forEach((month) => {
			const monthDate = new Date(month.date);
			const monthIndex = monthDate.getMonth();
			const monthYear = monthDate.getFullYear();

			const monthName = month.display.split("-")[0];
			const displayYear = `${monthName}-${monthYear}`;

			let daysLeftIndicator = "";
			if (monthIndex === currentMonth && monthYear === currentYear) {
				const lastDayOfMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
				const currentDay = today.getDate();
				const remainingDays = lastDayOfMonth - currentDay + 1;

				if (remainingDays >= 0) {
					daysLeftIndicator = `
										<br>
										<span class="days-left-indicator">
											${remainingDays} Day${remainingDays !== 1 ? "s" : ""} Left
										</span>
									`;
				}
			}

			header += `<th colspan="4" class="month-col">${displayYear}${daysLeftIndicator}</th>`;
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

		const styleId = "days-left-indicator-style";
		if (!document.getElementById(styleId)) {
			const style = document.createElement("style");
			style.id = styleId;
			style.innerHTML = `
                @keyframes smooth-blink {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.3; }
                }
                .days-left-indicator {
                    color: red;
                    font-weight: bold;
                    animation: smooth-blink 1.5s infinite;
                    font-size: 12px;
                }
            `;
			document.head.appendChild(style);
		}

		return header;
	}

	buildBranchTableRow(branch, months, serialNo, rowStyle = "", segmentName = "") {
		let html = `<tr class="branch-table-row" data-sol-id="${branch.sol_id}" style="${rowStyle}">`;
		html += `<td>${serialNo}</td>`;
		html += `<td>
			<div class="branch-info">
				<div class="branch-code-name">
					<a onclick="window.showBranchProfilePopup('${branch.sol_id}'); return false;" class="branch-code-link" style="cursor: pointer; text-decoration: underline;">${branch.sol_id}</a>
					<a onclick="window.showBranchProfilePopup('${branch.sol_id}'); return false;" class="branch-name-link" style="cursor: pointer;">${branch.branch}</a>
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

				html += `
                <td class="metric-cell category-cell">${this.getCategoryBadge(
					mdata.category,
					"small",
				)}</td>
                <td class="metric-cell amount-cell">${this.formatNumber(mdata.target)}</td>
                <td class="metric-cell amount-cell">${this.formatNumber(mdata.achievement)}</td>
                <td>
					<div style="display: flex; align-items: center; gap: 8px; justify-content: center;">
						<span class="pct-value" style="color: ${this.getPctColor(pct)}; min-width: 45px; text-align: right;">${pct.toFixed(2)}%</span>
						${this.renderProgressBar(pct)}
					</div>
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

	renderProgressBar(percentage) {
		const pct = Math.max(0, Math.min(100, percentage || 0));
		const color = this.getPctColor(pct);

		return `
			<div class="progress-container-3d">
				<div class="progress-bar-3d" style="width: ${pct}%; background-color: ${color};"></div>
			</div>
		`;
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

	updateSummaryCards(filteredBranches, reaggregatedZoneData) {
		if (!this.months || this.months.length === 0) return;
		
		const currentMonthKey = this.months[0].key;
		
		// 1. Total Branches - Count from filtered branches
		const totalBranches = filteredBranches.length;
		this.page.main.find("#summary-total-branches").text(totalBranches);
		
		// Trend calculation (vs previous month if available)
		const prevMonthKey = this.months.length > 1 ? this.months[1].key : null;
		const trendEl = this.page.main.find("#summary-branches-trend");
		if (prevMonthKey) {
			const currentCount = filteredBranches.filter(b => b.months[currentMonthKey]).length;
			const prevCount = filteredBranches.filter(b => b.months[prevMonthKey]).length;
			if (prevCount > 0) {
				const diff = ((currentCount - prevCount) / prevCount) * 100;
				trendEl.text(`${diff >= 0 ? "+" : ""}${diff.toFixed(1)}% from last month`);
				trendEl.removeClass("success danger muted").addClass(diff >= 0 ? "success" : "danger");
			} else {
				trendEl.text("New data this month").removeClass("success danger").addClass("muted");
			}
		} else {
			trendEl.text("Reporting Period").removeClass("success danger").addClass("muted");
		}
		
		// 2. Target Amount & Achievement - Sum from Zone Wise reaggregated data
		let totalTarget = 0;
		let totalAch = 0;
		reaggregatedZoneData.forEach(item => {
			if (item.isZoneTotal) {
				if (this.state.viewType === "Quarterly" || this.state.viewType === "Yearly") {
					this.months.forEach(month => {
						const mdata = item.months[month.key];
						if (mdata) {
							totalTarget += mdata.target || 0;
							totalAch += mdata.achievement || 0;
						}
					});
				} else {
					const mdata = item.months[currentMonthKey];
					if (mdata) {
						totalTarget += mdata.target || 0;
						totalAch += mdata.achievement || 0;
					}
				}
			}
		});
		
		this.page.main.find("#summary-target-amount").text("₹" + this.formatCurrency(totalTarget));
		let targetLabelText = `${this.normalizeTargetType(this.state.targetType)} target`;
		if (this.state.viewType === "Quarterly") {
			targetLabelText = "Quarterly target";
		} else if (this.state.viewType === "Yearly") {
			targetLabelText = "Yearly target";
		}

		this.page.main
			.find("#summary-target-label")
			.text(targetLabelText);
		this.page.main.find("#summary-achievement-amount").text("₹" + this.formatCurrency(totalAch));
		
		// Achievement Percentage
		const pct = totalTarget > 0 ? (totalAch / totalTarget) * 100 : 0;
		const pctEl = this.page.main.find("#summary-achievement-pct");
		pctEl.text(pct.toFixed(2) + "% achieved");
		pctEl.removeClass("success danger").addClass(pct >= 100 ? "success" : "danger");
		
		// 3. Active Zones - Unique zones in reaggregated data
		const activeZonesCount = reaggregatedZoneData.filter(item => item.isZoneTotal).length;
		this.page.main.find("#summary-active-zones").text(activeZonesCount + " Zones");
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
                    border-color: #417d81;
                    transform: translateY(-1px);
                }

                .filter-tag.active {
                    background: #417d81;
                    border-color: #417d81;
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
                    border-color: #417d81;
                }

                .btn-group .btn.active {
                    background: #417d81;
                    border-color: #417d81;
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
                    color: #417d81;
                }

                .tab-btn.active {
                    border-bottom-color: #417d81;
                    color: #417d81;
                    background: #e0e1dd;
                }

                /* Zone Table Styles */
                .zone-wise-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12px;
                }

             .zone-table-header th {
    /* Primary color #3d7579 with a subtle darkening for depth */
    background: linear-gradient(180deg, #3d7579 0%, #346569 100%);
    
    /* Pure white for maximum readability and a clean look */
    color: #ffffff;
    
    /* Professional spacing and typography */
    padding: 14px 10px;
    text-align: center;
    font-weight: 600;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.03em;

    /* Border adjusted to a darker shade of your teal to look integrated */
    border: 1px solid #2d5659;
    
    /* Optional: subtle top highlight for a "premium" feel */
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

               .zone-table-subheader th {
    /* A slightly lighter, muted teal to distinguish it from the main header */
    background: #4a8a8f; 
    
    /* Pure white for clarity, keeping the font size small as requested */
    color: #ffffff;
    padding: 8px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    
    /* Border that blends with the teal theme instead of the old blue-grey */
    border: 1px solid #366b6f;
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

                .branch-drilldown {
                    cursor: pointer;
                    text-decoration: underline;
                    color: #007bff;
                    font-weight: 600;
                }
                .branch-drilldown:hover {
                    color: #0056b3;
                    font-weight: bold;
                }

                .zone-toggle, .category-toggle {
                    display: inline-block;
                    width: 20px;
                    margin-right: 8px;
                    transition: transform 0.2s ease;
                }

                .region-detail-row {
                    background: #fff;
                    border-left: 4px solid #417d81;
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
                    border-left: 4px solid #417d81;
                }

                .drill-cell {
                    cursor: pointer;
                }

                .drill-link {
                    color: #417d81;
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
                    color: #417d81;
                }

                /* Branch Table Styles */
                .branch-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12px;
                }

              .branch-table-header th {
    /* Using your teal color #3d7579 with a subtle professional gradient */
    background: linear-gradient(180deg, #3d7579 0%, #346569 100%);
    
    /* Clean white text for better readability */
    color: #ffffff;
    
    /* Standardized padding and typography */
    padding: 12px 8px;
    text-align: center;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;

    /* Matching teal border to replace the old blue-grey */
    border: 1px solid #2d5659;
    
    /* Internal highlight for a modern, polished look */
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

               .branch-table-subheader th {
    /* A lighter, muted teal that complements #3d7579 */
    background: #4a8a8f;
    
    /* White text for sharp contrast on a smaller font */
    color: #ffffff;
    padding: 8px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    
    /* Matching teal border to replace the old grey-blue */
    border: 1px solid #366b6f;
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

                /* Agent Wise Table - Match Branch Table Styling */
                .agent-wise-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 12px;
                }
                .agent-wise-table th {
                    background: linear-gradient(180deg, #3d7579 0%, #346569 100%);
                    color: #ffffff;
                    padding: 12px 8px;
                    text-align: center;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.03em;
                    border: 1px solid #2d5659;
                    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
                }
                .agent-wise-table .branch-table-subheader th {
                    background: #4a8a8f;
                    color: #ffffff;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.02em;
                    border: 1px solid #366b6f;
                }
                .agent-wise-table .agent-zone-row,
                .agent-wise-table .agent-region-row {
                    border-bottom: 1px solid #e0e1dd;
                }
                .agent-wise-table .agent-region-row:hover {
                    background: #f8f9fa;
                }
                .agent-wise-table td {
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

                /* Agent toggle - keep arrow and zone name in same row */
                .agent-zone-row .branch-code-name {
                    flex-direction: row;
                    align-items: center;
                    gap: 8px;
                }

                .branch-code-link {
                    color: #417d81;
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
                    background: #417d81;
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
                    padding: 0;
                    z-index: 1000;
                    max-width: 700px;
                    min-width: 350px;
                    font-size: 13px;
                }
                .popup-main-container {
                    display: flex;
                }
                .popup-column {
                    flex: 1;
                    padding: 12px;
                    min-width: 320px;
                }
                .popup-column:first-child:not(:only-child) {
                    border-right: 1px solid #eee;
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

                /* Category Percentage Share */
                .cat-name-wrapper {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-start;
                }
                .category-percentage-share {
                    font-size: 12px;
                    color: #6c757d;
                    font-weight: 400;
                    margin-left: 0;
                }

                /* Category Total Row */
                .category-table-redesigned tfoot {
                    border-top: 2px solid #495057;
                }
                .category-total-row td {
                    font-weight: 700;
                    font-size: 15px;
                }
                .total-movement-cell {
                    cursor: pointer;
                }

                @keyframes progress-bar-stripes {
                  from { background-position: 40px 0; }
                  to { background-position: 0 0; }
                }

                .progress-container-3d {
                    width: 80px;
                    height: 14px;
                    background-color: #e9ecef;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
                    position: relative;
                }

                .progress-bar-3d {
                    height: 100%;
                    border-radius: 8px;
                    transition: width 0.6s ease;
                    background-size: 40px 40px;
                    animation: progress-bar-stripes 2s linear infinite;
                    background-image: linear-gradient(45deg, rgba(255,255,255,.15) 25%, transparent 25%, transparent 50%, rgba(255,255,255,.15) 50%, rgba(255,255,255,.15) 75%, transparent 75%, transparent);
                }

                /* Summary Cards Styles */
                .summary-cards-container {
                    display: flex;
                    gap: 20px;
                    margin-bottom: 25px;
                    padding: 5px 0;
                    flex-wrap: wrap;
                }
                .summary-card {
                    background: #fff;
                    border-radius: 16px;
                    padding: 24px;
                    flex: 1;
                    min-width: 240px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.05);
                    transition: transform 0.3s ease;
                }
                .summary-card:hover {
                    transform: translateY(-5px);
                }
                .summary-info {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                .summary-label {
                    font-size: 14px;
                    color: #64748b;
                    font-weight: 500;
                }
                .summary-value {
                    font-size: 28px;
                    font-weight: 800;
                    color: #1e293b;
                    letter-spacing: -0.5px;
                }
                .summary-subtext {
                    font-size: 13px;
                    font-weight: 600;
                    margin-top: 4px;
                }
                .summary-subtext.success { color: #10b981; }
                .summary-subtext.danger { color: #ef4444; }
                .summary-subtext.muted { color: #94a3b8; }
                
                .summary-icon-box {
                    width: 56px;
                    height: 56px;
                    background: linear-gradient(135deg, #417d81 0%, #346569 100%);
                    border-radius: 14px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #fff;
                    font-size: 24px;
                    box-shadow: 0 8px 20px rgba(65, 125, 129, 0.25);
                }
            </style>
        `;

		$("head").append(styles);
	}
}
