# Copyright (c) 2026, talib and contributors
# For license information, please see license.txt

import time
import frappe
import psycopg2
import psycopg2.extras
from custom_report.db_connection import get_dr_connection
from frappe.utils import get_first_day
from frappe import _

# Configurations for the 8 commission reports.
# Each report configuration defines the SQL query, mapping of SQL columns
# to DocType fields, and the unique keys for upserting.
REPORT_CONFIG = {
	"DD SAV": {
		"query": """
			WITH account_data AS (
				SELECT 
					d.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.cif_id,
					g.acct_opn_date,
					a2.relationshipopeningdate AS cif_id_opening_date,
					g.foracid,  
					g.acct_name AS acct_name,
					g.sol_id,  
					sol.sol_desc,  
					g.schm_code AS scheme_code,  
					gsp.schm_desc, 
					CASE 
						WHEN g.free_text ~ '^[0-9]+(\\.[0-9]+)?$' THEN 
							CAST(g.free_text AS NUMERIC) * DATE_PART('day', DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day')
						ELSE 
							0
					END AS total_flow_amount
				FROM 
					custom.dsamap AS d
				INNER JOIN 
					tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '1007'
				LEFT JOIN 
					crmuser.accounts AS a2 ON g.cif_id = a2.orgkey    
				LEFT JOIN 
					tbaadm.sol AS sol ON g.sol_id = sol.sol_id  
				LEFT JOIN 
					tbaadm.gsp AS gsp ON g.schm_code = gsp.schm_code  
				LEFT JOIN 
					custom.dsaauth AS d2 ON d.rm_id = d2.user_id
				LEFT JOIN 
					tbaadm.get AS g2 ON d2.user_id = g2.emp_id
			),
			transaction_data AS (
				SELECT 
					g.foracid,
					SUM(htd.tran_amt) AS total_tran_amt
				FROM 
					tbaadm.htd AS htd
				INNER JOIN 
					tbaadm.gam AS g ON g.acid = htd.acid
				WHERE 
					htd.part_tran_type = 'C' 
					AND htd.PSTD_FLG = 'Y'
					AND htd.DEL_FLG = 'N'
					AND htd.TRAN_SUB_TYPE != 'IP'
					AND htd.value_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				GROUP BY 
					g.foracid
			),
			reference_data AS (
				SELECT 
					ed.referencenumber, 
					da.user_id AS rm_id
				FROM 
					crmuser.entitydocument AS ed
				INNER JOIN 
					tbaadm.gam AS g ON ed.orgkey = g.cif_id
				INNER JOIN 
					custom.dsaauth AS da ON g.foracid = da.operacc
				WHERE 
					ed.doccode = 'PAN'
			)
			SELECT 
				ad.rm_id, 
				ad.rm_name, 
				ad.operacc, 
				ad.cif_id,
				ad.acct_opn_date,
				ad.cif_id_opening_date,
				ad.foracid,  
				ad.acct_name,
				COALESCE(td.total_tran_amt, 0) AS total_tran_amt, 
				COALESCE(ad.total_flow_amount, 0) AS total_flow_amount,
				ROUND(
					CASE
						WHEN LEAST(COALESCE(ad.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 100000 THEN 
							0.035 * LEAST(COALESCE(ad.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
						WHEN LEAST(COALESCE(ad.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) > 100000 
							 AND LEAST(COALESCE(ad.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0)) <= 200000 THEN 
							0.04 * LEAST(COALESCE(ad.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
						ELSE 
							0.05 * LEAST(COALESCE(ad.total_flow_amount, 0), COALESCE(td.total_tran_amt, 0))
					END::NUMERIC, 0) AS commission,
				COALESCE(rd.referencenumber, 'N/A') AS referencenumber,
				ad.scheme_code,  
				ad.schm_desc,  
				ad.sol_id,  
				ad.sol_desc
			FROM 
				account_data AS ad
			LEFT JOIN 
				transaction_data AS td ON ad.foracid = td.foracid
			LEFT JOIN 
				reference_data AS rd ON ad.rm_id = rd.rm_id
			ORDER BY 
				ad.foracid, ad.rm_id, ad.scheme_code;
		""",
		"mapping": {
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"operacc": "operative_account_number",
			"foracid": "foracid",
			"acct_name": "acct_name",
			"total_flow_amount": "total_flow_amount",
			"total_tran_amt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid", "rm_id", "scheme_code"]
	},
	"DD TDA": {
		"query": """
			WITH account_data AS (
				SELECT 
					d.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.cif_id,
					g.acct_opn_date,
					a2.relationshipopeningdate AS cif_id_opening_date,
					g.foracid,  
					g.acct_name AS acct_name,
					g.sol_id,  
					sol.sol_desc,  
					g.schm_code AS scheme_code,  
					gsp.schm_desc  
				FROM 
					custom.dsamap AS d
				INNER JOIN 
					tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
				LEFT JOIN 
					crmuser.accounts AS a2 ON g.cif_id = a2.orgkey
				LEFT JOIN 
					tbaadm.sol AS sol ON g.sol_id = sol.sol_id  
				LEFT JOIN 
					tbaadm.gsp AS gsp ON g.schm_code = gsp.schm_code  
				LEFT JOIN 
					custom.dsaauth AS d2 ON d.rm_id = d2.user_id
				LEFT JOIN 
					tbaadm.get AS g2 ON d2.user_id = g2.emp_id
			),
			flow_data AS (
				SELECT 
					d.rm_id, 
					g.foracid,  
					g.schm_code,  
					SUM(tdt.flow_amt) AS total_flow_amount
				FROM 
					custom.dsamap AS d
				INNER JOIN 
					tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
				INNER JOIN 
					tbaadm.tdt AS tdt ON tdt.acid = g.acid AND tdt.flow_code = 'NI' 
				WHERE 
					tdt.flow_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				GROUP BY 
					d.rm_id, g.foracid, g.schm_code
				HAVING 
					SUM(tdt.flow_amt) > 0
			),
			tran_data AS (
				SELECT 
					d.rm_id, 
					g.foracid,  
					g.schm_code,  
					SUM(dtt.tran_amt) AS total_tran_amt
				FROM 
					custom.dsamap AS d
				INNER JOIN 
					tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code = '2004'
				INNER JOIN 
					tbaadm.dtt AS dtt ON dtt.acid = g.acid AND dtt.flow_code = 'NI' 
				WHERE 
					dtt.value_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				GROUP BY 
					d.rm_id, g.foracid, g.schm_code
				HAVING 
					SUM(dtt.tran_amt) > 0
			),
			reference_data AS (
				SELECT 
					ed.referencenumber, 
					da.user_id AS rm_id
				FROM 
					crmuser.entitydocument AS ed
				INNER JOIN 
					tbaadm.gam AS g ON ed.orgkey = g.cif_id
				INNER JOIN 
					custom.dsaauth AS da ON g.foracid = da.operacc
				WHERE 
					ed.doccode = 'PAN'
			)
			SELECT 
				ad.rm_id, 
				ad.rm_name, 
				ad.operacc, 
				ad.cif_id,
				ad.acct_opn_date,
				ad.cif_id_opening_date,
				ad.foracid,  
				ad.acct_name,
				COALESCE(fd.total_flow_amount, 0) AS total_flow_amount, 
				COALESCE(td.total_tran_amt, 0) AS total_tran_amt, 
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
				COALESCE(rd.referencenumber, 'N/A') AS referencenumber,
				ad.scheme_code,  
				ad.schm_desc,  
				ad.sol_id,  
				ad.sol_desc  
			FROM 
				account_data AS ad
			LEFT JOIN 
				flow_data AS fd ON ad.rm_id = fd.rm_id AND ad.foracid = fd.foracid AND ad.scheme_code = fd.schm_code
			LEFT JOIN 
				tran_data AS td ON ad.rm_id = td.rm_id AND ad.foracid = td.foracid AND ad.scheme_code = td.schm_code
			LEFT JOIN 
				reference_data AS rd ON ad.rm_id = rd.rm_id
			WHERE 
				(fd.total_flow_amount > 0 OR td.total_tran_amt > 0)
			ORDER BY 
				ad.foracid, ad.rm_id, ad.scheme_code;
		""",
		"mapping": {
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"operacc": "operative_account_number",
			"foracid": "foracid",
			"acct_name": "acct_name",
			"total_flow_amount": "total_flow_amount",
			"total_tran_amt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid", "rm_id", "scheme_code"]
	},
	"RD": {
		"query": """
			WITH account_data AS (
				SELECT 
					d.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.cif_id,
					g.acct_opn_date,
					a2.relationshipopeningdate As CIF_ID_Opening_Date,
					g.foracid,  
					g.acct_name AS acct_name,
					g.sol_id,  
					sol.sol_desc,  
					g.schm_code As scheme_code,  
					gsp.schm_desc  
				FROM 
					custom.dsamap AS d
				INNER JOIN 
					tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code BETWEEN '2010' AND '2016'
				LEFT JOIN 
					crmuser.accounts AS a2 ON g.cif_id = a2.orgkey       
				LEFT JOIN 
					tbaadm.sol AS sol ON g.sol_id = sol.sol_id  
				LEFT JOIN 
					tbaadm.gsp AS gsp ON g.schm_code = gsp.schm_code  
				LEFT JOIN 
					custom.dsaauth AS d2 ON d.rm_id = d2.user_id
				LEFT JOIN 
					tbaadm.get AS g2 ON d2.user_id = g2.emp_id
			),
			flow_data AS (
				SELECT 
					d.rm_id, 
					g.foracid,  
					g.schm_code,  
					SUM(tdt.flow_amt) AS total_flow_amount
				FROM 
					custom.dsamap AS d
				INNER JOIN 
					tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code BETWEEN '2010' AND '2016'
				INNER JOIN 
					tbaadm.tdt AS tdt ON tdt.acid = g.acid AND tdt.flow_code = 'NI' 
				WHERE 
					tdt.flow_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				GROUP BY 
					d.rm_id, g.foracid, g.schm_code
				HAVING 
					SUM(tdt.flow_amt) > 0
			),
			tran_data AS (
				SELECT 
					d.rm_id, 
					g.foracid,  
					g.schm_code,  
					SUM(dtt.tran_amt) AS total_tran_amt
				FROM 
					custom.dsamap AS d
				INNER JOIN 
					tbaadm.gam AS g ON g.foracid = d.account_number AND g.schm_code BETWEEN '2010' AND '2016'
				INNER JOIN 
					tbaadm.dtt AS dtt ON dtt.acid = g.acid AND dtt.flow_code = 'NI' 
				WHERE 
					dtt.value_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				GROUP BY 
					d.rm_id, g.foracid, g.schm_code
				HAVING 
					SUM(dtt.tran_amt) > 0
			),
			reference_data AS (
				SELECT 
					ed.referencenumber, 
					da.user_id AS rm_id
				FROM 
					crmuser.entitydocument AS ed
				INNER JOIN 
					tbaadm.gam AS g ON ed.orgkey = g.cif_id
				INNER JOIN 
					custom.dsaauth AS da ON g.foracid = da.operacc
				WHERE 
					ed.doccode = 'PAN'
			)
			SELECT 
				ad.rm_id, 
				ad.rm_name, 
				ad.operacc, 
				ad.cif_id,
				ad.acct_opn_date,
				ad.CIF_ID_Opening_Date,
				ad.foracid,  
				ad.acct_name,
				COALESCE(fd.total_flow_amount, 0) AS total_flow_amount, 
				COALESCE(td.total_tran_amt, 0) AS total_tran_amt, 
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
				COALESCE(rd.referencenumber, 'N/A') AS referencenumber,
				ad.scheme_code,  
				ad.schm_desc,  
				ad.sol_id,  
				ad.sol_desc  
			FROM 
				account_data AS ad
			LEFT JOIN 
				flow_data AS fd ON ad.rm_id = fd.rm_id AND ad.foracid = fd.foracid AND ad.scheme_code = fd.schm_code
			LEFT JOIN 
				tran_data AS td ON ad.rm_id = td.rm_id AND ad.foracid = td.foracid AND ad.scheme_code = td.schm_code
			LEFT JOIN 
				reference_data AS rd ON ad.rm_id = rd.rm_id
			AND (fd.total_flow_amount > 0 OR td.total_tran_amt > 0)
			ORDER BY 
				ad.foracid, ad.rm_id, ad.scheme_code;
		""",
		"mapping": {
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"operacc": "operative_account_number",
			"foracid": "foracid",
			"acct_name": "acct_name",
			"total_flow_amount": "total_flow_amount",
			"total_tran_amt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid", "rm_id", "scheme_code"]
	},
	"SMBG": {
		"query": """
			WITH account_data AS(
				SELECT 
					d.rm_id, 
					g.cif_id,
					g.acct_opn_date,
					a2.relationshipopeningdate AS cif_id_opening_date,
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.foracid, 
					g.acct_name AS acct_name,
					g.sol_id,  
					sol.sol_desc,  
					g.schm_code  
				FROM 
					custom.dsamap AS d
				LEFT JOIN 
					tbaadm.gam AS g ON g.foracid = d.account_number 
						AND g.schm_code BETWEEN '2005' AND '2006'
				LEFT JOIN 
					crmuser.accounts AS a2 ON g.cif_id = a2.orgkey
				LEFT JOIN 
					custom.dsaauth AS d2 ON UPPER(d.rm_id) = UPPER(d2.user_id)
				LEFT JOIN 
					tbaadm.get AS g2 ON UPPER(d2.user_id) = UPPER(g2.emp_id)
				LEFT JOIN 
					tbaadm.sol AS sol ON g.sol_id = sol.sol_id
				WHERE 
					g.foracid IS NOT NULL
			),
			flow_data AS (
				SELECT 
					g.foracid, 
					SUM(tdt.flow_amt) AS total_flow_amount
				FROM 
					tbaadm.gam AS g
				JOIN 
					tbaadm.tdt AS tdt ON tdt.acid = g.acid 
						AND tdt.flow_code = 'NI' 
						AND tdt.flow_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				WHERE 
					g.schm_code BETWEEN '2005' AND '2006'
				GROUP BY 
					g.foracid
			),
			tran_data AS (
				SELECT 
					g.foracid, 
					SUM(dtt.tran_amt) AS total_tran_amt
				FROM 
					tbaadm.gam AS g
				JOIN 
					tbaadm.dtt AS dtt ON dtt.acid = g.acid 
						AND dtt.flow_code = 'NI' 
						AND dtt.value_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				WHERE 
					g.schm_code BETWEEN '2005' AND '2006'
				GROUP BY 
					g.foracid
			),
			reference_data AS (
				SELECT 
					ed.referencenumber AS pan_number, 
					da.user_id AS rm_id
				FROM 
					crmuser.entitydocument AS ed
				JOIN 
					tbaadm.gam AS g ON ed.orgkey = g.cif_id 
				JOIN 
					custom.dsaauth AS da ON g.foracid = da.operacc
				WHERE 
					ed.doccode = 'PAN'
			)
			SELECT 
				ad.rm_id, 
				ad.cif_id,
				ad.acct_opn_date,
				ad.cif_id_opening_date,
				ad.rm_name, 
				ad.operacc AS account_number, 
				ad.foracid, 
				ad.acct_name,
				COALESCE(fd.total_flow_amount, 0) AS total_flow_amount, 
				COALESCE(td.total_tran_amt, 0) AS total_tran_amt, 
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
			FROM 
				account_data AS ad
			LEFT JOIN 
				flow_data AS fd ON ad.foracid = fd.foracid
			LEFT JOIN 
				tran_data AS td ON ad.foracid = td.foracid
			LEFT JOIN 
				reference_data AS rd ON ad.rm_id = rd.rm_id
			LEFT JOIN 
				tbaadm.gam AS g ON ad.foracid = g.foracid
			LEFT JOIN 
				tbaadm.gsp AS gsp ON g.schm_code = gsp.schm_code
			ORDER BY 
				ad.sol_id, ad.rm_id, ad.schm_code, ad.foracid;
		""",
		"mapping": {
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"account_number": "operative_account_number",
			"foracid": "foracid",
			"acct_name": "acct_name",
			"total_flow_amount": "total_flow_amount",
			"total_tran_amt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid", "rm_id", "scheme_code"]
	},
	"FD 1": {
		"query": """
			WITH account_data AS (
				SELECT 
					ds.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.foracid,
					g.acct_name AS acct_name,
					tam.deposit_period_mths,
					tam.deposit_period_days,
					COUNT(DISTINCT g.acid) AS count_acid_gam,
					SUM(dtt.tran_amt) AS total_tran_amt_dtt,
					SUM(tdt.flow_amt) AS total_flow_amt_tdt,
					g.sol_id,
					sol.sol_desc,
					g.schm_code AS scheme_code,
					gsp.schm_desc
				FROM 
					custom.dsamap AS ds
				LEFT JOIN 
					tbaadm.gam AS g ON g.foracid = ds.account_number
					AND g.schm_code IN ('2018','2001','2023','2024','2025','2026','2027','2028','2029','2030')
					AND g.acct_opn_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
					AND g.acct_cls_flg = 'N'
				LEFT JOIN 
					tbaadm.tam AS tam ON tam.acid = g.acid
				LEFT JOIN 
					tbaadm.dtt AS dtt ON dtt.acid = g.acid 
					AND dtt.flow_code = 'PI'
					AND dtt.value_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				LEFT JOIN 
					tbaadm.tdt AS tdt ON tdt.acid = g.acid 
					AND tdt.flow_code = 'PI'
					AND tdt.flow_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				LEFT JOIN 
					custom.dsaauth AS d2 ON UPPER(ds.rm_id) = UPPER(d2.user_id)
				LEFT JOIN 
					tbaadm.get AS g2 ON d2.user_id = g2.emp_id
				LEFT JOIN 
					tbaadm.sol AS sol ON g.sol_id = sol.sol_id
				LEFT JOIN 
					tbaadm.gsp AS gsp ON gsp.schm_code = g.schm_code
				GROUP BY 
					ds.rm_id, 
					g2.emp_name, 
					d2.operacc, 
					g.foracid,
					g.acct_name,
					tam.deposit_period_mths,
					tam.deposit_period_days,
					g.sol_id,
					sol.sol_desc,
					g.schm_code,
					gsp.schm_desc
			),
			reference_data AS (
				SELECT 
					ed.referencenumber, 
					da.user_id AS rm_id
				FROM 
					crmuser.entitydocument AS ed
				JOIN 
					tbaadm.gam AS g ON ed.orgkey = g.cif_id 
				JOIN 
					custom.dsaauth AS da ON g.foracid = da.operacc
				WHERE 
					ed.doccode = 'PAN'
			)
			SELECT 
				ad.rm_id, 
				ad.rm_name, 
				ad.operacc, 
				ad.foracid,
				ad.acct_name,
				ad.deposit_period_mths,
				ad.deposit_period_days,
				ad.sol_id,
				ad.sol_desc,
				ad.scheme_code,
				ad.schm_desc,
				SUM(ad.total_tran_amt_dtt) AS total_tran_amt_dtt, 
				SUM(ad.total_flow_amt_tdt) AS total_flow_amt_tdt,
				ROUND(CASE
					WHEN ad.deposit_period_mths < 12 THEN 
						0.0050 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 12 THEN 
						0.015 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 24 THEN 
						0.03 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 48 
						 AND COALESCE(SUM(ad.total_tran_amt_dtt), 0) >= 1000000 THEN 
					   0.03 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 36 THEN 
						0.045 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 48 THEN 
						0.06 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 60 THEN 
						0.075 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					ELSE 
						0
				END, 0) AS commission,
				MAX(COALESCE(rd.referencenumber, 'N/A')) AS referencenumber
			FROM 
				account_data AS ad
			LEFT JOIN 
				reference_data AS rd 
				ON UPPER(ad.rm_id) = UPPER(rd.rm_id)
			WHERE 
				ad.count_acid_gam > 0 OR ad.total_tran_amt_dtt > 0 OR ad.total_flow_amt_tdt > 0
			GROUP BY 
				ad.rm_id, 
				ad.rm_name, 
				ad.operacc, 
				ad.foracid,
				ad.acct_name,
				ad.deposit_period_mths,
				ad.deposit_period_days,
				ad.sol_id,
				ad.sol_desc,
				ad.scheme_code,
				ad.schm_desc
			ORDER BY 
				ad.sol_id, ad.rm_id, ad.scheme_code, ad.deposit_period_mths;
		""",
		"mapping": {
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"operacc": "operative_account_number",
			"foracid": "foracid",
			"acct_name": "acct_name",
			"total_flow_amt_tdt": "total_flow_amount",
			"total_tran_amt_dtt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid", "rm_id", "scheme_code"]
	},
	"DAM": {
		"query": """
			WITH account_data AS (
				SELECT 
					ds.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.foracid,
					g.acct_name AS acct_name,
					tam.deposit_period_mths,
					tam.deposit_period_days,
					COUNT(DISTINCT g.acid) AS count_acid_gam,
					SUM(dtt.tran_amt) AS total_tran_amt_dtt,
					SUM(tdt.flow_amt) AS total_flow_amt_tdt,
					g.sol_id,
					sol.sol_desc,
					g.schm_code AS scheme_code,
					gsp.schm_desc
				FROM 
					custom.dsamap AS ds
				LEFT JOIN 
					tbaadm.gam AS g 
					ON g.foracid = ds.account_number
					AND g.schm_code IN ('2101','2102','2103','2104','2105','2201','2202','2002','2003')
					AND g.acct_opn_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
					AND g.acct_cls_flg = 'N'
				LEFT JOIN 
					tbaadm.tam AS tam ON tam.acid = g.acid
				LEFT JOIN 
					tbaadm.dtt AS dtt 
					ON dtt.acid = g.acid 
					AND dtt.flow_code = 'PI'
					AND dtt.value_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				LEFT JOIN 
					tbaadm.tdt AS tdt 
					ON tdt.acid = g.acid 
					AND tdt.flow_code = 'PI'
					AND tdt.flow_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				LEFT JOIN 
					custom.dsaauth AS d2 ON UPPER(ds.rm_id) = UPPER(d2.user_id)
				LEFT JOIN 
					tbaadm.get AS g2 ON d2.user_id = g2.emp_id
				LEFT JOIN 
					tbaadm.sol AS sol ON g.sol_id = sol.sol_id
				LEFT JOIN 
					tbaadm.gsp AS gsp ON gsp.schm_code = g.schm_code
				GROUP BY 
					ds.rm_id, g2.emp_name, d2.operacc, g.foracid, g.acct_name,
					tam.deposit_period_mths, tam.deposit_period_days,
					g.sol_id, sol.sol_desc, g.schm_code, gsp.schm_desc
			),
			reference_data AS (
				SELECT 
					ed.referencenumber, 
					da.user_id AS rm_id
				FROM 
					crmuser.entitydocument AS ed
				JOIN 
					tbaadm.gam AS g ON ed.orgkey = g.cif_id 
				JOIN 
					custom.dsaauth AS da ON g.foracid = da.operacc
				WHERE 
					ed.doccode = 'PAN'
			)
			SELECT 
				ad.rm_id, 
				ad.rm_name, 
				ad.operacc, 
				ad.foracid,
				ad.acct_name,
				ad.deposit_period_mths,
				ad.deposit_period_days,
				ad.sol_id,
				ad.sol_desc,
				ad.scheme_code,
				ad.schm_desc,
				SUM(ad.total_tran_amt_dtt) AS total_tran_amt_dtt, 
				SUM(ad.total_flow_amt_tdt) AS total_flow_amt_tdt,
				CASE 
					WHEN ad.scheme_code = '2201' 
						THEN ROUND(0.09 * LEAST(COALESCE(SUM(ad.total_flow_amt_tdt), 0), COALESCE(SUM(ad.total_tran_amt_dtt), 0)))
					WHEN ad.scheme_code = '2202' 
						THEN ROUND(0.03 * LEAST(COALESCE(SUM(ad.total_flow_amt_tdt), 0), COALESCE(SUM(ad.total_tran_amt_dtt), 0)))
					WHEN ad.deposit_period_mths = 36 
						THEN ROUND(0.03 * LEAST(COALESCE(SUM(ad.total_flow_amt_tdt), 0), COALESCE(SUM(ad.total_tran_amt_dtt), 0)))
					WHEN ad.deposit_period_mths = 12 
						THEN ROUND(0.01 * LEAST(COALESCE(SUM(ad.total_flow_amt_tdt), 0), COALESCE(SUM(ad.total_tran_amt_dtt), 0)))
					WHEN LEAST(COALESCE(SUM(ad.total_flow_amt_tdt), 0), COALESCE(SUM(ad.total_tran_amt_dtt), 0)) >= 1000000 
						THEN ROUND(0.03 * LEAST(COALESCE(SUM(ad.total_flow_amt_tdt), 0), COALESCE(SUM(ad.total_tran_amt_dtt), 0)))
					ELSE ROUND(0.075 * LEAST(COALESCE(SUM(ad.total_flow_amt_tdt), 0), COALESCE(SUM(ad.total_tran_amt_dtt), 0)))
				END AS commission,
				MAX(COALESCE(rd.referencenumber, 'N/A')) AS referencenumber
			FROM 
				account_data AS ad
			LEFT JOIN 
				reference_data AS rd ON UPPER(ad.rm_id) = UPPER(rd.rm_id)
			WHERE 
				ad.count_acid_gam > 0 
				OR ad.total_tran_amt_dtt > 0 
				OR ad.total_flow_amt_tdt > 0
			GROUP BY 
				ad.rm_id, ad.rm_name, ad.operacc, ad.foracid, ad.acct_name,
				ad.deposit_period_mths, ad.deposit_period_days,
				ad.sol_id, ad.sol_desc, ad.scheme_code, ad.schm_desc
			ORDER BY 
				ad.sol_id, ad.rm_id, ad.scheme_code, ad.deposit_period_mths;
		""",
		"mapping": {
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"operacc": "operative_account_number",
			"foracid": "foracid",
			"acct_name": "acct_name",
			"total_flow_amt_tdt": "total_flow_amount",
			"total_tran_amt_dtt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid", "rm_id", "scheme_code"]
	},
	"FD": {
		"query": """
			WITH account_data AS (
				SELECT 
					ds.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.foracid,  
					g.acct_name AS acct_name,
					tam.deposit_period_mths,
					tam.deposit_period_days,
					COUNT(DISTINCT g.acid) AS count_acid_gam,  
					SUM(dtt.tran_amt) AS total_tran_amt_dtt,  
					SUM(tdt.flow_amt) AS total_flow_amt_tdt,  
					g.sol_id,  
					sol.sol_desc,  
					g.schm_code AS scheme_code,  
					gsp.schm_desc  
				FROM 
					custom.dsamap AS ds
				LEFT JOIN 
					tbaadm.gam AS g ON g.foracid = ds.account_number
					AND g.schm_code IN ('2019','2020','2021','2022')
					AND g.acct_opn_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE 
					AND g.acct_cls_flg = 'N'
				LEFT JOIN 
					tbaadm.tam AS tam ON tam.acid = g.acid
				LEFT JOIN 
					tbaadm.dtt AS dtt ON dtt.acid = g.acid 
					AND dtt.flow_code = 'PI'
					AND dtt.value_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				LEFT JOIN 
					tbaadm.tdt AS tdt ON tdt.acid = g.acid 
					AND tdt.flow_code = 'PI'
					AND tdt.flow_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE
				LEFT JOIN 
					custom.dsaauth AS d2 ON UPPER(ds.rm_id) = UPPER(d2.user_id)
				LEFT JOIN 
					tbaadm.get AS g2 ON d2.user_id = g2.emp_id
				LEFT JOIN 
					tbaadm.sol AS sol ON g.sol_id = sol.sol_id
				LEFT JOIN 
					tbaadm.gsp AS gsp ON gsp.schm_code = g.schm_code
				GROUP BY 
					ds.rm_id, 
					g2.emp_name, 
					d2.operacc, 
					g.foracid,  
					g.acct_name,
					tam.deposit_period_mths,  
					tam.deposit_period_days,
					g.sol_id,  
					sol.sol_desc,  
					g.schm_code,  
					gsp.schm_desc
			),
			reference_data AS (
				SELECT 
					ed.referencenumber, 
					da.user_id AS rm_id
				FROM 
					crmuser.entitydocument AS ed
				JOIN 
					tbaadm.gam AS g ON ed.orgkey = g.cif_id 
				JOIN 
					custom.dsaauth AS da ON g.foracid = da.operacc
				WHERE 
					ed.doccode = 'PAN'
			)
			SELECT 
				ad.rm_id, 
				ad.rm_name, 
				ad.operacc, 
				ad.foracid,  
				ad.acct_name,
				ad.deposit_period_mths,
				ad.deposit_period_days,
				ad.sol_id,  
				ad.sol_desc,  
				ad.scheme_code,  
				ad.schm_desc,  
				SUM(ad.total_tran_amt_dtt) AS total_tran_amt_dtt, 
				SUM(ad.total_flow_amt_tdt) AS total_flow_amt_tdt,
				ROUND(CASE
					WHEN ad.deposit_period_mths < 13 THEN 
						0.0075 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 13 THEN 
						0.015 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 26 THEN 
						0.03 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 39 
						 AND COALESCE(SUM(ad.total_tran_amt_dtt), 0) >= 1000000 THEN 
						0.03 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 39 THEN 
						0.045 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 52 THEN 
						0.06 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					WHEN ad.deposit_period_mths = 65 THEN 
						0.075 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					ELSE 
						0
				END, 0) AS commission,  
				MAX(COALESCE(rd.referencenumber, 'N/A')) AS referencenumber  
			FROM 
				account_data AS ad
			LEFT JOIN 
				reference_data AS rd 
				ON UPPER(ad.rm_id) = UPPER(rd.rm_id)
			WHERE 
				ad.count_acid_gam > 0 OR ad.total_tran_amt_dtt > 0 OR ad.total_flow_amt_tdt > 0
			GROUP BY 
				ad.rm_id, 
				ad.rm_name, 
				ad.operacc, 
				ad.foracid,  
				ad.acct_name,
				ad.deposit_period_mths,
				ad.deposit_period_days,
				ad.sol_id,  
				ad.sol_desc,  
				ad.scheme_code,  
				ad.schm_desc
			ORDER BY 
				ad.sol_id, ad.rm_id, ad.scheme_code, ad.deposit_period_mths;
		""",
		"mapping": {
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"operacc": "operative_account_number",
			"foracid": "foracid",
			"acct_name": "acct_name",
			"total_flow_amt_tdt": "total_flow_amount",
			"total_tran_amt_dtt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid", "rm_id", "scheme_code"]
	},
	"SHARE": {
		"query": """
			WITH account_data AS (
				SELECT 
					ds.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.foracid,  
					g.acct_name AS acct_name,
					tam.deposit_period_mths,
					tam.deposit_period_days,
					COUNT(DISTINCT g.acid) AS count_acid_gam,  
					SUM(dtt.tran_amt) AS total_tran_amt_dtt,  
					SUM(tdt.flow_amt) AS total_flow_amt_tdt,  
					g.sol_id,  
					sol.sol_desc,  
					g.schm_code AS scheme_code,  
					gsp.schm_desc  
				FROM 
					custom.dsamap AS ds
				LEFT JOIN 
					tbaadm.gam AS g ON g.foracid = ds.account_number
					AND g.schm_code in ('9001','9002')  
					AND g.acct_opn_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE 
					AND g.acct_cls_flg = 'N'  
				LEFT JOIN 
					tbaadm.tam AS tam ON tam.acid = g.acid
				LEFT JOIN 
					tbaadm.dtt AS dtt ON dtt.acid = g.acid 
					AND dtt.flow_code = 'PI'
					AND dtt.value_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE 
				LEFT JOIN 
					tbaadm.tdt AS tdt ON tdt.acid = g.acid 
					AND tdt.flow_code = 'PI'
					AND tdt.flow_date BETWEEN %(start_date)s::DATE AND %(end_date)s::DATE 
				LEFT JOIN 
					custom.dsaauth AS d2 ON UPPER(ds.rm_id) = UPPER(d2.user_id)  
				LEFT JOIN 
					tbaadm.get AS g2 ON d2.user_id = g2.emp_id
				LEFT JOIN 
					tbaadm.sol AS sol ON g.sol_id = sol.sol_id  
				LEFT JOIN 
					tbaadm.gsp AS gsp ON gsp.schm_code = g.schm_code  
				GROUP BY 
					ds.rm_id, 
					g2.emp_name, 
					d2.operacc, 
					g.foracid,  
					g.acct_name,
					tam.deposit_period_mths,  
					tam.deposit_period_days,
					g.sol_id,  
					sol.sol_desc,  
					g.schm_code,  
					gsp.schm_desc  
			),
			reference_data AS (
				SELECT 
					ed.referencenumber, 
					da.user_id AS rm_id
				FROM 
					crmuser.entitydocument AS ed
				JOIN 
					tbaadm.gam AS g ON ed.orgkey = g.cif_id 
				JOIN 
					custom.dsaauth AS da ON g.foracid = da.operacc
				WHERE 
					ed.doccode = 'PAN'
			)
			SELECT 
				ad.rm_id, 
				ad.rm_name, 
				ad.operacc, 
				ad.foracid,  
				ad.acct_name,
				ad.deposit_period_mths,
				ad.deposit_period_days,
				ad.sol_id,  
				ad.sol_desc,  
				ad.scheme_code,  
				ad.schm_desc,  
				SUM(ad.total_tran_amt_dtt) AS total_tran_amt_dtt, 
				SUM(ad.total_flow_amt_tdt) AS total_flow_amt_tdt,
				ROUND(CASE
					WHEN ad.deposit_period_mths = 120 THEN 
						0.03 * LEAST(COALESCE(SUM(ad.total_tran_amt_dtt), 0), COALESCE(SUM(ad.total_flow_amt_tdt), 0))
					ELSE 
						0
				END, 0) AS commission,  
				MAX(COALESCE(rd.referencenumber, 'N/A')) AS referencenumber  
			FROM 
				account_data AS ad
			LEFT JOIN 
				reference_data AS rd 
				ON UPPER(ad.rm_id) = UPPER(rd.rm_id)  
			WHERE 
				ad.count_acid_gam > 0 OR ad.total_tran_amt_dtt > 0 OR ad.total_flow_amt_tdt > 0  
			GROUP BY 
				ad.rm_id, 
				ad.rm_name, 
				ad.operacc, 
				ad.foracid,  
				ad.acct_name,
				ad.deposit_period_mths,
				ad.deposit_period_days,
				ad.sol_id,  
				ad.sol_desc,  
				ad.scheme_code,  
				ad.schm_desc  
			ORDER BY 
				ad.sol_id, ad.rm_id, ad.scheme_code, ad.deposit_period_mths;
		""",
		"mapping": {
			"rm_id": "rm_id",
			"rm_name": "rm_name",
			"operacc": "operative_account_number",
			"foracid": "foracid",
			"acct_name": "acct_name",
			"total_flow_amt_tdt": "total_flow_amount",
			"total_tran_amt_dtt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid", "rm_id", "scheme_code"]
	}
}


@frappe.whitelist()
def sync_report(report_type: str, sync_date: str):
	"""
	Whitelisted API endpoint to trigger synchronization for a specific report or 'All Reports' and date.
	Executes directly without using enqueue.
	"""
	if not report_type or not sync_date:
		frappe.throw(_("Report Type and Date are required."))
	
	if report_type == "All Reports":
		return sync_all_reports(sync_date)

	if report_type not in REPORT_CONFIG:
		frappe.throw(_("Invalid Report Type: {0}").format(report_type))

	engine = SSandVSSyncEngine(report_type, sync_date)
	result = engine.execute()
	return result


@frappe.whitelist()
def sync_all_reports(sync_date: str = None):
	"""
	Directly synchronizes all 8 SS & VS report types sequentially without using enqueue.
	"""
	if not sync_date:
		sync_date = frappe.utils.add_days(frappe.utils.nowdate(), -1)

	total_summary = {
		"processed": 0,
		"inserted": 0,
		"updated": 0,
		"skipped": 0,
		"failed": 0,
		"details": {}
	}

	for report_type in REPORT_CONFIG.keys():
		try:
			engine = SSandVSSyncEngine(report_type, sync_date)
			res = engine.execute()
			total_summary["details"][report_type] = res
			total_summary["processed"] += res.get("processed", 0)
			total_summary["inserted"] += res.get("inserted", 0)
			total_summary["updated"] += res.get("updated", 0)
			total_summary["skipped"] += res.get("skipped", 0)
			total_summary["failed"] += res.get("failed", 0)
		except Exception as e:
			frappe.log_error(
				message=f"Failed direct sync of {report_type} on {sync_date}: {str(e)}",
				title="SS & VS Direct All Sync Error"
			)

	return total_summary


def daily_sync_all_ss_vs_reports():
	"""
	Scheduled cron function to directly sync all SS & VS reports for yesterday.
	"""
	yesterday = frappe.utils.add_days(frappe.utils.nowdate(), -1)
	return sync_all_reports(sync_date=yesterday)


def _sync_daily_t1_report(report_type: str):
	"""
	Helper method to calculate yesterday's date (T-1) and execute synchronization for the given report type.
	"""
	sync_enabled = frappe.db.get_single_value("Drishti Settings", "auto_sync")
	if not sync_enabled:
		frappe.logger("scheduler").info(f"SS & VS Daily Sync Cron ({report_type}): Sync is disabled in Drishti Settings. Skipping execution.")
		return

	yesterday = frappe.utils.add_days(frappe.utils.nowdate(), -1)
	engine = SSandVSSyncEngine(report_type, yesterday)
	return engine.execute()


def sync_dd_sav_daily():
	"""Cron scheduled at 07:00 AM IST daily - Syncs DD SAV report for T-1 (Yesterday) date."""
	return _sync_daily_t1_report("DD SAV")


def sync_dd_tda_daily():
	"""Cron scheduled at 07:05 AM IST daily - Syncs DD TDA report for T-1 (Yesterday) date."""
	return _sync_daily_t1_report("DD TDA")


def sync_rd_daily():
	"""Cron scheduled at 07:10 AM IST daily - Syncs RD report for T-1 (Yesterday) date."""
	return _sync_daily_t1_report("RD")


def sync_smbg_daily():
	"""Cron scheduled at 07:15 AM IST daily - Syncs SMBG report for T-1 (Yesterday) date."""
	return _sync_daily_t1_report("SMBG")


def sync_fd_1_daily():
	"""Cron scheduled at 07:20 AM IST daily - Syncs FD 1 report for T-1 (Yesterday) date."""
	return _sync_daily_t1_report("FD 1")


def sync_dam_daily():
	"""Cron scheduled at 07:25 AM IST daily - Syncs DAM report for T-1 (Yesterday) date."""
	return _sync_daily_t1_report("DAM")


def sync_fd_daily():
	"""Cron scheduled at 07:30 AM IST daily - Syncs FD report for T-1 (Yesterday) date."""
	return _sync_daily_t1_report("FD")


def sync_share_daily():
	"""Cron scheduled at 07:35 AM IST daily - Syncs SHARE report for T-1 (Yesterday) date."""
	return _sync_daily_t1_report("SHARE")


def execute_ss_vs_bulk_insert(fields: list, records: list, chunk_size: int = 5000) -> None:
	"""
	Direct chunked raw SQL bulk INSERT into tabSS and VS Report table without ORM overhead.
	Bypasses frappe.db.bulk_insert packet size limits by inserting in optimal chunks of 5000.
	"""
	if not records or not fields:
		return

	db_type = getattr(frappe.db, "db_type", "mariadb")

	if db_type == "mariadb":
		escaped_fields = ", ".join(f"`{f}`" for f in fields)
		table_name = "`tabSS and VS Report`"
		sql_prefix = f"INSERT IGNORE INTO {table_name}"
	else:
		escaped_fields = ", ".join(f'"{f}"' for f in fields)
		table_name = '"tabSS and VS Report"'
		sql_prefix = f"INSERT INTO {table_name}"

	row_placeholder = "(" + ", ".join(["%s"] * len(fields)) + ")"

	for i in range(0, len(records), chunk_size):
		chunk = records[i : i + chunk_size]
		placeholders = ", ".join([row_placeholder] * len(chunk))
		flattened_params = [val for row in chunk for val in row]

		if db_type == "mariadb":
			sql = f"{sql_prefix} ({escaped_fields}) VALUES {placeholders};"
		else:
			sql = f"{sql_prefix} ({escaped_fields}) VALUES {placeholders} ON CONFLICT DO NOTHING;"

		frappe.db.sql(sql, flattened_params)


class SSandVSSyncEngine:
	def __init__(self, report_type: str, sync_date: str):
		self.report_type = report_type
		self.sync_date = sync_date
		self.config = REPORT_CONFIG[self.report_type]
		self.query = self.config["query"]
		self.mapping = self.config["mapping"]
		self.unique_keys = self.config["unique_keys"]
		self.summary = {
			"processed": 0,
			"inserted": 0,
			"updated": 0,
			"skipped": 0,
			"failed": 0
		}

	def execute(self):
		# Calculate dynamic start and end dates based on the selected sync date.
		# start_date is the first day of the month of the selected sync_date.
		# end_date is the selected sync_date itself.
		start_date = get_first_day(self.sync_date)
		end_date = self.sync_date

		# 1 & 2. Establish connection and execute query with recovery conflict retry loop
		rows = []
		max_retries = 5

		for attempt in range(max_retries):
			conn = None
			try:
				conn = get_dr_connection()
				with conn:
					with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
						try:
							cursor.execute("SET statement_timeout = 0;")
						except Exception:
							pass
						cursor.execute(self.query, {
							"date": self.sync_date,
							"start_date": start_date,
							"end_date": end_date
						})
						rows = cursor.fetchall()
				if conn:
					try:
						conn.close()
					except Exception:
						pass
				break # Success, exit retry loop
			except Exception as e:
				if conn:
					try:
						conn.close()
					except Exception:
						pass

				err_str = str(e).lower()
				is_recovery_conflict = any(term in err_str for term in [
					"conflict with recovery", "canceling statement", "querycanceled",
					"serializationfailure", "55006", "40001"
				])

				if is_recovery_conflict and attempt < max_retries - 1:
					retry_delay = (attempt + 1) * 3
					frappe.log_error(f"DR DB Query Conflict for {self.report_type} (Attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...", "SS & VS Sync Retry")
					time.sleep(retry_delay)
				else:
					frappe.log_error(
						message=f"SQL Execution error in SS & VS sync ({self.report_type}): {str(e)}",
						title="SS & VS Sync Query Error"
					)
					frappe.throw(_("Error executing SQL query for report: {0}").format(str(e)))

		self.summary["processed"] = len(rows)
		if not rows:
			return self.summary

		# 3. Purge existing records for this (date, report_type) to ensure a clean sync without skipped rows
		frappe.db.delete("SS and VS Report", filters={"date": self.sync_date, "report_type": self.report_type})

		# 4. Prepare all rows for bulk insertion
		new_docs = []
		now_time = frappe.utils.now()
		user = frappe.session.user or "Administrator"

		for i, row in enumerate(rows):
			try:
				# Map row columns to DocType fields
				doc_data = {
					"name": frappe.generate_hash(length=16),
					"owner": user,
					"modified_by": user,
					"creation": now_time,
					"modified": now_time,
					"docstatus": 0,
					"idx": 0,
					"report_type": self.report_type,
					"date": self.sync_date
				}
				for sql_col, doctype_field in self.mapping.items():
					if sql_col in row:
						doc_data[doctype_field] = row[sql_col]

				new_docs.append(doc_data)

			except Exception as e:
				self.summary["failed"] += 1
				frappe.log_error(
					message=f"Failed to process row index {i} for {self.report_type}: {str(e)}\nRow details: {dict(row)}",
					title="SS & VS Sync Row Error"
				)

		# 5. Bulk insert all records in a single SQL query
		if new_docs:
			insert_fields = ["name", "owner", "modified_by", "creation", "modified", "docstatus", "idx", "date", "report_type"]
			for f in self.mapping.values():
				if f not in insert_fields:
					insert_fields.append(f)

			values_to_insert = [
				tuple(d.get(f) for f in insert_fields)
				for d in new_docs
			]

			execute_ss_vs_bulk_insert(insert_fields, values_to_insert, chunk_size=5000)
			self.summary["inserted"] = len(new_docs)

		# Final commit
		frappe.db.commit()

		# Log execution summary
		summary_msg = (
			f"SS & VS Report Sync finished ({self.report_type} on {self.sync_date}). "
			f"Processed: {self.summary['processed']}, "
			f"Inserted: {self.summary['inserted']}, "
			f"Updated: {self.summary['updated']}, "
			f"Skipped: {self.summary['skipped']}, "
			f"Failed: {self.summary['failed']}"
		)
		frappe.logger().info(summary_msg)

		return self.summary
