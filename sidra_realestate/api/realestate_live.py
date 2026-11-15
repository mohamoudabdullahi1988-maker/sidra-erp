# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Live records for the Berjaya Real Estate Sales screens (decision G25; demonstration 17 Nov 2026).

Read only. Every list goes through `frappe.get_list`, so role permissions and Company User
Permissions are the security boundary; schedule rows are read only for contracts the user may
read. A group the role cannot read is returned unavailable with a reason, never as zero. Money is
an exact two-place decimal string, or null when any amount is missing (unknown is never zero).

Installment schedules are obligations, not receipts: payments are not recorded in ERPNext yet
(D8), so nothing here says what was collected or what is overdue.
"""

from collections import Counter, defaultdict

import frappe
from frappe import _
from frappe.utils import add_days, add_months, getdate, nowdate

from sidra_realestate.api.live_period import block, period, within
from sidra_realestate.api.location_geometry import extract_point
from sidra_realestate.api.staff_dashboard import _staff_only, total

UNIT = "Sidra Unit"
CONTRACT = "Sidra Sale Contract"
RESERVATION = "Sidra Reservation"
LEAD = "Lead"
CONTRACT_STATUS = {0: "Draft", 1: "Confirmed", 2: "Cancelled"}
SCHEDULE_MONTHS = 12


def _readable(doctype) -> bool:
	return bool(frappe.db.exists("DocType", doctype)) and bool(frappe.has_permission(doctype, "read"))


def _unavailable(reason, **empty):
	return {"available": False, "reason": reason, **empty}


@frappe.whitelist(methods=["GET"])
def get_realestate_live(company: str, from_date: str | None = None, to_date: str | None = None) -> dict:
	"""Units by scheme and status, reservations, contracts, the coming schedule and lead stages.

	Reservations made, contracts signed and leads created in the period (live_period); units, the
	coming schedule and reservations about to expire are as they are today.
	"""
	_staff_only()
	# Every list below is filtered by this Company through get_list, so a Company the user's
	# User Permissions exclude returns nothing; no record is read around the permission check.
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Choose a Company"))
	today = getdate(nowdate())
	start, to = period(from_date, to_date)
	contracts = _contracts(company)
	return {
		"company": company,
		"currency": frappe.get_cached_value("Company", company, "default_currency"),
		"today": str(today),
		"units": _units(company),
		"period": block(start, to, ["reservations", "contracts", "leads"], ["units", "schedule", "expiring"]),
		"reservations": _reservations(company, today, start, to),
		# The schedule is every confirmed contract's coming installments; the list shows the period's.
		"contracts": _in_period(contracts, start, to),
		"schedule": _schedule(contracts, today),
		"leads": _leads(company, start, to),
	}


def _units(company):
	if not _readable(UNIT):
		return _unavailable(_("Your role does not include units."), schemes=[], rows=[])
	units = frappe.get_list(
		UNIT,
		filters={"company": company},
		fields=["name", "unit_code", "scheme", "status", "unit_type", "cash_price", "sidra_location"],
		limit_page_length=0,
	)
	scheme_names = {}
	if units and _readable("Sidra Scheme"):
		scheme_names = {
			row.name: row.scheme_name or row.name
			for row in frappe.get_list(
				"Sidra Scheme",
				filters={"name": ["in", sorted({u.scheme for u in units if u.scheme})]},
				fields=["name", "scheme_name"],
				limit_page_length=0,
			)
		}
	by_scheme = defaultdict(Counter)
	for unit in units:
		by_scheme[unit.scheme][unit.status] += 1
	available = [u.cash_price for u in units if u.status == "Available"]
	return {
		"available": True,
		"reason": None,
		"total": len(units),
		"status_counts": dict(Counter(u.status for u in units)),
		"value_available": total(available) if available else None,
		"schemes": [
			{
				"scheme": scheme,
				"name": scheme_names.get(scheme, scheme),
				"counts": dict(counts),
				"total": sum(counts.values()),
			}
			for scheme, counts in sorted(by_scheme.items(), key=lambda item: -sum(item[1].values()))
		],
		"points": [
			{"unit": u.name, "code": u.unit_code, "status": u.status, "point": list(point)}
			for u in units
			if (point := extract_point(u.sidra_location))
		][:300],
	}


def _reservations(company, today, start, to):
	if not _readable(RESERVATION):
		return _unavailable(_("Your role does not include reservations."), counts={})
	rows = frappe.get_list(
		RESERVATION,
		filters={"company": company},
		fields=["name", "unit", "status", "expires_on", "creation"],
		limit_page_length=0,
	)
	made = [r for r in rows if start <= getdate(r.creation) <= to]
	expiring = [
		r
		for r in rows
		if r.status == "Active"
		and r.expires_on
		and today <= getdate(r.expires_on) <= getdate(add_days(today, 7))
	]
	return {
		"available": True,
		"reason": None,
		"counts": dict(Counter(r.status for r in made)),
		"expiring": [{"name": r.name, "unit": r.unit, "expires_on": str(r.expires_on)} for r in expiring],
	}


def _contracts(company):
	if not _readable(CONTRACT):
		return _unavailable(_("Your role does not include sale contracts."), rows=[])
	rows = frappe.get_list(
		CONTRACT,
		filters={"company": company},
		fields=[
			"name",
			"customer",
			"contract_type",
			"source",
			"docstatus",
			"signed_on",
			"creation",
			"agreed_price",
			"amount_due",
			"installments",
			"currency",
		],
		order_by="modified desc",
		limit_page_length=0,
	)
	return {
		"available": True,
		"reason": None,
		"status_counts": dict(Counter(CONTRACT_STATUS.get(r.docstatus, "Draft") for r in rows)),
		"rows": [
			{
				"name": r.name,
				"customer": r.customer,
				"type": r.contract_type,
				"source": r.source,
				"status": CONTRACT_STATUS.get(r.docstatus, "Draft"),
				"signed_on": str(r.signed_on) if r.signed_on else None,
				"dated": str(getdate(r.signed_on or r.creation)),
				"agreed_price": total([r.agreed_price]) if r.agreed_price is not None else None,
				"installments": r.installments,
				"currency": r.currency,
			}
			for r in rows
		],
	}


def _in_period(contracts, start, to):
	"""The contracts signed in the period (a draft without a signing date: when it was created)."""
	if not contracts["available"]:
		return contracts
	rows = [r for r in contracts["rows"] if start <= getdate(r["dated"]) <= to]
	return {
		**contracts,
		"status_counts": dict(Counter(r["status"] for r in rows)),
		"rows": rows,
	}


def _schedule(contracts, today):
	"""Amounts scheduled per month on confirmed contracts, from this month on. Obligations only."""
	if not contracts["available"]:
		return _unavailable(contracts["reason"], months=[])
	confirmed = [r["name"] for r in contracts["rows"] if r["status"] == "Confirmed"]
	first = today.replace(day=1)
	months = [str(add_months(first, i))[:7] for i in range(SCHEDULE_MONTHS)]
	if not confirmed:
		return {
			"available": True,
			"reason": None,
			"total": "0.00",
			"months": [{"month": m, "amount": "0.00", "rows": 0} for m in months],
		}
	rows = frappe.get_all(  # child rows of contracts the user may read (listed above)
		"Sidra Installment Line",
		filters={
			"parenttype": CONTRACT,
			"parent": ["in", confirmed],
			"due_date": ["between", [first, add_months(first, SCHEDULE_MONTHS)]],
		},
		fields=["due_date", "amount"],
		limit_page_length=0,
	)
	amounts = defaultdict(list)
	for row in rows:
		amounts[str(row.due_date)[:7]].append(row.amount)
	return {
		"available": True,
		"reason": None,
		"total": total([value for m in months for value in amounts[m]]),
		"months": [
			{"month": m, "amount": total(amounts[m]) if amounts[m] else "0.00", "rows": len(amounts[m])}
			for m in months
		],
	}


def _leads(company, start, to):
	if not _readable(LEAD):
		return _unavailable(_("Your role does not include leads."), status_counts={}, source_counts={})
	from sidra_realestate.services.crm_channels import channel_field

	channel = channel_field(LEAD)
	rows = frappe.get_list(
		LEAD,
		filters=[["company", "=", company], *within("creation", start, to)],
		fields=["status"] + ([f"{channel} as channel"] if channel else []),
		limit_page_length=0,
	)
	return {
		"available": True,
		"reason": None,
		"total": len(rows),
		"status_counts": dict(Counter(r.status or "Not set" for r in rows)),
		"source_counts": dict(Counter(r.get("channel") or "Not set" for r in rows)),
	}
