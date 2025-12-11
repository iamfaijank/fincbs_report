import frappe

@frappe.whitelist()
def get_dashboard_data():
    """
    Phase 1: Returns dummy data
    Phase 2: Will connect to PostgreSQL via db_utils
    """
    return get_dummy_data()

def get_dummy_data():
    """Dummy data matching the Finacle structure"""
    return {
        "zones": [
            {
                "zone_name": "ZONE-1",
                "branch_score": 108,
                "dec_tgt": 102970500,
                "jan_tgt": 109671000,
                "feb_tgt": 116371500,
                "mar_tgt": 123072000,
                "djfm_total": 452085000,
                "categories": [
                    {"category": "Accelerator", "branch_score": 21, "dec_tgt": 27615000, "jan_tgt": 28930000, "feb_tgt": 30245000, "mar_tgt": 31560000, "djfm_total": 118350000},
                    {"category": "Learner", "branch_score": 20, "dec_tgt": 5652000, "jan_tgt": 6594000, "feb_tgt": 7536000, "mar_tgt": 8478000, "djfm_total": 28260000},
                    {"category": "Master", "branch_score": 21, "dec_tgt": 27394500, "jan_tgt": 28699000, "feb_tgt": 30003500, "mar_tgt": 31308000, "djfm_total": 117405000},
                    {"category": "Pinacle", "branch_score": 16, "dec_tgt": 32865000, "jan_tgt": 34430000, "feb_tgt": 35995000, "mar_tgt": 37560000, "djfm_total": 140850000},
                    {"category": "Starter", "branch_score": 20, "dec_tgt": 7644000, "jan_tgt": 8918000, "feb_tgt": 10192000, "mar_tgt": 11466000, "djfm_total": 38220000},
                    {"category": "Zero Level", "branch_score": 10, "dec_tgt": 1800000, "jan_tgt": 2100000, "feb_tgt": 2400000, "mar_tgt": 2700000, "djfm_total": 9000000}
                ]
            },
            {
                "zone_name": "ZONE-2",
                "branch_score": 30,
                "dec_tgt": 10716000,
                "jan_tgt": 12502000,
                "feb_tgt": 14288000,
                "mar_tgt": 16074000,
                "djfm_total": 53580000,
                "categories": [
                    {"category": "Accelerator", "branch_score": 1, "dec_tgt": 3240000, "jan_tgt": 3780000, "feb_tgt": 4320000, "mar_tgt": 4860000, "djfm_total": 16200000},
                    {"category": "Learner", "branch_score": 7, "dec_tgt": 2520000, "jan_tgt": 2940000, "feb_tgt": 3360000, "mar_tgt": 3780000, "djfm_total": 12600000},
                    {"category": "Master", "branch_score": 1, "dec_tgt": 312000, "jan_tgt": 364000, "feb_tgt": 416000, "mar_tgt": 468000, "djfm_total": 1560000},
                    {"category": "Starter", "branch_score": 4, "dec_tgt": 1440000, "jan_tgt": 1680000, "feb_tgt": 1920000, "mar_tgt": 2160000, "djfm_total": 7200000},
                    {"category": "Zero Level", "branch_score": 17, "dec_tgt": 5120000, "jan_tgt": 7140000, "feb_tgt": 8160000, "mar_tgt": 9180000, "djfm_total": 30600000}
                ]
            },
            {
                "zone_name": "ZONE-3",
                "branch_score": 28,
                "dec_tgt": 6120000,
                "jan_tgt": 7140000,
                "feb_tgt": 8160000,
                "mar_tgt": 9180000,
                "djfm_total": 30600000,
                "categories": [
                    {"category": "Learner", "branch_score": 5, "dec_tgt": 960000, "jan_tgt": 1120000, "feb_tgt": 1280000, "mar_tgt": 1440000, "djfm_total": 4800000},
                    {"category": "Starter", "branch_score": 2, "dec_tgt": 480000, "jan_tgt": 560000, "feb_tgt": 640000, "mar_tgt": 720000, "djfm_total": 2400000},
                    {"category": "Zero Level", "branch_score": 21, "dec_tgt": 4680000, "jan_tgt": 5460000, "feb_tgt": 6240000, "mar_tgt": 7020000, "djfm_total": 23400000}
                ]
            },
            {
                "zone_name": "ZONE-4",
                "branch_score": 20,
                "dec_tgt": 4500000,
                "jan_tgt": 5250000,
                "feb_tgt": 6000000,
                "mar_tgt": 6750000,
                "djfm_total": 22500000,
                "categories": [
                    {"category": "Learner", "branch_score": 6, "dec_tgt": 1440000, "jan_tgt": 1680000, "feb_tgt": 1920000, "mar_tgt": 2160000, "djfm_total": 7200000},
                    {"category": "Zero Level", "branch_score": 14, "dec_tgt": 4060000, "jan_tgt": 3570000, "feb_tgt": 4080000, "mar_tgt": 4590000, "djfm_total": 15300000}
                ]
            },
            {
                "zone_name": "ZONE-5",
                "branch_score": 19,
                "dec_tgt": 4716000,
                "jan_tgt": 5502000,
                "feb_tgt": 6288000,
                "mar_tgt": 7074000,
                "djfm_total": 23580000,
                "categories": [
                    {"category": "Learner", "branch_score": 11, "dec_tgt": 2760000, "jan_tgt": 3220000, "feb_tgt": 3680000, "mar_tgt": 4140000, "djfm_total": 13800000},
                    {"category": "Master", "branch_score": 2, "dec_tgt": 576000, "jan_tgt": 672000, "feb_tgt": 768000, "mar_tgt": 864000, "djfm_total": 2880000},
                    {"category": "Starter", "branch_score": 1, "dec_tgt": 240000, "jan_tgt": 280000, "feb_tgt": 320000, "mar_tgt": 360000, "djfm_total": 1200000},
                    {"category": "Zero Level", "branch_score": 5, "dec_tgt": 1140000, "jan_tgt": 1330000, "feb_tgt": 1520000, "mar_tgt": 1710000, "djfm_total": 5700000}
                ]
            },
            {
                "zone_name": "ZONE-6",
                "branch_score": 15,
                "dec_tgt": 3492000,
                "jan_tgt": 4074000,
                "feb_tgt": 4656000,
                "mar_tgt": 5238000,
                "djfm_total": 17460000,
                "categories": [
                    {"category": "Learner", "branch_score": 5, "dec_tgt": 1260000, "jan_tgt": 1470000, "feb_tgt": 1680000, "mar_tgt": 1890000, "djfm_total": 6300000},
                    {"category": "Master", "branch_score": 1, "dec_tgt": 252000, "jan_tgt": 294000, "feb_tgt": 336000, "mar_tgt": 378000, "djfm_total": 1260000},
                    {"category": "Starter", "branch_score": 1, "dec_tgt": 180000, "jan_tgt": 210000, "feb_tgt": 240000, "mar_tgt": 270000, "djfm_total": 900000},
                    {"category": "Zero Level", "branch_score": 8, "dec_tgt": 1800000, "jan_tgt": 2100000, "feb_tgt": 2400000, "mar_tgt": 2700000, "djfm_total": 9000000}
                ]
            }
        ],
        "grand_total": {
            "branch_score": 220,
            "dec_tgt": 132514500,
            "jan_tgt": 144139000,
            "feb_tgt": 155763500,
            "mar_tgt": 167388000,
            "djfm_total": 599805000
        }
    }
