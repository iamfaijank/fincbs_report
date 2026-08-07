import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class GLWiseTarget(Document):
    def validate(self):
        self.validate_zone_uniqueness()
        self.validate_allocation_sum()

    def validate_zone_uniqueness(self):
        zones = []
        for row in self.allocations:
            if row.zone in zones:
                frappe.throw(_("Zone {0} is duplicated in the allocations").format(row.zone))
            zones.append(row.zone)

    def validate_allocation_sum(self):
        scheme_fields = ["casa", "dam", "dd", "fd", "rd", "smbg", "share"]
        for row in self.allocations:
            total = sum(flt(row.get(f)) for f in scheme_fields)
            if abs(total - 100) > 0.01:
                frappe.throw(
                    _("Zone {0}: Total allocation must be 100%. Current sum: {1}%").format(
                        row.zone, total
                    )
                )
