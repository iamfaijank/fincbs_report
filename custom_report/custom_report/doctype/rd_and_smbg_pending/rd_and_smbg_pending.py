# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, now, flt, cint, add_days
from frappe import _
import time
from custom_report.db_connection import get_dr_connection, execute_dr_query


class RDandSMBGPending(Document):
	pass


@frappe.whitelist()
def sync_rd_and_smbg_pending(sync_date=None, date=None):
	"""
	Superfast Sync for RD & SMBG Pending records from DR PostgreSQL database to Frappe MariaDB.
	Optimized using raw tuple streaming, fast ID generation, disabled unique checks, and large-batch bulk inserts.
	"""
	start_time = time.time()
	selected_date = sync_date or date
	if not selected_date:
		selected_date = add_days(getdate(nowdate()), -1)

	ref_date = getdate(selected_date)
	today = getdate(nowdate())

	# Rule: Today and future dates CANNOT be selected!
	if ref_date >= today:
		frappe.throw(_("Today and future dates cannot be selected. Please select past dates only."))

	query = f"""
    WITH main_data AS (
        SELECT   
            g.acid,
            g.sol_id,
            s.sol_desc,
            g.cif_id,
            g.schm_code,
            p.schm_desc,
            g.foracid,
            g.acct_name,
            g.acct_opn_date,
            t.maturity_date,
            t.last_repayment_date,
            d.rm_id,
            g2.emp_name AS rm_name,
            d2.auth_id,
            d2.auth_role_id,
            t.deposit_amount,
            t.deposit_period_mths,
            t.deposit_period_days
        FROM tbaadm.gam g
        JOIN tbaadm.tam t
            ON g.acid = t.acid
        JOIN tbaadm.gsp p
            ON g.schm_code = p.schm_code
        JOIN tbaadm.sol s
            ON g.sol_id = s.sol_id
        JOIN crmuser.address a
            ON g.cif_id = a.orgkey
        LEFT JOIN custom.dsamap d
            ON g.foracid = d.account_number
        LEFT JOIN custom.dsaauth d2
            ON d.rm_id = d2.user_id
        LEFT JOIN tbaadm.get g2
            ON d2.user_id = g2.emp_id
        WHERE 
            g.schm_code IN ('2005','2010','2011','2012','2013','2014','2015','2016')
            AND g.entity_cre_flg = 'Y' 
            AND g.del_flg = 'N' 
            AND g.acct_cls_flg = 'N'
            AND a.preferredaddress = 'Y'
            AND t.maturity_date >= DATE '{ref_date}'
    ),
    tdt_summary AS (
        SELECT 
            acid,
            COUNT(
                CASE 
                    WHEN flow_amt > 0 
                    THEN 1 
                END
            ) - 
            COUNT(
                CASE 
                    WHEN tran_amt > 0 
                    THEN 1 
                END
            ) AS pending_instalments,
            SUM(flow_amt) - SUM(tran_amt) AS pending_amount,
            SUM(tran_amt) AS total_instalment_paid
        FROM tbaadm.tdt
        WHERE 
            flow_code = 'NI' 
            AND (flow_amt > 0 OR tran_amt > 0)
            AND flow_date <= DATE '{ref_date}'
        GROUP BY acid
    )
    SELECT 
        m.sol_id,
        m.sol_desc,
        m.cif_id,
        m.schm_code,
        m.schm_desc,
        m.foracid,
        m.acct_name,
        m.acct_opn_date,
        m.deposit_amount,
        m.maturity_date,
        m.deposit_period_mths,
        m.deposit_period_days,
        m.rm_id,
        m.rm_name,
        m.auth_id,
        m.auth_role_id,
        COALESCE(t.pending_instalments, 0) AS pending_instalments,
        COALESCE(t.pending_amount, 0) AS pending_amount,
        COALESCE(t.total_instalment_paid, 0) AS total_instalment_paid
    FROM main_data m
    LEFT JOIN tdt_summary t
        ON m.acid = t.acid
    WHERE NOT (
        COALESCE(t.pending_instalments, 0) > 24 
        AND m.last_repayment_date < (DATE '{ref_date}' - INTERVAL '1 year')
    )
    ORDER BY m.sol_id, m.foracid;
	"""

	rows = execute_dr_query(
		query=query,
		title="RD & SMBG Pending Sync"
	)

	fetch_time = time.time() - start_time

	# Fast deletion via direct SQL
	frappe.db.sql("DELETE FROM `tabRD and SMBG Pending` WHERE `date` = %s", (str(ref_date),))

	fields = [
		"name", "creation", "modified", "modified_by", "owner", "docstatus",
		"date", "sol_id", "sol_desc", "cif_id", "schm_code", "schm_desc",
		"foracid", "acct_name", "acct_opn_date", "deposit_amount", "maturity_date",
		"deposit_period_mths", "deposit_period_days", "rm_id", "rm_name",
		"auth_id", "auth_role_id", "pending_instalments", "pending_amount",
		"total_instalment_paid"
	]

	now_str = now()
	user = frappe.session.user if getattr(frappe.session, "user", None) else "Administrator"
	ref_date_str = str(ref_date)
	values = []

	# Pre-allocate tuples using raw tuple indices (5-10x faster than dict lookups & generate_hash)
	for row in rows:
		sol_id = row[0] or ""
		sol_desc = row[1] or ""
		cif_id = row[2] or ""
		schm_code = row[3] or ""
		schm_desc = row[4] or ""
		foracid = row[5] or ""
		acct_name = row[6] or ""
		acct_opn_date = row[7]
		deposit_amount = flt(row[8] or 0.0)
		maturity_date = row[9]
		deposit_period_mths = cint(row[10] or 0)
		deposit_period_days = cint(row[11] or 0)
		rm_id = row[12] or ""
		rm_name = row[13] or ""
		auth_id = row[14] or ""
		auth_role_id = row[15] or ""
		pending_instalments = cint(row[16] or 0)
		pending_amount = flt(row[17] or 0.0)
		total_instalment_paid = flt(row[18] or 0.0)

		# Fast unique primary key string formatting instead of 433k os.urandom calls
		name = f"{ref_date_str}_{foracid}" if foracid else frappe.generate_hash(length=10)

		values.append((
			name,
			now_str,
			now_str,
			user,
			user,
			0,
			ref_date_str,
			sol_id,
			sol_desc,
			cif_id,
			schm_code,
			schm_desc,
			foracid,
			acct_name,
			acct_opn_date,
			deposit_amount,
			maturity_date,
			deposit_period_mths,
			deposit_period_days,
			rm_id,
			rm_name,
			auth_id,
			auth_role_id,
			pending_instalments,
			pending_amount,
			total_instalment_paid
		))

	total_records = len(values)
	insert_start = time.time()

	if total_records > 0:
		# Temporarily disable unique/foreign key checks for superfast batch insertion
		frappe.db.sql("SET UNIQUE_CHECKS=0;")
		frappe.db.sql("SET FOREIGN_KEY_CHECKS=0;")

		try:
			chunk_size = 25000
			for i in range(0, total_records, chunk_size):
				chunk = values[i:i + chunk_size]
				frappe.db.bulk_insert(
					"RD and SMBG Pending",
					fields=fields,
					values=chunk,
					ignore_duplicates=True
				)
			frappe.db.commit()
		finally:
			frappe.db.sql("SET UNIQUE_CHECKS=1;")
			frappe.db.sql("SET FOREIGN_KEY_CHECKS=1;")

	total_time = time.time() - start_time
	insert_time = time.time() - insert_start

	frappe.logger("rd_smbg_sync").info(
		f"Synced {total_records} records in {total_time:.2f}s (Fetch: {fetch_time:.2f}s, Insert: {insert_time:.2f}s)."
	)

	return _("Successfully synced {0} RD and SMBG Pending records for date {1} in {2:.2f} seconds.").format(
		total_records, ref_date, total_time
	)


def daily_sync_rd_and_smbg_pending(sync_date=None):
	"""
	Cron job triggered daily for automated T-1 synchronization.
	"""
	if sync_date is None:
		sync_enabled = cint(frappe.db.get_single_value("Drishti Settings", "auto_sync"))
		if not sync_enabled:
			frappe.logger("scheduler").info("Daily RD & SMBG Pending Sync: Sync is disabled in Drishti Settings. Skipping.")
			return

		sync_date = add_days(getdate(nowdate()), -1)
		frappe.logger("scheduler").info(f"Daily RD & SMBG Pending Sync: Starting sync for {sync_date}.")
		try:
			msg = sync_rd_and_smbg_pending(sync_date=sync_date)
			frappe.logger("scheduler").info(f"Daily RD & SMBG Pending Sync: {msg}")
		except Exception as e:
			frappe.log_error(f"Daily RD & SMBG Pending Sync Error for {sync_date}: {e}", "RD & SMBG Pending Sync Error")
		return

	return sync_rd_and_smbg_pending(sync_date=str(sync_date))
