# Copyright (c) 2026, atul and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard import (
    get_agent_wise_demand_collection_data,
    get_staff_wise_demand_collection_data
)

class DDTrackerReport(Document):
	pass

def daily_sync_dd_tracker():
    sync_enabled = frappe.db.get_single_value("Drishti Settings", "auto_sync")
    if not sync_enabled:
        frappe.logger("scheduler").info("Daily DD Tracker Sync: Sync is disabled in Drishti Settings. Skipping execution.")
        return

    from frappe.utils import add_days, today
    yesterday = add_days(today(), -1)
    frappe.log_error("Starting Daily DD Tracker Sync for: " + yesterday, "DD Tracker Sync")
    try:
        result = sync_dd_tracker_data(yesterday)
        total = result.get("total", 0) if isinstance(result, dict) else 0
        success_msg = f"Successfully synced DD Tracker for: {yesterday}. Total Records: {total}"
        frappe.log_error(success_msg, "DD Tracker Sync")
        
        # Send Email on Success
        frappe.sendmail(
            recipients=["talib.s@sahayogmultistate.com", "atul.n@sahayogmultistate.com"],
            subject=f"✅ DD Tracker Sync Successful - {yesterday}",
            message=f"<p>Hello,</p><p>The daily DD Tracker data sync for <b>{yesterday}</b> has completed successfully.</p><p>Total Records Synced: <b>{total}</b></p>"
        )
    except Exception as e:
        error_msg = f"Failed to sync DD Tracker: {str(e)}"
        frappe.log_error(error_msg, "DD Tracker Sync Error")
        
        # Send Email on Failure
        frappe.sendmail(
            recipients=["talib.s@sahayogmultistate.com", "atul.n@sahayogmultistate.com"],
            subject=f"❌ DD Tracker Sync Failed - {yesterday}",
            message=f"<p>Hello,</p><p>The daily DD Tracker data sync for <b>{yesterday}</b> encountered an error:</p><pre>{str(e)}</pre>"
        )

from custom_report.custom_report.page.sahayog_dashboard.sahayog_dashboard import get_raw_demand_collection_data

@frappe.whitelist()
def sync_dd_tracker_data(sync_date):
    # Fetch RAW Data (ungrouped)
    raw_data = get_raw_demand_collection_data(sync_date)
    
    # Delete existing data for the same date to avoid duplicates
    frappe.db.delete("DD Tracker Report", {"date": sync_date})
    
    from frappe.utils import now
    
    # Process Raw Data for Bulk Insert
    fields = [
        "name", "creation", "modified", "modified_by", "owner", "docstatus",
        "date", "sol_id", "agent_code", "agent_name", "auth_id", "auth_name",
        "monthly_demand", "monthly_collection", "account_number", "customer_name",
        "opening_date", "product", "amount", "regular_count", "sma0_count",
        "sma1_count", "sma2_count", "npa_count", "total_count", "colle_category"
    ]
    
    values = []
    now_str = now()
    
    if raw_data:
        for row in raw_data:
            cat = row.get("colle_category") or "DEFAULT"
            values.append((
                frappe.generate_hash(length=10),  # name
                now_str,  # creation
                now_str,  # modified
                frappe.session.user if getattr(frappe.session, "user", None) else "Administrator",  # modified_by
                frappe.session.user if getattr(frappe.session, "user", None) else "Administrator",  # owner
                0,        # docstatus
                sync_date,
                row.get("sol_id") or "",
                row.get("rm_id") or "",
                row.get("rm_name") or "",
                row.get("auth_id") or "",
                row.get("auth_name") or "",
                row.get("monthly_demand_amount") or 0.0,
                row.get("total_tran_amt") or row.get("total_flow_amount") or 0.0,
                row.get("foracid") or "",
                row.get("cif_id") or "",
                row.get("acct_opn_date"),
                row.get("schm_code") or "",
                row.get("deposit_amount") or 0.0,
                1 if cat == "Regular" else 0,
                1 if cat == "A" else 0,
                1 if cat == "B" else 0,
                1 if cat == "C" else 0,
                1 if cat == "D" else 0,
                1,
                cat
            ))
            
    total_records = len(values)
    
    if total_records > 0:
        frappe.publish_realtime("progress", {"progress": 10, "title": "Syncing DD Tracker", "description": f"Inserting {total_records} records directly..."}, user=frappe.session.user)
        
        chunk_size = 5000
        for i in range(0, total_records, chunk_size):
            chunk = values[i:i + chunk_size]
            frappe.db.bulk_insert(
                "DD Tracker Report",
                fields=fields,
                values=chunk,
                ignore_duplicates=True
            )
            progress = int(((i + len(chunk)) / total_records) * 100)
            frappe.publish_realtime("progress", {"progress": progress, "title": "Syncing DD Tracker", "description": f"Inserted {i + len(chunk)} of {total_records} records"}, user=frappe.session.user)
            
        frappe.db.commit()
        
    return {"status": "Success", "total": total_records}
