# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Live construction records for the Berjaya Construction screens (decision G25, step 1)."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from sidra_realestate.api.construction_live import get_construction_live
from sidra_realestate.tests.helpers import (
	COMPANY,
	INSPECTOR,
	OUTSIDER,
	PROJECT_MANAGER,
	SALES_MANAGER,
	as_user,
	ensure_base_records,
	make_job,
)


class TestConstructionLive(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()
		cls.job = make_job(
			status="In Progress",
			site_location="_Test site, Masalaha",
			stages=[
				{
					"stage_name": "Foundation",
					"status": "Completed",
					"completion_pct": 100,
					"planned_start": add_days(today(), -60),
					"planned_end": add_days(today(), -30),
				},
				{
					"stage_name": "Structure",
					"status": "In Progress",
					"completion_pct": 40,
					"planned_start": add_days(today(), -30),
					"planned_end": add_days(today(), -2),
				},
				{
					"stage_name": "Roofing",
					"planned_start": add_days(today(), -2),
					"planned_end": add_days(today(), 30),
				},
			],
		)
		with as_user(INSPECTOR):
			cls.report = frappe.get_doc(
				{
					"doctype": "Sidra Inspection Report",
					"job": cls.job.name,
					"inspector": INSPECTOR,
					"inspection_date": today(),
					"result": "Fail",
					"stage": "Structure",
					"checklist": [{"item": "Rebar spacing", "result": "Fail", "remarks": "Spacing too wide"}],
					"defects_found": "Rebar spacing too wide on the north wall",
					"next_action": "Re-fix the rebar and call for re-inspection",
				}
			).insert()

	def row(self, data):
		return next(r for r in data["jobs"]["rows"] if r["name"] == self.job.name)

	def test_project_manager_sees_jobs_stages_and_inspections(self):
		with as_user(PROJECT_MANAGER):
			data = get_construction_live(COMPANY)
		job = self.row(data)
		self.assertEqual(job["status"], "In Progress")
		self.assertEqual(job["progress"], 47)  # (100 + 40 + 0) / 3, recorded completion only
		self.assertEqual((job["stages"], job["stages_completed"], job["stages_overdue"]), (3, 1, 1))
		self.assertEqual(job["start"], str(add_days(today(), -60)))
		self.assertEqual(job["end"], str(add_days(today(), 30)))
		self.assertIsNone(job["point"])  # no location recorded; nothing is guessed
		self.assertTrue(data["variations"]["available"])
		report = next(r for r in data["inspections"]["rows"] if r["name"] == self.report.name)
		self.assertEqual((report["result"], report["status"]), ("Fail", "Draft"))

	def test_unreadable_groups_are_unavailable_not_zero(self):
		with as_user(INSPECTOR):  # reads jobs and inspections, not variation orders
			data = get_construction_live(COMPANY)
		self.assertTrue(data["jobs"]["available"])
		self.assertEqual(
			data["variations"], {"available": False, "reason": data["variations"]["reason"], "rows": []}
		)
		self.assertTrue(data["variations"]["reason"])
		with as_user(SALES_MANAGER):  # no construction access at all
			data = get_construction_live(COMPANY)
		self.assertFalse(data["jobs"]["available"])
		self.assertFalse(data["inspections"]["available"])

	def test_outsiders_and_unknown_companies_are_refused(self):
		with as_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_construction_live(COMPANY)
		with as_user(PROJECT_MANAGER), self.assertRaises(frappe.ValidationError):
			get_construction_live("_Test No Such Company")
