# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""The Berjaya form engine for construction (G23, step 3): jobs and their records, Certify Stage,
Approve Contract, fields that change after submission, and the BOQ locked by its revision."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from sidra_realestate.api.forms import get_form, run_action, save_form, submit_form
from sidra_realestate.tests.helpers import (
	BUYER,
	COMPANY,
	GENERAL_MANAGER,
	PROJECT_MANAGER,
	as_user,
	ensure_base_records,
	issue_quotation,
	make_job,
	private_file,
)


def fields_of(form):
	return {field["fieldname"]: field for section in form["layout"] for field in section["fields"]}


def keys(form):
	return [action["key"] for action in form["actions"]]


class TestFormsConstruction(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def test_job_created_with_stages_and_offers_its_records(self):
		with as_user(PROJECT_MANAGER):
			created = save_form(
				"Sidra Construction Job",
				{
					"customer": BUYER,
					"company": COMPANY,
					"service_type": "Full Construction",
					"stages": [
						{"stage_name": "Foundation", "billing_pct": 40},
						{"stage_name": "Structure", "billing_pct": 60},
					],
				},
			)
			form = get_form("Sidra Construction Job", created["name"])
		self.assertEqual([row["stage_name"] for row in form["values"]["stages"]], ["Foundation", "Structure"])
		self.assertEqual(
			keys(form),
			[
				"new_sidra_construction_quotation",
				"new_sidra_boq_revision",
				"new_sidra_inspection_report",
				"new_sidra_project_risk",
			],
		)
		# A risk opens with the job and its Company filled in (G26).
		self.assertEqual(
			form["actions"][3]["navigate"],
			{"doctype": "Sidra Project Risk", "values": {"job": created["name"], "company": COMPANY}},
		)
		quotation = form["actions"][0]
		self.assertEqual(
			quotation["navigate"],
			{"doctype": "Sidra Construction Quotation", "values": {"job": created["name"]}},
		)
		with (
			as_user(PROJECT_MANAGER),
			self.assertRaises(frappe.ValidationError),
		):  # opens a form; nothing to run
			run_action("Sidra Construction Job", created["name"], quotation["key"], {}, created["modified"])

	def test_certify_a_completed_stage(self):
		job = make_job(
			status="In Progress",
			stages=[
				{
					"stage_name": "Foundation",
					"status": "Completed",
					"completion_pct": 100,
					"actual_start": add_days(today(), -20),
					"actual_end": add_days(today(), -1),
					"billing_pct": 20,
				},
				{"stage_name": "Structure"},
			],
		)
		with as_user(PROJECT_MANAGER):
			form = get_form("Sidra Construction Job", job.name)
		certify = next(action for action in form["actions"] if action["key"] == "certify_stage")
		options = certify["ask"][0]["options"]
		self.assertEqual(options, [{"value": job.stages[0].name, "label": "1. Foundation"}])
		self.assertEqual(certify["ask"][0]["default"], job.stages[0].name)
		with as_user(GENERAL_MANAGER):
			self.assertNotIn("certify_stage", keys(get_form("Sidra Construction Job", job.name)))
		with as_user(PROJECT_MANAGER):
			with self.assertRaises(frappe.ValidationError):  # values outside the action
				run_action(
					"Sidra Construction Job",
					job.name,
					"certify_stage",
					{"stage": options[0]["value"], "x": 1},
					form["modified"],
				)
			run_action(
				"Sidra Construction Job",
				job.name,
				"certify_stage",
				{"stage": options[0]["value"]},
				form["modified"],
			)
		self.assertTrue(frappe.db.get_value("Sidra Project Stage", job.stages[0].name, "certified"))

	def test_quotation_acceptance_after_submission_and_contract_approval(self):
		job = make_job(
			stages=[
				{"stage_name": "Foundation", "billing_pct": 40},
				{"stage_name": "Structure", "billing_pct": 60},
			]
		)
		with as_user(PROJECT_MANAGER):
			created = save_form(
				"Sidra Construction Quotation",
				{
					"job": job.name,
					"pricing_basis": "Fixed Fee",
					"fixed_fee": 20000,
					"scope": "Build a two-room house",
					"valid_until": add_days(today(), 30),
					"start_date": add_days(today(), 7),
					"duration_days": 120,
				},
			)
			issued = submit_form(
				"Sidra Construction Quotation", created["name"], expected_modified=created["modified"]
			)
			form = get_form("Sidra Construction Quotation", created["name"])
		self.assertTrue(form["permissions"]["write"])  # client acceptance may be recorded after issue
		editable = {name for name, field in fields_of(form).items() if field["editable"]}
		self.assertTrue(
			{"client_accepted_by", "client_accepted_on", "client_acceptance_document"} <= editable
		)
		self.assertNotIn("fixed_fee", editable)
		doc = frappe.get_doc("Sidra Construction Quotation", created["name"])
		url = private_file(name="signed-quotation.pdf", attached_to=doc, field="client_acceptance_document")
		with as_user(PROJECT_MANAGER):
			with self.assertRaises(frappe.ValidationError):  # a priced field cannot change after issue
				save_form(
					"Sidra Construction Quotation",
					{"fixed_fee": 1},
					name=doc.name,
					expected_modified=issued["modified"],
				)
			accepted = save_form(
				"Sidra Construction Quotation",
				{
					"client_accepted_by": BUYER,
					"client_accepted_on": today(),
					"client_acceptance_document": url,
				},
				name=doc.name,
				expected_modified=issued["modified"],
			)
			self.assertEqual(keys(get_form("Sidra Construction Quotation", doc.name)), [])  # not the GM
		with as_user(GENERAL_MANAGER):
			self.assertEqual(keys(get_form("Sidra Construction Quotation", doc.name)), ["approve_contract"])
			run_action("Sidra Construction Quotation", doc.name, "approve_contract", {}, accepted["modified"])
		self.assertEqual(
			frappe.db.get_value("Sidra Construction Job", job.name, "contract_quotation"), doc.name
		)
		with as_user(PROJECT_MANAGER):
			self.assertIn("new_sidra_variation_order", keys(get_form("Sidra Construction Job", job.name)))

	def test_boq_is_locked_by_an_approved_revision(self):
		job = make_job()
		with as_user(PROJECT_MANAGER):
			self.assertTrue(fields_of(get_form("Sidra Construction Job", job.name))["boq"]["editable"])
		quotation = issue_quotation(job)
		self.assertTrue(quotation.name)
		frappe.db.set_value("Sidra Construction Job", job.name, "boq_revision", "x", update_modified=False)
		with as_user(PROJECT_MANAGER):
			form = get_form("Sidra Construction Job", job.name)
			self.assertFalse(fields_of(form)["boq"]["editable"])
			with self.assertRaises(frappe.ValidationError):
				save_form(
					"Sidra Construction Job", {"boq": []}, name=job.name, expected_modified=form["modified"]
				)
