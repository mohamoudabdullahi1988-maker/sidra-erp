# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Project risk register (decision G26)."""

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.tests.helpers import (
	COMPANY,
	GENERAL_MANAGER,
	INSPECTOR,
	OTHER_COMPANY,
	PROJECT_MANAGER,
	SALES_USER,
	as_user,
	ensure_base_records,
	make_job,
)

IGNORE_TEST_RECORD_DEPENDENCIES = [
	"Sidra Construction Job",
	"Sidra Scheme",
	"Company",
	"Customer",
	"User",
	"UOM",
]


class TestSidraProjectRisk(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def risk(self, user=PROJECT_MANAGER, **values):
		with as_user(user):
			return frappe.get_doc(
				{
					"doctype": "Sidra Project Risk",
					"company": COMPANY,
					"category": "Schedule delays",
					"description": "_Test structure behind plan",
					"rating": "High",
					"risk_owner": "Site Manager",
					**values,
				}
			).insert()

	def test_project_manager_records_and_closes_a_risk(self):
		risk = self.risk(job=make_job().name)
		self.assertEqual(risk.status, "Open")
		self.assertIsNone(risk.closed_on)
		with as_user(PROJECT_MANAGER):
			risk.status = "Closed"
			risk.save()
			self.assertIsNotNone(risk.closed_on)
			risk.status = "Monitoring"
			risk.save()
			self.assertIsNone(risk.closed_on)

	def test_job_must_belong_to_the_company(self):
		job = make_job()
		with self.assertRaisesRegex(frappe.ValidationError, "belongs to"):
			self.risk(company=OTHER_COMPANY, job=job.name, user="Administrator")

	def test_who_may_record_and_read(self):
		self.risk(user=GENERAL_MANAGER)
		with as_user(INSPECTOR):
			self.assertTrue(frappe.has_permission("Sidra Project Risk", "read"))
			self.assertFalse(frappe.has_permission("Sidra Project Risk", "create"))
		with as_user(SALES_USER):
			self.assertFalse(frappe.has_permission("Sidra Project Risk", "read"))
