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
                    <div style="font-size:70px;color:#b71c1c;margin-bottom:20px;">📵</div>
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
                <div style="font-size:80px;color:#b71c1c;margin-bottom:20px;">🚫</div>
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

    // Page HTML with Sidebar and Main Content
    $(page.body).html(`
        <div style="display: flex; gap: 20px; max-width: 1200px; margin: 20px auto; font-family: sans-serif; align-items: flex-start;">
            <!-- Sidebar Filter -->
            <div id="sidebar_filter" style="width: 280px; background: #fff; border-radius: 10px; box-shadow: 0 3px 10px rgba(0,0,0,0.1); padding: 20px; display: none; position: sticky; top: 20px;">
                <h4 style="color: #196767; margin-top: 0; margin-bottom: 20px; border-bottom: 2px solid #e0f2f1; padding-bottom: 10px;">Filters</h4>
                
                <div style="margin-bottom: 20px;">
                    <label style="font-weight: 600; color: #196767; display: block; margin-bottom: 10px; font-size: 14px;">Select Branches (SOL ID)</label>
                    <div style="position: relative; margin-bottom: 10px;">
                        <input type="text" id="sol_id_search" class="form-control" placeholder="Search branches..." style="font-size: 13px; height: 32px;">
                    </div>
                    <div id="sol_id_list" style="max-height: 300px; overflow-y: auto; border: 1px solid #ebedef; border-radius: 4px; padding: 5px;">
                        <!-- Checkboxes will be populated here -->
                    </div>
                    <div style="margin-top: 10px; display: flex; gap: 8px;">
                        <button type="button" id="select_all_sol" style="flex: 1; font-size: 11px; padding: 4px; cursor: pointer; background: #f0f4f4; border: 1px solid #d1d8d8; border-radius: 4px;">Select All</button>
                        <button type="button" id="clear_all_sol" style="flex: 1; font-size: 11px; padding: 4px; cursor: pointer; background: #f0f4f4; border: 1px solid #d1d8d8; border-radius: 4px;">Clear</button>
                    </div>
                </div>
            </div>

            <!-- Main Content Area -->
            <div style="flex: 1;">
                <div style="max-width:480px; margin: 0 auto; background:#fff; border-radius:10px; box-shadow:0 3px 10px rgba(0,0,0,0.1); padding:20px;">
                    <h3 style="text-align:center; color:#196767; margin-bottom:10px;">Finacle CBS Report</h3>
                    <div id="user_permissions_info" style="text-align:center; margin-bottom:20px; display:none;">
                        <!-- Permissions info will be populated here -->
                    </div>
                    <form id="finacle-report-form" style="display:flex; flex-direction:column; gap:15px;">
                        <div>
                            <label style="font-weight:600; color:#196767; margin-bottom:5px;">Select Report</label>
                            <div style="position:relative;">
                                <input type="text" id="report_search" class="form-control" placeholder="🔍 Search or select report..." autocomplete="off" style="padding-right:35px;">
                                <span id="search_clear" style="position:absolute; right:10px; top:50%; transform:translateY(-50%); cursor:pointer; color:#999; display:none; font-size:18px;" title="Clear search">✕</span>
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
                        <div style="display:flex; gap:10px;">
                            <button type="button" id="download_csv" style="flex:1; background:#196767; color:white; border:none; padding:12px; font-weight:600; border-radius:5px; cursor:pointer;">
                                 Download
                            </button>
                            <button type="button" id="cancel_download" style="flex:1; background:#b71c1c; color:white; border:none; padding:12px; font-weight:600; border-radius:5px; cursor:pointer; display:none;">
                                 Cancel
                            </button>
                        </div>
                        <div id="progress_container" style="display:none; width:100%; height:12px; background:#eee; border-radius:6px; overflow:hidden; margin-top:10px; position:relative;">
                            <div id="progress_bar" style="width:0%; height:100%; background:linear-gradient(90deg,#196767,#00bfa5); transition:width 0.3s ease;"></div>
                            <div id="progress_percent" style="position:absolute; right:10px; top:-18px; font-size:12px; color:#196767; font-weight:600;"></div>
                        </div>
                        <div id="progress_text" style="display:none; font-size:13px; color:#555; text-align:right; margin-top:3px;"></div>
                        <div id="robot_msg" style="display:none; font-size:13px; color:#196767; text-align:left; margin-top:3px; font-style:italic;"></div>
                    </form>
                </div>
            </div>
        </div>
    `);

    const $reportSelect = $('#report_name');
    const $reportSearch = $('#report_search');
    const $reportDropdown = $('#report_dropdown');
    const $selectedReportValue = $('#selected_report_value');
    const $searchClear = $('#search_clear');
    const $solIdList = $('#sol_id_list');
    const $solIdSearch = $('#sol_id_search');
    
    // Fetch and show user permissions/branches
    function loadUserPermissions() {
        frappe.call({
            method: 'custom_report.api.get_user_report_permissions',
            callback: function(res) {
                if (res.message && (res.message.is_branch_user || res.message.is_dept_user)) {
                    const sol_ids = res.message.sol_ids || [];
                    userSolIds = sol_ids;
                    const is_dept = res.message.is_dept_user;
                    const $info = $('#user_permissions_info');
                    const $sidebar = $('#sidebar_filter');
                    
                    $info.show();
                    $sidebar.show();
                    
                    if (sol_ids.length > 0 || is_dept) {
                        let badgeHtml = '';
                        if (is_dept) {
                            badgeHtml = '<span id="dept_status_badge" style="background:#00796b;color:white;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600;">Full Access (All Branches)</span>';
                        } else {
                            badgeHtml = `
                                <span style="font-size:12px;color:#00796b;font-weight:600;">📍 Filtered for Branches:</span>
                                <div id="active_sol_badges" style="display:flex;flex-wrap:wrap;gap:4px;justify-content:center;margin-top:4px;">
                                    ${sol_ids.map(id => `<span class="sol-badge" data-sol="${id}" style="background:#196767;color:white;padding:1px 6px;border-radius:4px;font-size:11px;font-weight:600;">${id}</span>`).join('')}
                                </div>
                            `;
                        }

                        $info.html(`
                            <div style="background:#e0f2f1;border:1px solid #b2dfdb;border-radius:6px;padding:8px 12px;display:inline-block;">
                                ${badgeHtml}
                                <div id="dept_manual_badges" style="display:flex;flex-wrap:wrap;gap:4px;justify-content:center;margin-top:4px;"></div>
                            </div>
                        `);

                        // Populate sidebar list
                        populateSolIdList(sol_ids, is_dept);
                    } else if (!is_dept) {
                        $info.html(`
                            <div style="background:#ffebee;border:1px solid #ffcdd2;border-radius:6px;padding:10px 15px;">
                                <p style="color:#c62828;font-size:13px;font-weight:600;margin:0;">⚠️ No branches assigned in Report Preference.</p>
                                <p style="color:#555;font-size:11px;margin:5px 0 0 0;">Please contact your administrator to set up your branch list.</p>
                            </div>
                        `);
                        // Disable download if no branches assigned for branch report user
                        $('#download_csv').prop('disabled', true).css('opacity', '0.6').attr('title', 'No branches assigned');
                    }
                }
            }
        });
    }

    function populateSolIdList(sol_ids, is_dept) {
        let html = '';
        sol_ids.forEach(id => {
            // For dept users, don't check by default so they see "All Branches"
            const checked = is_dept ? '' : 'checked';
            html += `
                <div class="sol-item" style="display: flex; align-items: center; gap: 8px; padding: 4px; border-bottom: 1px solid #f8f9fa;">
                    <input type="checkbox" id="chk_${id}" value="${id}" ${checked} style="cursor: pointer;">
                    <label for="chk_${id}" style="font-size: 13px; margin: 0; cursor: pointer; color: #444;">${id}</label>
                </div>
            `;
        });
        $solIdList.html(html);

        // Sidebar checkbox changes
        $solIdList.on('change', 'input[type="checkbox"]', function() {
            updateActiveBadges(is_dept);
        });
    }

    function updateActiveBadges(is_dept) {
        const selected = getSelectedSolIds();
        
        if (is_dept) {
            const $statusBadge = $('#dept_status_badge');
            const $manualBadges = $('#dept_manual_badges');
            
            if (selected.length === 0) {
                $statusBadge.text('Full Access (All Branches)').css('background', '#00796b');
                $manualBadges.empty();
            } else {
                $statusBadge.text(`Filtered (${selected.length} Selected)`).css('background', '#196767');
                $manualBadges.html(selected.map(id => `<span class="sol-badge" data-sol="${id}" style="background:#196767;color:white;padding:1px 6px;border-radius:4px;font-size:11px;font-weight:600;">${id}</span>`).join(''));
            }
            $('#download_csv').prop('disabled', false).css('opacity', '1');
        } else {
            let html = selected.map(id => `<span class="sol-badge" data-sol="${id}" style="background:#196767;color:white;padding:1px 6px;border-radius:4px;font-size:11px;font-weight:600;">${id}</span>`).join('');
            
            if (selected.length === 0) {
                html = '<span style="color: #c62828; font-size: 11px;">No branches selected</span>';
                $('#download_csv').prop('disabled', true).css('opacity', '0.6');
            } else {
                $('#download_csv').prop('disabled', false).css('opacity', '1');
            }
            $('#active_sol_badges').html(html);
        }
    }

    function getSelectedSolIds() {
        return $solIdList.find('input[type="checkbox"]:checked').map(function() {
            return $(this).val();
        }).get();
    }

    // Sidebar search
    $solIdSearch.on('input', function() {
        const term = $(this).val().toLowerCase();
        $solIdList.find('.sol-item').each(function() {
            const id = $(this).find('input').val().toLowerCase();
            $(this).toggle(id.includes(term));
        });
    });

    // Select/Clear All
    $('#select_all_sol').on('click', () => {
        $solIdList.find('input[type="checkbox"]:visible').prop('checked', true);
        updateActiveBadges();
    });

    $('#clear_all_sol').on('click', () => {
        $solIdList.find('input[type="checkbox"]:visible').prop('checked', false);
        updateActiveBadges();
    });

    loadUserPermissions();

    let expectedDuration = 2;
    let currentXhr = null;
    let startDatePicker = null;
    let endDatePicker = null;
    let allReports = []; // Store all reports for searching

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
                
                // Update end date minimum to selected start date
                if (endDatePicker && selectedDates.length > 0) {
                    endDatePicker.set('minDate', selectedDates[0]);
                }
                
                // Validate if end date is already selected
                validateDateRange();
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
                
                // Validate date range
                validateDateRange();
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
    });

    function formatForAPI(val){ 
        const [d,m,y]=val.split('/'); 
        return `${y}-${m.padStart(2,'0')}-${d.padStart(2,'0')}`; 
    }
    
    function humanReadableTime(sec){ 
        const m=Math.floor(sec/60), s=Math.floor(sec%60); 
        return m>0?`${m} Minutes ${s} Seconds`:`${s} Seconds`; 
    }

    $('#download_csv').on('click',()=>downloadReport('csv'));
    $('#cancel_download').on('click',function(){
        if(currentXhr){ currentXhr.abort(); }
        $(this).prop('disabled',true).text('Cancelling...');
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
        
        // Build URL with optional sol_id filter for Branch Report role
        let url=`/api/method/custom_report.api.report_download?report_docname=${encodeURIComponent(reportDocName)}&start_date=${encodeURIComponent(start_date)}&end_date=${encodeURIComponent(end_date)}&file_type=${file_type}`;
        
        // If sidebar is visible, get selected sol_ids
        if ($('#sidebar_filter').is(':visible')) {
            const selectedSols = getSelectedSolIds();
            if (selectedSols.length > 0) {
                // Pass as stringified array or comma separated
                url += `&sol_id=${encodeURIComponent(JSON.stringify(selectedSols))}`;
            }
        }

        const xhr=new XMLHttpRequest();
        currentXhr = xhr;
        xhr.open("GET",url,true);
        xhr.responseType="blob";

        // Show progress UI
        $('#progress_container,#progress_text,#robot_msg').show();
        $('#progress_bar').width("0%"); 
        $('#progress_percent').text("0%");
        $('#download_csv').prop('disabled',true).text('Downloading...');
        $('#cancel_download').show().prop('disabled',false).text('❌ Cancel');

        const startTime=Date.now();
        const interval=setInterval(()=>{
            const elapsed=(Date.now()-startTime)/1000;
            const percent=Math.min(99,Math.floor((elapsed/expectedDuration)*100));
            $('#progress_bar').width(percent+"%");
            $('#progress_percent').text(percent+"%");
            $('#progress_text').text(`⏱ ${humanReadableTime(elapsed)} | ${percent}%`);
            $('#robot_msg').text(elapsed>expectedDuration?'🤖 Large data, please wait…':`⏳ About ${humanReadableTime(expectedDuration-elapsed)} remaining`);
        },200);

        xhr.onload=function(){
            clearInterval(interval);
            $('#cancel_download').hide();
            $('#download_csv').prop('disabled',false).text('Download');

            if(xhr.status===200){
                // Extract filename from Content-Disposition header
                let filename = "finacle_report.csv"; // Default fallback
                
                const contentDisposition = xhr.getResponseHeader('Content-Disposition');
                if (contentDisposition) {
                    // Parse filename from header: attachment; filename="Report_31-10-2025 12-30 PM.csv"
                    const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                    if (filenameMatch && filenameMatch[1]) {
                        filename = filenameMatch[1].replace(/['"]/g, '');
                    }
                }

                const blob=new Blob([xhr.response],{type:"text/csv"});
                const link=document.createElement("a"); 
                link.href=URL.createObjectURL(blob); 
                link.download=filename; // Use dynamic filename from backend
                link.click();
                
                $('#progress_bar').width("100%"); 
                $('#progress_percent').text("100%");
                $('#progress_text').text('✅ Download complete');
                $('#robot_msg').text('🤖 Done!');
                loadReports();
                setTimeout(()=>$('#progress_container,#progress_text,#robot_msg').fadeOut(),3000);

            } else {
                // DB connection failure message
                let errorMsg = '❌ Failed to download.';
                try {
                    const reader = new FileReader();
                    reader.onload = function() {
                        const msg = reader.result;
                        if(msg && msg.includes("Database connection failed")) {
                            errorMsg = "❌ Database connection is down. Please try later.";
                        }
                        $('#robot_msg').text(errorMsg);
                    };
                    reader.readAsText(xhr.response);
                } catch(e){
                    $('#robot_msg').text(errorMsg);
                }
                $('#progress_container,#progress_text').hide();
            }
        };

        xhr.onabort=function(){
            clearInterval(interval);
            $('#cancel_download').hide();
            $('#progress_container,#progress_text').hide();
            $('#robot_msg').text('⚠️ Download cancelled by user');
            $('#download_csv').prop('disabled',false).text('Download');
        };

        xhr.onerror=function(){
            clearInterval(interval);
            $('#cancel_download').hide();
            $('#progress_container,#progress_text').hide();
            $('#robot_msg').text('❌ Error during download'); 
            $('#download_csv').prop('disabled',false).text('Download'); 
        };

        xhr.send();
    }
}
