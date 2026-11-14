# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Attachments and comments on a record in Berjaya (G23, step 5), as Desk's sidebar and timeline.

- `get_extras`: the record's attached files (those uploaded to one of its fields are marked, since
  they belong to that field) and its comments, newest first, as plain text.
- `add_comment`: a comment on a record the user may read (Desk lets readers comment too).
- `remove_attachment`: removes a file attached to the record, not to one of its fields (those
  change through the record's form); needs write permission on the record.
Uploading uses Frappe's own `upload_file`, which checks the record's permission itself.
Only the record types the form engine serves can be used.
"""

import html

import frappe
from frappe import _
from frappe.utils import cstr, strip_html_tags

from sidra_realestate.api.forms import FORMS

COMMENT_TYPES = ("Comment", "Info")
MAX_COMMENT = 5000


def _record(doctype, name, permission="read"):
	if doctype not in FORMS:
		frappe.throw(_("{0} is not available in this interface").format(_(doctype)), frappe.PermissionError)
	if frappe.get_meta(doctype).issingle:
		name = doctype
	doc = frappe.get_doc(doctype, name)
	doc.check_permission(permission)
	return doc


@frappe.whitelist(methods=["GET"])
def get_extras(doctype: str, name: str) -> dict:
	doc = _record(doctype, name)
	files = frappe.get_all(
		"File",
		filters={"attached_to_doctype": doctype, "attached_to_name": doc.name, "is_folder": 0},
		fields=[
			"name",
			"file_name",
			"file_url",
			"is_private",
			"owner",
			"creation",
			"attached_to_field",
			"file_size",
		],
		order_by="creation desc",
		ignore_permissions=True,  # the record's read permission above is the check, as in Desk
	)
	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": doctype,
			"reference_name": doc.name,
			"comment_type": ("in", COMMENT_TYPES),
		},
		fields=["name", "comment_type", "content", "owner", "comment_email", "creation"],
		order_by="creation desc",
		limit_page_length=200,
		ignore_permissions=True,
	)
	can_write = bool(doc.has_permission("write"))
	return {
		"attachments": [
			{
				"name": row.name,
				"file_name": row.file_name,
				"file_url": row.file_url,
				"is_private": bool(row.is_private),
				"field": row.attached_to_field or None,
				"by": frappe.utils.get_fullname(row.owner),
				"on": cstr(row.creation),
				"size": row.file_size,
				"can_remove": can_write and not row.attached_to_field and doc.docstatus != 2,
			}
			for row in files
		],
		"comments": [
			{
				"name": row.name,
				"type": row.comment_type,
				# Desk stores comments as HTML; Berjaya shows them as plain text (rendered as text).
				"text": html.unescape(strip_html_tags(row.content or "")).strip(),
				"by": frappe.utils.get_fullname(row.comment_email or row.owner),
				"on": cstr(row.creation),
			}
			for row in comments
		],
		"can_attach": can_write and doc.docstatus != 2,
		"can_comment": True,
	}


@frappe.whitelist(methods=["POST"])
def add_comment(doctype: str, name: str, text: str) -> dict:
	doc = _record(doctype, name)
	text = (text or "").strip()
	if not text:
		frappe.throw(_("Write the comment first"))
	if len(text) > MAX_COMMENT:
		frappe.throw(_("A comment can be at most {0} characters").format(MAX_COMMENT))
	comment = doc.add_comment("Comment", frappe.utils.escape_html(text), comment_email=frappe.session.user)
	return {"name": comment.name}


@frappe.whitelist(methods=["POST"])
def remove_attachment(doctype: str, name: str, file: str) -> dict:
	doc = _record(doctype, name, "write")
	row = frappe.db.get_value(
		"File", file, ["attached_to_doctype", "attached_to_name", "attached_to_field"], as_dict=True
	)
	if not row or (row.attached_to_doctype, row.attached_to_name) != (doctype, doc.name):
		frappe.throw(_("This file is not attached to {0}").format(doc.name))
	if row.attached_to_field:
		frappe.throw(
			_("This file belongs to the field {0}; change it through the form").format(row.attached_to_field)
		)
	if doc.docstatus == 2:
		frappe.throw(_("A cancelled record's files are kept"))
	frappe.delete_doc("File", file, ignore_permissions=True)  # write permission on the record checked above
	return {"removed": file}
