# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""The Berjaya interface at /berjaya (and /berjaya/<anything>, see `website_route_rules`).

A Vue app built from `frontend/` into `public/berjaya/`; the build also writes this page's
template, `berjaya.html` (neither is committed: `bench build --app sidra_realestate`). This
module is the only server code the interface has: it admits signed-in Sidra staff on their
existing Frappe session and hands the page what the server knows about that session — which
sections the user may open and which unit fields the user may read. The frontend shows what it
is told and decides no permission itself. Read-only, not cached, no secret embedded; every
record still comes through Frappe's own permission-checked REST API.

"Berjaya" is the software (`branding.BRAND_NAME`). The company shown is the user's own Company record.
"""

from urllib.parse import quote

import frappe
from frappe import _

from sidra_realestate import branding
from sidra_realestate.api.shell import is_staff

no_cache = 1

ROUTE = "/berjaya"

# Every list the interface can show, by key, with the DocType it reads. The frontend has the same
# keys (frontend/src/records.js); the server says which of them this user may read and create.
LISTS = {
	"units": "Sidra Unit",
	"schemes": "Sidra Scheme",
	"price_history": "Sidra Unit Price History",
	"customers": "Customer",
	"kyc": "Sidra Customer KYC",
	# CRM: ERPNext's own CRM records.
	"leads": "Lead",
	"opportunities": "Opportunity",
	"contacts": "Contact",
	"reservations": "Sidra Reservation",
	"sale_quotations": "Sidra Sale Quotation",
	"contracts": "Sidra Sale Contract",
	"title_transfers": "Sidra Title Transfer",
	"jobs": "Sidra Construction Job",
	"construction_quotations": "Sidra Construction Quotation",
	"boq_revisions": "Sidra BOQ Revision",
	"variations": "Sidra Variation Order",
	"inspections": "Sidra Inspection Report",
	"profiles": "Sidra Contract Profile",
	"clauses": "Sidra Contract Clause",
	"imports": "Sidra Contract Import",
	"contract_settings": "Sidra Contract Settings",
}

# (key, label, lists whose read permission opens the section). Dashboard is open to all staff; it
# shows only what each group of the dashboard method lets the user read. Collections reads the
# installment rows of sale contracts. Finance uses the same test as the old /sidra front page:
# read access to the ledger.
NAV = (
	("dashboard", "Dashboard", ()),
	("properties", "Properties", ("units", "schemes", "price_history")),
	# CRM (Mohamoud, 15 Nov 2026): ERPNext's Lead, Opportunity and Contact beside Customer and KYC.
	("customers", "CRM", ("leads", "opportunities", "customers", "contacts", "kyc")),
	("sales", "Sales", ("reservations", "sale_quotations")),
	("contracts", "Contracts", ("contracts", "title_transfers")),
	("collections", "Collections", ("contracts",)),
	(
		"construction",
		"Construction",
		("jobs", "construction_quotations", "boq_revisions", "variations", "inspections"),
	),
	("setup", "Setup", ("profiles", "clauses", "imports", "contract_settings")),
	("finance", "Finance", ("ledger",)),
)
LEDGER = "GL Entry"

# Unit fields the Properties list may ask for; the page receives the ones this user may read.
UNIT_LIST_FIELDS = ("unit_code", "scheme", "company", "unit_type", "status", "area_sqm", "cash_price")


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=" + quote(_return_path(), safe="")
		raise frappe.Redirect(302)  # temporary: depends on the session, so browsers must not remember it
	if not is_staff():
		frappe.throw(_("{0} is for Sidra staff").format(branding.BRAND_NAME), frappe.PermissionError)
	context.boot = {
		"csrf_token": frappe.sessions.get_csrf_token(),
		"berjaya_boot": get_boot(),
	}
	context.no_cache = 1
	return context


def _return_path() -> str:
	"""Where to come back to after signing in: the page asked for, if it is one of ours."""
	path = getattr(getattr(frappe.local, "request", None), "path", "") or ""
	return path if path == ROUTE or path.startswith(ROUTE + "/") else ROUTE


def _can_read(doctype) -> bool:
	return bool(frappe.db.exists("DocType", doctype)) and bool(frappe.has_permission(doctype, "read"))


def _can_create(doctype) -> bool:
	return bool(frappe.has_permission(doctype, "create"))


def get_boot() -> dict:
	"""What the signed-in user's session allows. Call only for Sidra staff."""
	user = frappe.session.user
	readable = {key: _can_read(doctype) for key, doctype in LISTS.items()}
	readable["ledger"] = _can_read(LEDGER)
	readable_unit_fields = []
	if _can_read("Sidra Unit"):
		permitted = set(frappe.get_meta("Sidra Unit").get_permitted_fieldnames(user=user))
		readable_unit_fields = [field for field in UNIT_LIST_FIELDS if field in permitted]
	currencies = {}
	if _can_read("Company"):
		currencies = {
			row.name: row.default_currency
			for row in frappe.get_list("Company", fields=["name", "default_currency"], limit_page_length=0)
			if row.default_currency
		}
	return {
		# The software's name and icon, from the one source (branding.py, decisions G17-G19).
		"product_name": branding.BRAND_NAME,
		"favicon": branding.ICON,
		# The client company's own logo (decision G19: Sidra is the company using Berjaya).
		"company_logo": branding.COMPANY_LOGO,
		"user": {"name": user, "full_name": frappe.utils.get_fullname(user)},
		"company": frappe.defaults.get_user_default("Company"),
		"nav": [
			{"key": key, "label": _(label)}
			for key, label, lists in NAV
			if not lists or any(readable.get(name) for name in lists)
		],
		# What the user may do with each list. Create opens Desk's own form, which checks again.
		"lists": {
			key: {"read": readable[key], "create": readable[key] and _can_create(doctype)}
			for key, doctype in LISTS.items()
		},
		"properties": {"readable_fields": readable_unit_fields},
		"currencies": currencies,
	}
