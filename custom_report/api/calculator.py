import frappe
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from custom_report.db_connection import get_dr_connection

# Excel Rules Configuration
# penalty_slabs: (up_to_month, charge_percent)
# interest_slabs: (from_month, to_month, interest_rate)
SCHEME_RULES = {
    "2010": {
        "name": "RD 12M",
        "tenure_m": 12, "base_rate": 8.0, 
        "penalty_slabs": [(3, 6.0), (6, 4.0)], # 3m tak 6%, 3-6m 4%
        "interest_slabs": [(6, 9, 4.0), (9, 12, 6.0)]
    },
    "2011": {
        "name": "RD 24M",
        "tenure_m": 24, "base_rate": 8.0, 
        "penalty_slabs": [(6, 6.0), (12, 4.0)], 
        "interest_slabs": [(12, 18, 4.0), (18, 24, 6.0)]
    },
    "2012": {
        "name": "RD 36M",
        "tenure_m": 36, "base_rate": 8.0, 
        "penalty_slabs": [(9, 6.0), (18, 4.0)], 
        "interest_slabs": [(18, 27, 4.0), (27, 36, 6.0)]
    },
    "2013": {
        "name": "RD 48M",
        "tenure_m": 48, "base_rate": 8.0, 
        "penalty_slabs": [(12, 6.0), (24, 4.0)], 
        "interest_slabs": [(24, 36, 4.0), (36, 48, 6.0)]
    },
    "2014": {
        "name": "RD 60M",
        "tenure_m": 60, "base_rate": 8.0, 
        "penalty_slabs": [(15, 6.0), (30, 4.0)], 
        "interest_slabs": [(30, 45, 4.0), (45, 60, 6.0)]
    },
    "2015": {
        "name": "RD 60M",
        "tenure_m": 60, "base_rate": 8.0, 
        "penalty_slabs": [(15, 6.0), (30, 4.0)], 
        "interest_slabs": [(30, 45, 4.0), (45, 60, 6.0)]
    },
    "2005": {
        "name": "SMBG",
        "tenure_m": 66, "base_rate": 8.0, 
        "penalty_slabs": [(999, 1.8)], # Fixed 1.8% service charge 
        "interest_slabs": [(36, 66, 6.0)] # Only if > 3 years
    },
    "2016": {
        "name": "RD 120M",
        "tenure_m": 120, "base_rate": 8.0, 
        "penalty_slabs": [], 
        "interest_slabs": [(0, 120, 8.0)]
    }
}

def get_applicable_rules(schm_code, months_held):
    rule = SCHEME_RULES.get(str(schm_code))
    if not rule:
        return None, 0.0, 0.0

    # 1. Determine Interest Rate
    applied_rate = 0.0
    if months_held >= rule['tenure_m']:
        applied_rate = rule['base_rate']
    else:
        for low, high, rate in rule['interest_slabs']:
            if low <= months_held < high:
                applied_rate = rate
                break
    
    # 2. Determine Service Charge (Penalty on Principal)
    service_charge_percent = 0.0
    if months_held < rule['tenure_m']:
        for limit, charge in rule['penalty_slabs']:
            if months_held < limit:
                service_charge_percent = charge
                break

    return rule, applied_rate, service_charge_percent

@frappe.whitelist()
def ping():
    return "Pong"

@frappe.whitelist()
def get_account_details(foracid=None, settlement_date=None):
    if not foracid: return {"success": False, "error": "Account number is required"}
    
    logs = []
    # Default settlement date to today if not provided
    if not settlement_date:
        sett_dt = datetime.now()
    else:
        try:
            # Handle both YYYY-MM-DD (from UI picker) and DD/MM/YYYY
            if '-' in settlement_date:
                sett_dt = datetime.strptime(settlement_date, "%Y-%m-%d")
            else:
                sett_dt = datetime.strptime(settlement_date, "%d/%m/%Y")
        except ValueError:
            sett_dt = datetime.now()

    conn = None
    try:
        logs.append("Attempting to connect to Finacle DR Database...")
        conn = get_dr_connection()
        logs.append("Connection established successfully.")
        cursor = conn.cursor()
        
        logs.append(f"Searching for account: {foracid}...")
        # Optimized main query
        cursor.execute("""
            SELECT g.acid, g.cif_id, g.acct_name, s.sol_id, s.sol_desc, g.acct_opn_date, g.schm_code, 
                   p.schm_desc, t.maturity_date, t.maturity_amount, t.deposit_period_mths, t.deposit_amount
            FROM tbaadm.gam g
            JOIN tbaadm.sol s ON g.sol_id = s.sol_id
            JOIN tbaadm.gsp p ON g.schm_code = p.schm_code
            JOIN tbaadm.tam t ON g.acid = t.acid
            WHERE g.foracid = %s AND g.del_flg = 'N'
        """, (foracid,))
        
        res = cursor.fetchone()
        if not res: return {"success": False, "error": "Account not found", "status_log": logs}

        acid, cif, name, sol_id, sol_desc, opn_dt, schm_code, schm_desc, mat_dt, mat_amt, period, dep_amt = res
        logs.append("Account details and maturity records located.")
        
        # Calculate months held
        diff = relativedelta(sett_dt, opn_dt)
        months_held = (diff.years * 12) + diff.months
        logs.append(f"Account held for {months_held} months.")

        # Get Rules
        rule_meta, app_rate, penalty_pct = get_applicable_rules(schm_code, months_held)
        if not rule_meta: 
            error_msg = f"Scheme {schm_code} not configured"
            logs.append(error_msg)
            return {"success": False, "error": error_msg, "status_log": logs}

        # Fetch Credit Transactions
        logs.append("Fetching transaction history...")
        cursor.execute("""
            SELECT value_date, tran_amt, part_tran_type, tran_particular, tran_date 
            FROM tbaadm.htd 
            WHERE acid = %s AND del_flg = 'N'
            ORDER BY value_date DESC, tran_date DESC
        """, (acid,))
        
        trans = cursor.fetchall()
        
        total_principal = 0.0
        total_interest = 0.0
        transactions = []
        total_tran_sum = 0.0
        
        # Quarterly Compounding Logic & Transaction Mapping
        for val_date, amt, p_type, particular, t_date in trans:
            amt = float(amt or 0)
            total_tran_sum += amt
            
            transactions.append({
                "date": val_date.strftime("%d/%m/%Y") if val_date else "N/A",
                "amount": amt,
                "type": p_type,
                "particular": particular or ""
            })

            if p_type == 'C':
                total_principal += amt
                if val_date < sett_dt:
                    # Quarterly compounding (n=4)
                    t_years = (sett_dt - val_date).days / 365.25
                    if app_rate > 0:
                        interest = amt * ((1 + (app_rate/100)/4)**(4 * t_years) - 1)
                        total_interest += interest

        penalty_amt = (total_principal * penalty_pct / 100)
        logs.append(f"Calculated {len(transactions)} transactions.")
        
        data = {
            "success": True,
            "cif_id": cif,
            "acct_name": name,
            "sol_id": sol_id,
            "sol_desc": sol_desc,
            "acct_opn_date": opn_dt.strftime("%d/%m/%Y") if opn_dt else "N/A",
            "schm_code": schm_code,
            "schm_desc": schm_desc,
            "maturity_date": mat_dt.strftime("%d/%m/%Y") if mat_dt else "N/A",
            "maturity_amount": float(mat_amt or 0),
            "deposit_period_mths": int(period or 0),
            "deposit_amount": float(dep_amt or 0),
            "total_tran_sum": total_tran_sum,
            "transactions": transactions,
            "principal": total_principal,
            "interest": total_interest,
            "penalty": penalty_amt,
            "applied_rate": app_rate,
            "penalty_pct": penalty_pct,
            "status_log": logs
        }
        
        return data

    except Exception as e:
        error_msg = f"Database Error: {str(e)}"
        logs.append(error_msg)
        frappe.log_error(frappe.get_traceback(), "Interest Calculator Failure")
        return {"success": False, "error": error_msg, "status_log": logs}
    finally:
        if conn: conn.close()

@frappe.whitelist()
def get_scheme_details(schm_code):
    if not schm_code:
        return {"error": "Scheme code is required"}

    conn = None
    try:
        conn = get_dr_connection()
        cursor = conn.cursor()
        
        query = "SELECT schm_desc FROM tbaadm.gsp WHERE schm_code = %s"
        cursor.execute(query, (schm_code,))
        result = cursor.fetchone()
        
        if result:
            return {"schm_desc": result[0], "success": True}
        else:
            return {"error": "Scheme not found", "success": False}
            
    except Exception as e:
        return {"error": str(e), "success": False}
    finally:
        if conn:
            conn.close()
