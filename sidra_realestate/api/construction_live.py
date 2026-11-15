# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Live construction records for the Berjaya Construction screens (decision G25, step 1).

Read only. Every list goes through `frappe.get_list`, so role permissions and Company User
Permissions are the security boundary; stages are read only for jobs the user may read. A group
the user's role cannot read is returned unavailable with a reason, never as zero. Money is an
exact two-place decimal string, or null when nothing is recorded (unknown is never zero).
Nothing is computed that the records do not state: progress is the average of recorded stage
completion, and a job without stages has no progress.
"""

import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from sidra_realestate.api.location_geometry import extract_point, legacy_point
from sidra_realestate.api.staff_dashboard import _staff_only, money

JOB = "Sidra Construction Job"
VARIATION = "Sidra Variation Order"
INSPECTION = "Sidra Inspection Report"
RISK = "Sidra Project Risk"
DOCSTATUS = {0: "Draft", 1: "Approved", 2: "Cancelled"}
INSPECTION_STATUS = {0: "Draft", 1: "Issued", 2: "Cancelled"}


def _readable(doctype) -> bool:
	return bool(frappe.db.exists("DocType", doctype)) and bool(frappe.has_permission(doctype, "read"))


def _unavailable(reason):
	return {"available": False, "reason": reason, "rows": []}


@frappe.whitelist(methods=["GET"])
def get_construction_live(company: str) -> dict:
	"""Jobs with their stages, variation orders and inspection reports for one Company."""
	_staff_only()
	# Each list below is filtered by this Company through get_list, so a Company the user's
	# User Permissions exclude returns nothing; no record is read around the permission check.
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Choose a Company"))
	today = getdate(nowdate())
	jobs = _jobs(company, today)
	return {
		"company": company,
		"currency": frappe.get_cached_value("Company", company, "default_currency"),
		"today": str(today),
		"jobs": jobs,
		"variations": _variations(company),
		"inspections": _inspections(company),
		"risks": _risks(company),
	}


def _jobs(company, today):
	if not _readable(JOB):
		return _unavailable(_("Your role does not include construction jobs."))
	jobs = frappe.get_list(
		JOB,
		filters={"company": company},
		fields=[
			"name",
			"customer",
			"status",
			"service_type",
			"site_location",
			"sidra_location",
			"gps",
			"contract_value",
			"approved_variations",
			"current_contract_value",
			"boq_total",
			"contract_start_date",
			"contract_end_date",
		],
		order_by="modified desc",
		limit_page_length=0,
	)
	stages = (
		frappe.get_all(
			"Sidra Project Stage",
			filters={"parenttype": JOB, "parent": ["in", [j.name for j in jobs]]},
			fields=[
				"parent",
				"idx",
				"stage_name",
				"status",
				"planned_start",
				"planned_end",
				"actual_end",
				"completion_pct",
				"certified",
				"billing_pct",
				"billing_amount",
			],
			order_by="idx asc",
			limit_page_length=0,
		)
		if jobs
		else []
	)
	by_job = {}
	for stage in stages:
		by_job.setdefault(stage.parent, []).append(stage)
	rows = []
	for job in jobs:
		own = by_job.get(job.name, [])
		point = extract_point(job.sidra_location) or legacy_point(job.gps)
		overdue = [
			s for s in own if s.status != "Completed" and s.planned_end and getdate(s.planned_end) < today
		]
		starts = [s.planned_start for s in own if s.planned_start]
		ends = [s.planned_end for s in own if s.planned_end]
		rows.append(
			{
				"name": job.name,
				"customer": job.customer,
				"status": job.status,
				"service_type": job.service_type,
				"site": job.site_location,
				"point": list(point) if point else None,  # [latitude, longitude]
				"contract_value": money(job.contract_value),
				"approved_variations": money(job.approved_variations),
				"current_contract_value": money(job.current_contract_value),
				"boq_total": money(job.boq_total),
				# Each stage as recorded (Schedule and Cost & budget tabs). Billing amounts are
				# payment milestones, not invoices: nothing is invoiced before P2 (CON-07).
				"stage_rows": [
					{
						"stage": s.stage_name,
						"status": s.status,
						"planned_start": str(s.planned_start) if s.planned_start else None,
						"planned_end": str(s.planned_end) if s.planned_end else None,
						"actual_end": str(s.actual_end) if s.actual_end else None,
						"completion_pct": float(s.completion_pct or 0),
						"certified": bool(s.certified),
						"overdue": s in overdue,
						"billing_pct": float(s.billing_pct or 0),
						"billing_amount": money(s.billing_amount),
					}
					for s in own
				],
				"start": str(job.contract_start_date or (min(starts) if starts else "")) or None,
				"end": str(job.contract_end_date or (max(ends) if ends else "")) or None,
				"progress": round(sum(float(s.completion_pct or 0) for s in own) / len(own)) if own else None,
				"stages": len(own),
				"stages_completed": sum(1 for s in own if s.status == "Completed"),
				"stages_certified": sum(1 for s in own if s.certified),
				"stages_overdue": len(overdue),
			}
		)
	return {"available": True, "reason": None, "rows": rows}


def _variations(company):
	if not _readable(VARIATION):
		return _unavailable(_("Your role does not include variation orders."))
	rows = frappe.get_list(
		VARIATION,
		filters={"company": company},
		fields=[
			"name",
			"job",
			"amount",
			"docstatus",
			"description",
			"approved_by",
			"approved_on",
			"creation",
		],
		order_by="creation desc",
		limit_page_length=0,
	)
	return {
		"available": True,
		"reason": None,
		"rows": [
			{
				"name": r.name,
				"job": r.job,
				"amount": money(r.amount),
				"status": DOCSTATUS.get(r.docstatus, "Draft"),
				"description": (r.description or "")[:140],
				"approved_on": str(r.approved_on)[:10] if r.approved_on else None,
				"raised": str(r.creation)[:10],
			}
			for r in rows
		],
	}


def _inspections(company):
	if not _readable(INSPECTION):
		return _unavailable(_("Your role does not include inspection reports."))
	rows = frappe.get_list(
		INSPECTION,
		filters={"company": company},
		fields=["name", "job", "stage", "inspection_date", "result", "docstatus", "next_action_due"],
		order_by="inspection_date desc",
		limit_page_length=0,
	)
	return {
		"available": True,
		"reason": None,
		"rows": [
			{
				"name": r.name,
				"job": r.job,
				"stage": r.stage,
				"date": str(r.inspection_date) if r.inspection_date else None,
				"result": r.result or "Not recorded",
				"status": INSPECTION_STATUS.get(r.docstatus, "Draft"),
				"next_action_due": str(r.next_action_due) if r.next_action_due else None,
			}
			for r in rows
		],
	}


def _risks(company):
	"""The risk register (G26): every risk of this Company, open ones first by rating."""
	if not _readable(RISK):
		return _unavailable(_("Your role does not include the risk register."))
	rows = frappe.get_list(
		RISK,
		filters={"company": company},
		fields=[
			"name",
			"job",
			"scheme",
			"category",
			"description",
			"risk_owner",
			"rating",
			"status",
			"mitigation",
			"review_date",
			"closed_on",
		],
		order_by="modified desc",
		limit_page_length=0,
	)
	schemes = {}
	if any(r.scheme for r in rows) and _readable("Sidra Scheme"):
		schemes = {
			s.name: s.scheme_name
			for s in frappe.get_list(
				"Sidra Scheme",
				filters={"name": ["in", sorted({r.scheme for r in rows if r.scheme})]},
				fields=["name", "scheme_name"],
				limit_page_length=0,
			)
		}
	return {
		"available": True,
		"reason": None,
		"rows": [
			{
				"name": r.name,
				"job": r.job,
				# What the risk is about: the project's name, else the job, else the whole Company.
				"project": schemes.get(r.scheme) or r.scheme or r.job or _("All projects"),
				"category": r.category,
				"description": (r.description or "")[:140],
				"owner": r.risk_owner,
				"rating": r.rating,
				"status": r.status,
				"mitigation": (r.mitigation or "")[:140],
				"review_date": str(r.review_date) if r.review_date else None,
				"closed_on": str(r.closed_on) if r.closed_on else None,
			}
			for r in rows
		],
	}
