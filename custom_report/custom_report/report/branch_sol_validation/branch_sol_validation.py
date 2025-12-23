import frappe
from difflib import SequenceMatcher

STOP_WORDS = ["branch", "br", "bo", "ro", "dist", "district"]

def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    status_filter = filters.get("status")

    columns = get_columns()
    data = get_data(from_date, to_date, status_filter)

    report_summary = get_summary(data)

    # columns, data, message, chart, report_summary
    return columns, data, None, None, report_summary

def get_summary(data):
    total = len(data)
    matched = len([d for d in data if d.get("match_flag") == "Matched"])
    not_matched = total - matched

    matched_pct = round((matched * 100.0 / total), 1) if total else 0
    not_matched_pct = round((not_matched * 100.0 / total), 1) if total else 0

    return [
        {
            "value": total,
            "indicator": "blue",
            "label": "Total Records",
            "datatype": "Int",
        },
        {
            "value": f"{matched} ({matched_pct}%)",
            "indicator": "green",
            "label": "Matched",
            "datatype": "Data",
        },
        {
            "value": f"{not_matched} ({not_matched_pct}%)",
            "indicator": "red",
            "label": "Not Matched",
            "datatype": "Data",
        },
    ]


def get_columns():
    return [
        {"label": "Date",             "fieldname": "date",           "fieldtype": "Date",    "width": 100},
        {"label": "Report Sol ID",    "fieldname": "report_sol_id",  "fieldtype": "Data",    "width": 110},
        {"label": "Report Branch",    "fieldname": "report_branch",  "fieldtype": "Data",    "width": 200},
        {"label": "Master Sol ID",    "fieldname": "master_sol_id",  "fieldtype": "Data",    "width": 110},
        {"label": "Master Branch",    "fieldname": "master_branch",  "fieldtype": "Data",    "width": 200},
        {"label": "Similarity Score", "fieldname": "similarity",     "fieldtype": "Percent", "width": 120},
        {"label": "Status",           "fieldname": "status",         "fieldtype": "Data",    "width": 120},
        {"label": "Match Flag",       "fieldname": "match_flag",     "fieldtype": "Data",    "width": 110},
    ]


def get_data(from_date=None, to_date=None, status_filter=None):
    bcr_filters = {}
    if from_date and to_date:
        bcr_filters["date"] = ["between", [from_date, to_date]]

    rows = frappe.get_all(
        "Branch Category Report",
        filters=bcr_filters,
        fields=["sol_id", "branch", "date"],
        order_by="date desc, sol_id asc"
    )

    master_map = {
        str(b.sol_id).strip(): (b.branch or "").strip()
        for b in frappe.get_all("Sahayog Branch", fields=["sol_id", "branch"])
    }

    result = []
    for r in rows:
        rep_sol = (r.sol_id or "").strip()
        rep_branch = (r.branch or "").strip()
        master_branch = master_map.get(rep_sol, "")

        if not rep_sol or rep_sol not in master_map:
            status = "Sol Not Found"
            sim_score = 0
            master_sol_id = ""
        else:
            master_sol_id = rep_sol
            if rep_branch == master_branch:
                status = "Exact Match"
                sim_score = 100
            else:
                n1 = normalize_name(rep_branch)
                n2 = normalize_name(master_branch)
                sim_score = string_similarity(n1, n2)

                if sim_score >= 85:
                    status = "Probable Same"
                else:
                    status = "High Risk Mismatch"

        # final flag for color coding
        match_flag = "Matched" if status in ("Exact Match", "Probable Same") else "Not Matched"

        row = {
            "date": r.date,
            "report_sol_id": rep_sol,
            "report_branch": rep_branch,
            "master_sol_id": master_sol_id,
            "master_branch": master_branch,
            "similarity": sim_score,
            "status": status,
            "match_flag": match_flag,
        }

        if status_filter and status_filter != "All":
            if status != status_filter:
                continue

        result.append(row)

    return result


def normalize_name(name):
    n = (name or "").lower()
    for w in STOP_WORDS:
        n = n.replace(w, " ")
    return " ".join(n.split())


def string_similarity(a, b):
    if not a or not b:
        return 0
    return int(SequenceMatcher(None, a, b).ratio() * 100)
