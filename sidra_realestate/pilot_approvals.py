"""Approve the pilot's draft documents and give leads their channels (test site only, 15 Nov 2026).

Mohamoud, for the client demonstration: "approve all documents so that they can show data", keeping
two or three drafts of each kind for the approval steps shown live. On the pilot dataset (G16) and
its top-up, this loader once:

- issues each draft construction quotation, records the client's acceptance (fictional, with a
  placeholder scan) and has the General Manager approve it as the job's contract (CON-03, G11);
- has the General Manager approve the draft variation orders on those jobs (G11 second person);
- issues the draft inspection reports of the top-up;
- issues the draft sale quotations that are still valid and quotable, with any discount approved by
  the Sales Manager or General Manager first (G13); expired ones and ones whose plot has since been
  sold stay as they are;
- adds lead channels (ERPNext's UTM Sources, Lead Sources on older versions: WhatsApp, Email, Phone Call, Facebook, Instagram,
  Website) and spreads the top-up's leads across them.

Every step goes through the same controller rules as a user's click: nothing is forced, and a
document a rule refuses stays a draft and is reported. Approvals are recorded as the demo users
(`demo.gm`, `demo.manager`), never as the person who prepared the document. Nothing is posted,
invoiced or paid; no contract, title or unit is changed by hand.

The guards are the pilot's: Administrator only, the three staging flags, the top-up's manifest must
exist, one transaction with full rollback, a private manifest of its own, and a rerun that changes
nothing.

	bench --site <staging> execute sidra_realestate.pilot_approvals.approve_pilot_documents
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import getdate

from sidra_realestate.finance_demo import COMPANY
from sidra_realestate.pilot_demo import MANIFEST as PILOT_MANIFEST
from sidra_realestate.pilot_demo import _guard, _read_manifest
from sidra_realestate.pilot_extras import MANIFEST as EXTRAS_MANIFEST

MANIFEST = "sidra-pilot-approvals-v1.json"
SCHEMA = 1
KEEP_DRAFTS = 2  # of each kind, for the approval steps shown live
GENERAL_MANAGER = "demo.gm@example.com"
SALES_MANAGER = "demo.manager@example.com"
CHANNELS = ("WhatsApp", "Email", "Phone Call", "Facebook", "Instagram", "Website", "Walk In", "Reference")


def approve_pilot_documents():
	"""Approve once and commit; a rerun returns the manifest and changes nothing."""
	_guard()
	pilot = _read_manifest(PILOT_MANIFEST, None, required=False)
	if not pilot or not _read_manifest(EXTRAS_MANIFEST, None, required=False):
		frappe.throw(
			"Refusing: load the pilot dataset and its top-up first (pilot_extras.create_pilot_extras)."
		)
	missing = [user for user in (GENERAL_MANAGER, SALES_MANAGER) if not frappe.db.exists("User", user)]
	if missing:
		frappe.throw(
			"Refusing: approvals are recorded as the demo users, and these do not exist: "
			+ ", ".join(missing)
			+ ". Run sidra_realestate.demo.ensure_demo_users first. No data was changed."
		)
	existing = _read_manifest(MANIFEST, SCHEMA, required=False)
	if existing:
		return {**existing, "created": False}
	extras = _read_manifest(EXTRAS_MANIFEST, None, required=False)
	try:
		data = _approve(pilot, extras)
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
	finally:
		frappe.set_user("Administrator")
	frappe.db.commit()
	return {**data, "created": True}


def _approve(pilot, extras):
	today = datetime.now(ZoneInfo("Africa/Mogadishu")).date()
	result = {"schema": SCHEMA, "company": COMPANY, "as_of": str(today)}
	result["contracts"] = _construction_contracts(pilot.get("jobs", {}).get("quotations", []), today)
	result["variations"] = _variations(pilot.get("jobs", {}).get("variations", []), today)
	result["inspections"] = _inspections(extras.get("inspections", []))
	result["sale_quotations"] = _sale_quotations(pilot.get("sales", {}).get("quotations", []), today)
	result["channels"] = _channels(extras.get("leads", []))
	return result


def _drafts(doctype, names):
	"""This loader's own drafts, oldest first; the newest KEEP_DRAFTS stay drafts."""
	drafts = [n for n in names if frappe.db.get_value(doctype, n, "docstatus") == 0]
	return drafts[: max(len(drafts) - KEEP_DRAFTS, 0)], drafts[max(len(drafts) - KEEP_DRAFTS, 0) :]


def _attach(doc, fieldname, label):
	from sidra_realestate.demo import _placeholder_scan

	return (
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"{doc.name}-pilot-{label}.pdf",
				"content": _placeholder_scan(doc.name),
				"is_private": 1,
				"attached_to_doctype": doc.doctype,
				"attached_to_name": doc.name,
				"attached_to_field": fieldname,
			}
		)
		.insert(ignore_permissions=True)
		.file_url
	)


def _refused(name, exc):
	frappe.clear_messages()
	return {"name": name, "reason": str(exc).strip() or type(exc).__name__}


def _construction_contracts(names, today):
	from sidra_realestate.sidra_construction.doctype.sidra_construction_quotation.sidra_construction_quotation import (
		approve_contract,
	)

	approve, kept = _drafts("Sidra Construction Quotation", names)
	done, refused = [], []
	for name in approve:
		savepoint = f"contract_{frappe.scrub(name)}"
		frappe.db.savepoint(savepoint)
		try:
			frappe.set_user("Administrator")
			doc = frappe.get_doc("Sidra Construction Quotation", name)
			doc.submit()  # issued
			customer = frappe.db.get_value("Sidra Construction Job", doc.job, "customer")
			doc.client_accepted_by = customer
			doc.client_accepted_on = today
			doc.client_acceptance_document = _attach(doc, "client_acceptance_document", "acceptance")
			doc.save()
			frappe.set_user(GENERAL_MANAGER)
			approve_contract(name)
			done.append(name)
		except Exception as exc:
			frappe.db.rollback(save_point=savepoint)
			refused.append(_refused(name, exc))
	return {"approved": done, "kept_as_drafts": kept, "refused": refused}


def _variations(names, today):
	approve, kept = _drafts("Sidra Variation Order", names)
	done, refused = [], []
	for name in approve:
		savepoint = f"variation_{frappe.scrub(name)}"
		frappe.db.savepoint(savepoint)
		try:
			frappe.set_user("Administrator")
			doc = frappe.get_doc("Sidra Variation Order", name)
			doc.client_approved_by = frappe.db.get_value("Sidra Construction Job", doc.job, "customer")
			doc.client_approved_on = today
			doc.client_approval_document = _attach(doc, "client_approval_document", "client-approval")
			doc.save()
			frappe.set_user(GENERAL_MANAGER)  # a second person; the GM may approve any amount (G11)
			frappe.get_doc("Sidra Variation Order", name).submit()
			done.append(name)
		except Exception as exc:
			frappe.db.rollback(save_point=savepoint)
			refused.append(_refused(name, exc))
	return {"approved": done, "kept_as_drafts": kept, "refused": refused}


def _inspections(names):
	approve, kept = _drafts("Sidra Inspection Report", names)
	done, refused = [], []
	for name in approve:
		savepoint = f"inspection_{frappe.scrub(name)}"
		frappe.db.savepoint(savepoint)
		try:
			frappe.set_user("Administrator")
			frappe.get_doc("Sidra Inspection Report", name).submit()  # issued
			done.append(name)
		except Exception as exc:
			frappe.db.rollback(save_point=savepoint)
			refused.append(_refused(name, exc))
	return {"issued": done, "kept_as_drafts": kept, "refused": refused}


def _sale_quotations(names, today):
	from sidra_realestate.services.quotation import GENERAL_MANAGER as GM_LEVEL
	from sidra_realestate.services.quotation import NO_APPROVAL
	from sidra_realestate.sidra_sales.doctype.sidra_sale_quotation.sidra_sale_quotation import (
		approve_discount,
	)

	drafts = [n for n in names if frappe.db.get_value("Sidra Sale Quotation", n, "docstatus") == 0]
	# Expired quotations are left as they are: a past offer is not issued after its date.
	valid = [
		n for n in drafts if getdate(frappe.db.get_value("Sidra Sale Quotation", n, "valid_until")) >= today
	]
	expired = [n for n in drafts if n not in valid]
	approve, kept = valid[: max(len(valid) - KEEP_DRAFTS, 0)], valid[max(len(valid) - KEEP_DRAFTS, 0) :]
	done, refused = [], []
	for name in approve:
		savepoint = f"sale_{frappe.scrub(name)}"
		frappe.db.savepoint(savepoint)
		try:
			level = frappe.db.get_value("Sidra Sale Quotation", name, "discount_approval")
			if level and level != NO_APPROVAL:
				frappe.set_user(GENERAL_MANAGER if level == GM_LEVEL else SALES_MANAGER)
				approve_discount(name)
			frappe.set_user("Administrator")
			frappe.get_doc("Sidra Sale Quotation", name).submit()  # issued
			done.append(name)
		except Exception as exc:
			frappe.db.rollback(save_point=savepoint)
			refused.append(_refused(name, exc))
	return {"issued": done, "kept_as_drafts": kept, "expired_left_as_is": expired, "refused": refused}


def _channels(leads):
	"""The channels Sidra uses, and the top-up's leads spread across them (services.crm_channels)."""
	from sidra_realestate.services.crm_channels import channel_field, ensure_channel

	frappe.set_user("Administrator")
	field = channel_field("Lead")
	if not field:
		return {"channels_added": [], "leads": 0, "previous": {}, "note": "Lead has no channel field"}
	added = [channel for channel in CHANNELS if ensure_channel(channel)]
	previous = {}
	for index, name in enumerate(n for n in leads if frappe.db.exists("Lead", n)):
		previous[name] = frappe.db.get_value("Lead", name, field)
		frappe.db.set_value("Lead", name, field, CHANNELS[index % len(CHANNELS)], update_modified=False)
	return {"field": field, "channels_added": added, "leads": len(previous), "previous": previous}
