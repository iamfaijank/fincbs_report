frappe.pages["branch-profile"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Branch Profile",
		single_column: true,
	});

	/* ---------------- CSS ---------------- */
	$(`<style>
		.branch-profile-container { padding: 20px; font-family: Inter, Arial; }

		.profile-section {
			border: 1px solid #e5e7eb;
			border-radius: 10px;
			padding: 16px;
			background: #fff;
			margin-bottom: 16px;
		}

		.profile-section h6 {
			font-size: 14px;
			font-weight: 600;
			border-bottom: 1px solid #e5e7eb;
			padding-bottom: 6px;
			margin-bottom: 12px;
		}

		table.profile-table {
			width: 100%;
			font-size: 13px;
			border-collapse: collapse;
		}

		table.profile-table th {
			width: 45%;
			background: #f9fafb;
			padding: 8px;
			text-align: left;
			font-weight: 500;
			border-bottom: 1px solid #e5e7eb;
		}

		table.profile-table td {
			padding: 8px;
			border-bottom: 1px solid #e5e7eb;
		}

		.empty-box {
			text-align: center;
			color: #6b7280;
			padding: 40px;
		}

		#suggestions-dropdown li {
			cursor: pointer;
		}
	</style>`).appendTo("head");

	/* ---------------- HTML ---------------- */
	$(wrapper).find(".layout-main-section").html(`
		<div class="branch-profile-container">
			<div class="mb-4 d-flex align-items-center">
				<label class="fw-bold mr-3">SOL</label>
				<div id="search-field" style="width:300px"></div>
			</div>

			<div class="row">
				<div class="col-md-4" id="branch-details"></div>
				<div class="col-md-8" id="right-section"></div>
			</div>
		</div>
	`);

	init_sol_search(wrapper);

	/* -------- LOAD FROM URL -------- */
	const query = frappe.utils.get_query_params();
	if (query.sol_id) {
		$("#search-field input").val(query.sol_id);
		load_all_data(query.sol_id);
	}
};

/* ---------------- URL HANDLER ---------------- */
function update_url_sol(sol_id = null) {
	const url = new URL(window.location.href);
	if (sol_id) url.searchParams.set("sol_id", sol_id);
	else url.searchParams.delete("sol_id");
	window.history.pushState({}, "", url);
}

/* ---------------- SOL SEARCH ---------------- */
function init_sol_search(wrapper) {
	const control = new frappe.ui.form.ControlData({
		df: {
			fieldname: "sol",
			fieldtype: "Data",
			placeholder: "Type SOL ID",
		},
		parent: $(wrapper).find("#search-field"),
		render_input: true,
	});
	control.refresh();

	$(control.input).on("input", function () {
		const txt = $(this).val().trim();

		if (!txt) {
			$("#suggestions-dropdown").remove();
			update_url_sol(null);
			empty("#branch-details", "");
			empty("#right-section", "");
			return;
		}

		frappe.call({
			method: "custom_report.custom_report.page.branch_profile.branch_profile.search_branches",
			args: { txt },
			callback: (r) => show_suggestions(control.input, r.message || []),
		});
	});
}

/* ---------------- AUTOCOMPLETE ---------------- */
function show_suggestions(input, list) {
	$("#suggestions-dropdown").remove();
	if (!list.length) return;

	let ul = $(
		`<ul id="suggestions-dropdown" class="list-group position-absolute w-100 shadow" style="z-index:999"></ul>`
	);

	list.forEach((b) => {
		ul.append(`
			<li class="list-group-item" data-sol="${b.sol_id}">
				<b>${b.sol_id}</b> – ${b.branch}
			</li>
		`);
	});

	$(input).after(ul);

	ul.find("li").on("click", function () {
		const sol = $(this).data("sol");
		$(input).val(sol);
		ul.remove();

		update_url_sol(sol);
		load_all_data(sol);
	});
}

/* ---------------- LOAD BOTH SIDES ---------------- */
function load_all_data(sol) {
	load_branch_master(sol);
	load_branch_profile(sol);
}

/* ---------------- LEFT : BRANCH MASTER ---------------- */
function load_branch_master(sol) {
	frappe.call({
		method: "custom_report.custom_report.page.branch_profile.branch_profile.get_branch_data",
		args: { sol_id: sol },
		callback: (r) => render_branch_master(r.message?.[0]),
	});
}

function render_branch_master(b) {
	if (!b) return empty("#branch-details", "No Branch Found");

	$("#branch-details").html(
		build_section("Branch Master", {
			"SOL ID": b.sol_id,
			"Branch Name": b.branch,
			District: b.district,
			State: `${b.state} (${b.state_code})`,
			Zone: b.zone,
			Region: b.region,
			Email: b.email,
		})
	);
}

/* ---------------- RIGHT : BRANCH PROFILE ---------------- */
function load_branch_profile(sol) {
	frappe.call({
		method: "custom_report.custom_report.page.branch_profile.branch_profile.get_branch_profile_data",
		args: { sol_id: sol },
		callback: (r) => render_branch_profile(r.message),
	});
}

function render_branch_profile(data) {
	if (!data) return empty("#right-section", "No Branch Profile Data");

	let sections = {
		Management: ["bm_name", "bm_vintage", "bm_doj"],
		"Staff Strength": ["staff_count", "total_no_of_budgeted_staff", "total_staff_onboarded"],
		"Business Book": [
			"total_book",
			"ca_book",
			"sa_book",
			"fd_book",
			"rd_book",
			"dds_book",
			"smbg_book",
		],
		Performance: [
			"total_ytd_target",
			"total_ytd_achievement",
			"total_mtd_target",
			"total_mtd_achievement",
			"total_productivity",
			"audit_rating",
		],
	};

	let html = "";
	Object.keys(sections).forEach((title) => {
		let rows = {};
		sections[title].forEach((k) => {
			rows[frappe.model.unscrub(k)] = data[k];
		});
		html += build_section(title, rows);
	});

	$("#right-section").html(html);
}

/* ---------------- SECTION BUILDER ---------------- */
function build_section(title, rows) {
	let body = "";
	Object.keys(rows).forEach((label) => {
		body += `<tr><th>${label}</th><td>${rows[label] ?? "-"}</td></tr>`;
	});

	return `
		<div class="profile-section">
			<h6>${title}</h6>
			<table class="profile-table">${body}</table>
		</div>
	`;
}

/* ---------------- HELPERS ---------------- */
function empty(selector, msg) {
	$(selector).html(`<div class="empty-box">${msg}</div>`);
}
