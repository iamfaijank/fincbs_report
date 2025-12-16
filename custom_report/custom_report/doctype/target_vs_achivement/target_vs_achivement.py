# Copyright (c) 2025, Your Organization and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate, nowdate
from frappe import _

class TargetVsAchivement(Document):
    
    def validate(self):
        self.validate_dates()
        self.check_overlapping()
        self.calculate_metrics()
        self.update_segment()
        self.update_status()
    
    def validate_dates(self):
        if self.valid_from and self.valid_till:
            if getdate(self.valid_till) < getdate(self.valid_from):
                frappe.throw(_("Valid Till cannot be before Valid From"))
    
    def check_overlapping(self):
        if not self.valid_from or not self.valid_till:
            return
        
        existing = frappe.db.exists("Target Vs Achivement", {
            "sol_id": self.sol_id,
            "type": self.type,
            "financial_year": self.financial_year,
            "name": ["!=", self.name or ""],
            "status": ["!=", "Expired"]
        })
        
        if existing:
            frappe.throw(_("Active target already exists for this period"))
    
    def calculate_metrics(self):
        # Achievement %
        if self.target and flt(self.target) > 0:
            self.achievement_percentage = flt((flt(self.achievement) / flt(self.target)) * 100, 2)
        else:
            self.achievement_percentage = 0
        
        # Variance
        self.variance = flt(self.achievement) - flt(self.target)
        
        # Days remaining
        if self.status == "Active" and self.valid_till:
            days = date_diff(self.valid_till, nowdate())
            self.days_remaining = days if days > 0 else 0
        else:
            self.days_remaining = 0
    
    def update_segment(self):
        p = flt(self.achievement_percentage)
        if p > 100:
            self.performance_segment = "Exceeded (>100%)"
        elif p >= 75:
            self.performance_segment = "Top 25% (75-100%)"
        elif p >= 50:
            self.performance_segment = "Next 25% (50-75%)"
        elif p >= 25:
            self.performance_segment = "Mid 25% (25-50%)"
        else:
            self.performance_segment = "Bottom 25% (0-25%)"
    
    def update_status(self):
        if not self.valid_from or not self.valid_till:
            return
        
        current = getdate(nowdate())
        valid_from = getdate(self.valid_from)
        valid_till = getdate(self.valid_till)
        
        if current < valid_from:
            self.status = "Inactive"
        elif valid_from <= current <= valid_till:
            self.status = "Active"
        else:
            self.status = "Expired"
    
    def on_update(self):
        if self.status != "Active":
            return
        
        if self.has_value_changed('achievement'):
            self.check_milestones()
        
        self.check_expiry_alert()
    
    def check_milestones(self):
        if not self.enable_segment_notifications:
            return
        
        email = get_branch_email(self.sol_id)
        if not email:
            return
        
        p = flt(self.achievement_percentage)
        
        # 25%
        if p >= 25 and not self.bottom_segment_notified:
            send_milestone_email(self, email, "25%", "📊")
            self.db_set('bottom_segment_notified', 1, update_modified=False)
        
        # 50%
        if p >= 50 and not self.mid_segment_notified:
            send_milestone_email(self, email, "50%", "📈")
            self.db_set('mid_segment_notified', 1, update_modified=False)
        
        # 75%
        if p >= 75 and not self.next_segment_notified:
            send_milestone_email(self, email, "75%", "🚀")
            self.db_set('next_segment_notified', 1, update_modified=False)
        
        # 100%
        if p >= 100 and not self.top_segment_notified:
            send_milestone_email(self, email, "100%", "🎉")
            self.db_set('top_segment_notified', 1, update_modified=False)
    
    def check_expiry_alert(self):
        if not self.alert_before_expiry_days:
            return
        
        days = date_diff(self.valid_till, nowdate())
        
        if 0 < days <= flt(self.alert_before_expiry_days):
            email = get_branch_email(self.sol_id)
            if email:
                send_expiry_email(self, email)


# Helper Functions

def get_branch_email(sol_id):
    try:
        email = frappe.db.get_value("Sahayog Branch", sol_id, "email")
        return email.strip() if email and "@" in email else None
    except:
        return None


def send_milestone_email(doc, email, milestone, emoji):
    try:
        branch_name = frappe.db.get_value("Sahayog Branch", doc.sol_id, "branch_name") or doc.sol_id
        
        # Milestone tracker HTML
        milestones_html = f"""
        <div style="display: flex; gap: 10px; margin: 20px 0;">
            <div style="flex: 1; background: {'#4CAF50' if doc.achievement_percentage >= 25 else '#eee'}; 
                        color: {'white' if doc.achievement_percentage >= 25 else '#666'}; 
                        padding: 15px; border-radius: 5px; text-align: center;">
                <div style="font-size: 20px;">📊</div>
                <div style="font-weight: bold;">25%</div>
                <div style="font-size: 11px;">{'✓' if doc.achievement_percentage >= 25 else 'Pending'}</div>
            </div>
            <div style="flex: 1; background: {'#4CAF50' if doc.achievement_percentage >= 50 else '#eee'}; 
                        color: {'white' if doc.achievement_percentage >= 50 else '#666'}; 
                        padding: 15px; border-radius: 5px; text-align: center;">
                <div style="font-size: 20px;">📈</div>
                <div style="font-weight: bold;">50%</div>
                <div style="font-size: 11px;">{'✓' if doc.achievement_percentage >= 50 else 'Pending'}</div>
            </div>
            <div style="flex: 1; background: {'#4CAF50' if doc.achievement_percentage >= 75 else '#eee'}; 
                        color: {'white' if doc.achievement_percentage >= 75 else '#666'}; 
                        padding: 15px; border-radius: 5px; text-align: center;">
                <div style="font-size: 20px;">🚀</div>
                <div style="font-weight: bold;">75%</div>
                <div style="font-size: 11px;">{'✓' if doc.achievement_percentage >= 75 else 'Pending'}</div>
            </div>
            <div style="flex: 1; background: {'#4CAF50' if doc.achievement_percentage >= 100 else '#eee'}; 
                        color: {'white' if doc.achievement_percentage >= 100 else '#666'}; 
                        padding: 15px; border-radius: 5px; text-align: center;">
                <div style="font-size: 20px;">🎉</div>
                <div style="font-weight: bold;">100%</div>
                <div style="font-size: 11px;">{'✓' if doc.achievement_percentage >= 100 else 'Pending'}</div>
            </div>
        </div>
        """
        
        message = f"""
        <div style="font-family: Arial; max-width: 600px; margin: 0 auto;">
            <div style="background: #4CAF50; color: white; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">{emoji} {milestone} Milestone Achieved!</h2>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <p><strong>Branch:</strong> {branch_name}</p>
                <p><strong>Type:</strong> {doc.type}</p>
                <p><strong>Target:</strong> ₹{frappe.format_value(doc.target, {'fieldtype': 'Currency'})}</p>
                <p><strong>Achievement:</strong> ₹{frappe.format_value(doc.achievement, {'fieldtype': 'Currency'})}</p>
                <p><strong>Achievement %:</strong> {doc.achievement_percentage}%</p>
                <p><strong>Days Remaining:</strong> {doc.days_remaining}</p>
                
                <h3>Achievement Progress</h3>
                {milestones_html}
                
                <p style="text-align: center; margin-top: 20px;">
                    <a href="{frappe.utils.get_url_to_form('Target Vs Achivement', doc.name)}" 
                       style="background: #4CAF50; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Details
                    </a>
                </p>
            </div>
        </div>
        """
        
        frappe.sendmail(
            recipients=[email],
            subject=f"{emoji} {milestone} Milestone - {branch_name}",
            message=message,
            reference_doctype=doc.doctype,
            reference_name=doc.name
        )
    except Exception as e:
        frappe.log_error(str(e), "Milestone Email Error")


def send_expiry_email(doc, email):
    try:
        branch_name = frappe.db.get_value("Sahayog Branch", doc.sol_id, "branch_name") or doc.sol_id
        
        message = f"""
        <div style="font-family: Arial; max-width: 600px; margin: 0 auto;">
            <div style="background: #FF6B35; color: white; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">⚠️ Target Expiring Soon!</h2>
                <p style="margin: 5px 0 0 0;">Only {doc.days_remaining} days left</p>
            </div>
            <div style="padding: 20px; background: #FFF3E0;">
                <p><strong>Branch:</strong> {branch_name}</p>
                <p><strong>Current Achievement:</strong> {doc.achievement_percentage}%</p>
                <p><strong>Remaining:</strong> ₹{frappe.format_value(doc.target - doc.achievement, {'fieldtype': 'Currency'})}</p>
                <p style="text-align: center; margin-top: 20px;">
                    <a href="{frappe.utils.get_url_to_form('Target Vs Achivement', doc.name)}" 
                       style="background: #FF6B35; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Take Action
                    </a>
                </p>
            </div>
        </div>
        """
        
        frappe.sendmail(
            recipients=[email],
            subject=f"⚠️ Target Expiring - {branch_name}",
            message=message
        )
    except Exception as e:
        frappe.log_error(str(e), "Expiry Email Error")


@frappe.whitelist()
def auto_update_all_statuses():
    targets = frappe.get_all("Target Vs Achivement", 
                             filters={"status": ["!=", "Expired"]},
                             fields=["name"])
    
    for target in targets:
        try:
            doc = frappe.get_doc("Target Vs Achivement", target.name)
            doc.update_status()
            doc.calculate_metrics()
            doc.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(str(e), "Auto Update Error")
            continue
