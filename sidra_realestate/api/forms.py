# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Berjaya record forms: create, edit, submit, cancel, delete and actions without Desk (G23).

One engine serves every record type in `FORMS`. The server describes the form (fields, layout,
rules, what this user may change) from the DocType itself, and every write goes through the
record's own controller, so every rule that applies in Desk applies here. On top of that:

- **Only fields the form shows as editable can be written** (rules audit R7). A field is editable
  when it is a data field, not read-only, not hidden, at a permission level the user may write,
  the record is a draft (or the field may change after submission), and its
  `read_only_depends_on` rule does not make it read-only. Anything else in a request is refused,
  not ignored. A rule the parser does not understand makes the field read-only.
- **Stale edits are refused**: each change carries the `modified` value the user loaded.
- **Retries are safe**: a create carries a request key; submit, cancel and delete repeated after
  they succeeded change nothing.
- **Actions** (Reserve unit, Verify KYC, ...) are the existing whitelisted methods. The form lists
  only those whose conditions hold for this user and record, as Desk's buttons did; each method
  checks its own roles and state again when it runs.

Nothing here posts to the ledger (`CLAUDE.md` rule 3).
"""

import frappe
from frappe import _
from frappe.utils import cstr, get_fullname

from sidra_realestate.services import form_rules

# ---------------------------------------------------------------------- what the engine serves
DATA_TYPES = {
	"Data",
	"Small Text",
	"Text",
	"Long Text",
	"Text Editor",
	"Int",
	"Float",
	"Currency",
	"Percent",
	"Check",
	"Select",
	"Link",
	"Dynamic Link",
	"Date",
	"Datetime",
	"Time",
	"Attach",
	"Attach Image",
	"Phone",
	"Table",
	"Read Only",
	"Rating",
	"Duration",
	"Geolocation",
	"JSON",
}
# Shown but never written from Berjaya.
DISPLAY_ONLY_TYPES = {"Read Only", "Geolocation", "JSON", "Dynamic Link", "Text Editor"}
LAYOUT_TYPES = {"Section Break", "Column Break", "Tab Break"}
NEVER_WRITTEN = {"naming_series", "amended_from", "docstatus", "name", "owner", "creation", "modified"}

RESERVE_ROLES = ("Sidra Sales User", "Sidra Sales Manager")


def _unit_actions(doc):
	actions = []
	if set(RESERVE_ROLES) & set(frappe.get_roles()):
		if doc.status == "Available":
			actions.append(
				{
					"key": "reserve_unit",
					"label": _("Reserve unit"),
					"ask": [
						{
							"fieldname": "customer",
							"label": _("Customer"),
							"fieldtype": "Link",
							"options": "Customer",
							"reqd": 1,
						},
						{
							"fieldname": "days",
							"label": _("Days"),
							"fieldtype": "Int",
							"reqd": 1,
							"default": 7,
						},
					],
					# Rules audit R3: Desk warned before reserving a unit without a positive price.
					"confirm": None
					if (doc.cash_price or 0) > 0
					else _(
						"This unit has no positive asking price. Check its approved price history before reserving."
					),
				}
			)
		if doc.status == "Reserved" and doc.current_reservation:
			actions.append(
				{
					"key": "cancel_reservation",
					"label": _("Cancel reservation"),
					"confirm": _("Cancel reservation {0} and release the unit?").format(
						doc.current_reservation
					),
					"tone": "danger",
				}
			)
	return actions


def _reservation_actions(doc):
	if doc.status == "Active" and set(RESERVE_ROLES) & set(frappe.get_roles()):
		return [
			{
				"key": "cancel_reservation",
				"label": _("Cancel reservation"),
				"confirm": _("Cancel reservation {0} and release the unit?").format(doc.name),
				"tone": "danger",
			}
		]
	return []


def _kyc_actions(doc):
	if doc.status != "Verified" and doc.id_document and "Sidra Sales Manager" in frappe.get_roles():
		return [
			{
				"key": "verify_kyc",
				"label": _("Verify"),
				"confirm": _("Verify this KYC against the scanned ID?"),
			}
		]
	return []


def _run_reserve(doc, args):
	from sidra_realestate.services.reservations import reserve_unit

	result = reserve_unit(doc.name, args.get("customer"), args.get("days"))
	return {
		"message": _("Reserved as {0} until {1}").format(result["reservation"], result["expires_on"]),
		**result,
	}


def _run_cancel_reservation(doc, args):
	from sidra_realestate.services.reservations import cancel_reservation

	reservation = doc.name if doc.doctype == "Sidra Reservation" else doc.current_reservation
	cancel_reservation(reservation)
	return {"message": _("Reservation {0} cancelled").format(reservation)}


def _run_verify_kyc(doc, args):
	from sidra_realestate.sidra_sales.doctype.sidra_customer_kyc.sidra_customer_kyc import verify_kyc

	verify_kyc(doc.name)
	return {"message": _("KYC verified")}


def _quotation_actions(doc):
	"""Desk's Approve Discount button: SAL-05 / G13, never by the person who prepared it."""
	level = doc.get("discount_approval")
	if doc.docstatus != 0 or not level or level == "Not Needed" or doc.get("discount_approved_on"):
		return []
	roles = set(frappe.get_roles())
	may = "Sidra General Manager" in roles or (
		level == "Sidra Sales Manager" and "Sidra Sales Manager" in roles
	)
	if not may or frappe.session.user == doc.owner:
		return []
	return [
		{
			"key": "approve_discount",
			"label": _("Approve discount"),
			"confirm": _("Approve this quotation's discount?"),
		}
	]


def _title_transfer_actions(doc):
	"""Desk's Confirm Final Payment (second Sales Manager) and Confirm Handover (General Manager)."""
	roles = set(frappe.get_roles())
	actions = []
	if (
		not doc.final_payment_confirmed_on
		and doc.final_payment_date
		and doc.final_payment_evidence
		and "Sidra Sales Manager" in roles
		and frappe.session.user != doc.final_payment_entered_by
	):
		actions.append(
			{
				"key": "confirm_final_payment",
				"label": _("Confirm final payment"),
				"confirm": _("Confirm the final payment date and its evidence?"),
			}
		)
	if (
		doc.final_payment_confirmed_on
		and not doc.handover_confirmed_on
		and doc.handed_over_on
		and doc.handover_evidence
		and "Sidra General Manager" in roles
	):
		actions.append(
			{
				"key": "confirm_handover",
				"label": _("Confirm handover"),
				"confirm": _("Confirm the title deed was handed over?"),
			}
		)
	return actions


def _is_registered(doc):
	return doc.get("contract_type") == "Installment" and doc.get("source") == "External (registered)"


def _contract_actions(doc):
	"""Desk's Revise Draft, for a draft generated or cash contract the user may write."""
	if doc.docstatus == 0 and not _is_registered(doc) and doc.has_permission("write"):
		return [
			{
				"key": "revise_draft",
				"label": _("Revise draft"),
				"confirm": _(
					"Make a new draft with the profile's current terms and clause wording? This draft stays as it is. The signed copy is not copied."
				),
			}
		]
	return []


def _contract_submit(doc):
	"""A registered contract is confirmed on its registration screen (acknowledgement, G22)."""
	if _is_registered(doc):
		return _("Confirm a registered contract from its contract page")
	return None


def _run_approve_discount(doc, args):
	from sidra_realestate.sidra_sales.doctype.sidra_sale_quotation.sidra_sale_quotation import (
		approve_discount,
	)

	approve_discount(doc.name)
	return {"message": _("Discount approved")}


def _run_confirm_final_payment(doc, args):
	from sidra_realestate.sidra_sales.doctype.sidra_title_transfer.sidra_title_transfer import (
		confirm_final_payment,
	)

	confirm_final_payment(doc.name)
	return {"message": _("Final payment confirmed")}


def _run_confirm_handover(doc, args):
	from sidra_realestate.sidra_sales.doctype.sidra_title_transfer.sidra_title_transfer import (
		confirm_handover,
	)

	confirm_handover(doc.name)
	return {"message": _("Handover confirmed")}


def _run_revise_draft(doc, args):
	from sidra_realestate.sidra_sales.doctype.sidra_sale_contract.sidra_sale_contract import revise_draft

	name = revise_draft(doc.name)
	return {"message": _("New draft {0} made").format(name), "open": {"doctype": doc.doctype, "name": name}}


CONSTRUCTION_CLOSED = ("Closed", "Cancelled")


def _job_actions(doc):
	"""Desk's job buttons: create the job's quotation, BOQ revision, variation order, inspection
	report or risk (opens that form with the job filled in), and Certify Stage for a Project Manager."""
	if doc.get("status") in CONSTRUCTION_CLOSED:
		return []
	actions = []
	for doctype, label, wanted in (
		("Sidra Construction Quotation", _("New quotation"), not doc.contract_quotation),
		("Sidra BOQ Revision", _("New BOQ revision"), True),
		("Sidra Variation Order", _("New variation order"), bool(doc.contract_quotation)),
		("Sidra Inspection Report", _("New inspection report"), True),
		("Sidra Project Risk", _("New risk"), True),
	):
		if wanted and frappe.has_permission(doctype, "create"):
			values = {"job": doc.name}
			if doctype == "Sidra Project Risk":
				values["company"] = doc.company  # a risk names its Company; the job's is the one
			actions.append(
				{
					"key": "new_" + frappe.scrub(doctype),
					"label": label,
					"navigate": {"doctype": doctype, "values": values},
					"tone": "secondary",
				}
			)
	ready = [
		stage
		for stage in doc.get("stages") or []
		if not stage.certified
		and stage.status == "Completed"
		and float(stage.completion_pct or 0) == 100
		and stage.actual_end
	]
	if ready and "Sidra Project Manager" in frappe.get_roles():
		actions.append(
			{
				"key": "certify_stage",
				"label": _("Certify stage"),
				"confirm": _("Certification records completion only. It is not an invoice."),
				"ask": [
					{
						"fieldname": "stage",
						"label": _("Completed stage"),
						"fieldtype": "Select",
						"reqd": 1,
						"options": [
							{"value": row.name, "label": f"{row.idx}. {row.stage_name}"} for row in ready
						],
						"default": ready[0].name if len(ready) == 1 else "",
					}
				],
			}
		)
	return actions


def _job_locked(doc):
	"""The BOQ is controlled by an approved revision once there is one (Desk's read-only BOQ)."""
	return {"boq"} if doc.get("boq_revision") else set()


def _construction_quotation_actions(doc):
	if (
		doc.docstatus == 1
		and not doc.contract_approved_on
		and doc.client_accepted_on
		and doc.client_acceptance_document
		and "Sidra General Manager" in frappe.get_roles()
	):
		return [
			{
				"key": "approve_contract",
				"label": _("Approve contract"),
				"confirm": _(
					"Make this quotation the job's contract? This sets the job's contract value, dates and retention."
				),
			}
		]
	return []


def _run_certify_stage(doc, args):
	from sidra_realestate.sidra_construction.doctype.sidra_construction_job.sidra_construction_job import (
		certify_stage,
	)

	if not args.get("stage"):
		frappe.throw(_("Choose the completed stage to certify"))
	certify_stage(doc.name, args["stage"])
	return {"message": _("Stage certified")}


def _run_approve_contract(doc, args):
	from sidra_realestate.sidra_construction.doctype.sidra_construction_quotation.sidra_construction_quotation import (
		approve_contract,
	)

	approve_contract(doc.name)
	return {"message": _("Contract approved; the job's contract value is set")}


IMPORT_TEMPLATE = "/assets/sidra_realestate/templates/sidra_contract_import_template.csv"


def _profile_notes(doc):
	return [
		{
			"text": _(
				"{0} monthly installments; due day {1}. Agreed-price sales with no additional markup. Penalty, refund and title terms are recorded for the contract document, not calculated or posted by the system."
			).format(doc.installments or 0, doc.due_day or 0)
		}
	]


def _clause_notes(doc):
	if (doc.text_so or "").strip() and (doc.text_en or "").strip():
		return []
	return [
		{
			"text": _(
				"Wording is incomplete. Sidra must supply both Somali and English text before General Manager approval. Do not use this clause as approved wording."
			),
			"tone": "warning",
		}
	]


def _import_notes(doc):
	return [
		{
			"text": _(
				"Import dates use YYYY-MM-DD or DD/MM/YYYY, independently of your display settings. Imported records are registered installment contracts."
			),
			"link": {"label": _("Download template"), "url": IMPORT_TEMPLATE},
		}
	]


def _import_actions(doc):
	"""Desk's Validate (any time a file is attached) and Import (only after a successful Validate)."""
	if not doc.import_file or not doc.has_permission("write"):
		return []
	actions = [
		{
			"key": "validate_import",
			"label": _("Validate"),
			"confirm": _("Check every contract in the file? Nothing is kept."),
			"tone": "secondary",
		}
	]
	if doc.status == "Validated":
		actions.append(
			{
				"key": "run_import",
				"label": _("Import"),
				"confirm": _("Create the draft registered contracts from this file? All or nothing."),
			}
		)
	return actions


def _run_import_step(method):
	def run(doc, args):
		from sidra_realestate.sidra_sales.doctype.sidra_contract_import import sidra_contract_import

		result = getattr(sidra_contract_import, method)(doc.name) or {}
		return {
			"message": result.get("status") or _("Done"),
			"detail": result.get("log"),
			"failed": result.get("status") == "Failed",
		}

	return run


def _lead_actions(doc):
	actions = []
	if frappe.has_permission("Opportunity", "create"):
		actions.append(
			{
				"key": "create_opportunity",
				"label": _("Create opportunity"),
				"navigate": {
					"doctype": "Opportunity",
					"values": {"opportunity_from": "Lead", "party_name": doc.name},
				},
			}
		)
	if frappe.has_permission("Customer", "create"):
		actions.append(
			{
				"key": "make_customer",
				"label": _("Make customer"),
				"confirm": _("Create a customer from this lead?"),
			}
		)
	return actions


def _run_make_customer(doc, args):
	from erpnext.crm.doctype.lead.lead import make_customer

	doc = _locked("Lead", doc.name)
	doc.check_permission("read")
	frappe.has_permission("Customer", "create", throw=True)
	existing = frappe.db.get_value("Customer", {"lead_name": doc.name}, "name")
	if existing:
		customer = frappe.get_doc("Customer", existing)
		customer.check_permission("read")
	else:
		customer = make_customer(doc.name)
		customer.check_permission("create")
		customer.insert()
	return {"open": {"doctype": "Customer", "name": customer.name}}


RUNNERS = {
	"make_customer": _run_make_customer,
	"validate_import": _run_import_step("validate_import"),
	"run_import": _run_import_step("run_import"),
	"certify_stage": _run_certify_stage,
	"approve_contract": _run_approve_contract,
	"reserve_unit": _run_reserve,
	"cancel_reservation": _run_cancel_reservation,
	"verify_kyc": _run_verify_kyc,
	"approve_discount": _run_approve_discount,
	"confirm_final_payment": _run_confirm_final_payment,
	"confirm_handover": _run_confirm_handover,
	"revise_draft": _run_revise_draft,
}

# The record types Berjaya edits. `fields`: only these (for large ERPNext forms); `create_only`:
# fields the DocType marks read-only that its controller reads on insert; `create`/`edit`: False
# when the record changes only through actions.
FORMS = {
	"Contact": {"locked": lambda doc: {"links"}},
	"Address": {"locked": lambda doc: {"links"}},
	"Customer": {
		"fields": (
			"customer_name",
			"customer_type",
			"customer_group",
			"territory",
			"mobile_no",
			"email_id",
			"tax_id",
			"default_currency",
			"customer_details",
			"customer_primary_contact",
			"customer_primary_address",
			"disabled",
		),
		"create_only": ("mobile_no", "email_id"),
	},
	"Sidra Customer KYC": {"actions": _kyc_actions},
	# CRM uses ERPNext records and its native Lead-to-Customer mapping. Opportunity party
	# links are explicitly limited to the three supported CRM party types.
	"Lead": {
		"actions": _lead_actions,
		"fields": (
			"first_name",
			"last_name",
			"company",
			"phone",
			"whatsapp_no",
			"unsubscribed",
			"language",
			"company_name",
			"mobile_no",
			"email_id",
			"utm_source",  # the channel (ERPNext v15+); the form engine skips a field the DocType lacks
			"source",
			"status",
			"qualification_status",
			"territory",
			"city",
			"country",
			"lead_owner",
		),
	},
	"Opportunity": {
		"dynamic_links": {"party_name": ("Lead", "Customer", "Prospect")},
		"fields": (
			"opportunity_from",
			"party_name",
			"company",
			"currency",
			"status",
			"sales_stage",
			"opportunity_type",
			"utm_source",
			"source",
			"opportunity_amount",
			"probability",
			"expected_closing",
			"opportunity_owner",
		),
	},
	"Sidra Scheme": {},
	"Sidra Unit": {"actions": _unit_actions},
	"Sidra Reservation": {"create": False, "edit": False, "actions": _reservation_actions},
	"Sidra Unit Price History": {},
	"Sidra Sale Quotation": {
		"actions": _quotation_actions,
		# Desk's pickers (convenience only: the controller checks units and profiles itself).
		"link_filters": {
			"units.unit": {"status": ["in", ["Available", "Reserved"]]},
			"contract_profile": {"active": 1, "legal_hold": 0},
		},
	},
	"Sidra Sale Contract": {
		"actions": _contract_actions,
		"submit_refused": _contract_submit,
		"link_filters": {"contract_profile": {"active": 1}},
	},
	"Sidra Title Transfer": {
		"actions": _title_transfer_actions,
		"link_filters": {"contract": {"docstatus": 1}},
	},
	"Sidra Construction Job": {"actions": _job_actions, "locked": _job_locked},
	"Sidra Construction Quotation": {"actions": _construction_quotation_actions},
	"Sidra BOQ Revision": {},
	"Sidra Variation Order": {},
	"Sidra Inspection Report": {},
	"Sidra Project Risk": {},
	"Sidra Contract Profile": {"notes": _profile_notes},
	"Sidra Contract Clause": {"notes": _clause_notes},
	"Sidra Contract Settings": {},
	"Sidra Contract Import": {"notes": _import_notes, "actions": _import_actions},
}


# ---------------------------------------------------------------------- methods
@frappe.whitelist(methods=["GET"])
def get_form(doctype: str, name: str | None = None) -> dict:
	"""The form for one record (or a new one): layout, rules, values and what this user may do."""
	config = _config(doctype)
	if name:
		doc = frappe.get_doc(doctype, name)
		doc.check_permission("read")
	else:
		if not config.get("create", True):
			frappe.throw(_("{0} records are created through their actions, not this form").format(_(doctype)))
		frappe.has_permission(doctype, "create", throw=True)
		doc = frappe.new_doc(doctype)
	meta = frappe.get_meta(doctype)
	editable = _editable_fields(doc, config, rules=False)
	values = _readable_values(doc)
	return {
		"doctype": doctype,
		"name": doc.name if name else None,
		"title": _(doctype),
		"is_new": not name,
		"docstatus": doc.docstatus,
		"modified": cstr(doc.modified) if name else None,
		"values": values,
		"layout": _layout(meta, config, editable, doc),
		"permissions": _permissions(doc, config, is_new=not name),
		"notes": (config.get("notes") or (lambda d: []))(doc),
		"actions": [_public_action(action) for action in (config.get("actions") or (lambda d: []))(doc)]
		if name
		else [],
	}


@frappe.whitelist(methods=["POST"])
def save_form(
	doctype: str,
	data: dict | str,
	name: str | None = None,
	expected_modified: str | None = None,
	request_key: str | None = None,
	link_customer: str | None = None,
) -> dict:
	"""Create (no `name`) or update a record with the fields its form allows this user to change."""
	config = _config(doctype)
	values = frappe.parse_json(data) if isinstance(data, str) else data
	if not isinstance(values, dict):
		frappe.throw(_("Send the record's values as an object"))

	if not name:
		if not config.get("create", True):
			frappe.throw(_("{0} records are created through their actions, not this form").format(_(doctype)))
		earlier = _remembered(doctype, request_key)
		if earlier and frappe.db.exists(doctype, earlier):
			return _result(frappe.get_doc(doctype, earlier), repeated=True)
		frappe.has_permission(doctype, "create", throw=True)
		doc = frappe.new_doc(doctype)
		_apply(doc, values, config)
		doc.insert()
		if link_customer:
			from sidra_realestate.api.customer_connections import link_customer as connect

			connect(link_customer, doctype, doc.name)
		_remember(doctype, request_key, doc.name)
		return _result(doc)

	doc = _locked(doctype, name)
	if not config.get("edit", True):
		frappe.throw(_("{0} records change only through their actions").format(_(doctype)))
	doc.check_permission("write")
	check_not_stale(doc, expected_modified)
	_apply(doc, values, config)
	doc.save()
	return _result(doc)


@frappe.whitelist(methods=["POST"])
def submit_form(doctype: str, name: str, expected_modified: str | None = None) -> dict:
	config = _config(doctype)
	doc = _locked(doctype, name)
	doc.check_permission("read")
	if doc.docstatus == 1 and doc.modified_by == frappe.session.user:
		return _result(doc, repeated=True)
	if doc.docstatus != 0 or not frappe.get_meta(doctype).is_submittable or not config.get("edit", True):
		frappe.throw(_("{0} {1} cannot be submitted").format(_(doctype), name))
	refused = (config.get("submit_refused") or (lambda d: None))(doc)
	if refused:
		frappe.throw(refused)
	doc.check_permission("submit")
	check_not_stale(doc, expected_modified)
	doc.submit()
	return _result(doc)


@frappe.whitelist(methods=["POST"])
def cancel_form(doctype: str, name: str, expected_modified: str | None = None) -> dict:
	_config(doctype)
	doc = _locked(doctype, name)
	doc.check_permission("read")
	if doc.docstatus == 2 and doc.modified_by == frappe.session.user:
		return _result(doc, repeated=True)
	if doc.docstatus != 1:
		frappe.throw(_("Only a submitted {0} can be cancelled").format(_(doctype)))
	doc.check_permission("cancel")
	check_not_stale(doc, expected_modified)
	doc.cancel()
	return _result(doc)


@frappe.whitelist(methods=["POST"])
def delete_form(doctype: str, name: str, expected_modified: str | None = None) -> dict:
	config = _config(doctype)
	if not frappe.db.exists(doctype, name):
		return {"name": name, "deleted": True, "repeated": True}
	doc = _locked(doctype, name)
	if doc.docstatus == 1 or not config.get("edit", True):
		frappe.throw(_("{0} {1} cannot be deleted here").format(_(doctype), name))
	doc.check_permission("delete")
	check_not_stale(doc, expected_modified)
	frappe.delete_doc(doctype, name)
	return {"name": name, "deleted": True, "repeated": False}


@frappe.whitelist(methods=["POST"])
def run_action(
	doctype: str, name: str, action: str, args: dict | str | None = None, expected_modified: str | None = None
) -> dict:
	"""Run one of the record's actions, if the form currently offers it to this user."""
	config = _config(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	check_not_stale(doc, expected_modified)
	offered = {item["key"]: item for item in (config.get("actions") or (lambda d: []))(doc)}
	if action not in offered or action not in RUNNERS or offered[action].get("navigate"):
		frappe.throw(_("{0} is not available for {1} now. Reload it.").format(action, name))
	args = frappe.parse_json(args) if isinstance(args, str) else (args or {})
	if not isinstance(args, dict):
		frappe.throw(_("Send the action's values as an object"))
	allowed = {field["fieldname"] for field in offered[action].get("ask") or ()}
	unknown = sorted(set(args) - allowed)
	if unknown:
		frappe.throw(_("These values are not part of this action: {0}").format(", ".join(unknown)))
	return RUNNERS[action](doc, args) or {}


# ---------------------------------------------------------------------- form description
def _config(doctype):
	if doctype not in FORMS:
		frappe.throw(
			_("{0} cannot be edited in this interface yet").format(_(doctype)), frappe.PermissionError
		)
	return FORMS[doctype]


def _supported(field):
	return field.fieldtype in DATA_TYPES and field.fieldname not in NEVER_WRITTEN


def _selected(meta, config):
	"""The data fields of the form, in DocType order."""
	only = config.get("fields")
	if only:  # an explicit list shows its fields even where the DocType hides them
		return [field for field in meta.fields if _supported(field) and field.fieldname in only]
	return [field for field in meta.fields if _supported(field) and not field.hidden]


def _write_levels(doc):
	if doc.is_new():
		return {0} | set(frappe.get_meta(doc.doctype).get_permlevel_access("write") or [])
	return set(frappe.get_meta(doc.doctype).get_permlevel_access("write") or [])


def _rule_read_only(field, doc):
	rule = field.read_only_depends_on
	if not rule:
		return False
	tree = form_rules.parse(rule)
	if tree is None:
		return True  # not understood: the safe reading is read-only
	return form_rules.evaluate(tree, _rule_values(doc))


def _rule_values(doc):
	values = doc.as_dict()
	values["__islocal"] = 1 if doc.is_new() else 0
	return values


def _editable_fields(doc, config, rules=True):
	"""Fieldnames this user may change on this record (parent level). With `rules=False` the
	`read_only_depends_on` rules are left out: the form applies them live as values change, and
	`_apply` enforces them on the values as they will be saved."""
	meta = frappe.get_meta(doc.doctype)
	is_new = doc.is_new()
	if not is_new and (not config.get("edit", True) or not doc.has_permission("write")):
		return set()
	levels = _write_levels(doc)
	create_only = set(config.get("create_only") or ()) if is_new else set()
	locked = (config.get("locked") or (lambda d: set()))(doc)
	editable = set()
	for field in _selected(meta, config):
		if field.fieldname in create_only:
			editable.add(field.fieldname)
			continue
		dynamic = field.fieldtype == "Dynamic Link" and field.fieldname in config.get("dynamic_links", {})
		if (
			(field.fieldtype in DISPLAY_ONLY_TYPES and not dynamic)
			or field.read_only
			or (field.permlevel or 0) not in levels
		):
			continue
		if field.fieldname in locked:
			continue
		if doc.docstatus == 1 and not field.allow_on_submit:
			continue
		if doc.docstatus == 2:
			continue
		if rules and _rule_read_only(field, doc):
			continue
		editable.add(field.fieldname)
	return editable


def _child_editable(child_doctype):
	meta = frappe.get_meta(child_doctype)
	return [
		field
		for field in meta.fields
		if _supported(field)
		and not field.hidden
		and field.fieldtype not in DISPLAY_ONLY_TYPES
		and field.fieldtype != "Table"
		and not field.read_only
	]


def _field(field, editable, link_filters=None):
	options = field.options
	if field.fieldtype == "Select":
		options = [value for value in (field.options or "").split("\n")]
	return {
		"fieldname": field.fieldname,
		"label": _(field.label) if field.label else field.fieldname,
		"fieldtype": field.fieldtype,
		"options": options,
		"reqd": bool(field.reqd),
		"description": _(field.description) if field.description else None,
		"editable": editable,
		"bold": bool(field.bold),
		"link_filters": link_filters,
		"show": form_rules.parse(field.depends_on) if field.depends_on else None,
		"read_only_rule": form_rules.parse(field.read_only_depends_on)
		if field.read_only_depends_on
		else None,
		"mandatory_rule": form_rules.parse(field.mandatory_depends_on)
		if field.mandatory_depends_on
		else None,
		"unparsed": [
			key
			for key in ("depends_on", "read_only_depends_on", "mandatory_depends_on")
			if field.get(key) and form_rules.parse(field.get(key)) is None
		],
	}


def _layout(meta, config, editable, doc):
	"""Sections, each with its fields in order. Breaks follow the DocType's own layout."""
	only = set(config.get("fields") or ())
	sections, current = [], {"label": None, "show": None, "fields": []}
	for field in meta.fields:
		if field.fieldtype in ("Section Break", "Tab Break"):
			if current["fields"]:
				sections.append(current)
			current = {
				"label": _(field.label) if field.label else None,
				"show": form_rules.parse(field.depends_on) if field.depends_on else None,
				"fields": [],
			}
			continue
		if not _supported(field) or (only and field.fieldname not in only) or (not only and field.hidden):
			continue
		filters = config.get("link_filters") or {}
		entry = _field(field, field.fieldname in editable, filters.get(field.fieldname))
		if field.fieldtype == "Dynamic Link":
			entry["allowed_doctypes"] = list(config.get("dynamic_links", {}).get(field.fieldname, ()))
		for linked, allowed in config.get("dynamic_links", {}).items():
			if meta.get_field(linked).options == field.fieldname:
				entry["fieldtype"] = "Select"
				entry["options"] = list(allowed)
		if field.fieldtype == "Table":
			child_editable = {child.fieldname for child in _child_editable(field.options)}
			entry["columns"] = [
				_field(
					child,
					child.fieldname in child_editable and field.fieldname in editable,
					filters.get(f"{field.fieldname}.{child.fieldname}"),
				)
				for child in frappe.get_meta(field.options).fields
				if _supported(child) and not child.hidden and child.fieldtype != "Table"
			]
		current["fields"].append(entry)
	if current["fields"]:
		sections.append(current)
	return sections


def _readable_values(doc):
	"""The record's values this user may read (field-level read permissions applied)."""
	copy = frappe.get_doc(doc.as_dict()) if not doc.is_new() else doc
	if not doc.is_new():
		copy.apply_fieldlevel_read_permissions()
	values = copy.as_dict(no_default_fields=False, convert_dates_to_str=True)
	for key in ("__onload", "__last_sync_on", "_comments", "_assign", "_liked_by", "_user_tags", "_seen"):
		values.pop(key, None)
	return frappe.parse_json(frappe.as_json(values))


def _permissions(doc, config, is_new):
	from sidra_realestate.api.record_operations import capabilities

	meta = frappe.get_meta(doc.doctype)
	if is_new:
		return {"write": True, "submit": False, "cancel": False, "delete": False}
	editable_type = config.get("edit", True)
	return {
		**capabilities(doc),
		# A submitted record stays editable where its DocType lets fields change after submission
		# (e.g. a construction quotation's client acceptance).
		"write": bool(
			editable_type
			and doc.has_permission("write")
			and (
				doc.docstatus == 0
				or (doc.docstatus == 1 and any(field.allow_on_submit for field in _selected(meta, config)))
			)
		),
		"submit": bool(
			editable_type
			and meta.is_submittable
			and doc.docstatus == 0
			and doc.has_permission("submit")
			and not (config.get("submit_refused") or (lambda d: None))(doc)
		),
		"cancel": bool(meta.is_submittable and doc.docstatus == 1 and doc.has_permission("cancel")),
		"delete": bool(
			editable_type and not meta.issingle and doc.docstatus != 1 and doc.has_permission("delete")
		),
	}


def _public_action(action):
	return {
		"key": action["key"],
		"label": action["label"],
		"ask": action.get("ask") or [],
		"confirm": action.get("confirm"),
		"tone": action.get("tone") or "primary",
		"navigate": action.get("navigate"),
	}


# ---------------------------------------------------------------------- writing
def _apply(doc, values, config):
	"""Set the fields the form allows; refuse anything else (R7)."""
	meta = frappe.get_meta(doc.doctype)
	editable = _editable_fields(doc, config, rules=False)
	unknown = sorted(set(values) - editable)
	if unknown:
		frappe.throw(_("These fields cannot be changed on this form: {0}").format(", ".join(unknown)))
	original = {fieldname: doc.get(fieldname) for fieldname in values}
	for fieldname, value in values.items():
		field = meta.get_field(fieldname)
		if field.fieldtype == "Table":
			_apply_table(doc, field, value)
		else:
			doc.set(fieldname, value)
	for fieldname, allowed in config.get("dynamic_links", {}).items():
		field = meta.get_field(fieldname)
		target = doc.get(field.options)
		if target not in allowed:
			frappe.throw(_("This party type is not allowed"), frappe.PermissionError)
		if doc.get(fieldname):
			frappe.get_doc(target, doc.get(fieldname)).check_permission("read")
	# A field that is read-only by rule for the values as they will be saved keeps its value.
	for fieldname in values:
		field = meta.get_field(fieldname)
		if field.fieldtype == "Table" or not _rule_read_only(field, doc):
			continue
		if _comparable(doc.get(fieldname)) != _comparable(original[fieldname]):
			frappe.throw(_("{0} is read-only for these values").format(_(field.label)))
	if doc.doctype == "Customer" and {"customer_primary_contact", "customer_primary_address"} & set(values):
		from sidra_realestate.api.customer_connections import validate_primary_connections

		validate_primary_connections(doc)


def _comparable(value):
	"""Blank, None and zero-like values are one thing; numbers compare by value."""
	if value in (None, ""):
		return ""
	try:
		number = float(value)
	except TypeError, ValueError:
		return cstr(value)
	return "" if number == 0 else number


def _apply_table(doc, field, rows):
	if not isinstance(rows, list):
		frappe.throw(_("{0} must be a list of rows").format(_(field.label)))
	allowed = {child.fieldname for child in _child_editable(field.options)}
	existing = {row.name: row for row in doc.get(field.fieldname)}
	new_rows = []
	for number, row in enumerate(rows, start=1):
		if not isinstance(row, dict):
			frappe.throw(_("{0} row {1} must be an object").format(_(field.label), number))
		keep = row.get("name")
		extra = sorted(set(row) - allowed - {"name"})
		if extra:
			frappe.throw(
				_("{0} row {1}: these fields cannot be changed here: {2}").format(
					_(field.label), number, ", ".join(extra)
				)
			)
		if keep and keep in existing:
			target = existing[keep]  # keeps the row's read-only values (e.g. computed ones)
			for key in allowed & set(row):
				target.set(key, row[key])
			new_rows.append(target)
		else:
			new_rows.append({key: row[key] for key in allowed & set(row)})
	doc.set(field.fieldname, [])
	for row in new_rows:
		doc.append(field.fieldname, row)


def check_not_stale(doc, expected_modified):
	if not expected_modified:
		frappe.throw(_("Reload the record before changing it"), StaleRecord)
	if cstr(doc.modified) != cstr(expected_modified):
		frappe.throw(
			_("{0} was changed by {1} after you opened it. Reload it and make your change again.").format(
				doc.name, get_fullname(doc.modified_by)
			),
			StaleRecord,
		)


class StaleRecord(frappe.ValidationError):
	"""The record changed after the user loaded it."""


def _locked(doctype, name):
	if frappe.get_meta(doctype).issingle:
		# A single record (e.g. Contract Settings) has no row to lock; its version check still applies.
		return frappe.get_doc(doctype)
	if not frappe.db.get_value(doctype, name, "name", for_update=True):
		frappe.throw(_("{0} {1} not found").format(_(doctype), name), frappe.DoesNotExistError)
	return frappe.get_doc(doctype, name)


def _result(doc, repeated=False):
	return {
		"name": doc.name,
		"modified": cstr(doc.modified),
		"docstatus": doc.docstatus,
		"repeated": repeated,
	}


def _request_cache_key(doctype, request_key):
	return f"berjaya:form:create:{frappe.session.user}:{doctype}:{request_key}"


def _remembered(doctype, request_key):
	return frappe.cache.get_value(_request_cache_key(doctype, request_key)) if request_key else None


def _remember(doctype, request_key, name):
	if request_key:
		frappe.cache.set_value(_request_cache_key(doctype, request_key), name, expires_in_sec=24 * 60 * 60)
