# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""The Berjaya form engine for setup records (G23, step 4): contract profiles and clauses, the
single Contract Settings record, and the contract import with Validate and Import."""

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.forms import StaleRecord, get_form, run_action, save_form
from sidra_realestate.install import ensure_contract_profiles
from sidra_realestate.sidra_sales.doctype.sidra_contract_settings.sidra_contract_settings import (
	ensure_contract_settings,
)
from sidra_realestate.tests.helpers import (
	BUYER,
	COMPANY,
	GENERAL_MANAGER,
	SALES_MANAGER,
	SALES_USER,
	as_user,
	ensure_base_records,
	make_scheme,
	make_unit,
	unique,
)

HEADER = "external_reference,customer,signed_on,agreed_price,unit,unit_price,down_payment_mode,down_payment,row_type,due_date,amount"
SETTINGS = "Sidra Contract Settings"


def keys(form):
	return [action["key"] for action in form["actions"]]


class TestFormsSetup(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()
		ensure_contract_profiles()
		ensure_contract_settings()
		make_scheme("_TEST-FORMS-SETUP")

	def test_profile_created_by_the_general_manager_with_its_note(self):
		with as_user(GENERAL_MANAGER):
			created = save_form(
				"Sidra Contract Profile",
				{
					"profile_name": unique("_Test Profile"),
					"installments": 12,
					"due_day": 5,
					"active": 1,
					"title_deadline_days": 20,
				},
			)
			form = get_form("Sidra Contract Profile", created["name"])
		self.assertIn("12 monthly installments; due day 5", form["notes"][0]["text"])
		with as_user(SALES_MANAGER), self.assertRaises(frappe.PermissionError):
			save_form(
				"Sidra Contract Profile",
				{"profile_name": unique("_Test P"), "installments": 12, "due_day": 5},
			)

	def test_clause_warns_until_both_languages_are_supplied(self):
		with as_user(GENERAL_MANAGER):
			created = save_form(
				"Sidra Contract Clause", {"clause_code": unique("_T-CL"), "title": "Test clause"}
			)
			form = get_form("Sidra Contract Clause", created["name"])
			self.assertEqual(form["notes"][0]["tone"], "warning")
			updated = save_form(
				"Sidra Contract Clause",
				{"text_so": "Qodob tijaabo ah.", "text_en": "A test clause."},
				name=created["name"],
				expected_modified=created["modified"],
			)
			self.assertEqual(get_form("Sidra Contract Clause", updated["name"])["notes"], [])

	def test_contract_settings_single_record(self):
		with as_user(SALES_USER):
			form = get_form(SETTINGS, SETTINGS)
			self.assertFalse(form["permissions"]["write"])
			self.assertFalse(form["permissions"]["delete"])
		with as_user(GENERAL_MANAGER):
			form = get_form(SETTINGS, SETTINGS)
			self.assertTrue(form["permissions"]["write"])
			saved = save_form(
				SETTINGS, {"schedule_tolerance": 7}, name=SETTINGS, expected_modified=form["modified"]
			)
			with self.assertRaises(StaleRecord):
				save_form(
					SETTINGS, {"schedule_tolerance": 8}, name=SETTINGS, expected_modified=form["modified"]
				)
		self.assertEqual(frappe.db.get_single_value(SETTINGS, "schedule_tolerance"), 7)
		with as_user(GENERAL_MANAGER):
			save_form(SETTINGS, {"schedule_tolerance": 5}, name=SETTINGS, expected_modified=saved["modified"])

	def test_import_validate_then_import(self):
		unit = make_unit(unique("_T-FIMP"), "_TEST-FORMS-SETUP").name
		ref = unique("EXT-FIMP")
		content = f"{HEADER}\n{ref},{BUYER},15/01/2026,9000,{unit},9000,,,Installment,10/04/2026,9000"
		with as_user(SALES_MANAGER):
			form = get_form("Sidra Contract Import")
			self.assertEqual(form["notes"][0]["link"]["label"], "Download template")
			# Uploaded unattached on the new form, as Berjaya does; Frappe attaches it on save.
			file_doc = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": f"{frappe.generate_hash(length=6)}-contracts.csv",
					"content": content,
					"is_private": 1,
				}
			).insert()
			attached = save_form(
				"Sidra Contract Import", {"company": COMPANY, "import_file": file_doc.file_url}
			)
			created = attached
		self.assertEqual(
			frappe.db.get_value(
				"File", file_doc.name, ["attached_to_doctype", "attached_to_name", "attached_to_field"]
			),
			("Sidra Contract Import", created["name"], "import_file"),
		)
		with as_user(SALES_MANAGER):
			self.assertEqual(keys(get_form("Sidra Contract Import", created["name"])), ["validate_import"])
			result = run_action(
				"Sidra Contract Import", created["name"], "validate_import", {}, attached["modified"]
			)
			self.assertEqual(result["message"], "Validated", result)
			self.assertFalse(result["failed"])
			form = get_form("Sidra Contract Import", created["name"])
			self.assertEqual(keys(form), ["validate_import", "run_import"])
			result = run_action("Sidra Contract Import", created["name"], "run_import", {}, form["modified"])
		self.assertTrue(frappe.db.exists("Sidra Sale Contract", {"external_reference": ref}), result)
		with as_user(SALES_USER), self.assertRaises(frappe.PermissionError):  # no access to imports
			get_form("Sidra Contract Import", created["name"])
