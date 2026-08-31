import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now, flt
import csv
import io
import json


@frappe.whitelist()
def fast_import_product_wise_report(file_url=None, raw_data=None):
	"""
	Superfast bulk import for Product Wise Report bypassing ORM overhead.
	Supports reading directly from uploaded CSV/Excel or JSON payload in chunks of 5000.
	"""
	if not file_url and not raw_data:
		frappe.throw("No file or data provided for import.")

	records_to_insert = []
	current_user = frappe.session.user
	now_str = now()

	# Map of column headers (case-insensitive / label / fieldname) to fieldnames
	header_field_map = {
		"date": "date",
		"sol id": "sol_id",
		"sol_id": "sol_id",
		"solid": "sol_id",
		"zone": "zone",
		"region": "region",
		"product": "product",
		"scheme code": "scheme_code",
		"scheme_code": "scheme_code",
		"schemecode": "scheme_code",
		"total tran amount": "amount",
		"total_tran_amount": "amount",
		"amount": "amount"
	}

	# 1. Parse Data
	rows = []
	if file_url:
		file_doc = frappe.get_doc("File", {"file_url": file_url})
		file_content = file_doc.get_content()
		filename = file_doc.file_name.lower() if file_doc.file_name else ""

		if filename.endswith(".csv"):
			if isinstance(file_content, bytes):
				file_content = file_content.decode("utf-8-sig", errors="ignore")
			csv_reader = csv.DictReader(io.StringIO(file_content))
			for r in csv_reader:
				rows.append(r)
		elif filename.endswith(".xlsx") or filename.endswith(".xls"):
			import openpyxl
			wb = openpyxl.load_workbook(filename=io.BytesIO(file_content), data_only=True)
			sheet = wb.active
			headers = []
			for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
				if row_idx == 0:
					headers = [str(c).strip() if c is not None else "" for c in row]
				else:
					if not any(row):
						continue
					row_dict = {}
					for col_idx, val in enumerate(row):
						if col_idx < len(headers) and headers[col_idx]:
							row_dict[headers[col_idx]] = val
					rows.append(row_dict)
		else:
			frappe.throw("Unsupported file format. Please upload a .csv or .xlsx file.")
	elif raw_data:
		if isinstance(raw_data, str):
			rows = json.loads(raw_data)
		else:
			rows = raw_data

	if not rows:
		frappe.throw("No valid rows found to import.")

	# Pre-fetch Product group_name map for auto-populating `product` from scheme_code if missing
	product_group_map = {}
	try:
		products = frappe.get_all("Product", fields=["name", "group_name"])
		for p in products:
			product_group_map[str(p.name).strip().upper()] = p.group_name
	except Exception:
		pass

	# Pre-fetch Branch Master for auto-populating zone/region from sol_id if missing
	sol_branch_map = {}
	try:
		branches = frappe.get_all("Branch Master", fields=["sol_id", "zone", "region"])
		for b in branches:
			if b.sol_id:
				sol_branch_map[str(b.sol_id).strip()] = b
	except Exception:
		pass

	count = 0
	for row in rows:
		# Normalize keys in row
		normalized_row = {}
		for k, v in row.items():
			if k:
				clean_k = str(k).strip().lower().replace("_", " ")
				if clean_k in header_field_map:
					normalized_row[header_field_map[clean_k]] = v
				else:
					clean_k_slug = str(k).strip().lower()
					if clean_k_slug in header_field_map:
						normalized_row[header_field_map[clean_k_slug]] = v

		# Extract values
		raw_date = normalized_row.get("date")
		if not raw_date:
			continue
		try:
			date_val = str(getdate(raw_date))
		except Exception:
			continue

		sol_id = str(normalized_row.get("sol_id") or "").strip()
		zone = str(normalized_row.get("zone") or "").strip()
		region = str(normalized_row.get("region") or "").strip()
		scheme_code = str(normalized_row.get("scheme_code") or "").strip()
		product = str(normalized_row.get("product") or "").strip()
		amount = flt(normalized_row.get("amount") or 0)

		# Auto-fill missing zone/region if SOL ID available
		if sol_id and (not zone or not region) and sol_id in sol_branch_map:
			b_info = sol_branch_map[sol_id]
			if not zone:
				zone = b_info.get("zone") or ""
			if not region:
				region = b_info.get("region") or ""

		# Auto-fill product from scheme_code if missing
		if scheme_code and not product and scheme_code.upper() in product_group_map:
			product = product_group_map[scheme_code.upper()]

		# Generate unique name / hash
		name = frappe.generate_hash(length=10)

		records_to_insert.append((
			name, now_str, now_str, current_user, current_user, 0, 0,
			zone, region, product, amount, date_val, sol_id, scheme_code
		))
		count += 1

	if not records_to_insert:
		frappe.throw("No matching rows could be parsed. Check column headers.")

	# Batch Bulk Insert using raw SQL chunks
	chunk_size = 5000
	db_type = getattr(frappe.db, "db_type", "mariadb")
	row_placeholder = "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

	for i in range(0, len(records_to_insert), chunk_size):
		chunk = records_to_insert[i : i + chunk_size]
		placeholders = ", ".join([row_placeholder] * len(chunk))
		flattened_params = [val for r in chunk for val in r]

		if db_type == "mariadb":
			sql = f"""
			INSERT INTO `tabProduct Wise Report` (
				`name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus`, `idx`,
				`zone`, `region`, `product`, `amount`, `date`, `sol_id`, `scheme_code`
			) VALUES {placeholders};
			"""
		else:
			sql = f"""
			INSERT INTO "tabProduct Wise Report" (
				"name", "creation", "modified", "modified_by", "owner", "docstatus", "idx",
				"zone", "region", "product", "amount", "date", "sol_id", "scheme_code"
			) VALUES {placeholders};
			"""
		frappe.db.sql(sql, flattened_params)

	frappe.db.commit()
	return count
