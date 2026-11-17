"""Permission-checked native document operations for the staff interface."""

import frappe
from frappe import _
from frappe.utils import cstr

from sidra_realestate.api import forms
from sidra_realestate.api.record_extras import _record
from sidra_realestate.api.record_tools import assign

MAX_BULK = 50
RESET_FIELDS = {
	"status",
	"customer_primary_contact",
	"customer_primary_address",
	"actual_start",
	"actual_end",
	"completion_pct",
}
EVIDENCE_WORDS = (
	"approved",
	"accepted",
	"confirmed",
	"verified",
	"certified",
	"signed",
	"handover",
	"handed_over",
	"final_payment",
)


def _copyable(field):
	return not (
		field.no_copy
		or field.unique
		or field.fieldname in RESET_FIELDS
		or field.fieldtype in ("Attach", "Attach Image")
		or any(word in field.fieldname for word in EVIDENCE_WORDS)
	)


def capabilities(doc):
	meta = frappe.get_meta(doc.doctype)
	config = forms._config(doc.doctype)
	creatable = bool(
		not meta.issingle and config.get("create", True) and frappe.has_permission(doc.doctype, "create")
	)
	# Contracts have a dedicated, approved revision path that refreshes frozen terms.
	creatable = creatable and doc.doctype != "Sidra Sale Contract"
	return {
		# Frappe's legacy `allow_copy` flag is labelled "Hide Copy".
		"duplicate": bool(creatable and not meta.allow_copy),
		"amend": bool(
			creatable
			and meta.is_submittable
			and meta.has_field("amended_from")
			and doc.docstatus == 2
			and doc.has_permission("amend")
		),
		"rename": bool(meta.allow_rename and not meta.issingle and doc.has_permission("write")),
	}


def _source(doctype, name, operation):
	doc = _record(doctype, name)
	if operation not in ("duplicate", "amend", "rename") or not capabilities(doc).get(operation):
		frappe.throw(_("This operation is not permitted for this document"), frappe.PermissionError)
	return doc


@frappe.whitelist(methods=["GET"])
def prepare_copy(doctype, name, operation="duplicate"):
	"""Return an unsaved form, excluding approvals, evidence and no-copy/unique fields."""
	source = _source(doctype, name, operation)
	if operation not in ("duplicate", "amend"):
		frappe.throw(_("Choose duplicate or amend"))
	form = forms.get_form(doctype)
	meta = frappe.get_meta(doctype)
	values = forms._readable_values(source)
	for section in form["layout"]:
		for field in section["fields"]:
			key = field["fieldname"]
			df = meta.get_field(key)
			if not field["editable"] or not _copyable(df):
				continue
			if df.fieldtype == "Table":
				allowed = [f.fieldname for f in forms._child_editable(df.options) if _copyable(f)]
				form["values"][key] = [{k: row.get(k) for k in allowed} for row in values.get(key, [])]
			elif key in values:
				form["values"][key] = values[key]
	form["copy_source"] = {"name": name, "operation": operation, "modified": cstr(source.modified)}
	return form


@frappe.whitelist(methods=["POST"])
def save_copy(doctype, name, operation, data, expected_modified, request_key):
	_source(doctype, name, operation)
	if operation not in ("duplicate", "amend"):
		frappe.throw(_("Choose duplicate or amend"))
	forms.check_not_stale(forms._locked(doctype, name), expected_modified)
	cache_key = f"copy:{name}:{operation}:{request_key}"
	earlier = forms._remembered(doctype, cache_key)
	if earlier and frappe.db.exists(doctype, earlier):
		return forms._result(_record(doctype, earlier), repeated=True)
	values = frappe.parse_json(data) if isinstance(data, str) else data
	if not isinstance(values, dict):
		frappe.throw(_("Send values as an object"))
	if operation == "amend":
		forms._locked(doctype, name)
		if frappe.db.exists(doctype, {"amended_from": name, "docstatus": ["!=", 2]}):
			frappe.throw(_("This document already has an amendment"))
	doc = frappe.new_doc(doctype)
	forms._apply(doc, values, forms._config(doctype))
	if operation == "amend":
		doc.amended_from = name
	doc.insert()
	forms._remember(doctype, cache_key, doc.name)
	return forms._result(doc)


@frappe.whitelist(methods=["POST"])
def rename(doctype, name, new_name, expected_modified):
	doc = _source(doctype, name, "rename")
	forms.check_not_stale(forms._locked(doctype, name), expected_modified)
	new_name = cstr(new_name).strip()
	if not new_name or len(new_name) > 140:
		frappe.throw(_("Enter a name of 1–140 characters"))
	return {"name": frappe.rename_doc(doc.doctype, doc.name, new_name, merge=False)}


def _names(names):
	names = frappe.parse_json(names) if isinstance(names, str) else names
	if (
		not isinstance(names, list)
		or not 1 <= len(names) <= MAX_BULK
		or any(not isinstance(n, str) or not n for n in names)
	):
		frappe.throw(_("Select between 1 and 50 records"))
	return list(dict.fromkeys(names))


@frappe.whitelist(methods=["GET"])
def bulk_options(doctype, names):
	names = _names(names)
	loaded = [forms.get_form(doctype, name) for name in names]
	fields = None
	for form in loaded:
		editable = {
			f["fieldname"]: f
			for s in form["layout"]
			for f in s["fields"]
			if f["editable"] and f["fieldtype"] not in ("Table", "Attach", "Attach Image", "Dynamic Link")
		}
		fields = editable if fields is None else {k: v for k, v in fields.items() if k in editable}
	return {
		"records": [{"name": f["name"], "modified": f["modified"]} for f in loaded],
		"fields": list((fields or {}).values()),
		"can_assign": all(_record(doctype, n).has_permission("write") for n in names),
		"can_print": all(_record(doctype, n).has_permission("print") for n in names),
	}


@frappe.whitelist(methods=["POST"])
def bulk_action(doctype, records, operation, field=None, value=None, user=None):
	"""One transaction: any denied/stale/invalid record rolls back the entire batch."""
	forms._config(doctype)
	records = frappe.parse_json(records) if isinstance(records, str) else records
	if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
		frappe.throw(_("Send selected record versions"))
	names = _names([r.get("name") for r in records])
	if operation not in ("assign", "update", "print"):
		frappe.throw(_("Unknown bulk operation"))
	versions = {r["name"]: r.get("modified") for r in records}
	for name in sorted(names):
		doc = forms._locked(doctype, name)
		doc.check_permission("read")
		doc.check_permission("print" if operation == "print" else "write")
		forms.check_not_stale(doc, versions[name])
	if operation == "update":
		allowed = {f["fieldname"] for f in bulk_options(doctype, names)["fields"]}
		if field not in allowed:
			frappe.throw(_("This field is not editable on every selected record"))
	for name in names:
		if operation == "update":
			forms.save_form(doctype, {field: value}, name, versions[name])
		elif operation == "assign":
			assign(doctype, name, user)
	if operation == "print":
		return {
			"html": "<style>.batch-record { break-after: page; }</style>"
			+ "".join(
				'<section class="batch-record">' + frappe.get_print(doctype, name) + "</section>"
				for name in names
			)
		}
	return {"names": names, "operation": operation}
