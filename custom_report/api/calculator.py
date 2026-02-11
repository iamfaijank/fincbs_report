import frappe
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from custom_report.db_connection import get_dr_connection

# Excel Slab Mapping based on Audit Formula
RD_SLABS = {
    "2010": {"tenure": 12, "base_rate": 8.0, "slabs": [(6, 9, 4.0), (9, 12, 6.0)]},
    "2011": {"tenure": 24, "base_rate": 8.0, "slabs": [(12, 18, 4.0), (18, 24, 6.0)]},
    "2012": {"tenure": 36, "base_rate": 8.0, "slabs": [(18, 27, 4.0), (27, 36, 6.0)]},
    "2013": {"tenure": 48, "base_rate": 8.0, "slabs": [(12, 36, 4.0), (36, 48, 6.0)]},
    "2014": {"tenure": 60, "base_rate": 8.0, "slabs": [(30, 45, 4.0), (45, 60, 6.0)]},
    "2015": {"tenure": 60, "base_rate": 8.0, "slabs": [(30, 45, 4.0), (45, 60, 6.0)]},
    "2005": {"tenure": 66, "base_rate": 8.0, "slabs": [(36, 66, 6.0)]},
    "2016": {"tenure": 120, "base_rate": 8.0, "slabs": [(0, 120, 8.0)]}
}

def get_excel_interest_rate(schm_code, months_held):
    rule = RD_SLABS.get(str(schm_code))
    if not rule: return 0.0
    if months_held >= rule['tenure']: return rule['base_rate']
    for low, high, rate in rule['slabs']:
        if low <= months_held < high:
            return rate
    return 0.0

@frappe.whitelist()
def get_account_details(foracid=None, settlement_date=None):
    if not foracid: return {"success": False, "error": "Account number is required"}
    
    if not settlement_date: sett_dt = datetime.now()
    else:
        try:
            if '-' in settlement_date: sett_dt = datetime.strptime(settlement_date, "%Y-%m-%d")
            else: sett_dt = datetime.strptime(settlement_date, "%d/%m/%Y")
        except ValueError: sett_dt = datetime.now()

    conn = None
    try:
        conn = get_dr_connection()
        cursor = conn.cursor()
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
        
        diff_total = relativedelta(sett_dt + relativedelta(days=1), opn_dt)
        months_held_total = (diff_total.years * 12) + diff_total.months
        app_rate = get_excel_interest_rate(schm_code, months_held_total)
        base_rate = RD_SLABS.get(str(schm_code), {}).get('base_rate', 8.0)

        cursor.execute("""
            SELECT value_date, tran_amt, part_tran_type, tran_particular 
            FROM tbaadm.htd 
            WHERE acid = %s AND del_flg = 'N'
            ORDER BY value_date ASC
        """, (acid,))
        raw_trans = cursor.fetchall()
        
        total_cash_principal = 0.0
        total_interest = 0.0
        transactions = []
        processed_months = set()

        for val_date, amt, p_type, particular in raw_trans:
            amt = float(amt or 0)
            row_scheme_interest = 0.0
            row_months = 0
            eligible_amt = 0.0
            
            if p_type == 'C':
                total_cash_principal += amt # Sum of all credits
                if val_date < sett_dt:
                    month_key = f"{val_date.month}-{val_date.year}"
                    r_diff = relativedelta(sett_dt + relativedelta(days=1), val_date)
                    row_months = (r_diff.years * 12) + r_diff.months
                    
                    # Rule: Only one installment per month is eligible for interest
                    if row_months > 0 and month_key not in processed_months:
                        processed_months.add(month_key)
                        eligible_amt = min(amt, float(planned_installment or 0))
                        
                        if app_rate > 0:
                            total_interest += eligible_amt * ((1 + app_rate/400)**(row_months/3) - 1)
                        row_scheme_interest = eligible_amt * ((1 + base_rate/400)**(row_months/3) - 1)

            transactions.append({
                "date": val_date.strftime("%d/%m/%Y") if val_date else "N/A",
                "amount": amt,
                "type": p_type,
                "particular": particular or "",
                "row_interest": int(round(row_scheme_interest)),
                "row_months": row_months,
                "elg_amt": eligible_amt
            })

        # Sort DESC for UI
        transactions.reverse()

        penalty_amt = 0.0
        rule_meta = RD_SLABS.get(str(schm_code), {"tenure": 0})
        if months_held_total < rule_meta['tenure']:
            # Penalty calculated on Total Cash Principal
            penalty_amt = total_cash_principal * (0.018 if schm_code == '2005' else 0.01)

        return {
            "success": True, "cif_id": cif, "acct_name": name, "sol_id": sol_id, "sol_desc": sol_desc,
            "acct_opn_date": opn_dt.strftime("%d/%m/%Y"), "schm_code": schm_code, "schm_desc": schm_desc,
            "maturity_date": mat_dt.strftime("%d/%m/%Y"), "maturity_amount": float(mat_amt or 0),
            "deposit_period_mths": int(period or 0), "deposit_amount": float(planned_installment or 0),
            "planned_installment": float(planned_installment or 0),
            "transactions": transactions, "principal": round(total_cash_principal, 2),
            "interest": int(round(total_interest)), "penalty": int(round(penalty_amt)),
            "net_payable": int(round(total_cash_principal + total_interest - penalty_amt)),
            "applied_rate": app_rate, "months_held": months_held_total
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
