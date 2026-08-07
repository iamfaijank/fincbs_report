# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from custom_report.db_connection import get_dr_connection
import psycopg2.extras

class BookPositionandAccountDetails(Document):
	pass

def send_email_notification(status, sync_date, details_or_error=""):
	recipients = ["talib.s@sahayogmultistate.com", "atul.n@sahayogmultistate.com"]
	subject = f"Book Position Sync Status - {sync_date}"
	
	if status == "Success":
		message = f"""
		<p>Dear Team,</p>
		<p>The daily automated sync for <b>Book Position and Account Details</b> has completed successfully.</p>
		<table border="1" cellpadding="6" style="border-collapse: collapse; border-color: #cbd5e1;">
			<tr style="background-color: #f8fafc;">
				<th>Parameter</th>
				<th>Value</th>
			</tr>
			<tr>
				<td><b>Sync Target Date</b></td>
				<td>{sync_date}</td>
			</tr>
			<tr>
				<td><b>Status</b></td>
				<td style="color: green; font-weight: bold;">SUCCESS</td>
			</tr>
			<tr>
				<td><b>Records Saved</b></td>
				<td>{details_or_error}</td>
			</tr>
			<tr>
				<td><b>Execution Time</b></td>
				<td>{frappe.utils.now_datetime().strftime('%d-%m-%Y %I:%M %p')}</td>
			</tr>
		</table>
		<br>
		<p>Regards,<br>Sahayog System Automation</p>
		"""
	else:
		message = f"""
		<p>Dear Team,</p>
		<p style="color: red; font-weight: bold;">WARNING: The daily automated sync for Book Position has FAILED.</p>
		<table border="1" cellpadding="6" style="border-collapse: collapse; border-color: #cbd5e1;">
			<tr style="background-color: #f8fafc;">
				<th>Parameter</th>
				<th>Value</th>
			</tr>
			<tr>
				<td><b>Sync Target Date</b></td>
				<td>{sync_date}</td>
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
		frappe.log_error(f"Book Position Daily Sync Email Error: {e}", "Email Error")

def daily_sync_book_position():
	sync_enabled = frappe.db.get_single_value("Drishti Settings", "auto_sync")
	if not sync_enabled:
		frappe.logger("scheduler").info("Daily Book Position Sync: Sync is disabled in Drishti Settings. Skipping execution.")
		return

	# Sync data for yesterday (today - 1 day)
	from frappe.utils import add_days, today
	yesterday = add_days(today(), -1)
	frappe.log_error("Starting Daily Book Position Sync for: " + yesterday, "Book Position Sync")
	try:
		sync_data(yesterday)
		count = frappe.db.count("Book Position and Account Details", {"date": yesterday})
		frappe.log_error("Successfully synced Book Position for: " + yesterday, "Book Position Sync")
		send_email_notification("Success", yesterday, str(count))
	except Exception as e:
		frappe.log_error("Failed to sync Book Position: " + str(e), "Book Position Sync Error")
		send_email_notification("Failed", yesterday, str(e))

@frappe.whitelist()
def sync_data(sync_date):
	from frappe.utils import get_first_day, getdate
	
	# The user wants to sync MTD up to the given date (T-1)
	end_date = sync_date
	start_date = get_first_day(getdate(sync_date))

	query = """
SELECT 
    gam.sol_id,
    gam.schm_code, 
    gsp.schm_desc,  
    COUNT(DISTINCT CASE 
        WHEN gam.acct_opn_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
        AND gam.entity_cre_flg = 'Y'
        AND gam.del_flg = 'N'
        AND gam.acct_cls_flg = 'N'
        THEN gam.foracid 
    END) AS Account_Opened,
    COUNT(DISTINCT CASE 
        WHEN gam.acct_cls_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
        AND gam.entity_cre_flg = 'Y' 
        AND gam.del_flg = 'N'
        AND gam.acct_cls_flg = 'N'
        THEN gam.foracid 
    END) AS Account_Closed,
    COUNT(DISTINCT CASE 
        WHEN gam.acct_opn_date < %(start_date)s::DATE
        AND gam.entity_cre_flg = 'Y' 
         AND gam.del_flg = 'N'
        AND gam.acct_cls_flg = 'N'
        THEN gam.foracid 
    END) AS Opening_Number_of_Accts,
    COUNT(DISTINCT CASE 
    WHEN gam.acct_opn_date <= %(end_date)s::DATE
    AND gam.entity_cre_flg = 'Y'
    AND gam.del_flg = 'N'
    AND gam.acct_cls_flg = 'N'
    THEN gam.foracid 
    END) AS Closing_Number_of_Accounts,
    COALESCE((
        SELECT SUM(eab_inner.tran_date_bal)  
        FROM tbaadm.eab eab_inner
        WHERE eab_inner.acid IN (
            SELECT gam_inner.acid 
            FROM tbaadm.gam gam_inner 
            WHERE gam_inner.schm_code = gam.schm_code
              AND gam_inner.sol_id = gam.sol_id
        )  
        AND %(start_date)s::DATE - 1 BETWEEN eab_inner.eod_date AND eab_inner.end_eod_date
    ), 0) AS Opening_Balance,
    COALESCE((
        SELECT SUM(eab_inner.tran_date_bal)
        FROM tbaadm.eab eab_inner
        WHERE eab_inner.acid IN (
            SELECT gam_inner.acid 
            FROM tbaadm.gam gam_inner 
            WHERE gam_inner.schm_code = gam.schm_code
              AND gam_inner.sol_id = gam.sol_id 
        )  
        AND %(end_date)s::DATE BETWEEN eab_inner.eod_date AND eab_inner.end_eod_date
    ), 0) AS Closing_Balance,
    COALESCE(SUM(CASE 
        WHEN htd.part_tran_type = 'D'
        AND htd.tran_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
        THEN htd.tran_amt ELSE 0 
    END), 0) AS Total_Debit,
    COALESCE(SUM(CASE 
        WHEN htd.part_tran_type = 'C'
        AND htd.tran_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
        THEN htd.tran_amt ELSE 0 
    END), 0) AS Total_Credit 
FROM 
    tbaadm.gam gam  
LEFT JOIN 
    tbaadm.htd htd 
    ON gam.acid = htd.acid  
    AND htd.pstd_flg = 'Y' 
    AND htd.del_flg = 'N' 
    AND htd.tran_rmks != 'TACBSH' 
    AND htd.part_tran_type NOT IN ('IC','IP') 
    AND htd.tran_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
LEFT JOIN 
    tbaadm.gsp gsp ON gam.schm_code = gsp.schm_code 
INNER JOIN 
    tbaadm.sst ss ON ss.sol_id = gam.sol_id   
WHERE 
    ss.set_id BETWEEN '1001' AND '1260'   
GROUP BY 
    gam.sol_id, gam.schm_code, gsp.schm_desc
ORDER BY 
    gam.sol_id, gam.schm_code;
	"""

	conn = None
	try:
		import time
		
		max_retries = 3
		retry_delay = 5
		rows = []
		
		for attempt in range(max_retries):
			try:
				conn = get_dr_connection()
				with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
					cur.execute(query, {"start_date": start_date, "end_date": end_date})
					rows = cur.fetchall()
				break # Success, exit retry loop
			except Exception as e:
				if "conflict with recovery" in str(e).lower() and attempt < max_retries - 1:
					frappe.log_error(f"DR DB Query Conflict (Attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...", "Book Position Sync Retry")
					if conn:
						conn.close()
					time.sleep(retry_delay)
				else:
					raise # Re-raise if not a recovery conflict or out of retries
			
		# Delete existing records for this date
		frappe.db.delete("Book Position and Account Details", {"date": sync_date})
		
		for row in rows:
			doc = frappe.new_doc("Book Position and Account Details")
			doc.date = sync_date
			doc.sol_id = row['sol_id']
			doc.scheme_code = row['schm_code']
			doc.scheme_description = row['schm_desc']
			doc.account_opened = row['account_opened']
			doc.account_closed = row['account_closed']
			doc.opening_no_of_accounts = row['opening_number_of_accts']
			doc.closing_no_of_accounts = row['closing_number_of_accounts']
			doc.opening_balance = row['opening_balance']
			doc.closing_balance = row['closing_balance']
			doc.insert(ignore_permissions=True)
			
		frappe.db.commit()
		return "Success"
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Book Position Sync Error")
		frappe.throw(f"An error occurred during sync: {str(e)}")
	finally:
		if conn:
			conn.close()
