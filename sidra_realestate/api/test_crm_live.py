# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.crm_live import get_crm_live
from sidra_realestate.api.forms import get_form
from sidra_realestate.api.realestate_live import _leads
from sidra_realestate.patches.v0_4.add_crm_channels import CHANNELS, execute
from sidra_realestate.tests.helpers import COMPANY, OTHER_COMPANY, OUTSIDER, as_user, ensure_base_records


class TestCrmLive(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def test_native_channels_and_lead_queries(self):
		with as_user("Administrator"):
			execute()
			count = frappe.db.count("UTM Source")
			execute()
			self.assertEqual(count, frappe.db.count("UTM Source"))
			self.assertTrue(all(frappe.db.exists("UTM Source", c) for c in CHANNELS))
			before = get_crm_live(COMPANY)["leads"]["total"]
			for company in (COMPANY, OTHER_COMPANY):
				frappe.get_doc(
					{
						"doctype": "Lead",
						"first_name": "_Test Channel Buyer",
						"company": company,
						"utm_source": "WhatsApp",
					}
				).insert()
			result = get_crm_live(COMPANY)
			self.assertEqual(result["leads"]["total"], before + 1)
			self.assertGreaterEqual(result["leads"]["channel_counts"]["WhatsApp"], 1)
			self.assertGreaterEqual(_leads(COMPANY)["source_counts"]["WhatsApp"], 1)
			# Exact frontend Lead list fields, on the pinned ERPNext schema.
			rows = frappe.get_list(
				"Lead",
				fields=["name", "lead_name", "status", "utm_source", "mobile_no", "territory", "modified"],
			)
			self.assertTrue(rows)
			form = get_form("Lead")
			fields = {f["fieldname"] for s in form["layout"] for f in s["fields"]}
			self.assertIn("utm_source", fields)
			self.assertNotIn("source", fields)

	def test_denied_groups_and_outsider(self):
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_crm_live(COMPANY)
		with (
			as_user("Administrator"),
			patch("sidra_realestate.api.crm_live.frappe.has_permission", return_value=False),
		):
			result = get_crm_live(COMPANY)
			self.assertFalse(result["leads"]["available"])
			self.assertNotIn("total", result["leads"])
