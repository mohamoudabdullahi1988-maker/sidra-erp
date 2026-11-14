# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Decision G24: Sidra staff opening Desk go to Berjaya; administrators and finance keep Desk."""

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from werkzeug.exceptions import HTTPException

from sidra_realestate import cutover
from sidra_realestate.tests.helpers import (
	GENERAL_MANAGER,
	OUTSIDER,
	PROJECT_MANAGER,
	SALES_MANAGER,
	SALES_USER,
	SYSTEM_ONLY,
	as_user,
	ensure_base_records,
	ensure_user,
)

FINANCE = "sidra.finance@example.com"


class TestCutover(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()
		ensure_user(FINANCE, ["Sidra Finance Reviewer"])

	def visit(self, path, user, method="GET"):
		"""The redirect location for `path`, or None when the request goes through."""
		request = SimpleNamespace(path=path, method=method)
		with as_user(user), patch.object(frappe.local, "request", request, create=True):
			try:
				cutover.before_request()
			except HTTPException as e:
				response = e.get_response()
				self.assertEqual(response.status_code, 302)
				return response.headers["Location"]
		return None

	def test_staff_are_sent_to_berjaya(self):
		for user in (SALES_USER, SALES_MANAGER, PROJECT_MANAGER, GENERAL_MANAGER):
			with self.subTest(user=user):
				self.assertEqual(self.visit("/desk", user), "/berjaya")
				self.assertEqual(self.visit("/app/sidra-unit", user), "/berjaya/properties")

	def test_records_land_on_the_same_record(self):
		self.assertEqual(self.visit("/desk/sidra-unit/U 1", SALES_USER), "/berjaya/properties/U%201")
		self.assertEqual(
			self.visit("/desk/sidra-sale-contract/SSC-2026-00001", SALES_USER),
			"/berjaya/contracts/SSC-2026-00001",
		)
		self.assertEqual(
			self.visit("/desk/sidra-sale-quotation/new", SALES_USER), "/berjaya/sales/quotations"
		)
		self.assertEqual(
			self.visit("/desk/sidra-contract-settings", SALES_USER), "/berjaya/setup/contract-settings"
		)
		self.assertEqual(self.visit("/desk/user/x", SALES_USER), "/berjaya")

	def test_administrators_and_finance_keep_desk(self):
		for user in (SYSTEM_ONLY, FINANCE, "Administrator"):
			with self.subTest(user=user):
				self.assertIsNone(self.visit("/desk/sidra-unit", user))

	def test_only_desk_pages_are_redirected(self):
		for path in (
			"/api/method/frappe.auth.get_logged_user",
			"/printview",
			"/private/files/x.pdf",
			"/login",
			"/berjaya",
			"/desktop",
		):
			with self.subTest(path=path):
				self.assertIsNone(self.visit(path, SALES_USER))
		self.assertIsNone(self.visit("/desk/sidra-unit", SALES_USER, method="POST"))

	def test_non_staff_and_guests_are_left_alone(self):
		self.assertIsNone(self.visit("/desk", OUTSIDER))
		self.assertIsNone(self.visit("/desk", "Guest"))
