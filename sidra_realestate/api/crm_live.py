# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Live records for the Berjaya CRM dashboard (15 Nov 2026).

Read only, from ERPNext's own CRM records: Lead (with its Lead Source, the channel the lead came
through: WhatsApp, Email, Phone Call, ...), Opportunity, Customer and Sidra Customer KYC. Every list
goes through `frappe.get_list`, so role permissions and Company User Permissions are the boundary.
A group the role cannot read comes back unavailable with a reason, never as zero. Opportunity
amounts are exact two-place decimal strings. Nothing is changed.
"""

from collections import Counter, defaultdict

import frappe
from frappe import _
from frappe.utils import add_months, getdate, nowdate

from sidra_realestate.api.staff_dashboard import _staff_only, total

MONTHS = 12
NO_CHANNEL = "Not recorded"


def _readable(doctype) -> bool:
	return bool(frappe.db.exists("DocType", doctype)) and bool(frappe.has_permission(doctype, "read"))


def _unavailable(reason, **empty):
	return {"available": False, "reason": reason, **empty}


@frappe.whitelist(methods=["GET"])
def get_crm_live(company: str) -> dict:
	"""Leads by channel, status and month; opportunities by stage; customers and their KYC."""
	_staff_only()
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Choose a Company"))
	today = getdate(nowdate())
	return {
		"company": company,
		"currency": frappe.get_cached_value("Company", company, "default_currency"),
		"today": str(today),
		"leads": _leads(company, today),
		"opportunities": _opportunities(company),
		"customers": _customers(),
	}


def _leads(company, today):
	if not _readable("Lead"):
		return _unavailable(_("Your role does not include leads."), total=0, rows=[])
	rows = frappe.get_list(
		"Lead",
		filters={"company": company},
		fields=["name", "lead_name", "company_name", "source", "status", "creation"],
		order_by="creation desc",
		limit_page_length=0,
	)
	first = add_months(today.replace(day=1), -(MONTHS - 1))
	months = [str(add_months(first, i))[:7] for i in range(MONTHS)]
	per_month = Counter(str(r.creation)[:7] for r in rows)
	return {
		"available": True,
		"reason": None,
		"total": len(rows),
		"by_channel": dict(Counter(r.source or NO_CHANNEL for r in rows).most_common()),
		"by_status": dict(Counter(r.status or NO_CHANNEL for r in rows).most_common()),
		"months": [{"month": m, "count": per_month.get(m, 0)} for m in months],
		"rows": [
			{
				"name": r.name,
				"lead": r.lead_name or r.company_name or r.name,
				"channel": r.source or NO_CHANNEL,
				"status": r.status,
				"created": str(r.creation)[:10],
			}
			for r in rows[:10]
		],
	}


def _opportunities(company):
	if not _readable("Opportunity"):
		return _unavailable(_("Your role does not include opportunities."), stages=[], rows=[])
	rows = frappe.get_list(
		"Opportunity",
		filters={"company": company},
		fields=["name", "party_name", "sales_stage", "status", "opportunity_amount", "expected_closing"],
		order_by="modified desc",
		limit_page_length=0,
	)
	count, amounts = Counter(), defaultdict(list)
	for r in rows:
		stage = r.sales_stage or NO_CHANNEL
		count[stage] += 1
		if r.opportunity_amount is not None:
			amounts[stage].append(r.opportunity_amount)
	open_rows = [r for r in rows if r.status in ("Open", "Replied", "Quotation")]
	return {
		"available": True,
		"reason": None,
		"total": len(rows),
		"open": len(open_rows),
		"open_amount": total([r.opportunity_amount for r in open_rows if r.opportunity_amount is not None])
		if open_rows
		else "0.00",
		"by_status": dict(Counter(r.status for r in rows).most_common()),
		"stages": [
			{"stage": stage, "count": n, "amount": total(amounts[stage]) if amounts[stage] else None}
			for stage, n in count.most_common()
		],
		"rows": [
			{
				"name": r.name,
				"party": r.party_name,
				"stage": r.sales_stage,
				"status": r.status,
				"amount": total([r.opportunity_amount]) if r.opportunity_amount is not None else None,
				"expected_closing": str(r.expected_closing) if r.expected_closing else None,
			}
			for r in rows[:10]
		],
	}


def _customers():
	if not _readable("Customer"):
		return _unavailable(_("Your role does not include customers."), total=0, kyc={})
	customers = frappe.get_list("Customer", filters={"disabled": 0}, pluck="name", limit_page_length=0)
	kyc = None
	if _readable("Sidra Customer KYC"):
		kyc = dict(
			Counter(frappe.get_list("Sidra Customer KYC", pluck="status", limit_page_length=0)).most_common()
		)
	return {
		"available": True,
		"reason": None,
		"total": len(customers),
		# None: this role may not read KYC (restricted, G12); never shown as zero.
		"kyc": kyc,
	}
