# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Live records for the Berjaya Finance overview, Subcontractors and Stock screens."""

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.finance_live import get_finance_live, get_operations_live
from sidra_realestate.tests.helpers import (
	COMPANY,
	OUTSIDER,
	PROJECT_MANAGER,
	as_user,
	ensure_base_records,
)


class TestFinanceLive(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def test_administrator_gets_every_group_as_exact_strings(self):
		gl_before = frappe.db.count("GL Entry")
		with as_user("Administrator"):
			data = get_finance_live(COMPANY)
			ops = get_operations_live(COMPANY)
		self.assertEqual(frappe.db.count("GL Entry"), gl_before)  # read only
		self.assertEqual(len(data["pnl"]["months"]), 12)
		for month in data["pnl"]["months"]:
			self.assertIsInstance(month["income"], str)
			self.assertIsInstance(month["expense"], str)
		self.assertEqual([b["age"] for b in data["receivables"]["buckets"]][0], "Not yet due")
		self.assertTrue(data["cash"]["available"])
		self.assertTrue(ops["suppliers"]["available"])
		self.assertTrue(ops["stock"]["available"])

	def test_unreadable_groups_are_unavailable_not_zero(self):
		with as_user(PROJECT_MANAGER):  # no ledger, invoices or suppliers
			data = get_finance_live(COMPANY)
		for group in ("pnl", "cash", "receivables", "payables"):
			self.assertFalse(data[group]["available"], group)
			self.assertTrue(data[group]["reason"], group)

	def test_outsiders_and_unknown_companies_are_refused(self):
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_finance_live(COMPANY)
		with as_user("Administrator"), self.assertRaises(frappe.ValidationError):
			get_operations_live("_Test No Such Company")
