"""Run after the pilot loaders via TestDemo5Approvals; uses real approval controllers."""

from unittest.mock import patch

import frappe

from sidra_realestate.finance_demo import FLAGS
from sidra_realestate.pilot_approvals import approve_pilot_quotations
from sidra_realestate.pilot_demo import MANIFEST, _read_manifest
from sidra_realestate.tests.helpers import as_user


class PilotApprovalChecks:
	def test_guarded_approvals_rollback_and_repeat(self):
		with as_user("Administrator"), patch.dict(frappe.conf, {flag: 0 for flag in FLAGS}):
			with self.assertRaises(frappe.ValidationError):
				approve_pilot_quotations()
		with as_user("sidra.manager@example.com"), patch.dict(frappe.conf, {flag: 1 for flag in FLAGS}):
			with self.assertRaises(frappe.PermissionError):
				approve_pilot_quotations()
		with as_user("Administrator"), patch.dict(frappe.conf, {flag: 1 for flag in FLAGS}):
			pilot = _read_manifest(MANIFEST, None)
			gl = frappe.db.count("GL Entry")
			quotes = frappe.db.count("Sidra Construction Quotation")
			with patch(
				"sidra_realestate.pilot_approvals.approve_contract",
				side_effect=RuntimeError("approval failure"),
			):
				with self.assertRaisesRegex(RuntimeError, "approval failure"):
					approve_pilot_quotations()
			self.assertEqual(frappe.db.count("Sidra Construction Quotation"), quotes)
			data = approve_pilot_quotations()
			self.assertTrue(data["created"])
			self.assertEqual(len(data["quotations_approved"]), len(pilot["jobs"]["jobs"]))
			for name in pilot["jobs"]["jobs"]:
				job = frappe.get_doc("Sidra Construction Job", name)
				self.assertEqual(job.status, "Contracted")
				self.assertGreater(job.current_contract_value, 0)
				quote = frappe.get_doc("Sidra Construction Quotation", job.contract_quotation)
				self.assertEqual(quote.docstatus, 1)
				self.assertIn("FICTIONAL DEMO", quote.client_accepted_by)
				self.assertEqual(job.current_contract_value, quote.quoted_amount)
			self.assertFalse(approve_pilot_quotations()["created"])
			self.assertEqual(frappe.db.count("GL Entry"), gl)
			self.assertEqual(_read_manifest(MANIFEST, None), pilot)
