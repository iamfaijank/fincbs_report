import frappe
import json
from custom_report.db_connection import get_dr_connection


@frappe.whitelist()
def ping():
    return "Pong"



@frappe.whitelist()
def get_account_details(foracid=None):
    # Support for CLI execution: bench execute custom_report.api.calculator.get_account_details --args '["ACC_NO"]'
    if not foracid:
        return {"error": "Account number is required"}

    logs = []
    conn = None
    try:
        logs.append("Attempting to connect to Finacle DR Database...")
        conn = get_dr_connection()
        logs.append("Connection established successfully.")
        
        cursor = conn.cursor()
        
        logs.append(f"Searching for account: {foracid}...")
        query = """
            SELECT 
                g.cif_id, 
                g.acct_name, 
                s.sol_id, 
                s.sol_desc,
                g.acct_opn_date,
                g.schm_code,
                p.schm_desc,
                t.maturity_date,
                t.maturity_amount,
                t.deposit_period_mths
            FROM tbaadm.gam g
            JOIN tbaadm.sol s ON g.sol_id = s.sol_id
            JOIN tbaadm.gsp p ON g.schm_code = p.schm_code
            JOIN tbaadm.tam t ON g.acid = t.acid
            WHERE g.foracid = %s
        """
        cursor.execute(query, (foracid,))
        result = cursor.fetchone()
        
        if result:
            logs.append("Account, Branch, Scheme and Maturity records located.")
            data = {
                "cif_id": result[0],
                "acct_name": result[1],
                "sol_id": result[2],
                "sol_desc": result[3],
                "acct_opn_date": result[4].strftime("%d-%b-%Y").upper() if result[4] else "N/A",
                "schm_code": result[5],
                "schm_desc": result[6],
                "maturity_date": result[7].strftime("%d-%b-%Y").upper() if result[7] else "N/A",
                "maturity_amount": float(result[8]) if result[8] is not None else 0.0,
                "deposit_period_mths": int(result[9]) if result[9] is not None else 0,
                "status_log": logs,
                "success": True
            }
            # Print for CLI visibility
            print(json.dumps(data, indent=4))
            return data
        else:
            logs.append("Account not found in tbaadm.gam table.")
            error_data = {"error": "Account not found", "status_log": logs, "success": False}
            print(json.dumps(error_data, indent=4))
            return error_data
            
    except Exception as e:
        error_msg = f"Database Error: {str(e)}"
        logs.append(error_msg)
        frappe.log_error(frappe.get_traceback(), "Calculator API Error")
        error_data = {"error": error_msg, "status_log": logs, "success": False}
        print(json.dumps(error_data, indent=4))
        return error_data
    finally:
        if conn:
            conn.close()
            logs.append("Database connection closed.")

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






#             SELECT g.cif_id,g.acct_name,g.foracid AS Account_NO,g.acct_opn_date,g.schm_code,p.schm_desc,
#        s.sol_id,s.sol_desc as Branch,t.maturity_date,t.maturity_amount,t.deposit_period_mths, h.value_date,h.tran_amt
# FROM tbaadm.gam g
# JOIN tbaadm.gsp p ON g.schm_code=p.schm_code
# JOIN tbaadm.sol s ON g.sol_id=s.sol_id
# JOIN tbaadm.tam t ON g.acid=t.acid
# LEFT JOIN tbaadm.htd h ON g.acid=h.acid
# LEFT JOIN tbaadm.tph p1 ON g.acid=p1.acid
# WHERE g.entity_cre_flg='Y' AND g.del_flg='N'
# and g.schm_code in ('2005','2010','2011','2012','2013','2014','2015','2016')
# AND g.foracid='103020050365572';