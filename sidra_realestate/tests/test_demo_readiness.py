"""Read-only readiness check for the client demonstration (walkthrough v0.2)."""

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.demo_readiness import check_demo_readiness
from sidra_realestate.tests.helpers import SALES_MANAGER, as_user, ensure_base_records

WATCHED = ("Sidra Scheme", "Sidra Unit", "Lead", "Opportunity", "Sidra Inspection Report", "User", "File")


class TestDemoReadiness(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def test_reports_every_item_with_a_fix_and_changes_nothing(self):
		before = {doctype: frappe.db.count(doctype) for doctype in WATCHED}
		with as_user("Administrator"):
			report = check_demo_readiness()
		self.assertEqual({doctype: frappe.db.count(doctype) for doctype in WATCHED}, before)
		checks = {row["check"] for row in report["results"]}
		for expected in (
			"Berjaya interface built",
			"Pilot dataset loaded",
			"Top-up loaded",
			"User demo.gm@example.com",
		):
			self.assertIn(expected, checks)
		for row in report["results"]:
			self.assertIn(row["status"], ("PASS", "WARN", "FAIL"))
			if row["status"] != "PASS":
				self.assertTrue(row["fix"], row["check"])
		self.assertEqual(sum(report["summary"].values()), len(report["results"]))

	def test_only_the_administrator_may_run_it(self):
		with as_user(SALES_MANAGER), self.assertRaises(frappe.PermissionError):
			check_demo_readiness()
