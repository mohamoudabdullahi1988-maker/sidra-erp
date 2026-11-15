"""Approve manifest-owned fictional construction quotations for the rehearsal.

Mohamoud, 15 Nov 2026: approve demo documents so live screens have values. Only construction
quotations for the pilot's own jobs are in scope. Missing quotations use the job's recorded BOQ.
Acceptance files explicitly say FICTIONAL DEMO. No sales contract, inspection, variation,
invoice, payment, ledger entry, customer or Company is changed. Normal submit/approve controls
run; all work rolls back on failure. A private manifest makes a rerun a no-op.
"""

import json

import frappe
from frappe.utils import add_days, date_diff, getdate, today

from sidra_realestate.finance_demo import COMPANY
from sidra_realestate.pilot_demo import MANIFEST as PILOT_MANIFEST
from sidra_realestate.pilot_demo import _guard, _read_manifest, _refuse_foreign_gl
from sidra_realestate.sidra_construction.doctype.sidra_construction_quotation.sidra_construction_quotation import (
	approve_contract,
)

MANIFEST = "sidra-pilot-approvals-v1.json"
SCHEMA = 1
QUOTE = "Sidra Construction Quotation"
JOB = "Sidra Construction Job"


def approve_pilot_quotations():
	_guard()
	pilot = _read_manifest(PILOT_MANIFEST, None)
	_refuse_foreign_gl()
	existing = _read_manifest(MANIFEST, SCHEMA, required=False)
	if existing:
		return {**existing, "created": False}
	try:
		data = _approve(pilot)
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": MANIFEST,
				"content": json.dumps(data, indent=2),
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


def _approve(pilot):
	owned = pilot.get("jobs", {})
	names = owned.get("jobs", [])
	if not names or not all(isinstance(name, str) for name in names):
		frappe.throw("Refusing: pilot job ownership is missing.")
	quotes = set(owned.get("quotations", []))
	approved, created, files, skipped = [], [], [], []
	for name in names:
		job = frappe.get_doc(JOB, name)
		if job.company != COMPANY:
			frappe.throw("Refusing: a pilot job belongs to another Company.")
		if job.contract_quotation:
			skipped.append(name)
			continue  # preserve an existing approval and its evidence
		candidates = frappe.get_all(QUOTE, filters={"job": name}, pluck="name")
		if any(q not in quotes for q in candidates) or len(candidates) > 1:
			frappe.throw(
				f"Refusing: {name} has a quotation outside the pilot's ownership or multiple quotations."
			)
		if candidates:
			quote = frappe.get_doc(QUOTE, candidates[0])
			if (
				quote.company != COMPANY
				or quote.docstatus != 0
				or quote.client_acceptance_document
				or quote.client_accepted_by
			):
				frappe.throw(
					f"Refusing: {quote.name} was already issued or has client acceptance; review it manually."
				)
			if getdate(quote.valid_until) < getdate(today()):
				quote.valid_until = add_days(today(), 30)
			quote.save()
		else:
			starts = [row.planned_start for row in job.stages if row.planned_start]
			ends = [row.planned_end for row in job.stages if row.planned_end]
			if not job.boq or not starts or not ends:
				frappe.throw(f"Refusing: {name} needs a recorded BOQ and planned dates.")
			quote = frappe.get_doc(
				{
					"doctype": QUOTE,
					"job": name,
					"pricing_basis": "BOQ",
					"scope": "FICTIONAL DEMO ONLY: quotation from this pilot job's recorded BOQ.",
					"start_date": min(starts),
					"duration_days": max(1, date_diff(max(ends), min(starts)) + 1),
					"valid_until": add_days(today(), 30),
					"retention_pct": 0,
					"retention_period_months": 0,
				}
			).insert()
			created.append(quote.name)
		quote.submit()
		file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"FICTIONAL-DEMO-acceptance-{quote.name}.txt",
				"content": f"FICTIONAL DEMO ONLY — NOT A REAL SIGNATURE OR CLIENT ACCEPTANCE.\nQuotation: {quote.name}\nJob: {job.name}\nDemonstration acceptance authorised by Mohamoud for the pilot rehearsal on {today()}.\n",
				"is_private": 1,
				"attached_to_doctype": QUOTE,
				"attached_to_name": quote.name,
			}
		).insert()
		files.append(file.name)
		quote.client_accepted_by = "FICTIONAL DEMO CLIENT (rehearsal only)"
		quote.client_accepted_on = today()
		quote.client_acceptance_document = file.file_url
		quote.save()
		approve_contract(quote.name)
		approved.append(quote.name)
	return {
		"schema": SCHEMA,
		"company": COMPANY,
		"approved_on": today(),
		"quotations_approved": approved,
		"quotations_created": created,
		"acceptance_files": files,
		"already_contracted_jobs": skipped,
	}
