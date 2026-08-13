# Copyright (c) 2025, Your Organization and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today

# Module Level Constants
EXCLUDED_SOL_IDS = ["1000", "1104", "1059", "1081", "1031"]
FY_MONTHS = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "JAN", "FEB", "MAR"]
ALLOWED_ROLES = ["System Manager", "MIS Admin"]


class TargetVsAchivement(Document):
	"""DocType controller for Target Vs Achivement records."""

	def autoname(self):
		if not self.sol_id or not self.financial_year or not self.type:
			frappe.throw(_("SOL ID, Financial Year and Type are mandatory"))

		doc_type = self.type.upper()

		if doc_type in ("MONTHLY", "YTD"):
			if not self.month:
				frappe.throw(_("Month is mandatory for Monthly and YTD types"))

			self.name = f"{self.sol_id}-{self.financial_year}-{doc_type}-{self.month.upper()}"

		elif doc_type == "YEARLY":
			self.name = f"{self.sol_id}-{self.financial_year}-YEARLY"

		else:
			frappe.throw(_("Invalid target type specified."))

	def validate(self):
		self.check_duplicate()

	def check_duplicate(self):
		filters = {
			"sol_id": self.sol_id,
			"financial_year": self.financial_year,
			"type": self.type,
			"name": ["!=", self.name or ""],
		}
		if self.type in ("Monthly", "YTD") and self.month:
			filters["month"] = self.month

		if frappe.db.exists("Target Vs Achivement", filters):
			frappe.throw(
				_("Target record already exists for SOL ID '{0}', Financial Year '{1}' and Period '{2}'.")
				.format(self.sol_id, self.financial_year, self.month or self.type)
			)


def get_current_financial_year() -> str:
	"""Calculate current financial year (April to March) string, e.g. '2025-2026'."""
	dt = getdate(today())
	if dt.month >= 4:
		return f"{dt.year}-{dt.year + 1}"
	return f"{dt.year - 1}-{dt.year}"


def check_user_access():
	"""Check if current user has System Manager or MIS Admin role."""
	user_roles = frappe.get_roles()
	if not any(role in user_roles for role in ALLOWED_ROLES):
		frappe.throw(
			_("Access Denied: Only MIS Admin and System Manager can access Missing Target functionality."),
			frappe.PermissionError,
		)


@frappe.whitelist()
def get_missing_targets_matrix(financial_year: str = None) -> dict:
	"""Fetch missing targets matrix report aggregated by branch for Monthly, YTD, and Yearly targets."""
	check_user_access()
	if not financial_year:
		financial_year = get_current_financial_year()

	# Fetch available Financial Years
	fys = frappe.db.get_all(
		"Target Vs Achivement",
		fields=["distinct financial_year"],
		order_by="financial_year desc",
	)
	fy_list = [f.financial_year for f in fys if f.financial_year]
	if financial_year not in fy_list:
		fy_list.insert(0, financial_year)

	# Fetch valid branches (excluding Head Office and specified non-store SOL IDs)
	branches = frappe.get_all(
		"Sahayog Branch",
		filters=[
			["sol_id", "not in", EXCLUDED_SOL_IDS],
			["branch", "not like", "%HEAD OFFICE%"],
		],
		fields=["sol_id", "branch", "zone", "region"],
		order_by="sol_id asc",
	)

	# Fetch target records for selected Financial Year
	targets = frappe.get_all(
		"Target Vs Achivement",
		filters={"financial_year": financial_year},
		fields=["sol_id", "type", "month", "target", "name"],
	)

	# Build lookup map: (sol_id, type, month_or_None) -> target_info
	target_map = {}
	for t in targets:
		sol = str(t.sol_id or "").strip()
		ttype = str(t.type or "").strip()
		tmonth = str(t.month or "").strip().upper() if ttype in ("Monthly", "YTD") else None
		target_map[(sol, ttype, tmonth)] = {
			"target": flt(t.target or 0),
			"name": t.name,
		}

	matrix = []
	total_missing = 0
	total_stored = 0

	for b in branches:
		sol = str(b.sol_id or "").strip()
		row_data = {
			"sol_id": sol,
			"branch_name": b.branch or sol,
			"zone": b.zone or "-",
			"region": b.region or "-",
			"months": {},
			"ytd_months": {},
			"yearly": None,
			"missing_count": 0,
			"stored_count": 0,
		}

		# Process Monthly targets (APR to MAR)
		for m in FY_MONTHS:
			entry = target_map.get((sol, "Monthly", m))
			if entry:
				row_data["months"][m] = {"stored": True, "target": entry["target"], "name": entry["name"]}
				row_data["stored_count"] += 1
				total_stored += 1
			else:
				row_data["months"][m] = {"stored": False, "target": 0}
				row_data["missing_count"] += 1
				total_missing += 1

		# Process YTD targets (APR to MAR)
		for m in FY_MONTHS:
			entry_ytd = target_map.get((sol, "YTD", m)) or target_map.get((sol, "YTD", None))
			if entry_ytd:
				row_data["ytd_months"][m] = {"stored": True, "target": entry_ytd["target"], "name": entry_ytd["name"]}
				row_data["stored_count"] += 1
				total_stored += 1
			else:
				row_data["ytd_months"][m] = {"stored": False, "target": 0}
				row_data["missing_count"] += 1
				total_missing += 1

		# Process Yearly target
		entry_y = target_map.get((sol, "Yearly", None))
		if entry_y:
			row_data["yearly"] = {"stored": True, "target": entry_y["target"], "name": entry_y["name"]}
			row_data["stored_count"] += 1
			total_stored += 1
		else:
			row_data["yearly"] = {"stored": False, "target": 0}
			row_data["missing_count"] += 1
			total_missing += 1

		matrix.append(row_data)

	return {
		"financial_year": financial_year,
		"available_fys": fy_list,
		"months": FY_MONTHS,
		"matrix": matrix,
		"summary": {
			"total_branches": len(branches),
			"total_missing": total_missing,
			"total_stored": total_stored,
		},
	}


@frappe.whitelist()
def save_quick_target(sol_id: str, financial_year: str, type: str, month: str = None, target: float = 0) -> dict:
	"""Quick insert or update a Target Vs Achivement record directly from the Missing Targets widget."""
	check_user_access()

	target_val = flt(target)
	if target_val <= 0:
		frappe.throw(_("Target amount must be greater than 0"))

	filters = {
		"sol_id": sol_id,
		"financial_year": financial_year,
		"type": type,
	}
	if type in ("Monthly", "YTD") and month:
		filters["month"] = month

	doc_name = frappe.db.exists("Target Vs Achivement", filters)
	if doc_name:
		doc = frappe.get_doc("Target Vs Achivement", doc_name)
		doc.target = target_val
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({
			"doctype": "Target Vs Achivement",
			"sol_id": sol_id,
			"financial_year": financial_year,
			"type": type,
			"month": month if type in ("Monthly", "YTD") else None,
			"target": target_val,
		})
		doc.insert(ignore_permissions=True)

	return {"status": "success", "name": doc.name, "target": doc.target}
