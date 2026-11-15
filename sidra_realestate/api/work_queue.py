"""The signed-in staff user's native assignments and notification inbox."""

import frappe
from frappe import _

from sidra_realestate.api.staff_dashboard import _staff_only


@frappe.whitelist(methods=["GET"])
def get_queue():
	_staff_only()
	user = frappe.session.user
	tasks = frappe.get_list(
		"ToDo",
		filters={"allocated_to": user, "status": "Open"},
		fields=["name", "description", "date", "priority", "reference_type", "reference_name"],
		order_by="date asc, creation desc",
		limit_page_length=100,
	)
	visible = []
	for task in tasks:
		if task.reference_type and task.reference_name:
			if not frappe.db.exists(task.reference_type, task.reference_name) or not frappe.has_permission(
				task.reference_type, "read", doc=task.reference_name
			):
				continue
		visible.append(task)
	notifications = frappe.get_list(
		"Notification Log",
		filters={"for_user": user},
		fields=["name", "subject", "read", "creation"],
		order_by="creation desc",
		limit_page_length=100,
	)
	return {"tasks": visible, "notifications": notifications}


@frappe.whitelist(methods=["POST"])
def complete_task(name):
	_staff_only()
	doc = frappe.get_doc("ToDo", name)
	if doc.allocated_to != frappe.session.user:
		frappe.throw(_("This task is not assigned to you"), frappe.PermissionError)
	doc.check_permission("write")
	doc.status = "Closed"
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def read_notification(name):
	_staff_only()
	doc = frappe.get_doc("Notification Log", name)
	if doc.for_user != frappe.session.user:
		frappe.throw(_("This notification is not yours"), frappe.PermissionError)
	doc.check_permission("read")
	doc.db_set("read", 1)
	return {"name": doc.name, "read": 1}
