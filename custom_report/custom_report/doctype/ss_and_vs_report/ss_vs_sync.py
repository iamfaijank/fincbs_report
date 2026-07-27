# Copyright (c) 2026, talib and contributors
# For license information, please see license.txt

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
			"total_flow_amount": "total_flow_amount",
			"total_tran_amt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid"]
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
			"total_flow_amount": "total_flow_amount",
			"total_tran_amt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid"]
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
			"total_flow_amount": "total_flow_amount",
			"total_tran_amt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid"]
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
			"total_flow_amount": "total_flow_amount",
			"total_tran_amt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid"]
	},
	"FD 1": {
		"query": """
			WITH account_data AS (
				SELECT 
					ds.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.foracid,
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
			"total_flow_amt_tdt": "total_flow_amount",
			"total_tran_amt_dtt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid"]
	},
	"DAM": {
		"query": """
			WITH account_data AS (
				SELECT 
					ds.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.foracid,
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
					ds.rm_id, g2.emp_name, d2.operacc, g.foracid,
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
				ad.rm_id, ad.rm_name, ad.operacc, ad.foracid,
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
			"total_flow_amt_tdt": "total_flow_amount",
			"total_tran_amt_dtt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid"]
	},
	"FD": {
		"query": """
			WITH account_data AS (
				SELECT 
					ds.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.foracid,  
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
			"total_flow_amt_tdt": "total_flow_amount",
			"total_tran_amt_dtt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid"]
	},
	"SHARE": {
		"query": """
			WITH account_data AS (
				SELECT 
					ds.rm_id, 
					g2.emp_name AS rm_name, 
					d2.operacc,
					g.foracid,  
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
			"total_flow_amt_tdt": "total_flow_amount",
			"total_tran_amt_dtt": "total_transaction_amount",
			"commission": "commission",
			"scheme_code": "scheme_code",
			"schm_desc": "scheme_description",
			"sol_id": "sol_id",
			"sol_desc": "sol_description"
		},
		"unique_keys": ["date", "report_type", "foracid"]
	}
}


@frappe.whitelist()
def sync_report(report_type: str, sync_date: str):
	"""
	Whitelisted API endpoint to trigger synchronization for a specific report and date.
	"""
	if not report_type or not sync_date:
		frappe.throw(_("Report Type and Date are required."))
	
	if report_type not in REPORT_CONFIG:
		frappe.throw(_("Invalid Report Type: {0}").format(report_type))

	engine = SSandVSSyncEngine(report_type, sync_date)
	result = engine.execute()
	return result


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

		# 1. Establish database connection using existing DR mechanism
		conn = None
		try:
			conn = get_dr_connection()
		except Exception as e:
			frappe.log_error(
				message=f"DR Database connection failed for SS & VS sync: {str(e)}",
				title="SS & VS Sync Connection Error"
			)
			frappe.throw(_("Failed to connect to external PostgreSQL database: {0}").format(str(e)))

		# 2. Execute query
		rows = []
		try:
			with conn:
				with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
					cursor.execute(self.query, {
						"date": self.sync_date,
						"start_date": start_date,
						"end_date": end_date
					})
					rows = cursor.fetchall()
		except Exception as e:
			frappe.log_error(
				message=f"SQL Execution error in SS & VS sync ({self.report_type}): {str(e)}",
				title="SS & VS Sync Query Error"
			)
			frappe.throw(_("Error executing SQL query for report: {0}").format(str(e)))
		finally:
			if conn:
				conn.close()

		self.summary["processed"] = len(rows)
		if not rows:
			return self.summary

		# 3. Fetch existing records for cache lookups to optimize performance
		existing_records = frappe.get_all(
			"SS and VS Report",
			filters={"date": self.sync_date, "report_type": self.report_type},
			fields=["name"] + self.unique_keys
		)

		existing_map = {}
		for r in existing_records:
			key_val = tuple(str(r.get(k)).strip() if r.get(k) is not None else "" for k in self.unique_keys)
			existing_map[key_val] = r.name

		# 4. Iterate and Upsert in Batches
		batch_size = 500
		for i, row in enumerate(rows):
			try:
				# Map row columns to DocType fields
				doc_data = {
					"doctype": "SS and VS Report",
					"report_type": self.report_type,
					"date": self.sync_date
				}
				for sql_col, doctype_field in self.mapping.items():
					if sql_col in row:
						val = row[sql_col]
						doc_data[doctype_field] = val

				# Generate the key tuple to search cache
				row_key = tuple(str(doc_data.get(k)).strip() if doc_data.get(k) is not None else "" for k in self.unique_keys)
				existing_name = existing_map.get(row_key)

				if existing_name:
					# Check if there are differences before updating to optimize database hits
					existing_doc = frappe.get_doc("SS and VS Report", existing_name)
					has_diff = False
					for key, val in doc_data.items():
						if key != "doctype" and str(existing_doc.get(key)) != str(val):
							has_diff = True
							break

					if has_diff:
						# Update existing document using standard ORM fields method for efficiency
						frappe.db.set_value(
							"SS and VS Report",
							existing_name,
							{k: v for k, v in doc_data.items() if k != "doctype"},
							update_modified=True
						)
						self.summary["updated"] += 1
					else:
						self.summary["skipped"] += 1
				else:
					# Insert new record
					doc = frappe.get_doc(doc_data)
					doc.insert(ignore_permissions=True)
					self.summary["inserted"] += 1
					# Add newly inserted key to map to prevent duplicates within the same run
					existing_map[row_key] = doc.name

			except Exception as e:
				self.summary["failed"] += 1
				frappe.log_error(
					message=f"Failed to sync row index {i} for {self.report_type}: {str(e)}\nRow details: {dict(row)}",
					title="SS & VS Sync Row Error"
				)

			# Periodically commit to free up database locks and keep transaction small
			if (i + 1) % batch_size == 0:
				frappe.db.commit()

		# Final commit for remaining records
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
