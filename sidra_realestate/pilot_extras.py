"""Top-up for the pilot demonstration dataset (G16): real project names and the records it lacks.

Mohamoud, 15 Nov 2026, for the client demonstration: live screens show existing records, missing
ones are created, and Sidra's real project names are used. On top of `pilot_demo.py`'s dataset
this loader, once:

- names the four pilot schemes after Sidra's projects (Masalaha Hagbad, Rayan Gardens, Safa
  Housing, Berbera Townhouses; scheme codes stay SHP-...), and points each pilot construction
  job's site at its project with a map location;
- adds the inspection reports the pilot plan marks but never created;
- adds fictional CRM records: leads (prefixed "SHP") and opportunities from some of them.

Every person is fictional (rule 8); no phone number or email is invented. Nothing is posted,
invoiced or approved. The guards are the pilot's: Administrator only, the three staging flags,
the pilot's own manifest must exist, one transaction with full rollback, a private manifest of
its own, and a rerun that changes nothing.

	bench --site <staging> execute sidra_realestate.pilot_extras.create_pilot_extras
"""

import json
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import frappe

from sidra_realestate.finance_demo import COMPANY
from sidra_realestate.pilot_demo import MANIFEST as PILOT_MANIFEST
from sidra_realestate.pilot_demo import _guard, _read_manifest
from sidra_realestate.services.construction import CLOSED_STATUSES
from sidra_realestate.services.pilot_dataset import FAMILY, GIVEN, PREFIX

MANIFEST = "sidra-pilot-extras-v1.json"
SCHEMA = 1

# Pilot scheme code -> Sidra's project, its district and area, and a map point (latitude,
# longitude; approximate, for the map only).
PROJECTS = {
	f"{PREFIX}-HARGEISA-E": ("Masalaha Hagbad", "Hargeisa", "Masalaha", (9.5205, 44.1062)),
	f"{PREFIX}-HARGEISA-N": ("Rayan Gardens", "Hargeisa", "Masalaha", (9.5281, 44.1149)),
	f"{PREFIX}-BURCO-W": ("Safa Housing", "Hargeisa", "Airport Road", (9.5452, 44.0756)),
	f"{PREFIX}-BERBERA-C": ("Berbera Townhouses", "Berbera", "Berbera coast", (10.4352, 45.0158)),
}
INSPECTION_RESULTS = ("Pass", "Pass", "Pass with defects", "Fail")
LEAD_STATUSES = ("Lead", "Open", "Replied", "Interested", "Lead", "Open")
LEAD_SOURCES = ("Walk In", "Reference", "Advertisement", "Campaign", "Cold Calling")
SALES_STAGES = (
	"Prospecting",
	"Qualification",
	"Needs Analysis",
	"Proposal/Price Quote",
	"Negotiation/Review",
)


def create_pilot_extras():
	"""Create once and commit; a rerun returns the manifest and changes nothing."""
	_guard()
	pilot = _read_manifest(PILOT_MANIFEST, None, required=False)
	if not pilot:
		frappe.throw("Refusing: load the pilot dataset first (pilot_demo.create_pilot_demo_data).")
	existing = _read_manifest(MANIFEST, SCHEMA, required=False)
	if existing:
		return {**existing, "created": False}
	try:
		data = _create(pilot)
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": MANIFEST,
				"content": json.dumps(data, indent=2, default=str),
				"is_private": 1,
				"attached_to_doctype": "Company",
				"attached_to_name": COMPANY,
			}
		).insert()
	except Exception:
		frappe.db.rollback()
		raise
	frappe.db.commit()
	return {**data, "created": True}


def _create(pilot):
	today = datetime.now(ZoneInfo("Africa/Mogadishu")).date()
	rng = random.Random(15112026)
	return {
		"schema": SCHEMA,
		"company": COMPANY,
		"as_of": str(today),
		"schemes": _name_schemes(),
		"jobs": _place_jobs(pilot, rng),
		"inspections": _inspections(pilot, today, rng),
		**_crm(today, rng),
	}


def _name_schemes():
	"""Give each pilot scheme its project's name; the previous values are kept in the manifest."""
	renamed = []
	for code, (name, district, area, _point) in PROJECTS.items():
		before = frappe.db.get_value(
			"Sidra Scheme",
			{"scheme_code": code},
			["name", "scheme_name", "district", "neighbourhood"],
			as_dict=True,
		)
		if not before:
			continue
		frappe.db.set_value(
			"Sidra Scheme",
			before.name,
			{"scheme_name": name, "district": district, "neighbourhood": area},
			update_modified=False,
		)
		renamed.append({"scheme": before.name, "code": code, "before": before.scheme_name, "after": name})
	return renamed


def _project_of(plot_number):
	for code, project in PROJECTS.items():
		if (plot_number or "").startswith(code):
			return project
	return None


def _place_jobs(pilot, rng):
	"""Each pilot job's site names its project, with a point near it for the map."""
	placed = []
	for job in pilot.get("jobs", {}).get("jobs", []):
		plot = frappe.db.get_value("Sidra Construction Job", job, "plot_number")
		project = _project_of(plot)
		if not project:
			continue
		name, _district, _area, (lat, lng) = project
		point = {
			"type": "FeatureCollection",
			"features": [
				{
					"type": "Feature",
					"properties": {},
					"geometry": {
						"type": "Point",
						"coordinates": [
							round(lng + rng.uniform(-0.004, 0.004), 6),
							round(lat + rng.uniform(-0.004, 0.004), 6),
						],
					},
				}
			],
		}
		frappe.db.set_value(
			"Sidra Construction Job",
			job,
			{"site_location": f"{name}, plot {plot.rsplit('-', 1)[-1]}", "sidra_location": json.dumps(point)},
			update_modified=False,
		)
		placed.append(job)
	return placed


def _inspections(pilot, today, rng):
	"""Reports for open pilot jobs: on a stage the job has, dated in the past, never submitted."""
	created = []
	jobs = pilot.get("jobs", {}).get("jobs", [])
	for index, job in enumerate(jobs):
		if index % 2:
			continue
		doc = frappe.get_doc("Sidra Construction Job", job)
		# Any job that is not closed: the pilot jobs keep their default status (the pilot plan's
		# statuses are not applied by its loader), so the status itself is not a filter here.
		if doc.status in CLOSED_STATUSES or not doc.stages:
			continue
		stage = next((s for s in doc.stages if s.status != "Planned"), doc.stages[0])
		result = INSPECTION_RESULTS[len(created) % len(INSPECTION_RESULTS)]
		failed = result == "Fail"
		report = frappe.get_doc(
			{
				"doctype": "Sidra Inspection Report",
				"job": job,
				"company": COMPANY,
				"stage": stage.stage_name,
				"inspection_date": today - timedelta(days=rng.randint(2, 60)),
				"inspector": "Administrator",
				"result": result,
				"checklist": [
					{"item": "Setting out and levels (pilot)", "result": "Pass"},
					{
						"item": "Reinforcement and cover (pilot)",
						"result": "Fail" if failed else "Pass",
						"remarks": "Cover below drawing at two points (pilot)" if failed else "",
					},
				],
				"defects_found": "" if result == "Pass" else "Pilot: minor honeycombing and low cover found.",
				"next_action": "" if result == "Pass" else "Pilot: repair and call for re-inspection.",
			}
		).insert(ignore_permissions=True)
		created.append(report.name)
	return created


def _crm(today, rng):
	"""Fictional leads, and opportunities from some of them (CRM, 15 Nov 2026)."""
	sources = [s for s in LEAD_SOURCES if frappe.db.exists("UTM Source", s)]
	# ERPNext's standard sales stages (its setup wizard creates them; a bare site may lack them,
	# and a new Opportunity defaults to "Prospecting"). Only missing ones are added.
	added_stages = []
	for stage in SALES_STAGES:
		if not frappe.db.exists("Sales Stage", stage):
			frappe.get_doc({"doctype": "Sales Stage", "stage_name": stage}).insert(ignore_permissions=True)
			added_stages.append(stage)
	stages = list(SALES_STAGES)
	sales_type = "Sales" if frappe.db.exists("Opportunity Type", "Sales") else None
	projects = [p[0] for p in PROJECTS.values()]
	leads, opportunities = [], []
	for index in range(30):
		lead = frappe.get_doc(
			{
				"doctype": "Lead",
				"first_name": f"{PREFIX} {rng.choice(GIVEN)}",
				"last_name": rng.choice(FAMILY),
				"status": LEAD_STATUSES[index % len(LEAD_STATUSES)],
				"utm_source": sources[index % len(sources)] if sources else None,
				"company": COMPANY,
				"city": "Berbera" if index % 5 == 0 else "Hargeisa",
				"country": "Somalia" if frappe.db.exists("Country", "Somalia") else None,
				"qualification_status": ("Unqualified", "In Process", "Qualified")[index % 3],
			}
		).insert(ignore_permissions=True)
		leads.append(lead.name)
		if index % 3:
			continue
		opportunity = frappe.get_doc(
			{
				"doctype": "Opportunity",
				"opportunity_from": "Lead",
				"party_name": lead.name,
				"company": COMPANY,
				"currency": "USD",
				"opportunity_type": sales_type,
				"sales_stage": stages[(index // 3) % len(stages)],
				"utm_source": lead.utm_source,
				"opportunity_amount": (14300, 7150, 68000, 38000, 86000)[(index // 3) % 5],
				"probability": (20, 40, 60, 75, 90)[(index // 3) % 5],
				"expected_closing": today + timedelta(days=15 + index * 3),
				"title": f"{lead.lead_name}: {projects[(index // 3) % len(projects)]}",
			}
		).insert(ignore_permissions=True)
		opportunities.append(opportunity.name)
	return {"leads": leads, "opportunities": opportunities, "sales_stages_added": added_stages}
