# Copyright (c) 2026, atul and contributors
# For license information, see license.txt

"""Shared read helpers for the RD & SMBG Pending report.

Kept in one place so the Sahayog MIS API and the BDE/BDO dashboard use the
same date resolution and aggregation SQL instead of duplicating (and, in the
BDE case, running one query per branch).
"""

import frappe
from frappe.utils import getdate, nowdate

# SMBG (schm_code 2016) is intentionally excluded from every report read.
SCHM_EXCLUDE_FILTER = "(schm_code IS NULL OR schm_code != '2016')"


def resolve_target_date(preferred=None):
	"""Return the newest date that actually has data (never later than `preferred`).

	Uses a single query. Falls back to the overall MAX(date) only when
	`preferred` predates every stored row (mirrors the old exists() + MAX(date)
	behaviour without paying for two scans on every request).
	"""
	ref_date = getdate(preferred) if preferred else getdate(nowdate())

	latest = frappe.db.sql(
		"SELECT MAX(`date`) FROM `tabRD and SMBG Pending` WHERE `date` <= %s",
		(ref_date,),
	)[0][0]
	if latest:
		return str(latest)

	latest = frappe.db.sql("SELECT MAX(`date`) FROM `tabRD and SMBG Pending`")[0][0]
	return str(latest) if latest else str(ref_date)


def get_sol_summary(target_date, sol_ids=None):
	"""One aggregate query: per-branch account / collection / pending figures."""
	conditions = ["`date` = %s", SCHM_EXCLUDE_FILTER]
	values = [str(target_date)]

	if sol_ids:
		if isinstance(sol_ids, str):
			sol_list = [s.strip() for s in sol_ids.split(",") if s.strip()]
		else:
			sol_list = [str(s).strip() for s in (sol_ids or []) if str(s).strip()]
		if sol_list:
			conditions.append("`sol_id` IN ({})".format(",".join(["%s"] * len(sol_list))))
			values.extend(sol_list)

	query = """
		SELECT
			sol_id,
			sol_desc,
			COUNT(*) AS total_accounts,
			COALESCE(SUM(total_instalment_paid), 0) AS total_collection,
			COALESCE(SUM(CASE WHEN pending_amount > 0 THEN 1 ELSE 0 END), 0) AS pending_accounts,
			COALESCE(SUM(pending_amount), 0) AS pending_amount,
			COALESCE(SUM(pending_instalments), 0) AS pending_instalments
		FROM `tabRD and SMBG Pending`
		WHERE {}
		GROUP BY sol_id, sol_desc
		ORDER BY sol_id
	""".format(" AND ".join(conditions))

	return frappe.db.sql(query, tuple(values), as_dict=True)


def get_rm_details(target_date):
	"""One grouped query for the per-authorizer breakdown, keyed by sol_id.

	Replaces the previous per-branch detail queries (200+ round trips that each
	scanned the full table).
	"""
	query = """
		SELECT
			sol_id,
			rm_id,
			rm_name,
			auth_id,
			auth_role_id,
			COUNT(*) AS total_accounts,
			COALESCE(SUM(total_instalment_paid), 0) AS total_collection,
			COALESCE(SUM(CASE WHEN pending_amount > 0 THEN 1 ELSE 0 END), 0) AS pending_accounts,
			COALESCE(SUM(pending_amount), 0) AS pending_amount,
			COALESCE(SUM(pending_instalments), 0) AS pending_instalments
		FROM `tabRD and SMBG Pending`
		WHERE `date` = %s AND {exclude}
		GROUP BY sol_id, rm_id, rm_name, auth_id, auth_role_id
		ORDER BY rm_id
	""".format(exclude=SCHM_EXCLUDE_FILTER)

	rows = frappe.db.sql(query, (str(target_date),), as_dict=True)

	detail_map = {}
	for d in rows:
		sid = str(d.sol_id or "").strip()
		detail_map.setdefault(sid, []).append({
			"rm_id": d.rm_id or "",
			"rm_name": d.rm_name or "",
			"auth_id": d.auth_id or "",
			"auth_role_id": d.auth_role_id or "",
			"total_accounts": d.total_accounts or 0,
			"total_collection": float(d.total_collection or 0),
			"pending_accounts": d.pending_accounts or 0,
			"pending_amount": float(d.pending_amount or 0),
			"pending_instalments": d.pending_instalments or 0
		})
	return detail_map
