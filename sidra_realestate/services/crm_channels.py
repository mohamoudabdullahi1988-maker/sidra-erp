"""Where ERPNext keeps a lead's channel (WhatsApp, Email, Phone Call, ...).

ERPNext v15+ records it in `utm_source`, a link to Frappe's UTM Source; older versions used `source`,
a link to Lead Source. Everything in this app asks here instead of naming either, so the CRM
dashboard, the readiness check and the test-site loaders work on both.
"""

import frappe


def channel_field(doctype: str = "Lead") -> str | None:
	"""The field holding the channel on `doctype` (Lead or Opportunity), or None if it has none."""
	meta = frappe.get_meta(doctype)
	for fieldname in ("utm_source", "source"):
		field = meta.get_field(fieldname)
		if field and field.fieldtype == "Link":
			return fieldname
	return None


def channel_doctype(doctype: str = "Lead") -> str | None:
	"""The DocType the channel links to (UTM Source or Lead Source)."""
	fieldname = channel_field(doctype)
	return frappe.get_meta(doctype).get_field(fieldname).options if fieldname else None


def ensure_channel(name: str) -> bool:
	"""Create the channel record if it is missing; True when it was created."""
	doctype = channel_doctype()
	if not doctype or frappe.db.exists(doctype, name):
		return False
	values = {"doctype": doctype}
	if doctype == "Lead Source":
		values["source_name"] = name
	frappe.get_doc(values).insert(ignore_permissions=True, set_name=name)
	return True
