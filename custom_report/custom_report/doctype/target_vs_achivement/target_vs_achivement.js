frappe.ui.form.on("Target Vs Achivement", {
	refresh: function (frm) {
		// Remove existing intro manually
		remove_all_intros(frm);
		show_summary(frm);
	},

	onload: function (frm) {
		if (frm.is_new()) {
			frm.set_value("valid_from", frappe.datetime.get_today());
			frm.set_value("enable_segment_notifications", 1);
		}
	},

	valid_from: function (frm) {
		if (frm.doc.valid_from && frm.doc.type) {
			auto_set_dates(frm);
		}
		remove_all_intros(frm);
		show_summary(frm);
	},

	type: function (frm) {
		if (frm.doc.valid_from && frm.doc.type) {
			auto_set_dates(frm);
		}
	},

	target: function (frm) {
		remove_all_intros(frm);
		setTimeout(() => show_summary(frm), 200);
	},

	achievement: function (frm) {
		remove_all_intros(frm);
		setTimeout(() => show_summary(frm), 200);
	},

	valid_till: function (frm) {
		remove_all_intros(frm);
		show_summary(frm);
	},

	achievement_percentage: function (frm) {
		remove_all_intros(frm);
		show_summary(frm);
	},

	status: function (frm) {
		remove_all_intros(frm);
		show_summary(frm);
	},
});

function remove_all_intros(frm) {
	/**
	 * Manually remove all existing intro messages
	 * Works in all Frappe versions
	 */
	try {
		// Method 1: Using jQuery to remove intro area
		if (frm.$wrapper) {
			frm.$wrapper.find(".form-message").remove();
		}

		// Method 2: Clear internal intro array
		if (frm.intro_area) {
			frm.intro_area.html("");
		}
	} catch (e) {
		// Silently ignore errors
	}
}

function show_summary(frm) {
	if (!frm.doc.name) return;

	let p = frm.doc.achievement_percentage || 0;
	let seg = frm.doc.performance_segment || "";
	let emoji = get_emoji(seg);
	let color = get_color(p);

	// Milestone tracker
	let m_html = `
        <div style="display: flex; gap: 8px; margin-top: 10px;">
            ${milestone_box("📊", "25%", p >= 25)}
            ${milestone_box("📈", "50%", p >= 50)}
            ${milestone_box("🚀", "75%", p >= 75)}
            ${milestone_box("🎉", "100%", p >= 100)}
        </div>
    `;

	let html = "";

	if (frm.doc.status === "Active") {
		html = `
            <div style="background: linear-gradient(135deg, ${color} 0%, ${darken(color)} 100%); 
                        color: white; padding: 15px; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                    <div style="flex: 1;">
                        <div style="font-size: 20px; margin-bottom: 5px;">${emoji} ${seg}</div>
                        <div>Achievement: <strong style="font-size: 16px;">${p}%</strong></div>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        ${metric_box("Target", format_curr(frm.doc.target))}
                        ${metric_box("Achieved", format_curr(frm.doc.achievement))}
                        ${metric_box("Days Left", frm.doc.days_remaining)}
                    </div>
                </div>
                ${m_html}
            </div>
        `;
	} else if (frm.doc.status === "Expired") {
		html = `
            <div style="background: #6c757d; color: white; padding: 15px; border-radius: 8px;">
                <div style="font-size: 20px;">📊 Expired - ${seg}</div>
                <div>Final: <strong>${p}%</strong> | Variance: <strong>${format_curr(
			frm.doc.variance
		)}</strong></div>
                ${m_html}
            </div>
        `;
	} else {
		html = `
            <div style="background: #94a3b8; color: white; padding: 15px; border-radius: 8px;">
                <div style="font-size: 20px;">⏳ Not Started</div>
                <div>Starts: ${frappe.datetime.str_to_user(frm.doc.valid_from)}</div>
            </div>
        `;
	}

	frm.set_intro(html, get_intro_color(p, frm.doc.status));
}

function milestone_box(emoji, label, done) {
	return `
        <div style="flex: 1; background: ${done ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.2)"}; 
                    padding: 8px; border-radius: 5px; text-align: center; opacity: ${
						done ? "1" : "0.5"
					};">
            <div style="font-size: 14px;">${emoji}</div>
            <div style="font-size: 11px; font-weight: bold;">${label}</div>
            <div style="font-size: 9px;">${done ? "✓" : "○"}</div>
        </div>
    `;
}

function metric_box(label, value) {
	return `
        <div style="background: rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 5px; text-align: center;">
            <div style="font-size: 10px; opacity: 0.8;">${label}</div>
            <strong style="font-size: 14px;">${value}</strong>
        </div>
    `;
}

function get_emoji(seg) {
	if (seg.includes("Bottom")) return "📊";
	if (seg.includes("Mid")) return "📈";
	if (seg.includes("Next")) return "🚀";
	if (seg.includes("Top")) return "🎯";
	if (seg.includes("Exceeded")) return "🎉";
	return "📊";
}

function get_color(p) {
	if (p >= 100) return "#10b981";
	if (p >= 75) return "#10b981";
	if (p >= 50) return "#0d6efd";
	if (p >= 25) return "#fd7e14";
	return "#dc3545";
}

function get_intro_color(p, status) {
	if (status !== "Active") return p >= 75 ? "blue" : "red";
	if (p >= 75) return "green";
	if (p >= 50) return "blue";
	if (p >= 25) return "orange";
	return "red";
}

function darken(hex) {
	let num = parseInt(hex.replace("#", ""), 16);
	let r = (num >> 16) - 30;
	let g = ((num >> 8) & 0x00ff) - 30;
	let b = (num & 0x0000ff) - 30;
	return (
		"#" +
		(((r < 0 ? 0 : r) << 16) | ((g < 0 ? 0 : g) << 8) | (b < 0 ? 0 : b))
			.toString(16)
			.padStart(6, "0")
	);
}

function format_curr(val) {
	if (!val) return "0";
	return (
		"₹" + new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(Math.abs(val))
	);
}

function auto_set_dates(frm) {
	let from = frm.doc.valid_from;
	let type = frm.doc.type;
	if (!from || !type) return;

	let till;
	if (type === "Monthly") till = frappe.datetime.add_months(from, 1);
	else if (type === "Quarterly") till = frappe.datetime.add_months(from, 3);
	else if (type === "Half-Yearly") till = frappe.datetime.add_months(from, 6);
	else if (type === "Yearly") till = frappe.datetime.add_months(from, 12);

	if (till) {
		frm.set_value("valid_till", frappe.datetime.add_days(till, -1));
	}
}
