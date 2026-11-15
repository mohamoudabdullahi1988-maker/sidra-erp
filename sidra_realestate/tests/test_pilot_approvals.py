"""Approving the pilot's drafts and adding lead channels on the disposable CI site.

Run by `test_demo_datasets.TestDemo5Approvals`, after the pilot dataset and its top-up are loaded.
"""

from unittest.mock import patch

import frappe

from sidra_realestate.finance_demo import COMPANY, FLAGS
from sidra_realestate.pilot_approvals import (
	CHANNELS,
	GENERAL_MANAGER,
	KEEP_DRAFTS,
	approve_pilot_documents,
)
from sidra_realestate.tests.helpers import as_user


class PilotApprovalsChecks:
	def test_drafts_are_approved_through_the_rules_and_nothing_is_posted(self):
		with as_user("Administrator"), patch.dict(frappe.conf, {flag: 0 for flag in FLAGS}):
			with self.assertRaisesRegex(frappe.ValidationError, "staging-only flags"):
				approve_pilot_documents()
		with patch.dict(frappe.conf, {flag: 1 for flag in FLAGS}), as_user("sidra.manager@example.com"):
			with self.assertRaises(frappe.PermissionError):
				approve_pilot_documents()

		from sidra_realestate.demo import _ensure_users

		with as_user("Administrator"):
			_ensure_users()  # approvals are recorded as the demo users
		gl_before = frappe.db.count("GL Entry")
		with as_user("Administrator"), patch.dict(frappe.conf, {flag: 1 for flag in FLAGS}):
			data = approve_pilot_documents()
			self.assertTrue(data["created"])

			contracts = data["contracts"]
			self.assertTrue(contracts["approved"], contracts)
			self.assertLessEqual(len(contracts["kept_as_drafts"]), KEEP_DRAFTS)
			for name in contracts["approved"]:
				job = frappe.db.get_value("Sidra Construction Quotation", name, "job")
				values = frappe.db.get_value(
					"Sidra Construction Job",
					job,
					["contract_quotation", "contract_value", "contract_approved_by"],
					as_dict=True,
				)
				self.assertEqual(values.contract_quotation, name)
				self.assertGreater(values.contract_value, 0)
				self.assertEqual(values.contract_approved_by, GENERAL_MANAGER)  # never the preparer

			for name in data["variations"]["approved"]:
				self.assertEqual(
					frappe.db.get_value("Sidra Variation Order", name, "approved_by"), GENERAL_MANAGER
				)
			for name in data["inspections"]["issued"]:
				self.assertEqual(frappe.db.get_value("Sidra Inspection Report", name, "docstatus"), 1)
			for name in data["sale_quotations"]["issued"]:
				self.assertEqual(frappe.db.get_value("Sidra Sale Quotation", name, "status"), "Issued")
			for kind in ("variations", "inspections"):
				for name in data[kind]["kept_as_drafts"]:
					doctype = "Sidra Variation Order" if kind == "variations" else "Sidra Inspection Report"
					self.assertEqual(frappe.db.get_value(doctype, name, "docstatus"), 0)

			from sidra_realestate.services.crm_channels import channel_doctype, channel_field

			channels = set(frappe.get_all(channel_doctype(), pluck="name"))
			self.assertTrue(set(CHANNELS) <= channels)
			self.assertTrue(frappe.db.exists("Lead", {"company": COMPANY, channel_field(): "WhatsApp"}))

			again = approve_pilot_documents()
			self.assertFalse(again["created"])
		self.assertEqual(frappe.db.count("GL Entry"), gl_before)
