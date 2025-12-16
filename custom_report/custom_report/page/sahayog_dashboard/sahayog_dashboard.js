frappe.pages["sahayog_dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "MIS Dashboard",
		single_column: true,
	});

	new SahayogDashboard(page);
};

class SahayogDashboard {
	constructor(page) {
		this.page = page;
		this.data = null;
		this.rawData = null;
		this.collapsedGroups = new Set();
		this.currentView = "dashboard";
		this.groupBy = "zone";
		this.activeCategories = new Set();
		this.activeZones = new Set();
		this.filterCollapsed = true;
		this.timePeriod = "daily";
		this.allDrillData = [];
		this.currentZone = null;
		this.currentCategory = null;
		this.allExpanded = false;
		this.chartInstance = null;

		this.loadState();
		this.loadECharts();
		this.init();
	}

	loadECharts() {
		if (!window.echarts) {
			const script = document.createElement("script");
			script.src = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js";
			script.onload = () => {
				console.log("ECharts loaded successfully");
			};
			document.head.appendChild(script);
		}
	}

	init() {
		this.setupStyles();
		this.createFilterPanel();
		this.createCombinedFilters();
		this.createActiveFilterIndicator();
		this.createContentArea();
		this.createChartModal();
		this.createDrillDownView();
		this.loadView("dashboard");
	}

	saveState() {
		const state = {
			timePeriod: this.timePeriod,
			groupBy: this.groupBy,
			activeCategories: Array.from(this.activeCategories),
			activeZones: Array.from(this.activeZones),
			filterCollapsed: this.filterCollapsed,
			fromDate: $("#from-date-filter").val(),
			toDate: $("#to-date-filter").val(),
		};
		localStorage.setItem("sahayog_dashboard_state", JSON.stringify(state));
	}

	loadState() {
		const saved = localStorage.getItem("sahayog_dashboard_state");
		if (saved) {
			try {
				const state = JSON.parse(saved);
				this.timePeriod = state.timePeriod || "daily";
				this.groupBy = state.groupBy || "zone";
				this.activeCategories = new Set(state.activeCategories || []);
				this.activeZones = new Set(state.activeZones || []);
				this.filterCollapsed = state.filterCollapsed !== false;

				setTimeout(() => {
					if (state.fromDate) $("#from-date-filter").val(state.fromDate);
					if (state.toDate) $("#to-date-filter").val(state.toDate);
				}, 100);
			} catch (e) {
				console.error("Failed to load state:", e);
			}
		}
	}

	/**
	 * Transform flat data from Python backend into nested structure
	 * Python returns: [{zone, category, branch_count, loan_target, dep_target, loan_ach, dep_ach}, ...]
	 * We need: {zones: [{zone, categories: [...]}], grand_total: {...}}
	 */
	transformPythonData(flatData) {
		const zoneMap = {};

		// Group by zone and category
		flatData.forEach((row) => {
			const zoneName = row.zone;
			const categoryName = row.category;

			// Initialize zone if not exists
			if (!zoneMap[zoneName]) {
				zoneMap[zoneName] = {
					zone: zoneName,
					branch_count: 0,
					dec: { tgt: 0, ach: 0 },
					jan: { tgt: 0, ach: 0 },
					feb: { tgt: 0, ach: 0 },
					mar: { tgt: 0, ach: 0 },
					total: { tgt: 0, ach: 0 },
					categories: {},
				};
			}

			// Initialize category within zone if not exists
			if (!zoneMap[zoneName].categories[categoryName]) {
				zoneMap[zoneName].categories[categoryName] = {
					category: categoryName,
					branch_count: 0,
					dec: { tgt: 0, ach: 0 },
					jan: { tgt: 0, ach: 0 },
					feb: { tgt: 0, ach: 0 },
					mar: { tgt: 0, ach: 0 },
					total: { tgt: 0, ach: 0 },
				};
			}

			// Split loan/deposit into monthly breakdown (equal distribution for now)
			const loanTgt = row.loan_target || 0;
			const loanAch = row.loan_ach || 0;
			const depTgt = row.dep_target || 0;
			const depAch = row.dep_ach || 0;

			// Divide equally across 4 months (DEC, JAN, FEB, MAR)
			const monthlyLoanTgt = loanTgt / 4;
			const monthlyLoanAch = loanAch / 4;
			const monthlyDepTgt = depTgt / 4;
			const monthlyDepAch = depAch / 4;

			const monthlyTgt = monthlyLoanTgt + monthlyDepTgt;
			const monthlyAch = monthlyLoanAch + monthlyDepAch;

			// Update zone totals
			zoneMap[zoneName].branch_count += row.branch_count || 0;
			["dec", "jan", "feb", "mar"].forEach((month) => {
				zoneMap[zoneName][month].tgt += monthlyTgt;
				zoneMap[zoneName][month].ach += monthlyAch;
			});
			zoneMap[zoneName].total.tgt += loanTgt + depTgt;
			zoneMap[zoneName].total.ach += loanAch + depAch;

			// Update category within zone
			const cat = zoneMap[zoneName].categories[categoryName];
			cat.branch_count += row.branch_count || 0;
			["dec", "jan", "feb", "mar"].forEach((month) => {
				cat[month].tgt += monthlyTgt;
				cat[month].ach += monthlyAch;
			});
			cat.total.tgt += loanTgt + depTgt;
			cat.total.ach += loanAch + depAch;
		});

		// Convert to array format
		const zones = Object.values(zoneMap).map((zone) => ({
			...zone,
			categories: Object.values(zone.categories),
		}));

		// Calculate grand totals
		const grand_total = {
			branch_count: 0,
			dec: { tgt: 0, ach: 0 },
			jan: { tgt: 0, ach: 0 },
			feb: { tgt: 0, ach: 0 },
			mar: { tgt: 0, ach: 0 },
			total: { tgt: 0, ach: 0 },
		};

		zones.forEach((zone) => {
			grand_total.branch_count += zone.branch_count;
			["dec", "jan", "feb", "mar"].forEach((month) => {
				grand_total[month].tgt += zone[month].tgt;
				grand_total[month].ach += zone[month].ach;
			});
			grand_total.total.tgt += zone.total.tgt;
			grand_total.total.ach += zone.total.ach;
		});

		return { zones, grand_total };
	}

	setupStyles() {
		const styles = `
            <style>
                /* Filter Panel */
                .filter-panel {
                    background: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    padding: 0;
                    margin-bottom: 10px;
                    max-height: 0;
                    overflow: hidden;
                    transition: all 0.3s ease;
                }
                
                .filter-panel.expanded {
                    max-height: 120px;
                    padding: 12px;
                }
                
                .filter-row {
                    display: flex;
                    gap: 10px;
                    align-items: flex-end;
                    flex-wrap: wrap;
                }
                
                .filter-group {
                    flex: 1;
                    min-width: 140px;
                }
                
                .filter-group label {
                    display: block;
                    color: var(--text-muted);
                    font-size: 11px;
                    font-weight: 600;
                    margin-bottom: 4px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .filter-group input {
                    width: 100%;
                    padding: 6px 10px;
                    background: var(--control-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 4px;
                    color: var(--text-color);
                    font-size: 12px;
                }
                
                .filter-group input:focus {
                    outline: none;
                    border-color: #000;
                }
                
                .apply-filter-btn {
                    background: #000;
                    color: white;
                    border: none;
                    padding: 7px 16px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    white-space: nowrap;
                }
                
                .apply-filter-btn:hover {
                    background: #2d2d2d;
                }
                
                /* COMBINED FILTERS */
                .combined-filters {
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 10px 14px;
                    margin-bottom: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                }
                
                .filter-section {
                    margin-bottom: 8px;
                }
                
                .filter-section:last-child {
                    margin-bottom: 0;
                }
                
                .filter-section-label {
                    color: #64748b;
                    font-size: 10px;
                    font-weight: 700;
                    margin-bottom: 6px;
                    text-transform: uppercase;
                    letter-spacing: 0.8px;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }
                
                .filter-chips {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 6px;
                }
                
                .filter-chip {
                    padding: 6px 14px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    border: 2px solid transparent;
                    color: #1e293b;
                    position: relative;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                
                .filter-chip:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }

                .chip-count {
                    background: rgba(0, 0, 0, 0.15);
                    color: inherit;
                    padding: 2px 6px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: 700;
                    min-width: 20px;
                    text-align: center;
                }

                .filter-chip.active .chip-count {
                    background: rgba(255, 255, 255, 0.3);
                }
                
                .filter-chip[data-zone] {
                    background: rgba(255, 255, 255, 0.8);
                    border: 1px solid #cbd5e1;
                    color: #475569;
                }
                
                .filter-chip[data-zone]:hover {
                    background: white;
                    border-color: #94a3b8;
                }
                
                .filter-chip[data-zone].active {
                    background: #000;
                    color: white;
                    border-color: #000;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                
                .filter-chip[data-category="all"] {
                    background: white;
                    border: 1px solid #cbd5e1;
                    color: #475569;
                }
                
                .filter-chip[data-category="all"].active {
                    background: #000;
                    color: white;
                    border-color: #000;
                }
                
                .filter-chip[data-category="Pinacle"] {
                    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                    color: white;
                    border-color: #16a34a;
                }
                
                .filter-chip[data-category="Pinacle"].active {
                    border: 2px dashed white;
                    box-shadow: 0 0 0 3px #22c55e, 0 4px 12px rgba(34, 197, 94, 0.4);
                }
                
                .filter-chip[data-category="Master"] {
                    background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%);
                    color: white;
                    border-color: #0d9488;
                }
                
                .filter-chip[data-category="Master"].active {
                    border: 2px dashed white;
                    box-shadow: 0 0 0 3px #14b8a6, 0 4px 12px rgba(20, 184, 166, 0.4);
                }
                
                .filter-chip[data-category="Accelerator"] {
                    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
                    color: white;
                    border-color: #0284c7;
                }
                
                .filter-chip[data-category="Accelerator"].active {
                    border: 2px dashed white;
                    box-shadow: 0 0 0 3px #0ea5e9, 0 4px 12px rgba(14, 165, 233, 0.4);
                }
                
                .filter-chip[data-category="Starter"] {
                    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                    color: white;
                    border-color: #d97706;
                }
                
                .filter-chip[data-category="Starter"].active {
                    border: 2px dashed white;
                    box-shadow: 0 0 0 3px #f59e0b, 0 4px 12px rgba(245, 158, 11, 0.4);
                }
                
                .filter-chip[data-category="Learner"] {
                    background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
                    color: white;
                    border-color: #ea580c;
                }
                
                .filter-chip[data-category="Learner"].active {
                    border: 2px dashed white;
                    box-shadow: 0 0 0 3px #f97316, 0 4px 12px rgba(249, 115, 22, 0.4);
                }
                
                .filter-chip[data-category="Zero Level"] {
                    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                    color: white;
                    border-color: #dc2626;
                }
                
                .filter-chip[data-category="Zero Level"].active {
                    border: 2px dashed white;
                    box-shadow: 0 0 0 3px #ef4444, 0 4px 12px rgba(239, 68, 68, 0.4);
                }
                
                .clear-filters-btn {
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    color: #dc2626;
                    padding: 5px 14px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: inline-flex;
                    align-items: center;
                    gap: 5px;
                }
                
                .clear-filters-btn:hover {
                    background: rgba(239, 68, 68, 0.2);
                    border-color: rgba(239, 68, 68, 0.5);
                    color: #b91c1c;
                    transform: translateY(-1px);
                }
                
                .clear-filters-btn i {
                    font-size: 10px;
                }
                
                /* Active Filter Indicator */
                .active-filter-indicator {
                    background: linear-gradient(90deg, #000 0%, #1a1a1a 100%);
                    border-left: 3px solid #fff;
                    padding: 8px 14px;
                    margin-bottom: 12px;
                    border-radius: 4px;
                    display: none;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                
                .active-filter-indicator.show {
                    display: block;
                }
                
                .filter-indicator-text {
                    color: #e0e0e0;
                    font-size: 12px;
                    font-weight: 600;
                    line-height: 1.4;
                }
                
                .filter-badge {
                    display: inline-block;
                    background: rgba(255, 255, 255, 0.15);
                    color: white;
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: 700;
                    margin: 0 3px;
                }
                
                /* Content Views */
                .sahayog-content {
                    position: relative;
                }
                
                .view-container {
                    display: none;
                }
                
                .view-container.active {
                    display: block;
                }

                /* Table Header Controls */
                .table-header-controls {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 16px;
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                    border: 1px solid #e2e8f0;
                    border-bottom: none;
                    border-radius: 6px 6px 0 0;
                    gap: 16px;
                    flex-wrap: wrap;
                }

                .table-header-left {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    flex-wrap: wrap;
                }

                .table-header-right {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    flex-wrap: wrap;
                }

                .table-header-title {
                    font-size: 13px;
                    font-weight: 700;
                    color: #1e293b;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                /* Time Period Toggle */
                .time-period-toggle {
                    display: inline-flex;
                    gap: 0;
                    background: white;
                    border-radius: 5px;
                    padding: 2px;
                    border: 1px solid #cbd5e1;
                }
                
                .time-period-btn {
                    padding: 5px 12px;
                    border: none;
                    background: transparent;
                    color: #64748b;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    border-radius: 4px;
                    transition: all 0.2s;
                }
                
                .time-period-btn:hover {
                    background: #f1f5f9;
                    color: #334155;
                }
                
                .time-period-btn.active {
                    background: #000;
                    color: white;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                }

                /* Grouping Toggle */
                .grouping-toggle {
                    display: inline-flex;
                    gap: 0;
                    background: white;
                    border-radius: 5px;
                    padding: 2px;
                    border: 1px solid #cbd5e1;
                }
                
                .grouping-btn {
                    padding: 5px 12px;
                    border: none;
                    background: transparent;
                    color: #64748b;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    border-radius: 4px;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }
                
                .grouping-btn:hover {
                    background: #f1f5f9;
                    color: #334155;
                }
                
                .grouping-btn.active {
                    background: #000;
                    color: white;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                }

                .grouping-btn i {
                    font-size: 10px;
                }

                /* Chart Visualize Button with Dropdown */
                .chart-visualize-wrapper {
                    position: relative;
                }

                .chart-visualize-btn {
                    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                    color: white;
                    border: none;
                    padding: 5px 12px;
                    border-radius: 5px;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }

                .chart-visualize-btn:hover {
                    background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
                }

                .chart-visualize-btn i:first-child {
                    font-size: 11px;
                }

                .chart-visualize-btn i:last-child {
                    font-size: 8px;
                }

                .chart-dropdown {
                    position: absolute;
                    top: 100%;
                    right: 0;
                    margin-top: 5px;
                    background: white;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
                    min-width: 180px;
                    z-index: 1000;
                    display: none;
                }

                .chart-dropdown.show {
                    display: block;
                }

                .chart-dropdown-item {
                    padding: 10px 14px;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-size: 12px;
                    color: #475569;
                    border-bottom: 1px solid #f1f5f9;
                }

                .chart-dropdown-item:last-child {
                    border-bottom: none;
                }

                .chart-dropdown-item:hover {
                    background: #f8fafc;
                    color: #000;
                }

                .chart-dropdown-item i {
                    font-size: 14px;
                    width: 20px;
                    text-align: center;
                }

                .chart-dropdown-item.bar-chart i {
                    color: #6366f1;
                }

                .chart-dropdown-item.bubble-chart i {
                    color: #ec4899;
                }

                /* Filter Toggle Button */
                .filter-toggle-btn {
                    background: white;
                    color: #475569;
                    border: 1px solid #cbd5e1;
                    padding: 5px 12px;
                    border-radius: 5px;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    transition: all 0.2s;
                }
                
                .filter-toggle-btn:hover {
                    background: #f1f5f9;
                    border-color: #94a3b8;
                }

                .filter-toggle-btn i:first-child {
                    font-size: 10px;
                }

                .filter-toggle-btn i:last-child {
                    font-size: 8px;
                }

                .toggle-all-btn {
                    background: #000;
                    color: white;
                    border: none;
                    padding: 5px 12px;
                    border-radius: 5px;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }

                .toggle-all-btn:hover {
                    background: #2d2d2d;
                    transform: translateY(-1px);
                }

                .toggle-all-btn i {
                    font-size: 10px;
                }
                
                /* Chart Modal */
                .chart-modal {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.7);
                    z-index: 2000;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }

                .chart-modal.show {
                    display: flex;
                }

                .chart-modal-content {
                    background: white;
                    border-radius: 8px;
                    width: 90%;
                    max-width: 1200px;
                    max-height: 90vh;
                    overflow: auto;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                }

                .chart-modal-header {
                    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                    color: white;
                    padding: 16px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-radius: 8px 8px 0 0;
                }

                .chart-modal-title {
                    font-size: 16px;
                    font-weight: 700;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                .chart-modal-close {
                    background: rgba(255, 255, 255, 0.2);
                    border: none;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .chart-modal-close:hover {
                    background: rgba(255, 255, 255, 0.3);
                }

                .chart-modal-body {
                    padding: 20px;
                }

                #chart-container {
                    width: 100%;
                    height: 500px;
                }
                
                /* Table Styling */
                .table-container-wrapper {
                    position: relative;
                    max-height: 600px;
                    overflow-y: auto;
                    background: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 0 0 6px 6px;
                }

                .table-container {
                    background: var(--card-bg);
                    overflow: visible;
                }
                
                .sahayog-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 13px;
                }
                
                .sahayog-table th,
                .sahayog-table td {
                    padding: 12px 14px;
                    text-align: right;
                    border-bottom: 1px solid var(--table-border-color);
                }
                
                .sahayog-table .row-label {
                    text-align: left;
                    font-weight: 500;
                }
                
                .sahayog-table thead th {
                    background: #000;
                    color: white;
                    font-size: 11px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    position: sticky;
                    top: 0;
                    z-index: 10;
                    border: none;
                }

                .sahayog-table tfoot {
                    position: sticky;
                    bottom: 0;
                    z-index: 10;
                }
                
                .sahayog-table tbody tr:last-child td {
                    border-bottom: none;
                }
                
                .group-row {
                    background: var(--bg-light-gray);
                    font-weight: 600;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                
                .group-row:hover {
                    background: var(--bg-color);
                }
                
                .group-row td {
                    color: var(--text-color);
                }
                
                .collapse-icon {
                    display: inline-block;
                    margin-right: 8px;
                    transition: transform 0.2s;
                    color: #000;
                    font-size: 10px;
                }
                
                .group-row.collapsed .collapse-icon {
                    transform: rotate(-90deg);
                }
                
                .child-row {
                    transition: all 0.2s;
                }
                
                .child-row:hover {
                    transform: scale(1.002);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                
                .child-row td {
                    color: var(--text-color);
                }
                
                .child-row td.row-label {
                    padding-left: 36px;
                    font-weight: 600;
                }
                
                .child-row.hidden {
                    display: none;
                }
                
                .child-row.filtered-out {
                    display: none !important;
                }
                
                /* Category Row Colors */
                .cat-pinacle {
                    background: linear-gradient(90deg, rgba(34, 197, 94, 0.15) 0%, rgba(34, 197, 94, 0.05) 100%);
                    border-left: 5px solid #22c55e;
                }
                
                .cat-pinacle:hover {
                    background: linear-gradient(90deg, rgba(34, 197, 94, 0.25) 0%, rgba(34, 197, 94, 0.10) 100%);
                }
                
                .cat-master {
                    background: linear-gradient(90deg, rgba(20, 184, 166, 0.15) 0%, rgba(20, 184, 166, 0.05) 100%);
                    border-left: 5px solid #14b8a6;
                }
                
                .cat-master:hover {
                    background: linear-gradient(90deg, rgba(20, 184, 166, 0.25) 0%, rgba(20, 184, 166, 0.10) 100%);
                }
                
                .cat-accelerator {
                    background: linear-gradient(90deg, rgba(14, 165, 233, 0.15) 0%, rgba(14, 165, 233, 0.05) 100%);
                    border-left: 5px solid #0ea5e9;
                }
                
                .cat-accelerator:hover {
                    background: linear-gradient(90deg, rgba(14, 165, 233, 0.25) 0%, rgba(14, 165, 233, 0.10) 100%);
                }
                
                .cat-starter {
                    background: linear-gradient(90deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%);
                    border-left: 5px solid #f59e0b;
                }
                
                .cat-starter:hover {
                    background: linear-gradient(90deg, rgba(245, 158, 11, 0.25) 0%, rgba(245, 158, 11, 0.10) 100%);
                }
                
                .cat-learner {
                    background: linear-gradient(90deg, rgba(249, 115, 22, 0.15) 0%, rgba(249, 115, 22, 0.05) 100%);
                    border-left: 5px solid #f97316;
                }
                
                .cat-learner:hover {
                    background: linear-gradient(90deg, rgba(249, 115, 22, 0.25) 0%, rgba(249, 115, 22, 0.10) 100%);
                }
                
                .cat-zero {
                    background: linear-gradient(90deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.05) 100%);
                    border-left: 5px solid #ef4444;
                }
                
                .cat-zero:hover {
                    background: linear-gradient(90deg, rgba(239, 68, 68, 0.25) 0%, rgba(239, 68, 68, 0.10) 100%);
                }
                
                .tgt-ach-cell { font-size: 12px; line-height: 1.5; }
                .tgt-line { color: var(--text-muted); font-weight: 500; }
                .ach-line { color: #000; font-weight: 700; }
                .na-text { color: var(--gray-500); font-style: italic; }
                
                .grand-total-row {
                    background: linear-gradient(135deg, #000 0%, #1a1a1a 100%) !important;
                    font-weight: 700;
                    border-top: 3px solid #fff !important;
                    box-shadow: 0 -4px 12px rgba(0,0,0,0.3);
                }
                
                .grand-total-row td {
                    color: #ffffff !important;
                    border-bottom: none !important;
                    padding: 14px !important;
                }

                .grand-total-row .tgt-line,
                .grand-total-row .ach-line {
                    color: #ffffff !important;
                }
                
                .loading-row td {
                    text-align: center !important;
                    padding: 40px;
                    color: var(--text-muted);
                }

                /* DRILL DOWN */
                .drill-down-view {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: var(--bg-color);
                    z-index: 1050;
                    overflow: auto;
                }
                
                .drill-down-view.active {
                    display: block;
                }
                
                .drill-down-header {
                    background: #000;
                    color: white;
                    padding: 14px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    position: sticky;
                    top: 0;
                    z-index: 100;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                }
                
                .drill-down-title {
                    font-size: 15px;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .drill-close-btn {
                    background: rgba(255, 255, 255, 0.15);
                    border: none;
                    color: white;
                    padding: 7px 18px;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    gap: 6px;
                }
                
                .drill-close-btn:hover {
                    background: rgba(255, 255, 255, 0.25);
                }
                
                .drill-down-body {
                    padding: 20px;
                    max-width: 1600px;
                    margin: 0 auto;
                }

                .drill-filters {
                    background: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    padding: 12px;
                    margin-bottom: 15px;
                }
                
                .drill-filters-row {
                    display: flex;
                    gap: 12px;
                    flex-wrap: wrap;
                    align-items: flex-end;
                }
                
                .drill-filter-group {
                    flex: 1;
                    min-width: 180px;
                }
                
                .drill-filter-group label {
                    display: block;
                    color: var(--text-muted);
                    font-size: 11px;
                    font-weight: 600;
                    margin-bottom: 5px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .drill-filter-group select,
                .drill-filter-group input {
                    width: 100%;
                    padding: 7px 10px;
                    background: var(--control-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 4px;
                    color: var(--text-color);
                    font-size: 12px;
                }
                
                .drill-filter-group select:focus,
                .drill-filter-group input:focus {
                    outline: none;
                    border-color: #000;
                }
                
                .drill-reset-btn {
                    background: #1a1a1a;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    white-space: nowrap;
                }
                
                .drill-reset-btn:hover {
                    background: #2d2d2d;
                }
                
                @media (max-width: 768px) {
                    .table-header-controls {
                        flex-direction: column;
                        align-items: stretch;
                    }

                    .table-header-left,
                    .table-header-right {
                        justify-content: center;
                    }
                    
                    .filter-row {
                        flex-direction: column;
                    }
                    
                    .filter-group {
                        width: 100%;
                    }
                }
            </style>
        `;
		$(styles).appendTo("head");
	}

	switchTimePeriod(period) {
		this.timePeriod = period;
		$(".time-period-btn").removeClass("active");
		$(`.time-period-btn[data-period="${period}"]`).addClass("active");
		this.saveState();
		this.updateFilterIndicator();
		this.loadDashboardData();
	}

	createFilterPanel() {
		const filterHtml = `
            <div class="filter-panel ${this.filterCollapsed ? "" : "expanded"}" id="filter-panel">
                <div class="filter-row">
                    <div class="filter-group">
                        <label>From Date</label>
                        <input type="date" id="from-date-filter" />
                    </div>
                    <div class="filter-group">
                        <label>To Date</label>
                        <input type="date" id="to-date-filter" />
                    </div>
                    <div class="filter-group" style="flex: 0;">
                        <label>&nbsp;</label>
                        <button class="apply-filter-btn" id="apply-filter">
                            Apply
                        </button>
                    </div>
                </div>
            </div>
        `;
		$(filterHtml).appendTo(this.page.main);

		$("#apply-filter").on("click", () => this.applyFilters());
		$("#from-date-filter, #to-date-filter").on("change", () => this.saveState());
	}

	createCombinedFilters() {
		const filtersHtml = `
            <div class="combined-filters">
                <div class="filter-section">
                    <div class="filter-section-label">
                        <i class="fa fa-map-marker-alt" style="font-size: 9px;"></i> ZONE
                    </div>
                    <div class="filter-chips" id="zone-chips">
                        <div class="filter-chip active" data-zone="all">All <span class="chip-count">0</span></div>
                    </div>
                </div>
                
                <div class="filter-section">
                    <div class="filter-section-label">
                        <i class="fa fa-layer-group" style="font-size: 9px;"></i> PERFORMANCE CATEGORIES
                    </div>
                    <div class="filter-chips">
                        <div class="filter-chip ${
							this.activeCategories.size === 0 ? "active" : ""
						}" data-category="all">All <span class="chip-count" id="count-all">0</span></div>
                        <div class="filter-chip ${
							this.activeCategories.has("Pinacle") ? "active" : ""
						}" data-category="Pinacle">Pinacle <span class="chip-count" id="count-pinacle">0</span></div>
                        <div class="filter-chip ${
							this.activeCategories.has("Master") ? "active" : ""
						}" data-category="Master">Master <span class="chip-count" id="count-master">0</span></div>
                        <div class="filter-chip ${
							this.activeCategories.has("Accelerator") ? "active" : ""
						}" data-category="Accelerator">Accelerator <span class="chip-count" id="count-accelerator">0</span></div>
                        <div class="filter-chip ${
							this.activeCategories.has("Starter") ? "active" : ""
						}" data-category="Starter">Starter <span class="chip-count" id="count-starter">0</span></div>
                        <div class="filter-chip ${
							this.activeCategories.has("Learner") ? "active" : ""
						}" data-category="Learner">Learner <span class="chip-count" id="count-learner">0</span></div>
                        <div class="filter-chip ${
							this.activeCategories.has("Zero Level") ? "active" : ""
						}" data-category="Zero Level">Zero Level <span class="chip-count" id="count-zero">0</span></div>
                    </div>
                </div>

                <div class="filter-section" style="text-align: right; margin-top: 8px;">
                    <button class="clear-filters-btn" id="clear-all-filters">
                        <i class="fa fa-times-circle"></i> Clear All Filters
                    </button>
                </div>
            </div>
        `;
		$(filtersHtml).appendTo(this.page.main);

		this.loadZoneChips();

		$(".filter-chip[data-category]").on("click", (e) => {
			const chip = $(e.currentTarget);
			const category = chip.data("category");
			this.toggleCategoryFilter(category, chip);
		});

		$("#clear-all-filters").on("click", () => this.clearAllFilters());
	}

	loadZoneChips() {
		// Hardcoded zones - no server call
		const zones = [
			{ name: "ZONE-1" },
			{ name: "ZONE-2" },
			{ name: "ZONE-3" },
			{ name: "ZONE-4" },
			{ name: "ZONE-5" },
			{ name: "ZONE-6" },
		];

		const container = $("#zone-chips");

		zones.forEach((zone) => {
			const zoneName = zone.name;
			const isActive = this.activeZones.has(zoneName) ? "active" : "";

			container.append(`
            <div class="filter-chip ${isActive}" data-zone="${zoneName}">
                ${zoneName}
                <span class="chip-count zone-count-${zoneName}">0</span>
            </div>
        `);
		});

		$(".filter-chip[data-zone]").on("click", (e) => {
			const chip = $(e.currentTarget);
			const zone = chip.data("zone");
			this.toggleZoneFilter(zone, chip);
		});

		if (this.activeZones.size === 0) {
			$('.filter-chip[data-zone="all"]').removeClass("active");
		}
	}

	toggleZoneFilter(zone, chip) {
		if (zone === "all") {
			$(".filter-chip[data-zone]").removeClass("active");
			chip.addClass("active");
			this.activeZones.clear();
		} else {
			$('.filter-chip[data-zone="all"]').removeClass("active");
			chip.toggleClass("active");

			if (chip.hasClass("active")) {
				this.activeZones.add(zone);
			} else {
				this.activeZones.delete(zone);
			}

			if (this.activeZones.size === 0) {
				$('.filter-chip[data-zone="all"]').addClass("active");
			}
		}

		this.saveState();
		this.updateFilterIndicator();
		this.updateCategoryCounts();
		this.applyQuickFilters();
	}

	toggleCategoryFilter(category, chip) {
		if (category === "all") {
			$(".filter-chip[data-category]").removeClass("active");
			chip.addClass("active");
			this.activeCategories.clear();
		} else {
			$('.filter-chip[data-category="all"]').removeClass("active");
			chip.toggleClass("active");

			if (chip.hasClass("active")) {
				this.activeCategories.add(category);
			} else {
				this.activeCategories.delete(category);
			}

			if (this.activeCategories.size === 0) {
				$('.filter-chip[data-category="all"]').addClass("active");
			}
		}

		this.saveState();
		this.updateFilterIndicator();
		this.applyQuickFilters();
	}

	clearAllFilters() {
		this.activeZones.clear();
		$(".filter-chip[data-zone]").removeClass("active");
		$('.filter-chip[data-zone="all"]').addClass("active");

		this.activeCategories.clear();
		$(".filter-chip[data-category]").removeClass("active");
		$('.filter-chip[data-category="all"]').addClass("active");

		$("#from-date-filter").val("");
		$("#to-date-filter").val("");

		this.saveState();
		this.updateFilterIndicator();
		this.updateCategoryCounts();
		this.applyQuickFilters();
	}

	createActiveFilterIndicator() {
		const indicatorHtml = `
            <div class="active-filter-indicator" id="filter-indicator">
                <div class="filter-indicator-text" id="filter-indicator-text"></div>
            </div>
        `;
		$(indicatorHtml).appendTo(this.page.main);
		this.updateFilterIndicator();
	}

	updateFilterIndicator() {
		const indicator = $("#filter-indicator");
		const text = $("#filter-indicator-text");
		let parts = [];

		parts.push(`<span class="filter-badge">${this.timePeriod.toUpperCase()}</span>`);

		if (this.activeZones.size > 0) {
			const zoneList = Array.from(this.activeZones).join(", ");
			parts.push(`Zones <span class="filter-badge">${zoneList}</span>`);
		}

		if (this.activeCategories.size > 0) {
			const catList = Array.from(this.activeCategories).join(", ");
			parts.push(`Categories <span class="filter-badge">${catList}</span>`);
		}

		if (parts.length > 1) {
			text.html(`Viewing ${parts.join(" • ")}`);
			indicator.addClass("show");
		} else {
			text.html(`Viewing <span class="filter-badge">ALL DATA</span>`);
			indicator.addClass("show");
		}
	}

	updateCategoryCounts() {
		if (!this.rawData) return;

		const counts = {
			Pinacle: 0,
			Master: 0,
			Accelerator: 0,
			Starter: 0,
			Learner: 0,
			"Zero Level": 0,
			All: 0,
		};

		const zoneCounts = {};
		const showAllZones = this.activeZones.size === 0;

		if (this.rawData.zones) {
			this.rawData.zones.forEach((zone) => {
				const zoneMatch = showAllZones || this.activeZones.has(zone.zone);
				if (zoneMatch) {
					if (!zoneCounts[zone.zone]) {
						zoneCounts[zone.zone] = 0;
					}
					zoneCounts[zone.zone] += zone.branch_count || 0;
				}

				if (zone.categories) {
					zone.categories.forEach((cat) => {
						if (zoneMatch && counts.hasOwnProperty(cat.category)) {
							counts[cat.category] += cat.branch_count || 0;
							counts["All"] += cat.branch_count || 0;
						}
					});
				}
			});
		}

		$("#count-pinacle").text(counts["Pinacle"]);
		$("#count-master").text(counts["Master"]);
		$("#count-accelerator").text(counts["Accelerator"]);
		$("#count-starter").text(counts["Starter"]);
		$("#count-learner").text(counts["Learner"]);
		$("#count-zero").text(counts["Zero Level"]);
		$("#count-all").text(counts["All"]);

		Object.keys(zoneCounts).forEach((zone) => {
			$(`.zone-count-${zone}`).text(zoneCounts[zone]);
		});

		$('.filter-chip[data-zone="all"] .chip-count').text(counts["All"]);
	}

	createContentArea() {
		const contentHtml = `
            <div class="sahayog-content">
                <div id="dashboard-view" class="view-container active"></div>
                <div id="branch-targets-view" class="view-container"></div>
            </div>
        `;
		$(contentHtml).appendTo(this.page.main);

		this.page.set_secondary_action("Branch Targets", () => this.loadView("branch-targets"));
	}

	createChartModal() {
		const modalHtml = `
            <div class="chart-modal" id="chart-modal">
                <div class="chart-modal-content">
                    <div class="chart-modal-header">
                        <div class="chart-modal-title">
                            <i class="fa fa-chart-bar"></i>
                            <span id="chart-modal-title-text">Chart Visualization</span>
                        </div>
                        <button class="chart-modal-close" id="close-chart-modal">
                            <i class="fa fa-times"></i> Close
                        </button>
                    </div>
                    <div class="chart-modal-body">
                        <div id="chart-container"></div>
                    </div>
                </div>
            </div>
        `;
		$("body").append(modalHtml);

		$("#close-chart-modal").on("click", () => this.closeChartModal());
		$("#chart-modal").on("click", (e) => {
			if ($(e.target).is("#chart-modal")) {
				this.closeChartModal();
			}
		});
	}

	openChartModal(chartType) {
		$("#chart-modal").addClass("show");
		if (chartType === "bar") {
			$("#chart-modal-title-text").text("Bar Chart - Performance Overview");
			this.renderBarChart();
		} else if (chartType === "bubble") {
			$("#chart-modal-title-text").text("Bubble Chart - Zone vs Category Analysis");
			this.renderBubbleChart();
		}
	}

	closeChartModal() {
		$("#chart-modal").removeClass("show");
		if (this.chartInstance) {
			this.chartInstance.dispose();
			this.chartInstance = null;
		}
	}

	renderBarChart() {
		if (!window.echarts) {
			frappe.show_alert({ message: "ECharts library is loading...", indicator: "orange" });
			setTimeout(() => this.renderBarChart(), 500);
			return;
		}

		if (!this.rawData) {
			frappe.show_alert({ message: "No data available", indicator: "red" });
			return;
		}

		const chartDom = document.getElementById("chart-container");
		this.chartInstance = echarts.init(chartDom);

		const categories = [];
		const targetData = [];
		const achievementData = [];

		const showAllZones = this.activeZones.size === 0;
		const showAllCategories = this.activeCategories.size === 0;

		if (this.groupBy === "zone") {
			(this.rawData.zones || []).forEach((zone) => {
				const zoneMatch = showAllZones || this.activeZones.has(zone.zone);
				if (zoneMatch) {
					categories.push(zone.zone);
					targetData.push(zone.total.tgt || 0);
					achievementData.push(zone.total.ach || 0);
				}
			});
		} else {
			const categoryMap = {};
			(this.rawData.zones || []).forEach((zone) => {
				(zone.categories || []).forEach((cat) => {
					const catMatch = showAllCategories || this.activeCategories.has(cat.category);
					if (catMatch) {
						if (!categoryMap[cat.category]) {
							categoryMap[cat.category] = { tgt: 0, ach: 0 };
						}
						categoryMap[cat.category].tgt += cat.total.tgt || 0;
						categoryMap[cat.category].ach += cat.total.ach || 0;
					}
				});
			});

			Object.keys(categoryMap).forEach((cat) => {
				categories.push(cat);
				targetData.push(categoryMap[cat].tgt);
				achievementData.push(categoryMap[cat].ach);
			});
		}

		const option = {
			title: {
				text: "Target vs Achievement",
				left: "center",
				textStyle: { fontSize: 18, fontWeight: "bold" },
			},
			tooltip: {
				trigger: "axis",
				axisPointer: { type: "shadow" },
				formatter: function (params) {
					let result = params[0].name + "<br/>";
					params.forEach((param) => {
						result +=
							param.marker +
							" " +
							param.seriesName +
							": " +
							param.value.toLocaleString("en-IN") +
							"<br/>";
					});
					return result;
				},
			},
			legend: { data: ["Target", "Achievement"], top: 40 },
			grid: { left: "3%", right: "4%", bottom: "10%", containLabel: true },
			xAxis: {
				type: "category",
				data: categories,
				axisLabel: { interval: 0, rotate: 45 },
			},
			yAxis: {
				type: "value",
				name: "Amount",
				axisLabel: {
					formatter: function (value) {
						if (value >= 10000000) {
							return (value / 10000000).toFixed(1) + " Cr";
						} else if (value >= 100000) {
							return (value / 100000).toFixed(1) + " L";
						}
						return value;
					},
				},
			},
			series: [
				{
					name: "Target",
					type: "bar",
					data: targetData,
					itemStyle: { color: "#6366f1" },
				},
				{
					name: "Achievement",
					type: "bar",
					data: achievementData,
					itemStyle: { color: "#22c55e" },
				},
			],
		};

		this.chartInstance.setOption(option);

		window.addEventListener("resize", () => {
			if (this.chartInstance) {
				this.chartInstance.resize();
			}
		});
	}

	renderBubbleChart() {
		if (!window.echarts) {
			frappe.show_alert({ message: "ECharts library is loading...", indicator: "orange" });
			setTimeout(() => this.renderBubbleChart(), 500);
			return;
		}

		if (!this.rawData) {
			frappe.show_alert({ message: "No data available", indicator: "red" });
			return;
		}

		const chartDom = document.getElementById("chart-container");
		this.chartInstance = echarts.init(chartDom);

		const categoryOrder = [
			"Pinacle",
			"Master",
			"Accelerator",
			"Starter",
			"Learner",
			"Zero Level",
		];
		const zonesList = [];
		const data = [];

		const showAllZones = this.activeZones.size === 0;
		const showAllCategories = this.activeCategories.size === 0;

		(this.rawData.zones || []).forEach((zone) => {
			const zoneMatch = showAllZones || this.activeZones.has(zone.zone);
			if (!zoneMatch) return;

			if (!zonesList.includes(zone.zone)) {
				zonesList.push(zone.zone);
			}
			const zoneIndex = zonesList.indexOf(zone.zone);

			(zone.categories || []).forEach((cat) => {
				const catMatch = showAllCategories || this.activeCategories.has(cat.category);
				if (!catMatch) return;

				const categoryIndex = categoryOrder.indexOf(cat.category);
				if (zoneIndex >= 0 && categoryIndex >= 0) {
					data.push([
						zoneIndex,
						categoryIndex,
						cat.total.ach || 0,
						cat.branch_count || 0,
						zone.zone,
						cat.category,
						cat.total.tgt || 0,
					]);
				}
			});
		});

		const option = {
			title: {
				text: "Zone vs Category Performance",
				left: "center",
				textStyle: { fontSize: 18, fontWeight: "bold" },
			},
			tooltip: {
				formatter: function (params) {
					const d = params.data;
					return (
						`<strong>${d[4]}</strong> - ${d[5]}<br/>` +
						`Target: ${d[6].toLocaleString("en-IN")}<br/>` +
						`Achievement: ${d[2].toLocaleString("en-IN")}<br/>` +
						`Branches: ${d[3]}`
					);
				},
			},
			grid: { left: "10%", right: "10%", bottom: "15%", top: "15%" },
			xAxis: {
				type: "category",
				data: zonesList,
				name: "Zones",
				nameLocation: "middle",
				nameGap: 30,
				axisLabel: { interval: 0, rotate: 45 },
			},
			yAxis: {
				type: "category",
				data: categoryOrder,
				name: "Categories",
				nameLocation: "middle",
				nameGap: 50,
			},
			visualMap: {
				min: 0,
				max: Math.max(...data.map((d) => d[2])),
				dimension: 2,
				orient: "vertical",
				right: 10,
				top: "center",
				text: ["HIGH", "LOW"],
				calculable: true,
				inRange: {
					color: ["#f1f5f9", "#6366f1", "#4f46e5", "#4338ca"],
				},
			},
			series: [
				{
					type: "scatter",
					symbolSize: function (val) {
						return Math.max(val[3] * 5, 10);
					},
					data: data,
					itemStyle: {
						shadowBlur: 10,
						shadowColor: "rgba(0, 0, 0, 0.3)",
						shadowOffsetY: 5,
						opacity: 0.8,
					},
				},
			],
		};

		this.chartInstance.setOption(option);

		window.addEventListener("resize", () => {
			if (this.chartInstance) {
				this.chartInstance.resize();
			}
		});
	}

	switchGrouping(group) {
		this.groupBy = group;
		$(".grouping-btn").removeClass("active");
		$(`.grouping-btn[data-group="${group}"]`).addClass("active");
		this.saveState();
		this.loadDashboardData();
	}

	toggleFilter() {
		this.filterCollapsed = !this.filterCollapsed;
		const panel = $("#filter-panel");
		const icon = $("#toggle-filter .fa-chevron-down, #toggle-filter .fa-chevron-up");
		if (this.filterCollapsed) {
			panel.removeClass("expanded");
			icon.removeClass("fa-chevron-up").addClass("fa-chevron-down");
		} else {
			panel.addClass("expanded");
			icon.removeClass("fa-chevron-down").addClass("fa-chevron-up");
		}
		this.saveState();
	}

	applyFilters() {
		this.saveState();
		this.updateFilterIndicator();
		this.loadDashboardData();
	}

	applyQuickFilters() {
		const showAllCategories = this.activeCategories.size === 0;
		const showAllZones = this.activeZones.size === 0;

		$(".child-row").each((i, row) => {
			const $row = $(row);
			const category = $row.data("category");
			const zone = $row.data("zone");

			const categoryMatch = showAllCategories || this.activeCategories.has(category);
			const zoneMatch = showAllZones || this.activeZones.has(zone);

			if (categoryMatch && zoneMatch) {
				$row.removeClass("filtered-out");
			} else {
				$row.addClass("filtered-out");
			}
		});

		$(".group-row").each((i, groupRow) => {
			const idx = $(groupRow).data("idx");
			const visibleChildren = $(`.child-${idx}:not(.filtered-out)`).length;
			if (visibleChildren === 0) {
				$(groupRow).hide();
			} else {
				$(groupRow).show();
			}
		});

		this.updateCategoryCounts();
		this.saveState();
	}

	loadView(view) {
		this.currentView = view;
		$(".view-container").removeClass("active");
		$(`#${view}-view`).addClass("active");

		if (view === "dashboard") {
			this.page.set_title("MIS Dashboard");
			this.loadDashboardData();
		} else if (view === "branch-targets") {
			this.page.set_title("Branch Targets");
			this.loadBranchTargets();
		}
	}

	loadDashboardData() {
		const container = $("#dashboard-view");
		container.html(`
            <div class="table-header-controls">
                <div class="table-header-left">
                    <div class="table-header-title">Performance Overview</div>
                </div>
                <div class="table-header-right">
                    <div class="time-period-toggle">
                        <button class="time-period-btn ${
							this.timePeriod === "daily" ? "active" : ""
						}" data-period="daily">Daily</button>
                        <button class="time-period-btn ${
							this.timePeriod === "weekly" ? "active" : ""
						}" data-period="weekly">Weekly</button>
                        <button class="time-period-btn ${
							this.timePeriod === "monthly" ? "active" : ""
						}" data-period="monthly">Monthly</button>
                    </div>
                    <div class="grouping-toggle">
                        <button class="grouping-btn ${
							this.groupBy === "zone" ? "active" : ""
						}" data-group="zone">
                            <i class="fa fa-map-marker-alt"></i> Zone
                        </button>
                        <button class="grouping-btn ${
							this.groupBy === "category" ? "active" : ""
						}" data-group="category">
                            <i class="fa fa-layer-group"></i> Category
                        </button>
                    </div>
                    <div class="chart-visualize-wrapper">
                        <button class="chart-visualize-btn" id="chart-visualize-btn">
                            <i class="fa fa-chart-bar"></i> Visualize
                            <i class="fa fa-chevron-down"></i>
                        </button>
                        <div class="chart-dropdown" id="chart-dropdown">
                            <div class="chart-dropdown-item bar-chart" data-chart="bar">
                                <i class="fa fa-chart-bar"></i> <span>Bar Chart</span>
                            </div>
                            <div class="chart-dropdown-item bubble-chart" data-chart="bubble">
                                <i class="fa fa-chart-scatter"></i> <span>Bubble Chart</span>
                            </div>
                        </div>
                    </div>
                    <button class="filter-toggle-btn" id="toggle-filter">
                        <i class="fa fa-calendar"></i> Date
                        <i class="fa fa-chevron-down"></i>
                    </button>
                    <button class="toggle-all-btn" id="toggle-all-rows">
                        <i class="fa fa-expand-alt"></i> <span>Expand All</span>
                    </button>
                </div>
            </div>
            <div class="table-container-wrapper">
                <div class="table-container">
                    <table class="sahayog-table">
                        <thead>
                            <tr>
                                <th class="row-label">Row Labels</th>
                                <th>Branches</th>
                                <th>DEC-25</th>
                                <th>JAN-26</th>
                                <th>FEB-26</th>
                                <th>MAR-26</th>
                                <th>Total</th>
                            </tr>
                        </thead>
                        <tbody id="dashboard-tbody">
                            <tr class="loading-row">
                                <td colspan="7">
                                    <i class="fa fa-spinner fa-spin"></i> Loading...
                                </td>
                            </tr>
                        </tbody>
                        <tfoot id="dashboard-tfoot"></tfoot>
                    </table>
                </div>
            </div>
        `);

		this.attachDashboardEventListeners();

		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_dashboard_data",
			args: {
				from_date: $("#from-date-filter").val(),
				to_date: $("#to-date-filter").val(),
				time_period: this.timePeriod,
			},
			callback: (r) => {
				if (r.message) {
					// Transform flat Python data to nested structure
					const transformedData = this.transformPythonData(r.message);
					this.rawData = transformedData;
					this.renderDashboard(transformedData);
					this.updateCategoryCounts();
				}
			},
		});
	}

	attachDashboardEventListeners() {
		$(".grouping-btn")
			.off("click")
			.on("click", (e) => {
				const group = $(e.currentTarget).data("group");
				this.switchGrouping(group);
			});

		$(".time-period-btn")
			.off("click")
			.on("click", (e) => {
				const period = $(e.currentTarget).data("period");
				this.switchTimePeriod(period);
			});

		$("#toggle-filter")
			.off("click")
			.on("click", () => this.toggleFilter());
		$("#toggle-all-rows")
			.off("click")
			.on("click", () => this.toggleAllRows());

		$("#chart-visualize-btn")
			.off("click")
			.on("click", (e) => {
				e.stopPropagation();
				$("#chart-dropdown").toggleClass("show");
			});

		$(".chart-dropdown-item")
			.off("click")
			.on("click", (e) => {
				const chartType = $(e.currentTarget).data("chart");
				$("#chart-dropdown").removeClass("show");
				this.openChartModal(chartType);
			});

		$(document)
			.off("click.chart-dropdown")
			.on("click.chart-dropdown", (e) => {
				if (!$(e.target).closest(".chart-visualize-wrapper").length) {
					$("#chart-dropdown").removeClass("show");
				}
			});
	}

	toggleAllRows() {
		this.allExpanded = !this.allExpanded;
		const btn = $("#toggle-all-rows");
		const icon = btn.find("i");
		const text = btn.find("span");

		if (this.allExpanded) {
			this.collapsedGroups.clear();
			$(".group-row").removeClass("collapsed");
			$(".child-row").removeClass("hidden");
			icon.removeClass("fa-expand-alt").addClass("fa-compress-alt");
			text.text("Collapse All");
		} else {
			$(".group-row").each((i, row) => {
				const idx = $(row).data("idx");
				this.collapsedGroups.add(idx);
			});
			$(".group-row").addClass("collapsed");
			$(".child-row").addClass("hidden");
			icon.removeClass("fa-compress-alt").addClass("fa-expand-alt");
			text.text("Expand All");
		}
	}

	renderDashboard(data) {
		const tbody = $("#dashboard-tbody");
		const tfoot = $("#dashboard-tfoot");
		tbody.empty();
		tfoot.empty();
		this.collapsedGroups.clear();

		if (this.groupBy === "zone") {
			this.renderZoneGrouping(data, tbody);
		} else {
			this.renderCategoryGrouping(data, tbody);
		}

		if (data.grand_total) {
			tfoot.append(this.createGrandTotalRow(data.grand_total));
		}

		this.attachRowEvents();
		this.applyQuickFilters();
	}

	renderZoneGrouping(data, tbody) {
		data.zones.forEach((zone, idx) => {
			this.collapsedGroups.add(idx);
			tbody.append(this.createGroupRow(zone.zone, zone, idx));

			this.getSortedCategories(zone.categories).forEach((cat) => {
				tbody.append(this.createChildRow(cat, idx, zone.zone, cat.category));
			});
		});
	}

	renderCategoryGrouping(data, tbody) {
		const categoryData = this.transformToCategoryGrouping(data);

		categoryData.forEach((cat, idx) => {
			this.collapsedGroups.add(idx);
			tbody.append(this.createGroupRow(cat.category, cat, idx));

			const sortedZones = cat.zones.sort((a, b) => {
				return a.zone.localeCompare(b.zone);
			});

			sortedZones.forEach((zone) => {
				tbody.append(this.createChildRow(zone, idx, zone.zone, zone.category));
			});
		});
	}

	getSortedCategories(categories) {
		const order = ["Pinacle", "Master", "Accelerator", "Starter", "Learner", "Zero Level"];
		return categories.sort((a, b) => order.indexOf(a.category) - order.indexOf(b.category));
	}

	transformToCategoryGrouping(data) {
		const categoryOrder = [
			"Pinacle",
			"Master",
			"Accelerator",
			"Starter",
			"Learner",
			"Zero Level",
		];
		const categoryMap = {};

		categoryOrder.forEach((cat) => {
			categoryMap[cat] = {
				category: cat,
				branch_count: 0,
				dec: { tgt: 0, ach: 0 },
				jan: { tgt: 0, ach: 0 },
				feb: { tgt: 0, ach: 0 },
				mar: { tgt: 0, ach: 0 },
				total: { tgt: 0, ach: 0 },
				zones: [],
			};
		});

		data.zones.forEach((zone) => {
			zone.categories.forEach((cat) => {
				if (categoryMap[cat.category]) {
					categoryMap[cat.category].branch_count += cat.branch_count || 0;
					categoryMap[cat.category].dec.tgt += cat.dec.tgt || 0;
					categoryMap[cat.category].dec.ach += cat.dec.ach || 0;
					categoryMap[cat.category].jan.tgt += cat.jan.tgt || 0;
					categoryMap[cat.category].jan.ach += cat.jan.ach || 0;
					categoryMap[cat.category].feb.tgt += cat.feb.tgt || 0;
					categoryMap[cat.category].feb.ach += cat.feb.ach || 0;
					categoryMap[cat.category].mar.tgt += cat.mar.tgt || 0;
					categoryMap[cat.category].mar.ach += cat.mar.ach || 0;
					categoryMap[cat.category].total.tgt += cat.total.tgt || 0;
					categoryMap[cat.category].total.ach += cat.total.ach || 0;

					categoryMap[cat.category].zones.push({
						zone: zone.zone,
						category: cat.category,
						branch_count: cat.branch_count,
						dec: cat.dec,
						jan: cat.jan,
						feb: cat.feb,
						mar: cat.mar,
						total: cat.total,
					});
				}
			});
		});

		return categoryOrder.map((cat) => categoryMap[cat]).filter((cat) => cat.branch_count > 0);
	}

	createGroupRow(label, data, idx) {
		return `
            <tr class="group-row ${
				this.collapsedGroups.has(idx) ? "collapsed" : ""
			}" data-idx="${idx}">
                <td class="row-label">
                    <span class="collapse-icon">&#9662;</span> ${label}
                </td>
                <td>${data.branch_count}</td>
                <td>${this.formatTgtAch(data.dec)}</td>
                <td>${this.formatTgtAch(data.jan)}</td>
                <td>${this.formatTgtAch(data.feb)}</td>
                <td>${this.formatTgtAch(data.mar)}</td>
                <td>${this.formatTgtAch(data.total)}</td>
            </tr>
        `;
	}

	createChildRow(data, groupIdx, zone, category) {
		const label = this.groupBy === "zone" ? category : zone;
		const catClass = this.getCategoryClass(category);

		return `
            <tr class="child-row ${catClass} child-${groupIdx} ${
			this.collapsedGroups.has(groupIdx) ? "hidden" : ""
		}" data-zone="${zone}" data-category="${category}">
                <td class="row-label">${label}</td>
                <td style="cursor:pointer; color:#000; font-weight:700;">${data.branch_count}</td>
                <td>${this.formatTgtAch(data.dec)}</td>
                <td>${this.formatTgtAch(data.jan)}</td>
                <td>${this.formatTgtAch(data.feb)}</td>
                <td>${this.formatTgtAch(data.mar)}</td>
                <td>${this.formatTgtAch(data.total)}</td>
            </tr>
        `;
	}

	createGrandTotalRow(total) {
		return `
            <tr class="grand-total-row">
                <td class="row-label">Grand Total</td>
                <td>${total.branch_count}</td>
                <td>${this.formatTgtAch(total.dec, true)}</td>
                <td>${this.formatTgtAch(total.jan, true)}</td>
                <td>${this.formatTgtAch(total.feb, true)}</td>
                <td>${this.formatTgtAch(total.mar, true)}</td>
                <td>${this.formatTgtAch(total.total, true)}</td>
            </tr>
        `;
	}

	getCategoryClass(category) {
		const map = {
			Pinacle: "cat-pinacle",
			Master: "cat-master",
			Accelerator: "cat-accelerator",
			Starter: "cat-starter",
			Learner: "cat-learner",
			"Zero Level": "cat-zero",
		};
		return map[category] || "";
	}

	formatNumber(num) {
		if (!num) return 0;
		num = parseFloat(num);
		let str = num.toFixed(0);
		let last3 = str.substring(str.length - 3);
		let other = str.substring(0, str.length - 3);
		if (other !== "") last3 = "," + last3;
		return other.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + last3;
	}

	formatTgtAch(data, isGrandTotal = false) {
		if (!data || (data.tgt == null && data.ach == null)) {
			return `<div class="tgt-ach-cell"><span class="na-text">NA</span></div>`;
		}
		const tgt = data.tgt || 0;
		const ach = data.ach || 0;
		return `
            <div class="tgt-ach-cell">
                <div class="tgt-line">T: ${this.formatNumber(tgt)}</div>
                <div class="ach-line">A: ${this.formatNumber(ach)}</div>
            </div>
        `;
	}

	attachRowEvents() {
		$(".group-row")
			.off("click")
			.on("click", (e) => {
				const idx = $(e.currentTarget).data("idx");
				this.toggleGroup(idx);
			});

		$(".child-row td:nth-child(2)")
			.off("click")
			.on("click", (e) => {
				const row = $(e.currentTarget).closest("tr");
				const zone = row.data("zone");
				const category = row.data("category");
				this.openDrillDown(zone, category);
			});
	}

	toggleGroup(idx) {
		const groupRow = $(`.group-row[data-idx="${idx}"]`);
		const childRows = $(`.child-${idx}`);

		if (this.collapsedGroups.has(idx)) {
			this.collapsedGroups.delete(idx);
			groupRow.removeClass("collapsed");
			childRows.removeClass("hidden");
		} else {
			this.collapsedGroups.add(idx);
			groupRow.addClass("collapsed");
			childRows.addClass("hidden");
		}
	}

	createDrillDownView() {
		const drillHtml = `
            <div class="drill-down-view" id="drill-down-view">
                <div class="drill-down-header">
                    <div class="drill-down-title">
                        <i class="fa fa-layer-group"></i>
                        <span id="drill-title"></span>
                    </div>
                    <button class="drill-close-btn" id="drill-close">
                        <i class="fa fa-times"></i> Close
                    </button>
                </div>
                <div class="drill-down-body">
                    <div class="drill-filters">
                        <div class="drill-filters-row">
                            <div class="drill-filter-group">
                                <label>Branch</label>
                                <select id="drill-filter-branch" class="drill-filter">
                                    <option value="">All Branches</option>
                                </select>
                            </div>
                            <div class="drill-filter-group">
                                <label>SOL</label>
                                <input type="text" id="drill-filter-sol" class="drill-filter" placeholder="SOL ID" />
                            </div>
                            <div class="drill-filter-group">
                                <label>Region</label>
                                <select id="drill-filter-region" class="drill-filter">
                                    <option value="">All Regions</option>
                                </select>
                            </div>
                            <div class="drill-filter-group">
                                <label>District</label>
                                <select id="drill-filter-district" class="drill-filter">
                                    <option value="">All Districts</option>
                                </select>
                            </div>
                            <div class="drill-filter-group" style="flex: 0;">
                                <label>&nbsp;</label>
                                <button class="drill-reset-btn" id="drill-reset-filters">Reset</button>
                            </div>
                        </div>
                    </div>
                    <div class="table-container">
                        <table class="sahayog-table">
                            <thead>
                                <tr>
                                    <th class="row-label">Branch</th>
                                    <th>SOL</th>
                                    <th>Region</th>
                                    <th>District</th>
                                    <th>DEC-25</th>
                                    <th>JAN-26</th>
                                    <th>FEB-26</th>
                                    <th>MAR-26</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody id="drill-tbody"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
		$("body").append(drillHtml);

		$("#drill-close").on("click", () => this.closeDrillDown());
		$(".drill-filter").on("change input", () => this.applyDrillFilters());
		$("#drill-reset-filters").on("click", () => this.resetDrillFilters());
	}

	openDrillDown(zone, category) {
		this.currentZone = zone;
		this.currentCategory = category;

		$("#drill-title").text(`${zone} - ${category}`);
		$("#drill-down-view").addClass("active");
		$(".filter-panel, .combined-filters, .active-filter-indicator, .sahayog-content").hide();

		this.loadDrillFilterOptions();

		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_drill_down_data",
			args: {
				zone: zone,
				category: category,
				time_period: this.timePeriod,
				from_date: $("#from-date-filter").val(),
				to_date: $("#to-date-filter").val(),
			},
			callback: (r) => {
				if (r.message) {
					this.allDrillData = r.message;
					this.renderDrillDown(r.message);
				}
			},
		});
	}

	closeDrillDown() {
		$("#drill-down-view").removeClass("active");
		$(".filter-panel, .combined-filters, .active-filter-indicator, .sahayog-content").show();
		this.resetDrillFilters();
	}

	loadDrillFilterOptions() {
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Branch Category Report",
				filters: { zone: this.currentZone, branch_score: this.currentCategory },
				fields: ["branches"],
				order_by: "branches asc",
				limit_page_length: 0,
			},
			callback: (r) => {
				const select = $("#drill-filter-branch");
				select.html('<option value="">All Branches</option>');
				if (r.message) {
					r.message.forEach((b) => {
						select.append(`<option value="${b.branches}">${b.branches}</option>`);
					});
				}
			},
		});

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Region",
				fields: ["name"],
				order_by: "name asc",
				limit_page_length: 0,
			},
			callback: (r) => {
				const select = $("#drill-filter-region");
				select.html('<option value="">All Regions</option>');
				if (r.message) {
					r.message.forEach((reg) => {
						select.append(`<option value="${reg.name}">${reg.name}</option>`);
					});
				}
			},
		});

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "District",
				fields: ["name"],
				order_by: "name asc",
				limit_page_length: 0,
			},
			callback: (r) => {
				const select = $("#drill-filter-district");
				select.html('<option value="">All Districts</option>');
				if (r.message) {
					r.message.forEach((dist) => {
						select.append(`<option value="${dist.name}">${dist.name}</option>`);
					});
				}
			},
		});
	}

	applyDrillFilters() {
		if (!this.allDrillData) return;

		const filters = {
			branch: $("#drill-filter-branch").val(),
			sol: $("#drill-filter-sol").val().trim(),
			region: $("#drill-filter-region").val(),
			district: $("#drill-filter-district").val(),
		};

		let filtered = this.allDrillData.filter((row) => {
			if (filters.branch && row.branch !== filters.branch) return false;
			if (filters.sol && (!row.sol || !row.sol.toString().includes(filters.sol)))
				return false;
			if (filters.region && row.region !== filters.region) return false;
			if (filters.district && row.district !== filters.district) return false;
			return true;
		});

		this.renderDrillDown(filtered);
	}

	resetDrillFilters() {
		$(
			"#drill-filter-branch, #drill-filter-sol, #drill-filter-region, #drill-filter-district"
		).val("");
		this.renderDrillDown(this.allDrillData);
	}

	renderDrillDown(branches) {
		const tbody = $("#drill-tbody");
		tbody.empty();

		if (!branches || branches.length === 0) {
			tbody.html(
				`<tr><td colspan="9" style="text-align:center; padding:40px; color:var(--text-muted);">No branches found</td></tr>`
			);
			return;
		}

		branches.forEach((b) => {
			// Transform loan/deposit data into monthly (equal distribution)
			const loanTgt = b.loan_target || 0;
			const loanAch = b.loan_ach || 0;
			const depTgt = b.dep_target || 0;
			const depAch = b.dep_ach || 0;

			const monthlyLoanTgt = loanTgt / 4;
			const monthlyLoanAch = loanAch / 4;
			const monthlyDepTgt = depTgt / 4;
			const monthlyDepAch = depAch / 4;

			const decTgt = monthlyLoanTgt + monthlyDepTgt;
			const decAch = monthlyLoanAch + monthlyDepAch;
			const janTgt = monthlyLoanTgt + monthlyDepTgt;
			const janAch = monthlyLoanAch + monthlyDepAch;
			const febTgt = monthlyLoanTgt + monthlyDepTgt;
			const febAch = monthlyLoanAch + monthlyDepAch;
			const marTgt = monthlyLoanTgt + monthlyDepTgt;
			const marAch = monthlyLoanAch + monthlyDepAch;
			const totalTgt = loanTgt + depTgt;
			const totalAch = loanAch + depAch;

			tbody.append(`
                <tr class="child-row">
                    <td class="row-label">${b.branch || b.branches}</td>
                    <td>${b.sol}</td>
                    <td>${b.region}</td>
                    <td>${b.district}</td>
                    <td>${this.formatTgtAch({ tgt: decTgt, ach: decAch })}</td>
                    <td>${this.formatTgtAch({ tgt: janTgt, ach: janAch })}</td>
                    <td>${this.formatTgtAch({ tgt: febTgt, ach: febAch })}</td>
                    <td>${this.formatTgtAch({ tgt: marTgt, ach: marAch })}</td>
                    <td>${this.formatTgtAch({ tgt: totalTgt, ach: totalAch })}</td>
                </tr>
            `);
		});
	}

	loadBranchTargets() {
		const container = $("#branch-targets-view");
		container.html(`
            <div class="table-container">
                <table class="sahayog-table">
                    <thead>
                        <tr>
                            <th class="row-label">SOL ID</th>
                            <th>Target</th>
                            <th>Financial Year</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody id="targets-tbody">
                        <tr class="loading-row">
                            <td colspan="4"><i class="fa fa-spinner fa-spin"></i> Loading...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `);

		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_branch_targets",
			args: {
				from_date: $("#from-date-filter").val(),
				to_date: $("#to-date-filter").val(),
			},
			callback: (r) => {
				if (r.message) {
					this.renderBranchTargets(r.message);
				}
			},
		});
	}

	renderBranchTargets(targets) {
		const tbody = $("#targets-tbody");
		tbody.empty();

		if (!targets || targets.length === 0) {
			tbody.html(
				`<tr><td colspan="4" style="text-align:center; padding:40px; color:var(--text-muted);">No targets found</td></tr>`
			);
			return;
		}

		targets.forEach((t) => {
			tbody.append(`
                <tr class="child-row">
                    <td class="row-label">${t.sol_id}</td>
                    <td>${this.formatNumber(t.target)}</td>
                    <td>${t.financial_year}</td>
                    <td><span style="padding:5px 12px; background:#000; color:white; border-radius:14px; font-size:11px; font-weight:600;">${
						t.type
					}</span></td>
                </tr>
            `);
		});
	}
}
