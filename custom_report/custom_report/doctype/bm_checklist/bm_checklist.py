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
	"""Fetch mapping of dates to BM checklist records strictly for the specified BM employee."""
	if not employee_id and not sol_id:
		return {}

	emp_names = []
	if employee_id:
		clean_emp = str(employee_id).strip()
		emp_names.append(clean_emp)
		emp_doc = frappe.db.get_value("Employee", {"employee_number": clean_emp}, "name")
		if emp_doc and emp_doc not in emp_names:
			emp_names.append(emp_doc)
		emp_num = frappe.db.get_value("Employee", {"name": clean_emp}, "employee_number")
		if emp_num and emp_num not in emp_names:
			emp_names.append(emp_num)

	conditions = []
	values = []

	if emp_names:
		# Strictly filter by this BM's employee identity only
		conditions.append("bm_employee_id IN ({})".format(", ".join(["%s"] * len(emp_names))))
		values.extend(emp_names)
		if sol_id:
			conditions.append("sol_id = %s")
			values.append(str(sol_id).strip())
	elif sol_id:
		conditions.append("sol_id = %s")
		values.append(str(sol_id).strip())

	if start_date and end_date:
		conditions.append("date BETWEEN %s AND %s")
		values.extend([start_date, end_date])

	where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
	query = f"""
		SELECT name, date, bm_employee_id, sol_id, docstatus
		FROM `tabBM checklist`
		{where_clause}
		ORDER BY creation DESC
	"""
	records = frappe.db.sql(query, values, as_dict=True)

	status_map = {}
	for r in records:
		d_str = str(r.date)
		if d_str not in status_map:
			status_map[d_str] = {
				"name": r.name,
				"docstatus": r.docstatus,
				"bm_employee_id": r.bm_employee_id,
				"sol_id": r.sol_id,
				"exists": True
			}

	return status_map


