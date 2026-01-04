frappe.pages["branch-profile"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Branch Profile",
		single_column: true,
	});

	/* ---------------- CSS ---------------- */
	$(`<style>
		/* Prevent horizontal scroll */
		body, html {
			overflow-x: hidden;
			width: 100%;
		}
		
		/* Global Variables & Base Styles - LinkedIn Style */
		:root {
			--transition-base: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
			--transition-fast: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
			--shadow-sm: 0 0 0 1px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.08);
			--shadow-md: 0 0 0 1px rgba(0, 0, 0, 0.08), 0 4px 12px rgba(0, 0, 0, 0.12);
			--shadow-lg: 0 0 0 1px rgba(0, 0, 0, 0.08), 0 8px 24px rgba(0, 0, 0, 0.16);
			--radius-sm: 4px;
			--radius-md: 8px;
			--radius-lg: 12px;
			--radius-full: 9999px;
			--linkedin-bg: #f3f2ef;
			--linkedin-white: #ffffff;
			--linkedin-text: #000000;
			--linkedin-text-secondary: #666666;
			--linkedin-text-muted: #8e8e8e;
			--linkedin-blue: #0a66c2;
			--linkedin-blue-hover: #004182;
			--linkedin-border: rgba(0, 0, 0, 0.08);
		}

		.branch-profile-container {
			padding: 20px 0;
			font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
			background: transparent;
			min-height: 100vh;
			-webkit-font-smoothing: antialiased;
			-moz-osx-font-smoothing: grayscale;
			overflow-x: hidden;
			width: 100%;
			box-sizing: border-box;
		}

		/* Search Bar - Integrated in Tab Header */
		.search-in-tabs {
			display: flex;
			align-items: center;
			gap: 12px;
			padding: 0 16px;
			margin-bottom: 0;
			margin-left: auto;
		}

		.search-in-tabs label {
			font-weight: 500;
			color: var(--linkedin-text-secondary);
			font-size: 14px;
			white-space: nowrap;
		}

		#search-field {
			flex: 1;
			max-width: 280px;
		}

		#search-field input {
			background: var(--linkedin-white);
			border: 1px solid var(--linkedin-border);
			border-radius: var(--radius-sm);
			padding: 8px 12px;
			font-size: 14px;
			color: var(--linkedin-text);
			transition: var(--transition-base);
			width: 100%;
		}

		#search-field input:focus {
			outline: none;
			border-color: var(--linkedin-blue);
			box-shadow: 0 0 0 2px rgba(10, 102, 194, 0.1);
		}

		#search-field input::placeholder {
			color: var(--linkedin-text-muted);
		}

		/* Dashboard Grid - LinkedIn Style */
		.dashboard-grid {
			display: grid;
			grid-template-columns: 1fr 1.5fr 1fr;
			gap: 12px;
			width: 100%;
			padding: 0 24px;
			box-sizing: border-box;
			overflow-x: hidden;
		}

		.left-column, .right-column {
			overflow: visible !important;
			position: sticky;
			top: 20px;
			align-self: start;
			height: fit-content;
		}
		
		.left-column .dashboard-card,
		.right-column .dashboard-card {
			overflow: visible !important;
			max-height: none !important;
			height: auto !important;
		}

		.middle-column {
			overflow-y: visible;
		}
		
		.middle-column .dashboard-card {
			display: flex;
			flex-direction: column;
			max-height: calc(100vh - 40px);
			overflow: hidden;
		}
		
		.middle-column .tab-container {
			display: flex;
			flex-direction: column;
			height: 100%;
			min-height: 0;
		}

		@media (max-width: 1200px) {
			.dashboard-grid {
				grid-template-columns: 1fr;
				gap: 12px;
				padding: 0 16px;
			}
			
			.left-column, .right-column, .middle-column {
				position: static;
				max-height: none;
				overflow-y: visible;
			}
		}

		/* Card Styles - LinkedIn Style */
		.dashboard-card {
			background: var(--linkedin-white);
			border-radius: var(--radius-md);
			padding: 16px;
			box-shadow: var(--shadow-sm);
			margin-bottom: 12px;
			border: 1px solid var(--linkedin-border);
			transition: var(--transition-base);
			opacity: 0;
			animation: fadeInUp 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
		}

		.dashboard-card:nth-child(1) { animation-delay: 0.05s; }
		.dashboard-card:nth-child(2) { animation-delay: 0.1s; }
		.dashboard-card:nth-child(3) { animation-delay: 0.15s; }
		.dashboard-card:nth-child(4) { animation-delay: 0.2s; }

		.dashboard-card:hover {
			box-shadow: var(--shadow-md);
		}

		@keyframes fadeInUp {
			from {
				opacity: 0;
				transform: translateY(4px);
			}
			to {
				opacity: 1;
				transform: translateY(0);
			}
		}

		.card-header {
			font-size: 16px;
			font-weight: 600;
			color: var(--linkedin-text);
			margin-bottom: 16px;
			padding-bottom: 12px;
			border-bottom: 1px solid var(--linkedin-border);
			line-height: 1.5;
		}

		/* Branch Information - LinkedIn Style */
		.branch-name-id {
			font-size: 20px;
			font-weight: 600;
			color: var(--linkedin-text);
			margin-bottom: 16px;
			line-height: 1.4;
		}

		.branch-detail-row {
			display: flex;
			align-items: flex-start;
			margin-bottom: 10px;
			font-size: 14px;
			color: var(--linkedin-text-secondary);
			line-height: 1.5;
		}

		.branch-detail-label {
			font-weight: 500;
			min-width: 100px;
			color: var(--linkedin-text-muted);
			flex-shrink: 0;
		}

		.branch-detail-value {
			color: var(--linkedin-text);
			font-weight: 400;
		}

		.branch-address {
			margin-top: 16px;
			padding-top: 16px;
			border-top: 1px solid var(--linkedin-border);
			font-size: 14px;
			color: var(--linkedin-text-secondary);
			line-height: 1.6;
		}

		/* Branch Manager - LinkedIn Style */
		.manager-profile {
			display: flex;
			align-items: center;
			margin-bottom: 16px;
		}

		.manager-avatar {
			width: 56px;
			height: 56px;
			border-radius: var(--radius-full);
			background: var(--linkedin-blue);
			display: flex;
			align-items: center;
			justify-content: center;
			color: #fff;
			font-weight: 600;
			font-size: 20px;
			margin-right: 12px;
			flex-shrink: 0;
			transition: var(--transition-base);
		}

		.manager-avatar:hover {
			background: var(--linkedin-blue-hover);
		}

		.manager-name {
			font-size: 16px;
			font-weight: 600;
			color: var(--linkedin-text);
			margin-bottom: 4px;
			line-height: 1.4;
		}

		.manager-experience {
			font-size: 14px;
			color: var(--linkedin-text-secondary);
			line-height: 1.5;
		}

		.manager-detail {
			display: flex;
			align-items: center;
			margin-bottom: 8px;
			font-size: 14px;
			color: var(--linkedin-text-secondary);
			line-height: 1.5;
		}

		.manager-detail-label {
			font-weight: 500;
			min-width: 80px;
			color: var(--linkedin-text-muted);
			flex-shrink: 0;
		}

		/* Tabs - LinkedIn Style */
		.tab-container {
			margin-bottom: 0;
			display: flex;
			flex-direction: column;
			height: 100%;
		}

		.tab-header {
			display: flex;
			align-items: center;
			border-bottom: 1px solid var(--linkedin-border);
			margin-bottom: 16px;
			gap: 0;
			flex-wrap: wrap;
			position: sticky;
			top: 0;
			background: var(--linkedin-white);
			z-index: 10;
			padding-top: 0;
		}

		.tab-item {
			padding: 12px 16px;
			cursor: pointer;
			font-size: 14px;
			font-weight: 500;
			color: var(--linkedin-text-secondary);
			border-bottom: 2px solid transparent;
			margin-bottom: -1px;
			transition: var(--transition-base);
			position: relative;
			line-height: 1.5;
		}

		.tab-item:hover {
			color: var(--linkedin-text);
			background: rgba(0, 0, 0, 0.03);
		}

		.tab-item.active {
			color: var(--linkedin-blue);
			border-bottom-color: var(--linkedin-blue);
			font-weight: 600;
		}

		.tab-content {
			display: none;
			opacity: 0;
			transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
			overflow-y: auto;
			flex: 1;
			min-height: 0;
			max-height: calc(100vh - 180px);
		}

		.tab-content.active {
			display: block;
			opacity: 1;
		}

		/* Account Portfolio Summary - LinkedIn Style */
		.portfolio-grid {
			display: grid;
			grid-template-columns: repeat(2, 1fr);
			gap: 12px;
		}

		.portfolio-metric {
			background: var(--linkedin-bg);
			border: 1px solid var(--linkedin-border);
			border-radius: var(--radius-sm);
			padding: 16px;
			text-align: center;
			transition: var(--transition-base);
		}

		.portfolio-metric:hover {
			background: var(--linkedin-white);
			box-shadow: var(--shadow-sm);
		}

		.portfolio-metric-label {
			font-size: 12px;
			color: var(--linkedin-text-muted);
			font-weight: 500;
			margin-bottom: 8px;
			text-transform: uppercase;
			letter-spacing: 0.5px;
			line-height: 1.4;
		}

		.portfolio-metric-value {
			font-size: 24px;
			font-weight: 600;
			color: var(--linkedin-text);
			line-height: 1.2;
		}

		/* Branch Performance - LinkedIn Style */
		.performance-item {
			padding: 16px;
			background: var(--linkedin-bg);
			border-radius: var(--radius-sm);
			margin-bottom: 12px;
			border-left: 3px solid var(--linkedin-border);
			transition: var(--transition-base);
		}

		.performance-item:hover {
			background: var(--linkedin-white);
			box-shadow: var(--shadow-sm);
		}

		.performance-item:last-child {
			margin-bottom: 0;
		}

		.performance-header {
			display: flex;
			justify-content: space-between;
			align-items: center;
			margin-bottom: 10px;
		}

		.performance-period {
			font-size: 14px;
			font-weight: 600;
			color: var(--linkedin-text);
			line-height: 1.4;
		}

		.performance-status {
			padding: 4px 12px;
			border-radius: var(--radius-full);
			font-size: 11px;
			font-weight: 600;
			text-transform: uppercase;
			letter-spacing: 0.5px;
		}

		.status-learner, .status-starter {
			background: #fff3cd;
			color: #856404;
		}

		.status-master {
			background: #d1e7dd;
			color: #0f5132;
		}

		.performance-values {
			font-size: 14px;
			color: var(--linkedin-text-secondary);
			margin-bottom: 6px;
			line-height: 1.5;
		}

		.performance-percentage {
			font-size: 20px;
			font-weight: 600;
			color: var(--linkedin-text);
			line-height: 1.3;
		}

		/* Staff & Manpower - LinkedIn Style */
		.staff-grid {
			display: grid;
			grid-template-columns: repeat(3, 1fr);
			gap: 12px;
		}

		.staff-role-box {
			background: var(--linkedin-bg);
			border: 1px solid var(--linkedin-border);
			border-radius: var(--radius-sm);
			padding: 12px;
			text-align: center;
			transition: var(--transition-base);
		}

		.staff-role-box:hover {
			background: var(--linkedin-white);
			box-shadow: var(--shadow-sm);
		}

		.staff-role-label {
			font-size: 12px;
			color: var(--linkedin-text-muted);
			font-weight: 500;
			margin-bottom: 6px;
			text-transform: uppercase;
			letter-spacing: 0.5px;
			line-height: 1.4;
		}

		.staff-role-count {
			font-size: 22px;
			font-weight: 600;
			color: var(--linkedin-text);
			line-height: 1.2;
		}

		/* Empty State - LinkedIn Style */
		.empty-state {
			text-align: center;
			padding: 48px 24px;
			color: var(--linkedin-text-muted);
			font-size: 14px;
			line-height: 1.6;
		}

		/* Suggestions Dropdown - LinkedIn Style */
		#suggestions-dropdown {
			z-index: 999;
			border-radius: var(--radius-sm);
			overflow: hidden;
			box-shadow: var(--shadow-md);
			border: 1px solid var(--linkedin-border);
			background: var(--linkedin-white);
			animation: fadeInDown 0.2s cubic-bezier(0.4, 0, 0.2, 1);
		}

		@keyframes fadeInDown {
			from {
				opacity: 0;
				transform: translateY(-4px);
			}
			to {
				opacity: 1;
				transform: translateY(0);
			}
		}

		#suggestions-dropdown li {
			cursor: pointer;
			transition: var(--transition-fast);
			border: none;
			border-bottom: 1px solid var(--linkedin-border);
			background: var(--linkedin-white);
		}

		#suggestions-dropdown li:last-child {
			border-bottom: none;
		}

		#suggestions-dropdown li:hover {
			background: rgba(0, 0, 0, 0.03);
		}
	</style>`).appendTo("head");

	/* ---------------- HTML ---------------- */
	$(wrapper).find(".layout-main-section").html(`
		<div class="branch-profile-container">
			<div class="dashboard-grid">
				<div class="left-column">
					<div id="branch-info-card"></div>
					<div id="branch-manager-card"></div>
				</div>

				<div class="middle-column">
					<div class="dashboard-card">
						<div class="tab-container">
							<div class="tab-header">
								<div class="tab-item active" data-tab="business-metrics">Business Metrics</div>
								<div class="tab-item" data-tab="crm-customers">CRM & Customers</div>
								<div class="search-in-tabs">
									<label>Search:</label>
									<div id="search-field" style="position: relative;"></div>
								</div>
							</div>
							<div id="tab-business-metrics" class="tab-content active">
								<div id="account-portfolio-summary"></div>
							</div>
							<div id="tab-crm-customers" class="tab-content">
								<div class="empty-state">CRM & Customers data will be displayed here</div>
							</div>
						</div>
					</div>
				</div>

				<div class="right-column">
					<div id="branch-performance-card"></div>
					<div id="staff-manpower-card"></div>
				</div>
			</div>
		</div>
	`);

	// Initialize tab switching with smooth transitions
	$(".tab-item").on("click", function () {
		const tabId = $(this).data("tab");
		const $clickedTab = $(this);
		const $targetContent = $(`#tab-${tabId}`);

		// Smooth tab transition
		$(".tab-item").removeClass("active");
		$clickedTab.addClass("active");

		// Fade out current content, then fade in new content
		$(".tab-content.active").css("opacity", "0");
		setTimeout(() => {
			$(".tab-content").removeClass("active");
			$targetContent.addClass("active").css("opacity", "0");
			setTimeout(() => {
				$targetContent.css("opacity", "1");
			}, 10);
		}, 150);
	});

	init_sol_search(wrapper);

	/* -------- LOAD FROM URL -------- */
	const query = frappe.utils.get_query_params();
	if (query.sol_id) {
		$("#search-field input").val(query.sol_id);
		load_all_data(query.sol_id);
	}
};

/* ---------------- URL HANDLER ---------------- */
function update_url_sol(sol_id = null) {
	const url = new URL(window.location.href);
	if (sol_id) url.searchParams.set("sol_id", sol_id);
	else url.searchParams.delete("sol_id");
	window.history.pushState({}, "", url);
}

/* ---------------- SOL SEARCH ---------------- */
function init_sol_search(wrapper) {
	const control = new frappe.ui.form.ControlData({
		df: {
			fieldname: "sol",
			fieldtype: "Data",
			placeholder: "Type SOL ID or Branch Name",
		},
		parent: $(wrapper).find("#search-field"),
		render_input: true,
	});
	control.refresh();

	$(control.input).on("input", function () {
		const txt = $(this).val().trim();

		if (!txt) {
			$("#suggestions-dropdown").remove();
			update_url_sol(null);
			clear_all_cards();
			return;
		}

		frappe.call({
			method: "custom_report.custom_report.page.branch_profile.branch_profile.search_branches",
			args: { txt },
			callback: (r) => show_suggestions(control.input, r.message || []),
		});
	});
}

/* ---------------- AUTOCOMPLETE ---------------- */
function show_suggestions(input, list) {
	$("#suggestions-dropdown").remove();
	if (!list.length) return;

	let ul = $(
		`<ul id="suggestions-dropdown" class="list-group position-absolute w-100 shadow" style="z-index:999; max-width: 300px;"></ul>`
	);

	list.forEach((b) => {
		ul.append(`
			<li class="list-group-item" data-sol="${b.sol_id}">
				<b>${b.sol_id}</b> – ${b.branch}
			</li>
		`);
	});

	$(input).after(ul);

	ul.find("li").on("click", function () {
		const sol = $(this).data("sol");
		$(input).val(sol);
		ul.remove();

		update_url_sol(sol);
		load_all_data(sol);
	});
}

/* ---------------- LOAD ALL DATA ---------------- */
function load_all_data(sol) {
	load_branch_master(sol);
	load_branch_profile(sol);
}

/* ---------------- LEFT COLUMN: BRANCH INFORMATION ---------------- */
function load_branch_master(sol) {
	frappe.call({
		method: "custom_report.custom_report.page.branch_profile.branch_profile.get_branch_data",
		args: { sol_id: sol },
		callback: (r) => render_branch_info(r.message?.[0]),
	});
}

function render_branch_info(b) {
	if (!b) {
		$("#branch-info-card").html(
			`<div class="dashboard-card"><div class="empty-state">No Branch Found</div></div>`
		);
		return;
	}

	// Format established date if available
	const establishedDate = b.established_date || "15-Jan-2014";
	const address =
		b.address ||
		"Shri Ji Complex, Gayatri Mandir Road., opp. IndianOil, Gondia, Maharashtra 441614";

	const html = `
		<div class="dashboard-card" style="animation-delay: 0.05s;">
			<div class="card-header">Branch information</div>
			<div class="branch-name-id">${b.branch || "GONDIA"} - ${b.sol_id || "1001"}</div>
			<div class="branch-detail-row">
				<span class="branch-detail-label">Zone:</span>
				<span class="branch-detail-value">${b.zone || "ZONE -1"}</span>
			</div>
			<div class="branch-detail-row">
				<span class="branch-detail-label">Region:</span>
				<span class="branch-detail-value">${b.region || "REGION-2"}</span>
			</div>
			<div class="branch-detail-row">
				<span class="branch-detail-label">State:</span>
				<span class="branch-detail-value">${b.state || "MAHARASHTRA"}</span>
			</div>
			<div class="branch-detail-row">
				<span class="branch-detail-label">Established:</span>
				<span class="branch-detail-value">${establishedDate}</span>
			</div>
			<div class="branch-address">${address}</div>
		</div>
	`;

	$("#branch-info-card").html(html);
}

/* ---------------- LEFT COLUMN: BRANCH MANAGER ---------------- */
function load_branch_profile(sol) {
	frappe.call({
		method: "custom_report.custom_report.page.branch_profile.branch_profile.get_branch_profile_data",
		args: { sol_id: sol },
		callback: (r) => {
			// Use dummy data if no data returned
			const dummyData = {
				bm_name: "CHETAN DAYARAM RATHOD",
				bm_vintage: "8 YEARS EXPERIENCE",
				bm_phone: "8795357248",
				bm_email: "bm@sahayogmultistate.com",
				bm_doj: "10-Mar-2021",
				total_accounts: 6627,
				total_ytd_achievement: 8500000,
				total_closing_balance: 12500000,
				total_ytd_target: 10000000,
				month_achievement: 1400000,
				month_target: 2000000,
				yearly_achievement: 8500000,
				yearly_target: 10000000,
				bm_count: 1,
				bdo_count: 5,
				bde_count: 3,
				ro_count: 5,
				com_count: 1,
				bom_count: 2,
			};

			const data = r.message || dummyData;
			render_branch_manager(data);
			render_account_portfolio(data);
			render_branch_performance(data);
			render_staff_manpower(data);
		},
	});
}

function render_branch_manager(data) {
	// Always use dummy data as fallback
	const managerName = data.bm_name || "CHETAN DAYARAM RATHOD";
	const initials = managerName
		.split(" ")
		.map((n) => n[0])
		.join("")
		.substring(0, 2)
		.toUpperCase();
	const experience = data.bm_vintage || "8 YEARS EXPERIENCE";
	const phone = data.bm_phone || "8795357248";
	const email = data.bm_email || "bm@sahayogmultistate.com";
	const joinedDate = data.bm_doj || "10-Mar-2021";

	const html = `
		<div class="dashboard-card" style="animation-delay: 0.1s;">
			<div class="card-header">Branch Manager</div>
			<div class="manager-profile">
				<div class="manager-avatar">${initials}</div>
				<div>
					<div class="manager-name">${managerName}</div>
					<div class="manager-experience">${experience}</div>
				</div>
			</div>
			<div class="manager-detail">
				<span class="manager-detail-label">Phone:</span>
				<span>${phone}</span>
			</div>
			<div class="manager-detail">
				<span class="manager-detail-label">Email:</span>
				<span>${email}</span>
			</div>
			<div class="manager-detail">
				<span class="manager-detail-label">Joined:</span>
				<span>${joinedDate}</span>
			</div>
		</div>
	`;

	$("#branch-manager-card").html(html);
}

/* ---------------- MIDDLE COLUMN: ACCOUNT PORTFOLIO SUMMARY ---------------- */
function render_account_portfolio(data) {
	const totalAccounts = data.total_accounts || 6627;
	const totalYtdAchievement = data.total_ytd_achievement || 8500000;
	const totalClosingBalance = data.total_closing_balance || 12500000;
	const totalYtdTarget = data.total_ytd_target || 10000000;

	const html = `
		<div>
			<div class="card-header">Account Portfolio Summary</div>
			<div class="portfolio-grid">
				<div class="portfolio-metric">
					<div class="portfolio-metric-label">Total Accounts</div>
					<div class="portfolio-metric-value">${formatNumber(totalAccounts)}</div>
				</div>
				<div class="portfolio-metric">
					<div class="portfolio-metric-label">Total YTD Achievement</div>
					<div class="portfolio-metric-value">₹${formatCurrency(totalYtdAchievement)}</div>
				</div>
				<div class="portfolio-metric">
					<div class="portfolio-metric-label">Total Closing Balance</div>
					<div class="portfolio-metric-value">₹${formatCurrency(totalClosingBalance)}</div>
				</div>
				<div class="portfolio-metric">
					<div class="portfolio-metric-label">Total YTD Target</div>
					<div class="portfolio-metric-value">₹${formatCurrency(totalYtdTarget)}</div>
				</div>
			</div>
		</div>
	`;

	$("#account-portfolio-summary").html(html);
}

/* ---------------- RIGHT COLUMN: BRANCH PERFORMANCE ---------------- */
function render_branch_performance(data) {
	// Use dummy data with fallback
	const monthAchieved = data.month_achievement || 1400000;
	const monthTarget = data.month_target || 2000000;
	const monthPercent = Math.round((monthAchieved / monthTarget) * 100);
	const monthStatus = getPerformanceStatus(monthPercent);

	const ytdAchieved = data.total_ytd_achievement || 8500000;
	const ytdTarget = data.total_ytd_target || 10000000;
	const ytdPercent = Math.round((ytdAchieved / ytdTarget) * 100);
	const ytdStatus = getPerformanceStatus(ytdPercent);

	const yearlyAchieved = data.yearly_achievement || 8500000;
	const yearlyTarget = data.yearly_target || 10000000;
	const yearlyPercent = Math.round((yearlyAchieved / yearlyTarget) * 100);
	const yearlyStatus = getPerformanceStatus(yearlyPercent);

	const currentMonth = new Date().toLocaleString("default", { month: "short" }).toUpperCase();

	const html = `
		<div class="dashboard-card" style="animation-delay: 0.15s;">
			<div class="card-header">Branch Performance</div>
			<div class="performance-item">
				<div class="performance-header">
					<div class="performance-period">Month - ${currentMonth}</div>
					<div class="performance-status status-${monthStatus.toLowerCase()}">${monthStatus}</div>
				</div>
				<div class="performance-values">₹${formatCurrency(monthAchieved)} / ₹${formatCurrency(
		monthTarget
	)}</div>
				<div class="performance-percentage">${monthPercent}%</div>
			</div>
			<div class="performance-item">
<div class="performance-header">
<div class="performance-period">YTD</div>
<div class="performance-status status-${ytdStatus.toLowerCase()}">${ytdStatus}</div>
</div>
<div class="performance-values">₹formatCurrency(ytdAchieved)/₹{formatCurrency(ytdAchieved)} / ₹
formatCurrency(ytdAchieved)/₹{formatCurrency(ytdTarget)}
</div>
<div class="performance-percentage">${ytdPercent}%</div>
</div>
<div class="performance-item">
<div class="performance-header">
<div class="performance-period">Yearly</div>
<div class="performance-status status-${yearlyStatus.toLowerCase()}">${yearlyStatus}</div>
</div>
<div class="performance-values">₹formatCurrency(yearlyAchieved)/₹{formatCurrency(yearlyAchieved)} / ₹
formatCurrency(yearlyAchieved)/₹{formatCurrency(
		yearlyTarget
	)}
</div>
<div class="performance-percentage">${yearlyPercent}%</div>
</div>
</div>
`;
	$("#branch-performance-card").html(html);
}
/* ---------------- RIGHT COLUMN: STAFF & MANPOWER ---------------- */
function render_staff_manpower(data) {
	// Use dummy data with fallback
	const staffData = {
		"Branch Manager": data.bm_count || 1,
		BDO: data.bdo_count || 5,
		BDE: data.bde_count || 3,
		RO: data.ro_count || 5,
		COM: data.com_count || 1,
		BOM: data.bom_count || 2,
	};
	let staffHtml = "";
	Object.keys(staffData).forEach((role) => {
		staffHtml += `
		<div class="staff-role-box">
			<div class="staff-role-label">${role}</div>
			<div class="staff-role-count">${staffData[role]}</div>
		</div>
	`;
	});

	const html = `
	<div class="dashboard-card" style="animation-delay: 0.2s;">
		<div class="card-header">Staff & Manpower Details</div>
		<div class="staff-grid">
			${staffHtml}
		</div>
	</div>
`;

	$("#staff-manpower-card").html(html);
}
/* ---------------- HELPER FUNCTIONS ---------------- */
function clear_all_cards() {
	$("#branch-info-card").html("");
	$("#branch-manager-card").html("");
	$("#account-portfolio-summary").html("");
	$("#branch-performance-card").html("");
	$("#staff-manpower-card").html("");
}
function formatNumber(num) {
	if (!num) return "0";
	return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
function formatCurrency(num) {
	if (!num) return "0";
	// Convert to lakhs format for Indian currency
	const absNum = Math.abs(num);
	if (absNum >= 10000000) {
		return (num / 10000000).toFixed(2) + " Cr";
	} else if (absNum >= 100000) {
		return (num / 100000).toFixed(2) + " L";
	}
	return formatNumber(num);
}
function getPerformanceStatus(percent) {
	if (percent >= 80) return "Master";
	if (percent >= 50) return "Starter";
	return "Learner";
}
