# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""CRM in Berjaya: ERPNext's own Lead and Opportunity through the form engine (15 Nov 2026)."""

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.forms import get_form, run_action, save_form
from sidra_realestate.tests.helpers import (
	COMPANY,
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
		# A new Opportunity defaults to ERPNext's Sales Stage "Prospecting", which its setup
		# wizard creates; the bare CI site has none (LinkValidationError otherwise).
		if not frappe.db.exists("Sales Stage", "Prospecting"):
			frappe.get_doc({"doctype": "Sales Stage", "stage_name": "Prospecting"}).insert(
				ignore_permissions=True
			)

	def test_sales_user_creates_a_lead(self):
		first = unique("_Test Lead")
		with as_user(SALES_USER):
			get_form("Lead")  # the new-lead form opens for sales staff
			created = save_form("Lead", {"first_name": first, "mobile_no": "+252630000001"})
		lead = frappe.get_doc("Lead", created["name"])
		self.assertEqual(lead.first_name, first)
		self.assertEqual(lead.lead_name, first)

	def test_lead_actions_create_opportunity_and_customer(self):
		with as_user(SALES_USER):
			lead = save_form("Lead", {"first_name": unique("_Test Conversion")})
			form = get_form("Lead", lead["name"])
			action = next(a for a in form["actions"] if a["key"] == "create_opportunity")
			opportunity = save_form(
				"Opportunity",
				{
					**action["navigate"]["values"],
					"company": COMPANY,
					"currency": "USD",
					"status": "Open",
					"opportunity_amount": 5500,
				},
			)
			values = get_form("Opportunity", opportunity["name"])["values"]
			self.assertEqual((values["opportunity_from"], values["party_name"]), ("Lead", lead["name"]))
			# Creating the opportunity updates the lead (ERPNext sets its status), so the page is
			# reloaded before the next action, as the lead page does after returning to it.
			form = get_form("Lead", lead["name"])
			converted = run_action("Lead", lead["name"], "make_customer", {}, form["modified"])
			customer = get_form("Customer", converted["open"]["name"])
			self.assertEqual(customer["values"]["lead_name"], lead["name"])
			self.assertEqual(customer["values"]["customer_name"], form["values"]["lead_name"])
			# A refreshed repeat opens the mapped customer instead of duplicating it.
			again = run_action(
				"Lead", lead["name"], "make_customer", {}, get_form("Lead", lead["name"])["modified"]
			)
			self.assertEqual(again["open"], converted["open"])

	def test_dynamic_link_refuses_unapproved_target_on_create_and_update(self):
		with as_user(SALES_USER):
			lead = save_form("Lead", {"first_name": unique("_Test Party")})
			values = {
				"opportunity_from": "Lead",
				"party_name": lead["name"],
				"company": COMPANY,
				"currency": "USD",
			}
			with self.assertRaises(frappe.PermissionError):
				save_form(
					"Opportunity", {**values, "opportunity_from": "User", "party_name": "Administrator"}
				)
			created = save_form("Opportunity", values)
			with self.assertRaises(frappe.PermissionError):
				save_form(
					"Opportunity",
					{"opportunity_from": "User"},
					name=created["name"],
					expected_modified=created["modified"],
				)
			form = get_form("Opportunity")
			fields = {f["fieldname"]: f for section in form["layout"] for f in section["fields"]}
			self.assertEqual(fields["party_name"]["allowed_doctypes"], ["Lead", "Customer", "Prospect"])
			self.assertTrue(fields["party_name"]["editable"])
			self.assertEqual(fields["opportunity_from"]["fieldtype"], "Select")

	def test_outsider_cannot_convert_or_create_opportunity(self):
		with as_user(SALES_USER):
			lead = save_form("Lead", {"first_name": unique("_Test Restricted")})
		with as_user(OUTSIDER):
			with self.assertRaises(frappe.PermissionError):
				run_action("Lead", lead["name"], "make_customer", {}, lead["modified"])
			with self.assertRaises(frappe.PermissionError):
				save_form(
					"Opportunity",
					{"opportunity_from": "Lead", "party_name": lead["name"], "company": COMPANY},
				)

	def test_outsider_cannot_open_the_lead_form(self):
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_form("Lead")
