frappe.ui.form.on("GL Wise Target", {
    validate: function (frm) {
        let zones = {};
        for (let row of frm.doc.allocations || []) {
            if (zones[row.zone]) {
                frappe.msgprint(__("Zone {0} is duplicated", [row.zone]));
                frappe.validated = false;
                return false;
            }
            zones[row.zone] = true;

            let total = flt(row.casa) + flt(row.dam) + flt(row.dd) +
                        flt(row.fd) + flt(row.rd) + flt(row.smbg) + flt(row.share);
            if (Math.abs(total - 100) > 0.01) {
                frappe.msgprint(__("Zone {0}: Total allocation must be 100%. Current sum: {1}%", [row.zone, total]));
                frappe.validated = false;
                return false;
            }
        }
    }
});

function flt(v) { return parseFloat(v) || 0; }
