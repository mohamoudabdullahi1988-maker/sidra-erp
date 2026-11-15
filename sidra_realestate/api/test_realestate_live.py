# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Live records for the Berjaya Real Estate Sales screens (demonstration, 17 Nov 2026)."""

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.realestate_live import get_realestate_live
from sidra_realestate.tests.helpers import (
	COMPANY,
	OUTSIDER,
	PROJECT_MANAGER,
	SALES_MANAGER,
	as_user,
	ensure_base_records,
	make_confirmed_contract,
	make_scheme,
	make_unit,
	unique,
)

SCHEME = "_TEST-RE-LIVE"


class TestRealEstateLive(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()
		cls.scheme = make_scheme(SCHEME)
		for _ in range(3):
			make_unit(unique("_T-RELIVE"), cls.scheme, cash_price=12000)
		cls.contract = make_confirmed_contract("_TEST-RE-LIVE-C")

	def test_sales_manager_sees_units_contracts_and_schedule(self):
		with as_user(SALES_MANAGER):
			data = get_realestate_live(COMPANY)
		scheme = next(s for s in data["units"]["schemes"] if s["scheme"] == self.scheme)
		self.assertEqual(scheme["counts"].get("Available"), 3)
		self.assertGreaterEqual(data["units"]["total"], 4)
		contract = next(r for r in data["contracts"]["rows"] if r["name"] == self.contract.name)
		self.assertEqual(contract["status"], "Confirmed")
		self.assertEqual(contract["agreed_price"], "10000.00")
		self.assertEqual(len(data["schedule"]["months"]), 12)
		self.assertTrue(all(isinstance(m["amount"], str) for m in data["schedule"]["months"]))

	def test_unreadable_groups_are_unavailable_not_zero(self):
		with as_user(PROJECT_MANAGER):  # no units, contracts or reservations
			data = get_realestate_live(COMPANY)
		for group in ("units", "contracts", "reservations", "schedule"):
			self.assertFalse(data[group]["available"], group)
			self.assertTrue(data[group]["reason"], group)

	def test_outsiders_and_unknown_companies_are_refused(self):
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_realestate_live(COMPANY)
		with as_user(SALES_MANAGER), self.assertRaises(frappe.ValidationError):
			get_realestate_live("_Test No Such Company")

	def test_reservation_expiry_window_and_company_scope(self):
		from frappe.utils import add_days, today

		from sidra_realestate.services.reservations import reserve_unit
		from sidra_realestate.tests.helpers import BUYER, OTHER_COMPANY, make_scheme, make_unit, unique

		scheme = make_scheme(unique("_T-EXP"))
		other_scheme = make_scheme(unique("_T-EXP-OTHER"), company=OTHER_COMPANY)
		units = [make_unit(unique("_T-EXP"), scheme).name for _ in range(3)]
		other = make_unit(unique("_T-EXP-OTHER"), other_scheme).name
		with as_user("Administrator"):
			included = reserve_unit(units[0], BUYER, days=7)["reservation"]
			later = reserve_unit(units[1], BUYER, days=8)["reservation"]
			past = reserve_unit(units[2], BUYER, days=1)["reservation"]
			foreign = reserve_unit(other, BUYER, days=3)["reservation"]
		frappe.db.set_value("Sidra Reservation", past, "expires_on", add_days(today(), -1))
		with as_user(SALES_MANAGER):
			data = get_realestate_live(COMPANY)
		names = {r["name"] for r in data["reservations"]["expiring"]}
		self.assertIn(included, names)
		self.assertFalse({later, past, foreign} & names)
		self.assertIn("status_counts", data["contracts"])
		self.assertIn("total", data["schedule"])
