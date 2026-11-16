import frappe
import re

def clean_value(val, prefix):
    if not val:
        return "Unknown"
    val_str = str(val).strip().upper()
    digits = re.sub(r"[^0-9]", "", val_str)
    if digits:
        return f"{prefix}-{digits}"
    else:
        return re.sub(r"[\s\-]+", " ", val_str).strip()

def execute():
    # Fetch all records with name, zone, region
    records = frappe.db.get_all("Product Wise Report", fields=["name", "zone", "region"])
    
    for r in records:
        cleaned_zone = clean_value(r.get("zone"), "ZONE")
        cleaned_region = clean_value(r.get("region"), "REGION")
        
        if cleaned_zone != r.get("zone") or cleaned_region != r.get("region"):
            frappe.db.set_value(
                "Product Wise Report",
                r["name"],
                {
                    "zone": cleaned_zone,
                    "region": cleaned_region
                },
                update_modified=False
            )
    
    frappe.db.commit()
