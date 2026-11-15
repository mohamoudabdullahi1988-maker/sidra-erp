# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Rehearsal journeys through Berjaya's endpoints (#79), with real role checks.

Only base inventory/users and synthetic uploaded PDFs are fixtures. Every business
transition uses the screen endpoint; no controller shortcut or ignored permission.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, today

from sidra_realestate.api import contract_registration as registration
from sidra_realestate.api.forms import get_form, run_action, save_form, submit_form
from sidra_realestate.api.workflow import get_contract_timeline
from sidra_realestate.install import ensure_contract_profiles
from sidra_realestate.tests.helpers import (
	BUYER,
	COMPANY,
	GENERAL_MANAGER,
	OTHER_PROJECT_MANAGER,
	PROJECT_MANAGER,
	SALES_MANAGER,
	SALES_USER,
	as_user,
	ensure_base_records,
	make_scheme,
	make_unit,
	private_file,
	signing_values,
	unique,
)

CONTRACT = "Sidra Sale Contract"
JOB = "Sidra Construction Job"
LEDGER = ("GL Entry", "Sales Invoice", "Payment Entry", "Journal Entry")


class TestDemoFlows(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()
		ensure_contract_profiles()
		cls.scheme = make_scheme("_TEST-DEMO-FLOWS")

	def setUp(self):
		super().setUp()
		# The generic helper has only Sidra Sales Manager. Match the EXISTING
		# Sidra Sales Management profile for this rehearsal, inside its transaction.
		manager = frappe.get_doc("User", SALES_MANAGER)
		if "Sales User" not in [r.role for r in manager.roles]:
			manager.add_roles("Sales User")
		self.ledger_before = {dt: frappe.db.count(dt) for dt in LEDGER}

	def tearDown(self):
		try:
			self.assertEqual({dt: frappe.db.count(dt) for dt in LEDGER}, self.ledger_before)
		finally:
			super().tearDown()

	def unit(self):
		return make_unit(unique("_T-DEMO-FLOW"), self.scheme, cash_price=11000).name

	def read(self, doctype, name):
		return get_form(doctype, name)["values"]

	def update(self, doctype, name, values):
		return save_form(doctype, values, name=name, expected_modified=get_form(doctype, name)["modified"])

	def submit(self, doctype, name):
		return submit_form(doctype, name, expected_modified=get_form(doctype, name)["modified"])

	def action(self, doctype, name, action, args=None):
		return run_action(doctype, name, action, args or {}, get_form(doctype, name)["modified"])

	def scan(self, doctype, name, field):
		# File upload fixture only; setting the attachment field uses the screen's save.
		return private_file(attached_to=frappe.get_doc(doctype, name), field=field)

	def test_a_capture_external_contract(self):
		unit = self.unit()
		with as_user(SALES_USER):
			registration.get_registration_form()
			created = registration.save_registration_draft(
				{
					"customer": BUYER,
					"company": COMPANY,
					"external_reference": unique("EXT-DEMO-FLOW"),
					"signed_on": today(),
					"agreed_price": 11000,
					"down_payment": 1000,
					"down_payment_mode": "Recorded separately",
					"installments": 20,
					"due_day": 5,
					"units": [{"unit": unit, "allocated_price": 11000}],
				}
			)
			name = created["name"]
			before = get_contract_timeline(name)
			self.assertNotEqual({s["state"] for s in before["stages"]}, {"completed"})
			self.assertEqual(self.read("Sidra Unit", unit)["status"], "Available")
			filled = registration.fill_registration_schedule(name, expected_modified=created["modified"])
			parties = registration.save_registration_draft(
				{"parties": [{"role": "Witness", "full_name": "_Test Rehearsal Witness"}]},
				contract=name,
				expected_modified=filled["modified"],
			)
			ready = registration.attach_registration_copy(
				name,
				self.scan(CONTRACT, name, "signed_copy"),
				expected_modified=parties["modified"],
			)
			with self.assertRaises(frappe.PermissionError):
				registration.confirm_registration(name, expected_modified=ready["modified"])
			self.assertEqual(self.read(CONTRACT, name)["docstatus"], 0)
		with as_user(SALES_MANAGER):
			registration.confirm_registration(name, expected_modified=ready["modified"])
			doc = self.read(CONTRACT, name)
			self.assertEqual(doc["docstatus"], 1)
			self.assertEqual(doc["terms_approved_by"], SALES_MANAGER)
			self.assertEqual(len(doc["schedule"]), 20)
			self.assertEqual(sum(row["amount"] for row in doc["schedule"]), 10000)
			self.assertEqual({s["state"] for s in get_contract_timeline(name)["stages"]}, {"completed"})
			self.assertEqual(self.read("Sidra Unit", unit)["status"], "Under Contract")

	def test_b_sell_plot(self):
		unit = self.unit()
		with as_user(SALES_USER):
			lead = save_form("Lead", {"first_name": unique("_Test Rehearsal Buyer")})
			customer = save_form(
				"Customer",
				{
					"customer_name": self.read("Lead", lead["name"])["first_name"],
					"customer_type": "Individual",
				},
			)["name"]
			kyc = save_form(
				"Sidra Customer KYC",
				{
					"customer": customer,
					"id_type": "National ID",
					"id_number": unique("TEST-ID"),
					"phone": "+252630000001",
					"address": "_Test Hargeisa address",
				},
			)["name"]
			self.update(
				"Sidra Customer KYC",
				kyc,
				{"id_document": self.scan("Sidra Customer KYC", kyc, "id_document")},
			)
			self.action("Sidra Unit", unit, "reserve_unit", {"customer": customer, "days": 7})
			self.assertEqual(self.read("Sidra Unit", unit)["status"], "Reserved")
			quotation = save_form(
				"Sidra Sale Quotation",
				{
					"customer": customer,
					"contract_profile": "Profile A",
					"units": [{"unit": unit, "cash_price": 10600, "installment_price": 11000}],
				},
			)["name"]
			with self.assertRaises(frappe.ValidationError):
				self.submit("Sidra Sale Quotation", quotation)
		with as_user(SALES_MANAGER):
			self.action("Sidra Sale Quotation", quotation, "approve_discount")
		with as_user(SALES_USER):
			self.submit("Sidra Sale Quotation", quotation)
			contract = save_form(
				CONTRACT,
				{
					"customer": customer,
					"company": COMPANY,
					"contract_type": "Installment",
					"contract_profile": "Profile A",
					"signed_on": today(),
					"agreed_price": 11000,
					"units": [{"unit": unit, "allocated_price": 11000}],
					**signing_values(),
				},
			)["name"]
			self.update(CONTRACT, contract, {"signed_copy": self.scan(CONTRACT, contract, "signed_copy")})
		with as_user(SALES_MANAGER):
			with self.assertRaisesRegex(frappe.ValidationError, "KYC"):
				self.submit(CONTRACT, contract)
			self.assertEqual(self.read(CONTRACT, contract)["docstatus"], 0)
			self.action("Sidra Customer KYC", kyc, "verify_kyc")
			self.submit(CONTRACT, contract)
			doc = self.read(CONTRACT, contract)
			self.assertEqual(doc["docstatus"], 1)
			self.assertEqual(len(doc["schedule"]), 14)  # unchanged Profile A, not a guessed 22-month override
			self.assertEqual(sum(row["amount"] for row in doc["schedule"]), 11000)
			self.assertEqual(self.read("Sidra Unit", unit)["status"], "Under Contract")
			self.assertFalse(get_contract_timeline(contract)["supported"])

	def test_c_start_construction(self):
		with as_user(PROJECT_MANAGER):
			job = save_form(
				JOB,
				{
					"customer": BUYER,
					"company": COMPANY,
					"service_type": "Full Construction",
					"stages": [
						{"stage_name": "Foundation", "billing_pct": 40},
						{"stage_name": "Structure", "billing_pct": 50},
					],
				},
			)["name"]
			new = next(
				a for a in get_form(JOB, job)["actions"] if a["key"] == "new_sidra_construction_quotation"
			)
			quotation = save_form(
				new["navigate"]["doctype"],
				{
					**new["navigate"]["values"],
					"pricing_basis": "Fixed Fee",
					"fixed_fee": 20000,
					"scope": "_Test two-room building",
					"valid_until": add_days(today(), 30),
					"start_date": today(),
					"duration_days": 120,
					"retention_pct": 5,
					"retention_period_months": 12,
				},
			)["name"]
			self.submit("Sidra Construction Quotation", quotation)
			self.update(
				"Sidra Construction Quotation",
				quotation,
				{
					"client_accepted_by": BUYER,
					"client_accepted_on": today(),
					"client_acceptance_document": self.scan(
						"Sidra Construction Quotation", quotation, "client_acceptance_document"
					),
				},
			)
		with as_user(GENERAL_MANAGER):
			with self.assertRaisesRegex(frappe.ValidationError, "100"):
				self.action("Sidra Construction Quotation", quotation, "approve_contract")
			self.assertFalse(self.read(JOB, job)["contract_quotation"])
		with as_user(PROJECT_MANAGER):
			self.update(
				JOB,
				job,
				{
					"stages": [
						{"stage_name": "Foundation", "billing_pct": 40},
						{"stage_name": "Structure", "billing_pct": 60},
					]
				},
			)
		with as_user(GENERAL_MANAGER):
			self.action("Sidra Construction Quotation", quotation, "approve_contract")
		with as_user(PROJECT_MANAGER):
			inspection = save_form(
				"Sidra Inspection Report",
				{
					"job": job,
					"stage": "Foundation",
					"inspection_date": today(),
					"inspector": PROJECT_MANAGER,
					"result": "Pass",
					"checklist": [{"item": "_Test dimensions checked", "result": "Pass"}],
				},
			)["name"]
			self.assertEqual(self.read("Sidra Inspection Report", inspection)["docstatus"], 0)
			# A PM records inspections; only an Inspector may submit one. No role widening.
			self.assertFalse(get_form("Sidra Inspection Report", inspection)["permissions"]["submit"])
		for amount, approver in ((1000, OTHER_PROJECT_MANAGER), (1500, GENERAL_MANAGER)):
			with as_user(PROJECT_MANAGER):
				variation = save_form(
					"Sidra Variation Order",
					{"job": job, "amount": amount, "description": "_Test additional works"},
				)["name"]
				self.update(
					"Sidra Variation Order",
					variation,
					{
						"client_approved_by": BUYER,
						"client_approved_on": today(),
						"client_approval_document": self.scan(
							"Sidra Variation Order", variation, "client_approval_document"
						),
					},
				)
				with self.assertRaises(frappe.PermissionError):
					self.submit("Sidra Variation Order", variation)
			with as_user(approver):
				self.submit("Sidra Variation Order", variation)
		with as_user(PROJECT_MANAGER):
			doc = self.read(JOB, job)
			stages = [
				{"name": r["name"], "stage_name": r["stage_name"], "billing_pct": r["billing_pct"]}
				for r in doc["stages"]
			]
			stages[0].update(status="Completed", completion_pct=100, actual_start=today(), actual_end=today())
			self.update(JOB, job, {"stages": stages})
			self.action(JOB, job, "certify_stage", {"stage": stages[0]["name"]})
			doc = self.read(JOB, job)
			self.assertTrue(doc["stages"][0]["certified"])
			self.assertEqual(
				(doc["contract_value"], doc["approved_variations"], doc["current_contract_value"]),
				(20000, 2500, 22500),
			)
			self.assertEqual((doc["retention_pct"], doc["retention_period_months"]), (5, 12))
			self.assertEqual(getdate(doc["contract_start_date"]), getdate(today()))
			self.assertEqual(getdate(doc["contract_end_date"]), getdate(add_days(today(), 119)))
			self.assertEqual(sum(r["billing_amount"] for r in doc["stages"]), 22500)
