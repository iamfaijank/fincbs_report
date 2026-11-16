import frappe

def execute():
	"""
	Adds composite index on `tabBranch Category Report` (date, sol_id)
	to optimize daily Sahayog Dashboard queries and eliminate table scans.
	"""
	table = "tabBranch Category Report"
	index_name = "idx_bcr_date_sol_id"

	try:
		indexes = frappe.db.sql(f"SHOW INDEX FROM `{table}` WHERE Key_name = %s", (index_name,))
		if not indexes:
			frappe.db.sql(f"ALTER TABLE `{table}` ADD INDEX `{index_name}` (`date`, `sol_id`)")
	except Exception:
		pass
