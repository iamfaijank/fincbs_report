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
