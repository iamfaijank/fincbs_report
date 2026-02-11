import frappe
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from custom_report.db_connection import get_dr_connection

# Excel Slab Mapping based on Audit Formula
RD_SLABS = {
    "2010": {"tenure": 12, "slabs": [(6, 9, 4.0), (9, 12, 6.0)]},   # 1 Year
    "2011": {"tenure": 24, "slabs": [(12, 18, 4.0), (18, 24, 6.0)]}, # 2 Year
    "2012": {"tenure": 36, "slabs": [(18, 27, 4.0), (27, 36, 6.0)]}, # 3 Year
    "2013": {"tenure": 48, "slabs": [(24, 36, 4.0), (36, 48, 6.0)]}, # 4 Year
    "2014": {"tenure": 60, "slabs": [(30, 45, 4.0), (45, 60, 6.0)]}, # 5 Year
    "2015": {"tenure": 60, "slabs": [(30, 45, 4.0), (45, 60, 6.0)]}, # 5 Year (Same as 2014)
    "2005": {"tenure": 66, "slabs": [(36, 66, 6.0)]},                # SMBG
    "2016": {"tenure": 120, "slabs": [(0, 120, 8.0)]}                # RD 120M
}

def get_excel_interest_rate(schm_code, months_held):
    rule = RD_SLABS.get(str(schm_code))
    if not rule: return 0.0
    if months_held >= rule['tenure']: return 8.0 
    for low, high, rate in rule['slabs']:
        if low <= months_held < high:
            return rate
    return 0.0

@frappe.whitelist()
def get_account_details(foracid=None, settlement_date=None):
    if not foracid: return {"success": False, "error": "Account number is required"}
    
    # Handle settlement date adjustment (Excel +1 logic)
    if not settlement_date:
        sett_dt = datetime.now()
    else:
        try:
            if '-' in settlement_date: sett_dt = datetime.strptime(settlement_date, "%Y-%m-%d")
            else: sett_dt = datetime.strptime(settlement_date, "%d/%m/%Y")
        except ValueError: sett_dt = datetime.now()

    conn = None
    try:
        conn = get_dr_connection()
        cursor = conn.cursor()
        
        # Main Query to fetch account info
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
        if not res: return {"success": False, "error": "Account not found"}

        acid, cif, name, sol_id, sol_desc, opn_dt, schm_code, schm_desc, mat_dt, mat_amt, period, planned_installment = res
        
        # Excel logic for months: DATEDIF(Start, End + 1, "M")
        diff_total = relativedelta(sett_dt + relativedelta(days=1), opn_dt)
        months_held_total = (diff_total.years * 12) + diff_total.months
        app_rate = get_excel_interest_rate(schm_code, months_held_total)

        # Fetch Transactions
        cursor.execute("""
            SELECT value_date, tran_amt, part_tran_type, tran_particular 
            FROM tbaadm.htd 
            WHERE acid = %s AND del_flg = 'N'
            ORDER BY value_date DESC, tran_date DESC
        """, (acid,))
        raw_trans = cursor.fetchall()
        
        total_principal = 0.0
        total_interest = 0.0
        transactions = []
        
        for val_date, amt, p_type, particular in raw_trans:
            amt = float(amt or 0)
            row_interest = 0.0
            row_months = 0
            
            if p_type == 'C':
                total_principal += amt
                if val_date < sett_dt:
                    # Excel Rule: min(Amount Deposited, Planned Installment)
                    eligible_amt = min(amt, float(planned_installment or 0))
                    
                    # Row-wise DATEDIF logic
                    r_diff = relativedelta(sett_dt + relativedelta(days=1), val_date)
                    row_months = (r_diff.years * 12) + r_diff.months
                    
                    if app_rate > 0 and row_months > 0:
                        # Excel Formula: P * (1 + r/400)^(4 * months/12) - P
                        # Which simplifies to: P * (1 + r/400)^(months/3) - P
                        row_interest = eligible_amt * ((1 + app_rate/400)**(row_months/3) - 1)
                        total_interest += row_interest

            transactions.append({
                "date": val_date.strftime("%d/%m/%Y") if val_date else "N/A",
                "amount": amt,
                "type": p_type,
                "particular": particular or "",
                "accrued_interest": round(row_interest, 2),
                "row_months": row_months,
                "applied_rate": app_rate
            })

        # Penalty logic: 1% of Principal if Premature (except SMBG which is 1.8% fixed)
        penalty_amt = 0.0
        rule_meta = RD_SLABS.get(str(schm_code), {"tenure": 0})
        if months_held_total < rule_meta['tenure']:
            if schm_code == '2005':
                penalty_amt = total_principal * 0.018 # Fixed 1.8% for SMBG
            else:
                penalty_amt = total_principal * 0.01  # Standard 1% penalty

        return {
            "success": True,
            "cif_id": cif,
            "acct_name": name,
            "sol_id": sol_id,
            "sol_desc": sol_desc,
            "acct_opn_date": opn_dt.strftime("%d/%m/%Y"),
            "schm_code": schm_code,
            "schm_desc": schm_desc,
            "maturity_date": mat_dt.strftime("%d/%m/%Y"),
            "planned_installment": float(planned_installment or 0),
            "transactions": transactions,
            "principal": round(total_principal, 2),
            "interest": round(total_interest, 2),
            "penalty": round(penalty_amt, 2),
            "net_payable": round(total_principal + total_interest - penalty_amt, 2),
            "applied_rate": app_rate,
            "months_held": months_held_total
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Excel Logic Calculator Failure")
        return {"success": False, "error": str(e)}
    finally:
        if conn: conn.close()

@frappe.whitelist()
def get_scheme_details(schm_code):
    conn = None
    try:
        conn = get_dr_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT schm_desc FROM tbaadm.gsp WHERE schm_code = %s", (schm_code,))
        result = cursor.fetchone()
        return {"schm_desc": result[0], "success": True} if result else {"error": "Scheme not found", "success": False}
    except Exception as e: return {"error": str(e), "success": False}
    finally:
        if conn: conn.close()
