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


@frappe.whitelist(methods=["POST", "GET"])
def get_bm_checklist_details(name=None, employee_id=None, date=None, sol_id=None):
	"""Fetch existing BM checklist details or initial blank structure with template tasks."""
	doc = None
	if name and frappe.db.exists("BM checklist", name):
		doc = frappe.get_doc("BM checklist", name)
	elif employee_id and date:
		# Check if record already exists for this employee and date
		records = get_bm_checklist_status_for_week(employee_id=employee_id, start_date=date, end_date=date, sol_id=sol_id)
		if records and records.get(str(date)) and records[str(date)].get("name"):
			doc_name = records[str(date)]["name"]
			if frappe.db.exists("BM checklist", doc_name):
				doc = frappe.get_doc("BM checklist", doc_name)

	if doc:
		return {
			"status": "success",
			"is_new": False,
			"doc": doc.as_dict()
		}

	# Create clean new template structure
	resolved_emp_id = employee_id or ""
	emp_name = ""
	designation = ""
	resolved_sol_id = sol_id or ""

	if resolved_emp_id:
		emp_data = frappe.db.get_value("Employee", {"employee_number": resolved_emp_id}, ["name", "employee_name", "designation", "sol_id"], as_dict=True)
		if not emp_data:
			emp_data = frappe.db.get_value("Employee", resolved_emp_id, ["name", "employee_name", "designation", "sol_id"], as_dict=True)
		if emp_data:
			resolved_emp_id = emp_data.name
			emp_name = emp_data.employee_name or ""
			designation = emp_data.designation or ""
			if not resolved_sol_id:
				resolved_sol_id = emp_data.sol_id or ""

	template_tasks = get_bm_template_tasks()
	tasks = []
	for task_subj in template_tasks:
		tasks.append({
			"task": task_subj,
			"is_completed": 0,
			"remark": ""
		})

	new_doc = {
		"name": "",
		"bm_employee_id": resolved_emp_id,
		"name1": emp_name,
		"designation": designation,
		"sol_id": resolved_sol_id,
		"date": str(date or frappe.utils.today()),
		"table_lqft": tasks
	}

	return {
		"status": "success",
		"is_new": True,
		"doc": new_doc
	}


@frappe.whitelist(methods=["POST"])
def save_bm_checklist_doc(data=None):
	"""Save or update BM checklist document from custom UI."""
	if not data:
		data = frappe.form_dict.get("data") or frappe.request.get_data(as_text=True)

	import json
	if isinstance(data, str):
		doc_data = json.loads(data)
	else:
		doc_data = data or {}

	name = doc_data.get("name")
	is_new = not bool(name and frappe.db.exists("BM checklist", name))

	if not is_new:
		doc = frappe.get_doc("BM checklist", name)
		doc.date = doc_data.get("date") or doc.date
		doc.bm_employee_id = doc_data.get("bm_employee_id") or doc.bm_employee_id
		doc.name1 = doc_data.get("name1") or doc.name1
		doc.designation = doc_data.get("designation") or doc.designation
		doc.sol_id = doc_data.get("sol_id") or doc.sol_id

		# Replace / update child table tasks
		doc.set("table_lqft", [])
		for row in doc_data.get("table_lqft", []):
			doc.append("table_lqft", {
				"task": row.get("task", ""),
				"is_completed": 1 if row.get("is_completed") in (1, "1", True) else 0,
				"remark": row.get("remark", "") or ""
			})

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "BM Checklist updated successfully",
			"is_new": False,
			"doc": doc.as_dict()
		}
	else:
		# Check if already exists for this date and emp
		emp_id = doc_data.get("bm_employee_id")
		dt = doc_data.get("date") or frappe.utils.today()
		expected_name = f"{dt}-{emp_id}" if emp_id else f"{dt}"

		if frappe.db.exists("BM checklist", expected_name):
			doc = frappe.get_doc("BM checklist", expected_name)
			doc.set("table_lqft", [])
			for row in doc_data.get("table_lqft", []):
				doc.append("table_lqft", {
					"task": row.get("task", ""),
					"is_completed": 1 if row.get("is_completed") in (1, "1", True) else 0,
					"remark": row.get("remark", "") or ""
				})
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			return {
				"status": "success",
				"message": "BM Checklist updated successfully",
				"is_new": False,
				"doc": doc.as_dict()
			}

		doc = frappe.new_doc("BM checklist")
		doc.date = dt
		doc.bm_employee_id = emp_id
		doc.name1 = doc_data.get("name1")
		doc.designation = doc_data.get("designation")
		doc.sol_id = doc_data.get("sol_id")

		for row in doc_data.get("table_lqft", []):
			doc.append("table_lqft", {
				"task": row.get("task", ""),
				"is_completed": 1 if row.get("is_completed") in (1, "1", True) else 0,
				"remark": row.get("remark", "") or ""
			})

		doc.insert(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"message": "BM Checklist created successfully",
			"is_new": True,
			"doc": doc.as_dict()
		}



