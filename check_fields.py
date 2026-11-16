import frappe
try:
    doc = frappe.get_doc("DocType", "Sahayog Branch")
    fields = [f.fieldname for f in doc.fields]
    print(fields)
except Exception as e:
    print(e)
