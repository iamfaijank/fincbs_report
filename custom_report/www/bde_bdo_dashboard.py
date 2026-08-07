import frappe
import json
import re
from frappe.boot import load_translations

no_cache = 1


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	context.csrf_token = csrf_token
	context.boot = json.dumps(get_boot(), default=str)
	context.site_name = frappe.local.site
	return context


def get_boot():
	bootinfo = frappe._dict(
		{
			"site_name": frappe.local.site,
			"default_route": "/bde_bdo_dashboard",
		}
	)
	bootinfo.lang = frappe.local.lang
	load_translations(bootinfo)
	return bootinfo


def get_user_report_permissions(user):
	permissions = {
		"zones": [],
		"regions": [],
		"sol_data": [],
		"sol_ids": [],
		"is_restricted": False,
		"all_regions": False,
		"zone_ids": [],
		"region_ids": [],
		"has_access": True,
	}

	pref_name = frappe.db.get_value("Report Preference", {"user": user}, "name")
	if not pref_name:
		if "System Manager" in frappe.get_roles(user):
			return permissions
		permissions["has_access"] = False
		return permissions

	doc = frappe.get_doc("Report Preference", pref_name)
	permissions["pref_name"] = pref_name
	permissions["is_restricted"] = True
	permissions["all_regions"] = doc.all_regions

	permissions["zones"] = frappe.db.get_all(
		"Zone Items", filters={"parent": pref_name, "parentfield": "zone"}, pluck="zone"
	) or []
	permissions["zone_ids"] = [
		re.sub(r"\D", "", z) for z in permissions["zones"] if re.sub(r"\D", "", z)
	]

	permissions["regions"] = frappe.db.get_all(
		"Region Items", filters={"parent": pref_name, "parentfield": "region"}, pluck="region"
	) or []
	permissions["region_ids"] = [
		re.sub(r"\D", "", r) for r in permissions["regions"] if re.sub(r"\D", "", r)
	]

	permissions["sol_ids"] = frappe.db.get_all(
		"Sol Items", filters={"parent": pref_name, "parentfield": "sol_id"}, pluck="sol_id"
	) or []

	if permissions["sol_ids"]:
		branches = frappe.get_all(
			"Sahayog Branch",
			filters={"name": ["in", permissions["sol_ids"]]},
			fields=["name as sol_id", "branch as branch_name"],
		)
		permissions["sol_data"] = branches

	return permissions


@frappe.whitelist(allow_guest=True)
def get_rd_smbg_pending_table_data():
	from custom_report.db_connection import get_dr_connection

	query = """
    WITH main_data AS (
        SELECT g.acid, g.sol_id, s.sol_desc, t.maturity_date, t.last_repayment_date,
               s.division_name, s.region_name, s.circle_office_name
        FROM tbaadm.gam g
        JOIN tbaadm.tam t ON g.acid = t.acid
        JOIN tbaadm.sol s ON g.sol_id = s.sol_id
        WHERE g.schm_code IN ('2005','2010','2011','2012','2013','2014','2015','2016')
            AND g.entity_cre_flg = 'Y'
            AND g.del_flg = 'N'
            AND g.acct_cls_flg = 'N'
            AND t.maturity_date >= CURRENT_DATE
    ),
    tdt_summary AS (
        SELECT acid,
               COALESCE(SUM(tran_amt), 0) AS total_instalment_paid,
               COALESCE(SUM(flow_amt) - SUM(tran_amt), 0) AS pending_amount,
               COUNT(CASE WHEN flow_amt > 0 THEN 1 END) - COUNT(CASE WHEN tran_amt > 0 THEN 1 END) AS pending_instalments
        FROM tbaadm.tdt
        WHERE flow_code = 'NI'
            AND (flow_amt > 0 OR tran_amt > 0)
            AND flow_date <= CURRENT_DATE
        GROUP BY acid
    )
    SELECT m.sol_id, m.sol_desc, m.division_name, m.region_name, m.circle_office_name,
           COUNT(*) AS total_accounts,
           COALESCE(SUM(t.total_instalment_paid), 0) AS total_collection,
           COALESCE(SUM(CASE WHEN t.pending_amount > 0 THEN 1 ELSE 0 END), 0) AS pending_accounts,
           COALESCE(SUM(t.pending_amount), 0) AS pending_amount,
           COALESCE(SUM(t.pending_instalments), 0) AS pending_instalments
    FROM main_data m
    LEFT JOIN tdt_summary t ON m.acid = t.acid
    WHERE NOT (
        COALESCE(t.pending_instalments, 0) > 24
        AND m.last_repayment_date < (CURRENT_DATE - INTERVAL '1 year')
    )
    GROUP BY m.sol_id, m.sol_desc, m.division_name, m.region_name, m.circle_office_name
    ORDER BY m.sol_id
    """

	conn = get_dr_connection()
	if not conn:
		frappe.log_error("Failed to connect to DR database", "RD SMBG Table API")
		return []

	try:
		cursor = conn.cursor()
		cursor.execute(query)
		rows = cursor.fetchall()

		sol_ids_found = [str(r[0]) for r in rows] if rows else []
		branch_map = {}
		if sol_ids_found:
			sb_data = frappe.get_all(
				"Sahayog Branch",
				filters={"name": ["in", sol_ids_found]},
				fields=["name as sol_id", "zone", "region", "district", "branch"],
			)
			for b in sb_data:
				branch_map[b.sol_id] = {
					"zone": b.zone or "",
					"region": b.region or "",
					"district": b.district or "",
					"branch_name": b.branch or "",
				}

		result = []
		for row in rows:
			sid = str(row[0])
			sb = branch_map.get(sid, {})
			result.append(
				{
					"sol_id": sid,
					"sol_desc": row[1] or "",
					"zone": sb.get("zone", ""),
					"region": sb.get("region", ""),
					"district": sb.get("district", ""),
					"branch_name": sb.get("branch_name", ""),
					"total_accounts": row[5] or 0,
					"total_collection": float(row[6]) if row[6] else 0,
					"pending_accounts": row[7] or 0,
					"pending_amount": float(row[8]) if row[8] else 0,
					"pending_instalments": row[9] or 0,
				}
			)
		return result
	except Exception as e:
		frappe.log_error(
			f"Error executing RD/SMBG table query: {str(e)}", "RD SMBG Table API"
		)
		return []
	finally:
		try:
			conn.close()
		except Exception:
			pass


@frappe.whitelist(allow_guest=True)
def get_mis_filter_options():
	user = frappe.session.user
	perms = get_user_report_permissions(user)

	zones = []
	regions = []
	districts = []

	if perms.get("is_restricted"):
		allowed_zones = perms.get("zones", [])
		allowed_regions = perms.get("regions", [])
		if allowed_zones:
			zones = [
				r[0]
				for r in frappe.db.sql(
					"SELECT DISTINCT zone FROM `tabSahayog Branch` WHERE zone IS NOT NULL AND zone != ''"
				)
			]
			allowed_norm = [
				re.sub(r"[\s\-]+", "", z or "").upper() for z in allowed_zones
			]
			zones = [
				z
				for z in zones
				if re.sub(r"[\s\-]+", "", z or "").upper() in allowed_norm
			]
			regions = [
				r[0]
				for r in frappe.db.sql(
					"SELECT DISTINCT region FROM `tabSahayog Branch` WHERE region IS NOT NULL AND region != ''"
				)
			]
			if allowed_regions:
				allowed_reg_norm = [
					re.sub(r"[\s\-]+", "", r or "").upper() for r in allowed_regions
				]
				regions = [
					r
					for r in regions
					if re.sub(r"[\s\-]+", "", r or "").upper() in allowed_reg_norm
				]
			districts = [
				r[0]
				for r in frappe.db.sql(
					"SELECT DISTINCT district FROM `tabSahayog Branch` WHERE district IS NOT NULL AND district != ''"
				)
			]
		elif perms["sol_ids"]:
			branch_data = frappe.get_all(
				"Sahayog Branch",
				filters={"name": ["in", perms["sol_ids"]]},
				fields=["zone", "region", "district"],
			)
			zones = sorted(set(b.zone for b in branch_data if b.zone))
			regions = sorted(set(b.region for b in branch_data if b.region))
			districts = sorted(set(b.district for b in branch_data if b.district))
		else:
			zones = [
				r[0]
				for r in frappe.db.sql(
					"SELECT DISTINCT zone FROM `tabSahayog Branch` WHERE zone IS NOT NULL AND zone != ''"
				)
			]
			regions = [
				r[0]
				for r in frappe.db.sql(
					"SELECT DISTINCT region FROM `tabSahayog Branch` WHERE region IS NOT NULL AND region != ''"
				)
			]
			districts = [
				r[0]
				for r in frappe.db.sql(
					"SELECT DISTINCT district FROM `tabSahayog Branch` WHERE district IS NOT NULL AND district != ''"
				)
			]
	else:
		zones = [
			r[0]
			for r in frappe.db.sql(
				"SELECT DISTINCT zone FROM `tabSahayog Branch` WHERE zone IS NOT NULL AND zone != ''"
			)
		]
		regions = [
			r[0]
			for r in frappe.db.sql(
				"SELECT DISTINCT region FROM `tabSahayog Branch` WHERE region IS NOT NULL AND region != ''"
			)
		]
		districts = [
			r[0]
			for r in frappe.db.sql(
				"SELECT DISTINCT district FROM `tabSahayog Branch` WHERE district IS NOT NULL AND district != ''"
			)
		]

	fixed_sol_id = None
	allowed_sol_ids = perms.get("sol_ids", [])

	if perms.get("is_restricted") and perms.get("zones"):
		allowed_sol_ids = []
		perms["sol_data"] = []
	else:
		if not allowed_sol_ids:
			employee_sol = frappe.db.get_value(
				"Employee", {"user_id": user}, "sahayog_branch"
			)
			if employee_sol:
				allowed_sol_ids = [employee_sol]
				fixed_sol_id = employee_sol

		if not fixed_sol_id and len(allowed_sol_ids) == 1:
			fixed_sol_id = allowed_sol_ids[0]

	sol_data = perms.get("sol_data", [])
	if not sol_data and allowed_sol_ids:
		sol_data = frappe.get_all(
			"Sahayog Branch",
			filters={"name": ["in", allowed_sol_ids]},
			fields=["name as sol_id", "branch as branch_name"],
			order_by="name asc",
		)
	elif not sol_data:
		sol_data = frappe.get_all(
			"Sahayog Branch",
			fields=["name as sol_id", "branch as branch_name"],
			order_by="name asc",
		)

	return {
		"zones": sorted(zones),
		"regions": sorted(regions),
		"districts": sorted(districts),
		"sol_data": sol_data,
		"permissions": {
			"is_restricted": perms.get("is_restricted", False),
			"allowed_zones": perms.get("zones", []),
			"allowed_regions": perms.get("regions", []),
			"allowed_sol_ids": allowed_sol_ids,
			"fixed_sol_id": fixed_sol_id,
		},
	}
