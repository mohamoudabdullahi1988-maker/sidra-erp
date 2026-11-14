# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Decision G24: Sidra staff use Berjaya; ERPNext Desk stays for administrators and finance.

A signed-in Sidra staff member who opens a Desk page (`/desk`, `/app`) is sent to the matching
Berjaya page, or to its front page, unless they hold a role that keeps Desk. Only page requests
are redirected: API calls, files, print views and the login page are untouched, so Berjaya and
every server method work exactly as before. The redirect is temporary (302) because it depends on
the session. Desk itself is not changed or removed.
"""

from urllib.parse import quote

import frappe
from werkzeug.exceptions import HTTPException
from werkzeug.utils import redirect

from sidra_realestate.api.shell import is_staff

# Roles that keep Desk: system administration, and finance for the ERPNext ledger and its reports.
DESK_ROLES = frozenset(
	{"System Manager", "Accounts Manager", "Accounts User", "Auditor", "Sidra Finance Reviewer"}
)
DESK_PREFIXES = ("/desk", "/app")
BERJAYA = "/berjaya"

# Desk list routes (DocType slugs) and their Berjaya paths, so a bookmarked Desk link still lands
# on the same record. Anything else goes to the Berjaya front page.
ROUTES = {
	"sidra-unit": "/properties",
	"sidra-scheme": "/properties/schemes",
	"sidra-unit-price-history": "/properties/price-history",
	"customer": "/customers",
	"sidra-customer-kyc": "/customers/kyc",
	"sidra-reservation": "/sales/reservations",
	"sidra-sale-quotation": "/sales/quotations",
	"sidra-sale-contract": "/contracts",
	"sidra-title-transfer": "/contracts/title-transfers",
	"sidra-construction-job": "/construction",
	"sidra-construction-quotation": "/construction/quotations",
	"sidra-boq-revision": "/construction/boq-revisions",
	"sidra-variation-order": "/construction/variations",
	"sidra-inspection-report": "/construction/inspections",
	"sidra-contract-profile": "/setup/profiles",
	"sidra-contract-clause": "/setup/clauses",
	"sidra-contract-import": "/setup/imports",
	"sidra-contract-settings": "/setup/contract-settings",
}


def keeps_desk(roles) -> bool:
	return bool(DESK_ROLES & set(roles))


def berjaya_path(path: str) -> str:
	"""The Berjaya page for a Desk path: `/desk/sidra-unit/U-1` -> `/berjaya/properties/U-1`."""
	parts = [part for part in path.split("/") if part]
	if len(parts) < 2 or parts[1] not in ROUTES:
		return BERJAYA
	target = BERJAYA + ROUTES[parts[1]]
	if parts[1] == "sidra-contract-settings":
		return target
	if len(parts) >= 3 and parts[2] not in ("new", "view") and not parts[2].startswith("new-"):
		target += "/" + quote(parts[2], safe="")
	return target


def before_request():
	"""Send Sidra staff from Desk pages to Berjaya (G24)."""
	request = getattr(frappe.local, "request", None)
	if not request or request.method != "GET":
		return
	path = request.path or ""
	if not any(path == prefix or path.startswith(prefix + "/") for prefix in DESK_PREFIXES):
		return
	if frappe.session.user in ("Guest", "Administrator"):
		return
	if keeps_desk(frappe.get_roles()) or not is_staff():
		return
	# Frappe returns an HTTPException's own response as the request's response (frappe/app.py).
	raise HTTPException(response=redirect(berjaya_path(path), 302))
