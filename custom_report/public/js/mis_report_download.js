// Standalone MIS report CSV export module (loaded separately, called from
// sahayog_dashboard.js via window.exportMisReportCsv).
//
// Exports the FULL filtered dataset (all rows fetched from the underlying
// doctype/queries for the selected date, with the applied filters: search,
// zone, region, district) as CSV — not just the rows visible on screen.
//
// Rows that carry nested `details` (e.g. RD & SMBG Pending: per agent under
// each authorizer) are flattened: Branch Total row -> Agent rows grouped
// by their auth (no separate Auth Total rows).
//
// Usage: exportMisReportCsv(dashboardInstance, report, filteredRows)
//   dashboardInstance - the dashboard object (for state.selectedDate)
//   report            - the active MIS report config object (for report.name)
//   filteredRows      - the already-filtered row array (e.g. _getFilteredMISData(report))
(function () {
	if (window.exportMisReportCsv) return; // already loaded

	window.exportMisReportCsv = function (dashboardInstance, report, filtered) {
		if (!filtered || !filtered.length) {
			frappe.msgprint(__("No data available to download for the applied filters."));
			return;
		}

		// Flatten nested `details` (per auth/agent rows) under each branch row:
		// Branch Total row -> Agent rows (grouped by auth)
		let rows = [];

		const isGLWiseCH = report && report.id === "gl_wise_ch_report";
		if (isGLWiseCH) {
			// GL Wise CH Report: export SOL-wise data only - one row per SOL with
			// Zone / Region / District as columns (skip zone/region/district group rows)
			const solRows = (filtered || []).filter(r => r.type === "sol");
			const productCols = new Set();
			solRows.forEach(r => Object.keys(r.products || {}).forEach(p => productCols.add(p)));
			const products = Array.from(productCols).sort();
			rows = solRows.map(r => {
				const prods = r.products || {};
				const total = products.reduce((s, p) => s + (Number(prods[p]) || 0), 0);
				const pathParts = String(r.path || "").split("/");
				const solId = pathParts[3] || r.sol_id || "";
				const branchName = String(r.name || "").split(" - ").slice(1).join(" - ") || r.branch_name || "";
				const outRow = {
					zone: pathParts[0] || r.zone || "",
					region: pathParts[1] || r.region || "",
					district: pathParts[2] || r.district || "",
					sol_id: solId,
					branch_name: branchName,
				};
				products.forEach(p => { outRow[p] = Number(prods[p]) || 0; });
				outRow.total = total;
				return outRow;
			});
		} else {
			// Flatten nested `details` (per auth/agent rows) under each branch row:
			// Branch Total row -> Agent rows (grouped by auth)
			const flatten = filtered.some(r => Array.isArray(r.details) && r.details.length);
			filtered.forEach(r => {
				const detail = Array.isArray(r.details) ? r.details : [];
			if (!flatten) {
				rows.push({ ...r });
				return;
			}
			const parent = {};
			Object.keys(r).forEach(k => {
				if (k === "details" || (r[k] && typeof r[k] === "object")) return;
				parent[k] = r[k];
			});
			parent.level = "Branch Total";
			rows.push(parent);

			if (detail.length > 0) {
				// Only detail rows actually assigned to an agent produce auth/agent
				// rows; auths with only blank-agent records are excluded entirely
				// (their amounts remain in the Branch Total row).
				const assignable = detail.filter(
					d => String(d.rm_id || "").trim() || String(d.rm_name || "").trim()
				);
				const byAuth = {};
				assignable.forEach(d => {
					const authKey = String(d.auth_id || "");
					(byAuth[authKey] = byAuth[authKey] || []).push(d);
				});
				Object.keys(byAuth)
					.sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))
					.forEach(authKey => {
						const authRows = byAuth[authKey];
						// Agent rows under this auth (no Auth Total rows in export)
						authRows
							.slice()
							.sort((a, b) => String(a.rm_id || "").localeCompare(String(b.rm_id || ""), undefined, { numeric: true }))
							.forEach(d => {
								const child = {
									level: "Agent",
									zone: r.zone, region: r.region, district: r.district,
									sol_id: r.sol_id, branch_name: r.branch_name, sol_desc: r.sol_desc,
									auth_id: d.auth_id || authKey, auth_role_id: d.auth_role_id || "",
									rm_id: d.rm_id || "", rm_name: d.rm_name || "",
									total_accounts: d.total_accounts, total_collection: d.total_collection,
									pending_accounts: d.pending_accounts, pending_amount: d.pending_amount,
									pending_instalments: d.pending_instalments,
								};
								Object.keys(d).forEach(k => {
									if (k === "details" || k in child || child[k]) return;
									if (typeof d[k] === "object") return;
									child[k] = d[k];
								});
								rows.push(child);
							});
					});
			}
		});
		}

		// Derive the column set from the data itself; skip internal/object fields
		const seen = new Set();
		const allFields = [];
		rows.slice(0, 100).forEach(r => {
			Object.keys(r).forEach(k => {
				if (seen.has(k) || k.startsWith("_")) return;
				if (typeof r[k] === "object" && r[k] !== null) return;
				seen.add(k);
				allFields.push(k);
			});
		});

		// Level + hierarchy columns first, then remaining metric columns
		const leadFields = ["level", "report_date", "date", "zone", "region", "district", "sol_id", "branch_name", "sol_desc", "auth_id", "auth_role_id", "rm_id", "rm_name"];
		const fields = [];
		leadFields.forEach(f => { if (seen.has(f)) fields.push(f); });
		allFields.forEach(f => { if (!fields.includes(f)) fields.push(f); });

		const FIELD_LABELS = {
			level: "Level",
			report_date: "Report Date", date: "Date",
			zone: "Zone", region: "Region", district: "District",
			sol_id: "Sol ID", branch_name: "Branch Name", sol_desc: "SOL Name",
			auth_id: "Auth ID", auth_role_id: "Auth Role", auth_name: "Auth Name",
			rm_id: "Agent Code", rm_name: "Agent Name",
		};
		const label = f => FIELD_LABELS[f] || (f || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

		const csvCell = v => {
			const s = String(v == null ? "" : v);
			return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
		};

		const csv = [
			fields.map(f => label(f)).map(csvCell).join(","),
			...rows.map(r => fields.map(f => r[f]).map(csvCell).join(",")),
		].join("\r\n");

		const activeDate = (dashboardInstance && dashboardInstance.state && dashboardInstance.state.selectedDate) || $("#mis-date-filter").val() || "";
		const datePart = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(activeDate)
			? activeDate.split("-").reverse().join("_")
			: "";
		const reportName = (report && report.name) || "MIS_Report";
		const fileName = reportName.replace(/[^a-zA-Z0-9]+/g, "_") + (datePart ? "_" + datePart : "") + ".csv";

		const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" }));
		const a = document.createElement("a");
		a.href = url;
		a.download = fileName;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	};
})();
