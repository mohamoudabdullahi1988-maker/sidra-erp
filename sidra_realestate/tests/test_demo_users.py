# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Standalone demo-user command: guards, repeatability and the existing role profiles (#79)."""

from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.demo import USERS, ensure_demo_users
from sidra_realestate.install import ROLE_PROFILES, ensure_role_profiles
from sidra_realestate.tests.helpers import SALES_USER, as_user, ensure_base_records


class TestDemoUsers(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()
		ensure_role_profiles()

	def test_guard_refuses_non_administrator_before_writes(self):
		with patch.dict(frappe.conf, {"sidra_allow_demo_data": 1}), as_user(SALES_USER):
			with patch("sidra_realestate.demo._ensure_users") as create:
				with self.assertRaises(frappe.PermissionError):
					ensure_demo_users()
				create.assert_not_called()

	def test_guard_refuses_disabled_site_before_writes(self):
		for flag in (None, 0, "0"):
			with self.subTest(flag=flag), patch.dict(frappe.conf, {"sidra_allow_demo_data": flag}):
				with patch("sidra_realestate.demo._ensure_users") as create:
					with self.assertRaises(frappe.ValidationError):
						ensure_demo_users()
					create.assert_not_called()

	def test_command_is_repeatable_and_prints_interactive_password_commands(self):
		before = {
			dt: frappe.db.count(dt) for dt in ("GL Entry", "Customer", "Sidra Unit", "Sidra Sale Contract")
		}
		output = StringIO()
		with patch.dict(frappe.conf, {"sidra_allow_demo_data": 1}), redirect_stdout(output):
			first = ensure_demo_users()
			modified = {email: frappe.db.get_value("User", email, "modified") for email in USERS}
			second = ensure_demo_users()
		self.assertEqual(first, second)
		self.assertEqual(modified, {email: frappe.db.get_value("User", email, "modified") for email in USERS})
		self.assertEqual(before, {dt: frappe.db.count(dt) for dt in before})
		self.assertEqual(len(first["users"]), 5)
		for email, profile in first["users"].items():
			self.assertIn(f"set-password {email}", output.getvalue())
			self.assertTrue(set(ROLE_PROFILES[profile]) <= set(frappe.get_roles(email)))
		for email in ("demo.sales@example.com", "demo.manager@example.com", "demo.gm@example.com"):
			with as_user(email):
				for dt in ("Lead", "Opportunity", "Customer"):
					self.assertTrue(frappe.has_permission(dt, "read"), (email, dt))
		with as_user("demo.pm@example.com"):
			self.assertTrue(frappe.has_permission("Sidra Construction Job", "create"))
			self.assertTrue(frappe.has_permission("Sidra Inspection Report", "create"))
			self.assertFalse(frappe.has_permission("Sidra Inspection Report", "submit"))
		with as_user("demo.manager@example.com"):
			self.assertTrue(frappe.has_permission("Sidra Customer KYC", "write"))
			self.assertTrue(frappe.has_permission("Sidra Sale Contract", "submit"))
		with as_user("demo.gm@example.com"):
			self.assertTrue(frappe.has_permission("Sidra Construction Quotation", "read"))
			self.assertTrue(frappe.has_permission("Sidra Variation Order", "submit"))
