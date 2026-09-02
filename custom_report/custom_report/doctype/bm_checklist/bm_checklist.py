import frappe
from frappe.model.document import Document


class BMchecklist(Document):
	def autoname(self):
		date_str = str(self.date or frappe.utils.today())
		emp_id = str(self.bm_employee_id or "").strip()
		base_name = f"{date_str}-{emp_id}" if emp_id else f"{date_str}"

		if not frappe.db.exists("BM checklist", base_name):
			self.name = base_name
		else:
			count = frappe.db.count("BM checklist", filters={"name": ["like", f"{base_name}%"]})
			self.name = f"{base_name}-{count + 1}"

	def before_insert(self):
		if not self.date:
			self.date = frappe.utils.today()
		self.populate_default_tasks()

	def populate_default_tasks(self):
		if not self.get("table_lqft"):
			tasks = get_bm_template_tasks()
			for task_subject in tasks:
				self.append("table_lqft", {
					"task": task_subject,
					"is_completed": 0,
					"remark": ""
				})


@frappe.whitelist()
def get_bm_template_tasks():
	"""Fetch unique task subjects from Project Template 'BM'."""
	if not frappe.db.exists("Project Template", "BM"):
		return []

	template = frappe.get_doc("Project Template", "BM")
	tasks = []
	seen = set()

	for row in template.get("tasks", []):
		subject = (row.subject or "").strip()
		if not subject and row.task:
			subject = frappe.db.get_value("Task", row.task, "subject") or ""
			subject = subject.strip()

		if subject and subject.lower() not in seen:
			seen.add(subject.lower())
			tasks.append(subject)

	return tasks


@frappe.whitelist(methods=["POST", "GET"], allow_guest=True)
def get_bm_checklist_status_for_week(employee_id=None, start_date=None, end_date=None, sol_id=None):
	"""Fetch mapping of dates to BM checklist records for an employee or branch."""
	if not employee_id and sol_id:
		from custom_report.branch_v1 import get_bm_details_from_employee
		bm_res = get_bm_details_from_employee(sol_id)
		if bm_res and bm_res.get("data") and len(bm_res["data"]) > 0:
			first_bm = bm_res["data"][0]
			employee_id = first_bm.get("name") or first_bm.get("employee_number")

	if not employee_id and not sol_id:
		return {}

	filters = []
	if employee_id:
		emp_names = [employee_id]
		emp_doc = frappe.db.get_value("Employee", {"employee_number": employee_id}, "name")
		if emp_doc and emp_doc not in emp_names:
			emp_names.append(emp_doc)
		filters.append(["bm_employee_id", "in", emp_names])
	elif sol_id:
		filters.append(["sol_id", "=", sol_id])

	if start_date and end_date:
		filters.append(["date", "between", [start_date, end_date]])

	records = frappe.get_all(
		"BM checklist",
		filters=filters,
		fields=["name", "date", "bm_employee_id", "docstatus"]
	)

	status_map = {}
	for r in records:
		d_str = str(r.date)
		status_map[d_str] = {
			"name": r.name,
			"docstatus": r.docstatus,
			"exists": True
		}

	return status_map


