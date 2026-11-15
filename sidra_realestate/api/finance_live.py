# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Live records for the Berjaya Finance overview, Subcontractors and Stock screens (15 Nov 2026).

Read only, from ERPNext's own ledger and masters; ERPNext stays the only ledger (G4). Every list
goes through `frappe.get_list`, so role permissions and Company User Permissions are the boundary.
A group the role cannot read comes back unavailable with a reason, never as zero. Money is an
exact two-place decimal string (unknown is never zero). Nothing is posted or changed.
"""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_months, getdate, nowdate

from sidra_realestate.api.staff_dashboard import _staff_only, total

MONTHS = 12
AGE_BUCKETS = (
	("Not yet due", None),
	("1-30 days", 30),
	("31-60 days", 60),
	("61-90 days", 90),
	("90+ days", 10**6),
)


def _readable(doctype) -> bool:
	return bool(frappe.db.exists("DocType", doctype)) and bool(frappe.has_permission(doctype, "read"))


def _unavailable(reason, **empty):
	return {"available": False, "reason": reason, **empty}


def _company(company):
	_staff_only()
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Choose a Company"))
	return getdate(nowdate())


@frappe.whitelist(methods=["GET"])
def get_finance_live(company: str) -> dict:
	"""Income and expenses per month, cash and bank, and what is owed both ways, from the ledger."""
	today = _company(company)
	return {
		"company": company,
		"currency": frappe.get_cached_value("Company", company, "default_currency"),
		"today": str(today),
		"pnl": _pnl(company, today),
		"cash": _cash(company),
		"receivables": _ageing("Sales Invoice", "customer", company, today),
		"payables": _ageing("Purchase Invoice", "supplier", company, today),
	}


def _accounts(company, field, values):
	return {
		a.name: a
		for a in frappe.get_list(
			"Account",
			filters={"company": company, field: ["in", values], "is_group": 0},
			fields=["name", "account_name", "root_type", "account_type"],
			limit_page_length=0,
		)
	}


def _pnl(company, today):
	if not (_readable("GL Entry") and _readable("Account")):
		return _unavailable(_("Your role does not include the ledger."), months=[])
	first = add_months(today.replace(day=1), -(MONTHS - 1))
	accounts = _accounts(company, "root_type", ["Income", "Expense"])
	months = [str(add_months(first, i))[:7] for i in range(MONTHS)]
	income, expense = defaultdict(list), defaultdict(list)
	by_account = defaultdict(list)
	if accounts:
		for row in frappe.get_list(
			"GL Entry",
			filters={
				"company": company,
				"is_cancelled": 0,
				"account": ["in", list(accounts)],
				"posting_date": [">=", first],
			},
			fields=["posting_date", "account", "debit", "credit"],
			limit_page_length=0,
		):
			month = str(row.posting_date)[:7]
			if accounts[row.account].root_type == "Income":
				income[month].append(row.credit - row.debit)
			else:
				expense[month].append(row.debit - row.credit)
				by_account[accounts[row.account].account_name].append(row.debit - row.credit)
	return {
		"available": True,
		"reason": None,
		"months": [
			{"month": m, "income": total(income[m]) or "0.00", "expense": total(expense[m]) or "0.00"}
			for m in months
		],
		"expense_accounts": sorted(
			({"account": name, "amount": total(values)} for name, values in by_account.items()),
			key=lambda row: -float(row["amount"] or 0),
		)[:8],
	}


def _cash(company):
	if not (_readable("GL Entry") and _readable("Account")):
		return _unavailable(_("Your role does not include the ledger."), accounts=[])
	accounts = _accounts(company, "account_type", ["Bank", "Cash"])
	balances = defaultdict(list)
	if accounts:
		for row in frappe.get_list(
			"GL Entry",
			filters={"company": company, "is_cancelled": 0, "account": ["in", list(accounts)]},
			fields=["account", "debit", "credit"],
			limit_page_length=0,
		):
			balances[row.account].append(row.debit - row.credit)
	return {
		"available": True,
		"reason": None,
		"accounts": [
			{
				"account": accounts[name].account_name,
				"type": accounts[name].account_type,
				"balance": total(balances[name]) if balances[name] else "0.00",
			}
			for name in sorted(accounts)
		],
	}


def _ageing(doctype, party_field, company, today):
	if not _readable(doctype):
		return _unavailable(_("Your role does not include {0}.").format(_(doctype)), buckets=[], parties=[])
	rows = frappe.get_list(
		doctype,
		filters={"company": company, "docstatus": 1, "outstanding_amount": [">", 0]},
		fields=[party_field, "due_date", "outstanding_amount"],
		limit_page_length=0,
	)
	buckets = defaultdict(list)
	by_party = defaultdict(list)
	for row in rows:
		days = (today - getdate(row.due_date)).days if row.due_date else 0
		label = next(
			name for name, limit in AGE_BUCKETS if (limit is None and days <= 0) or (limit and days <= limit)
		)
		buckets[label].append(row.outstanding_amount)
		by_party[row.get(party_field)].append(row.outstanding_amount)
	return {
		"available": True,
		"reason": None,
		"buckets": [
			{
				"age": name,
				"amount": total(buckets[name]) if buckets[name] else "0.00",
				"count": len(buckets[name]),
			}
			for name, _limit in AGE_BUCKETS
		],
		"parties": sorted(
			({"party": party, "amount": total(values)} for party, values in by_party.items()),
			key=lambda row: -float(row["amount"] or 0),
		)[:10],
	}


@frappe.whitelist(methods=["GET"])
def get_operations_live(company: str) -> dict:
	"""Suppliers and subcontractors with what was invoiced and is still owed; stock on hand."""
	today = _company(company)
	return {
		"company": company,
		"currency": frappe.get_cached_value("Company", company, "default_currency"),
		"today": str(today),
		"suppliers": _suppliers(company),
		"stock": _stock(company),
	}


def _suppliers(company):
	if not (_readable("Supplier") and _readable("Purchase Invoice")):
		return _unavailable(_("Your role does not include suppliers and purchase invoices."), rows=[])
	suppliers = {
		s.name: s
		for s in frappe.get_list(
			"Supplier",
			filters={"disabled": 0},
			fields=["name", "supplier_name", "supplier_group"],
			limit_page_length=0,
		)
	}
	invoiced, owed, counts = defaultdict(list), defaultdict(list), defaultdict(int)
	for row in frappe.get_list(
		"Purchase Invoice",
		filters={"company": company, "docstatus": 1},
		fields=["supplier", "grand_total", "outstanding_amount"],
		limit_page_length=0,
	):
		invoiced[row.supplier].append(row.grand_total)
		owed[row.supplier].append(row.outstanding_amount)
		counts[row.supplier] += 1
	# Suppliers this Company has invoices from; a supplier with none would only add noise.
	return {
		"available": True,
		"reason": None,
		"rows": [
			{
				"supplier": name,
				"name": suppliers[name].supplier_name if name in suppliers else name,
				"group": suppliers[name].supplier_group if name in suppliers else None,
				"invoices": counts[name],
				"invoiced": total(invoiced[name]),
				"owed": total(owed[name]),
			}
			for name in sorted(counts, key=lambda n: -counts[n])
		],
	}


def _stock(company):
	if not (_readable("Bin") and _readable("Warehouse") and _readable("Item")):
		return _unavailable(_("Your role does not include stock."), rows=[])
	warehouses = frappe.get_list(
		"Warehouse", filters={"company": company, "is_group": 0}, pluck="name", limit_page_length=0
	)
	bins = (
		frappe.get_list(
			"Bin",
			filters={"warehouse": ["in", warehouses]},
			fields=["item_code", "warehouse", "actual_qty", "stock_value", "stock_uom"],
			limit_page_length=0,
		)
		if warehouses
		else []
	)
	names = {}
	if bins:
		names = {
			i.name: i.item_name
			for i in frappe.get_list(
				"Item",
				filters={"name": ["in", sorted({b.item_code for b in bins})]},
				fields=["name", "item_name"],
				limit_page_length=0,
			)
		}
	return {
		"available": True,
		"reason": None,
		"warehouses": len(warehouses),
		"rows": [
			{
				"item": b.item_code,
				"name": names.get(b.item_code, b.item_code),
				"warehouse": b.warehouse,
				"qty": float(b.actual_qty or 0),
				"uom": b.stock_uom,
				"value": total([b.stock_value]) if b.stock_value is not None else None,
			}
			for b in bins
		],
	}
