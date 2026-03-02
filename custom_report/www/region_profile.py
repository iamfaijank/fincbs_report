import frappe

def get_context(context):
    zone = frappe.form_dict.get("zone")
    region = frappe.form_dict.get("region")

    if not zone or not region:
        context.error = "Zone and Region are required."
        return context

    # Execute the query to get product achievements for the given zone and region
    products_data = frappe.db.sql("""
        SELECT
            product,
            SUM(amount) AS ach
        FROM `tabProduct Wise Report`
        WHERE
            zone = %(zone)s AND
            region = %(region)s
        GROUP BY
            product
        ORDER BY
            ach DESC
    """, {"zone": zone, "region": region}, as_dict=True)

    # Calculate total achievement
    total_ach = sum(p['ach'] for p in products_data)

    # Pass data to the template context
    context.zone = zone
    context.region = region
    context.products = products_data
    context.total_ach = total_ach

    return context
