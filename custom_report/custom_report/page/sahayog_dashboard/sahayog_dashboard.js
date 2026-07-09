// ============================================================================
// DRISHTI PERFORMANCE DASHBOARD - COMPLETE FUNCTIONAL VERSION
// Version: 6.0.0 | All Issues Fixed
// ============================================================================

const getRemainingWorkingDaysExcludingSundays = (year, monthIndex, currentDay) => {
	const lastDayOfMonth = new Date(year, monthIndex + 1, 0).getDate();
	let workingDays = 0;
	for (let day = currentDay; day <= lastDayOfMonth; day++) {
		const date = new Date(year, monthIndex, day);
		if (date.getDay() !== 0) { // 0 represents Sunday
			workingDays++;
		}
	}
	return workingDays;
};

frappe.pages["sahayog_dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Drishti",
		single_column: true,
	});

	// Style the title heading dynamically with bold styling
	$(wrapper).find(".title-text").html('<span style="font-weight: 800; color: #417d81; font-size: 24px; letter-spacing: -0.5px; font-family: \'Inter\', sans-serif;">Drishti</span>');
	$(wrapper).find(".title-text").after('<div id="drishti-subtitle" style="font-size: 12px; color: #64748b; margin-top: 4px; font-weight: 500; font-family: \'Inter\', sans-serif;">Updated till: Loading...</div>');

	wrapper.dashboard = new DrishtiDashboard(page);
};

frappe.pages["sahayog_dashboard"].on_page_show = function (wrapper) {
	// Inject Drishti title
	document.title = "Drishti";
	if ($("head title").length) {
		$("head title").text("Drishti");
	} else {
		$("<title>Drishti</title>").appendTo("head");
	}

	// Fetch and update latest date subtitle
	frappe.call({
		method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_latest_branch_category_report_date",
		callback: function (r) {
			if (r.message) {
				const dateParts = r.message.split("-");
				const formattedDate = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}`;
				$(wrapper).find("#drishti-subtitle").text("Updated till: " + formattedDate);
			} else {
				$(wrapper).find("#drishti-subtitle").text("");
			}
		}
	});

	// Clean up any old unmanaged container style tags from previous development sessions
	$("head style").each(function() {
		const text = $(this).text();
		if (text.includes(".container") && text.includes("max-width: 100%") && !text.includes(".sahayog-dashboard-full-width")) {
			$(this).remove();
		}
	});

	// Add full width class to body for page-specific styling
	$("body").addClass("sahayog-dashboard-full-width");

	// Inject custom breadcrumbs with live timer
	setTimeout(() => {
		const $breadcrumbs = $("#navbar-breadcrumbs");
		if ($breadcrumbs.length) {
			$breadcrumbs.html(`
				<li><a href="/app/sahayog-home" class="btn btn-default btn-xs" style="font-weight: 700; border-radius: 6px; padding: 2px 8px; color: #1e293b; border: 1px solid #cbd5e1; background-color: #f1f5f9; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); margin-right: 4px;">Back</a></li>
				<li style="display: inline-flex; align-items: center;">
					<!-- Working Days Left -->
					<div style="display: inline-flex; align-items: center; margin-left: 10px; vertical-align: middle;">
						<span id="drishti-header-timer" class="days-left-blink" style="font-size: 12px;"></span>
					</div>
				</li>
			`);

			// Set initial format toggle state from URL or state default
			const urlParams = new URLSearchParams(window.location.search);
			const formatMode = urlParams.get("formatMode") || "words";
			$breadcrumbs
				.find(`.format-toggle-btn[data-format="${formatMode}"]`)
				.addClass("active");

			// Repopulate headers if dashboard instance exists
			if (wrapper.dashboard) {
				wrapper.dashboard.repopulateHeaderFilters();
				wrapper.dashboard.setupHeaderToggle();
			}

			// Clear any existing interval
			if (frappe.pages["sahayog_dashboard"].timer_interval) {
				clearInterval(frappe.pages["sahayog_dashboard"].timer_interval);
				frappe.pages["sahayog_dashboard"].timer_interval = null;
			}

			const updateDrishtiTimer = () => {
				const $timer = $("#drishti-live-timer");
				if ($timer.length) {
					$timer.hide();
				}

				const $headerTimer = $("#drishti-header-timer");
				if ($headerTimer.length) {
					const now = new Date();
					const year = now.getFullYear();
					const currentMonthIndex = now.getMonth();
					const currentDay = now.getDate();

					const workingDaysLeft = getRemainingWorkingDaysExcludingSundays(year, currentMonthIndex, currentDay);
					const daysLeftText = workingDaysLeft === 1 ? "1 Working Day Left" : `${workingDaysLeft} Working Days Left`;

					$headerTimer.html(daysLeftText);
				}
			};

			updateDrishtiTimer();
		}
	}, 100);
};

frappe.pages["sahayog_dashboard"].on_page_hide = function (wrapper) {
	// Remove full width class from body
	$("body").removeClass("sahayog-dashboard-full-width");

	// Clear interval to avoid memory leaks
	if (frappe.pages["sahayog_dashboard"].timer_interval) {
		clearInterval(frappe.pages["sahayog_dashboard"].timer_interval);
		frappe.pages["sahayog_dashboard"].timer_interval = null;
	}
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
			selectedRegions: [],
			branchSearchTerm: "",
			selectedMonth: null,
			drillDownActive: false,
			expandedZones: {}, // Track expanded/collapsed zones
			selectedSegment: "all",
			dashboardMode: "drishti",
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

		// Registered MIS Reports configuration
		this.misReportsList = [
			{
				id: "rd_smbg_pending",
				name: "RD & SMBG Pending",
				tableData: [],
				expandedZones: {},
			expandedRegions: {},
			checkedRows: {},
			searchTerm: "",
			allExpanded: false,
			selectedMisZones: [],
				render: function(container, dashboardInstance) {
					const self = this;
					container.html(`
						<div style="display: flex; justify-content: center; align-items: center; min-height: 200px; width: 100%;" id="mis-loading"${self.tableData ? ' style="display: none;"' : ""}>
							<div class="spinner-border text-primary" role="status" style="width: 1.5rem; height: 1.5rem; border-width: 0.2em; animation: spinner-border .75s linear infinite;"></div>
							<span style="margin-left: 10px; font-weight: 600; color: #475569; font-size: 14px; font-family: 'Inter', sans-serif;">Loading RD & SMBG Pending data...</span>
						</div>
						<div id="mis-kpi-container"${self.tableData && self.tableData.length ? "" : ' style="display: none;"'}></div>
						<div style="display: flex; gap: 8px; align-items: center; margin-bottom: 10px;" id="mis-controls"${self.tableData && self.tableData.length ? "" : ' style="display: none;"'}>
							<div style="display: flex; align-items: center; gap: 6px;">
								<span style="font-weight: bold; color: #0d1b2a; font-size: 13px; white-space: nowrap;">Format:</span>
								<div class="btn-group mis-format-toggle" role="group">
									<button type="button" class="btn btn-sm mis-format-btn ${dashboardInstance.state.formatMode === 'number' ? 'active' : ''}" data-format="number" style="background: ${dashboardInstance.state.formatMode === 'number' ? '#417d81' : '#e2e8f0'}; color: ${dashboardInstance.state.formatMode === 'number' ? 'white' : '#475569'}; border: none; padding: 4px 10px; font-size: 12px; font-weight: 600; border-radius: 4px 0 0 4px; cursor: pointer;">Numbers</button>
									<button type="button" class="btn btn-sm mis-format-btn ${dashboardInstance.state.formatMode === 'words' ? 'active' : ''}" data-format="words" style="background: ${dashboardInstance.state.formatMode === 'words' ? '#417d81' : '#e2e8f0'}; color: ${dashboardInstance.state.formatMode === 'words' ? 'white' : '#475569'}; border: none; padding: 4px 10px; font-size: 12px; font-weight: 600; border-radius: 0 4px 4px 0; cursor: pointer;">Words</button>
								</div>
							</div>
							<input type="text" id="mis-search" placeholder="Search branch or SOL ID..." style="padding: 5px 10px; border: 1px solid #cbd5e1; border-radius: 4px; min-width: 200px; background: white; color: #1b263b; font-size: 13px; outline: none;">
							<button type="button" id="mis-expand-toggle" style="background: #e2e8f0; color: #475569; border: none; padding: 4px 10px; font-size: 12px; font-weight: 600; border-radius: 4px; cursor: pointer; white-space: nowrap;">▼ Expand All</button>
							<button type="button" id="mis-refetch" style="background: #e2e8f0; color: #475569; border: none; padding: 4px 10px; font-size: 12px; font-weight: 600; border-radius: 4px; cursor: pointer; white-space: nowrap;">⟳ Refetch</button>
							<div style="margin-left: auto; font-size: 13px; font-weight: 700; color: #417d81; background: rgba(65,125,129,0.08); padding: 6px 12px; border-radius: 6px;" id="mis-records-count"></div>
						</div>
						<div id="mis-zone-filter-row" style="display: none; margin-bottom: 10px;"></div>
						<div id="mis-table-container"${self.tableData ? "" : ' style="display: none;"'}></div>
					`);

					// If data already fetched, just re-render
					if (self.tableData && self.tableData.length > 0) {
						self.renderKPI(container.find("#mis-kpi-container"), dashboardInstance);
						container.find("#mis-records-count").text(`${self.tableData.length} branches`);
						self.renderMisTable(container.find("#mis-table-container"), dashboardInstance);
						self.renderZoneFilterTags(container, dashboardInstance);
						container.find("#mis-controls, #mis-table-container, #mis-kpi-container").show();
						container.find("#mis-loading").hide();
						self.attachReportEventHandlers(container, dashboardInstance);
						return;
					}

					let dataLoaded = 0;
					function checkLoaded() {
						dataLoaded++;
						if (dataLoaded >= 1) {
							container.find("#mis-loading").hide();
container.find("#mis-controls, #mis-table-container, #mis-kpi-container, #mis-zone-filter-row").show();
						}
					}

					// Fetch permissions and data in parallel
					frappe.call({
						method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_mis_filter_options",
						callback: function(r) {
							if (r.message) {
								self.filterOptions = r.message;
								const perms = r.message.permissions || {};
								console.log("Report Preference zones:", r.message.zones);
								console.log("Report Preference regions:", r.message.regions);
								console.log("Permissions:", perms);
								const solData = r.message.sol_data || [];
								// If zone permissions exist, use zones as primary filter — ignore sol_ids
								const useSolIds = (!r.message.zones || r.message.zones.length === 0) && perms.allowed_sol_ids && perms.allowed_sol_ids.length > 0;
								const solIds = useSolIds ? perms.allowed_sol_ids.join(",") : "";

								const cacheKey = "rd_smbg_cache_" + (solIds || "all");
								const cached = localStorage.getItem(cacheKey);

								if (cached) {
									try {
										const parsed = JSON.parse(cached);
										const age = Date.now() - parsed.timestamp;
										if (age < 3600000) {
											// Cache hit — use it, filter by permitted zones
											let data = parsed.tableData;
											const pz = self.filterOptions && self.filterOptions.zones;
											if (pz && pz.length > 0) {
												data = data.filter(r => pz.includes(r.zone));
											}
											self.tableData = data;
											self.renderKPI(container.find("#mis-kpi-container"), dashboardInstance);
											container.find("#mis-records-count").text(`${data.length} branches`);
											self.renderMisTable(container.find("#mis-table-container"), dashboardInstance);
											self.renderZoneFilterTags(container, dashboardInstance);
											checkLoaded();
											return;
										}
										// Expired cache — delete it
										localStorage.removeItem(cacheKey);
									} catch(e) {
										localStorage.removeItem(cacheKey);
									}
								}

								frappe.call({
									method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_rd_smbg_pending_table_data",
									args: { sol_ids: solIds },
									callback: function(r3) {
										if (r3.message) {
											let data = r3.message;
											const pz = self.filterOptions && self.filterOptions.zones;
											if (pz && pz.length > 0) {
												data = data.filter(r => pz.includes(r.zone));
											}
											self.tableData = data;
											self.renderKPI(container.find("#mis-kpi-container"), dashboardInstance);
											container.find("#mis-records-count").text(`${data.length} branches`);
											self.renderMisTable(container.find("#mis-table-container"), dashboardInstance);
											self.renderZoneFilterTags(container, dashboardInstance);
											// Cache
											setTimeout(function() {
												if (self.tableData) {
													localStorage.setItem(cacheKey, JSON.stringify({
														timestamp: Date.now(),
														tableData: self.tableData,
														solIds: solIds
													}));
												}
											}, 500);
										}
										checkLoaded();
									}
								});
							}
						}
					});
					
					self.attachReportEventHandlers(container, dashboardInstance);
				},
				attachReportEventHandlers: function(container, dashboardInstance) {
					const self = this;
					container.off("click", ".mis-format-btn").on("click", ".mis-format-btn", function() {
						const format = $(this).data("format");
						dashboardInstance.state.formatMode = format;
						container.find(".mis-format-btn").each(function() {
							const btn = $(this);
							const isActive = btn.data("format") === format;
							btn.css("background", isActive ? "#417d81" : "#e2e8f0");
							btn.css("color", isActive ? "white" : "#475569");
						});
						if (self.tableData && self.tableData.length > 0) {
							self.switchFormat(format, container, dashboardInstance);
						}
					});

					let searchTimeout;
					container.off("input", "#mis-search").on("input", "#mis-search", function() {
						clearTimeout(searchTimeout);
						searchTimeout = setTimeout(() => {
							self.searchTerm = $(this).val().toLowerCase().trim();
							if (self.tableData) {
								self.renderMisTable(container.find("#mis-table-container"), dashboardInstance);
							}
						}, 300);
					});

					container.off("click", "#mis-expand-toggle").on("click", "#mis-expand-toggle", function() {
						self.allExpanded = !self.allExpanded;
						const expand = self.allExpanded;
						if (!self.tableData) return;
						const zoneData = self.aggregateByZone();
						zoneData.forEach(z => {
							self.expandedZones[z.zone] = expand;
							z.regions.forEach(r => {
								self.expandedRegions[z.zone + "::" + r.region] = expand;
							});
						});
						$(this).text(expand ? "▲ Collapse All" : "▼ Expand All");
						self.renderMisTable(container.find("#mis-table-container"), dashboardInstance);
					});

					container.off("click", "#mis-refetch").on("click", "#mis-refetch", function() {
						self.refetchData(container, dashboardInstance);
					});
				},
				renderKPI: function(container, dashboardInstance) {
					const self = this;
					const data = self.tableData || [];
					const totalAccounts = data.reduce((s, r) => s + (r.total_accounts || 0), 0);
					const totalCollection = data.reduce((s, r) => s + (r.total_collection || 0), 0);
					const pendingAccounts = data.reduce((s, r) => s + (r.pending_accounts || 0), 0);
					const pendingInstalments = data.reduce((s, r) => s + (r.pending_instalments || 0), 0);
					const pendingAmount = data.reduce((s, r) => s + (r.pending_amount || 0), 0);

					const formatCount = (val) => {
						if (!val && val !== 0) return "0";
						return new Intl.NumberFormat("en-IN").format(val);
					};
					const formatAmount = (val) => {
						if (!val || val === 0) return "₹0";
						return "₹" + dashboardInstance.formatCurrency(val);
					};

					const kpiCards = [
						{ label: "Total Accounts", value: formatCount(totalAccounts), color: "#3b82f6", bg: "#eff6ff", icon: "📊" },
						{ label: "Total Collection", value: formatAmount(totalCollection), color: "#10b981", bg: "#ecfdf5", icon: "💰" },
						{ label: "Pending Accounts", value: formatCount(pendingAccounts), color: "#f59e0b", bg: "#fffbeb", icon: "⏳" },
						{ label: "Pending Instalments", value: formatCount(pendingInstalments), color: "#f97316", bg: "#fff7ed", icon: "📅" },
						{ label: "Pending Amount", value: formatAmount(pendingAmount), color: "#ef4444", bg: "#fef2f2", icon: "🔴" }
					];

					const cardsHtml = kpiCards.map(card => `
						<div class="kpi-card" style="background: ${card.bg}; border-left: 4px solid ${card.color};">
							<div class="kpi-card-header">
								<span class="kpi-icon">${card.icon}</span>
								<span class="kpi-label">${card.label}</span>
							</div>
							<div class="kpi-value" style="color: ${card.color};">${card.value}</div>
						</div>
					`).join('');

					container.html(`
						<style>
							#mis-kpi-container { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 18px; }
							#mis-kpi-container .kpi-card {
								flex: 1 1 180px;
								min-width: 150px;
								border-radius: 10px;
								padding: 16px 18px;
								box-shadow: 0 2px 4px rgba(0,0,0,0.04);
								box-sizing: border-box;
								min-height: 100px;
							}
							#mis-kpi-container .kpi-card-header {
								display: flex;
								align-items: center;
								gap: 10px;
								margin-bottom: 10px;
							}
							#mis-kpi-container .kpi-icon { font-size: 20px; flex-shrink: 0; line-height: 1; }
							#mis-kpi-container .kpi-label {
								font-size: 12px;
								font-weight: 600;
								color: #64748b;
								text-transform: uppercase;
								letter-spacing: 0.5px;
								font-family: 'Inter', sans-serif;
								white-space: nowrap;
								overflow: hidden;
								text-overflow: ellipsis;
							}
							#mis-kpi-container .kpi-value {
								font-size: clamp(18px, 2.2vw, 24px);
								font-weight: 800;
								font-family: 'Inter', sans-serif;
								line-height: 1.2;
								word-break: break-word;
							}
							@media (max-width: 768px) {
								#mis-kpi-container .kpi-card { flex: 1 1 140px; min-width: 120px; padding: 12px 14px; min-height: 80px; }
								#mis-kpi-container .kpi-value { font-size: 16px; }
							}
							@media (max-width: 480px) {
								#mis-kpi-container .kpi-card { flex: 1 1 100%; min-width: unset; }
							}
						</style>
						${cardsHtml}
					`);
				},
				refetchData: function(container, dashboardInstance) {
					const self = this;
					// Clear all rd_smbg cache keys from localStorage
					Object.keys(localStorage).forEach(key => {
						if (key.startsWith("rd_smbg_cache_")) {
							localStorage.removeItem(key);
						}
					});
					// Reset state
					self.tableData = [];
					self.filterOptions = null;
					self.selectedMisZones = [];
					self.expandedZones = {};
					self.expandedRegions = {};
					self.checkedRows = {};
					self.searchTerm = "";
					self.allExpanded = false;
					// Re-render which will re-fetch from APIs
					self.render(container, dashboardInstance);
				},
				switchFormat: function(format, container, dashboardInstance) {
					const self = this;
					if (self.tableData && self.tableData.length > 0) {
						const tableContainer = container.find("#mis-table-container");
						self.renderMisTable(tableContainer, dashboardInstance);
						self.renderZoneFilterTags(container, dashboardInstance);
					}
					self.renderKPI(container.find("#mis-kpi-container"), dashboardInstance);
				},
				renderMisTable: function(tableContainer, dashboardInstance) {
					const self = this;
					self.renderAnalysisTable(tableContainer, dashboardInstance);
				},
				renderZoneFilterTags: function(container, dashboardInstance) {
					const self = this;
					if (!self.tableData || self.tableData.length === 0) {
						container.find("#mis-zone-filter-row").hide();
						return;
					}
					// Use permitted zones from Report Preference
					const permittedZones = (self.filterOptions && self.filterOptions.zones) || [];
					let zones = permittedZones.length > 0 ? permittedZones : [...new Set(self.tableData.map(r => r.zone).filter(Boolean))].sort();
					console.log("MIS zone filter zones:", zones);
					if (zones.length === 0) {
						container.find("#mis-zone-filter-row").hide();
						return;
					}
					const allSelected = self.selectedMisZones.length === 0;
					let html = '<span style="font-weight: 600; color: #475569; font-size: 13px; white-space: nowrap;">Zone:</span>';
					html += `<button class="mis-zone-filter-tag ${allSelected ? "active" : ""}" data-zone="all" style="padding: 4px 12px; font-size: 12px; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 9999px; background: ${allSelected ? "#417d81" : "#fff"}; color: ${allSelected ? "#fff" : "#475569"}; cursor: pointer; transition: all 0.2s;">All</button>`;
					zones.forEach(zone => {
						const active = self.selectedMisZones.includes(zone);
						html += `<button class="mis-zone-filter-tag ${active ? "active" : ""}" data-zone="${zone}" style="padding: 4px 12px; font-size: 12px; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 9999px; background: ${active ? "#417d81" : "#fff"}; color: ${active ? "#fff" : "#475569"}; cursor: pointer; transition: all 0.2s;">${zone}</button>`;
					});
					const $row = container.find("#mis-zone-filter-row");
					$row.html(html).css("display", "flex").css({ "align-items": "center", "gap": "8px", "flex-wrap": "wrap", "margin-bottom": "10px" });

					container.off("click", ".mis-zone-filter-tag").on("click", ".mis-zone-filter-tag", function() {
						const zone = $(this).data("zone");
						if (zone === "all") {
							self.selectedMisZones = [];
						} else {
							const idx = self.selectedMisZones.indexOf(zone);
							if (idx > -1) {
								self.selectedMisZones.splice(idx, 1);
							} else {
								self.selectedMisZones.push(zone);
							}
						}
						self.renderZoneFilterTags(container, dashboardInstance);
						self.renderMisTable(container.find("#mis-table-container"), dashboardInstance);
					});
				},
				aggregateByZone: function() {
					const self = this;
					let data = self.tableData || [];
					const term = (self.searchTerm || "").trim();
					if (term) {
						const terms = term.split(",").map(t => t.trim().toLowerCase()).filter(t => t);
						data = data.filter(row => {
							const br = (row.branch_name || row.sol_desc || "").toLowerCase();
							const id = (row.sol_id || "").toLowerCase();
							return terms.some(t => br.includes(t) || id.includes(t));
						});
					}
					if (self.selectedMisZones && self.selectedMisZones.length > 0) {
						data = data.filter(row => self.selectedMisZones.includes(row.zone));
					}
					const zoneMap = {};

					data.forEach(row => {
						const zone = row.zone || "Unknown";
						const region = row.region || "Unknown";
						if (!zoneMap[zone]) {
							zoneMap[zone] = { zone, regions: {}, branches: [], total_accounts: 0, total_collection: 0, pending_accounts: 0, pending_amount: 0, pending_instalments: 0 };
						}
						if (!zoneMap[zone].regions[region]) {
							zoneMap[zone].regions[region] = { region, branches: [], total_accounts: 0, total_collection: 0, pending_accounts: 0, pending_amount: 0, pending_instalments: 0 };
						}
						zoneMap[zone].branches.push(row);
						zoneMap[zone].regions[region].branches.push(row);
						zoneMap[zone].total_accounts += row.total_accounts;
						zoneMap[zone].total_collection += row.total_collection;
						zoneMap[zone].pending_accounts += row.pending_accounts;
						zoneMap[zone].pending_amount += row.pending_amount;
						zoneMap[zone].pending_instalments += row.pending_instalments;
						zoneMap[zone].regions[region].total_accounts += row.total_accounts;
						zoneMap[zone].regions[region].total_collection += row.total_collection;
						zoneMap[zone].regions[region].pending_accounts += row.pending_accounts;
						zoneMap[zone].regions[region].pending_amount += row.pending_amount;
						zoneMap[zone].regions[region].pending_instalments += row.pending_instalments;
					});

					const sortedZones = Object.keys(zoneMap).sort((a, b) => {
						const numA = parseInt(a.replace(/\D/g, "")) || 0;
						const numB = parseInt(b.replace(/\D/g, "")) || 0;
						return numA - numB;
					});

					const result = [];
					sortedZones.forEach(zoneName => {
						const zd = zoneMap[zoneName];
						const sortedRegions = Object.keys(zd.regions).sort((a, b) => {
							const numA = parseInt(a.replace(/\D/g, "")) || 0;
							const numB = parseInt(b.replace(/\D/g, "")) || 0;
							return numA - numB;
						});
						const regions = sortedRegions.map(rn => zd.regions[rn]);
						result.push({ zone: zoneName, data: zd, regions });
					});
					return result;
				},
				renderAnalysisTable: function(tableContainer, dashboardInstance) {
					const self = this;
					const format = dashboardInstance.state.formatMode || "number";

					const fmtCount = (val) => {
						if (!val && val !== 0) return "0";
						if (format === "words") {
							if (val >= 10000000) return (val / 10000000).toFixed(2) + " Cr";
							if (val >= 100000) return (val / 100000).toFixed(2) + " L";
							if (val >= 1000) return (val / 1000).toFixed(2) + " K";
							return new Intl.NumberFormat("en-IN").format(val);
						}
						return new Intl.NumberFormat("en-IN").format(val);
					};
					const fmtAmt = (val) => {
						if (!val || val === 0) return "₹0";
						if (format === "words") {
							if (val >= 10000000) return "₹" + (val / 10000000).toFixed(2) + " Cr";
							if (val >= 100000) return "₹" + (val / 100000).toFixed(2) + " L";
							if (val >= 1000) return "₹" + (val / 1000).toFixed(2) + " K";
							return "₹" + new Intl.NumberFormat("en-IN").format(val);
						}
						return "₹" + new Intl.NumberFormat("en-IN").format(Math.round(val));
					};

					const zoneData = self.aggregateByZone();
					const totalFilteredBranches = zoneData.reduce((s, z) => s + z.data.branches.length, 0);
					const totalAllBranches = (self.tableData || []).length;
					tableContainer.parent().find("#mis-records-count").text(totalFilteredBranches + " / " + totalAllBranches + " branches" + (self.searchTerm ? " (filtered)" : ""));
					if (!zoneData || zoneData.length === 0) {
						tableContainer.html('<div style="padding: 30px; text-align: center; color: #64748b; font-weight: 600; font-family: \'Inter\', sans-serif;">No data to display.</div>');
						return;
					}

					const grandTotal = { total_accounts: 0, total_collection: 0, pending_accounts: 0, pending_amount: 0, pending_instalments: 0 };
					zoneData.forEach(z => {
						grandTotal.total_accounts += z.data.total_accounts;
						grandTotal.total_collection += z.data.total_collection;
						grandTotal.pending_accounts += z.data.pending_accounts;
						grandTotal.pending_amount += z.data.pending_amount;
						grandTotal.pending_instalments += z.data.pending_instalments;
					});

					const metricCols = [
						{ key: "total_accounts", label: "Total Accounts", align: "right", fmt: fmtCount },
						{ key: "total_collection", label: "Total Collection", align: "right", fmt: fmtAmt },
						{ key: "pending_accounts", label: "Pending Accounts", align: "right", fmt: fmtCount },
						{ key: "pending_instalments", label: "Pending Instalments", align: "right", fmt: fmtCount },
						{ key: "pending_amount", label: "Pending Amount", align: "right", fmt: fmtAmt }
					];

					let sr = 0;
					let rowsHtml = "";

					zoneData.forEach(z => {
						sr++;
						const zoneExpanded = self.expandedZones[z.zone];
						const zoneRow = z.data;
						const zoneChecked = self.checkedRows["zone::" + z.zone];
						rowsHtml += `<tr class="mis-zone-row${zoneChecked ? " mis-row-checked" : ""}" data-zone="${z.zone}" data-check-id="zone::${z.zone}" style="cursor: pointer; background: #f1f5f9; border-bottom: 1px solid #cbd5e1;">
							<td style="padding: 10px 14px; font-weight: 700; color: #0f172a; text-align: center; white-space: nowrap; width: 30px; vertical-align: middle;"><input type="checkbox" class="mis-row-check" data-check-id="zone::${z.zone}" ${zoneChecked ? "checked" : ""} style="cursor: pointer; width: 14px; height: 14px;"></td>
							<td style="padding: 10px 14px; font-weight: 700; color: #0f172a; text-align: center; white-space: nowrap; width: 40px; font-size: 14px;">${sr}</td>
							<td style="padding: 10px 14px; font-weight: 700; color: #0f172a; white-space: nowrap; font-size: 14px;">
								<span class="mis-zone-toggle" style="cursor: pointer; margin-right: 6px; font-size: 12px; color: #64748b;">${zoneExpanded ? "▼" : "▶"}</span>
								${z.zone}
							</td>
							<td style="padding: 10px 14px; font-weight: 700; color: #0d9488; text-align: center; white-space: nowrap; font-size: 14px;">${zoneRow.branches.length}</td>
							${metricCols.map(mc => `<td style="padding: 10px 14px; font-weight: 700; color: #0f172a; text-align: ${mc.align}; white-space: nowrap; font-size: 14px;">${mc.fmt(zoneRow[mc.key])}</td>`).join('')}
						</tr>`;

						z.regions.forEach(region => {
							const regionKey = z.zone + "::" + region.region;
							const regionExpanded = self.expandedRegions[regionKey];
							const regionRow = region;
							const regionChecked = self.checkedRows[regionKey];
							rowsHtml += `<tr class="mis-region-row${regionChecked ? " mis-row-checked" : ""}" data-zone="${z.zone}" data-region="${region.region}" data-check-id="${z.zone}::${region.region}" style="display: ${zoneExpanded ? "table-row" : "none"}; cursor: pointer; background: #f8fafc; border-bottom: 1px solid #e2e8f0;">
								<td style="padding: 8px 14px; text-align: center; white-space: nowrap; vertical-align: middle;"><input type="checkbox" class="mis-row-check" data-check-id="${z.zone}::${region.region}" ${regionChecked ? "checked" : ""} style="cursor: pointer; width: 14px; height: 14px;"></td>
								<td style="padding: 8px 14px; color: #64748b; text-align: center; white-space: nowrap; font-size: 14px;"></td>
								<td style="padding: 8px 14px; color: #334155; white-space: nowrap; font-size: 14px; padding-left: 30px; font-weight: 600;">
									<span class="mis-region-toggle" style="cursor: pointer; margin-right: 6px; font-size: 12px; color: #94a3b8;">${regionExpanded ? "▼" : "▶"}</span>
									${region.region}
								</td>
								<td style="padding: 8px 14px; color: #0d9488; text-align: center; white-space: nowrap; font-size: 14px; font-weight: 600;">${regionRow.branches.length}</td>
								${metricCols.map(mc => `<td style="padding: 8px 14px; color: #334155; text-align: ${mc.align}; white-space: nowrap; font-size: 14px; font-weight: 500;">${mc.fmt(regionRow[mc.key])}</td>`).join('')}
							</tr>`;

							regionRow.branches.forEach((branch, bi) => {
								const showBranch = zoneExpanded && self.expandedRegions[regionKey];
								const branchBg = bi % 2 === 0 ? "#ffffff" : "#f1f5f9";
								const solId = branch.sol_id || "branch_" + bi;
								const branchChecked = self.checkedRows[solId];
								rowsHtml += `<tr class="mis-branch-row${branchChecked ? " mis-row-checked" : ""}" data-zone="${z.zone}" data-region="${region.region}" data-check-id="${solId}" style="display: ${showBranch ? "table-row" : "none"}; background: ${branchBg}; border-bottom: 1px solid #e2e8f0;">
									<td style="padding: 6px 14px; text-align: center; white-space: nowrap; vertical-align: middle;"><input type="checkbox" class="mis-row-check" data-check-id="${solId}" ${branchChecked ? "checked" : ""} style="cursor: pointer; width: 14px; height: 14px;"></td>
									<td style="padding: 6px 14px; color: #94a3b8; text-align: center; white-space: nowrap; font-size: 14px;"></td>
									<td style="padding: 6px 14px; color: #475569; white-space: nowrap; font-size: 14px; padding-left: 50px; font-weight: 500;">${branch.sol_id} - ${branch.branch_name || branch.sol_desc}</td>
									<td style="padding: 6px 14px; color: #94a3b8; text-align: center; white-space: nowrap; font-size: 14px; font-weight: 500;">1</td>
									${metricCols.map(mc => `<td style="padding: 6px 14px; color: #475569; text-align: ${mc.align}; white-space: nowrap; font-size: 14px; font-weight: 500;">${mc.fmt(branch[mc.key])}</td>`).join('')}
								</tr>`;
							});
						});
					});

					const tableHtml = `
						<style>
							#mis-analysis-table { width: 100%; border-collapse: separate; border-spacing: 0; font-family: 'Inter', sans-serif; }
							#mis-analysis-table thead { position: sticky; top: 0; z-index: 2; }
							#mis-analysis-table tfoot { position: sticky; bottom: 0; z-index: 2; }
							#mis-analysis-table tfoot tr { box-shadow: 0 -2px 6px rgba(0,0,0,0.1); }
							#mis-analysis-table tbody tr { transition: background-color 0.2s ease; border-bottom: 1px solid #e2e8f0; }
							#mis-analysis-table tbody tr:hover { background: #dcfce7 !important; }
							#mis-analysis-table tbody tr.mis-row-checked { background: #bbf7d0 !important; }
							#mis-analysis-table tbody tr.mis-zone-row.mis-row-checked { background: #86efac !important; }
							#mis-analysis-table tbody tr.mis-region-row.mis-row-checked { background: #86efac !important; }
							#mis-analysis-table tbody tr.mis-branch-row.mis-row-checked { background: #86efac !important; }
							#mis-scroll-area { max-height: 550px; overflow: auto; border: 1px solid #e2e8f0; border-radius: 6px; }
						</style>
						<div id="mis-scroll-area">
							<table id="mis-analysis-table">
								<thead>
									<tr style="background: linear-gradient(180deg, #3d7579 0%, #346569 100%); color: #ffffff;">
										<th style="padding: 10px 12px; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; text-align: center; white-space: nowrap; width: 30px;"><input type="checkbox" class="mis-check-all" style="cursor: pointer; width: 14px; height: 14px;"></th>
										<th style="padding: 10px 12px; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; text-align: center; white-space: nowrap; width: 40px;">Sr</th>
										<th style="padding: 10px 12px; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; text-align: left; white-space: nowrap;">Zone / Region / Branch</th>
										<th style="padding: 10px 12px; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; text-align: center; white-space: nowrap;">Branches</th>
										${metricCols.map(mc => `<th style="padding: 10px 12px; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; text-align: ${mc.align}; white-space: nowrap;">${mc.label}</th>`).join('')}
									</tr>
								</thead>
								<tbody>
									${rowsHtml}
								</tbody>
								<tfoot>
									<tr style="background: #1e293b; color: #ffffff; font-weight: 700;">
										<td style="padding: 10px 12px; text-align: center; white-space: nowrap; font-size: 14px;"></td>
										<td style="padding: 10px 12px; text-align: center; white-space: nowrap; font-size: 14px;"></td>
										<td style="padding: 10px 12px; text-align: left; white-space: nowrap; font-size: 14px;">TOTAL</td>
										<td style="padding: 10px 12px; text-align: center; white-space: nowrap; font-size: 14px;">${zoneData.reduce((s, z) => s + z.data.branches.length, 0)}</td>
										${metricCols.map(mc => `<td style="padding: 10px 12px; text-align: ${mc.align}; white-space: nowrap; font-size: 14px;">${mc.fmt(grandTotal[mc.key])}</td>`).join('')}
									</tr>
								</tfoot>
							</table>
						</div>
					`;

					tableContainer.html(tableHtml);

					tableContainer.off("click", ".mis-zone-row").on("click", ".mis-zone-row", function(e) {
						if ($(e.target).closest(".mis-region-toggle, .mis-region-row, input[type=checkbox]").length) return;
						const zone = $(this).data("zone");
						self.expandedZones[zone] = !self.expandedZones[zone];
						const show = self.expandedZones[zone];
						const $regionRows = tableContainer.find(`.mis-region-row[data-zone="${zone}"]`);
						const $branchRows = tableContainer.find(`.mis-branch-row[data-zone="${zone}"]`);
						if (show) {
							$regionRows.stop(true, true).slideDown(200);
							$regionRows.each(function() {
								const r = $(this).data("region");
								if (self.expandedRegions[zone + "::" + r]) {
									tableContainer.find(`.mis-branch-row[data-zone="${zone}"][data-region="${r}"]`).stop(true, true).slideDown(200);
								}
							});
						} else {
							$branchRows.stop(true, true).slideUp(150);
							$regionRows.stop(true, true).slideUp(200);
						}
						$(this).find(".mis-zone-toggle").text(show ? "▼" : "▶");
					});

					tableContainer.off("click", ".mis-region-row").on("click", ".mis-region-row", function(e) {
						if ($(e.target).is("input[type=checkbox]")) return;
						e.stopPropagation();
						const zone = $(this).data("zone");
						const region = $(this).data("region");
						const regionKey = zone + "::" + region;
						self.expandedRegions[regionKey] = !self.expandedRegions[regionKey];
						const show = self.expandedRegions[regionKey];
						const $branchRows = tableContainer.find(`.mis-branch-row[data-zone="${zone}"][data-region="${region}"]`);
						if (show) {
							$branchRows.stop(true, true).slideDown(200);
						} else {
							$branchRows.stop(true, true).slideUp(150);
						}
						$(this).find(".mis-region-toggle").text(show ? "▼" : "▶");
					});

					tableContainer.off("change", ".mis-row-check").on("change", ".mis-row-check", function(e) {
						const checkId = $(this).data("check-id");
						const checked = $(this).prop("checked");
						self.checkedRows[checkId] = checked;
						const $row = $(this).closest("tr");
						$row.toggleClass("mis-row-checked", checked);
					});

					tableContainer.off("change", ".mis-check-all").on("change", ".mis-check-all", function(e) {
						const checked = $(this).prop("checked");
						tableContainer.find(".mis-row-check").each(function() {
							$(this).prop("checked", checked).trigger("change");
						});
					});
				},
			},
			{
				id: "term_deposit_pending",
				name: "Term Deposit Pending",
				columns: ["SOL ID", "Branch", "Account No", "Amount"],
				getData: () => [
					{ sol_id: "9001", branch: "Pune Main Branch", acc_no: "TD-88201", amount: "₹5,00,000" },
					{ sol_id: "9002", branch: "Mumbai Central Branch", acc_no: "TD-99102", amount: "₹12,50,000" },
					{ sol_id: "9003", branch: "Nagpur East Branch", acc_no: "TD-77303", amount: "₹8,20,000" }
				],
				render: function(container) {
					const data = this.getData();
					const headersHtml = this.columns.map(col => `
						<th style="padding: 12px 16px; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #cbd5e1;">${col}</th>
					`).join('');
					const rowsHtml = data.map(row => `
						<tr style="transition: background-color 0.15s ease;">
							<td style="padding: 12px 16px; border-bottom: 1px solid #cbd5e1; font-weight: 600; color: #1e293b;">${row.sol_id}</td>
							<td style="padding: 12px 16px; border-bottom: 1px solid #cbd5e1; color: #475569;">${row.branch}</td>
							<td style="padding: 12px 16px; border-bottom: 1px solid #cbd5e1; color: #475569;">${row.acc_no}</td>
							<td style="padding: 12px 16px; border-bottom: 1px solid #cbd5e1; color: #475569; font-weight: 500;">${row.amount}</td>
						</tr>
					`).join('');
					
					container.html(`
						<div class="mis-report-table-wrapper" style="background: #ffffff; border-radius: 8px; border: 1px solid #cbd5e1; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-top: 15px;">
							<table style="width: 100%; border-collapse: collapse; text-align: left; font-family: 'Inter', sans-serif;">
								<thead>
									<tr style="background: linear-gradient(180deg, #3d7579 0%, #346569 100%); color: #ffffff;">
										${headersHtml}
									</tr>
								</thead>
								<tbody class="mis-table-body">
									${rowsHtml}
								</tbody>
							</table>
						</div>
					`);
				}
			}
		];

		this.init();
	}

	init() {
		this.setupLegacyStyles();
		this.setupStyles();
		this.setupBranchProfilePopup();

		// Create wrappers for Drishti and MIS Dashboards to toggle visibility easily
		this.drishti_container = $('<div id="drishti-dashboard-container"></div>').appendTo(this.page.main);
		this.mis_container = null;

		this.createControls();
		this.createFilterTags();
		this.createTabsAndContainer();
		this.initDatePicker();
		this.setupHeaderToggle();
		this.updateStateFromUrl(); // Read from URL and update state
		this.switchDashboardMode(this.state.dashboardMode);
		this.updateUiFromState(); // Update UI from state
		this.loadFinancialYears();
	}

	setupBranchProfilePopup() {
		if (!window.showBranchProfilePopup) {
			window.showBranchProfilePopup = (sol_id) => {
				let d = new frappe.ui.Dialog({
					title: "Branch Profile - " + sol_id,
					size: "extra-large",
					minimizable: true,
				});

				d.$body.html(`
					<div id="iframe-loader-${sol_id}" style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 85vh; width: 100%;">
						<div class="spinner-border text-primary" role="status" style="margin-bottom: 15px; width: 3rem; height: 3rem; animation: spinner-border .75s linear infinite;"></div>
						<h4 style="color: #475569; font-weight: 600;">Branch Profile is Loading...</h4>
						<p style="color: #64748b;">Please wait</p>
					</div>
					<iframe id="iframe-content-${sol_id}" src="/branch_profile?sol_id=${sol_id}" style="width: 100%; height: 85vh; border: none; border-radius: 4px; display: none;"></iframe>
				`);

				d.$body.find(`#iframe-content-${sol_id}`).on("load", function () {
					d.$body.find(`#iframe-loader-${sol_id}`).fadeOut(200, function () {
						d.$body.find(`#iframe-content-${sol_id}`).fadeIn(200);
					});
				});

				d.$wrapper.css({
					"backdrop-filter": "blur(5px)",
					"background-color": "rgba(15, 23, 42, 0.6)",
				});

				// Increase the width of the modal
				d.$wrapper.find(".modal-dialog").css({
					"max-width": "80vw",
					width: "80vw",
				});

				// Add Full Screen button before the close button
				const fullScreenBtn = $(
					'<button class="btn btn-default btn-xs" style="margin-right: 12px; font-weight: 500; border-radius: 4px;"><i class="fa fa-external-link"></i> Full Screen</button>',
				);
				fullScreenBtn.on("click", function () {
					window.location.href = "/branch_profile?sol_id=" + sol_id;
				});

				let actions = d.$wrapper.find(".modal-actions");
				if (actions.length > 0) {
					actions.prepend(fullScreenBtn);
				} else {
					// Fallback for older Frappe versions
					let closeBtn = d.$wrapper.find(
						".modal-header .btn-close, .modal-header .close",
					);
					if (closeBtn.length > 0) {
						closeBtn.before(fullScreenBtn);
					}
				}

				// Some extra styling for the dialog to look modern and hide the default padding
				d.$body.css({
					padding: "0",
					overflow: "hidden",
				});

				d.show();
			};
		}
	}

	initDatePicker() {
		const self = this;
		const container = $("#date-selector-container");
		if (container.length) {
			container.find(".frappe-control").remove();
			
			this.dateControl = frappe.ui.form.make_control({
				parent: container,
				df: {
					fieldtype: "Date",
					fieldname: "date_selector",
					placeholder: "DD/MM/YYYY",
					only_input: true,
					change: function () {
						if (self.isRefreshingDate) return;
						const val = self.dateControl.get_value();
						if (!val) return;

						self.state.selectedDate = val;
						if (self.state.activeTab && self.tabDates.hasOwnProperty(self.state.activeTab)) {
							self.tabDates[self.state.activeTab] = val;
						}

						// Automatically update financial year based on selected date
						const calculatedFy = self.getFinancialYearFromDate(val);
						if (calculatedFy) {
							const $fySelector = $("#fy-selector");
							if ($fySelector.length) {
								if (!$fySelector.find(`option[value="${calculatedFy}"]`).length) {
									$fySelector.prepend(`<option value="${calculatedFy}">${calculatedFy}</option>`);
								}
								$fySelector.val(calculatedFy);
							}
							self.state.financialYear = calculatedFy;
						}

						// Automatically update selected quarter based on selected date
						self.state.selectedQuarter = self.getQuarterFromDate(val);

						// Automatically update selected month key based on selected date
						const monthNames = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
						const monthNum = parseInt(val.split("-")[1], 10); // 1-12
						self.state.selectedMonth = monthNames[monthNum - 1];

						self.updateUrlFromState();
						self.loadData();
					}
				},
				render_input: true
			});

			if (this.dateControl && this.dateControl.$input) {
				this.dateControl.$input.css({
					"padding": "6px 10px",
					"border": "1px solid #cbd5e1",
					"border-radius": "6px",
					"background": "white",
					"color": "#1b263b",
					"font-size": "13px",
					"font-weight": "600",
					"height": "32px",
					"width": "140px"
				});
				this.dateControl.$wrapper.css({
					"margin": "0",
					"padding": "0",
					"display": "inline-block"
				});
			}
		}
	}

	updateDatePickerValue(dateStr) {
		if (this.dateControl) {
			const currentVal = this.dateControl.get_value();
			if (currentVal === dateStr) return;

			this.isRefreshingDate = true;
			this.dateControl.set_value(dateStr || "");
			this.isRefreshingDate = false;
		}
	}

	loadFinancialYears() {
		const self = this;
		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_available_financial_years",
			callback: function (r) {
				if (r.message && r.message.length > 0) {
					self.financialYearsList = r.message;
					self.populateFinancialYears(r.message);
					// Select the latest (first) available year if not already set
					if (
						!self.state.financialYear ||
						!r.message.includes(self.state.financialYear)
					) {
						self.state.financialYear = r.message[0];
						$("#fy-selector").val(self.state.financialYear);
					}
					self.loadData();
				}
			},
		});
	}

	populateFinancialYears(fyList) {
		const selector = $("#fy-selector");
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
		this.updateDatePickerValue(defaultDate);
		if (this.state.activeTab && this.tabDates.hasOwnProperty(this.state.activeTab)) {
			this.tabDates[this.state.activeTab] = defaultDate;
		}
	}

	getDashboardViewForRequest() {
		return this.state.viewType;
	}

	normalizeDashboardResponse(data) {
		if (!this.isPreviousFinancialYear()) return data;

		if (this.state.viewType === "Monthly") {
			const targetMonth = this.state.selectedMonth || "MAR";
			data.months = (data.months || []).filter((month) => month.key === targetMonth);
		}

		return data;
	}

	normalizeTargetType(targetType) {
		return ["Monthly", "YTD", "Yearly"].includes(targetType) ? targetType : "Monthly";
	}

	setupLegacyStyles() {
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

			.sahayog-dashboard-full-width .container {
				max-width: 95% !important;
				width: 95% !important;
				padding-left: 0px !important;
				padding-right: 0px !important;
				margin: 0px auto !important;
			}
			.sahayog-dashboard-full-width .container .page-body {
				max-width: 100% !important;
				width: 100% !important;
				padding: 0px !important;
				margin: 0px !important;
			}

			/* Sticky columns for Zone table and Branch table */
			.zone-wise-table .sr-col,
			.zone-wise-table .zone-col,
			.zone-wise-table .branches-col {
				position: sticky;
				background-color: #ffffff;
				background-clip: border-box !important;
				box-sizing: border-box !important;
				border-right: none !important;
			}
			.zone-wise-table th.sr-col,
			.zone-wise-table th.zone-col,
			.zone-wise-table th.branches-col {
				z-index: 6;
				background: linear-gradient(180deg, #3d7579 0%, #346569 100%) !important;
				color: #ffffff !important;
				border-right: none !important;
			}
			.zone-wise-table th.sr-col {
				box-shadow: inset -1px 0 0 #366b6f !important;
			}
			.zone-wise-table th.zone-col {
				box-shadow: inset -1px 0 0 #366b6f !important;
			}
			.zone-wise-table th.branches-col {
				box-shadow: inset -2px 0 0 #2d5659 !important;
			}
			.zone-wise-table td.sr-col,
			.zone-wise-table td.zone-col,
			.zone-wise-table td.branches-col {
				z-index: 5;
				border-right: none !important;
			}
			.zone-wise-table td.sr-col {
				box-shadow: inset -1px 0 0 #cbd5e1 !important;
			}
			.zone-wise-table td.zone-col {
				box-shadow: inset -1px 0 0 #cbd5e1 !important;
			}
			.zone-wise-table td.branches-col {
				box-shadow: inset -2px 0 0 #3d7579 !important;
			}
			.zone-wise-table .sr-col {
				left: 0px;
				width: 50px;
				min-width: 50px;
				max-width: 50px;
			}
			.zone-wise-table .zone-col {
				left: 50px;
				width: 180px;
				min-width: 180px;
				max-width: 180px;
				text-align: left !important;
				white-space: normal !important;
			}
			.zone-wise-table .branches-col {
				left: 230px;
				width: 100px;
				min-width: 100px;
				max-width: 100px;
				white-space: normal !important;
			}
			.zone-wise-table tr:hover td.sr-col,
			.zone-wise-table tr:hover td.zone-col,
			.zone-wise-table tr:hover td.branches-col {
				background-color: #f8f9fa !important;
			}
			.zone-wise-table tr.zone-total-row td.sr-col,
			.zone-wise-table tr.zone-total-row td.zone-col,
			.zone-wise-table tr.zone-total-row td.branches-col {
				background-color: #e0e1dd !important;
			}
			.zone-wise-table tr.zone-total-row:hover td.sr-col,
			.zone-wise-table tr.zone-total-row:hover td.zone-col,
			.zone-wise-table tr.zone-total-row:hover td.branches-col {
				background-color: #d4d5d1 !important;
			}
			.region-detail-row td.sr-col {
				border-left: 4px solid #417d81 !important;
			}

			.branch-table td.sr-col,
			.branch-table td.branch-col,
			.branch-table td.segment-col {
				position: sticky;
				background-color: #ffffff;
				background-clip: border-box !important;
				box-sizing: border-box !important;
				border-right: none !important;
			}
			.branch-table th.sr-col,
			.branch-table th.branch-col,
			.branch-table th.segment-col {
				position: sticky;
				z-index: 6;
				background: linear-gradient(180deg, #3d7579 0%, #346569 100%) !important;
				color: #ffffff !important;
				box-sizing: border-box !important;
				border-right: none !important;
			}
			.branch-table th.sr-col {
				box-shadow: inset -1px 0 0 #366b6f !important;
			}
			.branch-table th.branch-col {
				box-shadow: inset -1px 0 0 #366b6f !important;
			}
			.branch-table th.segment-col {
				box-shadow: inset -2px 0 0 #2d5659 !important;
			}
			.branch-table td.sr-col,
			.branch-table td.branch-col,
			.branch-table td.segment-col {
				z-index: 5;
				border-right: none !important;
			}
			.branch-table td.sr-col {
				box-shadow: inset -1px 0 0 #cbd5e1 !important;
			}
			.branch-table td.branch-col {
				box-shadow: inset -1px 0 0 #cbd5e1 !important;
			}
			.branch-table td.segment-col {
				box-shadow: inset -2px 0 0 #3d7579 !important;
			}
			.branch-table .sr-col {
				left: 0px;
				width: 60px;
				min-width: 60px;
				max-width: 60px;
			}
			.branch-table .branch-col {
				left: 60px;
				width: 145px;
				min-width: 145px;
				max-width: 145px;
				white-space: normal !important;
			}
			.branch-table .segment-col {
				left: 205px;
				width: 80px;
				min-width: 80px;
				max-width: 80px;
				white-space: normal !important;
			}
			.branch-table-row {
				background-color: #ffffff;
			}

			.zone-wise-table, .branch-table {
				width: max-content !important;
				min-width: 100% !important;
			}

			.zone-wise-table th,
			.zone-wise-table td,
			.branch-table th,
			.branch-table td {
				white-space: nowrap;
			}

			.zone-wise-table th,
			.branch-table th,
			.agent-wise-table th,
			.product-wise-table th,
			.category-table-redesigned th {
				text-align: center !important;
				vertical-align: middle !important;
			}
		`;
		$(`<style>${style}</style>`).appendTo("head");
	}

	getQuarterFromDate(dateStr) {
		const date = new Date(dateStr || frappe.datetime.get_today());
		const month = date.getMonth(); // 0-indexed
		if (month >= 3 && month <= 5) return "Q1";
		if (month >= 6 && month <= 8) return "Q2";
		if (month >= 9 && month <= 11) return "Q3";
		return "Q4";
	}

	getFinancialYearFromDate(dateStr) {
		if (!dateStr) return null;
		const parts = dateStr.split("-");
		const year = parseInt(parts[0], 10);
		const month = parseInt(parts[1], 10); // 1-12

		let startYear;
		if (month >= 4) {
			startYear = year;
		} else {
			startYear = year - 1;
		}
		const endYear = startYear + 1;
		return `${startYear}-${endYear}`;
	}

	getQuarterDate(quarter, fy) {
		if (!fy) return frappe.datetime.get_today();
		const startYear = fy.split("-")[0];
		const endYear = fy.split("-")[1]
			? ("20" + fy.split("-")[1]).replace("2020", "20")
			: (parseInt(startYear) + 1).toString();
		const endYearFull = endYear.length === 2 ? "20" + endYear : endYear;
		switch (quarter) {
			case "Q1":
				return `${startYear}-06-30`;
			case "Q2":
				return `${startYear}-09-30`;
			case "Q3":
				return `${startYear}-12-31`;
			case "Q4":
				return `${endYearFull}-03-31`;
			default:
				return frappe.datetime.get_today();
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
			const startYear = this.state.financialYear
				? this.state.financialYear.split("-")[0]
				: new Date().getFullYear().toString();
			let endYear = this.state.financialYear
				? this.state.financialYear.split("-")[1]
				: (parseInt(startYear) + 1).toString();
			if (endYear && endYear.length === 2) endYear = "20" + endYear;

			const qMap = {
				Q1: [
					{
						key: "APR",
						display: `APR-${startYear.slice(-2)}`,
						date: `${startYear}-04-01`,
					},
					{
						key: "MAY",
						display: `MAY-${startYear.slice(-2)}`,
						date: `${startYear}-05-01`,
					},
					{
						key: "JUN",
						display: `JUN-${startYear.slice(-2)}`,
						date: `${startYear}-06-01`,
					},
				],
				Q2: [
					{
						key: "JUL",
						display: `JUL-${startYear.slice(-2)}`,
						date: `${startYear}-07-01`,
					},
					{
						key: "AUG",
						display: `AUG-${startYear.slice(-2)}`,
						date: `${startYear}-08-01`,
					},
					{
						key: "SEP",
						display: `SEP-${startYear.slice(-2)}`,
						date: `${startYear}-09-01`,
					},
				],
				Q3: [
					{
						key: "OCT",
						display: `OCT-${startYear.slice(-2)}`,
						date: `${startYear}-10-01`,
					},
					{
						key: "NOV",
						display: `NOV-${startYear.slice(-2)}`,
						date: `${startYear}-11-01`,
					},
					{
						key: "DEC",
						display: `DEC-${startYear.slice(-2)}`,
						date: `${startYear}-12-01`,
					},
				],
				Q4: [
					{ key: "JAN", display: `JAN-${endYear.slice(-2)}`, date: `${endYear}-01-01` },
					{ key: "FEB", display: `FEB-${endYear.slice(-2)}`, date: `${endYear}-02-01` },
					{ key: "MAR", display: `MAR-${endYear.slice(-2)}`, date: `${endYear}-03-01` },
				],
			};
			const quarter =
				this.state.selectedQuarter ||
				this.getQuarterFromDate(this.state.selectedDate || frappe.datetime.get_today());
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
			this.state.branchSearchTerm =
				queryParams.branchSearchTerm || this.state.branchSearchTerm;
			this.state.selectedMonth = queryParams.selectedMonth || this.state.selectedMonth;
			this.state.selectedSegment = queryParams.selectedSegment || this.state.selectedSegment;
			this.state.selectedQuarter = queryParams.selectedQuarter || this.state.selectedQuarter;
			this.state.dashboardMode = queryParams.dashboardMode || this.state.dashboardMode;

			if (queryParams.selectedRegions) {
				this.state.selectedRegions = queryParams.selectedRegions.split(",").filter(Boolean);
			} else if (queryParams.selectedRegion) {
				this.state.selectedRegions = [queryParams.selectedRegion];
			} else {
				this.state.selectedRegions = [];
			}

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
			branchSearchTerm: this.state.branchSearchTerm,
			selectedMonth: this.state.selectedMonth,
			selectedSegment: this.state.selectedSegment,
			dashboardMode: this.state.dashboardMode,
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
		if (this.state.selectedRegions.length > 0) {
			newSearchParams.set("selectedRegions", this.state.selectedRegions.join(","));
		}

		newUrl.search = newSearchParams.toString();
		history.pushState({}, "", newUrl.toString());
	}

	updateUiFromState() {
		// Update FY selector
		$("#fy-selector").val(this.state.financialYear);

		// Update View toggle
		this.page.main.find(".view-toggle-btn").removeClass("active");
		this.page.main
			.find(`.view-toggle-btn[data-view="${this.state.viewType}"]`)
			.addClass("active");

		// Update Quarter toggle
		if (this.state.viewType === "Quarterly") {
			this.page.main.find("#quarter-selector-container").show();
			this.page.main.find(".quarter-toggle-btn").removeClass("active");
			if (!this.state.selectedQuarter) {
				this.state.selectedQuarter = this.getQuarterFromDate(this.state.selectedDate || frappe.datetime.get_today());
				this.state.selectedDate = this.getQuarterDate(this.state.selectedQuarter, this.state.financialYear);
			}
			this.page.main
				.find(`.quarter-toggle-btn[data-quarter="${this.state.selectedQuarter}"]`)
				.addClass("active");
		} else {
			this.page.main.find("#quarter-selector-container").hide();
		}

		// Update Month selector
		if (this.state.viewType === "Monthly") {
			this.page.main.find("#month-selector-container").show();
			const dateToUse = this.state.selectedDate || frappe.datetime.get_today();
			const monthVal = parseInt(dateToUse.split("-")[1], 10); // 1-12
			this.page.main.find("#month-selector").val(monthVal);
		} else {
			this.page.main.find("#month-selector-container").hide();
		}

		// Update Target toggle
		this.page.main.find(".target-toggle-btn").removeClass("active");
		this.page.main
			.find(`.target-toggle-btn[data-target="${this.state.targetType}"]`)
			.addClass("active");

		// Update Format toggle
		$(".format-toggle-btn").removeClass("active");
		$(`.format-toggle-btn[data-format="${this.state.formatMode}"]`).addClass("active");

		// Update Date selector
		this.updateDatePickerValue(this.state.selectedDate);

		// Update Region selector
		this.updateRegionDropdownUI();

		// Update Branch search
		this.page.main.find("#branch-search").val(this.state.branchSearchTerm);

		// Update Segment filter
		this.page.main.find("#segment-filter").val(this.state.selectedSegment);

		// Update tabs
		this.page.main.find(".tab-btn").removeClass("active");
		this.page.main.find(`.tab-btn[data-tab="${this.state.activeTab}"]`).addClass("active");

		// Update dashboard mode toggle
		const header = $(this.page.wrapper || ".frappe-page:visible").find(".page-head-row").length 
			? $(this.page.wrapper || ".frappe-page:visible").find(".page-head-row") 
			: $(this.page.wrapper || ".frappe-page:visible").find(".page-head .container");
		if (header.length) {
			header.find(".dashboard-toggle-btn").removeClass("active");
			header.find(`.dashboard-toggle-btn[data-value="${this.state.dashboardMode}"]`).addClass("active");
		}

		// Update filter tags for zones and categories
		this.updateFilterTagsUI();
	}

	repopulateHeaderFilters() {
		if (this.financialYearsList && this.financialYearsList.length > 0) {
			this.populateFinancialYears(this.financialYearsList);
		}
		this.updateUiFromState();
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
		this.state.selectedRegions = [];
		this.state.branchSearchTerm = "";
		this.state.selectedMonth = null;
		this.state.drillDownActive = false;

		this.updateDatePickerValue("");
		this.updateRegionDropdownUI();
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
                        <span class="summary-subtext success" id="summary-target-label">Monthly target</span>
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
            <div class="filter-tags-row">
                <!-- Zone Selection -->
                <div class="filter-tags-container zone-filter-container">
                    <div class="filter-group">
                        <span class="filter-group-label">Zone:</span>
                        <div class="filter-tags" id="zone-tags"></div>
                    </div>
                </div>

            				<!-- Performance Categories -->
				<div class="filter-tags-container category-filter-container">
					<div class="filter-group">
						<span class="filter-group-label">Category:</span>
						<div class="filter-tags" id="category-tags"></div>
					</div>
				</div>
			</div>
		`;

		$(html).appendTo(this.drishti_container || this.page.main);
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

		// Calculate zone percentages using Largest Remainder Method
		const zonePercentages = {};
		if (allZonesCount === 0) {
			zonePercentages["all"] = 100;
			this.availableFilters.zones.forEach((z) => {
				zonePercentages[z] = 0;
			});
		} else {
			zonePercentages["all"] = 100;
			let sumFloors = 0;
			const items = [];

			this.availableFilters.zones.forEach((zone) => {
				const count = this.zoneCounts[zone] || 0;
				const exact = (count / allZonesCount) * 100;
				const floorVal = Math.floor(exact);
				sumFloors += floorVal;
				items.push({
					zone: zone,
					exact: exact,
					floorVal: floorVal,
					remainder: exact - floorVal,
				});
			});

			let diff = 100 - sumFloors;
			items.sort((a, b) => b.remainder - a.remainder);

			items.forEach((item, index) => {
				let finalVal = item.floorVal;
				if (index < diff) {
					finalVal += 1;
				}
				zonePercentages[item.zone] = finalVal;
			});
		}

		container.append(`
            <button class="filter-tag zone-tag ${allZonesActive ? "active" : ""}" data-zone="all">
                <span class="zone-tag-content">
                    All
                    <span class="filter-tag-count">${allZonesCount}</span>
                    <span class="zone-tag-pct">${zonePercentages["all"]}%</span>
                </span>
            </button>
        `);

		this.availableFilters.zones.forEach((zone) => {
			const count = this.zoneCounts[zone] || 0;
			const isActive = this.state.selectedZones.includes(zone);
			const zoneNum = zone.match(/\d+/);
			const displayName = zoneNum ? `Zone ${zoneNum[0]}` : zone;
			const pct = zonePercentages[zone];

			container.append(`
                <button class="filter-tag zone-tag ${
					isActive ? "active" : ""
				}" data-zone="${zone}">
                    <span class="zone-tag-content">
                        ${displayName}
                        <span class="filter-tag-count">${count}</span>
                        <span class="zone-tag-pct">${pct}%</span>
                    </span>
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

		// Calculate percentages using Largest Remainder Method to ensure total is exactly 100%
		const percentages = {};
		if (allCategoriesCount === 0) {
			percentages["all"] = 100;
			this.availableFilters.categories.forEach((cat) => {
				percentages[cat] = 0;
			});
		} else {
			percentages["all"] = 100;
			let sumFloors = 0;
			const items = [];

			this.availableFilters.categories.forEach((cat) => {
				const count = this.categoryCounts[cat] || 0;
				const exact = (count / allCategoriesCount) * 100;
				const floorVal = Math.floor(exact);
				sumFloors += floorVal;
				items.push({
					category: cat,
					exact: exact,
					floorVal: floorVal,
					remainder: exact - floorVal,
				});
			});

			let diff = 100 - sumFloors;
			items.sort((a, b) => b.remainder - a.remainder);

			items.forEach((item, index) => {
				let finalVal = item.floorVal;
				if (index < diff) {
					finalVal += 1;
				}
				percentages[item.category] = finalVal;
			});
		}

		container.append(`
            <button class="filter-tag category-tag all-tag ${
				allCategoriesActive ? "active" : ""
			}" data-category="all">
                <span class="category-tag-content">
                    All
                    <span class="filter-tag-count">${allCategoriesCount}</span>
                    <span class="category-tag-pct">${percentages["all"]}%</span>
                </span>
            </button>
        `);

		this.availableFilters.categories.forEach((category) => {
			const count = this.categoryCounts[category] || 0;
			const isActive = this.state.selectedCategories.includes(category);
			const color = categoryColors[category] || "#778da9";
			const pct = percentages[category];

			container.append(`
                <button class="filter-tag category-tag ${isActive ? "active" : ""}" 
                        data-category="${category}" 
                        style="border-left: 3px solid ${color};">
                    <span class="category-tag-content">
                        ${category}
                        <span class="filter-tag-count">${count}</span>
                        <span class="category-tag-pct">${pct}%</span>
                    </span>
                </button>
            `);
		});

		this.attachCategoryTagEvents();
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
		if (this.state.selectedRegions && this.state.selectedRegions.length > 0) {
			filteredBranches = filteredBranches.filter((b) =>
				this.state.selectedRegions.includes(b.region),
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
            <div style="border: 1px solid #cbd5e1; padding: 8px 12px; background: #fff; border-radius: 8px; margin-top: 6px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);">
                <!-- Filters Row -->
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #ddd;">
                    <!-- FY Selector -->
                    <div class="outlined-input-container fy-header-control">
                        <label class="outlined-input-label">FY</label>
                        <select id="fy-selector" style="width: 110px;">
                        </select>
                    </div>

                    <!-- Date Selector -->
                    <div id="date-selector-container" class="outlined-input-container">
                        <label class="outlined-input-label">Date</label>
                    </div>

                    <!-- Month Selector (shown only when view is Monthly) -->
                    <div id="month-selector-container" class="outlined-input-container" style="display: none;">
                        <label class="outlined-input-label">Month</label>
                        <select id="month-selector" style="width: 110px;">
                            <option value="4">April</option>
                            <option value="5">May</option>
                            <option value="6">June</option>
                            <option value="7">July</option>
                            <option value="8">August</option>
                            <option value="9">September</option>
                            <option value="10">October</option>
                            <option value="11">November</option>
                            <option value="12">December</option>
                            <option value="1">January</option>
                            <option value="2">February</option>
                            <option value="3">March</option>
                        </select>
                    </div>

                    <!-- Days Left countdown -->
                    <div style="display: flex; align-items: center;">
                        <span id="drishti-live-timer" style="font-size: 13px; font-weight: 600; color: #64748b; white-space: nowrap;"></span>
                    </div>

                    <!-- View Toggle Buttons -->
                    <div style="display: flex; align-items: center;">
                        <label style="font-weight: bold; color: #0d1b2a; margin-bottom: 0;">View:</label>
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
                    <div style="display: flex; align-items: center;">
                        <label style="font-weight: bold; color: #0d1b2a; margin-bottom: 0;">Target:</label>
                        <div class="btn-group" role="group" style="margin-left: 8px;">
                            <button type="button" class="btn btn-sm target-toggle-btn" data-target="Monthly">Monthly</button>
                            <button type="button" class="btn btn-sm target-toggle-btn" data-target="YTD">YTD</button>
                            <button type="button" class="btn btn-sm target-toggle-btn" data-target="Yearly">Yearly</button>
                        </div>
                    </div>
 
                    <!-- Region Filter (Multi-select dropdown) -->
                    <div class="dropdown outlined-input-container" id="region-dropdown-container">
                        <label class="outlined-input-label">Region</label>
                        <button class="btn btn-default btn-sm dropdown-toggle" type="button" id="region-dropdown-btn" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" style="min-width: 150px; text-align: left; display: inline-flex; align-items: center; justify-content: space-between;">
                            <span id="region-dropdown-label">All Regions</span>
                            <span class="caret" style="margin-left: 8px;"></span>
                        </button>
                        <ul class="dropdown-menu" id="region-dropdown-menu" aria-labelledby="region-dropdown-btn" style="max-height: 250px; overflow-y: auto; padding: 5px 0; border: 1px solid #cbd5e1; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); width: 220px;">
                        </ul>
                    </div>

                    <!-- Format Control -->
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="font-weight: bold; color: #0d1b2a; font-size: 13px; white-space: nowrap;">Format:</span>
                        <div class="btn-group" role="group">
                            <button type="button" class="btn btn-sm format-toggle-btn" data-format="number">Numbers</button>
                            <button type="button" class="btn btn-sm format-toggle-btn" data-format="words">Words</button>
                        </div>
                    </div>
                </div>

                <div id="tab-buttons" style="display: flex; align-items: center; gap: 24px; margin-bottom: 0; border-bottom: 2px solid #cbd5e1; width: 100%;">
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
                    <div style="margin-left: auto; display: flex; align-items: center; gap: 10px; padding-bottom: 6px;">
						<select id="segment-filter" style="padding: 6px 12px; border: 1px solid #cbd5e1; border-radius: 4px; background: white; color: #1b263b;">
							<option value="all">All Segments</option>
							<option value="Top 25%">Top 25%</option>
							<option value="Next 25%">Next 25%</option>
							<option value="Mid 25%">Mid 25%</option>
							<option value="Bottom 25%">Bottom 25%</option>
						</select>
                        <input type="text" id="branch-search" placeholder="Search branch or SOL ID (comma separated)..." 
                               style="padding: 6px 12px; border: 1px solid #cbd5e1; border-radius: 4px; min-width: 250px; background: white; color: #1b263b;" />
                        <button id="clear-filters" class="btn btn-secondary btn-sm" 
                                style="background: #417d81; border-color: #1b263b; color: white; font-weight: 600;"
                                title="Resets all filters to their default state and refreshes the dashboard.">
                            🔄 Reset & Refresh
                        </button>
                    </div>
                </div>

                <div id="error-message" style="color: #0d1b2a; display: none; padding: 10px; background: #ffebee; border-radius: 4px;"></div>

                <div id="tab-content" style="overflow: auto; max-height: 75vh;">
                    <div id="data-container" style="transition: opacity 0.2s ease-in-out;"></div>
                </div>
            </div>
        `;

		$(html).appendTo(this.drishti_container || this.page.main);
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
				if (self.state.branchSearchTerm && self.state.activeTab !== "branch") {
					self.switchTab("branch");
				} else {
					self.render();
				}
			}, 300);
		});

		// Financial Year
		$(document).off("change", "#fy-selector").on("change", "#fy-selector", function () {
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
			
			if (self.state.viewType === "Quarterly") {
				self.state.selectedMonth = null;
				const currentQ = self.getQuarterFromDate(frappe.datetime.get_today());
				self.state.selectedQuarter = currentQ;
				self.state.selectedDate = self.getQuarterDate(currentQ, self.state.financialYear);
			} else if (self.state.viewType === "Monthly") {
				self.state.selectedQuarter = null;
				if (self.isPreviousFinancialYear()) {
					self.applyPreviousFinancialYearDefaultDate();
				} else {
					self.state.selectedDate = frappe.datetime.get_today();
				}
			} else {
				self.state.selectedQuarter = null;
				self.applyPreviousFinancialYearDefaultDate();
			}
			
			self.updateUrlFromState();
			self.updateUiFromState();
			self.loadData();
		});

		this.page.main
			.find("#error-message")
			.on("click", ".view-change-option-link", function (e) {
				e.preventDefault();
				const view = $(this).data("view");
				self.page.main.find(`.view-toggle-btn[data-view="${view}"]`).trigger("click");
			});

		// Quarter Toggle Buttons
		this.page.main.find(".quarter-toggle-btn").on("click", function () {
			self.state.selectedMonth = null;
			self.state.selectedQuarter = $(this).data("quarter");
			self.state.selectedDate = self.getQuarterDate(
				self.state.selectedQuarter,
				self.state.financialYear,
			);
			self.updateUrlFromState();
			self.updateUiFromState();
			self.loadData();
		});

		// Month Selector change
		this.page.main.on("change", "#month-selector", function () {
			const selectedMonthNum = parseInt($(this).val()); // 1 to 12
			
			const now = new Date();
			const currentMonth = now.getMonth() + 1; // 1-12
			const currentYear = now.getFullYear();
			
			const startYear = parseInt(self.state.financialYear.split("-")[0]);
			const endYear = parseInt(self.state.financialYear.split("-")[1]);
			
			const selectedYear = (selectedMonthNum >= 4) ? startYear : endYear;
			
			const isFuture = (selectedYear > currentYear) || (selectedYear === currentYear && selectedMonthNum > currentMonth);
			
			if (isFuture) {
				frappe.show_alert({
					message: __("Future months cannot be accessed"),
					indicator: "orange"
				});
				const dateToUse = self.state.selectedDate || frappe.datetime.get_today();
				const prevMonthVal = new Date(dateToUse).getMonth() + 1;
				$(this).val(prevMonthVal);
				return;
			}
			
			let newDateStr = "";
			if (selectedYear === currentYear && selectedMonthNum === currentMonth) {
				const todayObj = new Date();
				newDateStr = `${todayObj.getFullYear()}-${String(todayObj.getMonth() + 1).padStart(2, "0")}-${String(todayObj.getDate()).padStart(2, "0")}`;
			} else {
				const lastDay = new Date(selectedYear, selectedMonthNum, 0).getDate();
				newDateStr = `${selectedYear}-${String(selectedMonthNum).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`;
			}
			
			self.state.selectedDate = newDateStr;
			if (self.state.activeTab && self.tabDates.hasOwnProperty(self.state.activeTab)) {
				self.tabDates[self.state.activeTab] = newDateStr;
			}

			// Automatically update selected month name key
			const monthNames = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
			self.state.selectedMonth = monthNames[selectedMonthNum - 1];
			
			self.updateDatePickerValue(newDateStr);
			self.updateUrlFromState();
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


		// Format Toggle
		$(document)
			.off("click", ".format-toggle-btn")
			.on("click", ".format-toggle-btn", function () {
				$(".format-toggle-btn").removeClass("active");
				$(this).addClass("active");
				self.state.formatMode = $(this).data("format");
				self.updateUrlFromState();
				self.render();
			});

		// Region Filter - All Regions checkbox change
		this.page.main.on("change", "#region-all-checkbox", function () {
			const isChecked = $(this).prop("checked");
			if (isChecked) {
				self.state.selectedRegions = [];
			} else {
				self.state.selectedRegions = [...self.availableFilters.regions];
			}
			self.updateRegionDropdownUI();
			self.updateUrlFromState();
			self.loadData();
		});

		// Region Filter - Individual checkbox change
		this.page.main.on("change", ".region-checkbox", function () {
			const region = $(this).val();
			const isChecked = $(this).prop("checked");

			if (isChecked) {
				if (!self.state.selectedRegions.includes(region)) {
					self.state.selectedRegions.push(region);
				}
			} else {
				const index = self.state.selectedRegions.indexOf(region);
				if (index > -1) {
					self.state.selectedRegions.splice(index, 1);
				}
			}

			// If all individual regions are selected, we can optionally clear the array to signify "All Regions"
			if (self.state.selectedRegions.length === self.availableFilters.regions.length) {
				self.state.selectedRegions = [];
			}

			self.updateRegionDropdownUI();
			self.updateUrlFromState();
			self.loadData();
		});

		// Prevent dropdown from closing when clicking inside the menu
		this.page.main.on("click", "#region-dropdown-menu", function (e) {
			e.stopPropagation();
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
			const method =
				tabId === "agent"
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

					if (self.state.selectedDate) {
						const monthNames = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
						const monthNum = parseInt(self.state.selectedDate.split("-")[1], 10);
						self.state.selectedMonth = monthNames[monthNum - 1];
					}

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

					// Update selectedDate if empty to reflect the actual loaded date
					if (!self.state.selectedDate && r.message.months && r.message.months.length > 0) {
						const latestMonth = r.message.months[r.message.months.length - 1];
						if (latestMonth && latestMonth.date) {
							self.state.selectedDate = latestMonth.date;
							if (self.state.activeTab && self.tabDates.hasOwnProperty(self.state.activeTab)) {
								self.tabDates[self.state.activeTab] = latestMonth.date;
							}
							self.updateDatePickerValue(latestMonth.date);
							if (self.state.viewType === "Monthly") {
								const monthVal = new Date(latestMonth.date).getMonth() + 1;
								self.page.main.find("#month-selector").val(monthVal);
							}
							self.updateUrlFromState();
						}
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
			},
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
			},
		});
	}

	// ========================================================================
	// DATA LOADING
	// ========================================================================
	loadData() {
		if (this.state.dashboardMode === "mis") {
			return;
		}
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
					console.log(
						`[loadData callback] Data received. branchData length: ${self.branchData?.length || 0}`,
					);

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

					// Update selectedDate if empty to reflect the actual loaded date
					if (!self.state.selectedDate && r.message.months && r.message.months.length > 0) {
						const latestMonth = r.message.months[r.message.months.length - 1];
						if (latestMonth && latestMonth.date) {
							self.state.selectedDate = latestMonth.date;
							if (self.state.activeTab && self.tabDates.hasOwnProperty(self.state.activeTab)) {
								self.tabDates[self.state.activeTab] = latestMonth.date;
							}
							self.updateDatePickerValue(latestMonth.date);
							if (self.state.viewType === "Monthly") {
								const monthVal = new Date(latestMonth.date).getMonth() + 1;
								self.page.main.find("#month-selector").val(monthVal);
							}
							self.updateUrlFromState();
						}
					}

					self.processNewApiResponse();
					self.updateFilterCounts();
					self.updateUiFromState();
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

		const menu = this.page.main.find("#region-dropdown-menu");
		if (!menu.length) return;
		menu.empty();

		// Add "All Regions" / toggle all item
		menu.append(`
			<li style="padding: 6px 12px; border-bottom: 1px solid #edf2f7; margin-bottom: 4px; white-space: nowrap; display: flex; align-items: center;">
				<label style="font-weight: bold; margin-bottom: 0; cursor: pointer; display: flex; align-items: center; width: 100%; color: #0d1b2a;">
					<input type="checkbox" id="region-all-checkbox" style="position: relative !important; margin: 0 8px 0 0 !important; cursor: pointer; width: 14px; height: 14px; vertical-align: middle;" />
					All Regions
				</label>
			</li>
		`);

		// Add each region checkbox
		this.availableFilters.regions.forEach((region) => {
			const isChecked = this.state.selectedRegions.includes(region);
			menu.append(`
				<li style="padding: 6px 12px; white-space: nowrap; display: flex; align-items: center;">
					<label style="font-weight: normal; margin-bottom: 0; cursor: pointer; display: flex; align-items: center; width: 100%; color: #1b263b;">
						<input type="checkbox" class="region-checkbox" value="${region}" ${isChecked ? "checked" : ""} style="position: relative !important; margin: 0 8px 0 0 !important; cursor: pointer; width: 14px; height: 14px; vertical-align: middle;" />
						${region}
					</label>
				</li>
			`);
		});

		this.updateRegionDropdownUI();
	}

	updateRegionDropdownUI() {
		const self = this;
		const container = this.page.main.find("#region-dropdown-container");
		if (!container.length) return;

		// Update checkboxes state
		const checkboxes = container.find(".region-checkbox");
		checkboxes.each(function () {
			const region = $(this).val();
			$(this).prop("checked", self.state.selectedRegions.includes(region));
		});

		// Update "All Regions" checkbox state
		const allCheckbox = container.find("#region-all-checkbox");
		const allSelected = checkboxes.length > 0 && checkboxes.length === self.state.selectedRegions.length;
		const noneSelected = self.state.selectedRegions.length === 0;

		if (noneSelected) {
			allCheckbox.prop("checked", true);
			allCheckbox.prop("indeterminate", false);
		} else if (allSelected) {
			allCheckbox.prop("checked", true);
			allCheckbox.prop("indeterminate", false);
		} else {
			allCheckbox.prop("checked", false);
			allCheckbox.prop("indeterminate", true);
		}

		// Update label
		const label = container.find("#region-dropdown-label");
		if (noneSelected) {
			label.text("All Regions");
		} else if (allSelected) {
			label.text("All Regions");
		} else if (self.state.selectedRegions.length === 1) {
			label.text(self.state.selectedRegions[0]);
		} else {
			label.text(`${self.state.selectedRegions.length} Regions`);
		}
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
				</div>`,
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
					(zone) =>
						this.getLocationIdentifier(zone) ===
						this.getLocationIdentifier(branch.zone),
				),
			);
		}

		// 3. Region filter
		if (this.state.selectedRegions && this.state.selectedRegions.length > 0) {
			filtered = filtered.filter((branch) =>
				this.state.selectedRegions.some(
					(region) =>
						this.getLocationIdentifier(region) ===
						this.getLocationIdentifier(branch.region),
				),
			);
		}

		// 4. Branch search term filter (supports comma-separated multi-search)
		if (this.state.branchSearchTerm) {
			const searchTerms = this.state.branchSearchTerm.toLowerCase().split(",").map(s => s.trim()).filter(Boolean);
			if (searchTerms.length > 0) {
				filtered = filtered.filter((branch) => {
					const branchName = (branch.branch || "").toLowerCase();
					const solId = (branch.sol_id || "").toLowerCase();
					return searchTerms.some(term => branchName.includes(term) || solId.includes(term));
				});
			}
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
			                <th rowspan="2" class="sr-col">Sr</th>
			                <th rowspan="2" class="zone-col">Zone/Region</th>
			                <th rowspan="2" class="branches-col">Branches</th>
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
			let highlightStyle = "";
			if (monthIndex === currentMonth && monthYear === currentYear) {
				const currentDay = today.getDate();
				const remainingDays = getRemainingWorkingDaysExcludingSundays(currentYear, currentMonth, currentDay);

				if (remainingDays >= 0) {
					daysLeftIndicator = `
						<br>
						<span class="days-left-indicator">
							${remainingDays} Working Day${remainingDays !== 1 ? "s" : ""} Left
						</span>
					`;
				}
				highlightStyle = `background: #6ca8ac !important; color: #ffffff !important; border-bottom: 2px solid #558a8e !important;`;
			}

			html += `<th colspan="3" ${highlightStyle ? `style="${highlightStyle}"` : ""}>${displayYear}${daysLeftIndicator}</th>`;
		});

		html += '</tr><tr class="zone-table-subheader">';

		months.forEach(() => {
			html += "<th>Target</th><th>Ach</th><th>ACH %</th>";
		});

		html += "</tr></thead><tbody>";

		const styleId = "days-left-indicator-style";
		if (!document.getElementById(styleId)) {
			const style = document.createElement("style");
			style.id = styleId;
			style.innerHTML = `
                @keyframes smooth-blink {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.75; }
                }
                .days-left-indicator {
                    display: inline-block;
                    background-color: #fef08a !important;
                    color: #854d0e !important;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-weight: 700;
                    animation: smooth-blink 1.8s ease-in-out infinite;
                    font-size: 10px;
                    margin-top: 4px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
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

		// Grand Total Row (Sticky Vertically and Horizontally)
		html += `<tfoot style="color: #ffffff; font-weight: bold; border-top: 2px solid #3d7579;">`;
		html += `<tr style="height: 40px;">`;
		html += `<td colspan="2" style="position: sticky; left: 0; bottom: 0; z-index: 9; background-color: #264a4d !important; color: #ffffff !important; text-align: left; padding-left: 12px; text-transform: uppercase; letter-spacing: 1px; border-right: none !important; box-shadow: inset -1px 0 0 #3d7579 !important;">TOTAL</td>`;
		html += `<td class="branches-col" style="position: sticky; left: 230px; bottom: 0; z-index: 9; background-color: #264a4d !important; color: #ffffff !important; text-align: center; border-right: none !important; box-shadow: inset -2px 0 0 #3d7579 !important;">${grandTotals.branches}</td>`;

		months.forEach((month) => {
			const totalTarget = grandTotals[month.key].target;
			const totalAchievement = grandTotals[month.key].achievement;
			const overallPercentage = totalTarget > 0 ? (totalAchievement / totalTarget) * 100 : 0;

			const monthDate = new Date(month.date);
			const monthIndex = monthDate.getMonth();
			const monthYear = monthDate.getFullYear();
			const isCurrentMonth = (monthIndex === currentMonth && monthYear === currentYear);

			const cellBg = isCurrentMonth ? "#6ca8ac !important" : "#264a4d !important";

			html += `
                 <td style="position: sticky; bottom: 0; z-index: 7; background-color: ${cellBg}; color: #ffffff !important;">${this.formatNumber(totalTarget)}</td>
                 <td style="position: sticky; bottom: 0; z-index: 7; background-color: ${cellBg}; color: #ffffff !important;">${this.formatNumber(totalAchievement)}</td>
                 <td style="position: sticky; bottom: 0; z-index: 7; background-color: ${cellBg}; color: #ffffff !important;">
 					<div style="display: flex; align-items: center; gap: 8px; justify-content: center;">
 						<span class="pct-value" style="color: ${isCurrentMonth ? "#ffffff !important" : this.getPctColor(overallPercentage)}; min-width: 45px; text-align: right; font-weight: bold;">${Math.round(overallPercentage)}%</span>
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
		html += `<td class="sr-col">${sr}</td>`;
		html += `<td class="zone-col"><span class="zone-toggle">${isExpanded ? "▼" : "▶"}</span> ${zoneName}</td>`;
		html += `<td class="branches-col branch-drilldown" data-zone="${zoneName}" title="Click to view branches in ${zoneName}">${branchCount}</td>`;

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
									)}; min-width: 45px; text-align: right;">${Math.round(mdata.percentage)}%</span>
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

		html += `<td class="sr-col">${sr}</td>`;
		html += `<td class="zone-col" style="padding-left: 30px;">${regionItem.region}</td>`;
		html += `<td class="branches-col branch-drilldown" data-zone="${zoneName}" data-region="${regionItem.region}" title="Click to view branches in ${regionItem.region}">${branchCount}</td>`;

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
									)}; min-width: 45px; text-align: right;">${Math.round(mdata.percentage)}%</span>
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
						<th rowspan="2">ACH %</th>
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
					<td>
						<div style="display: flex; align-items: center; gap: 8px; justify-content: center;">
							<span class="pct-value" style="color: ${this.getPctColor(zonePercent)}; min-width: 45px; text-align: right;">${Math.round(zonePercent)}%</span>
							${this.renderProgressBar(zonePercent)}
						</div>
					</td>
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
						<td>
							<div style="display: flex; align-items: center; gap: 8px; justify-content: center;">
								<span class="pct-value" style="color: ${this.getPctColor(rPercent)}; min-width: 45px; text-align: right;">${Math.round(rPercent)}%</span>
								${this.renderProgressBar(rPercent)}
							</div>
						</td>
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
			const percentage = totalBranches > 0 ? (count / totalBranches) * 100 : 0;

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
                        <span class="category-percentage-share" style="color: ${this.getPctColor(percentage)}; font-weight: 600;">• ${Math.round(percentage)}%</span>
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
		this.state.selectedRegions = region ? [region] : [];
		this.state.drillDownActive = true;

		// Update filter UI elements to reflect the change
		this.updateRegionDropdownUI();
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
		if (this.state.viewType === "Monthly" && this.state.selectedMonth) {
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
				branch.rowStyle = "";
			} else {
				const top25_index = Math.floor(total * 0.25);
				const next25_index = Math.floor(total * 0.5);
				const mid25_index = Math.floor(total * 0.75);

				if (index < top25_index) {
					branch.performanceSegment = "Top 25%";
					branch.rowStyle = "";
				} else if (index < next25_index) {
					branch.performanceSegment = "Next 25%";
					branch.rowStyle = "";
				} else if (index < mid25_index) {
					branch.performanceSegment = "Mid 25%";
					branch.rowStyle = "";
				} else {
					branch.performanceSegment = "Bottom 25%";
					branch.rowStyle = "";
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
					<th rowspan="2" class="segment-col">Segments</th>
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
			let highlightStyle = "";
			if (monthIndex === currentMonth && monthYear === currentYear) {
				const currentDay = today.getDate();
				const remainingDays = getRemainingWorkingDaysExcludingSundays(currentYear, currentMonth, currentDay);

				if (remainingDays >= 0) {
					daysLeftIndicator = `
										<br>
										<span class="days-left-indicator">
											${remainingDays} Working Day${remainingDays !== 1 ? "s" : ""} Left
										</span>
									`;
				}
				highlightStyle = `background: #6ca8ac !important; color: #ffffff !important; border-bottom: 2px solid #558a8e !important;`;
			}

			header += `<th colspan="4" class="month-col" ${highlightStyle ? `style="${highlightStyle}"` : ""}>${displayYear}${daysLeftIndicator}</th>`;
		});
		header += `</tr><tr class="branch-table-subheader">`;

		months.forEach(() => {
			header += `
                <th>Category</th>
                <th>Target</th>
                <th>Ach.</th>
                <th>ACH %</th>
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
		html += `<td class="sr-col">${serialNo}</td>`;
		html += `<td class="branch-col">
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
		html += `<td class="segment-col">${segmentName}</td>`;

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
					<div style="display: flex; align-items: center; gap: 4px; justify-content: center;">
						<span class="pct-value" style="color: ${this.getPctColor(pct)}; min-width: 36px; text-align: right;">${Math.round(pct)}%</span>
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
		const hue = Math.min(120, Math.max(0, (pct / 100) * 120));
		const lightness = hue > 45 && hue < 75 ? "35%" : "40%";
		return `hsl(${hue}, 85%, ${lightness})`;
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
			const currentCount = filteredBranches.filter((b) => b.months[currentMonthKey]).length;
			const prevCount = filteredBranches.filter((b) => b.months[prevMonthKey]).length;
			if (prevCount > 0) {
				const diff = ((currentCount - prevCount) / prevCount) * 100;
				trendEl.text(`${diff >= 0 ? "+" : ""}${diff.toFixed(1)}% from last month`);
				trendEl
					.removeClass("success danger muted")
					.addClass(diff >= 0 ? "success" : "danger");
			} else {
				trendEl
					.text("New data this month")
					.removeClass("success danger")
					.addClass("muted");
			}
		} else {
			trendEl.text("Reporting Period").removeClass("success danger").addClass("muted");
		}

		// 2. Target Amount & Achievement - Sum from Zone Wise reaggregated data
		let totalTarget = 0;
		let totalAch = 0;
		reaggregatedZoneData.forEach((item) => {
			if (item.isZoneTotal) {
				if (this.state.viewType === "Quarterly" || this.state.viewType === "Yearly") {
					this.months.forEach((month) => {
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

		this.page.main.find("#summary-target-label").text(targetLabelText);
		this.page.main
			.find("#summary-achievement-amount")
			.text("₹" + this.formatCurrency(totalAch));

		// Achievement Percentage
		const pct = totalTarget > 0 ? (totalAch / totalTarget) * 100 : 0;
		const pctEl = this.page.main.find("#summary-achievement-pct");
		pctEl.text(Math.round(pct) + "% achieved");

		// Color transition from red to green based on percentage
		const hue = Math.min(120, Math.max(0, (pct / 100) * 120));
		const lightness = hue > 45 && hue < 75 ? "35%" : "40%";
		pctEl.css("color", `hsl(${hue}, 85%, ${lightness})`);
		pctEl.removeClass("success danger");

		// 3. Active Zones - Unique zones in reaggregated data
		const activeZonesCount = reaggregatedZoneData.filter((item) => item.isZoneTotal).length;
		this.page.main.find("#summary-active-zones").text(activeZonesCount + " Zones");
	}

	// ========================================================================
	// STYLES
	// ========================================================================
	setupStyles() {
		const styles = `
            <style>
                #date-selector-container .form-group {
                    margin-bottom: 0 !important;
                }

                /* Remove top margin of dashboard tables to eliminate header gap */
                .zone-wise-table,
                .branch-table,
                .agent-wise-table,
                .product-wise-table,
                .category-table-redesigned {
                    margin-top: 0 !important;
                }

                /* Outlined Inputs (Material Design Style) */
                .outlined-input-container {
                    position: relative;
                    display: inline-flex;
                    align-items: center;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    background: #ffffff;
                    height: 32px;
                    margin-top: 6px; /* space for overlapping label */
                    box-sizing: border-box;
                    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
                }

                #date-selector-container.outlined-input-container {
                    padding: 0 6px 0 10px;
                    width: 154px;
                }
                
                .fy-header-control.outlined-input-container {
                    padding: 0 6px 0 10px;
                }

                #month-selector-container.outlined-input-container {
                    padding: 0 6px 0 10px;
                    width: 140px;
                }

                #region-dropdown-container.outlined-input-container {
                    padding: 0 10px;
                    min-width: 170px;
                }

                .outlined-input-label {
                    position: absolute;
                    left: 10px;
                    top: -8px;
                    background: #ffffff;
                    padding: 0 4px;
                    font-size: 11px;
                    font-weight: 700;
                    color: #64748b;
                    pointer-events: none;
                    z-index: 10;
                    line-height: 1;
                    transition: color 0.15s ease-in-out;
                }

                /* Outlined selectors, inputs, & buttons styles */
                .outlined-input-container select,
                .outlined-input-container input:not([type="checkbox"]),
                .outlined-input-container button {
                    border: none !important;
                    background: transparent !important;
                    outline: none !important;
                    box-shadow: none !important;
                    font-size: 13px !important;
                    font-weight: 600 !important;
                    color: #1b263b !important;
                    height: 28px !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    width: 100% !important;
                }

                /* Frappe wrapper styling overrides to let it fit within container */
                #date-selector-container .frappe-control,
                #date-selector-container .form-group,
                #date-selector-container .control-input-wrapper,
                #date-selector-container .control-input {
                    display: inline-block !important;
                    width: 100% !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    height: 100% !important;
                }
                
                #date-selector-container .clearfix {
                    display: none !important;
                }

                /* Container hover/focus states */
                .outlined-input-container:hover {
                    border-color: #94a3b8;
                }

                .outlined-input-container:focus-within {
                    border-color: #417d81 !important;
                    box-shadow: 0 0 0 3px rgba(65, 125, 129, 0.15) !important;
                }

                .outlined-input-container:focus-within .outlined-input-label {
                    color: #417d81 !important;
                }

                /* Region Dropdown menu styling for perfect alignment */
                #region-dropdown-menu {
                    padding: 4px 0 !important;
                    border: 1px solid #cbd5e1 !important;
                    border-radius: 8px !important;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
                }

                #region-dropdown-menu li {
                    display: flex !important;
                    align-items: center !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    transition: background-color 0.15s ease !important;
                }

                #region-dropdown-menu li:hover {
                    background-color: #f1f5f9 !important;
                }

                #region-dropdown-menu label {
                    display: inline-flex !important;
                    align-items: center !important;
                    width: 100% !important;
                    margin: 0 !important;
                    padding: 8px 16px !important;
                    font-size: 13px !important;
                    font-weight: 500 !important;
                    color: #1b263b !important;
                    cursor: pointer !important;
                    user-select: none !important;
                }

                #region-dropdown-menu input[type="checkbox"] {
                    position: relative !important;
                    margin: 0 10px 0 0 !important;
                    padding: 0 !important;
                    width: 15px !important;
                    height: 15px !important;
                    cursor: pointer !important;
                }

                .format-toggle-btn.active {
                    background-color: #417d81 !important;
                    border-color: #417d81 !important;
                    color: #ffffff !important;
                    font-weight: 700 !important;
                }
                .format-toggle-btn:not(.active) {
                    background-color: #ffffff !important;
                    border-color: #cbd5e1 !important;
                    color: #1e293b !important;
                    font-weight: 500 !important;
                }
                .format-toggle-btn:not(.active):hover {
                    background-color: #f1f5f9 !important;
                    border-color: #94a3b8 !important;
                    color: #0f172a !important;
                }

                /* Filter Tags Styles - Stacked vertically: Zone on top, Category below */
                .filter-tags-row {
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    margin-bottom: 6px;
                    width: 100%;
                }
                .zone-filter-container {
                    width: 100%;
                    padding-bottom: 10px;
                    border-bottom: 1px dashed #d1d5db;
                }
                .category-filter-container {
                    width: 100%;
                    padding-top: 4px;
                }
                .filter-tags-container {
                    display: flex;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 10px;
                    padding: 6px 12px;
                    background: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
                    align-self: stretch; /* Forces identical height stretch */
                    box-sizing: border-box;
                }

                .filter-group {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    width: 100%;
                }

                .filter-group-label {
                    font-size: 13px;
                    font-weight: 700;
                    color: #0f172a;
                    white-space: nowrap;
                }

                @media (max-width: 991px) {
                    .filter-tags-row {
                        gap: 8px;
                    }
                    .filter-tags-container {
                        padding: 4px 8px;
                        gap: 6px;
                    }
                    .filter-group {
                        gap: 6px;
                    }
                    .filter-group-label {
                        font-size: 12px;
                    }
                }

                .filter-tags {
                    display: flex;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 8px;
                    flex: 1 1 0;
                    min-width: 0;
                }

                #zone-tags {
                    gap: 5px;
                }

                .filter-tag {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 8px 18px;
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 700;
                    color: #1e293b;
                    cursor: pointer;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
                    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .zone-tag {
                    padding: 8px 18px;
                    gap: 6px;
                    font-size: 13px;
                }

                .zone-tag .filter-tag-count {
                    padding: 3px 8px;
                    font-size: 11px;
                }

                .zone-tag-content {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    line-height: 1.2;
                }

                .zone-tag-pct {
                    font-size: 11px;
                    font-weight: 700;
                    color: #64748b;
                    line-height: 1;
                    margin-left: auto;
                }

                .filter-tag:hover {
                    background: #f8fafc;
                    border-color: #cbd5e1;
                    transform: translateY(-1px);
                    text-decoration: none;
                }

                .filter-tag:active {
                    transform: scale(0.96);
                    transition: transform 0.1s ease;
                }

                @keyframes capsuleGlow {
                    0% { box-shadow: 0 0 0 0 rgba(13, 148, 136, 0); }
                    50% { box-shadow: 0 0 8px 3px rgba(13, 148, 136, 0.3); }
                    100% { box-shadow: 0 0 0 0 rgba(13, 148, 136, 0); }
                }

                .filter-tag.active {
                    background: #0d9488 !important;
                    border-color: #0d9488 !important;
                    color: #ffffff !important;
                    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
                    animation: capsuleGlow 0.4s ease-out;
                }

                .filter-tag-count {
                    background: #f1f5f9;
                    color: #64748b;
                    padding: 4px 10px;
                    border-radius: 9999px;
                    font-size: 12px;
                    font-weight: 700;
                    transition: all 0.2s ease;
                }

                .filter-tag.active .filter-tag-count {
                    background: rgba(255, 255, 255, 0.25) !important;
                    color: #ffffff !important;
                }

                .category-tag {
                    flex-direction: row;
                    align-items: center;
                    justify-content: center;
                    padding: 8px 14px;
                    gap: 6px !important;
                    font-size: 13px;
                    font-weight: 600;
                }

                .category-tag .filter-tag-count {
                    padding: 3px 8px;
                    font-size: 10px;
                }

                .category-tag-pct {
                    font-size: 11px;
                    font-weight: 700;
                    color: #64748b;
                    line-height: 1;
                    margin-left: auto;
                }

                .category-tag.active .category-tag-pct {
                    color: rgba(255, 255, 255, 0.85) !important;
                }

                .category-tag-content {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    line-height: 1.2;
                }

                /* Category-specific Active Colors */
                .category-tag[data-category="Pinnacle"].active {
                    background-color: #10b981 !important;
                    border-color: #10b981 !important;
                    color: #ffffff !important;
                    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
                }
                .category-tag[data-category="Master"].active {
                    background-color: #14b8a6 !important;
                    border-color: #14b8a6 !important;
                    color: #ffffff !important;
                    box-shadow: 0 4px 12px rgba(20, 184, 166, 0.25);
                }
                .category-tag[data-category="Accelerator"].active {
                    background-color: #3b82f6 !important;
                    border-color: #3b82f6 !important;
                    color: #ffffff !important;
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
                }
                .category-tag[data-category="Starter"].active {
                    background-color: #f59e0b !important;
                    border-color: #f59e0b !important;
                    color: #ffffff !important;
                    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
                }
                .category-tag[data-category="Learner"].active {
                    background-color: #ef4444 !important;
                    border-color: #ef4444 !important;
                    color: #ffffff !important;
                    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
                }
                .category-tag[data-category="Zero Level"].active {
                    background-color: #dc2626 !important;
                    border-color: #dc2626 !important;
                    color: #ffffff !important;
                    box-shadow: 0 4px 12px rgba(220, 38, 38, 0.25);
                }

                /* Ensure active category tag left border looks clean */
                .category-tag.active {
                    border-left-width: 1px !important;
                }

                /* Toggle Button Styles */
                .btn-group .btn {
                    background: #fff;
                    border: 1px solid #cbd5e1;
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

                /* Tab Styles (Active Capsule, Inactive Flat) */
                .tab-btn {
                    padding: 6px 16px !important;
                    background: transparent !important;
                    border: none !important;
                    color: #64748b !important;
                    font-weight: 600 !important;
                    font-size: 13px !important;
                    cursor: pointer !important;
                    border-radius: 9999px !important;
                    transition: all 0.15s ease-in-out !important;
                    outline: none !important;
                    margin: 0 !important;
                }

                .tab-btn:hover {
                    color: #417d81 !important;
                    background: rgba(65, 125, 129, 0.08) !important;
                }

                .tab-btn.active {
                    background: #417d81 !important;
                    color: #ffffff !important;
                    font-weight: 700 !important;
                    box-shadow: 0 4px 10px rgba(65, 125, 129, 0.25) !important;
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
                    border: 1px solid #cbd5e1;
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
                    border: 1px solid #cbd5e1;
                    text-align: center;
                }

                .category-table-subheader th {
                    background: #1b263b;
                    color: #e0e1dd;
                    padding: 8px;
                    font-size: 11px;
                    border: 1px solid #cbd5e1;
                }

                .category-table td {
                    padding: 10px 8px;
                    border: 1px solid #cbd5e1;
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
                    background: #e2e8f0 !important;
                }
                .branch-table-row:hover td.sr-col,
                .branch-table-row:hover td.branch-col,
                .branch-table-row:hover td.segment-col {
                    background: #e2e8f0 !important;
                }

                .branch-table thead {
                    position: sticky;
                    top: 0;
                    z-index: 10;
                }

                .branch-table td {
                    padding: 10px 8px;
                    border: 1px solid #cbd5e1;
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
                    border: 1px solid #cbd5e1;
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
                    background: linear-gradient(180deg, #3d7579 0%, #346569 100%) !important;
                    color: #ffffff !important;
                    font-weight: 600;
                    padding: 12px 15px;
                    text-align: left !important;
                    border: 1px solid #2d5659 !important;
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
                    border-top: 2px solid #3d7579;
                }
                .category-total-row {
                    background-color: #264a4d !important;
                }
                .category-total-row td {
                    font-weight: 700;
                    font-size: 15px;
                    color: #ffffff !important;
                    border-color: #3d7579 !important;
                }
                .total-movement-cell {
                    cursor: pointer;
                }

                @keyframes progress-bar-stripes {
                  from { background-position: 40px 0; }
                  to { background-position: 0 0; }
                }

                .progress-container-3d {
                    flex: 1;
                    height: 10px;
                    background-color: #e9ecef;
                    border-radius: 6px;
                    overflow: hidden;
                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
                    position: relative;
                    min-width: 30px;
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
                    gap: 10px;
                    margin-bottom: 12px;
                    padding: 2px 0;
                    flex-wrap: wrap;
                }
                .summary-card {
                    background: #fff;
                    border-radius: 8px;
                    padding: 4px 12px;
                    flex: 1;
                    min-width: 200px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
                    border: 1px solid #cbd5e1;
                    transition: transform 0.2s ease;
                }
                .summary-card:hover {
                    transform: translateY(-2px);
                }
                .summary-info {
                    display: flex;
                    flex-direction: column;
                    gap: 1px;
                }
                .summary-label {
                    font-size: 11px;
                    color: #64748b;
                    font-weight: 600;
                }
                .summary-value {
                    font-size: 18px;
                    font-weight: 800;
                    color: #1e293b;
                    letter-spacing: -0.3px;
                }
                .summary-subtext {
                    font-size: 10px;
                    font-weight: 600;
                    margin-top: 1px;
                }
                .summary-subtext.success { color: #10b981; }
                .summary-subtext.danger { color: #ef4444; }
                .summary-subtext.muted { color: #94a3b8; }
                
                .summary-icon-box {
                    width: 26px;
                    height: 26px;
                    background: linear-gradient(135deg, #417d81 0%, #346569 100%);
                    border-radius: 5px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #fff;
                    font-size: 12px;
                    box-shadow: 0 2px 6px rgba(65, 125, 129, 0.1);
                }

                @keyframes redBlink {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.35; }
                }
                .days-left-blink {
                    color: #ef4444 !important;
                    font-weight: 700;
                    animation: redBlink 1s ease-in-out infinite;
                }

                /* MIS Dashboard & Toggle Custom Styles */
                .dashboard-header-toggle-wrapper {
                    position: absolute;
                    left: 50%;
                    top: 14px;
                    transform: translateX(-50%);
                    z-index: 100;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .dashboard-toggle-switch-container {
                    display: inline-flex;
                    align-items: center;
                    background: #f8fafc;
                    padding: 2px;
                    border-radius: 6px;
                    border: 1px solid #cbd5e1;
                    font-family: 'Inter', sans-serif;
                }
                .dashboard-toggle-btn {
                    border: none !important;
                    background: transparent !important;
                    padding: 4px 10px !important;
                    font-size: 11px !important;
                    font-weight: 600 !important;
                    color: #64748b !important;
                    border-radius: 4px !important;
                    cursor: pointer !important;
                    transition: all 0.15s ease-in-out !important;
                    box-shadow: none !important;
                    line-height: 1 !important;
                }
                .dashboard-toggle-btn.active {
                    background: #ffffff !important;
                    color: #417d81 !important;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
                }
                .dashboard-toggle-btn:hover:not(.active) {
                    color: #1e293b !important;
                }
                .mis-report-tab-btn {
                    padding: 6px 16px !important;
                    background: transparent !important;
                    border: none !important;
                    color: #64748b !important;
                    font-weight: 600 !important;
                    font-size: 13px !important;
                    cursor: pointer !important;
                    border-radius: 9999px !important;
                    transition: all 0.15s ease-in-out !important;
                    outline: none !important;
                    margin: 0 !important;
                }
                .mis-report-tab-btn:hover {
                    color: #417d81 !important;
                    background: rgba(65, 125, 129, 0.08) !important;
                }
                .mis-report-tab-btn.active {
                    background: #417d81 !important;
                    color: #ffffff !important;
                    font-weight: 700 !important;
                    box-shadow: 0 4px 10px rgba(65, 125, 129, 0.25) !important;
                }
                .mis-table-body tr:hover {
                    background-color: #f8fafc !important;
                }
                @media (max-width: 768px) {
                    .dashboard-header-toggle-wrapper {
                        position: static !important;
                        transform: none !important;
                        margin: 10px auto !important;
                        width: 100%;
                        justify-content: center;
                    }
                }
            </style>
        `;

		$("head").append(styles);
	}

	setupHeaderToggle() {
		const self = this;
		const header = $(this.page.wrapper || ".frappe-page:visible").find(".page-head-row").length 
			? $(this.page.wrapper || ".frappe-page:visible").find(".page-head-row") 
			: $(this.page.wrapper || ".frappe-page:visible").find(".page-head .container");

		if (!header.length) return;

		// Make sure header has relative position for absolute centering of toggle
		header.css("position", "relative");

		// Remove any existing toggle first to prevent duplicates
		header.find(".dashboard-header-toggle-wrapper").remove();

		const toggleHtml = `
			<div class="dashboard-header-toggle-wrapper">
				<div class="dashboard-toggle-switch-container">
					<button type="button" class="dashboard-toggle-btn active" data-value="drishti">Drishti</button>
					<button type="button" class="dashboard-toggle-btn" data-value="mis">MIS Reports</button>
				</div>
			</div>
		`;

		header.append(toggleHtml);

		// Handle click events
		header.off("click", ".dashboard-toggle-btn").on("click", ".dashboard-toggle-btn", function() {
			const val = $(this).data("value");
			header.find(".dashboard-toggle-btn").removeClass("active");
			$(this).addClass("active");
			self.switchDashboardMode(val);
			self.updateUrlFromState();
		});
	}

	switchDashboardMode(mode) {
		this.state.dashboardMode = mode;
		if (mode === "drishti") {
			if (this.mis_container) this.mis_container.hide();
			if (this.drishti_container) this.drishti_container.show();
			$(this.page.wrapper).find("#drishti-subtitle").show();
			$("#drishti-header-timer").show();
			this.loadData();
		} else {
			if (this.drishti_container) this.drishti_container.hide();
			if (this.mis_container) {
				this.mis_container.show();
			} else {
				this.initMisReportsContainer();
			}
			$(this.page.wrapper).find("#drishti-subtitle").hide();
			$("#drishti-header-timer").hide();
		}
	}

	initMisReportsContainer() {
		this.mis_container = $('<div id="mis-reports-container" style="border: 1px solid #cbd5e1; padding: 16px; background: #fff; border-radius: 8px; margin-top: 6px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);"></div>').appendTo(this.page.main);
		
		const selectorHtml = `
			<div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; margin-bottom: 16px; width: 100%;">
				<div style="display: flex; gap: 12px;" id="mis-report-selector-tabs">
				</div>
			</div>
			<div id="mis-report-content-area" style="min-height: 200px;"></div>
		`;
		this.mis_container.html(selectorHtml);

		const self = this;
		const tabSelectorContainer = this.mis_container.find("#mis-report-selector-tabs");
		this.misReportsList.forEach((report, index) => {
			const activeClass = index === 0 ? "active" : "";
			tabSelectorContainer.append(`
				<button class="mis-report-tab-btn ${activeClass}" data-report-id="${report.id}">
					${report.name}
				</button>
			`);
		});

		this.mis_container.on("click", ".mis-report-tab-btn", function() {
			self.mis_container.find(".mis-report-tab-btn").removeClass("active");
			$(this).addClass("active");

			const reportId = $(this).data("report-id");
			self.renderMisReport(reportId);
		});

		if (this.misReportsList.length > 0) {
			this.renderMisReport(this.misReportsList[0].id);
		}
	}

	renderMisReport(reportId) {
		const report = this.misReportsList.find(r => r.id === reportId);
		const contentArea = this.mis_container.find("#mis-report-content-area");
		if (report && contentArea.length) {
			if (typeof report.render === "function") {
				report.render(contentArea, this);
			} else {
				contentArea.html('<p style="color: #64748b; padding: 20px;">No custom renderer provided for this report.</p>');
			}
		}
	}
}
