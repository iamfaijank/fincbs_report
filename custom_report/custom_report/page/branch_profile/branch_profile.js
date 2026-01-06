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


        .date-filter-container {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding: 12px 16px;
            background: var(--linkedin-bg);
            border-radius: var(--radius-sm);
            border: 1px solid var(--linkedin-border);
        }
        .date-filter-container label {
            font-weight: 500;
            color: var(--linkedin-text-secondary);
            font-size: 14px;
            white-space: nowrap;
        }
        #date-filter {
            background: var(--linkedin-white);
            border: 1px solid var(--linkedin-border);
            border-radius: var(--radius-sm);
            padding: 8px 12px;
            font-size: 14px;
            color: var(--linkedin-text);
        }
        #date-filter:focus {
            outline: none;
            border-color: var(--linkedin-blue);
            box-shadow: 0 0 0 2px rgba(10, 102, 194, 0.1);
        }


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
            from { opacity: 0; transform: translateY(4px); }
            to   { opacity: 1; transform: translateY(0); }
        }


        .card-header {
            font-size: 16px;
            font-weight: 600;
            color: var(--linkedin-text);
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--linkedin-border);
            line-height: 1.5;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .card-header small {
            font-size: 12px;
            opacity: 0.7;
        }


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


        .performance-item {
            padding: 16px;
            background: var(--linkedin-bg);
            border-radius: var(--radius-sm);
            margin-bottom: 12px;
            border-left: 4px solid;
            transition: var(--transition-base);
        }
        .performance-item:hover {
            background: var(--linkedin-white);
            box-shadow: var(--shadow-sm);
        }
        .performance-item:last-child {
            margin-bottom: 0;
        }
        .performance-item.status-pinnacle-overachievers {
            border-left-color: #28a745;
        }
        .performance-item.status-master {
            border-left-color: #20c997;
        }
        .performance-item.status-accelerator {
            border-left-color: #ffc107;
        }
        .performance-item.status-starter {
            border-left-color: #fd7e14;
        }
        .performance-item.status-learner {
            border-left-color: #dc3545;
        }
        .performance-item.status-zero-level {
            border-left-color: #6c757d;
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
            padding: 6px 12px;
            border-radius: var(--radius-full);
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .status-pinnacle-overachievers {
            background: #d4edda;
            color: #155724;
        }
        .status-master {
            background: #d1ecf1;
            color: #0c5460;
        }
        .status-accelerator {
            background: #fff3cd;
            color: #856404;
        }
        .status-starter {
            background: #ffeaa7;
            color: #856404;
        }
        .status-learner {
            background: #f8d7da;
            color: #721c24;
        }
        .status-zero-level {
            background: #e9ecef;
            color: #495057;
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


        .empty-state {
            text-align: center;
            padding: 48px 24px;
            color: var(--linkedin-text-muted);
            font-size: 14px;
            line-height: 1.6;
        }


        .no-data-state {
            padding: 32px 24px;
            text-align: center;
        }
        .no-data-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--linkedin-text);
            margin-bottom: 8px;
        }
        .no-data-latest {
            font-size: 14px;
            color: var(--linkedin-text-secondary);
            margin-bottom: 16px;
        }
        .no-data-latest strong {
            color: var(--linkedin-blue);
            font-weight: 600;
        }
        .no-data-instruction {
            font-size: 13px;
            color: var(--linkedin-text-muted);
        }


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
            from { opacity: 0; transform: translateY(-4px); }
            to   { opacity: 1; transform: translateY(0); }
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


        /* CRM & Customers Tab Styles */
        .crm-date-filter-section {
            margin-bottom: 24px;
            padding: 16px;
            background: var(--linkedin-bg);
            border-radius: var(--radius-md);
            border: 1px solid var(--linkedin-border);
        }

        .crm-filter-row {
            display: flex;
            gap: 16px;
            align-items: center;
            flex-wrap: wrap;
        }

        .crm-filter-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .crm-filter-group label {
            font-weight: 500;
            color: var(--linkedin-text-secondary);
            font-size: 14px;
            white-space: nowrap;
        }

        .crm-date-input {
            background: var(--linkedin-white);
            border: 1px solid var(--linkedin-border);
            border-radius: var(--radius-sm);
            padding: 8px 12px;
            font-size: 14px;
            color: var(--linkedin-text);
            transition: var(--transition-base);
            min-width: 150px;
        }

        .crm-date-input:focus {
            outline: none;
            border-color: var(--linkedin-blue);
            box-shadow: 0 0 0 2px rgba(10, 102, 194, 0.1);
        }

        .crm-metrics-section {
            margin-top: 16px;
        }

        .crm-metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-top: 16px;
        }

        @media (max-width: 768px) {
            .crm-metrics-grid {
                grid-template-columns: 1fr;
            }
        }

        .crm-metric-card {
            background: var(--linkedin-white);
            border: 1px solid var(--linkedin-border);
            border-radius: var(--radius-md);
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            transition: var(--transition-base);
            box-shadow: var(--shadow-sm);
        }

        .crm-metric-card:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }

        .crm-metric-icon {
            font-size: 36px;
            line-height: 1;
            flex-shrink: 0;
        }

        .crm-metric-content {
            flex: 1;
        }

        .crm-metric-label {
            font-size: 13px;
            color: var(--linkedin-text-muted);
            font-weight: 500;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .crm-metric-value {
            font-size: 32px;
            font-weight: 600;
            color: var(--linkedin-text);
            line-height: 1.2;
        }

        .crm-metric-subtext {
            font-size: 12px;
            color: var(--linkedin-text-secondary);
            margin-top: 4px;
        }

        /* Specific color accents for different metrics */
        .crm-total { border-left: 4px solid #0a66c2; }
        .crm-converted { border-left: 4px solid #28a745; }
        .crm-followup { border-left: 4px solid #ffc107; }
        .crm-not-interested { border-left: 4px solid #dc3545; }
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
                                <div class="empty-state">Select a branch to view CRM data</div>
                            </div>
                        </div>
                    </div>
                </div>


                <div class="right-column">
                    <div class="date-filter-container">
                        <label for="date-filter">Select Date:</label>
                        <input type="date" id="date-filter" />
                    </div>
                    <div id="branch-performance-card"></div>
                    <div id="staff-manpower-card"></div>
                </div>
            </div>
        </div>
    `);


    // Initialize date filter with today's date
    const today = new Date().toISOString().split("T")[0];
    $("#date-filter").val(today);


    // Tabs functionality
    $(".tab-item").on("click", function () {
        const tabId = $(this).data("tab");
        const $clickedTab = $(this);
        const $targetContent = $(`#tab-${tabId}`);


        $(".tab-item").removeClass("active");
        $clickedTab.addClass("active");


        $(".tab-content.active").css("opacity", "0");
        setTimeout(() => {
            $(".tab-content").removeClass("active");
            $targetContent.addClass("active").css("opacity", "0");
            setTimeout(() => {
                $targetContent.css("opacity", "1");
            }, 10);
        }, 150);

        // Load CRM data when CRM tab is clicked
        if (tabId === "crm-customers") {
            const sol_id = $("#search-field input").val().trim();
            if (sol_id) {
                // Render the HTML first with dates pre-filled
                render_crm_skeleton();
                // Then load the data
                setTimeout(() => {
                    load_crm_data(sol_id);
                }, 100);
            }
        }
    });


    init_sol_search(wrapper);


    // -------- LOAD FROM URL --------
    const query = frappe.utils.get_query_params();
    if (query.sol_id) {
        $("#search-field input").val(query.sol_id);
        load_all_data(query.sol_id);
    }


    // Date filter change handler
    $("#date-filter").on("change", function () {
        const sol_id = $("#search-field input").val().trim();
        if (sol_id) {
            load_performance_data(sol_id);
        }
    });

    // CRM date filter change handler (using event delegation)
    $(document).on("change", "#crm-from-date, #crm-to-date", function () {
        const sol_id = $("#search-field input").val().trim();
        if (sol_id) {
            load_crm_data(sol_id);
        }
    });
};


/* ---------------- DATE UTILITY FUNCTIONS ---------------- */
// Convert dd/mm/yyyy to yyyy-mm-dd for backend
function formatDateForBackend(ddmmyyyy) {
    const parts = ddmmyyyy.split('/');
    if (parts.length === 3) {
        return `${parts[2]}-${parts[1]}-${parts[0]}`;
    }
    return ddmmyyyy;
}

// Convert yyyy-mm-dd to dd/mm/yyyy for display
function formatDateForDisplay(yyyymmdd) {
    const parts = yyyymmdd.split('-');
    if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return yyyymmdd;
}

// Get default dates (first day of month and today)
function get_default_dates() {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);

    // Format as dd/mm/yyyy
    const formatDate = (date) => {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
    };

    return {
        fromDate: formatDate(firstDay),
        toDate: formatDate(today)
    };
}


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
    load_performance_data(sol);
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


    const branch = b.branch || "";
    const solId = b.sol_id || "";
    const zone = b.zone || "";
    const region = b.region || "";
    const state = b.state || "";
    const address = b.address || "";
    const email = b.email || "";


    const html = `
        <div class="dashboard-card" style="animation-delay: 0.05s;">
            <div class="card-header">Branch Information</div>
            <div class="branch-name-id">${branch} - ${solId}</div>
            <div class="branch-detail-row">
                <span class="branch-detail-label">Zone:</span>
                <span class="branch-detail-value">${zone}</span>
            </div>
            <div class="branch-detail-row">
                <span class="branch-detail-label">Region:</span>
                <span class="branch-detail-value">${region}</span>
            </div>
            <div class="branch-detail-row">
                <span class="branch-detail-label">State:</span>
                <span class="branch-detail-value">${state}</span>
            </div>
            <div class="branch-detail-row">
                <span class="branch-detail-label">Email:</span>
                <span class="branch-detail-value">${email}</span>
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
            const data = r.message || {};
            render_branch_manager(data);
            render_account_portfolio(data);
            render_staff_manpower(data);
        },
    });
}


function render_branch_manager(data) {
    const managerName = data.bm_name || "";
    const initials = (managerName || "NA")
        .split(" ")
        .filter(Boolean)
        .map((n) => n[0])
        .join("")
        .substring(0, 2)
        .toUpperCase();


    const experience = data.bm_vintage || "";
    const phone = data.bm_phone || "";
    const email = data.bm_email || "";
    const joinedDate = data.bm_doj || "";


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
    const totalAccounts = data.total_customers_id || 0;
    const totalYtdAchievement = Number(data.total_ytd_achievement) || 0;
    const totalClosingBalance = Number(data.total_book) || 0;
    const totalYtdTarget = Number(data.total_ytd_target) || 0;


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
                    <div class="portfolio-metric-value">₹${formatCurrency(
                        totalYtdAchievement
                    )}</div>
                </div>
                <div class="portfolio-metric">
                    <div class="portfolio-metric-label">Total Closing Balance</div>
                    <div class="portfolio-metric-value">₹${formatCurrency(
                        totalClosingBalance
                    )}</div>
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


/* ---------------- CRM & CUSTOMERS FUNCTIONALITY ---------------- */
function render_crm_skeleton() {
    const dates = get_default_dates();

    const html = `
        <div class="crm-date-filter-section">
            <div class="crm-filter-row">
                <div class="crm-filter-group">
                    <label for="crm-from-date">From Date</label>
                    <input type="text" id="crm-from-date" class="crm-date-input" 
                           value="${dates.fromDate}" placeholder="DD/MM/YYYY" />
                </div>
                <div class="crm-filter-group">
                    <label for="crm-to-date">To Date</label>
                    <input type="text" id="crm-to-date" class="crm-date-input" 
                           value="${dates.toDate}" placeholder="DD/MM/YYYY" />
                </div>
            </div>
        </div>

        <div class="crm-metrics-section">
            <div class="card-header">CRM Lead Statistics</div>
            <div class="crm-metrics-grid">
                <div class="crm-metric-card crm-total">
                    <div class="crm-metric-icon">📊</div>
                    <div class="crm-metric-content">
                        <div class="crm-metric-label">Total Leads</div>
                        <div class="crm-metric-value">Loading...</div>
                    </div>
                </div>

                <div class="crm-metric-card crm-converted">
                    <div class="crm-metric-icon">✅</div>
                    <div class="crm-metric-content">
                        <div class="crm-metric-label">Converted Leads</div>
                        <div class="crm-metric-value">Loading...</div>
                    </div>
                </div>

                <div class="crm-metric-card crm-followup">
                    <div class="crm-metric-icon">📞</div>
                    <div class="crm-metric-content">
                        <div class="crm-metric-label">Follow Up</div>
                        <div class="crm-metric-value">Loading...</div>
                    </div>
                </div>

                <div class="crm-metric-card crm-not-interested">
                    <div class="crm-metric-icon">❌</div>
                    <div class="crm-metric-content">
                        <div class="crm-metric-label">Not Interested</div>
                        <div class="crm-metric-value">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    $("#tab-crm-customers").html(html);
}


function load_crm_data(sol_id) {
    const fromDateDisplay = $("#crm-from-date").val();
    const toDateDisplay = $("#crm-to-date").val();

    if (!fromDateDisplay || !toDateDisplay) {
        frappe.msgprint("Please select both From and To dates");
        return;
    }

    // Convert dd/mm/yyyy to yyyy-mm-dd for backend
    const fromDate = formatDateForBackend(fromDateDisplay);
    const toDate = formatDateForBackend(toDateDisplay);

    frappe.call({
        method: "custom_report.custom_report.page.branch_profile.branch_profile.get_crm_data",
        args: {
            sol_id: sol_id,
            from_date: fromDate,
            to_date: toDate
        },
        callback: (r) => {
            render_crm_data(r.message || {});
            console.log(r.message);
        },
        error: (r) => {
            $("#tab-crm-customers").html(
                '<div class="empty-state">Error loading CRM data</div>'
            );
        }
    });
}


function render_crm_data(data) {
    const dates = get_default_dates();
    const totalLeads = data.total_leads || 0;
    const convertedLeads = data.converted_leads || 0;
    const followUp = data.follow_up || 0;
    const notInterested = data.not_interested || 0;
    const conversionRate = totalLeads > 0 ? ((convertedLeads / totalLeads) * 100).toFixed(1) : 0;

    // Convert backend dates (yyyy-mm-dd) to display format (dd/mm/yyyy)
    const fromDateValue = data.from_date ? formatDateForDisplay(data.from_date) : dates.fromDate;
    const toDateValue = data.to_date ? formatDateForDisplay(data.to_date) : dates.toDate;

    const html = `
        <div class="crm-date-filter-section">
            <div class="crm-filter-row">
                <div class="crm-filter-group">
                    <label for="crm-from-date">From Date</label>
                    <input type="text" id="crm-from-date" class="crm-date-input" 
                           value="${fromDateValue}" placeholder="DD/MM/YYYY" />
                </div>
                <div class="crm-filter-group">
                    <label for="crm-to-date">To Date</label>
                    <input type="text" id="crm-to-date" class="crm-date-input" 
                           value="${toDateValue}" placeholder="DD/MM/YYYY" />
                </div>
            </div>
        </div>

        <div class="crm-metrics-section">
            <div class="card-header">CRM Lead Statistics</div>
            <div class="crm-metrics-grid">
                <div class="crm-metric-card crm-total">
                    <div class="crm-metric-icon">📊</div>
                    <div class="crm-metric-content">
                        <div class="crm-metric-label">Total Leads</div>
                        <div class="crm-metric-value">${formatNumber(totalLeads)}</div>
                    </div>
                </div>

                <div class="crm-metric-card crm-converted">
                    <div class="crm-metric-icon">✅</div>
                    <div class="crm-metric-content">
                        <div class="crm-metric-label">Converted Leads</div>
                        <div class="crm-metric-value">${formatNumber(convertedLeads)}</div>
                        <div class="crm-metric-subtext">${conversionRate}% conversion</div>
                    </div>
                </div>

                <div class="crm-metric-card crm-followup">
                    <div class="crm-metric-icon">📞</div>
                    <div class="crm-metric-content">
                        <div class="crm-metric-label">Follow Up</div>
                        <div class="crm-metric-value">${formatNumber(followUp)}</div>
                    </div>
                </div>

                <div class="crm-metric-card crm-not-interested">
                    <div class="crm-metric-icon">❌</div>
                    <div class="crm-metric-content">
                        <div class="crm-metric-label">Not Interested</div>
                        <div class="crm-metric-value">${formatNumber(notInterested)}</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    $("#tab-crm-customers").html(html);
}


/* ---------------- RIGHT COLUMN: PERFORMANCE DATA LOADING (UPDATED) ---------------- */
function load_performance_data(sol_id) {
    const selectedDate = $("#date-filter").val();


    frappe.call({
        method: "custom_report.custom_report.page.branch_profile.branch_profile.get_performance_data",
        args: {
            sol_id: sol_id,
            date: selectedDate,
        },
        callback: (r) => {
            if (r.message && r.message.data_exists) {
                render_branch_performance(r.message);
            } else if (r.message && r.message.latest_date) {
                show_no_data_message(r.message.latest_date, selectedDate);
            } else {
                $("#branch-performance-card").html(
                    '<div class="dashboard-card"><div class="empty-state">No performance data available for this branch</div></div>'
                );
            }
        },
        error: (r) => {
            $("#branch-performance-card").html(
                '<div class="dashboard-card"><div class="empty-state">Error loading performance data</div></div>'
            );
        },
    });
}


/* ---------------- NEW: NO DATA MESSAGE WITH LATEST DATE ---------------- */
function show_no_data_message(latestDate, selectedDate) {
    const formattedLatest = new Date(latestDate).toLocaleDateString("en-IN");
    const formattedSelected = new Date(selectedDate).toLocaleDateString("en-IN");


    const html = `
        <div class="dashboard-card" style="animation-delay: 0.15s;">
            <div class="card-header">
                Branch Performance 
                <small>No Data - ${formattedSelected}</small>
            </div>
            <div class="no-data-state">
                <div class="no-data-title">
                    No data available for ${formattedSelected}
                </div>
                <div class="no-data-latest">
                    Latest available data: <strong>${formattedLatest}</strong>
                </div>
                <div class="no-data-instruction">
                    Please select ${formattedLatest} or any other available date from the date picker.
                </div>
            </div>
        </div>
    `;


    $("#branch-performance-card").html(html);
}


/* ---------------- RIGHT COLUMN: BRANCH PERFORMANCE ---------------- */
function render_branch_performance(data) {
    const performanceData = [
        {
            period: "Month",
            achievement: Number(data.monthly_achievement) || 0,
            target: Number(data.monthly_target) || 0,
        },
        {
            period: "Yearly",
            achievement: Number(data.yearly_achievement) || 0,
            target: Number(data.yearly_target) || 0,
        },
        {
            period: "YTD",
            achievement: Number(data.yearly_achievement) || 0,
            target: Number(data.ytd_target) || 0,
        },
    ];


    let performanceHtml = "";
    performanceData.forEach((item) => {
        const percent = item.target ? Math.round((item.achievement / item.target) * 100) : 0;
        const status = getPerformanceStatus(percent);
        const statusClass = status.toLowerCase().replace(/[\s()]/g, "-");


        performanceHtml += `
            <div class="performance-item status-${statusClass}">
                <div class="performance-header">
                    <div class="performance-period">${item.period}</div>
                    <span class="performance-badge status-${statusClass}">${status}</span>

                </div>
                <div class="performance-values">
                    ₹${formatCurrency(item.achievement)} / ₹${formatCurrency(item.target)}
                </div>
                <div class="performance-percentage">${percent}%</div>
            </div>
        `;
    });


    const financialYear = data.financial_year || "N/A";
    const html = `
        <div class="dashboard-card" style="animation-delay: 0.15s;">
            <div class="card-header">
                Branch Performance 
                <small>(${financialYear}) - ${data.selected_date}</small>
            </div>
            ${performanceHtml}
        </div>
    `;


    $("#branch-performance-card").html(html);
}


/* ---------------- RIGHT COLUMN: STAFF & MANPOWER ---------------- */
function render_staff_manpower(data) {
    const staffData = {
        "Staff Nos": data.staff_nos || 0,
        "Budgeted Staff": data.total_no_of_budgeted_staff || 0,
        "Staff Onboarded": data.total_staff_onboarded || 0,
        "DDS Agent": data.total_dds_agent || 0,
        "Active DDS Agent": data.total_active_dds_agent || 0,
        "SS Agent": data.total_ss_agent || 0,
        "Active SS Agent": data.total_active_ss_agent || 0,
    };


    let staffHtml = "";
    Object.keys(staffData).forEach((role) => {
        staffHtml += `
            <div class="staff-role-box">
                <div class="staff-role-label">${role}</div>
                <div class="staff-role-count">${formatNumber(staffData[role])}</div>
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
    $("#tab-crm-customers").html('<div class="empty-state">Select a branch to view CRM data</div>');
}


function formatNumber(num) {
    if (!num) return "0";
    return num.toLocaleString("en-IN");
}


function formatCurrency(num) {
    if (!num) return "0";
    return num.toLocaleString("en-IN");
}


function getPerformanceStatus(percent) {
    if (percent > 100) return "Pinnacle (Overachievers)";
    if (percent >= 80) return "Master";
    if (percent >= 60) return "Accelerator";
    if (percent >= 40) return "Starter";
    if (percent >= 20) return "Learner";
    return "Zero Level";
}