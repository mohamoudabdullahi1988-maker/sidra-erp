"""Native document history and assignments for the Berjaya record tools."""

import frappe
from frappe import _

from sidra_realestate.api.record_extras import _record


@frappe.whitelist(methods=["GET"])
def get_tools(doctype, name):
	doc = _record(doctype, name)
	permitted = set(frappe.get_meta(doctype).get_permitted_fieldnames(user=frappe.session.user))
	versions = []
	if doc.has_permission("write"):
		versions = frappe.get_all(
			"Version",
			filters={"ref_doctype": doctype, "docname": name},
			fields=["name", "owner", "creation", "data"],
			order_by="creation desc",
			limit_page_length=50,
		)
	return {
		"can_assign": bool(doc.has_permission("write")),
		"can_print": bool(doc.has_permission("print")),
		"assignments": frappe.get_all(
			"ToDo",
			filters={"reference_type": doctype, "reference_name": name, "status": "Open"},
			fields=["name", "allocated_to", "description", "date", "priority"],
		),
		"versions": [
			{
				"name": v.name,
				"by": v.owner,
				"on": v.creation,
				"changed": [
					change
					for change in frappe.parse_json(v.data).get("changed", [])
					if change and change[0] in permitted
				],
			}
			for v in versions
		],
	}


@frappe.whitelist(methods=["POST"])
def assign(doctype, name, user, description="", due_date=None):
	from frappe.desk.form.assign_to import add

	doc = _record(doctype, name, "write")
	if not frappe.db.exists("User", {"name": user, "enabled": 1, "user_type": "System User"}):
		frappe.throw(_("Choose an enabled staff user"))
	return add(
		{
			"doctype": doc.doctype,
			"name": doc.name,
			"assign_to": [user],
			"description": description or _("Review {0}").format(name),
			"date": due_date or None,
			"notify": 0,
		}
	)
