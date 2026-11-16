"""Native operations, permission boundaries and validation (synthetic records only)."""

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.customer_connections import get_connections, link_customer
from sidra_realestate.api.forms import StaleRecord, get_form, save_form
from sidra_realestate.api.record_operations import bulk_action, bulk_options, prepare_copy, rename, save_copy
from sidra_realestate.api.record_tools import get_tools, set_share, set_tag
from sidra_realestate.api.record_workflow import get_timeline
from sidra_realestate.tests.helpers import (
	BUYER,
	OTHER_BUYER,
	OUTSIDER,
	SALES_USER,
	as_user,
	ensure_base_records,
	make_job,
	unique,
)


class TestRecordOperations(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def lead(self):
		return save_form("Lead", {"first_name": unique("_Test Record Tools")})

	def test_amend_cancelled_inspection_preserves_lineage(self):
		with as_user("Administrator"):
			job = make_job(status="In Progress")
			doc = frappe.get_doc(
				{
					"doctype": "Sidra Inspection Report",
					"job": job.name,
					"inspector": "Administrator",
					"inspection_date": frappe.utils.today(),
					"result": "Pass",
					"checklist": [{"item": "Synthetic check", "result": "Pass"}],
				}
			).insert()
			doc.submit()
			with self.assertRaises(frappe.PermissionError):
				prepare_copy(doc.doctype, doc.name, "amend")
			doc.cancel()
			form = prepare_copy(doc.doctype, doc.name, "amend")
			values = {
				"job": job.name,
				"inspector": "Administrator",
				"inspection_date": frappe.utils.today(),
				"result": "Pass",
				"checklist": [{"item": "Synthetic check", "result": "Pass"}],
			}
			new = save_copy(
				doc.doctype, doc.name, "amend", values, form["copy_source"]["modified"], unique("amend")
			)
			amended = frappe.get_doc(doc.doctype, new["name"])
			self.assertEqual((amended.docstatus, amended.amended_from), (0, doc.name))
			with self.assertRaises(frappe.ValidationError):
				save_copy(
					doc.doctype, doc.name, "amend", values, form["copy_source"]["modified"], unique("amend")
				)

	def test_connections_preserve_other_customers_and_primary(self):
		with as_user("Administrator"):
			contact = save_form("Contact", {"first_name": unique("_Test Linked")}, link_customer=BUYER)
			name = contact["name"]
			link_customer(OTHER_BUYER, "Contact", name)
			link_customer(BUYER, "Contact", name, primary=1)
			link_customer(BUYER, "Contact", name, primary=1)
			self.assertEqual(len(get_connections("Contact", name)["rows"]), 2)
			self.assertEqual(frappe.db.get_value("Customer", BUYER, "customer_primary_contact"), name)
			link_customer(BUYER, "Contact", name, operation="unlink")
			self.assertFalse(frappe.db.get_value("Customer", BUYER, "customer_primary_contact"))
			self.assertEqual(
				get_connections("Contact", name)["rows"], [{"doctype": "Customer", "name": OTHER_BUYER}]
			)
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			link_customer(BUYER, "Contact", name)

	def test_unlinked_primary_is_rejected(self):
		with as_user("Administrator"):
			contact = save_form("Contact", {"first_name": unique("_Test Unlinked")})
			buyer = get_form("Customer", BUYER)
			with self.assertRaises(frappe.ValidationError):
				save_form("Customer", {"customer_primary_contact": contact["name"]}, BUYER, buyer["modified"])

	def test_duplicate_is_unsaved_and_retry_does_not_create_two(self):
		with as_user("Administrator"):
			lead = self.lead()
			before = frappe.db.count("Lead")
			form = prepare_copy("Lead", lead["name"])
			self.assertTrue(form["is_new"])
			self.assertEqual(frappe.db.count("Lead"), before)
			values = {"first_name": form["values"]["first_name"]}
			args = ("Lead", lead["name"], "duplicate", values, lead["modified"], unique("copy"))
			copy = save_copy(*args)
			self.assertNotEqual(copy["name"], lead["name"])
			self.assertEqual(save_copy(*args)["name"], copy["name"])
			with self.assertRaises(frappe.PermissionError):
				prepare_copy("Lead", lead["name"], "amend")
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			prepare_copy("Lead", lead["name"])

	def test_bulk_checks_stale_and_read_only_fields(self):
		with as_user("Administrator"):
			one, two = self.lead(), self.lead()
			options = bulk_options("Lead", [one["name"], two["name"]])
			self.assertIn("first_name", [f["fieldname"] for f in options["fields"]])
			with self.assertRaises(frappe.ValidationError):
				bulk_action("Lead", options["records"], "update", field="owner", value=OUTSIDER)
			stale = [{**r, "modified": "1900-01-01"} for r in options["records"]]
			with self.assertRaises(StaleRecord):
				bulk_action("Lead", stale, "update", field="first_name", value="_Test Changed")
			bulk_action("Lead", options["records"], "update", field="first_name", value="_Test Changed")
			for name in (one["name"], two["name"]):
				self.assertEqual(frappe.db.get_value("Lead", name, "first_name"), "_Test Changed")
			with self.assertRaises(frappe.ValidationError):
				bulk_options("Lead", ["x"] * 51)
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			bulk_options("Lead", [one["name"]])

	def test_bulk_assignment_and_print(self):
		with as_user("Administrator"):
			lead = self.lead()
			records = bulk_options("Lead", [lead["name"]])["records"]
			bulk_action("Lead", records, "assign", user=SALES_USER)
			self.assertTrue(
				any(a.allocated_to == SALES_USER for a in get_tools("Lead", lead["name"])["assignments"])
			)
			records = bulk_options("Lead", [lead["name"]])["records"]
			self.assertIn("html", bulk_action("Lead", records, "print"))

	def test_native_tags_shares_and_denials(self):
		with as_user("Administrator"):
			lead = self.lead()
			name = lead["name"]
			set_tag("Lead", name, "Review")
			set_tag("Lead", name, "Review")
			self.assertEqual(get_tools("Lead", name)["tags"].count("Review"), 1)
			set_tag("Lead", name, "Review", remove=1)
			self.assertNotIn("Review", get_tools("Lead", name)["tags"])
			set_share("Lead", name, SALES_USER)
			self.assertTrue(any(s.user == SALES_USER for s in get_tools("Lead", name)["shares"]))
			set_share("Lead", name, SALES_USER, remove=1)
			self.assertFalse(any(s.user == SALES_USER for s in get_tools("Lead", name)["shares"]))
		with as_user(OUTSIDER):
			with self.assertRaises(frappe.PermissionError):
				set_tag("Lead", name, "Forbidden")
			with self.assertRaises(frappe.PermissionError):
				set_share("Lead", name, SALES_USER)
			with self.assertRaises(frappe.PermissionError):
				get_timeline("Lead", name)

	def test_rename_requires_version_and_updates_native_links(self):
		with as_user("Administrator"):
			contact = save_form("Contact", {"first_name": unique("_Test Rename")}, link_customer=BUYER)
			name = contact["name"]
			link_customer(BUYER, "Contact", name, primary=1)
			form = get_form("Contact", name)
			self.assertTrue(form["permissions"]["rename"])
			with self.assertRaises(StaleRecord):
				rename("Contact", name, unique("_Test Renamed"), "old")
			new = rename("Contact", name, unique("_Test Renamed"), form["modified"])["name"]
			self.assertEqual(frappe.db.get_value("Customer", BUYER, "customer_primary_contact"), new)
			self.assertFalse(frappe.db.exists("Contact", name))
