"""Fictional risks for the risk register (G26) on the disposable CI site.

Run by `test_demo_datasets.TestDemo4Risks`, after the pilot dataset and its top-up are loaded.
"""

from unittest.mock import patch

import frappe

from sidra_realestate.finance_demo import COMPANY, FLAGS
from sidra_realestate.pilot_risks import RISKS, create_pilot_risks
from sidra_realestate.tests.helpers import as_user


class PilotRisksChecks:
	def test_risks_are_added_once_and_post_nothing(self):
		with as_user("Administrator"), patch.dict(frappe.conf, {flag: 0 for flag in FLAGS}):
			with self.assertRaisesRegex(frappe.ValidationError, "staging-only flags"):
				create_pilot_risks()
		with patch.dict(frappe.conf, {flag: 1 for flag in FLAGS}), as_user("sidra.manager@example.com"):
			with self.assertRaises(frappe.PermissionError):
				create_pilot_risks()

		gl_before = frappe.db.count("GL Entry")
		with as_user("Administrator"), patch.dict(frappe.conf, {flag: 1 for flag in FLAGS}):
			data = create_pilot_risks()
			self.assertTrue(data["created"])
			self.assertEqual(len(data["risks"]), len(RISKS))
			self.assertEqual(frappe.db.count("Sidra Project Risk", {"company": COMPANY}), len(RISKS))
			self.assertTrue(
				frappe.db.exists("Sidra Project Risk", {"company": COMPANY, "scheme": ("is", "set")})
			)
			closed = frappe.get_all("Sidra Project Risk", filters={"status": "Closed"}, pluck="closed_on")
			self.assertTrue(closed and all(closed))

			again = create_pilot_risks()
			self.assertFalse(again["created"])
			self.assertEqual(frappe.db.count("Sidra Project Risk", {"company": COMPANY}), len(RISKS))
		self.assertEqual(frappe.db.count("GL Entry"), gl_before)
