# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from custom_report.db_connection import get_dr_connection
import psycopg2.extras

class BookPositionandAccountDetails(Document):
	pass

def execute_book_position_bulk_insert(records: list, chunk_size: int = 5000) -> None:
	"""
	Direct DB-to-DB bulk INSERT into tabBook Position and Account Details table without ORM overhead.
	Executes chunked raw SQL INSERT queries for maximum performance.
	"""
	if not records:
		return

	db_type = getattr(frappe.db, "db_type", "mariadb")
	row_placeholder = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

	for i in range(0, len(records), chunk_size):
		chunk = records[i : i + chunk_size]
		placeholders = ", ".join([row_placeholder] * len(chunk))
		flattened_params = [val for row in chunk for val in row]

		if db_type == "mariadb":
			sql = f"""
			INSERT INTO `tabBook Position and Account Details` (
				`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `idx`,
				`date`, `sol_id`, `scheme_code`, `scheme_description`, `account_opened`,
				`account_closed`, `opening_no_of_accounts`, `closing_no_of_accounts`,
				`opening_balance`, `closing_balance`, `group_name`, `group_subname`
			) VALUES {placeholders};
			"""
		else:
			sql = f"""
			INSERT INTO "tabBook Position and Account Details" (
				"name", "creation", "modified", "modified_by", "owner", "docstatus", "idx",
				"date", "sol_id", "scheme_code", "scheme_description", "account_opened",
				"account_closed", "opening_no_of_accounts", "closing_no_of_accounts",
				"opening_balance", "closing_balance", "group_name", "group_subname"
			) VALUES {placeholders};
			"""
		frappe.db.sql(sql, flattened_params)


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
WITH opening_bal AS (
    SELECT 
        g.sol_id,
        g.schm_code,
        SUM(e.tran_date_bal) AS opening_balance
    FROM tbaadm.eab e
    INNER JOIN tbaadm.gam g ON g.acid = e.acid
    INNER JOIN tbaadm.sst ss ON ss.sol_id = g.sol_id
    WHERE ss.set_id BETWEEN '1001' AND '1260'
      AND %(start_date)s::DATE - 1 BETWEEN e.eod_date AND e.end_eod_date
    GROUP BY g.sol_id, g.schm_code
),
closing_bal AS (
    SELECT 
        g.sol_id,
        g.schm_code,
        SUM(e.tran_date_bal) AS closing_balance
    FROM tbaadm.eab e
    INNER JOIN tbaadm.gam g ON g.acid = e.acid
    INNER JOIN tbaadm.sst ss ON ss.sol_id = g.sol_id
    WHERE ss.set_id BETWEEN '1001' AND '1260'
      AND %(end_date)s::DATE BETWEEN e.eod_date AND e.end_eod_date
    GROUP BY g.sol_id, g.schm_code
)
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
    COALESCE(ob.opening_balance, 0) AS Opening_Balance,
    COALESCE(cb.closing_balance, 0) AS Closing_Balance,
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
LEFT JOIN
    opening_bal ob ON ob.sol_id = gam.sol_id AND ob.schm_code = gam.schm_code
LEFT JOIN
    closing_bal cb ON cb.sol_id = gam.sol_id AND cb.schm_code = gam.schm_code
WHERE 
    ss.set_id BETWEEN '1001' AND '1260'   
GROUP BY 
    gam.sol_id, gam.schm_code, gsp.schm_desc, ob.opening_balance, cb.closing_balance
ORDER BY 
    gam.sol_id, gam.schm_code;
	"""

	conn = None
	try:
		import time
		
		max_retries = 5
		rows = []
		
		for attempt in range(max_retries):
			try:
				conn = get_dr_connection()
				with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
					try:
						cur.execute("SET statement_timeout = 0;")
					except Exception:
						pass
					cur.execute(query, {"start_date": start_date, "end_date": end_date})
					rows = cur.fetchall()
				break # Success, exit retry loop
			except Exception as e:
				err_str = str(e).lower()
				is_recovery_conflict = any(term in err_str for term in [
					"conflict with recovery", "canceling statement", "querycanceled",
					"serializationfailure", "55006", "40001"
				])
				if is_recovery_conflict and attempt < max_retries - 1:
					retry_delay = (attempt + 1) * 3
					frappe.log_error(f"DR DB Query Conflict (Attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...", "Book Position Sync Retry")
					if conn:
						try:
							conn.close()
						except Exception:
							pass
					time.sleep(retry_delay)
				else:
					raise # Re-raise if not a recovery conflict or out of retries
			
		# Delete existing records for this date
		frappe.db.delete("Book Position and Account Details", {"date": sync_date})

		from frappe.utils import now_datetime
		now_time = now_datetime()
		session_user = getattr(frappe.session, "user", "Administrator") if getattr(frappe, "session", None) else "Administrator"

		# Pre-fetch products map to populate group_name & group_subname
		products = frappe.get_all("Product", fields=["name", "group_name", "group_subname"])
		prod_map = {p.name: p for p in products}

		bulk_data = []
		for row in rows:
			name = frappe.generate_hash(length=16)
			schm_code = row['schm_code']
			prod_info = prod_map.get(schm_code, {})

			bulk_data.append((
				name,
				now_time,
				now_time,
				session_user,
				session_user,
				0,
				0,
				sync_date,
				row['sol_id'],
				schm_code,
				row['schm_desc'],
				row['account_opened'],
				row['account_closed'],
				row['opening_number_of_accts'],
				row['closing_number_of_accounts'],
				row['opening_balance'],
				row['closing_balance'],
				prod_info.get('group_name'),
				prod_info.get('group_subname')
			))

		execute_book_position_bulk_insert(bulk_data, chunk_size=5000)
		frappe.db.commit()
		return "Success"
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Book Position Sync Error")
		frappe.throw(f"An error occurred during sync: {str(e)}")
	finally:
		if conn:
			conn.close()
