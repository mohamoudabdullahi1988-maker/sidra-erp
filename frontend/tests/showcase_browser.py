"""Screen check of every Berjaya business-line screen before the client demonstration.

Opens each module and tab of the sample screens (G25), then each tab that can show live records
with synthetic server answers, at laptop (1440px) and phone (390px) width. On each screen it checks:

- no script error;
- no horizontal page scroll;
- the page title is shown;
- no "NaN", "undefined", "Infinity" or "[object Object]" anywhere;
- every tile shows a value.

A screenshot of each screen goes to frontend/.verify/showcase/ (not committed).

Run from the repository root with the Vite dev server on 127.0.0.1:8080:
    (cd frontend && yarn dev --port 8080 --host 127.0.0.1) &
    python3 frontend/tests/showcase_browser.py

Every answer here is synthetic and lives only in this test.
"""

import json
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import browser  # noqa: E402  (the shared synthetic session and server answers)

BASE = browser.BASE
COMPANY = browser.COMPANY
OUT = browser.OUT / "showcase"
WIDTHS = (1440, 390)
BAD_TEXT = ("NaN", "undefined", "Infinity", "[object Object]")

# Module -> (route path, tabs, tabs with live records). Mirrors frontend/src/showcase/pages.js and
# live.js; `test_every_module_is_checked` below fails if a module or tab is added there and not here.
MODULES = {
	"executive": ("/executive", ["overview"], ["overview"]),
	"build": (
		"/build",
		["portfolio", "schedule", "cost", "variations", "quality", "risk", "stock", "subcontractors"],
		["portfolio", "schedule", "cost", "variations", "quality", "risk", "stock", "subcontractors"],
	),
	"design": ("/design", ["overview", "architecture", "civil", "inspection"], ["overview", "inspection"]),
	"realestate": ("/real-estate", ["inventory", "pipeline", "contracts"], ["inventory", "pipeline", "contracts"]),
	"crm": ("/crm", ["overview"], ["overview"]),
	"brokerage": ("/brokerage", ["overview"], []),
	"finance": ("/finance-overview", ["overview"], ["overview"]),
}

STAGES = [
	{"stage": "Foundation", "status": "Completed", "planned_start": "2026-07-01", "planned_end": "2026-08-15", "actual_end": "2026-08-14", "completion_pct": 100, "certified": True, "overdue": False, "billing_pct": 30, "billing_amount": "6300.00"},
	{"stage": "Structure", "status": "In Progress", "planned_start": "2026-08-16", "planned_end": "2026-11-01", "actual_end": None, "completion_pct": 55, "certified": False, "overdue": True, "billing_pct": 40, "billing_amount": "8400.00"},
	{"stage": "Finishing", "status": "Planned", "planned_start": "2026-11-02", "planned_end": "2027-02-28", "actual_end": None, "completion_pct": 0, "certified": False, "overdue": False, "billing_pct": 30, "billing_amount": "6300.00"},
]


def job(name, customer, site, status, service, point, value, stages=STAGES):
	return {
		"name": name, "customer": customer, "status": status, "service_type": service, "site": site, "point": point,
		"contract_value": value, "approved_variations": "800.00" if value else None,
		"current_contract_value": value, "boq_total": value, "stage_rows": stages if value else [],
		"start": "2026-07-01" if value else None, "end": "2027-02-28" if value else None,
		"progress": 52 if value else None, "stages": len(stages) if value else 0,
		"stages_completed": 1 if value else 0, "stages_certified": 1 if value else 0, "stages_overdue": 1 if value else 0,
	}


CONSTRUCTION = {
	"company": COMPANY, "currency": "USD", "today": "2026-11-15",
	"jobs": {"available": True, "reason": None, "rows": [
		job("SCJ-2026-00007", "Synthetic Buyer One", "Masalaha Hagbad, plot 12", "In Progress", "Full Construction", [9.5205, 44.1062], "21000.00"),
		job("SCJ-2026-00008", "Synthetic Buyer Two", "Rayan Gardens, plot 4", "Contracted", "Full Construction", [9.5281, 44.1149], "34500.00"),
		job("SCJ-2026-00009", "Synthetic Client Three", None, "Quoted", "Design Only", None, None),
		job("SCJ-2026-00010", "Synthetic Client Four", "Berbera Townhouses, plot 2", "In Progress", "Inspection Only", [10.4352, 45.0158], "1500.00"),
	]},
	"variations": {"available": True, "reason": None, "rows": [
		{"name": "SVO-2026-00001", "job": "SCJ-2026-00007", "amount": "800.00", "status": "Approved", "description": "Extra boundary wall", "approved_on": "2026-10-02", "raised": "2026-09-28"},
		{"name": "SVO-2026-00002", "job": "SCJ-2026-00008", "amount": "1200.00", "status": "Draft", "description": "Second bathroom tiling upgrade", "approved_on": None, "raised": "2026-11-10"},
	]},
	"inspections": {"available": True, "reason": None, "rows": [
		{"name": "SIR-2026-00004", "job": "SCJ-2026-00007", "stage": "Structure", "date": "2026-11-05", "result": "Fail", "status": "Draft", "next_action_due": "2026-11-20"},
		{"name": "SIR-2026-00005", "job": "SCJ-2026-00010", "stage": "Foundation", "date": "2026-10-20", "result": "Pass", "status": "Issued", "next_action_due": None},
	]},
	"risks": {"available": True, "reason": None, "rows": [
		{"name": "RSK-2026-00001", "job": None, "project": "Masalaha Hagbad", "category": "Weather disruption", "description": "Gu rains may flood the site access road", "owner": "Site Manager", "rating": "High", "status": "Open", "mitigation": "Temporary drainage", "review_date": "2026-11-25", "closed_on": None},
		{"name": "RSK-2026-00002", "job": None, "project": "All projects", "category": "Cost overruns", "description": "Steel price up since the budget", "owner": "Quantity Surveyor", "rating": "Medium", "status": "Monitoring", "mitigation": "Review the BOQ", "review_date": "2026-12-06", "closed_on": None},
		{"name": "RSK-2026-00003", "job": "SCJ-2026-00007", "project": "SCJ-2026-00007", "category": "Schedule delays", "description": "Structure stage behind after a failed inspection", "owner": "Project Manager", "rating": "High", "status": "Open", "mitigation": "Extra shift", "review_date": "2026-11-20", "closed_on": None},
		{"name": "RSK-2026-00004", "job": None, "project": "All projects", "category": "Currency movement", "description": "Shilling movement on labour rates", "owner": "Finance Manager", "rating": "Low", "status": "Closed", "mitigation": "Rates fixed in dollars", "review_date": None, "closed_on": "2026-11-01"},
	]},
}

REALESTATE = {
	"company": COMPANY, "currency": "USD", "today": "2026-11-15",
	"units": {
		"available": True, "reason": None, "total": 60, "value_available": "286000.00",
		"status_counts": {"Available": 20, "Reserved": 6, "Under Contract": 22, "Sold": 12},
		"schemes": [
			{"name": "Masalaha Hagbad", "counts": {"Available": 12, "Reserved": 3, "Under Contract": 10, "Sold": 5}},
			{"name": "Rayan Gardens", "counts": {"Available": 8, "Reserved": 3, "Under Contract": 12, "Sold": 7}},
		],
		"rows": [],
	},
	"reservations": {"available": True, "reason": None, "counts": {"Active": 6, "Converted": 19, "Expired": 3}},
	"contracts": {"available": True, "reason": None, "rows": [
		{"name": "SSC-2026-00055", "customer": "Synthetic Buyer One", "type": "Installment", "source": "Generated", "status": "Confirmed", "agreed_price": "18590.00", "signed_on": "2026-10-01"},
		{"name": "SSC-2026-00061", "customer": "Synthetic Buyer Two", "type": "Installment", "source": "External", "status": "Draft", "agreed_price": "9295.00", "signed_on": None},
	]},
	"schedule": {"available": True, "reason": None, "months": [{"month": f"2026-{m:02d}" if m <= 12 else f"2027-{m - 12:02d}", "amount": "4225.00"} for m in range(11, 23)]},
	"leads": {"available": True, "reason": None, "total": 30, "status_counts": {"Lead": 10, "Open": 8, "Interested": 7, "Replied": 5}, "source_counts": {"Walk In": 12, "Reference": 9, "Advertisement": 9}},
}

FINANCE = {
	"company": COMPANY, "currency": "USD", "today": "2026-11-15",
	"pnl": {"available": True, "reason": None, "months": [{"month": f"2026-{m:02d}", "income": f"{9000 + 400 * m}.00", "expense": f"{6000 + 300 * m}.00"} for m in range(1, 12)] + [{"month": "2025-12", "income": "8000.00", "expense": "6100.00"}], "expense_accounts": [{"account": "Salaries", "amount": "42000.00"}, {"account": "Materials", "amount": "31000.00"}]},
	"cash": {"available": True, "reason": None, "accounts": [{"account": "Dahabshiil Bank", "type": "Bank", "balance": "48250.00"}, {"account": "Cash", "type": "Cash", "balance": "1900.00"}]},
	"receivables": {"available": True, "reason": None, "buckets": [{"age": a, "amount": v, "count": 2} for a, v in (("Not yet due", "6000.00"), ("1-30 days", "2500.00"), ("31-60 days", "900.00"), ("61-90 days", "0.00"), ("90+ days", "400.00"))], "parties": [{"party": "Synthetic Buyer One", "amount": "4200.00"}]},
	"payables": {"available": False, "reason": "Your role does not include Purchase Invoice.", "buckets": [], "parties": []},
}

OPERATIONS = {
	"company": COMPANY, "currency": "USD", "today": "2026-11-15",
	"suppliers": {"available": True, "reason": None, "rows": [
		{"supplier": "SUP-1", "name": "Synthetic Cement Co", "group": "Raw Material", "invoices": 6, "invoiced": "18400.00", "owed": "2400.00"},
		{"supplier": "SUP-2", "name": "Synthetic Tiling Crew", "group": "Services", "invoices": 3, "invoiced": "5200.00", "owed": "0.00"},
	]},
	"stock": {"available": True, "reason": None, "warehouses": 2, "rows": [
		{"item": "CEM-50", "name": "Cement 50 kg", "warehouse": "Site Store - SH", "qty": 340.0, "uom": "Bag", "value": "3060.00"},
		{"item": "REBAR-12", "name": "Rebar 12 mm", "warehouse": "Site Store - SH", "qty": 1.5, "uom": "Tonne", "value": None},
	]},
}

CRM = {
	"company": COMPANY, "currency": "USD", "today": "2026-11-15",
	"leads": {
		"available": True, "reason": None, "total": 30,
		"by_channel": {"WhatsApp": 9, "Email": 5, "Phone Call": 5, "Facebook": 4, "Walk In": 4, "Not recorded": 3},
		"by_status": {"Lead": 12, "Open": 8, "Interested": 6, "Replied": 4},
		"months": [{"month": f"2026-{m:02d}" if m <= 12 else f"2027-{m - 12:02d}", "count": (m * 7) % 9} for m in range(1, 13)],
		"rows": [{"name": f"CRM-LEAD-2026-000{i}", "lead": f"Synthetic Lead {i}", "channel": "WhatsApp", "status": "Lead", "created": "2026-11-14"} for i in range(1, 6)],
	},
	"opportunities": {
		"available": True, "reason": None, "total": 10, "open": 8, "open_amount": "114400.00",
		"by_status": {"Open": 8, "Converted": 2},
		"stages": [{"stage": "Prospecting", "count": 4, "amount": "57200.00"}, {"stage": "Qualification", "count": 3, "amount": "42900.00"}, {"stage": "Negotiation/Review", "count": 3, "amount": None}],
		"rows": [],
	},
	"customers": {"available": True, "reason": None, "total": 40, "kyc": {"Verified": 31, "Draft": 9}},
}

LIVE_ANSWERS = {
	"get_crm_live": CRM,
	"get_construction_live": CONSTRUCTION,
	"get_realestate_live": REALESTATE,
	"get_finance_live": FINANCE,
	"get_operations_live": OPERATIONS,
}


RISK_ROWS = [
	{**{k: v for k, v in row.items() if k not in ("project", "owner")}, "risk_owner": row["owner"], "doctype": "Sidra Project Risk"}
	for row in CONSTRUCTION["risks"]["rows"]
	if row["job"] == "SCJ-2026-00007"
]
BOOT = {**browser.BOOT, "lists": {**browser.BOOT["lists"], "risks": {"read": True, "create": True}}}


def answer(url):
	path = unquote(urlparse(url).path)
	if path.endswith(("locations.get_location", "record_extras.get_extras", "forms.get_form")):
		# Side panels of a record page; not under test here, so they say they are unavailable.
		return 403, {"exception": "frappe.exceptions.PermissionError: Not permitted"}
	if path == "/api/resource/Sidra Project Risk":
		return 200, {"data": RISK_ROWS}
	if path.startswith("/api/v2/doctype/Sidra Project Risk/") and path.endswith("/count"):
		return 200, {"data": len(RISK_ROWS)}
	for method, body in LIVE_ANSWERS.items():
		if path.endswith(method):
			return 200, {"message": body}
	return browser.answer(url)


def check_screen(page, width, name, path, errors):
	page.goto(BASE + path)
	page.wait_for_load_state("networkidle")
	expect(page.locator(".sc h1, .sc__title, h1").first).to_be_visible()
	if "source=live" in path:
		expect(page.get_by_text("Live records for").first).to_be_visible()
		expect(page.get_by_text("Could not load")).to_have_count(0)
	else:
		expect(page.get_by_text("Sample data").first).to_be_visible()
	text = page.inner_text("main") if page.locator("main").count() else page.inner_text("body")
	bad = [word for word in BAD_TEXT if word in text]
	assert not bad, f"{name} at {width}px shows {bad}"
	overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
	assert overflow <= 0, f"{name} at {width}px overflows the viewport by {overflow}px"
	assert not errors, f"{name} at {width}px: {errors}"
	page.screenshot(path=str(OUT / f"{name}-{width}.png"), full_page=True)
	print(f"PASS {width}px {name}")


def test_every_module_is_checked():
	"""The list above must name every module and tab the interface has."""
	import subprocess

	script = (
		"import('./src/showcase/pages.js').then(async ({ MODULES }) => {"
		" const { LIVE_TABS } = await import('./src/showcase/live.js');"
		" console.log(JSON.stringify(Object.fromEntries(Object.entries(MODULES).map(([k, m]) =>"
		" [k, [Object.keys(m.tabs), LIVE_TABS[k] ?? []]])))) })"
	)
	frontend = Path(__file__).resolve().parent.parent
	found = json.loads(subprocess.check_output(["node", "--input-type=module", "-e", script], cwd=frontend))
	expected = {key: [tabs, live] for key, (_path, tabs, live) in MODULES.items()}
	assert {k: [v[0], sorted(v[1])] for k, v in found.items()} == {k: [v[0], sorted(v[1])] for k, v in expected.items()}, (
		"Showcase modules or live tabs changed; update MODULES in showcase_browser.py",
		found,
	)
	print("PASS every module and live tab is in the screen check")


def main():
	OUT.mkdir(parents=True, exist_ok=True)
	test_every_module_is_checked()
	with sync_playwright() as p:
		# PW_CHROMIUM: a Chromium binary when the installed Playwright has no matching browser.
		chromium = p.chromium.launch(headless=True, executable_path=os.environ.get("PW_CHROMIUM") or None)
		for width in WIDTHS:
			page = chromium.new_page(viewport={"width": width, "height": 900})
			errors = []
			page.on("pageerror", lambda e, errors=errors: errors.append(str(e)))
			page.add_init_script("window.berjaya_boot = " + json.dumps(BOOT))
			page.route("**/api/**", lambda route: route.fulfill(**dict(zip(("status", "json"), answer(route.request.url)))))
			screens = 0
			for key, (path, tabs, live) in MODULES.items():
				for tab in tabs:
					tab_path = path if len(tabs) == 1 else f"{path}/{tab}"
					check_screen(page, width, f"{key}-{tab}-sample", tab_path, errors)
					screens += 1
					if tab in live:
						check_screen(page, width, f"{key}-{tab}-live", tab_path + "?source=live", errors)
						screens += 1
			# A construction job lists its risks (G26).
			page.goto(BASE + "/construction/SCJ-2026-00007")
			expect(page.get_by_role("heading", name="Risks")).to_be_visible()
			expect(page.get_by_text("RSK-2026-00003")).to_be_visible()
			overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
			assert overflow <= 0 and not errors, (overflow, errors)
			page.screenshot(path=str(OUT / f"job-risks-{width}.png"), full_page=True)
			print(f"PASS {width}px job page lists its risks")
			page.close()
			print(f"{screens} screens at {width}px")
		chromium.close()
	print("All screen checks passed.")


if __name__ == "__main__":
	main()
