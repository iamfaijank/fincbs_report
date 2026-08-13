# Copyright (c) 2025, Your Organization and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TargetVsAchivement(Document):
	def autoname(self):
		if not self.sol_id or not self.financial_year or not self.type:
			frappe.throw(_("SOL ID, Financial Year and Type are mandatory"))

		doc_type = self.type.upper()

		if doc_type == "MONTHLY":
			if not self.month:
				frappe.throw(_("Month is mandatory for Monthly type"))

			self.name = f"{self.sol_id}-{self.financial_year}-MONTHLY-{self.month.upper()}"

		elif doc_type in ("YEARLY", "YTD"):
			self.name = f"{self.sol_id}-{self.financial_year}-{doc_type}"

		else:
			frappe.throw(_("Invalid type"))

	def validate(self):
		self.check_duplicate()

	def check_duplicate(self):
		filters = {
			"sol_id": self.sol_id,
			"financial_year": self.financial_year,
			"type": self.type,
			"name": ["!=", self.name or ""],
		}
		if self.type == "Monthly" and self.month:
			filters["month"] = self.month

		existing = frappe.db.exists("Target Vs Achivement", filters)
		if existing:
			frappe.throw(
				_("Target record already exists for this SOL ID, Financial Year and Period.")
			)


@frappe.whitelist()
def get_missing_targets_matrix(financial_year=None):
	if not financial_year:
		today_dt = frappe.utils.today()
		dt = frappe.utils.getdate(today_dt)
		if dt.month >= 4:
			financial_year = f"{dt.year}-{dt.year + 1}"
		else:
			financial_year = f"{dt.year - 1}-{dt.year}"

	# Available Financial Years list
	fys = frappe.db.get_all(
		"Target Vs Achivement",
		fields=["distinct financial_year"],
		order_by="financial_year desc",
	)
	fy_list = [f.financial_year for f in fys if f.financial_year]
	if financial_year not in fy_list:
		fy_list.insert(0, financial_year)

	# Fetch all branches from Sahayog Branch
	branches = frappe.get_all(
		"Sahayog Branch",
		fields=["sol_id", "branch_name", "zone", "region"],
		order_by="sol_id asc",
	)

	# Month list in FY sequence: Apr to Mar
	months = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC", "JAN", "FEB", "MAR"]

	# Fetch all targets for selected FY
	targets = frappe.get_all(
		"Target Vs Achivement",
		filters={"financial_year": financial_year},
		fields=["sol_id", "type", "month", "target", "name"],
	)

	# Map: (sol_id, type, month_or_None) -> target_info
	target_map = {}
	for t in targets:
		sol = str(t.sol_id or "").strip()
		ttype = str(t.type or "").strip()
		tmonth = str(t.month or "").strip().upper() if ttype == "Monthly" else None
		target_map[(sol, ttype, tmonth)] = {
			"target": float(t.target or 0),
			"name": t.name,
		}

	matrix = []
	total_missing = 0
	total_stored = 0

	for b in branches:
		sol = str(b.sol_id or "").strip()
		row_data = {
			"sol_id": sol,
			"branch_name": b.branch_name or sol,
			"zone": b.zone or "-",
			"region": b.region or "-",
			"months": {},
			"yearly": None,
			"ytd": None,
			"missing_count": 0,
			"stored_count": 0,
		}

		# Monthly targets (Apr to Mar)
		for m in months:
			entry = target_map.get((sol, "Monthly", m))
			if entry:
				row_data["months"][m] = {"stored": True, "target": entry["target"], "name": entry["name"]}
				row_data["stored_count"] += 1
				total_stored += 1
			else:
				row_data["months"][m] = {"stored": False, "target": 0}
				row_data["missing_count"] += 1
				total_missing += 1

		# Yearly target
		entry_y = target_map.get((sol, "Yearly", None))
		if entry_y:
			row_data["yearly"] = {"stored": True, "target": entry_y["target"], "name": entry_y["name"]}
			row_data["stored_count"] += 1
			total_stored += 1
		else:
			row_data["yearly"] = {"stored": False, "target": 0}
			row_data["missing_count"] += 1
			total_missing += 1

		# YTD target
		entry_ytd = target_map.get((sol, "YTD", None))
		if entry_ytd:
			row_data["ytd"] = {"stored": True, "target": entry_ytd["target"], "name": entry_ytd["name"]}
			row_data["stored_count"] += 1
			total_stored += 1
		else:
			row_data["ytd"] = {"stored": False, "target": 0}
			row_data["missing_count"] += 1
			total_missing += 1

		matrix.append(row_data)

	return {
		"financial_year": financial_year,
		"available_fys": fy_list,
		"months": months,
		"matrix": matrix,
		"summary": {
			"total_branches": len(branches),
			"total_missing": total_missing,
			"total_stored": total_stored,
		},
	}
