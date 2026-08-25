import frappe
import json
import re
import hashlib
import inspect
import datetime
from frappe.utils import getdate

no_cache = 1


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	context.csrf_token = csrf_token
	context.site_name = frappe.local.site
	return context


@frappe.whitelist(allow_guest=True)
def get_last_available_date():
	last_date = frappe.db.get_value("DD Tracker Report", {}, "MAX(date)")
	return {"last_date": str(last_date) if last_date else None}


def sahayog_cache(ttl=86400):
	def decorator(func):
		def wrapper(*args, **kwargs):
			sig = inspect.signature(func)
			has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
			has_args = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in sig.parameters.values())
			if has_kwargs:
				filtered_kwargs = kwargs
			else:
				filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
			if has_args:
				filtered_args = args
			else:
				pos_params = [p for p in sig.parameters.values() if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
				filtered_args = args[:len(pos_params)]
			args_str = f"{filtered_args}_{json.dumps(filtered_kwargs, sort_keys=True, default=str)}"
			key_hash = hashlib.md5(args_str.encode('utf-8')).hexdigest()
			cache_key = f"sahayog_cache|{func.__name__}|{key_hash}"
			cached_data = frappe.cache.get_value(cache_key)
			if cached_data is not None:
				return cached_data
			result = func(*filtered_args, **filtered_kwargs)
			if result:
				frappe.cache.set_value(cache_key, result, expires_in_sec=ttl)
			return result
		def clear_cache():
			frappe.cache.delete_keys(f"sahayog_cache|{func.__name__}|*")
		wrapper.clear_cache = clear_cache
		wrapper.__name__ = func.__name__
		wrapper.__doc__ = func.__doc__
		return wrapper
	return decorator


def get_sahayog_branches_cached():
	cache_key = "sahayog_branches_map"
	cached_data = frappe.cache.get_value(cache_key)
	if cached_data:
		return cached_data
	branches = frappe.get_all("Sahayog Branch", fields=["name as sol_id", "branch as branch_name", "zone", "region", "district"])
	branches_map = {}
	for b in branches:
		sol_id = str(b.sol_id or "")
		branches_map[sol_id] = {"sol_id": sol_id, "branch_name": b.branch_name or "", "zone": b.zone or "", "region": b.region or "", "district": b.district or ""}
	frappe.cache.set_value(cache_key, branches_map, expires_in_sec=86400)
	return branches_map


def _build_branch_map(sol_ids):
	branches_map = get_sahayog_branches_cached()
	branch_map = {}
	for sid in sol_ids:
		b = branches_map.get(sid, {})
		branch_map[sid] = {"zone": b.get("zone", "Unknown"), "region": b.get("region", "Unknown"), "district": b.get("district", "Unknown"), "branch_name": b.get("branch_name", sid)}
	return branch_map


def _get_employee_designations(emp_ids):
	designation_map = {}
	if emp_ids:
		employees = frappe.get_all("Employee", filters={"name": ["in", list(emp_ids)]}, fields=["name", "designation"])
		for emp in employees:
			designation_map[emp.name] = emp.designation or ""
	return designation_map


def _extract_emp_id(auth_id):
	if not auth_id or auth_id == "Unknown":
		return None
	digits = re.findall(r'\d+', auth_id)
	if digits:
		try:
			return str(int(''.join(digits)))
		except ValueError:
			return None
	return None


@frappe.whitelist(allow_guest=True)
def get_rd_smbg_pending_table_data():
	import datetime
	ref_date = datetime.date.today().strftime("%Y-%m-%d")

	has_date_records = frappe.db.exists("RD and SMBG Pending", {"date": ref_date})
	if not has_date_records:
		latest_date = frappe.db.sql("SELECT MAX(date) FROM `tabRD and SMBG Pending`")[0][0]
		if latest_date:
			ref_date = str(latest_date)

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
	WHERE `date` = %s
	GROUP BY sol_id, sol_desc
	ORDER BY sol_id
	"""
	detail_query = """
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
	WHERE `date` = %s AND sol_id = %s
	GROUP BY sol_id, rm_id, rm_name, auth_id, auth_role_id
	ORDER BY rm_id
	"""
	try:
		rows = frappe.db.sql(query, (ref_date,), as_dict=True)
		sol_ids_found = [r.sol_id.strip() for r in rows if r.sol_id]
		branch_map = {}
		if sol_ids_found:
			sb_data = frappe.get_all("Sahayog Branch", filters={"name": ["in", sol_ids_found]}, fields=["name as sol_id", "zone", "region", "district", "branch"])
			for b in sb_data:
				branch_map[b.sol_id] = {"zone": b.zone or "", "region": b.region or "", "district": b.district or "", "branch_name": b.branch or ""}
		detail_map = {}
		for sid in sol_ids_found:
			details = frappe.db.sql(detail_query, (ref_date, sid), as_dict=True)
			detail_map[sid] = [{"rm_id": d.rm_id or "", "rm_name": d.rm_name or "", "auth_id": d.auth_id or "", "auth_role_id": d.auth_role_id or "", "total_accounts": d.total_accounts or 0, "total_collection": float(d.total_collection or 0), "pending_accounts": d.pending_accounts or 0, "pending_amount": float(d.pending_amount or 0), "pending_instalments": d.pending_instalments or 0} for d in details]
		result = []
		for r in rows:
			sid = str(r.sol_id).strip()
			sb = branch_map.get(sid, {})
			result.append({"sol_id": sid, "sol_desc": r.sol_desc or "", "zone": sb.get("zone", ""), "region": sb.get("region", ""), "district": sb.get("district", ""), "branch_name": sb.get("branch_name", ""), "total_accounts": r.total_accounts or 0, "total_collection": float(r.total_collection or 0), "pending_accounts": r.pending_accounts or 0, "pending_amount": float(r.pending_amount or 0), "pending_instalments": r.pending_instalments or 0, "details": detail_map.get(sid, [])})
		return result
	except Exception as e:
		frappe.log_error(f"RD/SMBG query error: {str(e)}", "RD SMBG API")
		return []


@frappe.whitelist(allow_guest=True)
def get_bucket_wise_account_mis_data(selected_date=None):
	if not selected_date:
		selected_date = str(datetime.date.today())
	records = frappe.db.get_all("DD Tracker Report", filters={"date": selected_date}, fields=["sol_id", "colle_category", "sma0_count", "sma1_count", "sma2_count", "npa_count"])
	if not records:
		return {"summary": [], "total_records": 0}
	sol_ids = list(set(r.sol_id for r in records if r.sol_id))
	branch_map = _build_branch_map(sol_ids)
	summary = {}
	total_recs = 0
	for r in records:
		sid = r.sol_id
		if not sid:
			continue
		br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
		key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}"
		if key not in summary:
			summary[key] = {"zone": br["zone"], "region": br["region"], "district": br["district"], "sol_id": sid, "sol_desc": br["branch_name"], "Excess": 0, "A": 0, "B": 0, "C": 0, "D": 0, "DEFAULT": 0, "grand_total": 0}
		cat = r.colle_category
		if cat and cat in summary[key]:
			summary[key][cat] += 1
		else:
			if r.sma0_count:
				summary[key]["A"] += r.sma0_count
			elif r.sma1_count:
				summary[key]["B"] += r.sma1_count
			elif r.sma2_count:
				summary[key]["C"] += r.sma2_count
			elif r.npa_count:
				summary[key]["D"] += r.npa_count
			else:
				summary[key]["DEFAULT"] += 1
		summary[key]["grand_total"] += 1
		total_recs += 1
	result = sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))
	return {"summary": result, "total_records": total_recs}


@frappe.whitelist(allow_guest=True)
def get_new_account_report_data(selected_date=None):
	if not selected_date:
		selected_date = str(datetime.date.today())
	dt = getdate(selected_date)
	records = frappe.db.get_all("DD Tracker Report", filters={"date": selected_date}, fields=["sol_id", "auth_id", "auth_name", "amount", "opening_date"])
	if not records:
		return []
	sol_ids = list(set(r.sol_id for r in records if r.sol_id))
	branch_map = _build_branch_map(sol_ids)
	emp_ids = set()
	for r in records:
		eid = _extract_emp_id(r.auth_id)
		if eid:
			emp_ids.add(eid)
	designation_map = _get_employee_designations(emp_ids)
	summary = {}
	for r in records:
		sid = r.sol_id
		if not sid:
			continue
		opn_dt_str = r.opening_date
		is_new = False
		if opn_dt_str:
			try:
				opn_dt = getdate(opn_dt_str)
				if opn_dt.month == dt.month and opn_dt.year == dt.year:
					is_new = True
			except Exception:
				pass
		if not is_new:
			continue
		br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
		auth_id = r.auth_id or "Unknown"
		auth_name = r.auth_name or "Unknown"
		designation = ""
		eid = _extract_emp_id(auth_id)
		if eid:
			designation = designation_map.get(eid) or ""
		key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}||{auth_id}||{auth_name}||{designation}"
		if key not in summary:
			summary[key] = {"zone": br["zone"], "region": br["region"], "district": br["district"], "sol_id": sid, "sol_desc": br["branch_name"], "auth_id": auth_id, "auth_name": auth_name, "designation": designation, "new_ac": 0, "deposit_amount": 0.0}
		summary[key]["new_ac"] += 1
		summary[key]["deposit_amount"] += float(r.amount or 0)
	return sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))


@frappe.whitelist(allow_guest=True)
def get_staff_wise_demand_collection_data(selected_date=None):
	if not selected_date:
		selected_date = str(datetime.date.today())
	records = frappe.db.get_all("DD Tracker Report", filters={"date": selected_date}, fields=["sol_id", "auth_id", "auth_name", "monthly_demand", "monthly_collection"])
	if not records:
		return []
	sol_ids = list(set(r.sol_id for r in records if r.sol_id))
	branch_map = _build_branch_map(sol_ids)
	emp_ids = set()
	for r in records:
		eid = _extract_emp_id(r.auth_id)
		if eid:
			emp_ids.add(eid)
	designation_map = _get_employee_designations(emp_ids)
	summary = {}
	for r in records:
		sid = r.sol_id
		if not sid:
			continue
		br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
		auth_id = r.auth_id or "Unknown"
		auth_name = r.auth_name or "Unknown"
		designation = ""
		eid = _extract_emp_id(auth_id)
		if eid:
			designation = designation_map.get(eid) or ""
		key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}||{auth_id}||{auth_name}||{designation}"
		if key not in summary:
			summary[key] = {"zone": br["zone"], "region": br["region"], "district": br["district"], "sol_id": sid, "sol_desc": br["branch_name"], "auth_id": auth_id, "auth_name": auth_name, "designation": designation, "monthly_demand_amount": 0.0, "monthly_collection": 0.0}
		summary[key]["monthly_demand_amount"] += float(r.monthly_demand or 0)
		summary[key]["monthly_collection"] += float(r.monthly_collection or 0)
	return sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))


@frappe.whitelist(allow_guest=True)
def get_agent_wise_demand_collection_data(selected_date=None):
	if not selected_date:
		selected_date = str(datetime.date.today())
	records = frappe.db.get_all("DD Tracker Report", filters={"date": selected_date}, fields=["sol_id", "agent_code", "agent_name", "monthly_demand", "monthly_collection"])
	if not records:
		return []
	sol_ids = list(set(r.sol_id for r in records if r.sol_id))
	branch_map = _build_branch_map(sol_ids)
	summary = {}
	for r in records:
		sid = r.sol_id
		if not sid:
			continue
		br = branch_map.get(sid, {"zone": "Unknown", "region": "Unknown", "district": "Unknown", "branch_name": sid})
		rm_id = r.agent_code or "Unknown"
		rm_name = r.agent_name or "Unknown"
		key = f"{br['zone']}||{br['region']}||{br['district']}||{sid}||{rm_id}||{rm_name}"
		if key not in summary:
			summary[key] = {"zone": br["zone"], "region": br["region"], "district": br["district"], "sol_id": sid, "sol_desc": br["branch_name"], "rm_id": rm_id, "rm_name": rm_name, "monthly_demand_amount": 0.0, "monthly_collection": 0.0}
		summary[key]["monthly_demand_amount"] += float(r.monthly_demand or 0)
		summary[key]["monthly_collection"] += float(r.monthly_collection or 0)
	return sorted(summary.values(), key=lambda x: (x["zone"], x["region"], x["district"], x["sol_id"]))
