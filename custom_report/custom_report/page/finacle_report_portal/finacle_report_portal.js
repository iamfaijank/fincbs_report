frappe.pages['finacle-report-portal'].on_page_load = function(wrapper) {
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

    // Page HTML
    $(page.body).html(`
        <div style="max-width:480px;margin:40px auto;font-family:sans-serif;">
            <div style="padding:20px;background:#fff;border-radius:10px;box-shadow:0 3px 10px rgba(0,0,0,0.1);">
                <h3 style="text-align:center;color:#196767;margin-bottom:25px;">Finacle CBS Report</h3>
                <form id="finacle-report-form" style="display:flex;flex-direction:column;gap:15px;">
                    <div>
                        <label style="font-weight:600;color:#196767;margin-bottom:5px;">Select Report</label>
                        <select id="report_name" class="form-control" required>
                            <option value="" disabled selected>Loading reports...</option>
                        </select>
                        <div id="report_error" style="color:red;font-size:12px;display:none;margin-top:3px;"></div>
                    </div>
                    <div style="display:flex;gap:10px;">
                        <div style="flex:1;">
                            <label style="font-weight:600;color:#196767;margin-bottom:5px;">Start Date</label>
                            <input type="text" id="start_date" class="form-control" required placeholder="DD/MM/YYYY">
                            <div id="start_date_error" style="color:red;font-size:11px;display:none;margin-top:3px;"></div>
                        </div>
                        <div style="flex:1;">
                            <label style="font-weight:600;color:#196767;margin-bottom:5px;">End Date</label>
                            <input type="text" id="end_date" class="form-control" required placeholder="DD/MM/YYYY">
                            <div id="end_date_error" style="color:red;font-size:11px;display:none;margin-top:3px;"></div>
                        </div>
                    </div>
                    <div style="display:flex;gap:10px;">
                        <button type="button" id="download_csv" style="flex:1;background:#196767;color:white;border:none;padding:12px;font-weight:600;border-radius:5px;cursor:pointer;">
                             Download
                        </button>
                        <button type="button" id="cancel_download" style="flex:1;background:#b71c1c;color:white;border:none;padding:12px;font-weight:600;border-radius:5px;cursor:pointer;display:none;">
                             Cancel
                        </button>
                    </div>
                    <div id="progress_container" style="display:none;width:100%;height:12px;background:#eee;border-radius:6px;overflow:hidden;margin-top:10px;position:relative;">
                        <div id="progress_bar" style="width:0%;height:100%;background:linear-gradient(90deg,#196767,#00bfa5);transition:width 0.3s ease;"></div>
                        <div id="progress_percent" style="position:absolute;right:10px;top:-18px;font-size:12px;color:#196767;font-weight:600;"></div>
                    </div>
                    <div id="progress_text" style="display:none;font-size:13px;color:#555;text-align:right;margin-top:3px;"></div>
                    <div id="robot_msg" style="display:none;font-size:13px;color:#196767;text-align:left;margin-top:3px;font-style:italic;"></div>
                </form>
            </div>
        </div>
    `);

    const $reportSelect = $('#report_name');
    let expectedDuration = 2;
    let currentXhr = null;
    let startDatePicker = null;
    let endDatePicker = null;

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
                if (!reports.length) return $reportSelect.html(`<option disabled selected>No reports available</option>`);
                $reportSelect.html(`<option value="" disabled selected>Select Report</option>`);
                reports.forEach(r => {
                    const dur = r.last_duration ? parseFloat(r.last_duration) : '';
                    $reportSelect.append(`<option value="${r.name}" data-duration="${dur}">${r.report_name}</option>`);
                });
            }
        });
    }
    loadReports();

    $reportSelect.on('change', function() {
        const lastDuration = parseFloat($(this).find('option:selected').data('duration'));
        expectedDuration = lastDuration && lastDuration >= 2 ? lastDuration : 2;
        if (lastDuration) {
            $('#progress_text').show().text(`Time Required: ${humanReadableTime(lastDuration)}`);
            $('#robot_msg').show().text('🤖 Ready to download.');
        } else {
            $('#progress_text').hide();
            $('#robot_msg').hide();
        }
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
        const reportDocName=$reportSelect.val(),
              start_date_val=$('#start_date').val(),
              end_date_val=$('#end_date').val();

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
        const url=`/api/method/custom_report.api.report_download?report_docname=${encodeURIComponent(reportDocName)}&start_date=${encodeURIComponent(start_date)}&end_date=${encodeURIComponent(end_date)}&file_type=${file_type}`;

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
