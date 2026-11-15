"""Where ERPNext keeps a lead's channel (WhatsApp, Email, Phone Call, ...).

ERPNext records it in a Link field on Lead and Opportunity: `utm_source` on current versions,
`source` on older ones. The DocType it links to also differs (UTM Source, or Lead Source, whose
controller module is missing on some ERPNext v16 sites). Everything in this app asks here instead
of naming either, so the CRM dashboard, the readiness check and the test-site loaders work on all.
"""

import frappe


def channel_field(doctype: str = "Lead") -> str | None:
	"""The field holding the channel on `doctype` (Lead or Opportunity), or None if it has none."""
	meta = frappe.get_meta(doctype)
	for fieldname in ("utm_source", "source"):
		field = meta.get_field(fieldname)
		if field and field.fieldtype == "Link" and frappe.db.has_column(doctype, fieldname):
			return fieldname
	return None


def channel_doctype(doctype: str = "Lead") -> str | None:
	"""The DocType the channel links to (UTM Source or Lead Source)."""
	fieldname = channel_field(doctype)
	return frappe.get_meta(doctype).get_field(fieldname).options if fieldname else None


def ensure_channel(name: str) -> bool:
	"""Create the channel record if it is missing; True when it was created.

	The record is written with Frappe's plain insert of a named row when the linked DocType's
	controller cannot be loaded (seen on ERPNext v16: "No module named
	'frappe.core.doctype.lead_source'"); a channel has no fields that need a controller.
	"""
	doctype = channel_doctype()
	if not doctype or frappe.db.exists(doctype, name):
		return False
	values = {"doctype": doctype}
	if frappe.get_meta(doctype).get_field("source_name"):
		values["source_name"] = name
	try:
		frappe.get_doc(values).insert(ignore_permissions=True, set_name=name)
	except ImportError:
		frappe.clear_messages()
		now = frappe.utils.now()
		row = {
			"name": name,
			"owner": "Administrator",
			"modified_by": "Administrator",
			"creation": now,
			"modified": now,
		}
		if "source_name" in values and frappe.db.has_column(doctype, "source_name"):
			row["source_name"] = name
		columns = ", ".join(f"`{c}`" for c in row)
		frappe.db.sql(
			f"insert into `tab{doctype}` ({columns}) values ({', '.join(['%s'] * len(row))})",  # noqa: S608
			tuple(row.values()),
		)
	return True
