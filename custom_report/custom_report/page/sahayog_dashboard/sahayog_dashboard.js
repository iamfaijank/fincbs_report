frappe.pages["sahayog_dashboard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Sahayog BI Dashboard",
		single_column: true,
	});

	new SahayogDashboard(page);
};

class SahayogDashboard {
	constructor(page) {
		this.page = page;
		this.data = null;
		this.collapsedZones = new Set();
		this.filters = {
			zone: "",
			from_date: "",
			to_date: "",
		};
		this.branchFilters = {};
		this.transactionFilters = {};
		this.init();
	}

	init() {
		this.setupStyles();
		this.createFilterSection();
		this.createTableStructure();
		this.createDrillDownModal();
		this.createBranchDrillDownModal();
		this.loadData();
	}

	getCategoryClass(category) {
		const categoryMap = {
			Accelerator: "category-accelerator",
			Pinacle: "category-pinacle",
			Master: "category-master",
			Learner: "category-learner",
			Starter: "category-starter",
			"Zero Level": "category-zero-level",
		};
		return categoryMap[category] || "";
	}

	setupStyles() {
		const styles = `
            <style>
                /* Global Reset */
                .page-content {
                    padding: 20px !important;
                    background: #F8FAFC;
                }
                
                /* Modern Filter Section */
                .filter-section {
                    background: white;
                    padding: 20px 25px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                    border: 1px solid #E2E8F0;
                }
                
                .filter-row {
                    display: flex;
                    gap: 16px;
                    align-items: flex-end;
                    flex-wrap: wrap;
                }
                
                .filter-group {
                    display: flex;
                    flex-direction: column;
                    min-width: 200px;
                }
                
                .filter-group label {
                    font-size: 11px;
                    font-weight: 600;
                    color: #64748B;
                    margin-bottom: 6px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .filter-group select,
                .filter-group input {
                    padding: 10px 14px;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    font-size: 14px;
                    color: #1E293B;
                    background: white;
                    transition: all 0.2s;
                }
                
                .filter-group select:focus,
                .filter-group input:focus {
                    outline: none;
                    border-color: #6366F1;
                    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
                }
                
                .apply-filter-btn {
                    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
                    color: white;
                    border: none;
                    padding: 10px 28px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
                }
                
                .apply-filter-btn:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 8px rgba(99, 102, 241, 0.3);
                }
                
                /* Main Table Container */
                .sahayog-dashboard-container {
                    width: 100%;
                    overflow-x: auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                    border: 1px solid #E2E8F0;
                }
                
                .sahayog-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 13px;
                }
                
                .sahayog-table td, 
                .sahayog-table th {
                    border: 1px solid #F1F5F9;
                    padding: 12px 16px;
                    text-align: right;
                    white-space: nowrap;
                }
                
                .sahayog-table .row-label {
                    text-align: left;
                    padding-left: 16px;
                }

                /* Modern Header */
                .sahayog-table thead th {
                    position: sticky;
                    top: 0;
                    background: linear-gradient(180deg, #1E293B 0%, #334155 100%);
                    color: white;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 14px 16px;
                    z-index: 100;
                    border: none;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                .sahayog-table col:nth-child(1) { width: 200px; }
                .sahayog-table col:nth-child(2) { width: 150px; }
                .sahayog-table col:nth-child(3) { width: 150px; }
                .sahayog-table col:nth-child(4) { width: 150px; }
                .sahayog-table col:nth-child(5) { width: 150px; }
                .sahayog-table col:nth-child(6) { width: 150px; }
                .sahayog-table col:nth-child(7) { width: 150px; }
                
                /* Zone Rows - Minimal Colors */
                .zone-row {
                    font-weight: 600;
                    font-size: 13px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .zone-row:hover {
                    background: #F8FAFC !important;
                }
                
                .zone-1-row { background-color: #EFF6FF; }
                .zone-2-row { background-color: #FAFAFA; }
                .zone-3-row { background-color: #FFF7ED; }
                .zone-4-row { background-color: #FEF2F2; }
                .zone-5-row { background-color: #F9FAFB; }
                .zone-6-row { background-color: #FFFBEB; }
                
                /* Category Rows - Subtle Gradient Colors */
                .category-row {
                    font-size: 13px;
                    transition: all 0.2s;
                }
                
                .category-row:hover {
                    transform: translateX(2px);
                }
                
                .category-row td.row-label {
                    padding-left: 40px !important;
                    font-weight: 500;
                }
                
                /* Minimal Category Colors */
                .category-accelerator {
                    background: linear-gradient(90deg, #ECFDF5 0%, #D1FAE5 100%) !important;
                    color: #065F46 !important;
                }
                
                .category-pinacle {
                    background: linear-gradient(90deg, #F0FDF4 0%, #DCFCE7 100%) !important;
                    color: #14532D !important;
                }
                
                .category-master {
                    background: linear-gradient(90deg, #FEFCE8 0%, #FEF9C3 100%) !important;
                    color: #713F12 !important;
                }
                
                .category-learner {
                    background: linear-gradient(90deg, #FFF7ED 0%, #FFEDD5 100%) !important;
                    color: #7C2D12 !important;
                }
                
                .category-starter {
                    background: linear-gradient(90deg, #FEF2F2 0%, #FEE2E2 100%) !important;
                    color: #7F1D1D !important;
                }
                
                .category-zero-level {
                    background: linear-gradient(90deg, #FEE2E2 0%, #FECACA 100%) !important;
                    color: #991B1B !important;
                }
                
                /* Clickable Elements */
                .branch-score-cell {
                    cursor: pointer;
                    font-weight: 700;
                    text-decoration: none;
                    position: relative;
                    color: #6366F1 !important;
                }
                
                .branch-score-cell::after {
                    content: '';
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 1px;
                    background: #6366F1;
                    transform: scaleX(0);
                    transition: transform 0.2s;
                }
                
                .branch-score-cell:hover::after {
                    transform: scaleX(1);
                }
                
                /* Grand Total */
                .grand-total-row {
                    background: linear-gradient(90deg, #EDE9FE 0%, #DDD6FE 100%) !important;
                    color: #5B21B6 !important;
                    font-weight: 700;
                    font-size: 13px;
                }
                
                .grand-total-row td {
                    border-top: 2px solid #A78BFA !important;
                    padding: 14px 16px;
                }

                /* Collapse Icon */
                .collapse-icon {
                    display: inline-block;
                    margin-right: 8px;
                    transition: transform 0.3s;
                    font-size: 10px;
                    color: #64748B;
                }
                
                .zone-row.collapsed .collapse-icon {
                    transform: rotate(-90deg);
                }

                .category-row.hidden {
                    display: none;
                }
                
                /* Modern Modal Backdrop */
                .drill-down-backdrop,
                .branch-drill-down-backdrop {
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(15, 23, 42, 0.6);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    z-index: 1000;
                    animation: fadeIn 0.2s ease;
                }
                
                .drill-down-backdrop.show,
                .branch-drill-down-backdrop.show {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                /* Modern Modal */
                .drill-down-modal,
                .branch-drill-down-modal {
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
                    width: 92%;
                    max-width: 1400px;
                    max-height: 90vh;
                    overflow: hidden;
                    animation: slideUp 0.3s ease;
                    display: flex;
                    flex-direction: column;
                }
                
                @keyframes slideUp {
                    from { 
                        opacity: 0;
                        transform: translateY(40px) scale(0.96);
                    }
                    to { 
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                }
                
                /* Modal Header */
                .drill-down-header,
                .branch-drill-down-header {
                    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
                    color: white;
                    padding: 20px 28px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .drill-down-title,
                .branch-drill-down-title {
                    font-size: 18px;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                
                .drill-down-close {
                    background: rgba(255, 255, 255, 0.15);
                    border: none;
                    color: white;
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                    font-size: 18px;
                }
                
                .drill-down-close:hover {
                    background: rgba(255, 255, 255, 0.25);
                    transform: rotate(90deg);
                }
                
                /* Modal Body */
                .drill-down-body,
                .branch-drill-down-body {
                    padding: 28px;
                    overflow-y: auto;
                    flex: 1;
                    background: #F8FAFC;
                }
                
                /* Info Section */
                .drill-down-info {
                    background: white;
                    padding: 18px 24px;
                    border-radius: 12px;
                    margin-bottom: 24px;
                    border-left: 4px solid #6366F1;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                }
                
                .drill-down-info-row {
                    display: flex;
                    gap: 32px;
                    font-size: 14px;
                    flex-wrap: wrap;
                }
                
                .drill-down-info-item {
                    display: flex;
                    gap: 8px;
                }
                
                .drill-down-info-label {
                    font-weight: 600;
                    color: #64748B;
                }
                
                .drill-down-info-value {
                    color: #1E293B;
                    font-weight: 600;
                }
                
                /* Filter Search Row */
                .filter-search-row {
                    background: white;
                    padding: 16px 20px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    display: flex;
                    gap: 12px;
                    flex-wrap: wrap;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                }
                
                .filter-search-input {
                    flex: 1;
                    min-width: 150px;
                    padding: 8px 12px;
                    border: 1px solid #E2E8F0;
                    border-radius: 8px;
                    font-size: 13px;
                    transition: all 0.2s;
                }
                
                .filter-search-input:focus {
                    outline: none;
                    border-color: #6366F1;
                    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
                }
                
                .filter-search-input::placeholder {
                    color: #94A3B8;
                }
                
                .clear-filters-btn {
                    background: #F1F5F9;
                    color: #475569;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .clear-filters-btn:hover {
                    background: #E2E8F0;
                }
                
                /* Modern Table in Modal */
                .drill-down-table-container {
                    background: white;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                }
                
                .drill-down-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 13px;
                }
                
                .drill-down-table thead {
                    background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
                }
                
                .drill-down-table th {
                    padding: 14px 16px;
                    text-align: left;
                    font-weight: 600;
                    color: #475569;
                    border-bottom: 2px solid #E2E8F0;
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .drill-down-table td {
                    padding: 12px 16px;
                    border-bottom: 1px solid #F1F5F9;
                    color: #1E293B;
                }
                
                .drill-down-table tbody tr {
                    transition: all 0.2s;
                }
                
                .drill-down-table tbody tr:hover {
                    background: #F8FAFC;
                }
                
                /* Clickable Branch ID */
                .branch-id-link {
                    color: #6366F1;
                    font-weight: 700;
                    cursor: pointer;
                    text-decoration: none;
                    position: relative;
                }
                
                .branch-id-link::after {
                    content: '';
                    position: absolute;
                    bottom: -2px;
                    left: 0;
                    right: 0;
                    height: 2px;
                    background: #6366F1;
                    transform: scaleX(0);
                    transition: transform 0.2s;
                }
                
                .branch-id-link:hover::after {
                    transform: scaleX(1);
                }
                
                /* Status Badge */
                .status-badge {
                    padding: 6px 12px;
                    border-radius: 16px;
                    font-size: 12px;
                    font-weight: 600;
                    display: inline-block;
                }
                
                .status-achieved {
                    background: #D1FAE5;
                    color: #065F46;
                }
                
                .status-on-track {
                    background: #FEF3C7;
                    color: #78350F;
                }
                
                .status-below {
                    background: #FEE2E2;
                    color: #991B1B;
                }
                
                /* Empty State */
                .drill-down-empty {
                    text-align: center;
                    padding: 80px 20px;
                    color: #94A3B8;
                }
                
                .drill-down-empty i {
                    font-size: 56px;
                    margin-bottom: 16px;
                    display: block;
                    opacity: 0.5;
                }
                
                /* Loading State */
                .loading-row td {
                    text-align: center;
                    padding: 40px;
                    color: #64748B;
                }
                
                /* Scrollbar */
                .drill-down-body::-webkit-scrollbar,
                .branch-drill-down-body::-webkit-scrollbar {
                    width: 10px;
                }
                
                .drill-down-body::-webkit-scrollbar-track,
                .branch-drill-down-body::-webkit-scrollbar-track {
                    background: #F1F5F9;
                }
                
                .drill-down-body::-webkit-scrollbar-thumb,
                .branch-drill-down-body::-webkit-scrollbar-thumb {
                    background: #CBD5E1;
                    border-radius: 5px;
                }
                
                .drill-down-body::-webkit-scrollbar-thumb:hover,
                .branch-drill-down-body::-webkit-scrollbar-thumb:hover {
                    background: #94A3B8;
                }
            </style>
        `;
		$(styles).appendTo("head");
	}

	createFilterSection() {
		const filterHtml = `
            <div class="filter-section">
                <div class="filter-row">
                    <div class="filter-group">
                        <label>Zone</label>
                        <select id="zone-filter">
                            <option value="">All Zones</option>
                            <option value="ZONE-1">ZONE-1</option>
                            <option value="ZONE-2">ZONE-2</option>
                            <option value="ZONE-3">ZONE-3</option>
                            <option value="ZONE-4">ZONE-4</option>
                            <option value="ZONE-5">ZONE-5</option>
                            <option value="ZONE-6">ZONE-6</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>From Date</label>
                        <input type="date" id="from-date-filter" />
                    </div>
                    
                    <div class="filter-group">
                        <label>To Date</label>
                        <input type="date" id="to-date-filter" />
                    </div>
                    
                    <div class="filter-group">
                        <label>&nbsp;</label>
                        <button class="apply-filter-btn" id="apply-filter">
                            <i class="fa fa-search"></i> Apply Filters
                        </button>
                    </div>
                </div>
            </div>
        `;

		$(filterHtml).appendTo(this.page.main);
		this.setupFilterEvents();
	}

	setupFilterEvents() {
		$("#apply-filter").on("click", () => {
			this.filters.zone = $("#zone-filter").val();
			this.filters.from_date = $("#from-date-filter").val();
			this.filters.to_date = $("#to-date-filter").val();
			this.loadData();
		});

		$("#zone-filter, #from-date-filter, #to-date-filter").on("keypress", (e) => {
			if (e.which === 13) {
				$("#apply-filter").click();
			}
		});
	}

	createTableStructure() {
		const container = $(`<div class="sahayog-dashboard-container"></div>`).appendTo(
			this.page.main
		);

		const table = $(`
            <table class="sahayog-table">
                <colgroup>
                    <col /><col /><col /><col /><col /><col /><col />
                </colgroup>
                <thead>
                    <tr>
                        <th class="row-label">Row Labels</th>
                        <th>Count of Branch Score</th>
                        <th>Sum of DEC-25-TGT</th>
                        <th>Sum of JAN-26-TGT</th>
                        <th>Sum of FEB-26-TGT</th>
                        <th>Sum of MAR-26-TGT</th>
                        <th>Sum of DJFM TOTAL</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="loading-row">
                        <td colspan="7"><i class="fa fa-spinner fa-spin"></i> Loading data...</td>
                    </tr>
                </tbody>
                <tfoot></tfoot>
            </table>
        `).appendTo(container);

		this.table_body = table.find("tbody");
		this.table_foot = table.find("tfoot");
	}

	createDrillDownModal() {
		const modalHtml = `
            <div class="drill-down-backdrop" id="drill-down-backdrop">
                <div class="drill-down-modal">
                    <div class="drill-down-header">
                        <div class="drill-down-title">
                            <i class="fa fa-building"></i>
                            <span id="drill-down-modal-title">Branch Details</span>
                        </div>
                        <button class="drill-down-close" id="close-drill-down">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                    <div class="drill-down-body">
                        <div class="drill-down-info" id="drill-down-info"></div>
                        
                        <div class="filter-search-row" id="branch-filter-row">
                            <input type="text" class="filter-search-input" id="filter-branch-id" placeholder="🔍 Search Branch ID...">
                            <input type="text" class="filter-search-input" id="filter-branch-name" placeholder="🔍 Search Branch Name...">
                            <input type="text" class="filter-search-input" id="filter-region" placeholder="🔍 Search Region...">
                            <input type="text" class="filter-search-input" id="filter-manager" placeholder="🔍 Search Manager...">
                            <button class="clear-filters-btn" id="clear-branch-filters">
                                <i class="fa fa-times"></i> Clear
                            </button>
                        </div>
                        
                        <div class="drill-down-table-container">
                            <table class="drill-down-table">
                                <thead>
                                    <tr>
                                        <th>Branch ID</th>
                                        <th>Branch Name</th>
                                        <th>Region</th>
                                        <th>Manager</th>
                                        <th>Target</th>
                                        <th>Achievement</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody id="drill-down-table-body"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;

		$(modalHtml).appendTo("body");

		$("#close-drill-down").on("click", () => this.closeDrillDown());
		$("#drill-down-backdrop").on("click", (e) => {
			if (e.target.id === "drill-down-backdrop") {
				this.closeDrillDown();
			}
		});

		$(document).on("keydown", (e) => {
			if (e.key === "Escape" && $("#drill-down-backdrop").hasClass("show")) {
				this.closeDrillDown();
			}
		});
	}

	createBranchDrillDownModal() {
		const modalHtml = `
            <div class="branch-drill-down-backdrop" id="branch-drill-down-backdrop">
                <div class="branch-drill-down-modal">
                    <div class="branch-drill-down-header">
                        <div class="branch-drill-down-title">
                            <i class="fa fa-receipt"></i>
                            <span id="branch-drill-down-modal-title">Transaction Details</span>
                        </div>
                        <button class="drill-down-close" id="close-branch-drill-down">
                            <i class="fa fa-times"></i>
                        </button>
                    </div>
                    <div class="branch-drill-down-body">
                        <div class="drill-down-info" id="branch-drill-down-info"></div>
                        
                        <div class="filter-search-row" id="transaction-filter-row">
                            <input type="text" class="filter-search-input" id="filter-txn-id" placeholder="🔍 Search Transaction ID...">
                            <input type="text" class="filter-search-input" id="filter-customer" placeholder="🔍 Search Customer...">
                            <input type="text" class="filter-search-input" id="filter-product" placeholder="🔍 Search Product...">
                            <input type="text" class="filter-search-input" id="filter-payment" placeholder="🔍 Search Payment Mode...">
                            <button class="clear-filters-btn" id="clear-transaction-filters">
                                <i class="fa fa-times"></i> Clear
                            </button>
                        </div>
                        
                        <div class="drill-down-table-container">
                            <table class="drill-down-table">
                                <thead>
                                    <tr>
                                        <th>Transaction ID</th>
                                        <th>Date</th>
                                        <th>Customer</th>
                                        <th>Product</th>
                                        <th>Quantity</th>
                                        <th>Amount</th>
                                        <th>Payment Mode</th>
                                    </tr>
                                </thead>
                                <tbody id="branch-drill-down-table-body"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;

		$(modalHtml).appendTo("body");

		$("#close-branch-drill-down").on("click", () => this.closeBranchDrillDown());
		$("#branch-drill-down-backdrop").on("click", (e) => {
			if (e.target.id === "branch-drill-down-backdrop") {
				this.closeBranchDrillDown();
			}
		});

		$(document).on("keydown", (e) => {
			if (e.key === "Escape" && $("#branch-drill-down-backdrop").hasClass("show")) {
				this.closeBranchDrillDown();
			}
		});
	}

	loadData() {
		frappe.call({
			method: "custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard.get_dashboard_data",
			args: { filters: this.filters },
			callback: (r) => {
				if (r.message) {
					this.data = r.message;
					this.renderTable(this.data);
				} else {
					this.showError("No data available");
				}
			},
			error: (r) => {
				this.showError("Failed to load dashboard data");
			},
		});
	}

	renderTable(data) {
		this.table_body.empty();
		this.table_foot.empty();
		this.collapsedZones.clear();

		let zonesToRender = data.zones;
		if (this.filters.zone) {
			zonesToRender = data.zones.filter((z) => z.zone_name === this.filters.zone);
		}

		zonesToRender.forEach((zone, index) => {
			this.collapsedZones.add(index);

			const zoneRow = this.renderZoneRow(zone, index);
			const categoryRows = this.renderCategoryRows(zone, index);

			this.table_body.append(zoneRow);
			this.table_body.append(categoryRows);
		});

		if (data.grand_total) {
			const grandTotalRow = this.renderGrandTotalRow(data.grand_total);
			this.table_foot.append(grandTotalRow);
		}

		this.addEventListeners();
	}

	renderZoneRow(zone, index) {
		const isCollapsed = this.collapsedZones.has(index);
		let zoneClass = "zone-1-row";
		if (zone.zone_name === "ZONE-1") zoneClass = "zone-1-row";
		else if (zone.zone_name === "ZONE-2") zoneClass = "zone-2-row";
		else if (zone.zone_name === "ZONE-3") zoneClass = "zone-3-row";
		else if (zone.zone_name === "ZONE-4") zoneClass = "zone-4-row";
		else if (zone.zone_name === "ZONE-5") zoneClass = "zone-5-row";
		else if (zone.zone_name === "ZONE-6") zoneClass = "zone-6-row";

		return $(`
            <tr class="zone-row ${zoneClass} ${
			isCollapsed ? "collapsed" : ""
		}" data-zone-index="${index}">
                <td class="row-label">
                    <span class="collapse-icon">▼</span>
                    ${zone.zone_name}
                </td>
                <td class="branch-score-cell" data-zone="${zone.zone_name}" data-type="zone">
                    ${this.formatIndianNumber(zone.branch_score)}
                </td>
                <td>${this.formatIndianNumber(zone.dec_tgt)}</td>
                <td>${this.formatIndianNumber(zone.jan_tgt)}</td>
                <td>${this.formatIndianNumber(zone.feb_tgt)}</td>
                <td>${this.formatIndianNumber(zone.mar_tgt)}</td>
                <td>${this.formatIndianNumber(zone.djfm_total)}</td>
            </tr>
        `);
	}

	renderCategoryRows(zone, zoneIndex) {
		const isCollapsed = this.collapsedZones.has(zoneIndex);
		const rows = [];

		const categoryOrder = [
			"Accelerator",
			"Pinacle",
			"Master",
			"Learner",
			"Starter",
			"Zero Level",
		];
		const sortedCategories = zone.categories.sort((a, b) => {
			return categoryOrder.indexOf(a.category) - categoryOrder.indexOf(b.category);
		});

		sortedCategories.forEach((cat) => {
			const categoryClass = this.getCategoryClass(cat.category);

			const row = $(`
                <tr class="category-row ${categoryClass} category-for-zone-${zoneIndex} ${
				isCollapsed ? "hidden" : ""
			}">
                    <td class="row-label">${cat.category}</td>
                    <td class="branch-score-cell" data-zone="${zone.zone_name}" data-category="${
				cat.category
			}" data-type="category">
                        ${this.formatIndianNumber(cat.branch_score)}
                    </td>
                    <td>${this.formatIndianNumber(cat.dec_tgt)}</td>
                    <td>${this.formatIndianNumber(cat.jan_tgt)}</td>
                    <td>${this.formatIndianNumber(cat.feb_tgt)}</td>
                    <td>${this.formatIndianNumber(cat.mar_tgt)}</td>
                    <td>${this.formatIndianNumber(cat.djfm_total)}</td>
                </tr>
            `);
			rows.push(row);
		});

		return rows;
	}

	renderGrandTotalRow(total) {
		return $(`
            <tr class="grand-total-row">
                <td class="row-label">Grand Total</td>
                <td>${this.formatIndianNumber(total.branch_score)}</td>
                <td>${this.formatIndianNumber(total.dec_tgt)}</td>
                <td>${this.formatIndianNumber(total.jan_tgt)}</td>
                <td>${this.formatIndianNumber(total.feb_tgt)}</td>
                <td>${this.formatIndianNumber(total.mar_tgt)}</td>
                <td>${this.formatIndianNumber(total.djfm_total)}</td>
            </tr>
        `);
	}

	addEventListeners() {
		this.table_body.off("click", ".zone-row .row-label, .zone-row .collapse-icon");
		this.table_body.on("click", ".zone-row .row-label, .zone-row .collapse-icon", (e) => {
			e.stopPropagation();
			const zoneIndex = $(e.currentTarget).closest(".zone-row").data("zone-index");
			this.toggleZoneCollapse(zoneIndex);
		});

		this.table_body.off("click", ".branch-score-cell");
		this.table_body.on("click", ".branch-score-cell", (e) => {
			e.stopPropagation();
			const cell = $(e.currentTarget);
			const zone = cell.data("zone");
			const category = cell.data("category");
			const type = cell.data("type");

			this.openDrillDown(zone, category, type);
		});
	}

	toggleZoneCollapse(zoneIndex) {
		const zoneRow = this.table_body.find(`.zone-row[data-zone-index="${zoneIndex}"]`);
		const categoryRows = this.table_body.find(`.category-for-zone-${zoneIndex}`);

		if (this.collapsedZones.has(zoneIndex)) {
			this.collapsedZones.delete(zoneIndex);
			zoneRow.removeClass("collapsed");
			categoryRows.removeClass("hidden");
		} else {
			this.collapsedZones.add(zoneIndex);
			zoneRow.addClass("collapsed");
			categoryRows.addClass("hidden");
		}
	}

	openDrillDown(zone, category, type) {
		let title = `Branch Details - ${zone}`;
		if (category) {
			title += ` (${category})`;
		}
		$("#drill-down-modal-title").text(title);

		const infoHtml = `
            <div class="drill-down-info-row">
                <div class="drill-down-info-item">
                    <span class="drill-down-info-label">Zone:</span>
                    <span class="drill-down-info-value">${zone}</span>
                </div>
                ${
					category
						? `
                <div class="drill-down-info-item">
                    <span class="drill-down-info-label">Category:</span>
                    <span class="drill-down-info-value">${category}</span>
                </div>
                `
						: ""
				}
                <div class="drill-down-info-item">
                    <span class="drill-down-info-label">View:</span>
                    <span class="drill-down-info-value">${
						type === "zone" ? "Zone Level" : "Category Level"
					}</span>
                </div>
            </div>
        `;
		$("#drill-down-info").html(infoHtml);

		this.branchFilters = {};
		this.currentBranches = this.getDummyBranches();
		this.renderBranchTable();
		this.setupBranchFilters();

		$("#drill-down-backdrop").addClass("show");
	}

	getDummyBranches() {
		return [
			{
				id: "BR001",
				name: "Main Branch",
				region: "Central",
				manager: "John Doe",
				target: 5000000,
				achievement: 4500000,
				status: "On Track",
			},
			{
				id: "BR002",
				name: "North Branch",
				region: "North",
				manager: "Jane Smith",
				target: 3500000,
				achievement: 3800000,
				status: "Achieved",
			},
			{
				id: "BR003",
				name: "South Branch",
				region: "South",
				manager: "Mike Johnson",
				target: 4200000,
				achievement: 3200000,
				status: "Below Target",
			},
			{
				id: "BR004",
				name: "East Branch",
				region: "East",
				manager: "Sarah Wilson",
				target: 3800000,
				achievement: 3600000,
				status: "On Track",
			},
			{
				id: "BR005",
				name: "West Branch",
				region: "West",
				manager: "David Brown",
				target: 4500000,
				achievement: 4800000,
				status: "Achieved",
			},
			{
				id: "BR006",
				name: "Downtown Branch",
				region: "Central",
				manager: "Emma Davis",
				target: 4000000,
				achievement: 4100000,
				status: "Achieved",
			},
			{
				id: "BR007",
				name: "Suburb Branch",
				region: "North",
				manager: "Michael Lee",
				target: 3000000,
				achievement: 2800000,
				status: "Below Target",
			},
		];
	}

	setupBranchFilters() {
		$("#filter-branch-id, #filter-branch-name, #filter-region, #filter-manager")
			.off("input")
			.on("input", (e) => {
				const field = e.target.id.replace("filter-", "").replace("-", "_");
				this.branchFilters[field] = $(e.target).val().toLowerCase();
				this.renderBranchTable();
			});

		$("#clear-branch-filters")
			.off("click")
			.on("click", () => {
				$("#filter-branch-id, #filter-branch-name, #filter-region, #filter-manager").val(
					""
				);
				this.branchFilters = {};
				this.renderBranchTable();
			});
	}

	renderBranchTable() {
		const tbody = $("#drill-down-table-body");
		tbody.empty();

		let filteredBranches = this.currentBranches.filter((branch) => {
			if (
				this.branchFilters.branch_id &&
				!branch.id.toLowerCase().includes(this.branchFilters.branch_id)
			)
				return false;
			if (
				this.branchFilters.branch_name &&
				!branch.name.toLowerCase().includes(this.branchFilters.branch_name)
			)
				return false;
			if (
				this.branchFilters.region &&
				!branch.region.toLowerCase().includes(this.branchFilters.region)
			)
				return false;
			if (
				this.branchFilters.manager &&
				!branch.manager.toLowerCase().includes(this.branchFilters.manager)
			)
				return false;
			return true;
		});

		if (filteredBranches.length === 0) {
			tbody.html(`
                <tr>
                    <td colspan="7">
                        <div class="drill-down-empty">
                            <i class="fa fa-search"></i>
                            <p>No branches found matching your filters</p>
                        </div>
                    </td>
                </tr>
            `);
			return;
		}

		filteredBranches.forEach((branch) => {
			const achievementPct = ((branch.achievement / branch.target) * 100).toFixed(1);
			let statusClass = "status-on-track";

			if (branch.status === "Achieved") statusClass = "status-achieved";
			else if (branch.status === "Below Target") statusClass = "status-below";

			const row = $(`
                <tr>
                    <td>
                        <span class="branch-id-link" data-branch-id="${
							branch.id
						}" data-branch-name="${branch.name}">
                            ${branch.id}
                        </span>
                    </td>
                    <td>${branch.name}</td>
                    <td>${branch.region}</td>
                    <td>${branch.manager}</td>
                    <td>₹${this.formatIndianNumber(branch.target)}</td>
                    <td>₹${this.formatIndianNumber(
						branch.achievement
					)} <small>(${achievementPct}%)</small></td>
                    <td>
                        <span class="status-badge ${statusClass}">
                            ${branch.status}
                        </span>
                    </td>
                </tr>
            `);
			tbody.append(row);
		});

		$(".branch-id-link")
			.off("click")
			.on("click", (e) => {
				const branchId = $(e.currentTarget).data("branch-id");
				const branchName = $(e.currentTarget).data("branch-name");
				this.openBranchDrillDown(branchId, branchName);
			});
	}

	openBranchDrillDown(branchId, branchName) {
		$("#branch-drill-down-modal-title").text(`${branchName} - ${branchId}`);

		const infoHtml = `
            <div class="drill-down-info-row">
                <div class="drill-down-info-item">
                    <span class="drill-down-info-label">Branch ID:</span>
                    <span class="drill-down-info-value">${branchId}</span>
                </div>
                <div class="drill-down-info-item">
                    <span class="drill-down-info-label">Branch Name:</span>
                    <span class="drill-down-info-value">${branchName}</span>
                </div>
                <div class="drill-down-info-item">
                    <span class="drill-down-info-label">View:</span>
                    <span class="drill-down-info-value">Transaction Level</span>
                </div>
            </div>
        `;
		$("#branch-drill-down-info").html(infoHtml);

		this.transactionFilters = {};
		this.currentTransactions = this.getDummyTransactions();
		this.renderTransactionTable();
		this.setupTransactionFilters();

		$("#branch-drill-down-backdrop").addClass("show");
	}

	getDummyTransactions() {
		return [
			{
				id: "TXN001",
				date: "2025-12-01",
				customer: "ABC Corp",
				product: "Product A",
				quantity: 50,
				amount: 250000,
				payment_mode: "Credit",
			},
			{
				id: "TXN002",
				date: "2025-12-03",
				customer: "XYZ Ltd",
				product: "Product B",
				quantity: 30,
				amount: 180000,
				payment_mode: "Cash",
			},
			{
				id: "TXN003",
				date: "2025-12-05",
				customer: "DEF Industries",
				product: "Product C",
				quantity: 75,
				amount: 420000,
				payment_mode: "UPI",
			},
			{
				id: "TXN004",
				date: "2025-12-07",
				customer: "GHI Enterprises",
				product: "Product A",
				quantity: 100,
				amount: 500000,
				payment_mode: "Credit",
			},
			{
				id: "TXN005",
				date: "2025-12-09",
				customer: "JKL Trading",
				product: "Product D",
				quantity: 25,
				amount: 150000,
				payment_mode: "Cash",
			},
			{
				id: "TXN006",
				date: "2025-12-10",
				customer: "MNO Solutions",
				product: "Product B",
				quantity: 60,
				amount: 360000,
				payment_mode: "UPI",
			},
		];
	}

	setupTransactionFilters() {
		$("#filter-txn-id, #filter-customer, #filter-product, #filter-payment")
			.off("input")
			.on("input", (e) => {
				const field = e.target.id.replace("filter-", "").replace("-", "_");
				this.transactionFilters[field] = $(e.target).val().toLowerCase();
				this.renderTransactionTable();
			});

		$("#clear-transaction-filters")
			.off("click")
			.on("click", () => {
				$("#filter-txn-id, #filter-customer, #filter-product, #filter-payment").val("");
				this.transactionFilters = {};
				this.renderTransactionTable();
			});
	}

	renderTransactionTable() {
		const tbody = $("#branch-drill-down-table-body");
		tbody.empty();

		let filteredTransactions = this.currentTransactions.filter((txn) => {
			if (
				this.transactionFilters.txn_id &&
				!txn.id.toLowerCase().includes(this.transactionFilters.txn_id)
			)
				return false;
			if (
				this.transactionFilters.customer &&
				!txn.customer.toLowerCase().includes(this.transactionFilters.customer)
			)
				return false;
			if (
				this.transactionFilters.product &&
				!txn.product.toLowerCase().includes(this.transactionFilters.product)
			)
				return false;
			if (
				this.transactionFilters.payment &&
				!txn.payment_mode.toLowerCase().includes(this.transactionFilters.payment)
			)
				return false;
			return true;
		});

		if (filteredTransactions.length === 0) {
			tbody.html(`
                <tr>
                    <td colspan="7">
                        <div class="drill-down-empty">
                            <i class="fa fa-search"></i>
                            <p>No transactions found matching your filters</p>
                        </div>
                    </td>
                </tr>
            `);
			return;
		}

		filteredTransactions.forEach((txn) => {
			const row = $(`
                <tr>
                    <td><strong>${txn.id}</strong></td>
                    <td>${txn.date}</td>
                    <td>${txn.customer}</td>
                    <td>${txn.product}</td>
                    <td>${txn.quantity} units</td>
                    <td>₹${this.formatIndianNumber(txn.amount)}</td>
                    <td><span class="status-badge status-on-track">${txn.payment_mode}</span></td>
                </tr>
            `);
			tbody.append(row);
		});
	}

	closeDrillDown() {
		$("#drill-down-backdrop").removeClass("show");
	}

	closeBranchDrillDown() {
		$("#branch-drill-down-backdrop").removeClass("show");
	}

	formatIndianNumber(num) {
		if (num === null || num === undefined || num === "") return "0";
		num = typeof num === "string" ? parseFloat(num) : num;
		if (num % 1 !== 0) return num.toFixed(2);

		let numStr = num.toString();
		let lastThree = numStr.substring(numStr.length - 3);
		let otherNumbers = numStr.substring(0, numStr.length - 3);

		if (otherNumbers !== "") {
			lastThree = "," + lastThree;
		}

		return otherNumbers.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + lastThree;
	}

	showError(message) {
		this.table_body.html(`
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #EF4444;">
                    <i class="fa fa-exclamation-triangle"></i> ${message}
                </td>
            </tr>
        `);
	}
}
