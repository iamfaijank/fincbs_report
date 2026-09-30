# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import datetime
from decimal import Decimal

import frappe
import psycopg2.extras
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, get_first_day, get_table_name, getdate, now

from custom_report.db_connection import execute_dr_query

DOCTYPE = "Staff Productivity"

# Per report type configuration:
#   query          -> DR (PostgreSQL) SQL, executed with the `sync_date` param
#   mapping        -> SQL column -> DocType fieldname
#   mirror_fields  -> DocType fieldname that reuses the value of an SQL column
#   derived_fields -> DocType Check fieldname derived from an SQL column
#   date_fields    -> mapped fields that must hold a plain `date`, not datetime
# Only the report types present here can be synced, the rest raise a clear error.
REPORT_CONFIG = {
	"BDE & BDO": {
		"title": "BDE and BDO Productivity",
		"query": """
			SELECT
				g.cif_id          AS cif_id,
				g.foracid         AS foracid,
				g.acct_name       AS acct_name,
				g.acct_opn_date   AS acct_opn_date,
				g.acct_cls_date   AS acct_cls_date,
				CASE
					WHEN g.acct_cls_date IS NULL THEN 'ACTIVE'
					ELSE 'CLOSED'
				END               AS account_status,
				g.sol_id          AS sol_id,
				s.sol_desc        AS sol_desc,
				g.schm_code       AS scheme_code,
				g1.schm_desc      AS schm_desc,
				t.deposit_amount  AS deposit_amount,
				g.clr_bal_amt     AS clr_bal_amt,
				d.rm_id           AS agent_id,
				g2.emp_name       AS agent_name,
				d2.auth_id        AS auth_id,
				d2.auth_role_id   AS auth_name,
				d2.operacc        AS operacc,
				g_operacc.foracid AS account_number
			FROM tbaadm.gam g
			JOIN tbaadm.sol s
				ON g.sol_id = s.sol_id
			JOIN tbaadm.gsp g1
				ON g.schm_code = g1.schm_code
			LEFT JOIN custom.dsamap d
				ON g.foracid = d.account_number
			LEFT JOIN custom.dsaauth d2
				ON d.rm_id = d2.user_id
			LEFT JOIN tbaadm.get g2
				ON d2.user_id = g2.emp_id
			LEFT JOIN tbaadm.gam g_operacc
				ON d2.operacc = g_operacc.foracid
			LEFT JOIN tbaadm.tam t
				ON g.acid = t.acid
			WHERE
				(
					g.schm_type = 'TDA'
					OR g.schm_code IN ('1002', '1011', '1102', '1103', '1104')
				)
				AND g.entity_cre_flg = 'Y'
				AND g.del_flg = 'N'
				AND g.acct_opn_date::DATE BETWEEN %(start_date)s::DATE AND %(sync_date)s::DATE
			ORDER BY g.foracid, g.cif_id, g.sol_id, g.schm_code
		""",
		"mapping": {
			"cif_id": "cif_id",
			"foracid": "foracid",
			"acct_name": "account_name",
			"acct_opn_date": "account_open_date",
			"acct_cls_date": "account_close_date",
			"account_status": "account_status",
			"sol_id": "sol_id",
			"sol_desc": "sol_desc",
			"scheme_code": "scheme_code",
			"schm_desc": "schm_desc",
			"deposit_amount": "deposit_amount",
			"clr_bal_amt": "clr_bal_amt",
			"agent_id": "agent_id",
			"agent_name": "agent_name",
			"auth_id": "auth_id",
			"auth_name": "auth_name",
			"operacc": "operacc",
			"account_number": "account_number",
		},
		# `customer_name` carries the same `g.acct_name` value as `account_name`.
		"mirror_fields": {"customer_name": "acct_name"},
		# account_close_flag = 1 when the account has a closing date, else 0.
		"derived_fields": {"account_close_flag": "acct_cls_date"},
		"date_fields": ["account_open_date", "account_close_date"],
	},
	"RD": {
		"title": "RD Productivity",
		"query": """
			WITH account_data AS (
				SELECT
					d.rm_id,
					g2.emp_name AS rm_name,
					d2.auth_id,
					d2.auth_role_id,
					d2.operacc,
					g.cif_id,
					g.acct_opn_date,
					g.acct_cls_date,
					a2.relationshipopeningdate AS CIF_ID_Opening_Date,
					g.foracid,
					g.sol_id,
					sol.sol_desc,
					g.schm_code AS scheme_code,
					gsp.schm_desc
				FROM custom.dsamap AS d
				INNER JOIN tbaadm.gam AS g
					ON g.foracid = d.account_number
					AND g.schm_code BETWEEN '2010' AND '2016'
				LEFT JOIN crmuser.accounts AS a2
					ON g.cif_id = a2.orgkey
				LEFT JOIN tbaadm.sol AS sol
					ON g.sol_id = sol.sol_id
				LEFT JOIN tbaadm.gsp AS gsp
					ON g.schm_code = gsp.schm_code
				LEFT JOIN custom.dsaauth AS d2
					ON d.rm_id = d2.user_id
				LEFT JOIN tbaadm.get AS g2
					ON d2.user_id = g2.emp_id
			),
			flow_data AS (
				SELECT
					d.rm_id,
					g.foracid,
					g.schm_code,
					SUM(tdt.flow_amt) AS total_flow_amount
				FROM custom.dsamap AS d
				INNER JOIN tbaadm.gam AS g
					ON g.foracid = d.account_number
					AND g.schm_code BETWEEN '2010' AND '2016'
				INNER JOIN tbaadm.tdt AS tdt
					ON tdt.acid = g.acid
					AND tdt.flow_code = 'NI'
				WHERE tdt.flow_date BETWEEN %(start_date)s AND %(sync_date)s
				GROUP BY
					d.rm_id,
					g.foracid,
					g.schm_code
				HAVING SUM(tdt.flow_amt) > 0
			),
			tran_data AS (
				SELECT
					d.rm_id,
					g.foracid,
					g.schm_code,
					SUM(dtt.tran_amt) AS total_tran_amt
				FROM custom.dsamap AS d
				INNER JOIN tbaadm.gam AS g
					ON g.foracid = d.account_number
					AND g.schm_code BETWEEN '2010' AND '2016'
				INNER JOIN tbaadm.dtt AS dtt
					ON dtt.acid = g.acid
					AND dtt.flow_code = 'NI'
				WHERE dtt.value_date BETWEEN %(start_date)s AND %(sync_date)s
				GROUP BY
					d.rm_id,
					g.foracid,
					g.schm_code
				HAVING SUM(dtt.tran_amt) > 0
			),
			reference_data AS (
				SELECT
					ed.referencenumber,
					da.user_id AS rm_id
				FROM crmuser.entitydocument AS ed
				INNER JOIN tbaadm.gam AS g
					ON ed.orgkey = g.cif_id
				INNER JOIN custom.dsaauth AS da
					ON g.foracid = da.operacc
				WHERE ed.doccode = 'PAN'
			)
			SELECT
				ad.rm_id,
				ad.rm_name,
				ad.auth_id,
				ad.auth_role_id,
				ad.operacc,
				ad.cif_id,
				ad.acct_opn_date,
				ad.acct_cls_date,
				ad.CIF_ID_Opening_Date,
				ad.foracid,
				COALESCE(fd.total_flow_amount, 0) AS total_flow_amount,
				COALESCE(td.total_tran_amt, 0) AS total_tran_amt,
				CASE
					WHEN ad.acct_cls_date IS NOT NULL
					     AND ad.acct_cls_date < %(start_date)s
					THEN 0
					ELSE COALESCE(fd.total_flow_amount, 0)
				END AS demand,
				ROUND(
					CASE
						WHEN LEAST(
							COALESCE(fd.total_flow_amount, 0),
							COALESCE(td.total_tran_amt, 0)
						) <= 100000
						THEN 0.035 * LEAST(
							COALESCE(fd.total_flow_amount, 0),
							COALESCE(td.total_tran_amt, 0)
						)

						WHEN LEAST(
							COALESCE(fd.total_flow_amount, 0),
							COALESCE(td.total_tran_amt, 0)
						) > 100000
						AND LEAST(
							COALESCE(fd.total_flow_amount, 0),
							COALESCE(td.total_tran_amt, 0)
						) <= 200000
						THEN 0.04 * LEAST(
							COALESCE(fd.total_flow_amount, 0),
							COALESCE(td.total_tran_amt, 0)
						)

						ELSE 0.05 * LEAST(
							COALESCE(fd.total_flow_amount, 0),
							COALESCE(td.total_tran_amt, 0)
						)
					END
				) AS commission,
				COALESCE(rd.referencenumber, 'N/A') AS referencenumber,
				ad.scheme_code,
				ad.schm_desc,
				ad.sol_id,
				ad.sol_desc
			FROM account_data AS ad
			LEFT JOIN flow_data AS fd
				ON ad.rm_id = fd.rm_id
				AND ad.foracid = fd.foracid
				AND ad.scheme_code = fd.schm_code
			LEFT JOIN tran_data AS td
				ON ad.rm_id = td.rm_id
				AND ad.foracid = td.foracid
				AND ad.scheme_code = td.schm_code
			LEFT JOIN reference_data AS rd
				ON ad.rm_id = rd.rm_id
				AND (fd.total_flow_amount > 0 OR td.total_tran_amt > 0)
			ORDER BY
				ad.foracid,
				ad.rm_id,
				ad.scheme_code
		""",
		"mapping": {
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"auth_id": "auth_id",
			"auth_role_id": "auth_role_id",
			"operacc": "operacc",
			"cif_id": "cif_id",
			"acct_opn_date": "account_open_date",
			"acct_cls_date": "account_close_date",
			# PostgreSQL folds the unquoted `CIF_ID_Opening_Date` alias to lowercase.
			"cif_id_opening_date": "cif_opening_date",
			"foracid": "foracid",
			"total_flow_amount": "total_flow_amount",
			# total_tran_amt is the Collection, demand is the Demand.
			"total_tran_amt": "total_tran_amt",
			"demand": "demand",
			"commission": "commission",
			"referencenumber": "referencenumber",
			"scheme_code": "scheme_code",
			"schm_desc": "schm_desc",
			"sol_id": "sol_id",
			"sol_desc": "sol_desc",
		},
		"date_fields": ["account_open_date", "account_close_date", "cif_opening_date"],
	},
	"SMBG": {
		"title": "SMBG Productivity",
		"query": """
			WITH account_data AS (
				SELECT
					d2.auth_id,
					d2.auth_role_id,
					d.rm_id,
					g2.emp_name AS rm_name,
					g.cif_id,
					g.acct_opn_date,
					g.acct_cls_date,
					a2.relationshipopeningdate AS cif_id_opening_date,
					d2.operacc,
					g.foracid,
					g.sol_id,
					sol.sol_desc,
					g.schm_code
				FROM custom.dsamap AS d
				LEFT JOIN tbaadm.gam AS g
					ON g.foracid = d.account_number
					AND g.schm_code BETWEEN '2005' AND '2006'
				LEFT JOIN crmuser.accounts AS a2
					ON g.cif_id = a2.orgkey
				LEFT JOIN custom.dsaauth AS d2
					ON UPPER(d.rm_id) = UPPER(d2.user_id)
				LEFT JOIN tbaadm.get AS g2
					ON UPPER(d2.user_id) = UPPER(g2.emp_id)
				LEFT JOIN tbaadm.sol AS sol
					ON g.sol_id = sol.sol_id
				WHERE g.foracid IS NOT NULL
			),
			flow_data AS (
				SELECT
					g.foracid,
					SUM(tdt.flow_amt) AS total_flow_amount
				FROM tbaadm.gam AS g
				JOIN tbaadm.tdt AS tdt
					ON tdt.acid = g.acid
					AND tdt.flow_code = 'NI'
					AND tdt.flow_date BETWEEN %(start_date)s AND %(sync_date)s
				WHERE g.schm_code BETWEEN '2005' AND '2006'
				GROUP BY g.foracid
			),
			tran_data AS (
				SELECT
					g.foracid,
					SUM(dtt.tran_amt) AS total_tran_amt
				FROM tbaadm.gam AS g
				JOIN tbaadm.dtt AS dtt
					ON dtt.acid = g.acid
					AND dtt.flow_code = 'NI'
					AND dtt.value_date BETWEEN %(start_date)s AND %(sync_date)s
				WHERE g.schm_code BETWEEN '2005' AND '2006'
				GROUP BY g.foracid
			),
			reference_data AS (
				SELECT
					ed.referencenumber AS pan_number,
					da.user_id AS rm_id
				FROM crmuser.entitydocument AS ed
				JOIN tbaadm.gam AS g
					ON ed.orgkey = g.cif_id
				JOIN custom.dsaauth AS da
					ON g.foracid = da.operacc
				WHERE ed.doccode = 'PAN'
			)
			SELECT
				ad.auth_id,
				ad.auth_role_id,
				ad.rm_id,
				ad.rm_name,
				ad.cif_id,
				ad.acct_opn_date,
				ad.acct_cls_date,
				ad.cif_id_opening_date,
				ad.operacc,
				ad.operacc AS account_number,
				ad.foracid,
				COALESCE(fd.total_flow_amount, 0) AS total_flow_amount,
				COALESCE(td.total_tran_amt, 0) AS total_tran_amt,
				/* ADDITIONAL DEMAND COLUMN */
				CASE
					WHEN ad.acct_cls_date IS NOT NULL
					     AND ad.acct_cls_date < %(start_date)s
					THEN 0
					ELSE COALESCE(fd.total_flow_amount, 0)
				END AS demand,
				ROUND(
					CASE
						WHEN g.acct_opn_date >= CURRENT_DATE - INTERVAL '1 year' THEN
							LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) * 0.15
						ELSE
							LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) * 0.05
					END, 2
				) AS commission,
				COALESCE(rd.pan_number, 'N/A') AS pan_number,
				CASE
					WHEN g.acct_opn_date >= CURRENT_DATE - INTERVAL '1 year' THEN 'Yes'
					ELSE 'No'
				END AS is_within_one_year,
				ad.sol_id,
				ad.sol_desc,
				ad.schm_code AS scheme_code,
				gsp.schm_desc
			FROM account_data AS ad
			LEFT JOIN flow_data AS fd
				ON ad.foracid = fd.foracid
			LEFT JOIN tran_data AS td
				ON ad.foracid = td.foracid
			LEFT JOIN reference_data AS rd
				ON ad.rm_id = rd.rm_id
			LEFT JOIN tbaadm.gam AS g
				ON ad.foracid = g.foracid
			LEFT JOIN tbaadm.gsp AS gsp
				ON g.schm_code = gsp.schm_code
			ORDER BY
				ad.sol_id, ad.rm_id, ad.schm_code, ad.foracid
		""",
		"mapping": {
			"auth_id": "auth_id",
			"auth_role_id": "auth_role_id",
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"cif_id": "cif_id",
			"acct_opn_date": "account_open_date",
			"acct_cls_date": "account_close_date",
			"cif_id_opening_date": "cif_opening_date",
			"operacc": "operacc",
			"account_number": "account_number",
			"foracid": "foracid",
			"total_flow_amount": "total_flow_amount",
			"total_tran_amt": "total_tran_amt",
			"demand": "demand",
			"commission": "commission",
			"pan_number": "pan_number",
			"is_within_one_year": "is_within_one_year",
			"sol_id": "sol_id",
			"sol_desc": "sol_desc",
			"scheme_code": "scheme_code",
			"schm_desc": "schm_desc",
		},
		"mirror_fields": {"referencenumber": "pan_number"},
		"derived_fields": {"account_close_flag": "acct_cls_date"},
		"date_fields": ["account_open_date", "account_close_date", "cif_opening_date"],
	},
}


class StaffProductivity(Document):
	pass


def _quote(identifier):
	"""Quote a table/column identifier for the active database."""
	if getattr(frappe.db, "db_type", "mariadb") == "mariadb":
		return f"`{identifier}`"
	return f'"{identifier}"'


def _cleanse(value, as_date=False):
	"""
	Coerce a value coming out of psycopg2 into something the local DB accepts.
	- `datetime.datetime` on a Date field is truncated to a plain `date`
	- `Decimal` (PostgreSQL NUMERIC) becomes a float for the Currency columns
	- 'Yes'/'No' strings for Check fields become 1/0
	"""
	if as_date and isinstance(value, datetime.datetime):
		return value.date()
	if isinstance(value, Decimal):
		return float(value)
	if value == "Yes":
		return 1
	if value == "No":
		return 0
	return value


def _bulk_insert(fields, records, constants=None, chunk_size=5000, commit_every=50000):
	"""
	Chunked raw SQL insert, without ORM overhead.

	`records` hold the values of `fields` only. `constants` (field -> value) are
	the same on every row, so they are escaped once and inlined into the row
	template instead of being escaped again for every row.

	A commit every `commit_every` records keeps each transaction small: one huge
	transaction makes InnoDB slow down noticeably as it grows.
	"""
	if not records or not fields:
		return

	constants = constants or {}
	is_mariadb = getattr(frappe.db, "db_type", "mariadb") == "mariadb"
	quote = "`" if is_mariadb else '"'
	table = _quote(get_table_name(DOCTYPE))

	columns = ", ".join(f"{quote}{f}{quote}" for f in (*fields, *constants))
	# `%` is doubled because the driver %-formats the whole statement.
	inlined = [
		(str(v) if isinstance(v, int) else frappe.db.escape(str(v))).replace("%", "%%")
		for v in constants.values()
	]
	placeholder = "(" + ", ".join(["%s"] * len(fields) + inlined) + ")"

	# IGNORE is required on MariaDB: the queries LEFT JOIN tables that hold the
	# amount columns, so a row without a match yields NULL, which the DocType's
	# NOT NULL currency columns would otherwise reject and fail the whole chunk.
	prefix = f"INSERT {'IGNORE ' if is_mariadb else ''}INTO {table} ({columns}) VALUES "

	for i in range(0, len(records), chunk_size):
		chunk = records[i : i + chunk_size]
		frappe.db.sql(prefix + ", ".join([placeholder] * len(chunk)), [v for row in chunk for v in row])
		if (i + chunk_size) % commit_every == 0:
			frappe.db.commit()


def _delete_names(names, chunk_size=20000):
	"""Delete records by `name`, committing chunk by chunk."""
	table = _quote(get_table_name(DOCTYPE))
	for i in range(0, len(names), chunk_size):
		chunk = names[i : i + chunk_size]
		frappe.db.sql(f"DELETE FROM {table} WHERE name IN ({', '.join(['%s'] * len(chunk))})", chunk)
		frappe.db.commit()


@frappe.whitelist()
def sync_staff_productivity(report_type, date=None):
	"""
	Whitelisted endpoint behind the 'Sync' button of the Staff Productivity list
	view. Pulls the report from the DR database and stores it in the DocType.
	Defaults to T-1 (yesterday) when no date is supplied.

	Re-syncing a (report type, date) replaces its records: the fresh rows are
	inserted first and the previous ones deleted only afterwards, so a sync that
	fails part way never loses the data that was already there.
	"""
	if report_type not in REPORT_CONFIG:
		frappe.throw(
			_("Report Type '{0}' is not configured yet. Synced so far: {1}.").format(
				report_type, ", ".join(REPORT_CONFIG)
			)
		)

	sync_date = getdate(date) if date else add_days(getdate(), -1)
	config = REPORT_CONFIG[report_type]
	mapping = config["mapping"]
	mirror = config.get("mirror_fields", {})
	derived = config.get("derived_fields", {})
	date_fields = set(config.get("date_fields", []))

	# The query is cumulative month to date, so one snapshot covers the whole month
	# up to and including the sync date.
	rows = execute_dr_query(
		config["query"],
		{"start_date": str(get_first_day(sync_date)), "sync_date": str(sync_date)},
		cursor_factory=psycopg2.extras.RealDictCursor,
		title=f"Staff Productivity Sync ({report_type})",
	) or []

	# Records of a previous sync of this (date, report_type), replaced below.
	existing = frappe.get_all(
		DOCTYPE, filters={"report_type": report_type, "date": str(sync_date)}, pluck="name"
	)

	timestamp, user = now(), frappe.session.user or "Administrator"
	# Same value on every row, inlined once by `_bulk_insert`.
	constants = {
		"owner": user,
		"modified_by": user,
		"creation": timestamp,
		"modified": timestamp,
		"docstatus": 0,
		"idx": 0,
		"date": str(sync_date),
		"report_type": report_type,
	}

	# Per row values, in the order of `fields`: `name`, the 1:1 mapped columns,
	# the mirrored columns, then the Check fields derived from a nullable column.
	mapped = [(sql_col, field in date_fields) for sql_col, field in mapping.items()]
	fields = ["name", *mapping.values(), *mirror, *derived]
	mirror_cols, derived_cols = list(mirror.values()), list(derived.values())

	records, failed = [], 0
	for i, row in enumerate(rows):
		try:
			records.append(
				(
					# The raw insert bypasses autoname, so the DocType's "hash" naming
					# is applied here.
					frappe.generate_hash(length=10),
					*(_cleanse(row.get(col), as_date=is_date) for col, is_date in mapped),
					*(row.get(col) for col in mirror_cols),
					*(1 if row.get(col) else 0 for col in derived_cols),
				)
			)
		except Exception as e:
			failed += 1
			frappe.log_error(
				title="Staff Productivity Sync Row Error",
				message=f"Failed to process row index {i} for {report_type}: {e}\nRow: {dict(row)}",
			)

	_bulk_insert(fields, records, constants)
	frappe.db.commit()
	_delete_names(existing)

	summary = {
		"report_type": report_type,
		"date": str(sync_date),
		"processed": len(rows),
		"inserted": len(records),
		# Records of the previous sync of this date, removed after the insert.
		"replaced": len(existing),
		"failed": failed,
	}
	frappe.logger().info(f"Staff Productivity Sync {summary}")

	return summary


@frappe.whitelist()
def clear_staff_productivity_data(confirm=False):
	"""
	'Delete All' button of the list view. Without `confirm` it only returns the
	record count for the confirmation dialog; with it, every record is deleted.

	Chunked DELETE rather than TRUNCATE: TRUNCATE is DDL, so it would implicitly
	commit and could not be rolled back if it failed part way.
	"""
	if not confirm:
		return {"total": frappe.db.count(DOCTYPE)}

	if not frappe.has_permission(DOCTYPE, "write"):
		frappe.throw(_("Not permitted to delete {0} records.").format(DOCTYPE), frappe.PermissionError)

	total = frappe.db.count(DOCTYPE)
	if not total:
		return {"total": 0, "deleted": 0, "remaining": 0}

	table = _quote(get_table_name(DOCTYPE))
	chunk_size = 20000
	while True:
		names = frappe.db.sql(f"SELECT name FROM {table} LIMIT {chunk_size}", pluck=True)
		if not names:
			break
		frappe.db.delete(DOCTYPE, {"name": ["in", names]})
		frappe.db.commit()

	remaining = frappe.db.count(DOCTYPE)
	frappe.log_error(
		title="Staff Productivity Delete All",
		message=(
			f"Deleted {total - remaining} of {total} records. "
			f"Remaining: {remaining}. User: {frappe.session.user}."
		),
	)

	return {"total": total, "deleted": total - remaining, "remaining": remaining}
