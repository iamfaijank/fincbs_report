import frappe
from frappe.utils import getdate


@frappe.whitelist()
def search_branches(txt):
    if not txt:
        return []

    return frappe.db.get_list(
        "Sahayog Branch",
        filters={
            "sol_id": ["like", f"%{txt}%"],
        },
        fields=["name", "sol_id", "branch"],
        limit_page_length=10,
    )


@frappe.whitelist()
def get_branch_data(sol_id):
    return frappe.db.get_list(
        "Sahayog Branch",
        filters={"sol_id": sol_id},
        fields=[
            "name",
            "sol_id",
            "branch",
            "state",
            "state_code",
            "district",
            "zone",
            "region",
            "email",
            "address",
        ],
        limit_page_length=1,
    )


@frappe.whitelist()
def get_branch_profile_data(sol_id):
    """
    Fetch Branch Profile Data based on SOL ID
    """
    data = frappe.db.get_list(
        "Branch Profile Data",
        filters={"sol_id": sol_id},
        fields="*",
        limit_page_length=1,
    )
    return data[0] if data else {}


@frappe.whitelist()
def get_performance_data(sol_id, date):
    """
    ✅ UPDATED: Returns data_exists + latest_date for perfect frontend integration
    """
    try:
        frappe.logger().info(f"Fetching performance data for SOL: {sol_id}, Date: {date}")
        
        # 1. ✅ EXACT DATE MATCH CHECK (priority 1)
        branch_category_data = frappe.db.get_list(
            "Branch Category Report",
            filters={
                "sol_id": sol_id,
                "date": date  # Exact date match
            },
            fields=["name", "sol_id", "date", "achievement", "yearly_achievement"],
            limit_page_length=1,
        )
        
        # 2. ✅ If exact date data exists → return full data
        if branch_category_data:
            monthly_achievement = float(branch_category_data[0].get("achievement", 0) or 0)
            yearly_achievement = float(branch_category_data[0].get("yearly_achievement", 0) or 0)
            
            # Get targets
            fiscal_year = get_fiscal_year(date)
            targets = get_targets(sol_id, fiscal_year)
            
            return {
                "data_exists": True,  # ✅ Frontend expects this
                "monthly_achievement": monthly_achievement,
                "monthly_target": targets.get("monthly", 0),
                "yearly_achievement": yearly_achievement,
                "yearly_target": targets.get("yearly", 0),
                "ytd_target": targets.get("ytd", targets.get("ytd ", 0)),
                "selected_date": date,
                "financial_year": fiscal_year,
            }
        
        # 3. ✅ NO EXACT DATE DATA → Find latest available date
        latest_record = frappe.db.sql("""
            SELECT date, achievement, yearly_achievement 
            FROM `tabBranch Category Report`
            WHERE sol_id = %s 
            ORDER BY date DESC 
            LIMIT 1
        """, (sol_id,), as_dict=1)
        
        if latest_record:
            latest_date = latest_record[0].date
            frappe.logger().info(f"Latest data found for {sol_id}: {latest_date}")
            
            return {
                "data_exists": False,  # ✅ Frontend expects this
                "latest_date": latest_date.strftime('%Y-%m-%d'),  # ✅ YYYY-MM-DD format
            }
        
        # 4. ✅ NO DATA AT ALL for this branch
        return {
            "data_exists": False,
            "latest_date": None
        }
        
    except Exception as e:
        frappe.log_error(
            title="Branch Performance Data Error",
            message=f"SOL: {sol_id}, Date: {date}, Error: {str(e)}"
        )
        return {
            "data_exists": False,
            "latest_date": None,
            "error": str(e)
        }


# ✅ HELPER FUNCTIONS
def get_fiscal_year(date_str):
    """Calculate Indian Financial Year (Apr 1 - Mar 31)"""
    date_obj = getdate(date_str)
    year = date_obj.year
    month = date_obj.month
    
    if month >= 4:  # April onwards
        return f"{year}-{year+1}"
    else:  # Jan-Mar
        return f"{year-1}-{year}"


def get_targets(sol_id, fiscal_year):
    """Get targets from Target Vs Achievement"""
    target_data = frappe.db.sql("""
        SELECT type, target 
        FROM `tabTarget Vs Achivement`
        WHERE sol_id = %s AND financial_year = %s
    """, (sol_id, fiscal_year), as_dict=1)
    
    targets = {}
    for item in target_data:
        type_key = item.type.lower().strip()
        targets[type_key] = float(item.target or 0)
    
    return targets
