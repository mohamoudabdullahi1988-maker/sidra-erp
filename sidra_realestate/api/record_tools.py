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
		"can_share": bool(doc.has_permission("share") and doctype != "Sidra Customer KYC"),
		"can_tag": bool(doc.has_permission("write") and not doc.meta.issingle),
		"tags": [t for t in (doc.get("_user_tags") or "").split(",") if t],
		"shares": frappe.get_all(
			"DocShare",
			filters={"share_doctype": doctype, "share_name": name},
			fields=["user", "read", "write", "share", "everyone"],
		)
		if doc.has_permission("share")
		else [],
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


@frappe.whitelist(methods=["POST"])
def set_tag(doctype, name, tag, remove=0):
	from frappe.desk.doctype.tag.tag import DocTags

	doc = _record(doctype, name, "write")
	if doc.meta.issingle:
		frappe.throw(_("Tags are not supported on settings"))
	tag = str(tag or "").strip()
	if not tag or len(tag) > 140 or "," in tag:
		frappe.throw(_("Enter a tag of 1–140 characters without commas"))
	# Serialize read/modify/write of the native comma-separated tag field.
	frappe.db.get_value(doctype, name, "name", for_update=True)
	manager = DocTags(doctype)
	(manager.remove if frappe.utils.cint(remove) else manager.add)(name, tag)
	return {"tag": tag}


@frappe.whitelist(methods=["POST"])
def set_share(doctype, name, user, write=0, remove=0):
	import frappe.share

	_record(doctype, name, "share")
	if doctype == "Sidra Customer KYC":
		frappe.throw(_("Identity access requires General Manager approval for this buyer (G32)"), frappe.PermissionError)
	if not frappe.db.exists("User", {"name": user, "enabled": 1, "user_type": "System User"}):
		frappe.throw(_("Choose an enabled staff user"))
	frappe.share.validate_user_access(user, _("User"))
	if frappe.utils.cint(remove):
		frappe.share.remove(doctype, name, user)
	else:
		frappe.share.add(doctype, name, user=user, read=1, write=frappe.utils.cint(write), notify=0)
	return {"user": user}
