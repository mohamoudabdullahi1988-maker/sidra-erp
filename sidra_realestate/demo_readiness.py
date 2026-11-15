"""Read-only readiness check for the client demonstration (walkthrough v0.2, 17 Nov 2026).

Lists what `docs/DEMO-SCRIPT_v0.2.md` needs on the test site and whether it is there, with the
command or step that fixes each gap. It reads only: nothing is created, changed or posted, and no
password or personal value is printed.

	bench --site sidra.local execute sidra_realestate.demo_readiness.check_demo_readiness
"""

import os

import frappe

from sidra_realestate.demo import USERS
from sidra_realestate.finance_demo import COMPANY
from sidra_realestate.pilot_demo import MANIFEST as PILOT_MANIFEST
from sidra_realestate.pilot_extras import MANIFEST as EXTRAS_MANIFEST
from sidra_realestate.pilot_extras import PROJECTS
from sidra_realestate.services.pilot_dataset import PREFIX

BENCH = "cd /home/frappe/sidra/frappe-bench && sudo -u frappe bench --site sidra.local"
# The roles each demonstration user needs for its steps in the walkthrough (install.ROLE_PROFILES).
DEMO_ROLES = {
	"demo.sales@example.com": ("Sidra Sales User", "Sales User"),
	"demo.manager@example.com": ("Sidra Sales Manager",),
	"demo.gm@example.com": ("Sidra General Manager",),
	"demo.pm@example.com": ("Sidra Project Manager",),
}


def check_demo_readiness() -> dict:
	"""PASS / FAIL / WARN per item, each with what to do. Administrator only; reads only."""
	if frappe.session.user != "Administrator":
		frappe.throw(
			"Run the readiness check as Administrator through bench execute.", frappe.PermissionError
		)
	results = []

	def add(name, ok, detail, fix=None, warn=False):
		results.append(
			{
				"check": name,
				"status": "PASS" if ok else ("WARN" if warn else "FAIL"),
				"detail": detail,
				"fix": None if ok else fix,
			}
		)

	_interface(add)
	_data(add)
	_sales(add)
	_construction(add)
	_crm(add)
	_users(add)

	summary = {s: sum(r["status"] == s for r in results) for s in ("PASS", "WARN", "FAIL")}
	for r in results:
		print(
			f"{r['status']:5} {r['check']}: {r['detail']}" + (f"\n      fix: {r['fix']}" if r["fix"] else "")
		)
	print(f"\n{summary['PASS']} passed, {summary['WARN']} warnings, {summary['FAIL']} failed")
	return {"summary": summary, "results": results}


def _manifest(file_name):
	return frappe.db.exists(
		"File", {"attached_to_doctype": "Company", "attached_to_name": COMPANY, "file_name": file_name}
	)


def _interface(add):
	path = os.path.join(frappe.get_app_path("sidra_realestate"), "www", "berjaya.html")
	add(
		"Berjaya interface built",
		os.path.exists(path),
		"www/berjaya.html present" if os.path.exists(path) else "www/berjaya.html missing",
		"bash /root/berjaya-deploy_v0.1.sh",
	)


def _data(add):
	add(
		"Company",
		bool(frappe.db.exists("Company", COMPANY)),
		COMPANY,
		"The test Company is missing: see docs/PILOT-DEMO_v0.1.md.",
	)
	add(
		"Pilot dataset loaded",
		bool(_manifest(PILOT_MANIFEST)),
		"twelve-month fictional dataset (G16)",
		f"{BENCH} execute sidra_realestate.pilot_demo.create_pilot_demo_data",
	)
	add(
		"Top-up loaded",
		bool(_manifest(EXTRAS_MANIFEST)),
		"real project names, map points, inspections, leads",
		f"{BENCH} execute sidra_realestate.pilot_extras.create_pilot_extras",
	)
	names = set(
		frappe.get_all("Sidra Scheme", filters={"scheme_code": ("like", PREFIX + "-%")}, pluck="scheme_name")
	)
	wanted = {project[0] for project in PROJECTS.values()}
	add(
		"Real project names",
		wanted <= names,
		", ".join(sorted(names & wanted)) or "none of the project names found",
		f"{BENCH} execute sidra_realestate.pilot_extras.create_pilot_extras",
	)


def _sales(add):
	masalaha = frappe.db.get_value("Sidra Scheme", {"scheme_name": "Masalaha Hagbad"}, "name")
	available = (
		frappe.db.count("Sidra Unit", {"scheme": masalaha, "status": "Available", "company": COMPANY})
		if masalaha
		else 0
	)
	add(
		"A Masalaha Hagbad plot to sell",
		available >= 2,
		f"{available} available",
		"Reserve or sell fewer during rehearsal, or cancel a rehearsal reservation (Units → the unit → Cancel reservation).",
	)
	profiles = frappe.get_all(
		"Sidra Contract Profile", filters={"active": 1, "legal_hold": 0}, pluck="name", limit_page_length=0
	)
	add(
		"An active contract profile",
		bool(profiles),
		", ".join(profiles) or "none active without a legal hold",
		"Setup → Contract profiles: one active profile without a legal hold is needed for a generated contract.",
	)
	verified = frappe.db.count("Sidra Customer KYC", {"status": "Verified"})
	add(
		"Buyers with verified KYC",
		verified >= 1,
		f"{verified} verified",
		"Verify one buyer's KYC as demo.manager (CRM → KYC → Verify) before the meeting.",
	)


def _construction(add):
	jobs = frappe.get_all(
		"Sidra Construction Job",
		filters={"company": COMPANY},
		fields=["name", "sidra_location", "contract_quotation"],
		limit_page_length=0,
	)
	add("Construction jobs", len(jobs) >= 5, f"{len(jobs)} jobs", "Load the pilot dataset (see above).")
	placed = sum(1 for j in jobs if j.sidra_location)
	add(
		"Jobs on the map",
		placed >= 5,
		f"{placed} with a location",
		f"{BENCH} execute sidra_realestate.pilot_extras.create_pilot_extras",
	)
	reports = frappe.db.count("Sidra Inspection Report", {"company": COMPANY})
	add(
		"Inspection reports",
		reports >= 1,
		f"{reports} reports",
		f"{BENCH} execute sidra_realestate.pilot_extras.create_pilot_extras",
	)
	variations = frappe.db.count("Sidra Variation Order", {"company": COMPANY})
	add(
		"Variation orders",
		variations >= 1,
		f"{variations} orders",
		"Load the pilot dataset (see above).",
		warn=True,
	)


def _crm(add):
	leads = frappe.db.count("Lead", {"company": COMPANY}) if frappe.db.exists("DocType", "Lead") else 0
	opportunities = (
		frappe.db.count("Opportunity", {"company": COMPANY})
		if frappe.db.exists("DocType", "Opportunity")
		else 0
	)
	add(
		"Sales stage for new opportunities",
		bool(frappe.db.exists("Sales Stage", "Prospecting")),
		"ERPNext's default stage 'Prospecting' exists"
		if frappe.db.exists("Sales Stage", "Prospecting")
		else "missing",
		f"{BENCH} execute sidra_realestate.pilot_extras.create_pilot_extras  (adds ERPNext's standard sales stages)",
	)
	add(
		"CRM leads and opportunities",
		leads >= 1 and opportunities >= 1,
		f"{leads} leads, {opportunities} opportunities",
		f"{BENCH} execute sidra_realestate.pilot_extras.create_pilot_extras",
	)


def _users(add):
	for email, roles_needed in DEMO_ROLES.items():
		if not frappe.db.exists("User", email):
			add(
				f"User {email}",
				False,
				"does not exist",
				f"{BENCH} execute sidra_realestate.demo.ensure_demo_users  (then set the printed passwords)",
			)
			continue
		enabled = frappe.db.get_value("User", email, "enabled")
		roles = set(frappe.get_roles(email))
		missing = [role for role in roles_needed if role not in roles]
		# Whether a password is set (Frappe's __Auth table); the password itself is never read.
		has_password = bool(
			frappe.db.sql(
				"select 1 from `__Auth` where doctype='User' and name=%s and fieldname='password' limit 1",
				email,
			)
		)
		problems = []
		if not enabled:
			problems.append("disabled")
		if missing:
			problems.append("missing roles: " + ", ".join(missing))
		if not has_password:
			problems.append("no password set")
		add(
			f"User {email}",
			not problems,
			"ready" if not problems else "; ".join(problems),
			f"{BENCH} set-password {email} <password>"
			if problems == ["no password set"]
			else f"Give {email} the role profile '{USERS.get(email)}' (Desk → User), enable it, and set a password.",
		)
	sales_reads_leads = frappe.db.exists("User", "demo.sales@example.com") and frappe.has_permission(
		"Lead", "read", user="demo.sales@example.com"
	)
	add(
		"Sales staff can open CRM leads",
		bool(sales_reads_leads),
		"demo.sales may read Lead" if sales_reads_leads else "demo.sales cannot read Lead",
		"demo.sales needs ERPNext's Sales User role (role profile 'Sidra Sales Staff').",
		warn=True,
	)
