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
    "2013": {"tenure": 48, "base_rate": 8.0, "slabs": [(24, 36, 4.0), (36, 48, 6.0)]},
    "2014": {"tenure": 60, "base_rate": 8.0, "slabs": [(30, 45, 4.0), (45, 60, 6.0)]},
    "2015": {"tenure": 60, "base_rate": 8.0, "slabs": [(30, 45, 4.0), (45, 60, 6.0)]},
    "2005": {"tenure": 66, "base_rate": 8.0, "slabs": [(36, 66, 6.0)]},
    "2016": {"tenure": 120, "base_rate": 8.0, "slabs": [(0, 120, 8.0)]}
}

def get_cycle_offset(start_date, value_date):
    start = start_date.date() if hasattr(start_date, "date") else start_date
    value = value_date.date() if hasattr(value_date, "date") else value_date
    offset = (value.year - start.year) * 12 + (value.month - start.month)
    if offset > 0 and value.day <= start.day:
        offset -= 1
    return max(offset, 0)

def get_cycle_start(start_date, cycle_offset):
    return start_date + relativedelta(months=cycle_offset)

def get_excel_interest_rate(schm_code, months_held):
    rule = RD_SLABS.get(str(schm_code))
    if not rule: return 0.0
    if months_held >= rule['tenure']: return rule['base_rate']
    for low, high, rate in rule['slabs']:
        if low <= months_held < high:
            return rate
    return 0.0

def get_service_charge_percent(schm_code, months_held):
    sc = str(schm_code)
    # RD Schemes
    if sc == "2010":
        if months_held < 3: return 6.0
        if months_held < 6: return 4.0
        return 0.0
    if sc == "2011":
        if months_held < 6: return 6.0
        if months_held < 12: return 4.0
        return 0.0
    if sc == "2012":
        if months_held < 9: return 6.0
        if months_held < 18: return 4.0
        return 0.0
    if sc == "2013":
        if months_held < 12: return 6.0
        if months_held < 24: return 4.0
        return 0.0
    if sc in ["2014", "2015"]:
        if months_held < 15: return 6.0
        if months_held < 30: return 4.0
        return 0.0
    
    # Static & Tiered Percentages
    if sc in ["2005", "2006"]: return 18.0
    if sc in ["2002", "2003", "2203"]: return 11.0
    if sc in ["2101", "2104"]: return 3.0
    if sc in ["2018"]: return 2.5
    if sc in ["2019", "2023"]: return 3.5
    
    if sc in ["2001", "2027", "2103", "2201"]:
        if months_held < 12: return 11.0 if sc == "2201" else 9.5
        if months_held < 24: return 9.5 if sc == "2201" else 8.0
        if months_held < 36: return 8.0 if sc == "2201" else 6.5
        if months_held < 48: return 6.5 if sc == "2201" else 5.0
        if sc == "2201" and months_held < 60: return 5.0
        return 3.5

    if sc == "2004":
        if months_held < 3: return 6.0
        if months_held < 8: return 4.0
        return 0.0
        
    if sc in ["2020", "2024"]:
        limit = 13 if sc == "2020" else 12
        return 5.0 if months_held < limit else 3.5
        
    if sc in ["2021", "2025"]:
        limit1 = 13 if sc == "2021" else 12
        limit2 = 26 if sc == "2021" else 24
        if months_held < limit1: return 6.5
        if months_held < limit2: return 5.0
        return 3.5
        
    if sc == "2026":
        if months_held < 12: return 8.0
        if months_held < 24: return 6.5
        if months_held < 36: return 5.0
        return 3.5
        
    if sc == "2022":
        return 5.0 if months_held < 26 else 3.5
        
    if sc in ["2028", "2029", "2030"]:
        return 5.0 if months_held < 24 else 3.5
        
    if sc in ["2102", "2105", "2202"]:
        if months_held < 12: return 5.0
        return 3.0 if sc == "2102" else 3.5

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
        planned_installment = float(planned_installment or 0)
        
        cursor.execute("""
            SELECT value_date, tran_amt, part_tran_type, tran_particular 
            FROM tbaadm.htd 
            WHERE acid = %s AND del_flg = 'N'
            ORDER BY value_date ASC
        """, (acid,))
        raw_trans = cursor.fetchall()
        raw_trans.sort(key=lambda x: x[0])

        # Account closure handling:
        # first debit/negative amount indicates closure, so exclude that row and
        # all rows on/after that calendar date from further calculation/display.
        closure_date = None
        for val_date, amt, p_type, particular in raw_trans:
            txn_amt = float(amt or 0)
            txn_type = (p_type or "").strip().upper()
            if txn_amt < 0 or txn_type == "D":
                closure_date = val_date
                break
        if closure_date:
            closure_day = closure_date.date() if hasattr(closure_date, "date") else closure_date
            raw_trans = [
                row for row in raw_trans
                if row[0] and (row[0].date() if hasattr(row[0], "date") else row[0]) < closure_day
            ]

        is_premature = mat_dt and sett_dt < mat_dt
        diff_sett = relativedelta(sett_dt, opn_dt)
        sett_m_offset = (diff_sett.years * 12) + diff_sett.months

        # Map credits to cycle offsets from opening date, keeping cycle end inclusive.
        credits_by_month = {}
        for val_date, amt, p_type, particular in raw_trans:
            if mat_dt and val_date and val_date >= mat_dt: continue
            if val_date > sett_dt: continue
            
            m_v = get_cycle_offset(opn_dt, val_date)
            
            if p_type == 'C':
                credits_by_month[m_v] = credits_by_month.get(m_v, 0) + float(amt or 0)

        # Settlement cycle offset
        sett_m_offset = get_cycle_offset(opn_dt, sett_dt)

        # Update months_held_total based on premature logic
        if is_premature:
            # For interest rate slab, use relativedelta months
            diff_rel = relativedelta(sett_dt, opn_dt)
            m_rel = (diff_rel.years * 12) + diff_rel.months
            # If installment exists in the current cycle, it counts towards rate slab
            installment_exists_rel = credits_by_month.get(sett_m_offset, 0) > 0
            months_held_for_rate = m_rel + 1 if installment_exists_rel else m_rel
            
            # For loop and ledger, use cycle count to ensure settlement cycle appears
            months_held_total = sett_m_offset + 1
        else:
            diff_total = relativedelta(sett_dt + relativedelta(days=1), opn_dt)
            months_held_total = (diff_total.years * 12) + diff_total.months
            months_held_for_rate = months_held_total

        app_rate = get_excel_interest_rate(schm_code, months_held_for_rate)
        base_rate = RD_SLABS.get(str(schm_code), {}).get('base_rate', 8.0)

        # Maturity uses quarterly compounding; premature uses simple interest.
        principal_sum = 0.0
        total_interest = 0.0
        
        # State for quarterly compounding
        compounded_interest = 0.0
        accrued_current_quarter = 0.0
        
        compounded_interest_base = 0.0
        accrued_current_quarter_base = 0.0

        # Iterate month by month for the duration of the account
        monthly_data = {}
        for m in range(months_held_total):
            cycle_installment = credits_by_month.get(m, 0)
            principal_sum += cycle_installment

            # 2. Calculate Monthly Interest
            m_int = 0.0
            m_base_int = 0.0
            cycle_has_payment = cycle_installment > 0

            if cycle_has_payment and m < sett_m_offset:
                # Full cycle interest is allowed only when a payment exists in that cycle.
                interest_base = principal_sum if is_premature else (principal_sum + compounded_interest)
                base_interest_base = principal_sum if is_premature else (principal_sum + compounded_interest_base)
                m_int = interest_base * (app_rate / 1200.0)
                m_base_int = base_interest_base * (base_rate / 1200.0)
            elif cycle_has_payment and m == sett_m_offset:
                # Settlement cycle: keep pro-rata handling, but only when the cycle has a payment.
                cycle_start = get_cycle_start(opn_dt, m)
                days = (sett_dt - cycle_start).days
                if days > 0:
                    interest_base = principal_sum if is_premature else (principal_sum + compounded_interest)
                    base_interest_base = principal_sum if is_premature else (principal_sum + compounded_interest_base)
                    m_int = interest_base * (app_rate / 100.0) * (days / 365.0)
                    m_base_int = base_interest_base * (base_rate / 100.0) * (days / 365.0)
            
            total_interest += m_int
            accrued_current_quarter += m_int
            accrued_current_quarter_base += m_base_int
            
            # 3. Handle Quarter End (Compounding)
            if not is_premature and (m + 1) % 3 == 0:
                compounded_interest += accrued_current_quarter
                accrued_current_quarter = 0
                compounded_interest_base += accrued_current_quarter_base
                accrued_current_quarter_base = 0
            
            # Store interest to associate with transactions
            monthly_data[m] = {"app_int": m_int, "base_int": m_base_int}

        # Build transaction list with associated monthly interest
        transactions = []
        processed_months = set()
        total_principal_for_sc = 0.0

        for val_date, amt, p_type, particular in raw_trans:
            if mat_dt and val_date and val_date >= mat_dt: continue
            
            amt = float(amt or 0)
            row_int = 0.0
            row_scheme_int = 0.0
            
            if p_type == 'C':
                total_principal_for_sc += amt
                m_offset = get_cycle_offset(opn_dt, val_date)
                
                # Assign monthly interest to the first transaction of the month
                if m_offset in monthly_data and m_offset not in processed_months:
                    row_int = monthly_data[m_offset]["app_int"]
                    row_scheme_int = monthly_data[m_offset]["base_int"]
                    processed_months.add(m_offset)

            transactions.append({
                "date": val_date.strftime("%d/%m/%Y") if val_date else "N/A",
                "amount": amt,
                "type": p_type,
                "particular": particular or "",
                "accrued_interest": int(row_int + 0.5),
                "scheme_interest": int(row_scheme_int + 0.5),
                "elg_amt": amt
            })

        transactions.reverse()

        # Calculate Service Charge with 18% GST
        sc_percent = get_service_charge_percent(schm_code, months_held_total)
        base_charge = total_principal_for_sc * (sc_percent / 100.0)
        penalty_amt = base_charge * 1.18 # Add 18% GST

        # Passbook Charges: Rs. 60 if premature before 3 years for 2005 scheme
        passbook_charges = 0
        if str(schm_code) == "2005" and months_held_total < 36:
            passbook_charges = 60

        return {
            "success": True, "cif_id": cif, "acct_name": name, "sol_id": sol_id, "sol_desc": sol_desc,
            "acct_opn_date": opn_dt.strftime("%d/%m/%Y"), "schm_code": schm_code, "schm_desc": schm_desc,
            "maturity_date": mat_dt.strftime("%d/%m/%Y"), "maturity_amount": float(mat_amt or 0),
            "deposit_period_mths": int(period or 0), "deposit_amount": float(planned_installment or 0),
            "planned_installment": float(planned_installment or 0),
            "transactions": transactions, "principal": int(total_principal_for_sc + 0.5),
            "interest": int(total_interest + 0.5), "penalty": int(penalty_amt + 0.5),
            "passbook_charges": passbook_charges,
            "net_payable": int(total_principal_for_sc + total_interest - penalty_amt - passbook_charges + 0.5),
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
