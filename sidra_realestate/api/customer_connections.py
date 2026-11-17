"""Native Contact/Address Dynamic Links; no parallel customer directory."""

import frappe
from frappe import _

from sidra_realestate.api.forms import _locked
from sidra_realestate.api.record_extras import _record

TYPES = {"Contact": "customer_primary_contact", "Address": "customer_primary_address"}


@frappe.whitelist(methods=["GET"])
def get_connections(doctype, name):
	doc = _record(doctype, name)
	if doctype == "Customer":
		rows = []
		for kind, primary in TYPES.items():
			links = frappe.get_all(
				"Dynamic Link",
				filters={
					"parenttype": kind,
					"parentfield": "links",
					"link_doctype": "Customer",
					"link_name": name,
				},
				fields=["parent"],
			)
			for link in links:
				if frappe.has_permission(kind, "read", doc=link.parent):
					rows.append(
						{"doctype": kind, "name": link.parent, "primary": doc.get(primary) == link.parent}
					)
	elif doctype in TYPES:
		rows = [
			{"doctype": "Customer", "name": r.link_name}
			for r in doc.get("links") or []
			if r.link_doctype == "Customer" and frappe.has_permission("Customer", "read", doc=r.link_name)
		]
	else:
		frappe.throw(_("Customer connections are not available for this record"))
	return {"rows": rows, "can_write": doc.has_permission("write"), "modified": str(doc.modified)}


@frappe.whitelist(methods=["POST"])
def link_customer(customer, doctype, name, operation="link", primary=0):
	if doctype not in TYPES or operation not in ("link", "unlink"):
		frappe.throw(_("Choose a Contact or Address and a supported operation"))
	# Both endpoints must be writable; a contact editor cannot attach it to an arbitrary buyer.
	buyer = _locked("Customer", customer)
	buyer.check_permission("read")
	buyer.check_permission("write")
	doc = _locked(doctype, name)
	doc.check_permission("read")
	doc.check_permission("write")
	existing = [r for r in doc.get("links") or [] if r.link_doctype == "Customer" and r.link_name == customer]
	if operation == "unlink":
		if buyer.get(TYPES[doctype]) == name:
			buyer.set(TYPES[doctype], None)
			buyer.save()
			# Customer hooks may update the linked Contact/Address. Reload under our row lock.
			doc.reload()
		for row in list(doc.get("links") or []):
			if row.link_doctype == "Customer" and row.link_name == customer:
				doc.remove(row)
	elif not existing:
		doc.append("links", {"link_doctype": "Customer", "link_name": customer})
	doc.save()
	if operation == "link" and frappe.utils.cint(primary):
		buyer.reload()
		buyer.set(TYPES[doctype], name)
		buyer.save()
	return {"name": name}


def validate_primary_connections(doc):
	"""Primary pickers must point at an existing native link to this customer."""
	for doctype, field in TYPES.items():
		name = doc.get(field)
		if not name:
			continue
		target = _record(doctype, name)
		if not any(
			r.link_doctype == "Customer" and r.link_name == doc.name for r in target.get("links") or []
		):
			frappe.throw(_("Link {0} to this customer before choosing it as primary").format(name))
