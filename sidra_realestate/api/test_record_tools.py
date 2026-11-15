import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.forms import get_form
from sidra_realestate.api.record_tools import assign, get_tools
from sidra_realestate.tests.helpers import OUTSIDER, PROJECT_MANAGER, as_user, ensure_base_records, make_job


class TestRecordTools(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def test_native_assignment_and_denial(self):
		job = make_job()
		with as_user("Administrator"):
			assign(job.doctype, job.name, PROJECT_MANAGER, "Review demo scope")
			tools = get_tools(job.doctype, job.name)
			self.assertTrue(any(a.allocated_to == PROJECT_MANAGER for a in tools["assignments"]))
			self.assertTrue(tools["can_print"])
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_tools(job.doctype, job.name)
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			assign(job.doctype, job.name, PROJECT_MANAGER)

	def test_contact_address_and_lead_forms(self):
		with as_user("Administrator"):
			for doctype in ("Contact", "Address"):
				self.assertTrue(get_form(doctype)["is_new"])
			form = get_form("Lead")
			fields = {f["fieldname"] for section in form["layout"] for f in section["fields"]}
			self.assertTrue({"company", "phone", "whatsapp_no", "unsubscribed"} <= fields)
