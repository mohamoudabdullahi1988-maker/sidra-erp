# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Live records for the Berjaya CRM dashboard: leads by channel, opportunities, customers."""

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.crm_live import get_crm_live
from sidra_realestate.tests.helpers import (
	COMPANY,
	INSPECTOR,
	OUTSIDER,
	SALES_USER,
	as_user,
	ensure_base_records,
	unique,
)


class TestCrmLive(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()
		for channel in ("WhatsApp", "Email"):
			if not frappe.db.exists("Lead Source", channel):
				frappe.get_doc({"doctype": "Lead Source", "source_name": channel}).insert(
					ignore_permissions=True
				)
		cls.leads = [
			frappe.get_doc(
				{
					"doctype": "Lead",
					"first_name": unique("_Test CRM Lead"),
					"company": COMPANY,
					"source": source,
				}
			).insert(ignore_permissions=True)
			for source in ("WhatsApp", "WhatsApp", "Email", None)
		]

	def test_sales_staff_see_leads_by_channel(self):
		with as_user(SALES_USER):
			data = get_crm_live(COMPANY)
		leads = data["leads"]
		self.assertTrue(leads["available"])
		self.assertGreaterEqual(leads["by_channel"]["WhatsApp"], 2)
		self.assertGreaterEqual(leads["by_channel"]["Email"], 1)
		self.assertGreaterEqual(leads["by_channel"]["Not recorded"], 1)  # no channel is said, not guessed
		self.assertEqual(len(leads["months"]), 12)
		self.assertGreaterEqual(leads["months"][-1]["count"], 4)
		self.assertTrue(data["opportunities"]["available"])
		self.assertIsInstance(data["opportunities"]["open_amount"], str)

	def test_unreadable_groups_say_why(self):
		with as_user(INSPECTOR):  # construction only: no CRM records
			data = get_crm_live(COMPANY)
		self.assertFalse(data["leads"]["available"])
		self.assertTrue(data["leads"]["reason"])
		self.assertFalse(data["opportunities"]["available"])

	def test_outsiders_and_unknown_companies_are_refused(self):
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_crm_live(COMPANY)
		with as_user(SALES_USER), self.assertRaises(frappe.ValidationError):
			get_crm_live("_Test No Such Company")
