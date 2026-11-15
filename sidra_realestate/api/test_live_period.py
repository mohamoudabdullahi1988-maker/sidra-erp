# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Dashboard periods (15 Nov 2026): the range every live method reads dated activity for."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_months, getdate, today

from sidra_realestate.api.construction_live import get_construction_live
from sidra_realestate.api.crm_live import get_crm_live
from sidra_realestate.api.live_period import months, period
from sidra_realestate.tests.helpers import (
	COMPANY,
	INSPECTOR,
	SALES_USER,
	as_user,
	ensure_base_records,
	make_job,
	unique,
)


class TestLivePeriod(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def test_default_custom_and_refused_periods(self):
		start, to = period()
		self.assertEqual(to, getdate(today()))
		self.assertEqual(start, add_months(getdate(today()).replace(day=1), -11))
		self.assertEqual(len(months(start, to)), 12)
		self.assertEqual(period("2026-03-01", "2026-06-30"), (getdate("2026-03-01"), getdate("2026-06-30")))
		self.assertEqual(
			months(getdate("2026-03-15"), getdate("2026-06-02")), ["2026-03", "2026-04", "2026-05", "2026-06"]
		)
		with self.assertRaises(frappe.ValidationError):
			period("2026-07-01", "2026-06-30")
		with self.assertRaises(frappe.ValidationError):
			period("2010-01-01", "2026-06-30")

	def test_dated_records_follow_the_period_and_snapshots_do_not(self):
		job = make_job(status="In Progress")
		with as_user(INSPECTOR):
			report = frappe.get_doc(
				{
					"doctype": "Sidra Inspection Report",
					"job": job.name,
					"inspector": INSPECTOR,
					"inspection_date": add_days(today(), -40),
					"result": "Pass",
					"checklist": [{"item": "Formwork", "result": "Pass"}],
				}
			).insert()
		recent = (str(add_days(today(), -10)), today())
		older = (str(add_days(today(), -60)), str(add_days(today(), -30)))
		with as_user(INSPECTOR):
			now = get_construction_live(COMPANY, *recent)
			then = get_construction_live(COMPANY, *older)
		names = lambda data: {r["name"] for r in data["inspections"]["rows"]}  # noqa: E731
		self.assertNotIn(report.name, names(now))
		self.assertIn(report.name, names(then))
		# The job portfolio is as it is today, whatever the period.
		self.assertIn(job.name, {r["name"] for r in then["jobs"]["rows"]})
		self.assertEqual(then["period"]["from"], older[0])
		self.assertIn("jobs", then["period"]["as_of_today"])

	def test_crm_leads_are_counted_in_their_period(self):
		lead = frappe.get_doc(
			{"doctype": "Lead", "first_name": unique("_Test Period Lead"), "company": COMPANY}
		).insert(ignore_permissions=True)
		with as_user(SALES_USER):
			now = get_crm_live(COMPANY, str(add_days(today(), -1)), today())
			before = get_crm_live(COMPANY, str(add_days(today(), -90)), str(add_days(today(), -30)))
		self.assertIn(lead.name, {r["name"] for r in now["leads"]["rows"]})  # newest first
		self.assertNotIn(lead.name, {r["name"] for r in before["leads"]["rows"]})
		self.assertIn(len(before["leads"]["months"]), (3, 4))  # every month the 60 days touch
