# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""The /berjaya page: existing session only, staff only, and a boot that follows permissions."""

import os
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.website.serve import get_response

from sidra_realestate import branding
from sidra_realestate.tests.helpers import (
	OUTSIDER,
	PROJECT_MANAGER,
	SALES_MANAGER,
	as_user,
	ensure_base_records,
)
from sidra_realestate.www import berjaya as page


def _nav_keys(user):
	with as_user(user):
		return [item["key"] for item in page.get_boot()["nav"]]


class TestBerjayaPage(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def test_guest_is_sent_to_login_with_a_return_to_berjaya(self):
		with as_user("Guest"), self.assertRaises(frappe.Redirect) as raised:
			page.get_context(frappe._dict())
		self.assertEqual(frappe.local.flags.redirect_location, "/login?redirect-to=%2Fberjaya")
		# Temporary (302): a permanent redirect would be remembered by the browser and send a
		# user who has since signed in back to the sign-in page.
		self.assertEqual(raised.exception.http_status_code, 302)

	def test_signed_in_outsider_is_refused(self):
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			page.get_context(frappe._dict())

	def test_navigation_follows_the_users_permissions(self):
		sales = _nav_keys(SALES_MANAGER)
		project = _nav_keys(PROJECT_MANAGER)
		for keys in (sales, project):
			self.assertIn("dashboard", keys)
		self.assertIn("properties", sales)
		self.assertIn("contracts", sales)
		self.assertNotIn("properties", project)
		self.assertNotIn("contracts", project)
		self.assertIn("construction", project)
		doctypes = {**page.LISTS, "ledger": page.LEDGER}
		for key, _label, lists in page.NAV:
			if lists:
				for user, keys in ((SALES_MANAGER, sales), (PROJECT_MANAGER, project)):
					with as_user(user):
						can = any(frappe.has_permission(doctypes[name], "read") for name in lists)
						self.assertEqual(key in keys, bool(can), (user, key))

	def test_list_permissions_come_from_the_server(self):
		with as_user(PROJECT_MANAGER):
			lists = page.get_boot()["lists"]
			self.assertEqual(set(lists), set(page.LISTS))
			for key, doctype in page.LISTS.items():
				self.assertEqual(lists[key]["read"], bool(frappe.has_permission(doctype, "read")), key)
				self.assertEqual(
					lists[key]["create"],
					bool(lists[key]["read"] and frappe.has_permission(doctype, "create")),
					key,
				)
		self.assertTrue(lists["jobs"]["read"])
		self.assertFalse(lists["kyc"]["read"], "KYC is for sales staff and the General Manager")

	def test_boot_lists_only_readable_unit_fields(self):
		with as_user(SALES_MANAGER):
			boot = page.get_boot()
		self.assertEqual(boot["user"]["name"], SALES_MANAGER)
		self.assertEqual(boot["product_name"], branding.BRAND_NAME)
		self.assertEqual(boot["company_logo"], branding.COMPANY_LOGO)
		self.assertTrue(set(boot["properties"]["readable_fields"]) <= set(page.UNIT_LIST_FIELDS))
		self.assertIn("unit_code", boot["properties"]["readable_fields"])
		with as_user(PROJECT_MANAGER):
			self.assertEqual(page.get_boot()["properties"]["readable_fields"], [])
		self.assertEqual(
			set(boot),
			{
				"product_name",
				"favicon",
				"company_logo",
				"user",
				"company",
				"nav",
				"lists",
				"properties",
				"currencies",
			},
		)

	def test_every_path_under_berjaya_reaches_the_page(self):
		rules = frappe.get_hooks("website_route_rules")
		self.assertIn({"from_route": "/berjaya/<path:app_path>", "to_route": "berjaya"}, rules)

	def test_built_page_renders_with_the_session_boot(self):
		template = os.path.join(frappe.get_app_path("sidra_realestate"), "www", "berjaya.html")
		if not os.path.exists(template):
			self.skipTest("frontend not built (bench build --app sidra_realestate)")
		with as_user(SALES_MANAGER):
			frappe.local.session.data.csrf_token = "test-csrf-token"
			response = get_response("berjaya")
		self.assertEqual(response.status_code, 200)
		html = response.get_data(as_text=True)
		self.assertIn('window["berjaya_boot"]', html)
		self.assertIn("/assets/sidra_realestate/berjaya/assets/", html)
		self.assertIn(SALES_MANAGER, html)

	def test_retired_demo_companies_are_hidden_without_deleting_records(self):
		rows = [
			frappe._dict(name=name, default_currency="USD")
			for name in ("Sidra Homes", "Sidra Demo Homes", "Sidra Finance Demo - Fictional")
		]
		original_get_list = frappe.get_list

		def company_rows(doctype, *args, **kwargs):
			return rows if doctype == "Company" else original_get_list(doctype, *args, **kwargs)

		with (
			as_user("Administrator"),
			patch.object(page.frappe, "get_list", side_effect=company_rows),
			patch.object(page.frappe.defaults, "get_user_default", return_value="Sidra Demo Homes"),
		):
			boot = page.get_boot()
		self.assertEqual(boot["currencies"], {"Sidra Homes": "USD"})
		self.assertEqual(boot["company"], "Sidra Homes")
