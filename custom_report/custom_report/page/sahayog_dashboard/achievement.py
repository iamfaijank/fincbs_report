import frappe
import json
from dateutil.relativedelta import relativedelta
from custom_report.db_connection import get_dr_connection
from datetime import datetime



def date_control(input_date):
    current_date = datetime.strptime(input_date, "%d-%m-%Y").date()

    if current_date >= datetime.today().date():
        current_date = datetime.today().date() - relativedelta(days=1)
        if current_date.weekday() == 6:  # 6 is Sunday
            current_date = current_date - relativedelta(days=1)
            print(f"Notice: Adjusted past Sunday. Automatically picking Saturday T-2 date ({current_date.strftime('%d-%m-%Y')}).")
        else:
            print(f"Notice: Provided date is today or in the future. Automatically adjusting to T-1 date ({current_date.strftime('%d-%m-%Y')}).")

    current_month_first_date = current_date.replace(day=1)
    current_month_total_days_till_date = current_date.day

    last_month_last_date = current_month_first_date - relativedelta(days=1)
    last_month_first_date = last_month_last_date.replace(day=1)
    last_month_total_days = last_month_last_date.day

    print("\n==============================")
    print(f"Current Date: {current_date}")
    print(f"Current Month First Date: {current_month_first_date}")
    print(f"Current Month Days Till Date: {current_month_total_days_till_date}")
    print(f"Last Month First Date: {last_month_first_date}")
    print(f"Last Month Last Date: {last_month_last_date}")
    print(f"Last Month Total Days: {last_month_total_days}")
    print("==============================\n")

    return {
        "current_date": current_date,
        "current_month_first_date": current_month_first_date,
        "current_month_total_days_till_date": current_month_total_days_till_date,
        "last_month_first_date": last_month_first_date,
        "last_month_last_date": last_month_last_date,
        "last_month_total_days": last_month_total_days
    }


def execute_achievement_query(dates):
    curr_date = dates['current_date'].strftime('%Y-%m-%d')
    curr_first = dates['current_month_first_date'].strftime('%Y-%m-%d')
    last_first = dates['last_month_first_date'].strftime('%Y-%m-%d')
    last_last = dates['last_month_last_date'].strftime('%Y-%m-%d')
    curr_days = dates['current_month_total_days_till_date']
    last_days = dates['last_month_total_days']

    query = f"""
	---FINAL DRISHTI QUERY 19-06-2026---- SOL WISE----
-- ✅ FIX: flow_data aur tran_data mein FD scheme codes ke CLOSED accounts exclude kiye gaye hain
--         Baaki poori query BILKUL AS-IT-IS hai, koi change nahi.
--         FD Scheme Codes: '2008','2009','2001','2031','2023','2020','2018','2019','2032','2033','2106'
--         Condition: Agar schm_code FD wala hai aur acct_cls_flg != 'N' (closed) toh exclude karo
 
 
WITH excluded_accts AS (
    SELECT column_value AS account_number
    FROM (VALUES
        ('100110020002993'),
        ('100110020101562'),
        ('100111020003840'),
        ('100144590010496'),
        ('110544207002485')
    ) t(column_value)
),
/* ================= FLOW DATA (NO EXCLUSION) ================= */  
flow_data AS (
    SELECT
        g.sol_id,
        s.sol_desc,
        s.region_name,
        s.division_name,
        s.circle_office_name,
        SUM(tdt.flow_amt) AS total_flow_amount
    FROM custom.dsamap d
    INNER JOIN tbaadm.gam g
        ON g.foracid = d.account_number
       AND g.schm_type = 'TDA'
    INNER JOIN tbaadm.sol s
        ON s.sol_id = g.sol_id
    INNER JOIN tbaadm.tdt tdt
        ON tdt.acid = g.acid
       AND tdt.flow_code IN ('PI','NI')
    WHERE tdt.flow_date BETWEEN DATE '{curr_first}' AND DATE '{curr_date}'  ---REPORT MONTH START{{current_month_first_date}} & END DATE{{current_date}}
      -- ✅ FIX: FD scheme codes ke closed accounts exclude karo
      --         Agar account FD scheme ka hai AUR closed hai toh mat lo
      AND NOT (
                g.schm_code IN ('2008','2009','2001','2031','2023','2020','2018','2019','2032','2033','2106','2103')
                AND g.acct_cls_flg != 'N'
              )
    GROUP BY
        g.sol_id,
        s.sol_desc,
        s.region_name,
        s.division_name,
        s.circle_office_name
),
/* ================= TRAN DATA (NO EXCLUSION) ================= */
tran_data AS (
    SELECT
        g.sol_id,
        SUM(dtt.tran_amt) AS total_tran_amt
    FROM custom.dsamap d
    INNER JOIN tbaadm.gam g
        ON g.foracid = d.account_number
       AND g.schm_type = 'TDA'
    INNER JOIN tbaadm.dtt dtt
        ON dtt.acid = g.acid
       AND dtt.flow_code IN ('PI','NI')
    WHERE dtt.value_date BETWEEN DATE '{curr_first}' AND DATE '{curr_date}'  ---REPORT MONTH START{{current_month_first_date}} & END DATE{{current_date}}
      -- ✅ FIX: FD scheme codes ke closed accounts exclude karo
      --         Agar account FD scheme ka hai AUR closed hai toh mat lo
      AND NOT (
                g.schm_code IN ('2008','2009','2001','2031','2023','2020','2018','2019','2032','2033','2106','2103')
                AND g.acct_cls_flg != 'N'
              )
    GROUP BY g.sol_id
),
final_data AS (
    SELECT
        COALESCE(f.sol_id, t.sol_id) AS sol_id,
        COALESCE(f.sol_desc, s.sol_desc) AS sol_desc,
        COALESCE(f.region_name, s.region_name) AS region_name,
        COALESCE(f.division_name, s.division_name) AS division_name,
        COALESCE(f.circle_office_name, s.circle_office_name) AS circle_office_name,
        COALESCE(f.total_flow_amount, 0) AS total_flow_amount,
        COALESCE(t.total_tran_amt, 0) AS total_tran_amt
    FROM flow_data f
    FULL OUTER JOIN tran_data t
        ON f.sol_id = t.sol_id
    LEFT JOIN tbaadm.sol s
        ON s.sol_id = COALESCE(f.sol_id, t.sol_id)
),
/* ================= MAB BASE DATA (EXCLUDED ACCOUNTS APPLIED) ================= */
june_data AS (
    SELECT
        g.sol_id,
        e.tran_date_bal,
        (
            EXTRACT(
                DAY FROM (
                    LEAST(
                        CASE
                            WHEN e.end_eod_date = DATE '2099-12-31'   --HARDCODE DATE
                                THEN DATE '{curr_date}'   ---REPORT MONTH END DATE{{current_date}}
                            ELSE e.end_eod_date
                        END,
                        DATE '{curr_date}'   ---REPORT MONTH END DATE{{current_date}}
                    )
                    -
                    GREATEST(e.eod_date, DATE '{curr_first}') ---REPORT MONTH START DATE{{current_month_first_date}}
                )
            ) + 1
        ) AS active_days
    FROM tbaadm.gam g
    JOIN tbaadm.eab e
        ON g.acid = e.acid
    WHERE g.schm_code IN ('1002','1011','1102','1103','1104')
      -- 🔥 EXCLUDE ACCOUNTS ONLY FOR MAB
      -- 🔥 EXCLUDE ACCOUNTS ONLY FOR MAB
      AND NOT EXISTS (
            SELECT 1
            FROM excluded_accts x
            WHERE x.account_number = g.foracid
          )
      AND (
            g.acct_cls_date IS NULL
            OR g.acct_cls_date BETWEEN DATE '{curr_first}' AND DATE '{curr_date}'  ---REPORT MONTH START{{current_month_first_date}} & END DATE{{current_date}}
          )
      AND e.eod_date <= DATE '{curr_date}'  ---REPORT MONTH END DATE{{current_date}}
      AND (
            CASE
                WHEN e.end_eod_date = DATE '2099-12-31'    --HARDCODE DATE
                    THEN DATE '{curr_date}'   ---REPORT MONTH END DATE{{current_date}}
                ELSE e.end_eod_date
            END
          ) >= DATE '{curr_first}'  ---REPORT MONTH START DATE{{current_month_first_date}}
),
june_mab AS (
    SELECT
        sol_id,
        SUM(tran_date_bal * active_days) / {curr_days} AS closing_mab  --TOTAL DAYS OF CURRENT MONTH AS PER REPORT DATE RANGE{{current_month_total_days_till_date}} map to 24
    FROM june_data
    GROUP BY sol_id
),
may_data AS (
    SELECT
        g.sol_id,
        e.tran_date_bal,
        (
            EXTRACT(
                DAY FROM (
                    LEAST(
                        CASE
                            WHEN e.end_eod_date = DATE '2099-12-31'   --HARDCODE DATE
                                THEN DATE '{last_last}'   ---LAST MONTH END DATE{{last_month_last_date}}
                            ELSE e.end_eod_date
                        END,
                        DATE '{last_last}' ---LAST MONTH END DATE{{last_month_last_date}}
                    )
                    -
                    GREATEST(e.eod_date, DATE '{last_first}') ---LAST MONTH START DATE{{last_month_first_date}}
                )
            ) + 1
        ) AS active_days
    FROM tbaadm.gam g
    JOIN tbaadm.eab e
        ON g.acid = e.acid
    WHERE g.schm_code IN ('1002','1011','1102','1103','1104')
      -- 🔥 EXCLUDE SAME ACCOUNTS
      -- 🔥 EXCLUDE ACCOUNTS ONLY FOR MAB
      AND NOT EXISTS (
            SELECT 1
            FROM excluded_accts x
            WHERE x.account_number = g.foracid
          )
      AND (
            g.acct_cls_date IS NULL
            OR g.acct_cls_date BETWEEN DATE '{curr_first}' AND DATE '{curr_date}' ---REPORT MONTH START{{current_month_first_date}} & END DATE{{current_date}}
          )
      AND e.eod_date <= DATE '{last_last}' ---LAST MONTH END DATE{{last_month_last_date}}
      AND (
            CASE
                WHEN e.end_eod_date = DATE '2099-12-31'  --HARDCODE DATE
                    THEN DATE '{last_last}' ---LAST MONTH END DATE{{last_month_last_date}}
                ELSE e.end_eod_date
            END
          ) >= DATE '{last_first}' ---LAST MONTH START DATE{{last_month_first_date}}
),
may_mab AS (
    SELECT
        sol_id,
        SUM(tran_date_bal * active_days) / {last_days} AS opening_mab -- TOTAL DAYS OF LAST MONTH{{last_month_total_days}} map to 31
    FROM may_data
    GROUP BY sol_id
),
june_balance AS (
    SELECT
        g.sol_id,
        SUM(e.tran_date_bal) AS closing_balance
    FROM tbaadm.gam g
    JOIN tbaadm.eab e
        ON g.acid = e.acid
    WHERE g.schm_code IN ('1002','1011','1102','1103','1104')
      -- 🔥 EXCLUDE ACCOUNTS
      -- 🔥 EXCLUDE ACCOUNTS ONLY FOR MAB
      AND NOT EXISTS (
            SELECT 1
            FROM excluded_accts x
            WHERE x.account_number = g.foracid
          )
      AND (
            g.acct_cls_date IS NULL
            OR g.acct_cls_date BETWEEN DATE '{curr_first}' AND DATE '{curr_date}'  ---REPORT MONTH START{{current_month_first_date}} & END DATE{{current_date}}
          )
      AND DATE '{curr_date}' BETWEEN e.eod_date  ---REPORT MONTH END DATE{{current_date}}
      AND CASE
            WHEN e.end_eod_date = DATE '2099-12-31'   --HARDCODE DATE
                THEN DATE '{curr_date}' ---REPORT MONTH END DATE{{current_date}}
            ELSE e.end_eod_date
          END
    GROUP BY g.sol_id
),
may_balance AS (
    SELECT
        g.sol_id,
        SUM(e.tran_date_bal) AS opening_balance
    FROM tbaadm.gam g
    JOIN tbaadm.eab e
        ON g.acid = e.acid
    WHERE g.schm_code IN ('1002','1011','1102','1103','1104')
      -- 🔥 EXCLUDE ACCOUNTS
      -- 🔥 EXCLUDE ACCOUNTS ONLY FOR MAB
      AND NOT EXISTS (
            SELECT 1
            FROM excluded_accts x
            WHERE x.account_number = g.foracid
          )
      AND (
            g.acct_cls_date IS NULL
            OR g.acct_cls_date BETWEEN DATE '{curr_first}' AND DATE '{curr_date}' ---REPORT MONTH START{{current_month_first_date}} & END DATE{{current_date}}
          )
      AND DATE '{last_last}' BETWEEN e.eod_date ---LAST MONTH END DATE{{last_month_last_date}}
      AND CASE
            WHEN e.end_eod_date = DATE '2099-12-31'  --HARDCODE DATE
                THEN DATE '{last_last}' ---LAST MONTH END DATE{{last_month_last_date}}
            ELSE e.end_eod_date
          END
    GROUP BY g.sol_id
),
mab_final AS (
    SELECT
        m.sol_id,
        ab.opening_balance,
        mb.closing_balance,
        ROUND(COALESCE(a.opening_mab, 0), 0) AS opening_mab,
        ROUND(COALESCE(m.closing_mab, 0), 0) AS closing_mab,
        ROUND(COALESCE(m.closing_mab, 0), 0)
        - ROUND(COALESCE(a.opening_mab, 0), 0) AS inc_mab
    FROM june_mab m
    LEFT JOIN may_mab a
        ON m.sol_id = a.sol_id
    LEFT JOIN june_balance mb
        ON m.sol_id = mb.sol_id
    LEFT JOIN may_balance ab
        ON m.sol_id = ab.sol_id
)
/* ================= FINAL OUTPUT ================= */
SELECT
    s.sol_id,
    s.sol_desc,
    s.region_name,
    s.division_name,
    s.circle_office_name,
    COALESCE(f.total_flow_amount, 0) AS total_flow_amount,
    COALESCE(f.total_tran_amt, 0) AS total_tran_amt,
--    COALESCE(CEIL(m.opening_balance), 0) AS opening_balance,
--    COALESCE(CEIL(m.closing_balance), 0) AS closing_balance,
    COALESCE(m.opening_balance, 0) AS opening_balance,
    COALESCE(m.closing_balance, 0) AS closing_balance,
    COALESCE(m.opening_mab, 0) AS opening_mab,
    COALESCE(m.closing_mab, 0) AS closing_mab,
    COALESCE(m.inc_mab, 0) AS inc_mab,
--    ROUND(
--    COALESCE(f.total_tran_amt, 0)
--    + COALESCE(m.inc_mab, 0),
--     0) AS achivment
   ROUND(
        CASE
            WHEN COALESCE(m.inc_mab, 0) < 0
                THEN COALESCE(f.total_tran_amt, 0) - ABS(COALESCE(m.inc_mab, 0))  
            ELSE
                COALESCE(f.total_tran_amt, 0) + COALESCE(m.inc_mab, 0)
        END,
    0) AS achivment
FROM tbaadm.sol s
LEFT JOIN final_data f
    ON s.sol_id = f.sol_id
LEFT JOIN mab_final m
    ON s.sol_id = m.sol_id
WHERE s.sol_id NOT IN ('1000','1031','1059','1081','1104')   ---EXCLUDE THESE SOL_ID FROM FINAL OUTPUT    
ORDER BY achivment DESC;
"""

    print("\nExecuting query on DR database... Please wait...")
    conn = get_dr_connection()
    if not conn:
        print("Failed to connect to DR database")
        return

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        
        if not result:
            print("No data found.")
            return []
            
        print(f"Query executed successfully! Returned {len(result)} rows.\n")
        
        # Get column names
        headers = [desc[0] for desc in cursor.description]
        
        # Format as JSON for all records
        json_data = []
        for row in result:
            row_dict = {}
            for i, val in enumerate(row):
                if val is None:
                    row_dict[headers[i]] = None
                elif isinstance(val, (int, float, str, bool)):
                    row_dict[headers[i]] = val
                else:
                    # Convert Decimals/Dates etc. to string
                    row_dict[headers[i]] = str(val)
            json_data.append(row_dict)
            
        print("Showing records by achievement in JSON format:\n")
        print(json.dumps(json_data, indent=4))
        
        return result
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def get_fiscal_year(date_obj):
    """Calculate Indian Financial Year (Apr–Mar)"""
    year = date_obj.year
    if date_obj.month >= 4:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"


def get_previous_month_last_ytd(sol_id, date_obj):
    """
    Returns the yearly_achievement of the last synced day of the previous month 
    in the same financial year. Returns 0.0 if there is no previous month or no record.
    """
    import calendar
    from frappe.utils import getdate
    
    fiscal_year = get_fiscal_year(date_obj)
    start_year = int(fiscal_year.split("-")[0])
    
    # Financial year months list: April is first
    fy_months = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]
    current_month = date_obj.month
    
    # Find the month immediately preceding current_month in the FY list
    try:
        curr_idx = fy_months.index(current_month)
    except ValueError:
        return 0.0
        
    if curr_idx == 0:
        # April has no previous month in the current financial year
        return 0.0
        
    prev_month = fy_months[curr_idx - 1]
    prev_year = start_year if prev_month >= 4 else start_year + 1
    
    # Find the last day of that previous month
    last_day = calendar.monthrange(prev_year, prev_month)[1]
    start_date = f"{prev_year}-{prev_month:02d}-01"
    end_date = f"{prev_year}-{prev_month:02d}-{last_day:02d}"
    
    # Query the latest record in that month for this sol_id
    last_ytd = frappe.db.get_value(
        "Branch Category Report",
        {
            "sol_id": sol_id,
            "date": ["between", [start_date, end_date]],
            "docstatus": ["<", 2]
        },
        "yearly_achievement",
        order_by="date desc"
    )
    
    return float(last_ytd or 0.0)


def recalculate_subsequent_ytd(sol_id, date_obj):
    """
    Recalculates yearly_achievement and ytd_achi for all records of sol_id 
    in the same financial year that are dated AFTER date_obj.
    """
    from frappe.utils import getdate
    
    fiscal_year = get_fiscal_year(date_obj)
    start_year = int(fiscal_year.split("-")[0])
    
    # Financial year ends on March 31st of start_year + 1
    end_of_fy = f"{start_year + 1}-03-31"
    
    # Get all subsequent records of the same FY ordered by date ascending
    records = frappe.db.get_all(
        "Branch Category Report",
        filters={
            "sol_id": sol_id,
            "date": [">", date_obj],
            "docstatus": ["<", 2]
        },
        fields=["name", "date", "achievement"],
        order_by="date asc"
    )
    
    if not records:
        return
        
    for rec in records:
        rec_date = getdate(rec.date)
        if rec_date > getdate(end_of_fy):
            continue
            
        # Get baseline (previous month's last YTD)
        prev_month_ytd = get_previous_month_last_ytd(sol_id, rec_date)
        
        # Calculate new YTD
        achievement = float(rec.achievement or 0.0)
        yearly_achievement = prev_month_ytd + achievement
        
        # Fetch YTD target
        ytd_target = frappe.db.get_value(
            "Target Vs Achivement",
            {"sol_id": sol_id, "financial_year": fiscal_year, "type": "YTD"},
            "target"
        )
        ytd_target = float(ytd_target or 0.0)
        ytd_achi_pct = (yearly_achievement / ytd_target * 100) if ytd_target > 0.0 else 0.0
        
        # Update the record
        frappe.db.set_value(
            "Branch Category Report",
            rec.name,
            {
                "yearly_achievement": yearly_achievement,
                "ytd_achi": safe_str(round(ytd_achi_pct, 2))
            },
            update_modified=False
        )


def safe_str(val):
    """Helper to convert values to string type safely"""
    if val is None:
        return ""
    try:
        # If it has a float value, format cleanly without trailing .0 if integer
        f_val = float(val)
        return str(int(f_val)) if f_val.is_integer() else str(f_val)
    except (ValueError, TypeError):
        return str(val)


@frappe.whitelist()
def generate_and_save_branch_category_report(input_date):
    """
    Generate and save achievement records to 'Branch Category Report' doctype for a particular date.
    Validates if records already exist for the given date before inserting.
    """
    from frappe.utils import getdate
    
    # 1. Date conversion
    date_obj = getdate(input_date)
    input_date_str = date_obj.strftime("%d-%m-%Y")
    dates = date_control(input_date_str)
    processed_date = dates["current_date"]
    
    # Sunday validation (exclude Sundays)
    if processed_date.weekday() == 6:  # 6 is Sunday in Python
        frappe.msgprint(f"Date {processed_date} is a Sunday. Sundays are excluded from data sync.")
        return []
        
    # 2. Check if records already exist for this processed date
    if frappe.db.exists("Branch Category Report", {"date": processed_date}):
        frappe.msgprint(f"Branch Category Report records already exist for date {processed_date}. Skipping insert.")
        return []
        
    # 3. Execute achievement query
    query_results = execute_achievement_query(dates)
    if not query_results:
        return []
        
    saved_count = 0
    for row in query_results:
        sol_id = str(row[0]).strip()
        sol_desc = row[1]
        region_name = row[2]
        division_name = row[3]
        circle_office_name = row[4]
        total_flow_amount = row[5]
        total_tran_amt = row[6]
        opening_balance = row[7]
        closing_balance = row[8]
        opening_mab = row[9]
        closing_mab = row[10]
        inc_mab = row[11]
        achievement = float(row[12] or 0)
        
        # Calculate YTD achievement (previous month last YTD + current month achievement)
        prev_achievement = get_previous_month_last_ytd(sol_id, processed_date)
        yearly_achievement = prev_achievement + achievement

        # Fetch proper zone, region, and branch from 'Sahayog Branch' using sol_id
        branch_info = frappe.db.get_value(
            "Sahayog Branch",
            {"sol_id": sol_id},
            ["zone", "region", "branch"],
            as_dict=True
        )
        
        final_zone = division_name
        final_region = region_name
        final_branch = sol_desc
        
        if branch_info:
            if branch_info.get("zone"):
                final_zone = branch_info.get("zone")
            if branch_info.get("region"):
                final_region = branch_info.get("region")
            if branch_info.get("branch"):
                final_branch = branch_info.get("branch")

        # Get targets from 'Target Vs Achivement' to calculate category and YTD %
        month_val = processed_date.month
        year_val = processed_date.year
        if month_val >= 4:
            financial_year = f"{year_val}-{year_val+1}"
        else:
            financial_year = f"{year_val-1}-{year_val}"
            
        month_key = processed_date.strftime("%b").upper()

        monthly_target = frappe.db.get_value(
            "Target Vs Achivement",
            {"sol_id": sol_id, "financial_year": financial_year, "type": "Monthly", "month": month_key},
            "target"
        )
        monthly_target = float(monthly_target or 0)
        
        ytd_target = frappe.db.get_value(
            "Target Vs Achivement",
            {"sol_id": sol_id, "financial_year": financial_year, "type": "YTD"},
            "target"
        )
        ytd_target = float(ytd_target or 0)

        # Calculate percentages
        monthly_pct = (achievement / monthly_target * 100) if monthly_target > 0 else 0
        ytd_achi_pct = (yearly_achievement / ytd_target * 100) if ytd_target > 0 else 0
        
        # Calculate Category
        if monthly_pct >= 100:
            branch_category = "Pinnacle"
        elif monthly_pct >= 80:
            branch_category = "Master"
        elif monthly_pct >= 60:
            branch_category = "Accelerator"
        elif monthly_pct >= 40:
            branch_category = "Starter"
        elif monthly_pct >= 20:
            branch_category = "Learner"
        else:
            branch_category = "Zero Level"
        
        # Create DocType record
        doc = frappe.get_doc({
            "doctype": "Branch Category Report",
            "sol_id": sol_id,
            "branch": final_branch,
            "zone": final_zone,
            "region": final_region,
            "district": circle_office_name,
            "date": processed_date,
            "achievement": safe_str(achievement),
            "yearly_achievement": yearly_achievement,
            "branch_category": branch_category,
            "ytd_achi": safe_str(round(ytd_achi_pct, 2)),
            "total_flow_amount": safe_str(total_flow_amount),
            "total_tran_amt": safe_str(total_tran_amt),
            "opening_balance": safe_str(opening_balance),
            "closing_balance": safe_str(closing_balance),
            "opening_mab": safe_str(opening_mab),
            "closing_mab": safe_str(closing_mab),
            "inc_mab": safe_str(inc_mab)
        })
        
        doc.insert(ignore_permissions=True)
        saved_count += 1
        recalculate_subsequent_ytd(sol_id, processed_date)
        
    frappe.db.commit()
    return saved_count


@frappe.whitelist()
def get_current_month_sync_status():
    """
    Returns the sync status of all days of the current month.
    Future dates are marked as is_future = True.
    Excludes Sundays and future dates from the badge count.
    """
    from frappe.utils import getdate, today, add_days
    import datetime
    from dateutil.relativedelta import relativedelta
    import calendar

    today_date = getdate(today())
    start_of_month = today_date.replace(day=1)
    
    # Calculate last day of the current month
    _, last_day_num = calendar.monthrange(today_date.year, today_date.month)
    last_day_of_month = today_date.replace(day=last_day_num)
    
    # Sync limit (normally yesterday, but if it is the 1st of month, then today)
    limit_date = today_date - relativedelta(days=1)
    if limit_date < start_of_month:
        limit_date = today_date
        
    # Get all distinct dates in Branch Category Report for this month
    stored_rows = frappe.db.sql("""
        SELECT DISTINCT date 
        FROM `tabBranch Category Report`
        WHERE date BETWEEN %s AND %s
    """, (start_of_month, today_date), as_dict=True)
    
    stored_dates = {getdate(r.date) for r in stored_rows}
    
    dates_status = []
    synced_count = 0
    total_days = 0
    
    curr = start_of_month
    while curr <= last_day_of_month:
        is_sunday = curr.weekday() == 6
        is_future = curr > limit_date
        has_data = curr in stored_dates if not is_future else False
        
        if not is_future and not is_sunday:
            total_days += 1
            if has_data:
                synced_count += 1
                
        dates_status.append({
            "date": str(curr),
            "day_name": curr.strftime("%a"),
            "formatted_date": curr.strftime("%d %b"),
            "has_data": has_data,
            "is_sunday": is_sunday,
            "is_future": is_future
        })
        curr = add_days(curr, 1)
        
    dates_status.reverse()
    
    return {
        "dates_status": dates_status,
        "synced_count": synced_count,
        "total_days": total_days
    }




def daily_sync_cron():
    """
    Cron job triggered daily at 8:00 AM.
    Syncs the achievement data for yesterday if enabled in Drishti Settings.
    If yesterday was Sunday (Today is Monday), it skips execution.
    """
    from frappe.utils import getdate, today, add_days
    
    # 1. Check if sync is enabled in Drishti Settings
    sync_enabled = frappe.db.get_single_value("Drishti Settings", "branch_category_report_sync")
    if not sync_enabled:
        frappe.logger("scheduler").info("Daily Sync Cron: Sync is disabled in Drishti Settings. Skipping execution.")
        return
        
    today_date = getdate(today())
    yesterday = add_days(today_date, -1)
    
    frappe.logger("scheduler").info(f"Daily Sync Cron: Triggering sync for {yesterday} at 8:00 AM.")
    
    try:
        saved_count = generate_and_save_branch_category_report(yesterday)
        frappe.logger("scheduler").info(f"Daily Sync Cron: Successfully synced {saved_count} records for {yesterday}.")
        send_sync_status_email(yesterday, "Success", "Sync completed successfully.", saved_count)
    except Exception as e:
        error_msg = frappe.get_traceback() or str(e)
        frappe.logger("scheduler").error(f"Daily Sync Cron Error for {yesterday}: {e}")
        send_sync_status_email(yesterday, "Failed", error_msg)


def send_sync_status_email(sync_date, status, details_or_error, saved_count=0):
    """
    Sends sync status email to configured recipients.
    """
    recipients = ["talib.s@sahayogmultistate.com", "atul.n@sahayogmultistate.com"]
    subject = f"Branch Category Report Sync Status - {sync_date.strftime('%d-%m-%Y')}"
    
    if status == "Success":
        message = f"""
        <p>Dear Team,</p>
        <p>The daily automated sync for <b>Branch Category Report</b> has completed successfully.</p>
        <table border="1" cellpadding="6" style="border-collapse: collapse; border-color: #cbd5e1;">
            <tr style="background-color: #f8fafc;">
                <th>Parameter</th>
                <th>Value</th>
            </tr>
            <tr>
                <td><b>Sync Target Date</b></td>
                <td>{sync_date.strftime('%d-%m-%Y')}</td>
            </tr>
            <tr>
                <td><b>Status</b></td>
                <td style="color: green; font-weight: bold;">SUCCESS</td>
            </tr>
            <tr>
                <td><b>Records Saved</b></td>
                <td>{saved_count}</td>
            </tr>
            <tr>
                <td><b>Execution Time</b></td>
                <td>{frappe.utils.now_datetime().strftime('%d-%m-%Y %I:%M %p')}</td>
            </tr>
        </table>
        <br>
        <p>Regards,<br>Sahayog System Automation</p>
        """
    elif status == "Skipped":
        message = f"""
        <p>Dear Team,</p>
        <p>The daily automated sync for <b>Branch Category Report</b> was skipped.</p>
        <p><b>Reason:</b> {details_or_error}</p>
        <br>
        <p>Regards,<br>Sahayog System Automation</p>
        """
    else:
        message = f"""
        <p>Dear Team,</p>
        <p style="color: red; font-weight: bold;">WARNING: The daily automated sync for Branch Category Report has FAILED.</p>
        <table border="1" cellpadding="6" style="border-collapse: collapse; border-color: #cbd5e1;">
            <tr style="background-color: #f8fafc;">
                <th>Parameter</th>
                <th>Value</th>
            </tr>
            <tr>
                <td><b>Sync Target Date</b></td>
                <td>{sync_date.strftime('%d-%m-%Y')}</td>
            </tr>
            <tr>
                <td><b>Status</b></td>
                <td style="color: red; font-weight: bold;">FAILED</td>
            </tr>
            <tr>
                <td><b>Error Details</b></td>
                <td><pre style="color: red;">{details_or_error}</pre></td>
            </tr>
            <tr>
                <td><b>Execution Time</b></td>
                <td>{frappe.utils.now_datetime().strftime('%d-%m-%Y %I:%M %p')}</td>
            </tr>
        </table>
        <br>
        <p>Please check the scheduler logs or Finacle DB Credentials setting.</p>
        <br>
        <p>Regards,<br>Sahayog System Automation</p>
        """
        
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            delayed=False
        )
    except Exception as e:
        frappe.logger("scheduler").error(f"Daily Sync Email Error: Failed to send email to recipients: {e}")





def interactive_date_control():
    while True:
        input_date = input(
            "Enter date (DD-MM-YYYY) or 'q' to quit: "
        ).strip()

        if input_date.lower() in ["q", "quit", "exit"]:
            print("Exiting...")
            break

        try:
            dates = date_control(input_date)
            execute_achievement_query(dates)
        except Exception as e:
            print(f"Error: {e}")


import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_date = sys.argv[1]
        try:
            date_control(input_date)
        except Exception as e:
            print(f"Error: {e}")
    else:
        interactive_date_control()