"""Paginated native record activity with field-level redaction of Version data."""

import frappe
from frappe.utils import cint

from sidra_realestate.api.conversations import _plain
from sidra_realestate.api.record_extras import _record


def _visible(meta, parenttype=None):
	permitted = set(meta.get_permitted_fieldnames(user=frappe.session.user, parenttype=parenttype))
	return {
		f.fieldname
		for f in meta.fields
		if f.fieldname in permitted and not f.hidden and f.fieldtype != "Password"
	}


def version_changes(doctype, data):
	meta = frappe.get_meta(doctype)
	visible = _visible(meta)
	result = [f"{f}: {old} → {new}" for f, old, new in data.get("changed", []) if f in visible]
	for action in ("added", "removed"):
		for field, row in data.get(action, []):
			if (
				field not in visible
				or not meta.get_field(field)
				or meta.get_field(field).fieldtype not in ("Table", "Table MultiSelect")
			):
				continue
			child_fields = _visible(frappe.get_meta(meta.get_field(field).options), doctype)
			values = ", ".join(f"{k}: {v}" for k, v in row.items() if k in child_fields)
			result.append(f"{field}: row {action} ({values})")
	for field, index, row_name, changes in data.get("row_changed", []):
		if (
			field not in visible
			or not meta.get_field(field)
			or meta.get_field(field).fieldtype not in ("Table", "Table MultiSelect")
		):
			continue
		child_fields = _visible(frappe.get_meta(meta.get_field(field).options), doctype)
		result.extend(
			f"{field}, row {cint(index) + 1}: {f}: {old} → {new}"
			for f, old, new in changes
			if f in child_fields
		)
	return result


@frappe.whitelist(methods=["GET"])
def timeline(doctype, name, start=0):
	doc = _record(doctype, name)
	start = max(0, cint(start))
	limit = start + 51
	events = [{"key": "created", "kind": "Created", "on": doc.creation, "by": doc.owner, "text": name}]
	for row in frappe.get_all(
		"Comment",
		filters={"reference_doctype": doctype, "reference_name": name},
		fields=["name", "creation", "owner", "comment_type", "content"],
		order_by="creation desc, name desc",
		limit_page_length=limit,
	):
		events.append(
			{
				"key": "comment:" + row.name,
				"kind": row.comment_type,
				"on": row.creation,
				"by": row.owner,
				"text": _plain(row.content),
			}
		)
	if doc.has_permission("write"):
		for row in frappe.get_all(
			"Version",
			filters={"ref_doctype": doctype, "docname": name},
			fields=["name", "creation", "owner", "data"],
			order_by="creation desc, name desc",
			limit_page_length=limit,
		):
			events.append(
				{
					"key": "version:" + row.name,
					"kind": "Changed",
					"on": row.creation,
					"by": row.owner,
					"text": "\n".join(version_changes(doctype, frappe.parse_json(row.data) or {}))
					or "No changes visible at your field permission level.",
				}
			)
	for row in frappe.get_list(
		"Communication",
		filters={"reference_doctype": doctype, "reference_name": name},
		fields=["name", "creation", "owner", "subject", "sent_or_received", "communication_medium"],
		order_by="creation desc, name desc",
		page_length=limit,
	):
		events.append(
			{
				"key": "communication:" + row.name,
				"kind": f"{row.communication_medium} {row.sent_or_received}",
				"on": row.creation,
				"by": row.owner,
				"text": row.subject,
			}
		)
	for row in frappe.get_all(
		"File",
		filters={"attached_to_doctype": doctype, "attached_to_name": name},
		fields=["name", "creation", "owner", "file_name"],
		order_by="creation desc, name desc",
		limit_page_length=limit,
	):
		if frappe.get_doc("File", row.name).has_permission("read"):
			events.append(
				{
					"key": "file:" + row.name,
					"kind": "Attachment",
					"on": row.creation,
					"by": row.owner,
					"text": row.file_name,
				}
			)
	events.sort(key=lambda row: (str(row["on"]), row["key"]), reverse=True)
	return {
		"rows": events[start : start + 50],
		"has_more": len(events) > start + 50,
		"versions_visible": bool(doc.has_permission("write")),
	}
