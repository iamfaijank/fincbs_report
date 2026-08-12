# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, now, flt, cint
from frappe import _
import psycopg2.extras
from custom_report.db_connection import get_dr_connection


class MaturityTracker(Document):
	pass


@frappe.whitelist()
def sync_maturity_tracker(from_date=None, to_date=None):
	if not from_date or not to_date:
		frappe.throw(_("From Date and To Date are mandatory."))

	dt_from = getdate(from_date)
	dt_to = getdate(to_date)
	today = getdate(nowdate())

	# Rule: Today and future dates CANNOT be selected!
	if dt_from >= today or dt_to >= today:
		frappe.throw(_("Today and future dates cannot be selected. Please select past dates only."))

	if dt_from > dt_to:
		frappe.throw(_("From Date cannot be greater than To Date."))

	query = """
	WITH debit_cte AS (
	    SELECT
	        g.cif_id,
	        g.acct_name,
	        STRING_AGG(DISTINCT g.foracid, ', ') AS account_numbers,
	        STRING_AGG(DISTINCT g.sol_id, ', ') AS sol_ids,
	        STRING_AGG(DISTINCT s.division_name, ', ') AS division_name,
	        STRING_AGG(DISTINCT s.region_name, ', ') AS region_name,
	        STRING_AGG(DISTINCT s.circle_office_name, ', ') AS circle_office_name,
	        COUNT(DISTINCT g.acid) AS account_count,
	        SUM(h.tran_amt) AS total_debit_amount,
	        MAX(h.tran_date) AS last_debit_transaction_date
	    FROM tbaadm.gam g
	    JOIN tbaadm.htd h
	        ON g.acid = h.acid
	    LEFT JOIN tbaadm.sol s
	        ON g.sol_id = s.sol_id
	    WHERE g.schm_code IN (
	        '2001','2002','2003','2018','2019',
	        '2020','2021','2023',
	        '2101','2102','2103','2104',
	        '2105','2106',
	        '2201','2202','2203'
	    )
	      AND g.entity_cre_flg = 'Y' AND g.del_flg = 'N'
	      AND h.part_tran_type = 'D' AND h.pstd_flg = 'Y'
	      AND h.tran_date BETWEEN %s AND %s
	      AND h.tran_particular NOT ILIKE '%%xfr%%'
	    GROUP BY g.cif_id, g.acct_name
	),
	deposit_cte AS (
	    SELECT
	        g.cif_id,
	        STRING_AGG(DISTINCT g.foracid, ', ') AS deposit_account_numbers,
	        COUNT(DISTINCT g.acid) AS deposit_account_count,
	        SUM(t.deposit_amount) AS total_deposit_amount
	    FROM tbaadm.gam g
	    JOIN tbaadm.tam t
	        ON g.acid = t.acid
	    WHERE g.acct_opn_date BETWEEN %s AND %s
	      AND g.schm_code IN (
	        '2001','2002','2003','2018','2019',
	        '2020','2021','2023',
	        '2101','2102','2103','2104',
	        '2105','2106',
	        '2201','2202','2203'
	    )
	      AND g.entity_cre_flg = 'Y' AND g.del_flg = 'N'
	      AND g.cif_id IN (SELECT cif_id FROM debit_cte)
	    GROUP BY g.cif_id
	)
	SELECT
	    d.cif_id,
	    d.acct_name,
	    d.account_numbers,
	    d.sol_ids,
	    d.account_count,
	    d.total_debit_amount AS maturity_paid,
	    d.last_debit_transaction_date,
	    COALESCE(dep.total_deposit_amount, 0) AS total_deposit_amount,
	    CASE WHEN dep.cif_id IS NOT NULL THEN 'Yes' ELSE 'No' END AS deposit_done_flag,
	    CASE
	        WHEN COALESCE(dep.total_deposit_amount, 0) > d.total_debit_amount
	            THEN d.total_debit_amount
	        ELSE COALESCE(dep.total_deposit_amount, 0)
	    END AS renewal_amount,
	    d.division_name,
	    d.region_name,
	    d.circle_office_name AS zone
	FROM debit_cte d
	LEFT JOIN deposit_cte dep
	    ON d.cif_id = dep.cif_id
	ORDER BY d.cif_id;
	"""

	conn = get_dr_connection()
	rows = []
	try:
		with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
			cursor.execute(query, (str(dt_from), str(dt_to), str(dt_from), str(dt_to)))
			rows = cursor.fetchall()
	finally:
		conn.close()

	# Clear existing data for this date range to prevent duplicates
	frappe.db.delete("Maturity Tracker", {"from_date": str(dt_from), "to_date": str(dt_to)})

	fields = [
		"name", "creation", "modified", "modified_by", "owner", "docstatus",
		"cif_id", "acct_name", "sol_ids", "account_numbers", "account_count",
		"maturity_paid", "last_debit_transaction_date", "total_deposit_amount",
		"deposit_done_flag", "renewal_amount", "division_name", "region_name",
		"zone", "from_date", "to_date"
	]

	now_str = now()
	user = frappe.session.user if getattr(frappe.session, "user", None) else "Administrator"
	values = []

	for row in rows:
		values.append((
			frappe.generate_hash(length=10),
			now_str,
			now_str,
			user,
			user,
			0,
			row.get("cif_id") or "",
			row.get("acct_name") or "",
			row.get("sol_ids") or "",
			row.get("account_numbers") or "",
			cint(row.get("account_count") or 0),
			flt(row.get("maturity_paid") or 0.0),
			row.get("last_debit_transaction_date"),
			flt(row.get("total_deposit_amount") or 0.0),
			row.get("deposit_done_flag") or "No",
			flt(row.get("renewal_amount") or 0.0),
			row.get("division_name") or "",
			row.get("region_name") or "",
			row.get("zone") or "",
			str(dt_from),
			str(dt_to)
		))

	total_records = len(values)
	if total_records > 0:
		chunk_size = 5000
		for i in range(0, total_records, chunk_size):
			chunk = values[i:i + chunk_size]
			frappe.db.bulk_insert(
				"Maturity Tracker",
				fields=fields,
				values=chunk,
				ignore_duplicates=True
			)
		frappe.db.commit()

	return f"Successfully synced {total_records} Maturity Tracker records for date range {dt_from} to {dt_to}."
