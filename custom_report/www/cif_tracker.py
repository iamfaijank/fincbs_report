import frappe
from psycopg2.extras import RealDictCursor
from custom_report.db_connection import get_dr_connection

def get_context(context):
    # Prevent caching and require login
    context.no_cache = 1
    context.login_required = True
    
    # Check if user has "CIF Tracker" role
    context.has_access = check_user_access()

def check_user_access():
    """Helper to check if user has access based on designation OR role"""
    user = frappe.session.user
    if user == "Administrator":
        return True

    user_roles = set(frappe.get_roles(user))
    if "System Manager" in user_roles:
        return True
        
    # Check designation first (Full access for these designations)
    designation = frappe.db.get_value("Employee", {"user_id": user}, "designation")
    if designation in ['BRANCH MANAGER', 'Branch Operation Manager', 'CLUSTER OPERATION MANAGER', 'Asst. Branch Manager', 'BRANCH MANAGER JLL','Sr. Branch Manager','Asst. Branch Manager JLL']:
        return True

    # Fallback to role-based access if designation doesn't match
    if "CIF Tracker" in user_roles:
        return True
        
    return False

@frappe.whitelist()
def get_cif_details(cif_id):
    # Security check for API call
    if not check_user_access():
        frappe.throw("Only BOM, ABM, BM, Sr. BM and COM users have access to the CIF Tracker; please connect with them for assistance.", frappe.PermissionError)

    if not cif_id or len(str(cif_id)) < 4 or len(str(cif_id)) > 9:
        return {"success": False, "error": "CIF ID must be between 4 and 9 digits"}

    conn = None
    try:
        conn = get_dr_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT c.cif_id,
                   c.cust_name,
                    CASE
                       WHEN corp.corp_key IS NOT NULL THEN 'CORPORATE'
                       ELSE 'RETAIL'
                   END AS cif_type,
                   c.primary_sol_id                         AS sol_id,
                   s.sol_desc                               AS sol_desc,       
                   -- ==================== MAKER DETAILS ====================
                   c.rcre_user_id                           AS maker_id,
                   u_mkr.loginid                            AS maker_login_id,
                   COALESCE(
                       NULLIF(TRIM(g_mkr.emp_name), ''),
                       NULLIF(TRIM(CONCAT(p_mkr.firstname, ' ', p_mkr.lastname)), ''),
                       u_mkr.loginid
                   ) AS maker_name,
                   TO_CHAR(c.rcre_time, 'HH24:MI:SS')       AS saved_time,
                   c.rcre_time::DATE                        AS created_date,      
                   -- ==================== RAW TECHNICAL STATUS CODES ====================
                   c.entity_cre_flg                         AS core_flg,          -- Y / N
                   a.recordstatus                           AS acc_status,         -- A / I / U
                   am.recordstatus                          AS mod_status,         -- D / F / R
                   -- ==================== CHECKER DETAILS ====================
                   CASE
                       WHEN c.entity_cre_flg = 'Y' OR a.recordstatus = 'A'
                           THEN COALESCE(u_appr.loginid, bc.def_checker_id)
                       ELSE COALESCE(u_chk.loginid, bc.def_checker_id)
                   END AS checker_login_id,
                   -- CHECKER NAME (Kabhi Blank Space nahi aayega):
                   CASE
                       -- 1. Verified Case:
                       WHEN c.entity_cre_flg = 'Y' OR a.recordstatus = 'A'
                           THEN COALESCE(
                               NULLIF(TRIM(g_appr.emp_name), ''),
                               NULLIF(TRIM(CONCAT(p_appr.firstname, ' ', p_appr.lastname)), ''),
                               NULLIF(TRIM(bc.def_checker_name), ''),
                               u_appr.loginid,
                               bc.def_checker_id
                           )
                       -- 2. Pending Case:
                       ELSE COALESCE(
                           NULLIF(TRIM(g_chk.emp_name), ''),
                           NULLIF(TRIM(CONCAT(p_chk.firstname, ' ', p_chk.lastname)), ''),
                           NULLIF(TRIM(bc.def_checker_name), ''),
                           u_chk.loginid,
                           bc.def_checker_id
                       )
                   END AS checker_person_name,
                    -- >>>>> YAHAN PAR YE 2 CONDITIONS PASTE KAREIN <<<<<
                   CASE
                       WHEN c.entity_cre_flg = 'Y' OR a.recordstatus = 'A'
                           THEN TO_CHAR(c.lchg_time, 'HH24:MI:SS')
                       ELSE NULL
                   END AS verified_time,
                   CASE
                       WHEN c.entity_cre_flg = 'Y' OR a.recordstatus = 'A'
                           THEN c.lchg_time::DATE
                       ELSE NULL
                   END AS verified_date,
                   -- ==================== EXACT STATUS ====================
                   CASE
                       WHEN c.del_flg = 'Y' THEN 'Deleted / Cancelled'
                       WHEN c.entity_cre_flg = 'Y' OR a.recordstatus = 'A' THEN 'Verified'
                       WHEN am.recordstatus = 'R' THEN 'Rejected by Checker'
                       WHEN am.recordstatus = 'F' OR a.recordstatus = 'U' THEN 'Under Verification'
                       WHEN am.recordstatus = 'D' OR a.recordstatus = 'I' THEN 'Saved (Maker Tray)'
                       ELSE 'Saved (Incomplete)'
                   END AS exact_status,
                   -- ==================== CURRENT TRAY SUMMARY ====================
                   CASE
                       WHEN c.entity_cre_flg = 'Y' OR a.recordstatus = 'A'
                           THEN CONCAT('Verified By: ', COALESCE(NULLIF(TRIM(g_appr.emp_name), ''), NULLIF(TRIM(CONCAT(p_appr.firstname, ' ', p_appr.lastname)), ''), bc.def_checker_name, u_appr.loginid))
                       WHEN am.recordstatus = 'F' OR a.recordstatus = 'U'
                           THEN CONCAT('Pending with Checker: ', COALESCE(NULLIF(TRIM(g_chk.emp_name), ''), NULLIF(TRIM(CONCAT(p_chk.firstname, ' ', p_chk.lastname)), ''), bc.def_checker_name, u_chk.loginid))
                       WHEN am.recordstatus = 'D' OR a.recordstatus = 'I'
                           THEN CONCAT('Pending with Maker: ', COALESCE(NULLIF(TRIM(g_mkr.emp_name), ''), NULLIF(TRIM(CONCAT(p_mkr.firstname, ' ', p_mkr.lastname)), ''), u_mkr.loginid))
                       WHEN am.recordstatus = 'R'
                           THEN 'Rejected by Checker'
                       ELSE 'Incomplete'
                   END AS current_tray_status
            FROM crmuser.cmg c
            LEFT JOIN tbaadm.sol s
                   ON TRIM(c.primary_sol_id) = TRIM(s.sol_id)
            LEFT JOIN crmuser.accounts a
                   ON TRIM(c.cif_id) = TRIM(a.orgkey)
            LEFT JOIN crmuser.accounts_mod am
                   ON TRIM(c.cif_id) = TRIM(am.orgkey)
            LEFT JOIN crmuser.corporate corp
                   ON TRIM(c.cif_id) = TRIM(corp.corp_key)
            -- Branch Checker Subquery:
            LEFT JOIN (
                SELECT DISTINCT ON (TRIM(u.sol_id))
                    TRIM(u.sol_id) AS sol_id,
                    u.user_id      AS def_checker_id,
                    g.emp_name     AS def_checker_name
                FROM tbaadm.upr u
                JOIN tbaadm.get g
                  ON TRIM(u.user_id) = TRIM(g.emp_id)
                WHERE u.del_flg = 'N'
                  AND u.user_work_class IN ('301', '401')
                ORDER BY TRIM(u.sol_id), u.user_work_class DESC, u.user_id
            ) bc ON TRIM(c.primary_sol_id) = bc.sol_id
            -- Maker Mapping:
            LEFT JOIN crmuser.users u_mkr
                   ON TRIM(c.rcre_user_id) = u_mkr.personid::TEXT
            LEFT JOIN tbaadm.get g_mkr
                   ON TRIM(u_mkr.loginid) = TRIM(g_mkr.emp_id)
            LEFT JOIN crmuser.person p_mkr
                   ON u_mkr.personid = p_mkr.personid
            -- Specifically Assigned Checker:
            LEFT JOIN crmuser.users u_chk
                   ON am.assignedto = u_chk.personid
            LEFT JOIN tbaadm.get g_chk
                   ON TRIM(u_chk.loginid) = TRIM(g_chk.emp_id)
            LEFT JOIN crmuser.person p_chk
                   ON u_chk.personid = p_chk.personid
            -- Verifier / Approver:
            LEFT JOIN crmuser.users u_appr
                   ON TRIM(c.lchg_user_id) = u_appr.personid::TEXT
            LEFT JOIN tbaadm.get g_appr
                   ON TRIM(u_appr.loginid) = TRIM(g_appr.emp_id)
            LEFT JOIN crmuser.person p_appr
                   ON u_appr.personid = p_appr.personid
            WHERE c.del_flg = 'N'
              AND TRIM(c.cif_id) = %s
              AND c.rcre_time::DATE = CURRENT_DATE
            ORDER BY c.rcre_time DESC;
        """
        cursor.execute(query, (str(cif_id).strip(),))
        rows = cursor.fetchall()
        
        data = []
        if rows:
            for r in rows:
                item = dict(r)
                for k, v in item.items():
                    if v is not None and hasattr(v, 'isoformat'):
                        item[k] = v.isoformat()
                data.append(item)
        
        if data:
            return {"success": True, "data": data}
        else:
            return {"success": False, "error": "The mentioned CIF has either not been submitted correctly or has already been verified. Please verify the details and try again.\n If the CIF has been submitted and the verifier details are not visible, please advise the branch checker to get into their tray."}

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="CIF Tracker Error")
        return {"success": False, "error": str(e)}
    finally:
        if conn:
            conn.close()
