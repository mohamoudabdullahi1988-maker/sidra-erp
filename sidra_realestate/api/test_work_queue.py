import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.work_queue import complete_task, get_queue, read_notification
from sidra_realestate.tests.helpers import (
	OUTSIDER,
	PROJECT_MANAGER,
	SALES_MANAGER,
	as_user,
	ensure_base_records,
)


class TestWorkQueue(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def test_own_tasks_only_and_completion(self):
		with as_user("Administrator"):
			own = frappe.get_doc(
				{"doctype": "ToDo", "allocated_to": PROJECT_MANAGER, "description": "_Test review scope"}
			).insert()
			other = frappe.get_doc(
				{"doctype": "ToDo", "allocated_to": SALES_MANAGER, "description": "_Test private task"}
			).insert()
		with as_user(PROJECT_MANAGER):
			result = get_queue()
			self.assertIn(own.name, [t.name for t in result["tasks"]])
			self.assertNotIn(other.name, [t.name for t in result["tasks"]])
			self.assertEqual(complete_task(own.name)["status"], "Closed")
			with self.assertRaises(frappe.PermissionError):
				complete_task(other.name)
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_queue()

	def test_notifications_cannot_be_changed_for_another_user(self):
		with as_user("Administrator"):
			n = frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": "_Test task update",
					"for_user": SALES_MANAGER,
					"type": "Alert",
				}
			).insert(ignore_permissions=True)
		with as_user(PROJECT_MANAGER):
			self.assertNotIn(n.name, [r.name for r in get_queue()["notifications"]])
			with self.assertRaises(frappe.PermissionError):
				read_notification(n.name)
		with as_user(SALES_MANAGER):
			self.assertEqual(read_notification(n.name)["read"], 1)
