# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""CRM in Berjaya: ERPNext's own Lead and Opportunity through the form engine (15 Nov 2026)."""

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.forms import get_form, save_form
from sidra_realestate.tests.helpers import (
	OUTSIDER,
	SALES_USER,
	as_user,
	ensure_base_records,
	unique,
)


class TestCrmForms(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def test_sales_user_creates_a_lead(self):
		first = unique("_Test Lead")
		with as_user(SALES_USER):
			get_form("Lead")  # the new-lead form opens for sales staff
			created = save_form("Lead", {"first_name": first, "mobile_no": "+252630000001"})
		lead = frappe.get_doc("Lead", created["name"])
		self.assertEqual(lead.first_name, first)
		self.assertEqual(lead.lead_name, first)

	def test_opportunity_is_not_created_in_berjaya(self):
		with as_user(SALES_USER), self.assertRaises(frappe.ValidationError):
			save_form("Opportunity", {"status": "Open"})

	def test_outsider_cannot_open_the_lead_form(self):
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_form("Lead")
