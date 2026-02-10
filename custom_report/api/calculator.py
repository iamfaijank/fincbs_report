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
                g.acid,
                g.cif_id, 
                g.acct_name, 
                s.sol_id, 
                s.sol_desc,
                g.acct_opn_date,
                g.schm_code,
                p.schm_desc,
                t.maturity_date,
                t.maturity_amount,
                t.deposit_period_mths,
                t.deposit_amount
            FROM tbaadm.gam g
            JOIN tbaadm.sol s ON g.sol_id = s.sol_id
            JOIN tbaadm.gsp p ON g.schm_code = p.schm_code
            JOIN tbaadm.tam t ON g.acid = t.acid
            WHERE g.foracid = %s
        """
        cursor.execute(query, (foracid,))
        result = cursor.fetchone()
        
        if result:
            acid = result[0]
            logs.append("Account details and maturity records located.")
            
            # Fetch Transactions
            logs.append("Fetching transaction history...")
            tran_query = """
                SELECT value_date, tran_amt, part_tran_type 
                FROM tbaadm.htd 
                WHERE acid = %s 
                ORDER BY value_date DESC 
                LIMIT 10
            """
            cursor.execute(tran_query, (acid,))
            trans = cursor.fetchall()
            
            transactions = []
            for tr in trans:
                transactions.append({
                    "date": tr[0].strftime("%d-%b-%Y").upper() if tr[0] else "N/A",
                    "amount": float(tr[1]) if tr[1] is not None else 0.0,
                    "type": tr[2] # 'C' or 'D'
                })
            
            logs.append(f"Found {len(transactions)} transactions.")
            
            data = {
                "cif_id": result[1],
                "acct_name": result[2],
                "sol_id": result[3],
                "sol_desc": result[4],
                "acct_opn_date": result[5].strftime("%d-%b-%Y").upper() if result[5] else "N/A",
                "schm_code": result[6],
                "schm_desc": result[7],
                "maturity_date": result[8].strftime("%d-%b-%Y").upper() if result[8] else "N/A",
                "maturity_amount": float(result[9]) if result[9] is not None else 0.0,
                "deposit_period_mths": int(result[10]) if result[10] is not None else 0,
                "deposit_amount": float(result[11]) if result[11] is not None else 0.0,
                "transactions": transactions,
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