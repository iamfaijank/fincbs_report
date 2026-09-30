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
	"DD": {
		"title": "DD Productivity",
		"query": """
			WITH account_data AS (
				SELECT
					d.rm_id,
					g2.emp_name AS rm_name,
					d2.auth_id,
					d2.auth_role_id,
					g.cif_id,
					g.acct_opn_date,
					a2.relationshipopeningdate AS cif_id_opening_date,
					d2.operacc,
					g.foracid,
					g.acct_name AS customer_name,
					g.clr_bal_amt,
					tam.deposit_period_mths,
					tam.deposit_period_days,
					tam.deposit_amount,
					tam.maturity_amount,
					tam.maturity_date,
					g.sol_id,
					sol.sol_desc,
					g.schm_code,
					gsp.schm_desc,
					g.acct_cls_date,
					g.acct_cls_flg
				FROM custom.dsamap AS d
				INNER JOIN tbaadm.gam AS g
					ON g.foracid = d.account_number
					AND g.schm_code = '2004'
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
				LEFT JOIN tbaadm.tam AS tam
					ON g.acid = tam.acid
				WHERE g.acct_cls_flg <> 'Y'
					OR g.acct_cls_date >= DATE_TRUNC('month', %(sync_date)s::DATE)::DATE
			),
			demand_data AS (
				SELECT
					ad.foracid,
					ad.schm_code,
					CASE
						WHEN ad.acct_opn_date::DATE < DATE_TRUNC('month', %(sync_date)s::DATE)::DATE
							AND ad.maturity_date::DATE > (DATE_TRUNC('month', %(sync_date)s::DATE) + INTERVAL '1 month' - INTERVAL '1 day')::DATE
						THEN ad.deposit_amount * (
							(DATE_TRUNC('month', %(sync_date)s::DATE) + INTERVAL '1 month' - INTERVAL '1 day')::DATE
							- DATE_TRUNC('month', %(sync_date)s::DATE)::DATE + 1
						)
						WHEN ad.maturity_date::DATE >= DATE_TRUNC('month', %(sync_date)s::DATE)::DATE
							AND ad.maturity_date::DATE <= (DATE_TRUNC('month', %(sync_date)s::DATE) + INTERVAL '1 month' - INTERVAL '1 day')::DATE
						THEN ad.deposit_amount * (
							ad.maturity_date::DATE - DATE_TRUNC('month', %(sync_date)s::DATE)::DATE
						)
						WHEN ad.acct_opn_date::DATE >= DATE_TRUNC('month', %(sync_date)s::DATE)::DATE
							AND ad.acct_opn_date::DATE <= (DATE_TRUNC('month', %(sync_date)s::DATE) + INTERVAL '1 month' - INTERVAL '1 day')::DATE
						THEN ad.deposit_amount * (
							ad.acct_opn_date::DATE - DATE_TRUNC('month', %(sync_date)s::DATE)::DATE + 1
						)
						ELSE 0
					END AS demand_amount
				FROM account_data AS ad
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
					AND g.schm_code = '2004'
				INNER JOIN tbaadm.tdt AS tdt
					ON tdt.acid = g.acid
					AND tdt.flow_code = 'NI'
				WHERE tdt.flow_date BETWEEN %(start_date)s AND %(sync_date)s
					AND (
						g.acct_cls_flg <> 'Y'
						OR g.acct_cls_date >= DATE_TRUNC('month', %(sync_date)s::DATE)::DATE
					)
				GROUP BY d.rm_id, g.foracid, g.schm_code
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
					AND g.schm_code = '2004'
				INNER JOIN tbaadm.dtt AS dtt
					ON dtt.acid = g.acid
					AND dtt.flow_code = 'NI'
				WHERE dtt.value_date BETWEEN %(start_date)s AND %(sync_date)s
					AND (
						g.acct_cls_flg <> 'Y'
						OR g.acct_cls_date >= DATE_TRUNC('month', %(sync_date)s::DATE)::DATE
					)
				GROUP BY d.rm_id, g.foracid, g.schm_code
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
				ad.operacc,
				ad.operacc AS account_number,
				ad.auth_id,
				ad.auth_role_id AS auth_name,
				ad.auth_role_id,
				ad.cif_id,
				ad.acct_opn_date,
				CASE
					WHEN ad.acct_opn_date::DATE >= DATE_TRUNC('month', %(sync_date)s::DATE) - INTERVAL '12 months'
					THEN 'M' || (
						(
							EXTRACT(YEAR FROM AGE(
								DATE_TRUNC('month', %(sync_date)s::DATE),
								DATE_TRUNC('month', ad.acct_opn_date::DATE)
							)) * 12
							+
							EXTRACT(MONTH FROM AGE(
								DATE_TRUNC('month', %(sync_date)s::DATE),
								DATE_TRUNC('month', ad.acct_opn_date::DATE)
							))
						)::INT
					)::TEXT
					ELSE 'M12+'
				END AS bucket,
				ad.cif_id_opening_date,
				LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365) AS account_age,
				ad.foracid,
				ad.customer_name,
				ad.customer_name AS account_name,
				ad.schm_code,
				ad.schm_code AS scheme_code,
				ad.schm_desc,
				ad.sol_id,
				ad.sol_desc,
				ad.deposit_period_mths::INT AS deposit_period_mths,
				ad.deposit_period_days::INT AS deposit_period_days,
				ad.deposit_amount,
				ad.maturity_amount,
				ad.maturity_date,
				ad.acct_cls_date,
				CASE
					WHEN ad.acct_cls_date IS NULL THEN 'ACTIVE'
					ELSE 'CLOSED'
				END AS account_status,
				COALESCE(fd.total_flow_amount, 0) AS total_flow_amount,
				COALESCE(td.total_tran_amt, 0) AS total_tran_amt,
				COALESCE(dd.demand_amount, 0) AS monthly_demand_amount,
				COALESCE(dd.demand_amount, 0) AS demand,
				COALESCE(td.total_tran_amt, 0) AS monthly_collection,
				LEAST(
					ROUND(COALESCE(dd.demand_amount, 0) / NULLIF(ad.deposit_amount, 0), 2),
					365
				)::INT AS monthly_demand_days,
				LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365) * ad.deposit_amount AS ytd_demand_amount,
				COALESCE(ad.clr_bal_amt, 0) AS ytd_collection,
				LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365)::INT AS ytd_demand_days,
				CASE
					WHEN (LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365) * ad.deposit_amount) = 0
					THEN 0
					ELSE ROUND(
						(
							COALESCE(ad.clr_bal_amt, 0)::NUMERIC
							/
							(
								LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365)
								* ad.deposit_amount
							)
						) * 100
					)
				END AS ytd_coll_pct,
				CASE
					WHEN (LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365) * ad.deposit_amount) = 0
					THEN 'DEFAULT'
					WHEN (
						(
							COALESCE(ad.clr_bal_amt, 0)::NUMERIC
							/
							(
								LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365)
								* ad.deposit_amount
							)
						) * 100
					) > 100 THEN 'Excess'
					WHEN (
						(
							COALESCE(ad.clr_bal_amt, 0)::NUMERIC
							/
							(
								LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365)
								* ad.deposit_amount
							)
						) * 100
					) > 75 THEN 'A'
					WHEN (
						(
							COALESCE(ad.clr_bal_amt, 0)::NUMERIC
							/
							(
								LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365)
								* ad.deposit_amount
							)
						) * 100
					) > 50 THEN 'B'
					WHEN (
						(
							COALESCE(ad.clr_bal_amt, 0)::NUMERIC
							/
							(
								LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365)
								* ad.deposit_amount
							)
						) * 100
					) > 25 THEN 'C'
					WHEN (
						(
							COALESCE(ad.clr_bal_amt, 0)::NUMERIC
							/
							(
								LEAST(GREATEST(%(sync_date)s::DATE - ad.acct_opn_date::DATE, 0), 365)
								* ad.deposit_amount
							)
						) * 100
					) > 0 THEN 'D'
					ELSE 'DEFAULT'
				END AS colle_category,
				ROUND(
					CASE
						WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 100000 THEN
							0.035 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
						WHEN LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) > 100000
							AND LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 200000 THEN
							0.04 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
						ELSE
							0.05 * LEAST(COALESCE(fd.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
					END
				) AS commission,
				COALESCE(rd.referencenumber, 'N/A') AS referencenumber
			FROM account_data AS ad
			LEFT JOIN flow_data AS fd
				ON ad.rm_id = fd.rm_id
				AND ad.foracid = fd.foracid
				AND ad.schm_code = fd.schm_code
			LEFT JOIN tran_data AS td
				ON ad.rm_id = td.rm_id
				AND ad.foracid = td.foracid
				AND ad.schm_code = td.schm_code
			LEFT JOIN demand_data AS dd
				ON ad.foracid = dd.foracid
				AND ad.schm_code = dd.schm_code
			LEFT JOIN reference_data AS rd
				ON ad.rm_id = rd.rm_id
			WHERE (fd.total_flow_amount > 0 OR td.total_tran_amt > 0)
			ORDER BY ad.foracid, ad.rm_id, ad.schm_code
		""",
		"mapping": {
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"operacc": "operacc",
			"account_number": "account_number",
			"auth_id": "auth_id",
			"auth_name": "auth_name",
			"auth_role_id": "auth_role_id",
			"cif_id": "cif_id",
			"acct_opn_date": "account_open_date",
			"bucket": "bucket",
			"cif_id_opening_date": "cif_opening_date",
			"account_age": "account_age",
			"foracid": "foracid",
			"customer_name": "customer_name",
			"account_name": "account_name",
			"scheme_code": "scheme_code",
			"schm_desc": "schm_desc",
			"sol_id": "sol_id",
			"sol_desc": "sol_desc",
			"deposit_period_mths": "deposit_period_mths",
			"deposit_period_days": "deposit_period_days",
			"deposit_amount": "deposit_amount",
			"maturity_amount": "maturity_amount",
			"maturity_date": "maturity_date",
			"acct_cls_date": "account_close_date",
			"account_status": "account_status",
			"total_flow_amount": "total_flow_amount",
			"total_tran_amt": "total_tran_amt",
			"monthly_demand_amount": "monthly_demand_amount",
			"demand": "demand",
			"monthly_collection": "monthly_collection",
			"monthly_demand_days": "monthly_demand_days",
			"ytd_demand_amount": "ytd_demand_amount",
			"ytd_collection": "ytd_collection",
			"ytd_demand_days": "ytd_demand_days",
			"ytd_coll_pct": "ytd_coll_pct",
			"colle_category": "colle_category",
			"commission": "commission",
			"referencenumber": "referencenumber",
		},
		"mirror_fields": {"pan_number": "referencenumber"},
		"derived_fields": {"account_close_flag": "acct_cls_date"},
		"date_fields": [
			"account_open_date",
			"account_close_date",
			"cif_opening_date",
			"maturity_date",
		],
	},
	"CASA": {
		"title": "CASA Productivity",
		"query": """
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
			opening_period AS (
				SELECT
					(DATE_TRUNC('month', %(sync_date)s::DATE) - INTERVAL '1 month')::DATE AS opening_start_date,
					(DATE_TRUNC('month', %(sync_date)s::DATE) - INTERVAL '1 day')::DATE AS opening_end_date
			),
			sol_gl_transferred_accts AS (
				SELECT DISTINCT acid
				FROM tbaadm.htd
				WHERE (tran_particular ILIKE '%%Ac xfr from Sol%%'
				       OR tran_particular ILIKE '%%Ac xfr from gl%%')
				  AND tran_date >= %(start_date)s::DATE
				  AND tran_date <= %(sync_date)s::DATE
			),
			balance_duration AS (
				SELECT
					gam.acid,
					gam.foracid,
					gam.sol_id,
					s.sol_desc,
					gam.schm_code,
					gam.acct_name,
					gam.cif_id,
					gam.acct_opn_date,
					gam.acct_cls_flg,
					gam.acct_cls_date,
					a.relationshipopeningdate AS CIF_ID_Opening_Date,
					eab.tran_date_bal AS balance,
					eab.tran_date_bal,
					eab.eod_date,
					gam.clr_bal_amt,
					EXTRACT(
						DAY FROM (
							LEAST(
								CASE
									WHEN eab.end_eod_date = DATE '2099-12-31' THEN %(sync_date)s::DATE
									ELSE eab.end_eod_date
								END,
								%(sync_date)s::DATE
							)
							- GREATEST(eab.eod_date, %(start_date)s::DATE)
						)
					) + 1 AS active_days
				FROM tbaadm.gam gam
				INNER JOIN tbaadm.eab eab ON gam.acid = eab.acid
				INNER JOIN tbaadm.sol s ON s.sol_id = gam.sol_id
				LEFT JOIN crmuser.accounts a ON a.orgkey = gam.cif_id
				WHERE gam.schm_code IN ('1002','1102','1103','1104','1011')
					AND NOT EXISTS (
						SELECT 1 FROM excluded_accts x WHERE x.account_number = gam.foracid
					)
					AND eab.eod_date <= %(sync_date)s::DATE
					AND (
						CASE
							WHEN eab.end_eod_date = DATE '2099-12-31' THEN %(sync_date)s::DATE
							ELSE eab.end_eod_date
						END
					) >= %(start_date)s::DATE
					AND (
						gam.acct_cls_date IS NULL
						OR (
							gam.acct_cls_date >= %(start_date)s::DATE
							AND gam.acct_cls_date < CURRENT_DATE
						)
					)
			),
			weighted_balances AS (
				SELECT
					bd.*,
					t.deposit_amount,
					(bd.balance * bd.active_days) AS weighted_balance
				FROM balance_duration bd
				LEFT JOIN tbaadm.tam t ON bd.acid = t.acid
			),
			closing_calc_raw AS (
				SELECT
					wb.foracid,
					SUM(wb.weighted_balance) AS total_weighted_balance,
					((%(sync_date)s::DATE - %(start_date)s::DATE) + 1) AS total_days,
					SUM(wb.weighted_balance)::numeric
						/ NULLIF(((%(sync_date)s::DATE - %(start_date)s::DATE) + 1), 0) AS raw_avg
				FROM weighted_balances wb
				GROUP BY wb.foracid
			),
			closing_calc AS (
				SELECT
					foracid,
					total_weighted_balance,
					total_days,
					CASE
						WHEN raw_avg - FLOOR(raw_avg) = 0.5 THEN
							CASE
								WHEN MOD(FLOOR(raw_avg)::bigint, 2) = 0 THEN FLOOR(raw_avg)
								ELSE FLOOR(raw_avg) + 1
							END
						ELSE ROUND(raw_avg, 0)
					END AS closing_mab
				FROM closing_calc_raw
			),
			opening_balance_duration AS (
				SELECT
					gam.foracid,
					eab.tran_date_bal,
					EXTRACT(
						DAY FROM (
							LEAST(
								CASE
									WHEN eab.end_eod_date = DATE '2099-12-31' THEN op.opening_end_date
									ELSE eab.end_eod_date
								END,
								op.opening_end_date
							)
							- GREATEST(eab.eod_date, op.opening_start_date)
						)
					) + 1 AS active_days
				FROM tbaadm.gam gam
				JOIN tbaadm.eab eab ON gam.acid = eab.acid
				CROSS JOIN opening_period op
				WHERE gam.schm_code IN ('1002','1102','1103','1104','1011')
					AND NOT EXISTS (
						SELECT 1 FROM excluded_accts x WHERE x.account_number = gam.foracid
					)
					AND eab.eod_date <= op.opening_end_date
					AND (
						CASE
							WHEN eab.end_eod_date = DATE '2099-12-31' THEN op.opening_end_date
							ELSE eab.end_eod_date
						END
					) >= op.opening_start_date
					AND (
						gam.acct_cls_date IS NULL
						OR gam.acct_cls_date >= op.opening_start_date
					)
			),
			opening_calc_raw AS (
				SELECT
					ob.foracid,
					SUM(ob.tran_date_bal * ob.active_days)::numeric
						/ NULLIF((SELECT (opening_end_date - opening_start_date) + 1 FROM opening_period), 0) AS raw_avg
				FROM opening_balance_duration ob
				GROUP BY ob.foracid
			),
			opening_mab_calc AS (
				SELECT
					foracid,
					CASE
						WHEN raw_avg - FLOOR(raw_avg) = 0.5 THEN
							CASE
								WHEN MOD(FLOOR(raw_avg)::bigint, 2) = 0 THEN FLOOR(raw_avg)
								ELSE FLOOR(raw_avg) + 1
							END
						ELSE ROUND(raw_avg, 0)
					END AS opening_mab
				FROM opening_calc_raw
			),
			final_output AS (
				SELECT
					wb.foracid,
					wb.schm_code,
					cc.closing_mab,
					CASE
						WHEN sgt.acid IS NOT NULL THEN 0
						ELSE COALESCE(om.opening_mab, 0)
					END AS opening_mab,
					cc.closing_mab - CASE
						WHEN sgt.acid IS NOT NULL THEN 0
						ELSE COALESCE(om.opening_mab, 0)
					END AS inc_mab,
					get.emp_name,
					d2.auth_id,
					d2.auth_role_id
				FROM weighted_balances wb
				INNER JOIN closing_calc cc ON cc.foracid = wb.foracid
				LEFT JOIN custom.dsamap dsamap ON dsamap.account_number = wb.foracid
				LEFT JOIN tbaadm.get get ON dsamap.rm_id = get.emp_id
				LEFT JOIN custom.dsaauth d2 ON dsamap.rm_id = d2.user_id
				LEFT JOIN opening_mab_calc om ON om.foracid = wb.foracid
				LEFT JOIN sol_gl_transferred_accts sgt ON sgt.acid = wb.acid
				GROUP BY
					wb.foracid, wb.schm_code, cc.closing_mab,
					get.emp_name, d2.auth_id, d2.auth_role_id,
					om.opening_mab, sgt.acid
			)
			SELECT
				fo.auth_id AS auth_id,
				fo.auth_role_id AS auth_role_id,
				MAX(fo.emp_name) AS auth_name,
				COUNT(*) AS account_count,
				COUNT(*) FILTER (WHERE fo.schm_code = '1002') AS sa,
				COUNT(*) FILTER (WHERE fo.schm_code IN ('1102','1103')) AS ca,
				COUNT(*) FILTER (WHERE fo.schm_code IN ('1011','1104')) AS tasc,
				SUM(fo.closing_mab) AS total_closing_mab,
				SUM(fo.opening_mab) AS total_opening_mab,
				SUM(fo.inc_mab) AS total_inc_mab
			FROM final_output fo
			WHERE fo.auth_id IS NOT NULL
			GROUP BY fo.auth_id, fo.auth_role_id
			ORDER BY total_inc_mab DESC
		""",
		"mapping": {
			"auth_id": "auth_id",
			"auth_role_id": "auth_role_id",
			"auth_name": "auth_name",
			"account_count": "account_count",
			"sa": "sa",
			"ca": "ca",
			"tasc": "tasc",
			"total_closing_mab": "total_closing_mab",
			"total_opening_mab": "total_opening_mab",
			"total_inc_mab": "total_inc_mab",
		},
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
