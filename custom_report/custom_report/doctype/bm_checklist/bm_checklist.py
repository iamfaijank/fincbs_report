import frappe
from frappe.model.document import Document


class BMchecklist(Document):
	def before_insert(self):
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

