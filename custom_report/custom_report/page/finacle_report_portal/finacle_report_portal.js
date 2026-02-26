frappe.pages['finacle-report-portal'].on_page_load = function(wrapper) {
    // ============================================================================
    // ADVANCED MOBILE DETECTION (WORKS EVEN IN DESKTOP MODE)
    // ============================================================================
    
    function isMobileDevice() {
        // Method 1: Check User Agent
        const ua = navigator.userAgent || navigator.vendor || window.opera;
        const mobileUA = /android|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile/i.test(ua);
        
        // Method 2: Check Touch Capability
        const hasTouch = (
            'ontouchstart' in window ||
            navigator.maxTouchPoints > 0 ||
            navigator.msMaxTouchPoints > 0
        );
        
        // Method 3: Check Screen Size (actual device screen, not viewport)
        const smallScreen = (
            window.screen.width <= 768 ||
            window.screen.height <= 768
        );
        
        // Method 4: Check Device Pixel Ratio (mobile devices usually have higher DPR)
        const highDPR = window.devicePixelRatio > 1;
        
        // Method 5: Check for mobile-specific orientation API
        const hasOrientation = typeof window.orientation !== 'undefined';
        
        // Combine all checks (if ANY 2+ are true, it's mobile)
        let mobileIndicators = 0;
        if (mobileUA) mobileIndicators++;
        if (hasTouch) mobileIndicators++;
        if (smallScreen) mobileIndicators++;
        if (hasOrientation) mobileIndicators++;
        
        // Final decision: if 2 or more indicators say mobile, treat as mobile
        return mobileIndicators >= 2;
    }
    
    // Block mobile access (even in desktop mode)
    if (isMobileDevice()) {
        const page = frappe.ui.make_app_page({
            parent: wrapper,
            title: 'Not Supported on Mobile',
            single_column: true
        });

        $(page.body).html(`
            <div style="display:flex;justify-content:center;align-items:center;min-height:60vh;font-family:sans-serif;">
                <div style="max-width:600px;text-align:center;padding:40px;background:#fff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
                    <div style="font-size:70px;color:#b71c1c;margin-bottom:20px;">\uD83D\uDCF4</div>
                    <h2 style="color:#b71c1c;margin-bottom:15px;font-size:26px;">This App Is Not Supported on Mobile</h2>
                    <p style="color:#555;font-size:15px;line-height:1.6;margin-bottom:20px;">
                        The <strong>Finacle Report Portal</strong> can only be accessed from a Desktop or Laptop browser.
                    </p>
                    <p style="color:#777;font-size:14px;line-height:1.6;margin-bottom:25px;">
                        Please open this URL on your Desktop or Laptop to continue.
                    </p>
                    <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:15px;margin-bottom:20px;">
                        <p style="color:#856404;font-size:13px;margin:0;line-height:1.5;">
                            <strong>⚠️ Note:</strong> This restriction applies even if you enable "Desktop Mode" in your mobile browser.
                        </p>
                    </div>
                    <button onclick="window.location.href='/'" style="margin-top:10px;background:#196767;color:white;border:none;padding:10px 26px;font-weight:600;border-radius:6px;cursor:pointer;font-size:14px;">
                        ⬅ Back to Home
                    </button>
                </div>
            </div>
        `);

        return; // Stop further initialization on mobile
    }

    // ============================================================================
    // ROLE-BASED ACCESS CONTROL
    // ============================================================================
    
    const ALLOWED_ROLES = [
        "HR Department Report",
        "JLL Department Report",
        "MIS Department Report",
        "Loan Department Report",
        "Audit Department Report",
        "Finance Department Report",
        "Operation Department Report",
        "Two Wheeler Department Report",
        "Head Office Report",
        "Branch Report",
        "System Manager",
        "Finacle Report Admin"
    ];
    
    // Check if user has any of the allowed roles
    const userRoles = frappe.user_roles || [];
    const hasAccess = ALLOWED_ROLES.some(role => userRoles.includes(role));
    
    // If user doesn't have access, show denial message
    if (!hasAccess) {
        showAccessDeniedPage(wrapper);
        return; // Stop page initialization
    }
    
    // If access granted, initialize the page normally
    initializeReportPortal(wrapper);
};


// ============================================================================
// ACCESS DENIED PAGE
// ============================================================================

function showAccessDeniedPage(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Access Denied',
        single_column: true
    });
    
    $(page.body).html(`
        <div style="display:flex;justify-content:center;align-items:center;min-height:60vh;font-family:sans-serif;">
            <div style="max-width:600px;text-align:center;padding:40px;background:#fff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
                <div style="font-size:80px;color:#b71c1c;margin-bottom:20px;">\uD83D\uDEAB</div>
                <h2 style="color:#b71c1c;margin-bottom:15px;font-size:28px;">Access Denied</h2>
                <p style="color:#555;font-size:16px;line-height:1.6;margin-bottom:25px;">
                    You do not have permission to access the <strong>Finacle Report Portal</strong>.
                </p>
                <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:20px;margin-bottom:25px;">
                    <p style="color:#856404;font-size:14px;margin:0;line-height:1.6;">
                        <strong>ℹ️ Need Access?</strong><br>
                        To request access to this page, please contact the IT administrator at:
                    </p>
                    <div style="margin-top:15px;padding:12px;background:#fff;border-radius:6px;border:1px dashed #ffc107;">
                        <a href="mailto:atul.n@sahayogmultistate.com" style="color:#196767;font-weight:600;font-size:15px;text-decoration:none;">
                            📧 atul.n@sahayogmultistate.com
                        </a>
                    </div>
                </div>
                <button onclick="window.history.back()" style="margin-top:25px;background:#196767;color:white;border:none;padding:12px 30px;font-weight:600;border-radius:6px;cursor:pointer;font-size:14px;">
                    ← Go Back
                </button>
            </div>
        </div>
    `);
}


// ============================================================================
// MAIN REPORT PORTAL INITIALIZATION
// ============================================================================

function initializeReportPortal(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Finacle Report Portal',
        single_column: true
    });

    // Include flatpickr CSS & JS
    if (!document.querySelector('#flatpickr-css')) {
        const link = document.createElement('link');
        link.id = 'flatpickr-css';
        link.rel = 'stylesheet';
        link.href = 'https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css';
        document.head.appendChild(link);
    }
    if (!document.querySelector('#flatpickr-js')) {
        const script = document.createElement('script');
        script.id = 'flatpickr-js';
        script.src = 'https://cdn.jsdelivr.net/npm/flatpickr';
        document.head.appendChild(script);
    }

    // Page HTML with Form
    $(page.body).html(`
        <div style="max-width:480px; margin: 40px auto; font-family: sans-serif;">
            <style>
                @keyframes finacleTitleFlow {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }
                @keyframes newBtnPulse {
                    0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.45); }
                    70% { box-shadow: 0 0 0 8px rgba(245, 158, 11, 0); }
                    100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
                }
                .finacle-title-gradient {
                    text-align: center;
                    font-weight: 900;
                    font-size: 24px;
                    line-height: 1.2;
                    margin: 0 0 12px 0;
                    background: linear-gradient(90deg, #196767, #00bfa5, #196767);
                    background-size: 220% 220%;
                    -webkit-background-clip: text;
                    background-clip: text;
                    color: transparent;
                    animation: finacleTitleFlow 4s ease-in-out infinite;
                }
                .date-chip {
                    background: #f3f4f6;
                    border: 1px solid #d0d7de;
                    color: #5f6b7a;
                    padding: 3px 8px;
                    border-radius: 999px;
                    font-size: 10px;
                    font-weight: 700;
                    cursor: pointer;
                    transition: all 0.15s ease;
                }
                .date-chip:hover {
                    background: #eceff3;
                    border-color: #c6cdd7;
                }
                .date-chip-active {
                    background: #e6f6f4 !important;
                    border-color: #89cfc4 !important;
                    color: #196767 !important;
                    box-shadow: inset 0 0 0 1px #6ec2b5;
                }
                .download-focus {
                    box-shadow: 0 8px 22px rgba(25, 103, 103, 0.14);
                    transform: scale(1.01);
                }
                .new-btn-attn {
                    animation: newBtnPulse 1.4s ease-in-out infinite;
                }
            </style>
            <h3 class="finacle-title-gradient">Finacle CBS Report</h3>
            
            <div id="user_permissions_info" style="text-align:center; margin-bottom:20px; display:none;">
                <!-- Permissions info will be populated here -->
            </div>

            <form id="finacle-report-form" style="display:flex; flex-direction:column; gap:8px;">
                    <div id="selection_sections" style="display:flex; flex-direction:column; gap:8px;">
                    <div style="border:1px solid #d0d7de; border-radius:8px; background:#fff; padding:10px;">
                        <div>
                            <label style="font-weight:600; color:#196767; margin-bottom:5px;">Select Report</label>
                            <div style="position:relative;">
                                <input type="text" id="report_search" class="form-control" placeholder="\uD83D\uDD0D Search or select report..." autocomplete="off" style="padding-right:35px;">
                                <span id="search_clear" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);cursor:pointer;color:#999;display:none;font-size:18px;" title="Clear search">✕</span>
                                <select id="report_name" class="form-control" required style="display:none;">
                                    <option value="" disabled selected>Loading reports...</option>
                                </select>
                                <div id="report_dropdown" style="display:none; position:absolute; top:100%; left:0; right:0; background:white; border:1px solid #ddd; border-radius:5px; max-height:250px; overflow-y:auto; z-index:1000; box-shadow:0 4px 8px rgba(0,0,0,0.1); margin-top:2px;">
                                    <!-- Dropdown items will be populated here -->
                                </div>
                            </div>
                            <input type="hidden" id="selected_report_value" value="">
                            <div id="report_error" style="color:red; font-size:12px; display:none; margin-top:3px;"></div>
                        </div>
                    </div>
                    <div style="border:1px solid #d0d7de; border-radius:8px; background:#fff; padding:10px; display:flex; flex-direction:column; gap:8px;">
                        <!-- Branch Selection Dropdown -->
                        <div id="branch_filter_container" style="display: none; flex-direction: column;">
                            <label style="font-weight:600; color:#196767; margin-bottom:5px;">Select Branches</label>
                            <div style="position: relative;">
                                <div id="branch_selector_display" class="form-control" style="cursor: pointer; min-height: 34px; display: flex; align-items: center; justify-content: space-between; padding-right: 10px; background: #fff;">
                                    <span id="selected_branches_text" style="font-size: 13px; color: #555; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Loading branches...</span>
                                    <span style="color: #999;">▼</span>
                                </div>

                                <div id="branch_picker_dropdown" style="display:none; position:absolute; top:100%; left:0; right:0; background:white; border:1px solid #ddd; border-radius:5px; max-height:260px; overflow-y:auto; z-index:1001; box-shadow:0 4px 8px rgba(0,0,0,0.1); margin-top:2px; padding: 8px;">
                                    <div style="margin-bottom: 10px;">
                                        <input type="text" id="sol_id_search" class="form-control" placeholder="Search branches..." style="font-size: 13px; height: 32px;">
                                    </div>
                                    <div id="sol_id_list" style="max-height: 140px; overflow-y: auto; border: 1px solid #ebedef; border-radius: 4px; padding: 5px; margin-bottom: 8px;">
                                        <!-- Checkboxes will be populated here -->
                                    </div>
                                    <div style="display: flex; gap: 8px;">
                                        <button type="button" id="select_all_sol" style="flex: 1; font-size: 11px; padding: 4px; cursor: pointer; background: #f0f4f4; border: 1px solid #d1d8d8; border-radius: 4px;">Select All</button>
                                        <button type="button" id="clear_all_sol" style="flex: 1; font-size: 11px; padding: 4px; cursor: pointer; background: #f0f4f4; border: 1px solid #d1d8d8; border-radius: 4px;">Clear</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div style="border:1px solid #d0d7de; border-radius:8px; background:#fff; padding:10px; display:flex; flex-direction:column; gap:8px;">
                        <div style="display:flex; gap:10px;">
                            <div style="flex:1;">
                                <label style="font-weight:600; color:#196767; margin-bottom:5px;">Start Date</label>
                                <input type="text" id="start_date" class="form-control" required placeholder="DD/MM/YYYY">
                                <div id="start_date_error" style="color:red; font-size:11px; display:none; margin-top:3px;"></div>
                            </div>
                            <div style="flex:1;">
                                <label style="font-weight:600; color:#196767; margin-bottom:5px;">End Date</label>
                                <input type="text" id="end_date" class="form-control" required placeholder="DD/MM/YYYY">
                                <div id="end_date_error" style="color:red; font-size:11px; display:none; margin-top:3px;"></div>
                            </div>
                        </div>
                        <div style="display:flex; flex-wrap:wrap; gap:6px;">
                            <button type="button" class="date-chip" data-range="today">Today</button>
                            <button type="button" class="date-chip" data-range="yesterday">Yesterday</button>
                            <button type="button" class="date-chip" data-range="last_7_days">Last 7 Days</button>
                            <button type="button" class="date-chip" data-range="this_month">This Month</button>
                            <button type="button" class="date-chip" data-range="last_month">Last Month</button>
                        </div>
                    </div>
                    </div>
                    <div id="download_section" style="border:1px solid #d0d7de; border-radius:8px; background:#fff; padding:10px; display:flex; flex-direction:column; gap:8px; transition:all .25s ease;">
                        <div style="display:flex; gap:10px;">
                        <div id="download_dropdown_wrap" style="flex:1; position:relative;">
                            <button type="button" id="download_csv" style="width:100%; background:#196767; color:white; border:none; padding:10px; font-weight:600; border-radius:5px; cursor:pointer; display:flex; align-items:center; justify-content:space-between;">
                                 <span>Download</span>
                                 <span id="download_arrow" style="font-size:12px; opacity:0.9;">▾</span>
                            </button>
                            <div id="download_mode_options" style="display:none; position:absolute; top:calc(100% + 6px); left:0; right:0; background:#fff; border:1px solid #d6e5e5; border-radius:8px; box-shadow:0 8px 18px rgba(0,0,0,0.12); z-index:1200; padding:6px;">
                                <button type="button" id="download_mode_normal" style="width:100%; text-align:left; background:transparent; color:#224; border:none; padding:9px 10px; font-weight:600; border-radius:6px; cursor:pointer;">
                                     CSV File (Normal Speed)
                                </button>
                                <button type="button" id="download_mode_zipped" style="width:100%; text-align:left; background:transparent; color:#224; border:none; padding:9px 10px; font-weight:600; border-radius:6px; cursor:pointer;">
                                     Zip File (Small Size + Fast)
                                </button>
                            </div>
                        </div>
                        <button type="button" id="cancel_download" style="flex:0 0 auto; min-width:auto; background:transparent; color:#b71c1c; border:none; padding:2px 0; font-weight:700; border-radius:0; cursor:pointer; display:none; text-decoration:underline; text-underline-offset:2px;">
                             Cancel
                        </button>
                        <button type="button" id="new_download_btn" style="display:none; flex:0 0 auto; background:#f5b301; color:#3b2a00; border:1px solid #d49700; border-radius:5px; padding:7px 12px; font-size:12px; font-weight:800; cursor:pointer;">+ New</button>
                        </div>
                        <div style="display:flex; align-items:center; gap:8px;">
                        <span id="download_status_badge" style="display:none; font-size:11px; font-weight:700; padding:3px 8px; border-radius:999px; background:#e0f2f1; color:#196767; white-space:nowrap;">Queued</span>
                        <div id="progress_container" style="display:none; flex:1; height:12px; background:#eee; border-radius:6px; overflow:hidden; position:relative;">
                            <div id="progress_bar" style="width:0%; height:100%; background:linear-gradient(90deg,#196767,#00bfa5); transition:width 0.3s ease;"></div>
                        </div>
                        <div id="progress_percent" style="display:none; min-width:56px; text-align:right; font-size:16px; font-weight:800; color:#e53935; line-height:1;">0%</div>
                        <button type="button" id="retry_download" style="display:none; background:#196767; color:white; border:none; padding:5px 10px; font-size:11px; font-weight:600; border-radius:4px; cursor:pointer; white-space:nowrap;">
                            Retry
                        </button>
                        </div>
                        <div style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        <span id="progress_text" style="display:none; font-size:12px; color:#555; vertical-align:middle;"></span>
                        <span id="robot_msg" style="display:none; font-size:12px; color:#196767; margin-left:8px; vertical-align:middle; font-style:italic;"></span>
                        </div>
                        <div id="download_metrics" style="display:none; margin-top:2px;">
                            <div style="display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px;">
                                <div style="background:#f8fbfb; border:1px solid #dfeeee; border-radius:8px; padding:8px;">
                                    <div style="font-size:10px; font-weight:700; color:#4b5f5f; text-transform:uppercase; letter-spacing:.2px;">Rows Fetched</div>
                                    <div id="metric_rows_fetched" style="margin-top:2px; font-size:15px; font-weight:800; color:#196767;">0</div>
                                </div>
                                <div style="background:#f8fbfb; border:1px solid #dfeeee; border-radius:8px; padding:8px;">
                                    <div style="font-size:10px; font-weight:700; color:#4b5f5f; text-transform:uppercase; letter-spacing:.2px;">File Size (MB)</div>
                                    <div id="metric_file_size_mb" style="margin-top:2px; font-size:15px; font-weight:800; color:#196767;">0.00</div>
                                </div>
                                <div style="background:#f8fbfb; border:1px solid #dfeeee; border-radius:8px; padding:8px;">
                                    <div style="font-size:10px; font-weight:700; color:#4b5f5f; text-transform:uppercase; letter-spacing:.2px;">Time Taken</div>
                                    <div id="metric_time_taken" style="margin-top:2px; font-size:15px; font-weight:800; color:#196767;">0 Seconds</div>
                                </div>
                            </div>
                        </div>
                    </div>
            </form>
        </div>
    `);

    const $reportSelect = $('#report_name');
    const $reportSearch = $('#report_search');
    const $reportDropdown = $('#report_dropdown');
    const $selectedReportValue = $('#selected_report_value');
    const $searchClear = $('#search_clear');
    
    // Branch Filter Elements
    const $branchFilterContainer = $('#branch_filter_container');
    const $branchSelectorDisplay = $('#branch_selector_display');
    const $branchPickerDropdown = $('#branch_picker_dropdown');
    const $selectedBranchesText = $('#selected_branches_text');
    const $solIdList = $('#sol_id_list');
    const $solIdSearch = $('#sol_id_search');
    const $downloadHint = $('#download_hint');
    
    let currentSolData = [];
    let isDeptUser = false;
    let hasBranchAccessIssue = false;

    // Fetch and show user permissions/branches
    function loadUserPermissions() {
        frappe.call({
            method: 'custom_report.api.get_user_report_permissions',
            callback: function(res) {
                if (res.message && (res.message.is_branch_user || res.message.is_dept_user)) {
                    currentSolData = res.message.sol_data || [];
                    isDeptUser = res.message.is_dept_user;
                    const $info = $('#user_permissions_info');
                    
                    $branchFilterContainer.css('display', 'flex');
                    
                    if (currentSolData.length > 0 || isDeptUser) {
                        hasBranchAccessIssue = false;
                        let statusText = '';
                        if (isDeptUser) {
                            statusText = 'Full Access (All Branches)';
                        } else {
                            statusText = `${currentSolData.length} Branches Selected`;
                            // Pre-select all for branch users
                            currentSolData.forEach(d => d.selected = true);
                        }

                        $selectedBranchesText.text(statusText);
                        renderSolIdList();
                    } else if (!isDeptUser) {
                        hasBranchAccessIssue = true;
                        $info.show().html(`
                            <div style="background:#ffebee;border:1px solid #ffcdd2;border-radius:6px;padding:10px 15px;">
                                <p style="color:#c62828;font-size:13px;font-weight:600;margin:0;">⚠️ No branches assigned in Report Preference.</p>
                                <p style="color:#555;font-size:11px;margin:5px 0 0 0;">Please contact your administrator to set up your branch list.</p>
                            </div>
                        `);
                        $selectedBranchesText.text('No branches assigned');
                    }
                    updateSummaryBar();
                    refreshDownloadActionState();
                }
            }
        });
    }

    function renderSolIdList() {
        const searchTerm = $solIdSearch.val().toLowerCase();
        
        // Sort: Selected items first, then by sol_id
        const sortedData = [...currentSolData].sort((a, b) => {
            if (!!a.selected !== !!b.selected) {
                return a.selected ? -1 : 1;
            }
            return a.sol_id.localeCompare(b.sol_id);
        });

        let html = '';
        sortedData.forEach(d => {
            const display_name = `${d.sol_id} (${d.branch_name})`;
            if (display_name.toLowerCase().includes(searchTerm)) {
                const checked = d.selected ? 'checked' : '';
                html += `
                    <div class="sol-item" style="display: flex; align-items: center; gap: 8px; padding: 4px; border-bottom: 1px solid #f8f9fa; ${d.selected ? 'background: #f0fafa;' : ''}">
                        <input type="checkbox" id="chk_${d.sol_id}" value="${d.sol_id}" ${checked} style="cursor: pointer;">
                        <label for="chk_${d.sol_id}" style="font-size: 13px; margin: 0; cursor: pointer; color: ${d.selected ? '#196767' : '#444'}; font-weight: ${d.selected ? '600' : '400'};">${display_name}</label>
                    </div>
                `;
            }
        });
        
        $solIdList.html(html || '<div style="text-align:center; padding:10px; color:#999; font-size:12px;">No branches found</div>');

        // Bind events to new checkboxes
        $solIdList.find('input[type="checkbox"]').on('change', function() {
            const sol_id = $(this).val();
            const is_checked = $(this).is(':checked');
            
            // Update data model
            const item = currentSolData.find(d => d.sol_id === sol_id);
            if (item) item.selected = is_checked;
            
            updateActiveBadges(isDeptUser);
            // Re-render to update grouping
            renderSolIdList();
        });
    }

    function updateActiveBadges(is_dept) {
        const selectedCount = currentSolData.filter(d => d.selected).length;
        
        if (is_dept) {
            if (selectedCount === 0) {
                $selectedBranchesText.text('Full Access (All Branches)');
            } else {
                $selectedBranchesText.text(`${selectedCount} Branches Selected`);
            }
        } else {
            if (selectedCount === 0) {
                $selectedBranchesText.text('No branches selected');
            } else {
                $selectedBranchesText.text(`${selectedCount} Branches Selected`);
            }
        }
        updateSummaryBar();
        refreshDownloadActionState();
    }

    // Toggle Dropdown
    $branchSelectorDisplay.on('click', function(e) {
        e.stopPropagation();
        $branchPickerDropdown.toggle();
        if ($branchPickerDropdown.is(':visible')) {
            $solIdSearch.focus();
            renderSolIdList(); // Refresh list on open
        }
    });

    $(document).on('click', function(e) {
        if (!$(e.target).closest('#branch_filter_container').length) {
            $branchPickerDropdown.hide();
        }
    });

    // Branch Search
    $solIdSearch.on('input', function() {
        renderSolIdList();
    });

    // Select/Clear All
    $('#select_all_sol').on('click', () => {
        const searchTerm = $solIdSearch.val().toLowerCase();
        currentSolData.forEach(d => {
            const display_name = `${d.sol_id} (${d.branch_name})`.toLowerCase();
            if (display_name.includes(searchTerm)) {
                d.selected = true;
            }
        });
        updateActiveBadges(isDeptUser);
        renderSolIdList();
    });

    $('#clear_all_sol').on('click', () => {
        const searchTerm = $solIdSearch.val().toLowerCase();
        currentSolData.forEach(d => {
            const display_name = `${d.sol_id} (${d.branch_name})`.toLowerCase();
            if (display_name.includes(searchTerm)) {
                d.selected = false;
            }
        });
        updateActiveBadges(isDeptUser);
        renderSolIdList();
    });

    function getSelectedSols() {
        return currentSolData.filter(d => d.selected).map(d => ({ id: d.sol_id, branch: d.branch_name }));
    }

    function getSelectedSolIds() {
        return currentSolData.filter(d => d.selected).map(d => d.sol_id);
    }

    loadUserPermissions();

    let expectedDuration = 2;
    let currentRequestId = null;
    let currentXhr = null;
    let currentLogId = null;
    let statusPollTimer = null;
    let statusPollInFlight = false;
    let lastStatusUpdatedAt = 0;
    let userCancelledCurrentRequest = false;
    let startDatePicker = null;
    let endDatePicker = null;
    let allReports = []; // Store all reports for searching
    let activeDatePreset = null;
    let isDownloadFocusMode = false;

    function toDDMMYYYY(dateObj) {
        const d = String(dateObj.getDate()).padStart(2, '0');
        const m = String(dateObj.getMonth() + 1).padStart(2, '0');
        const y = String(dateObj.getFullYear());
        return `${d}/${m}/${y}`;
    }

    function setActiveDateChip(preset) {
        activeDatePreset = preset || null;
        $('.date-chip').each(function() {
            const isActive = $(this).data('range') === activeDatePreset;
            $(this).toggleClass('date-chip-active', isActive);
        });
    }

    function setDateRange(startDate, endDate, preservePreset) {
        if (startDatePicker && endDatePicker) {
            startDatePicker.setDate(startDate, false);
            endDatePicker.setDate(endDate, false);
            endDatePicker.set('minDate', startDate);
        } else {
            $('#start_date').val(toDDMMYYYY(startDate));
            $('#end_date').val(toDDMMYYYY(endDate));
        }
        if (!preservePreset) {
            setActiveDateChip(null);
        }
        validateDateRange();
        updateSummaryBar();
        refreshDownloadActionState();
    }

    function applyDatePreset(preset) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        let start = new Date(today);
        let end = new Date(today);

        if (preset === 'yesterday') {
            start.setDate(today.getDate() - 1);
            end = new Date(start);
        } else if (preset === 'last_7_days') {
            start.setDate(today.getDate() - 6);
        } else if (preset === 'this_month') {
            start = new Date(today.getFullYear(), today.getMonth(), 1);
        } else if (preset === 'last_month') {
            start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            end = new Date(today.getFullYear(), today.getMonth(), 0);
        }

        setDateRange(start, end, true);
        setActiveDateChip(preset);
    }

    function updateSummaryBar() {
        return;
    }

    function refreshDownloadActionState() {
        if (currentRequestId) {
            return;
        }

        const reportDocName = $selectedReportValue.val();
        const start = $('#start_date').val();
        const end = $('#end_date').val();
        const selectedCount = currentSolData.filter(d => d.selected).length;
        const dateValid = validateDateRange();
        const hasDates = Boolean(start && end);
        const branchOk = hasBranchAccessIssue ? false : (isDeptUser ? true : selectedCount > 0);
        const valid = Boolean(reportDocName && hasDates && dateValid && branchOk);

        $('#download_csv')
            .prop('disabled', !valid)
            .css('opacity', valid ? '1' : '0.6');

        if (valid) {
            $downloadHint.text('Ready to download');
        } else if (hasBranchAccessIssue) {
            $downloadHint.text('No branches assigned to this user');
        } else if (!reportDocName) {
            $downloadHint.text('Select report to enable download');
        } else if (!hasDates) {
            $downloadHint.text('Select start and end date');
        } else if (!dateValid) {
            $downloadHint.text('Fix date range first');
        } else if (!branchOk) {
            $downloadHint.text('Select at least one branch');
        } else {
            $downloadHint.text('Complete required fields');
        }
    }

    // Initialize datepickers with validation
    function initDatepickers() {
        if (!window.flatpickr) return setTimeout(initDatepickers, 50);
        
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        const yesterday = new Date(today); 
        yesterday.setDate(today.getDate() - 1);

        // Start Date Picker
        startDatePicker = flatpickr("#start_date", { 
            dateFormat: "d/m/Y", 
            defaultDate: firstDay,
            onChange: function(selectedDates, dateStr, instance) {
                // Clear previous errors
                $('#start_date_error').hide();
                $('#end_date_error').hide();
                setActiveDateChip(null);
                
                // Update end date minimum to selected start date
                if (endDatePicker && selectedDates.length > 0) {
                    endDatePicker.set('minDate', selectedDates[0]);
                }
                
                // Validate if end date is already selected
                validateDateRange();
                updateSummaryBar();
                refreshDownloadActionState();
            }
        });

        // End Date Picker
        endDatePicker = flatpickr("#end_date", { 
            dateFormat: "d/m/Y", 
            defaultDate: yesterday,
            minDate: firstDay, // Initially set to first day
            onChange: function(selectedDates, dateStr, instance) {
                // Clear previous errors
                $('#end_date_error').hide();
                setActiveDateChip(null);
                
                // Validate date range
                validateDateRange();
                updateSummaryBar();
                refreshDownloadActionState();
            }
        });
    }
    initDatepickers();

    // Date validation function
    function validateDateRange() {
        const start_date_val = $('#start_date').val();
        const end_date_val = $('#end_date').val();

        // If both dates are selected, validate
        if (start_date_val && end_date_val) {
            const startDate = parseDateFromDDMMYYYY(start_date_val);
            const endDate = parseDateFromDDMMYYYY(end_date_val);

            if (endDate < startDate) {
                $('#end_date_error').text('❌ End date cannot be before start date').show();
                return false;
            } else {
                $('#end_date_error').hide();
                return true;
            }
        }
        return true;
    }

    // Helper function to parse DD/MM/YYYY to Date object
    function parseDateFromDDMMYYYY(dateStr) {
        const [day, month, year] = dateStr.split('/').map(Number);
        return new Date(year, month - 1, day); // month is 0-indexed
    }

    // Load reports
    function loadReports() {
        frappe.call({
            method: 'custom_report.api.get_user_reports',
            callback: function(res) {
                const reports = res.message || [];
                if (!reports.length) {
                    $reportSelect.html(`<option disabled selected>No reports available</option>`);
                    $reportSearch.prop('disabled', true).attr('placeholder', 'No reports available');
                    return;
                }
                
                // Store all reports
                allReports = reports;
                
                // Populate hidden select
                $reportSelect.html(`<option value="" disabled selected>Select Report</option>`);
                reports.forEach(r => {
                    const dur = r.last_duration ? parseFloat(r.last_duration) : '';
                    $reportSelect.append(`<option value="${r.name}" data-duration="${dur}">${r.report_name}</option>`);
                });
                
                // Enable search
                $reportSearch.prop('disabled', false);
                updateSummaryBar();
                refreshDownloadActionState();
            }
        });
    }
    loadReports();

    // Search functionality
    $reportSearch.on('input focus', function() {
        const searchTerm = $(this).val().toLowerCase();
        
        // Show clear button if there's text
        if (searchTerm.length > 0) {
            $searchClear.show();
        } else {
            $searchClear.hide();
        }
        
        // Filter reports
        const filteredReports = allReports.filter(r => 
            r.report_name.toLowerCase().includes(searchTerm)
        );
        
        // Populate dropdown
        if (filteredReports.length > 0) {
            let html = '';
            filteredReports.forEach(r => {
                html += `<div class="report-item" data-value="${r.name}" data-duration="${r.last_duration || ''}" style="padding:10px;cursor:pointer;border-bottom:1px solid #f0f0f0;transition:background 0.2s;">
                    <div style="font-weight:500;color:#333;">${r.report_name}</div>
                </div>`;
            });
            $reportDropdown.html(html).show();
            
            // Add hover effect
            $('.report-item').hover(
                function() { $(this).css('background', '#f5f5f5'); },
                function() { $(this).css('background', 'white'); }
            );
            
            // Handle selection
            $('.report-item').on('click', function() {
                const value = $(this).data('value');
                const text = $(this).find('div').first().text();
                const duration = $(this).data('duration');
                
                // Set values
                $selectedReportValue.val(value);
                $reportSearch.val(text);
                $reportSelect.val(value);
                $reportDropdown.hide();
                $searchClear.show();
                
                // Update duration
                expectedDuration = duration && duration >= 2 ? duration : 2;
                if (duration) {
                    $('#progress_text').show().text(`Time Required: ${humanReadableTime(duration)}`);
                    $('#robot_msg').show().text('🤖 Ready to download.');
                } else {
                    $('#progress_text').hide();
                    $('#robot_msg').hide();
                }
                updateSummaryBar();
                refreshDownloadActionState();
            });
        } else {
            $reportDropdown.html('<div style="padding:10px;color:#999;text-align:center;">No reports found</div>').show();
        }
    });

    // Close dropdown when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('#report_search, #report_dropdown').length) {
            $reportDropdown.hide();
        }
        if (!$(e.target).closest('#download_csv, #download_mode_options').length) {
            setDownloadMenuOpen(false);
        }
    });

    // Clear search
    $searchClear.on('click', function() {
        $reportSearch.val('');
        $selectedReportValue.val('');
        $reportSelect.val('');
        $(this).hide();
        $reportDropdown.hide();
        $('#progress_text').hide();
        $('#robot_msg').hide();
        updateSummaryBar();
        refreshDownloadActionState();
    });

    $('.date-chip').on('click', function() {
        applyDatePreset($(this).data('range'));
    });

    $('#reset_filters').on('click', function() {
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        const yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);

        $reportSearch.val('');
        $selectedReportValue.val('');
        $reportSelect.val('');
        $searchClear.hide();
        $reportDropdown.hide();

        setDateRange(firstDay, yesterday);

        if (currentSolData.length) {
            currentSolData.forEach(d => { d.selected = !isDeptUser; });
            updateActiveBadges(isDeptUser);
            renderSolIdList();
        } else {
            updateSummaryBar();
            refreshDownloadActionState();
        }

        $('#report_error,#start_date_error,#end_date_error').hide();
        $('#progress_text,#robot_msg').hide();
    });

    function formatForAPI(val){ 
        const [d,m,y]=val.split('/'); 
        return `${y}-${m.padStart(2,'0')}-${d.padStart(2,'0')}`; 
    }
    
    function humanReadableTime(sec){ 
        const m=Math.floor(sec/60), s=Math.floor(sec%60); 
        return m>0?`${m} Minutes ${s} Seconds`:`${s} Seconds`; 
    }

    function humanReadableBytes(bytes) {
        if (!bytes || bytes <= 0) return "0 B";
        const units = ["B", "KB", "MB", "GB", "TB"];
        const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
        const value = bytes / Math.pow(1024, i);
        return `${value.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
    }

    function updateProgressPercent(percent) {
        const p = Math.max(0, Math.min(100, Number(percent) || 0));
        const hue = Math.round((p * 120) / 100); // 0=red,120=green
        const hue2 = Math.min(120, hue + 18);
        $('#progress_percent')
            .text(`${p}%`)
            .css('color', `hsl(${hue}, 85%, 42%)`);
        $('#progress_bar').css('background', `linear-gradient(90deg, hsl(${hue}, 78%, 40%), hsl(${hue2}, 82%, 46%))`);
    }

    function stopStatusPolling() {
        if (statusPollTimer) {
            clearInterval(statusPollTimer);
            statusPollTimer = null;
        }
    }

    function setDownloadStatus(status, label) {
        const $badge = $('#download_status_badge');
        const palette = {
            queued: { bg: '#fff8e1', color: '#8d6e00' },
            running: { bg: '#e3f2fd', color: '#0d47a1' },
            success: { bg: '#e8f5e9', color: '#1b5e20' },
            failed: { bg: '#ffebee', color: '#b71c1c' },
            cancelled: { bg: '#fafafa', color: '#616161' },
        };
        const c = palette[status] || palette.queued;
        $badge.css({ background: c.bg, color: c.color }).text(label || status).show();
    }

    function setDownloadFocusMode(enabled) {
        if (enabled && isDownloadFocusMode) return;
        if (!enabled && !isDownloadFocusMode) return;

        isDownloadFocusMode = enabled;
        if (enabled) {
            $('#selection_sections').stop(true, true).slideUp(220);
            $('#download_section').addClass('download-focus');
            const top = Math.max(0, ($('#download_section').offset().top || 0) - (window.innerHeight * 0.28));
            $('html, body').stop(true).animate({ scrollTop: top }, 260);
        } else {
            $('#selection_sections').stop(true, true).slideDown(180);
            $('#download_section').removeClass('download-focus');
            $('#new_download_btn').hide().removeClass('new-btn-attn');
        }
    }

    function resetDownloadUI() {
        $('#cancel_download').hide().prop('disabled', false).text('Cancel');
        if (!$('#download_csv #download_arrow').length) {
            $('#download_csv').html('<span>Download</span><span id="download_arrow" style="font-size:12px; opacity:0.9;">▾</span>');
        } else {
            $('#download_csv span').first().text('Download');
        }
        $('#download_csv').prop('disabled', false).css('display', 'flex').show();
        $('#download_mode_options').hide();
        $('#download_arrow').text('▾');
        $('#new_download_btn').hide().removeClass('new-btn-attn');
        refreshDownloadActionState();
    }

    function setDownloadMenuOpen(open) {
        $('#download_mode_options').toggle(!!open);
        $('#download_arrow').text(open ? '▴' : '▾');
    }

    function showDownloadMetrics(rowsFetched, fileSizeMb, timeTakenSec) {
        $('#metric_rows_fetched').text((Number(rowsFetched) || 0).toLocaleString());
        const size = Number(fileSizeMb) || 0;
        $('#metric_file_size_mb').text(size.toFixed(2));
        $('#metric_time_taken').text(humanReadableTime(Number(timeTakenSec) || 0));
        $('#download_metrics').show();
    }

    function hideDownloadMetrics() {
        $('#download_metrics').hide();
    }

    function startStatusPolling(requestId, startedAt) {
        stopStatusPolling();
        currentRequestId = requestId;
        statusPollInFlight = false;
        lastStatusUpdatedAt = 0;
        userCancelledCurrentRequest = false;

        const pollStatus = () => {
            if (statusPollInFlight) return;
            statusPollInFlight = true;
            frappe.call({
                method: 'custom_report.api.get_report_download_status',
                args: { request_id: requestId },
                callback: function(res) {
                    statusPollInFlight = false;
                    const st = res.message || {};
                    const updatedAt = Number(st.updated_at || 0);
                    if (updatedAt && updatedAt < lastStatusUpdatedAt) {
                        return;
                    }
                    if (updatedAt) {
                        lastStatusUpdatedAt = updatedAt;
                    }
                    const elapsed = (Date.now() - startedAt) / 1000;
                    const percent = Math.min(95, Math.floor((elapsed / expectedDuration) * 100));
                    const rowsFetched = Number(st.rows_processed || 0);

                    $('#progress_bar').width(percent + "%");
                    updateProgressPercent(percent);
                    $('#progress_text').text(
                        `⏱ ${humanReadableTime(elapsed)} | Rows Fetched: ${rowsFetched.toLocaleString()} | Size: ${humanReadableBytes(st.bytes_written || 0)}`
                    );
                    $('#robot_msg').text(st.message || `🤖 Processing... Rows ${rowsFetched.toLocaleString()}`);
                    setDownloadStatus(
                        st.status === 'queued' || st.status === 'cancel_requested' ? 'queued' : (st.status || 'running'),
                        st.status === 'queued' ? 'Queued' : (st.status === 'running' ? 'Running' : (st.status === 'cancel_requested' ? 'Cancelling' : st.status))
                    );

                    if (st.status === 'success' && st.file_url && !userCancelledCurrentRequest) {
                        stopStatusPolling();
                        currentRequestId = null;
                        $('#progress_bar').width("100%");
                        updateProgressPercent(100);
                        $('#progress_text').text(
                            `✅ Completed | Rows Fetched: ${(st.rows_processed || 0).toLocaleString()} | Size: ${humanReadableBytes(st.bytes_written || 0)}`
                        );
                        $('#robot_msg').text('🤖 Done!');
                        $('#progress_text,#robot_msg').hide();
                        setDownloadStatus('success', 'Success');
                        $('#retry_download').hide();
                        resetDownloadUI();

                        const link = document.createElement("a");
                        link.href = st.download_url || st.file_url;
                        link.download = st.filename || "finacle_report.csv";
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);

                        loadReports();
                        setDownloadFocusMode(true);
                        $('#new_download_btn').css('display', 'inline-block').show().addClass('new-btn-attn');
                        setTimeout(()=>$('#progress_container,#progress_percent,#progress_text,#robot_msg').fadeOut(),3000);
                    } else if (st.status === 'failed') {
                        stopStatusPolling();
                        currentRequestId = null;
                        resetDownloadUI();
                        $('#progress_container,#progress_percent,#progress_text').hide();
                        $('#robot_msg').text(st.error ? `❌ ${st.error}` : '❌ Failed to download.');
                        setDownloadStatus('failed', 'Failed');
                        $('#retry_download').show();
                        setDownloadFocusMode(false);
                    } else if (st.status === 'cancelled') {
                        stopStatusPolling();
                        currentRequestId = null;
                        resetDownloadUI();
                        $('#progress_container,#progress_percent,#progress_text').hide();
                        $('#robot_msg').text('⚠️ Download cancelled by user');
                        setDownloadStatus('cancelled', 'Cancelled');
                        $('#retry_download').show();
                        setDownloadFocusMode(false);
                    } else if (st.status === 'cancel_requested') {
                        $('#robot_msg').text('⚠️ Cancellation requested. Stopping job...');
                        setDownloadStatus('queued', 'Cancelling');
                    }
                },
                error: function() {
                    statusPollInFlight = false;
                    stopStatusPolling();
                    currentRequestId = null;
                    resetDownloadUI();
                    $('#progress_container,#progress_percent,#progress_text').hide();
                    $('#robot_msg').text('❌ Error while checking download status');
                    setDownloadStatus('failed', 'Failed');
                    $('#retry_download').show();
                    setDownloadFocusMode(false);
                }
            });
        };

        pollStatus();
        statusPollTimer = setInterval(pollStatus, 1000);
    }

    $('#download_csv').on('click', function() {
        if ($(this).prop('disabled')) return;
        setDownloadMenuOpen(!$('#download_mode_options').is(':visible'));
    });
    $('#download_mode_normal').on('click', () => {
        setDownloadMenuOpen(false);
        downloadReport('csv');
    });
    $('#download_mode_zipped').on('click', () => {
        setDownloadMenuOpen(false);
        downloadReport('csv.gz');
    });
    $('#download_mode_options button').hover(
        function() { $(this).css('background', '#eef6f6'); },
        function() { $(this).css('background', 'transparent'); }
    );
    $('#cancel_download').on('click',function(){
        if(currentXhr){
            currentXhr.abort();
        }
        if (currentLogId) {
            frappe.call({
                method: 'custom_report.api.update_report_log_status',
                args: { log_id: currentLogId, status: 'Cancelled' }
            });
            currentLogId = null;
        }
        stopStatusPolling();
        currentRequestId = null;
        resetDownloadUI();
        $('#progress_container,#progress_percent,#progress_text').hide();
        $('#robot_msg').text('⚠️ Download cancelled by user').show();
        setDownloadStatus('cancelled', 'Cancelled');
        $('#retry_download').show();
        hideDownloadMetrics();
        setDownloadFocusMode(false);
    });

    $('#retry_download').on('click', function() {
        $(this).hide();
        downloadReport('csv');
    });

    $('#new_download_btn').on('click', function() {
        setDownloadFocusMode(false);
        hideDownloadMetrics();
        $('#download_status_badge,#progress_container,#progress_percent,#progress_text,#robot_msg,#retry_download').hide();
        resetDownloadUI();
    });

    function downloadReport(file_type){
        const reportDocName = $selectedReportValue.val(); // Use hidden input value
        const start_date_val=$('#start_date').val();
        const end_date_val=$('#end_date').val();

        // Clear all previous errors
        $('#report_error').hide();
        $('#start_date_error').hide();
        $('#end_date_error').hide();

        // Validate all fields are filled
        if(!reportDocName||!start_date_val||!end_date_val){
            $('#report_error').text('⚠️ Please complete all fields.').show();
            return;
        }

        // Validate date range
        if (!validateDateRange()) {
            return; // Stop if validation fails
        }

        const start_date=formatForAPI(start_date_val), end_date=formatForAPI(end_date_val);
        
        // Get selected sol_ids from dropdown
        const selectedSols = getSelectedSolIds();

        // Show progress UI
        setDownloadMenuOpen(false);
        setDownloadFocusMode(true);
        $('#progress_container,#progress_percent,#progress_text,#robot_msg').show();
        $('#progress_bar').width("0%"); 
        updateProgressPercent(0);
        $('#download_csv').prop('disabled', true).hide();
        $('#cancel_download').show().prop('disabled', false).text('Cancel');
        $('#retry_download').hide();
        setDownloadStatus('queued', 'Queued');
        hideDownloadMetrics();

        frappe.call({
            method: 'custom_report.api.create_report_log_entry',
            args: {
                report_docname: reportDocName,
                start_date: start_date,
                end_date: end_date,
                sol_id: selectedSols.length ? JSON.stringify(selectedSols) : null
            },
            callback: function(res) {
                const payload = res.message || {};
                if (!payload.log_id) {
                    resetDownloadUI();
                    $('#progress_container,#progress_percent,#progress_text').hide();
                    $('#robot_msg').text('❌ Unable to create report log');
                    setDownloadStatus('failed', 'Failed');
                    return;
                }

                currentLogId = payload.log_id;
                if (payload.queue_position) {
                    $('#robot_msg').text(`🤖 Queued at position ${payload.queue_position}, starting...`);
                }

                let url=`/api/method/custom_report.api.report_download?report_docname=${encodeURIComponent(reportDocName)}&start_date=${encodeURIComponent(start_date)}&end_date=${encodeURIComponent(end_date)}&file_type=${file_type}&log_id=${encodeURIComponent(currentLogId)}`;
                if (selectedSols.length > 0) {
                    url += `&sol_id=${encodeURIComponent(JSON.stringify(selectedSols))}`;
                }

                const xhr = new XMLHttpRequest();
                currentXhr = xhr;
                xhr.open("GET", url, true);
                xhr.responseType = "blob";
                xhr.timeout = 0;

                setDownloadStatus('running', 'Running');
                $('#robot_msg').text('🤖 Download in progress...');

                const startedAt = Date.now();
                const timer = setInterval(() => {
                    const elapsed = (Date.now() - startedAt) / 1000;
                    const percent = Math.min(95, Math.floor((elapsed / expectedDuration) * 100));
                    $('#progress_bar').width(percent + "%");
                    updateProgressPercent(percent);
                    $('#progress_text').text(`⏱ ${humanReadableTime(elapsed)} | Download in progress...`);
                }, 500);

                xhr.onload = function() {
                    clearInterval(timer);
                    currentXhr = null;

                    if (xhr.status === 200) {
                        let filename = "finacle_report.csv";
                        const contentDisposition = xhr.getResponseHeader('Content-Disposition');
                        if (contentDisposition) {
                            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                            if (filenameMatch && filenameMatch[1]) {
                                filename = filenameMatch[1].replace(/['"]/g, '');
                            }
                        }

                        const blob = new Blob([xhr.response], {type: "text/csv"});
                        const link = document.createElement("a");
                        link.href = URL.createObjectURL(blob);
                        link.download = filename;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(link.href);

                        $('#progress_bar').width("100%");
                        updateProgressPercent(100);
                        $('#progress_text').text('✅ Completed');
                        $('#robot_msg').text('🤖 Done!');
                        $('#progress_text,#robot_msg').hide();
                        setDownloadStatus('success', 'Success');
                        resetDownloadUI();
                        loadReports();
                        const totalTimeSec = (Date.now() - startedAt) / 1000;
                        const finalLogId = currentLogId;
                        currentLogId = null;
                        if (finalLogId) {
                            frappe.call({
                                method: 'custom_report.api.get_report_log_metrics',
                                args: { log_id: finalLogId },
                                callback: function(metricRes) {
                                    const m = metricRes.message || {};
                                    showDownloadMetrics(m.rows_fetched, m.file_size_mb, totalTimeSec);
                                },
                                error: function() {
                                    showDownloadMetrics(0, blob.size / (1024 * 1024), totalTimeSec);
                                }
                            });
                        } else {
                            showDownloadMetrics(0, blob.size / (1024 * 1024), totalTimeSec);
                        }
                        setDownloadFocusMode(true);
                        $('#new_download_btn').css('display', 'inline-block').show().addClass('new-btn-attn');
                    } else {
                        if (currentLogId) {
                            frappe.call({
                                method: 'custom_report.api.update_report_log_status',
                                args: { log_id: currentLogId, status: 'Failed', error_message: `HTTP ${xhr.status}` }
                            });
                            currentLogId = null;
                        }
                        resetDownloadUI();
                        $('#progress_container,#progress_percent,#progress_text').hide();
                        $('#robot_msg').text('❌ Failed to download');
                        setDownloadStatus('failed', 'Failed');
                        $('#retry_download').show();
                        hideDownloadMetrics();
                        setDownloadFocusMode(false);
                    }
                };

                xhr.onerror = function() {
                    clearInterval(timer);
                    currentXhr = null;
                    if (currentLogId) {
                        frappe.call({
                            method: 'custom_report.api.update_report_log_status',
                            args: { log_id: currentLogId, status: 'Failed', error_message: 'Network error during download' }
                        });
                        currentLogId = null;
                    }
                    resetDownloadUI();
                    $('#progress_container,#progress_percent,#progress_text').hide();
                    $('#robot_msg').text('❌ Error during download');
                    setDownloadStatus('failed', 'Failed');
                    $('#retry_download').show();
                    hideDownloadMetrics();
                    setDownloadFocusMode(false);
                };

                xhr.onabort = function() {
                    clearInterval(timer);
                    currentXhr = null;
                    if (currentLogId) {
                        frappe.call({
                            method: 'custom_report.api.update_report_log_status',
                            args: { log_id: currentLogId, status: 'Cancelled' }
                        });
                        currentLogId = null;
                    }
                    resetDownloadUI();
                    $('#progress_container,#progress_percent,#progress_text').hide();
                    $('#robot_msg').text('⚠️ Download cancelled by user');
                    setDownloadStatus('cancelled', 'Cancelled');
                    $('#retry_download').show();
                    hideDownloadMetrics();
                    setDownloadFocusMode(false);
                };

                xhr.send();
            },
            error: function() {
                resetDownloadUI();
                $('#progress_container,#progress_percent,#progress_text').hide();
                $('#robot_msg').text('❌ Unable to create report log');
                setDownloadStatus('failed', 'Failed');
                hideDownloadMetrics();
                setDownloadFocusMode(false);
            }
        });
    }

    updateSummaryBar();
    refreshDownloadActionState();
}
