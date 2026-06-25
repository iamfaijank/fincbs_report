import frappe
import json
from dateutil.relativedelta import relativedelta
from custom_report.db_connection import get_dr_connection
from datetime import datetime



def date_control(input_date):
    current_date = datetime.strptime(input_date, "%d-%m-%Y").date()

    if current_date >= datetime.today().date():
        current_date = datetime.today().date() - relativedelta(days=1)
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
ORDER BY achivment DESC LIMIT 5;
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
        
        # Format as JSON for the Top 5 records
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
            
        print("Showing Top 5 records by achievement in JSON format:\n")
        print(json.dumps(json_data, indent=4))
        
        return result
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


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