# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Attachments and comments on records in Berjaya (G23, step 5)."""

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.record_extras import add_comment, get_extras, remove_attachment
from sidra_realestate.tests.helpers import (
	OUTSIDER,
	SALES_MANAGER,
	SALES_USER,
	as_user,
	ensure_base_records,
	ensure_customer,
	make_scheme,
	make_unit,
	private_file,
	unique,
)


class TestRecordExtras(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()
		make_scheme("_TEST-EXTRAS")

	def unit(self):
		return frappe.get_doc("Sidra Unit", make_unit(unique("_T-EX"), "_TEST-EXTRAS").name)

	def test_comments_are_plain_text_and_open_to_readers(self):
		unit = self.unit()
		with as_user(SALES_USER):  # reads units only, may still comment, as in Desk
			add_comment("Sidra Unit", unit.name, "Buyer asked about <b>drainage</b>")
			extras = get_extras("Sidra Unit", unit.name)
			with self.assertRaises(frappe.ValidationError):
				add_comment("Sidra Unit", unit.name, "   ")
		comment = next(row for row in extras["comments"] if row["type"] == "Comment")
		self.assertEqual(
			comment["text"], "Buyer asked about <b>drainage</b>"
		)  # escaped on save, shown as text
		self.assertFalse(extras["can_attach"])
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_extras("Sidra Unit", unit.name)
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			add_comment("Sidra Unit", unit.name, "x")

	def test_attachments_listed_and_removed_with_write_permission(self):
		unit = self.unit()
		loose = private_file(name="site-photo.pdf", attached_to=unit, field=None)
		kept = frappe.get_all(
			"File", filters={"file_url": loose, "attached_to_name": unit.name}, pluck="name"
		)[0]
		with as_user(SALES_MANAGER):
			extras = get_extras("Sidra Unit", unit.name)
		row = next(item for item in extras["attachments"] if item["name"] == kept)
		self.assertTrue(row["can_remove"] and row["is_private"])
		self.assertIsNone(row["field"])
		with as_user(SALES_USER), self.assertRaises(frappe.PermissionError):
			remove_attachment("Sidra Unit", unit.name, kept)
		with as_user(SALES_MANAGER):
			remove_attachment("Sidra Unit", unit.name, kept)
		self.assertFalse(frappe.db.exists("File", kept))

	def test_field_files_change_through_the_form(self):
		doc = frappe.get_doc(
			{
				"doctype": "Sidra Customer KYC",
				"customer": ensure_customer(unique("_Test Extras Buyer")),
				"id_type": "Passport",
				"id_number": unique("ID"),
				"phone": "+252630000000",
				"address": "Hargeisa",
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
		url = private_file(attached_to=doc, field="id_document")
		file = frappe.get_all("File", filters={"file_url": url}, pluck="name")[0]
		with as_user(SALES_MANAGER):
			extras = get_extras("Sidra Customer KYC", doc.name)
			self.assertEqual(extras["attachments"][0]["field"], "id_document")
			self.assertFalse(extras["attachments"][0]["can_remove"])
			with self.assertRaises(frappe.ValidationError):
				remove_attachment("Sidra Customer KYC", doc.name, file)

	def test_only_records_the_interface_serves(self):
		with as_user(SALES_MANAGER), self.assertRaises(frappe.PermissionError):
			get_extras("User", "Administrator")
