"""Fictional risks for the risk register on the test site (decision G26, 15 Nov 2026).

On top of the pilot dataset and its top-up (`pilot_extras.py`), this loader once adds twelve
fictional project risks to the Company Sidra Homes, so the Construction → Risk tab has live records
to show. A risk is a record only: nothing is posted, approved or changed on a job or contract.
The guards are the pilot's: Administrator only, the three staging flags, the top-up's manifest must
exist, one transaction with full rollback, a private manifest of its own, and a rerun that changes
nothing.

	bench --site <staging> execute sidra_realestate.pilot_risks.create_pilot_risks
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import add_days

from sidra_realestate.finance_demo import COMPANY
from sidra_realestate.pilot_demo import _guard, _read_manifest
from sidra_realestate.pilot_extras import MANIFEST as EXTRAS_MANIFEST

MANIFEST = "sidra-pilot-risks-v1.json"
SCHEMA = 1
ALL = None  # a risk to every project: neither a project nor a job
JOB = "job"  # a risk to one construction job: the first pilot job

# (category, description, project name / ALL / JOB, owner, rating, status, mitigation, review in days)
RISKS = (
	(
		"Regulatory compliance",
		"Permit for Berbera Townhouses phase 2 not yet issued",
		"Berbera Townhouses",
		"Project Manager",
		"High",
		"Open",
		"Follow up weekly with the municipality",
		7,
	),
	(
		"Design errors",
		"Drawings revision for the extension option",
		"Safa Housing",
		"Design Lead",
		"Medium",
		"Mitigating",
		"Second check of revised drawings",
		14,
	),
	(
		"Scope creep",
		"Buyer requests for early extensions",
		"Safa Housing",
		"Project Manager",
		"Medium",
		"Open",
		"Extensions only through a variation order",
		14,
	),
	(
		"Labour shortages",
		"Skilled tilers scarce during the Hajj season",
		"Rayan Gardens",
		"Site Manager",
		"Low",
		"Monitoring",
		"Book two tiling crews in advance",
		30,
	),
	(
		"Material delivery",
		"Cement shipments delayed at Berbera port",
		ALL,
		"Procurement Officer",
		"High",
		"Mitigating",
		"Keep two weeks of cement on site",
		7,
	),
	(
		"Schedule delays",
		"Structure stage behind after a failed inspection",
		JOB,
		"Project Manager",
		"High",
		"Open",
		"Re-inspection booked; extra shift",
		5,
	),
	(
		"Cost overruns",
		"Steel price up since the budget",
		ALL,
		"Quantity Surveyor",
		"Medium",
		"Monitoring",
		"Review the BOQ at the next revision",
		21,
	),
	(
		"Equipment downtime",
		"Concrete pump due for overhaul",
		"Rayan Gardens",
		"Plant Manager",
		"Low",
		"Monitoring",
		"Hire a standby pump for pours",
		30,
	),
	(
		"Weather disruption",
		"Gu rains may flood the site access road",
		"Masalaha Hagbad",
		"Site Manager",
		"Medium",
		"Open",
		"Temporary drainage before the rains",
		10,
	),
	(
		"Safety hazards",
		"Work at height on townhouse roofs",
		"Berbera Townhouses",
		"Safety Officer",
		"Medium",
		"Mitigating",
		"Harness checks at every shift start",
		7,
	),
	(
		"Stakeholder disputes",
		"Neighbour boundary claim on one plot",
		"Masalaha Hagbad",
		"Legal Officer",
		"Low",
		"Open",
		"Survey the boundary with both parties",
		21,
	),
	(
		"Currency movement",
		"Shilling movement on local labour rates",
		ALL,
		"Finance Manager",
		"Low",
		"Closed",
		"Labour rates fixed in dollars",
		None,
	),
)


def create_pilot_risks():
	"""Create once and commit; a rerun returns the manifest and changes nothing."""
	_guard()
	if not _read_manifest(EXTRAS_MANIFEST, None, required=False):
		frappe.throw("Refusing: load the top-up first (pilot_extras.create_pilot_extras).")
	existing = _read_manifest(MANIFEST, SCHEMA, required=False)
	if existing:
		return {**existing, "created": False}
	try:
		data = _create()
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


def _create():
	today = datetime.now(ZoneInfo("Africa/Mogadishu")).date()
	schemes = dict(
		frappe.get_all(
			"Sidra Scheme", filters={"company": COMPANY}, fields=["scheme_name", "name"], as_list=True
		)
	)
	job = frappe.get_all(
		"Sidra Construction Job", filters={"company": COMPANY}, order_by="creation asc", pluck="name", limit=1
	)
	created = []
	for category, description, where, owner, rating, status, mitigation, review in RISKS:
		doc = frappe.get_doc(
			{
				"doctype": "Sidra Project Risk",
				"company": COMPANY,
				"scheme": schemes.get(where) if where not in (ALL, JOB) else None,
				"job": job[0] if where == JOB and job else None,
				"category": category,
				"description": description,
				"risk_owner": owner,
				"rating": rating,
				"status": status,
				"mitigation": mitigation,
				"review_date": add_days(today, review) if review is not None else None,
			}
		).insert()
		created.append(doc.name)
	return {"schema": SCHEMA, "company": COMPANY, "as_of": str(today), "risks": created}
