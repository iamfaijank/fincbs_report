frappe.pages["sahayog_dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "MIS Dashboard",
		single_column: true,
	});

	new SahayogDashboard(page);
};

class SahayogDashboard {
	constructor(page) {
		this.page = page;

		// Data state
		this.data = null;
		this.rawData = null;
		this.allDrillData = [];
		this.availableDates = [];
		this.selectedDate = null;

		// UI state
		this.collapsedGroups = new Set();
		this.collapsedSegments = new Set([1, 2, 3, 4]); // All segments collapsed by default
		this.currentView = "dashboard";
		this.groupBy = "zone";
		this.activeCategories = new Set();
		this.activeZones = new Set();
		this.allExpanded = false;
		this.chartInstance = null;

		// Drill-down context
		this.currentZone = null;
		this.currentCategory = null;

		// Helpers
		this.dateSelectTimer = null;
		this.chartInstance = null;

		this.loadState();
		this.loadECharts();
		this.init();
	}

	loadECharts() {
		if (!window.echarts) {
			const script = document.createElement("script");
			script.src = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js";
			script.onload = () => console.log("ECharts loaded");
			document.head.appendChild(script);
		}
	}

	init() {
		this.setupStyles();
		this.loadAvailableDates();
	}

	saveState() {
		const state = {
			selectedDate: this.selectedDate,
			groupBy: this.groupBy,
			activeCategories: Array.from(this.activeCategories),
			activeZones: Array.from(this.activeZones),
		};
		localStorage.setItem("sahayog_dashboard_state", JSON.stringify(state));
	}

	loadState() {
		const saved = localStorage.getItem("sahayog_dashboard_state");
		if (!saved) return;

		try {
			const state = JSON.parse(saved);
			this.selectedDate = state.selectedDate || null;
			this.groupBy = state.groupBy || "zone";
			this.activeCategories = new Set(state.activeCategories || []);
			this.activeZones = new Set(state.activeZones || []);
		} catch (e) {
			console.error("Failed to load state:", e);
		}
	}

	loadAvailableDates() {
		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_available_dates",
			callback: (r) => {
				if (r.message && r.message.length > 0) {
					this.availableDates = r.message;

					if (!this.selectedDate) {
						this.selectedDate = this.availableDates[0].date;
					}

					this.createCombinedFilters();
					this.createActiveFilterIndicator();
					this.createContentArea();
					this.createChartModal();
					this.createDrillDownView();
					this.loadView("dashboard");
				} else {
					frappe.msgprint(
						"No data available. Please import Branch Category Report records."
					);
				}
			},
		});
	}

	// Create compact timeline in table header
	createCompactTimeline() {
		const timelineHtml = `
            <div class="timeline-container">
                <div class="compact-timeline">
                    <div class="timeline-dates-compact" id="timeline-dates-compact"></div>
                </div>
            </div>
        `;

		const container = $(timelineHtml);
		const datesContainer = container.find("#timeline-dates-compact");

		this.availableDates.forEach((dateObj) => {
			const isSelected = dateObj.date === this.selectedDate;
			const dateItem = $(`
                <div class="timeline-date-compact ${isSelected ? "selected" : ""}" data-date="${
				dateObj.date
			}" title="${dateObj.display_full}">
                    <div class="timeline-day-compact">${dateObj.day_name}</div>
                    <div class="timeline-num-compact">${dateObj.day_num}</div>
                </div>
            `);

			dateItem.on("click", () => this.selectDate(dateObj.date));
			datesContainer.append(dateItem);
		});

		// Smooth-scroll the selected date into center
		setTimeout(() => {
			const parent = datesContainer.get(0);
			const sel = datesContainer.find(".timeline-date-compact.selected").get(0);
			if (parent && sel) {
				const parentWidth = parent.clientWidth;
				const targetLeft = sel.offsetLeft + sel.offsetWidth / 2 - parentWidth / 2;
				parent.scrollTo({ left: targetLeft, behavior: "smooth" });
			}
		}, 80);

		return container;
	}

	selectDate(date) {
		this.selectedDate = date;

		$(".timeline-date-compact").removeClass("selected");
		$(`.timeline-date-compact[data-date="${date}"]`).addClass("selected");

		// Debounce rapid clicks to avoid multiple API calls
		if (this.dateSelectTimer) clearTimeout(this.dateSelectTimer);
		this.dateSelectTimer = setTimeout(() => {
			this.saveState();
			this.updateFilterIndicator();
			this.loadDashboardData();
			this.dateSelectTimer = null;
		}, 220);
	}

	transformPythonData(flatData) {
		const zoneMap = {};

		flatData.forEach((row) => {
			const zoneName = row.zone;
			const categoryName = row.category;

			if (!zoneMap[zoneName]) {
				zoneMap[zoneName] = {
					zone: zoneName,
					branch_count: 0,
					dec: { tgt: 0, ach: 0, available: false },
					jan: { tgt: 0, ach: 0, available: false },
					feb: { tgt: 0, ach: 0, available: false },
					mar: { tgt: 0, ach: 0, available: false },
					total: { tgt: 0, ach: 0 },
					categories: {},
				};
			}

			if (!zoneMap[zoneName].categories[categoryName]) {
				zoneMap[zoneName].categories[categoryName] = {
					category: categoryName,
					branch_count: 0,
					dec: { tgt: 0, ach: 0, available: false },
					jan: { tgt: 0, ach: 0, available: false },
					feb: { tgt: 0, ach: 0, available: false },
					mar: { tgt: 0, ach: 0, available: false },
					total: { tgt: 0, ach: 0 },
				};
			}

			zoneMap[zoneName].branch_count += row.branch_count || 0;
			["dec", "jan", "feb", "mar"].forEach((month) => {
				zoneMap[zoneName][month].tgt += row[month].tgt || 0;
				zoneMap[zoneName][month].ach += row[month].ach || 0;
				if (row[month].available) {
					zoneMap[zoneName][month].available = true;
				}
			});
			zoneMap[zoneName].total.tgt += row.total.tgt || 0;
			zoneMap[zoneName].total.ach += row.total.ach || 0;

			const cat = zoneMap[zoneName].categories[categoryName];
			cat.branch_count += row.branch_count || 0;
			["dec", "jan", "feb", "mar"].forEach((month) => {
				cat[month].tgt += row[month].tgt || 0;
				cat[month].ach += row[month].ach || 0;
				if (row[month].available) {
					cat[month].available = true;
				}
			});
			cat.total.tgt += row.total.tgt || 0;
			cat.total.ach += row.total.ach || 0;
		});

		const zones = Object.values(zoneMap).map((zone) => ({
			...zone,
			categories: Object.values(zone.categories),
		}));

		const grand_total = {
			branch_count: 0,
			dec: { tgt: 0, ach: 0, available: false },
			jan: { tgt: 0, ach: 0, available: false },
			feb: { tgt: 0, ach: 0, available: false },
			mar: { tgt: 0, ach: 0, available: false },
			total: { tgt: 0, ach: 0 },
		};

		zones.forEach((zone) => {
			grand_total.branch_count += zone.branch_count;
			["dec", "jan", "feb", "mar"].forEach((month) => {
				grand_total[month].tgt += zone[month].tgt;
				grand_total[month].ach += zone[month].ach;
				if (zone[month].available) {
					grand_total[month].available = true;
				}
			});
			grand_total.total.tgt += zone.total.tgt;
			grand_total.total.ach += zone.total.ach;
		});

		return { zones, grand_total };
	}

	setupStyles() {
		const styles = `
            <style>
                /* Compact Timeline in Table Header */
                .compact-timeline {
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                }
                .timeline-dates-compact {
                    display: inline-flex;
                    gap: 4px;
                    overflow-x: auto;
                    max-width: 100%;
                    padding: 2px;
                }
                .timeline-dates-compact::-webkit-scrollbar {
                    height: 4px;
                }
                .timeline-dates-compact::-webkit-scrollbar-thumb {
                    background: rgba(0,0,0,0.2);
                    border-radius: 2px;
                }
                .timeline-date-compact {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-width: 42px;
                    padding: 4px 6px;
                    background: rgba(255,255,255,0.7);
                    border: 1.5px solid #cbd5e1;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .timeline-date-compact:hover {
                    background: white;
                    border-color: #94a3b8;
                    transform: translateY(-1px);
                }
                .timeline-date-compact.selected {
                    background: #000;
                    border-color: #000;
                    color: white;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                }
                .timeline-day-compact {
                    font-size: 8px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.3px;
                    opacity: 0.7;
                }
                .timeline-date-compact.selected .timeline-day-compact {
                    opacity: 1;
                }
                .timeline-num-compact {
                    font-size: 14px;
                    font-weight: 700;
                    line-height: 1;
                }

                /* Combined Filters */
                .combined-filters {
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 10px 14px;
                    margin-bottom: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                }
                .filter-section { margin-bottom: 8px; }
                .filter-section:last-child { margin-bottom: 0; }
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
                .filter-chips { display: flex; flex-wrap: wrap; gap: 6px; }
                .filter-chip {
                    padding: 6px 14px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    border: 2px solid transparent;
                    color: #1e293b;
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
                .filter-chip.active .chip-count { background: rgba(255, 255, 255, 0.3); }
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
                .active-filter-indicator.show { display: block; }
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

                /* Table Styles */
                .sahayog-content { position: relative; }
                .view-container { display: none; }
                .view-container.active { display: block; }

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
                .table-header-left, .table-header-right {
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

                /* Chart Visualize Button */
                .chart-visualize-wrapper { position: relative; }
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
                .chart-dropdown.show { display: block; }
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
                .chart-dropdown-item:last-child { border-bottom: none; }
                .chart-dropdown-item:hover {
                    background: #f8fafc;
                    color: #000;
                }
                .chart-dropdown-item i {
                    font-size: 14px;
                    width: 20px;
                    text-align: center;
                }
                .chart-dropdown-item.bar-chart i { color: #6366f1; }
                .chart-dropdown-item.bubble-chart i { color: #ec4899; }

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
                .chart-modal.show { display: flex; }
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
                .chart-modal-body { padding: 20px; }
                #chart-container { width: 100%; height: 500px; }

                .table-container-wrapper {
                    position: relative;
                    max-height: 600px;
                    overflow-y: auto;
                    background: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 0 0 6px 6px;
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
                .group-row {
                    background: var(--bg-light-gray);
                    font-weight: 600;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                .group-row:hover { background: var(--bg-color); }
                .collapse-icon {
                    display: inline-block;
                    margin-right: 8px;
                    transition: transform 0.2s;
                    color: #000;
                    font-size: 10px;
                }
                .group-row.collapsed .collapse-icon { transform: rotate(-90deg); }
                .child-row { transition: all 0.2s; }
                .child-row:hover {
                    transform: scale(1.002);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .child-row td.row-label {
                    padding-left: 36px;
                    font-weight: 600;
                }
                .child-row.hidden { display: none; }
                .child-row.filtered-out { display: none !important; }

                /* Category Colors */
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
                .na-text {
                    color: #94a3b8;
                    font-style: italic;
                    font-size: 11px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                }

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

                /* Drill-down Segment Styles */
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
                .drill-down-view.active { display: block; }
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

                /* Performance Segments */
                .segment-header-row {
                    font-weight: 700;
                    cursor: pointer;
                    transition: all 0.2s;
                    border-top: 2px solid #cbd5e1 !important;
                }
                .segment-header-row:hover { opacity: 0.9; }
                .segment-header-row td {
                    padding: 14px 16px !important;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    color: white !important;
                }
                .segment-header-row .collapse-icon {
                    display: inline-block;
                    margin-right: 10px;
                    transition: all 0.2s;
                    font-size: 14px;
                    width: 15px;
                    text-align: center;
                    color: white;
                }

                .segment-top {
                    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                    border-left: 5px solid #15803d !important;
                    box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
                }
                .segment-top:hover {
                    background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
                }

                .segment-next {
                    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
                    border-left: 5px solid #0369a1 !important;
                    box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3);
                }
                .segment-next:hover {
                    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
                }

                .segment-mid {
                    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                    border-left: 5px solid #b45309 !important;
                    box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
                }
                .segment-mid:hover {
                    background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
                }

                .segment-bottom {
                    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                    border-left: 5px solid #b91c1c !important;
                    box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
                }
                .segment-bottom:hover {
                    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                }

                .segment-child-1,
                .segment-child-2,
                .segment-child-3,
                .segment-child-4 {
                    transition: all 0.2s;
                }
                .segment-child-1:hover,
                .segment-child-2:hover,
                .segment-child-3:hover,
                .segment-child-4:hover {
                    transform: scale(1.001);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }

                .segment-child-1 {
                    background: linear-gradient(90deg, rgba(34, 197, 94, 0.05) 0%, transparent 100%);
                }
                .segment-child-2 {
                    background: linear-gradient(90deg, rgba(14, 165, 233, 0.05) 0%, transparent 100%);
                }
                .segment-child-3 {
                    background: linear-gradient(90deg, rgba(245, 158, 11, 0.05) 0%, transparent 100%);
                }
                .segment-child-4 {
                    background: linear-gradient(90deg, rgba(239, 68, 68, 0.05) 0%, transparent 100%);
                }

                @media (max-width: 768px) {
                    .table-header-controls { flex-direction: column; }
                }
            </style>
        `;
		$(styles).appendTo("head");
	}

	createCombinedFilters() {
		const filtersHtml = `
            <div class="combined-filters">
                <div class="filter-section">
                    <div class="filter-section-label">
                        <i class="fa fa-map-marker-alt" style="font-size: 9px;"></i> ZONE
                    </div>
                    <div class="filter-chips" id="zone-chips">
                        <div class="filter-chip active" data-zone="all">
                            All <span class="chip-count zone-count-all">0</span>
                        </div>
                    </div>
                </div>

                <div class="filter-section">
                    <div class="filter-section-label">
                        <i class="fa fa-layer-group" style="font-size: 9px;"></i> PERFORMANCE CATEGORIES
                    </div>
                    <div class="filter-chips">
                        <div class="filter-chip ${
							this.activeCategories.size === 0 ? "active" : ""
						}" data-category="all">
                            All <span class="chip-count" id="count-all">0</span>
                        </div>
                        <div class="filter-chip ${
							this.activeCategories.has("Pinacle") ? "active" : ""
						}" data-category="Pinacle">
                            Pinacle <span class="chip-count" id="count-pinacle">0</span>
                        </div>
                        <div class="filter-chip ${
							this.activeCategories.has("Master") ? "active" : ""
						}" data-category="Master">
                            Master <span class="chip-count" id="count-master">0</span>
                        </div>
                        <div class="filter-chip ${
							this.activeCategories.has("Accelerator") ? "active" : ""
						}" data-category="Accelerator">
                            Accelerator <span class="chip-count" id="count-accelerator">0</span>
                        </div>
                        <div class="filter-chip ${
							this.activeCategories.has("Starter") ? "active" : ""
						}" data-category="Starter">
                            Starter <span class="chip-count" id="count-starter">0</span>
                        </div>
                        <div class="filter-chip ${
							this.activeCategories.has("Learner") ? "active" : ""
						}" data-category="Learner">
                            Learner <span class="chip-count" id="count-learner">0</span>
                        </div>
                        <div class="filter-chip ${
							this.activeCategories.has("Zero Level") ? "active" : ""
						}" data-category="Zero Level">
                            Zero Level <span class="chip-count" id="count-zero">0</span>
                        </div>
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

		$(document).on("click", ".filter-chip[data-category] .chip-count", (e) => {
			e.stopPropagation();
			const chip = $(e.currentTarget).closest(".filter-chip");
			const category = chip.data("category");
			if (!category || category === "all") {
				frappe.show_alert({
					message: "Please select a specific category",
					indicator: "orange",
				});
				return;
			}
			this.openDrillDown("ALL", category);
		});

		$("#clear-all-filters").on("click", () => this.clearAllFilters());
	}

	loadZoneChips() {
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
		const parts = [];

		const selectedDateObj = this.availableDates.find((d) => d.date === this.selectedDate);
		if (selectedDateObj) {
			parts.push(`<span class="filter-badge">${selectedDateObj.display_full}</span>`);
		}

		if (this.activeZones.size > 0) {
			const zoneList = Array.from(this.activeZones).join(", ");
			parts.push(`Zones <span class="filter-badge">${zoneList}</span>`);
		}

		if (this.activeCategories.size > 0) {
			const catList = Array.from(this.activeCategories).join(", ");
			parts.push(`Categories <span class="filter-badge">${catList}</span>`);
		}

		if (parts.length > 0) {
			text.html(`Viewing ${parts.join(" • ")}`);
		} else {
			text.html(`Viewing <span class="filter-badge">ALL DATA</span>`);
		}
		indicator.addClass("show");
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
				if (!zoneMatch) return;

				if (!zoneCounts[zone.zone]) {
					zoneCounts[zone.zone] = 0;
				}
				zoneCounts[zone.zone] += zone.branch_count || 0;

				if (zone.categories) {
					zone.categories.forEach((cat) => {
						if (counts.hasOwnProperty(cat.category)) {
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
		$(".zone-count-all").text(counts["All"]);
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
		// Create chart modal HTML and attach handlers
		const modalHtml = `
            <div class="chart-modal" id="chart-modal">
                <div class="chart-modal-content">
                    <div class="chart-modal-header">
                        <div class="chart-modal-title"><i class="fa fa-chart-bar"></i> <span id="chart-modal-title">Chart</span></div>
                        <button class="chart-modal-close" id="chart-modal-close">Close</button>
                    </div>
                    <div class="chart-modal-body">
                        <div id="chart-container"></div>
                    </div>
                </div>
            </div>
        `;

		$("body").append(modalHtml);

		$("#chart-modal-close").on("click", () => this.closeChartModal());

		// Ensure chart resizes on window resize
		$(window).on("resize.sahayog_chart", () => {
			if (this.chartInstance && this.chartInstance.resize) {
				this.chartInstance.resize();
			}
		});
	}

	openChartModal(type) {
		$("#chart-modal").addClass("show");
		$("#chart-modal-title").text(
			type === "bar" ? "Bar Chart - Performance Overview" : "Bubble Chart - Zone vs Category"
		);
		// Wait until echarts loaded
		const render = () => {
			if (!window.echarts) {
				setTimeout(render, 150);
				return;
			}
			this.renderChart(type);
		};
		render();
	}

	closeChartModal() {
		$("#chart-modal").removeClass("show");
		if (this.chartInstance && this.chartInstance.dispose) {
			this.chartInstance.dispose();
			this.chartInstance = null;
		}
	}

	renderChart(type) {
		const container = document.getElementById("chart-container");
		if (!container) return;
		container.innerHTML = "";
		const chart = window.echarts.init(container);
		this.chartInstance = chart;

		if (!this.rawData) {
			chart.setOption({ title: { text: "No data" } });
			return;
		}

		if (type === "bar") {
			this.renderBarChart(chart);
		} else {
			this.renderBubbleChart(chart);
		}
	}

	renderBarChart(chart) {
		// Build series based on current grouping and active filters
		const groupBy = this.groupBy || "zone";
		const showAllZones = this.activeZones.size === 0;
		const showAllCategories = this.activeCategories.size === 0;

		const xLabels = [];
		const tgtSeries = [];
		const achSeries = [];

		if (groupBy === "zone") {
			this.rawData.zones.forEach((z) => {
				if (!showAllCategories) {
					// when categories filtered, sum only categories matching activeCategories
					let tgt = 0,
						ach = 0;
					z.categories.forEach((c) => {
						if (showAllCategories || this.activeCategories.has(c.category)) {
							tgt += c.total.tgt || 0;
							ach += c.total.ach || 0;
						}
					});
					xLabels.push(z.zone);
					tgtSeries.push(tgt);
					achSeries.push(ach);
				} else {
					xLabels.push(z.zone);
					tgtSeries.push(z.total.tgt || 0);
					achSeries.push(z.total.ach || 0);
				}
			});
		} else {
			// group by category
			const categoryOrder = [
				"Pinacle",
				"Master",
				"Accelerator",
				"Starter",
				"Learner",
				"Zero Level",
			];
			const categories = this.transformToCategoryGrouping(this.rawData);
			categories.forEach((c) => {
				xLabels.push(c.category);
				tgtSeries.push(c.total.tgt || 0);
				achSeries.push(c.total.ach || 0);
			});
		}

		const option = {
			title: { text: "Target vs Achievement" },
			tooltip: { trigger: "axis" },
			legend: { data: ["Target", "Achievement"] },
			toolbox: { feature: { saveAsImage: {} } },
			xAxis: { type: "category", data: xLabels },
			yAxis: { type: "value" },
			series: [
				{ name: "Target", type: "bar", data: tgtSeries, itemStyle: { color: "#60a5fa" } },
				{
					name: "Achievement",
					type: "bar",
					data: achSeries,
					itemStyle: { color: "#16a34a" },
				},
			],
		};

		chart.setOption(option);
	}

	renderBubbleChart(chart) {
		// X: zones, Y: categories, size: total achievement
		const zones = this.rawData.zones.map((z) => z.zone);
		const categoryOrder = [
			"Pinacle",
			"Master",
			"Accelerator",
			"Starter",
			"Learner",
			"Zero Level",
		];
		const dataPoints = [];

		this.rawData.zones.forEach((z, zi) => {
			z.categories.forEach((c) => {
				const size = c.total.ach || 0;
				const yi = categoryOrder.indexOf(c.category);
				if (yi >= 0) {
					dataPoints.push([zi, yi, Math.round(size / 1000)]);
				}
			});
		});

		const option = {
			title: { text: "Zone vs Category - Achievement" },
			xAxis: { type: "category", data: zones, name: "Zone" },
			yAxis: { type: "category", data: categoryOrder, name: "Category" },
			series: [
				{
					type: "scatter",
					symbolSize: function (data) {
						return Math.max(6, data[2]);
					},
					data: dataPoints,
					itemStyle: { color: "#ec4899" },
				},
			],
			tooltip: {
				formatter: function (params) {
					const zi = params.value[0];
					const yi = params.value[1];
					const size = params.value[2];
					return (
						zones[zi] +
						" / " +
						categoryOrder[yi] +
						"<br/>Achievement(≈): " +
						size * 1000
					);
				},
			},
		};

		chart.setOption(option);
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
					<div id="drill-segments-container"></div>
				</div>
			</div>
		`;

		$("body").append(drillHtml);

		$("#drill-close").on("click", () => this.closeDrillDown());
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
		if (!this.selectedDate) return;

		const container = $("#dashboard-view");
		container.html(`
            <div class="table-header-controls">
                <div class="table-header-left">
                    <div class="table-header-title">Performance Overview</div>
                </div>
                <div class="table-header-right">
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
                        <button class="chart-visualize-btn" id="chart-visualize-btn">📊 Visualize ▼</button>
                        <div class="chart-dropdown" id="chart-dropdown">
                            <div class="chart-dropdown-item bar-chart" data-chart="bar"><i>▦</i> Bar Chart</div>
                            <div class="chart-dropdown-item bubble-chart" data-chart="bubble"><i>●</i> Bubble Chart</div>
                        </div>
                    </div>
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

		// Insert compact timeline inline with the header controls (after grouping toggle)
		try {
			const groupingToggle = container.find(".grouping-toggle");
			if (groupingToggle.length) {
				groupingToggle.after(this.createCompactTimeline());
			}
		} catch (e) {
			console.error("Failed to insert timeline:", e);
		}

		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_dashboard_data",
			args: {
				selected_date: this.selectedDate,
			},
			callback: (r) => {
				if (r.message) {
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

		$("#toggle-all-rows")
			.off("click")
			.on("click", () => this.toggleAllRows());

		// Chart visualize dropdown
		$(document)
			.off("click.dashboard_chart")
			.on("click.dashboard_chart", (e) => {
				if (
					!$(e.target).closest(
						"#chart-visualize-btn, #chart-dropdown, .chart-visualize-wrapper"
					).length
				) {
					$("#chart-dropdown").removeClass("show");
				}
			});

		$("#chart-visualize-btn")
			.off("click")
			.on("click", (e) => {
				e.stopPropagation();
				$("#chart-dropdown").toggleClass("show");
			});

		$(".chart-dropdown-item")
			.off("click")
			.on("click", (e) => {
				const chart = $(e.currentTarget).data("chart");
				$("#chart-dropdown").removeClass("show");
				this.openChartModal(chart);
			});
	}

	switchGrouping(group) {
		this.groupBy = group;
		$(".grouping-btn").removeClass("active");
		$(`.grouping-btn[data-group="${group}"]`).addClass("active");
		this.saveState();
		this.loadDashboardData();
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

			const sortedZones = cat.zones.sort((a, b) => a.zone.localeCompare(b.zone));
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
				dec: { tgt: 0, ach: 0, available: false },
				jan: { tgt: 0, ach: 0, available: false },
				feb: { tgt: 0, ach: 0, available: false },
				mar: { tgt: 0, ach: 0, available: false },
				total: { tgt: 0, ach: 0 },
				zones: [],
			};
		});

		data.zones.forEach((zone) => {
			zone.categories.forEach((cat) => {
				if (categoryMap[cat.category]) {
					categoryMap[cat.category].branch_count += cat.branch_count || 0;
					["dec", "jan", "feb", "mar"].forEach((month) => {
						categoryMap[cat.category][month].tgt += cat[month].tgt || 0;
						categoryMap[cat.category][month].ach += cat[month].ach || 0;
						if (cat[month].available) {
							categoryMap[cat.category][month].available = true;
						}
					});
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
                <td>${this.formatTgtAch(total.dec)}</td>
                <td>${this.formatTgtAch(total.jan)}</td>
                <td>${this.formatTgtAch(total.feb)}</td>
                <td>${this.formatTgtAch(total.mar)}</td>
                <td>${this.formatTgtAch(total.total)}</td>
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

	/**
	 * Format Target/Achievement cell.
	 * If data.available is false, show "N/A" for achievement.
	 */
	formatTgtAch(data) {
		if (!data) {
			return `<div class="tgt-ach-cell"><span class="na-text">N/A</span></div>`;
		}

		const tgt = data.tgt || 0;
		const ach = data.ach || 0;
		const available = data.available || false;

		if (!available) {
			// Future month - show target but N/A for achievement
			return `
                <div class="tgt-ach-cell">
                    <div class="tgt-line">T: ${this.formatNumber(tgt)}</div>
                    <div class="na-text">A: N/A</div>
                </div>
            `;
		}

		// Current/past month - show both target and achievement
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

		$(".group-row td:nth-child(2)")
			.off("click")
			.on("click", (e) => {
				e.stopPropagation();
				if (this.groupBy === "category") {
					const groupRow = $(e.currentTarget).closest("tr");
					const category = groupRow
						.find(".row-label")
						.clone()
						.children()
						.remove()
						.end()
						.text()
						.trim();
					if (category) {
						this.openDrillDown("ALL", category);
					}
				}
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

	openDrillDown(zone, category) {
		this.currentZone = zone;
		this.currentCategory = category;

		const titleText = zone === "ALL" ? `${category} - All Zones` : `${zone} - ${category}`;
		$("#drill-title").text(titleText);
		$("#drill-down-view").addClass("active");
		$(
			".timeline-container, .combined-filters, .active-filter-indicator, .sahayog-content"
		).hide();

		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_drill_down_data",
			args: {
				zone: zone,
				category: category,
				selected_date: this.selectedDate,
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
		$(
			".timeline-container, .combined-filters, .active-filter-indicator, .sahayog-content"
		).show();
	}

	renderDrillDown(branches) {
		const container = $("#drill-segments-container");
		container.empty();

		if (!branches || branches.length === 0) {
			container.html(
				`<div style="text-align:center; padding:40px;">No branches found</div>`
			);
			return;
		}

		// Compute ach_pct for each branch if not provided
		branches.forEach((b) => {
			const yearly = b.yearly_target || 0;
			const totalAch = b.total_ach || 0;
			let pct = 0;
			if (yearly > 0) {
				pct = (totalAch / yearly) * 100;
			}
			b.ach_pct = b.ach_pct !== undefined ? b.ach_pct : pct;
		});

		// Segment buckets
		const segments = [
			{ key: "TOP", range: [75, 100], class: "segment-child-1", colorClass: "segment-top" },
			{ key: "NEXT", range: [50, 75], class: "segment-child-2", colorClass: "segment-next" },
			{ key: "MID", range: [25, 50], class: "segment-child-3", colorClass: "segment-mid" },
			{
				key: "BOTTOM",
				range: [0, 25],
				class: "segment-child-4",
				colorClass: "segment-bottom",
			},
		];

		segments.forEach((seg, idx) => {
			const items = branches.filter((b) => {
				const p = b.ach_pct || 0;
				return p >= seg.range[0] && p <= seg.range[1];
			});

			// Sort descending by ach_pct
			items.sort((a, b) => (b.ach_pct || 0) - (a.ach_pct || 0));

			// Header
			const header = $(
				`<div class="table-container" style="margin-bottom:8px;">
					<table class="sahayog-table segment-header-row ${seg.colorClass}">
						<thead>
							<tr>
								<td class="row-label" style="text-align:left;">
									<span class="collapse-icon">&#9658;</span> ${seg.key} (${items.length} branches)
								</td>
								<td style="text-align:right">Zone</td>
								<td style="text-align:right">SOL</td>
								<td style="text-align:right">Region</td>
								<td style="text-align:right">District</td>
								<td style="text-align:right">DEC-25</td>
								<td style="text-align:right">JAN-26</td>
								<td style="text-align:right">FEB-26</td>
								<td style="text-align:right">MAR-26</td>
								<td style="text-align:right">Total</td>
							</tr>
						</thead>
					</table>
					<div class="segment-children ${seg.class}" style="display:none;"></div>
				</div>`
			);

			container.append(header);

			const childrenContainer = container.find(".segment-children").last();
			if (items.length === 0) {
				childrenContainer.append(
					`<div style="padding:14px; text-align:center;">No branches in this segment</div>`
				);
			} else {
				// Build rows
				items.forEach((b) => {
					childrenContainer.append(`
						<div class="child-row ${
							seg.class
						}" style="display:flex; align-items:center; gap:8px; padding:10px 14px;">
							<div style="flex:1; text-align:left; font-weight:600;">${
								b.branch || b.branch_name
							} <span style="background:rgba(0,0,0,0.06); padding:2px 8px; border-radius:8px; font-size:11px; font-weight:700; margin-left:8px;">${(
						b.ach_pct || 0
					).toFixed(1)}%</span></div>
							<div style="width:80px; text-align:right">${b.zone}</div>
							<div style="width:80px; text-align:right">${b.sol_id || ""}</div>
							<div style="width:120px; text-align:right">${b.region || ""}</div>
							<div style="width:120px; text-align:right">${b.district || ""}</div>
							<div style="width:120px; text-align:right">${this.formatTgtAch(b.dec)}</div>
							<div style="width:120px; text-align:right">${this.formatTgtAch(b.jan)}</div>
							<div style="width:120px; text-align:right">${this.formatTgtAch(b.feb)}</div>
							<div style="width:120px; text-align:right">${this.formatTgtAch(b.mar)}</div>
							<div style="width:120px; text-align:right">${this.formatTgtAch(
								b.total || {
									tgt: b.yearly_target,
									ach: b.total_ach,
									available: true,
								}
							)}</div>
						</div>
					`);
				});
			}

			// Toggle on header click
			header.find(".segment-header-row").on("click", function () {
				const icon = $(this).find(".collapse-icon");
				const segChildren = $(this).next(".segment-children");
				if (segChildren.is(":visible")) {
					segChildren.slideUp(150);
					icon.html("&#9658;");
				} else {
					segChildren.slideDown(150);
					icon.html("&#9662;");
				}
			});
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
			args: { selected_date: this.selectedDate },
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
				`<tr><td colspan="4" style="text-align:center; padding:40px;">No targets found</td></tr>`
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
