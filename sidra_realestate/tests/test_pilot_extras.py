"""The pilot top-up (real project names, inspections, CRM) on the disposable CI site.

Run by `test_demo_datasets.TestDemo3Extras`, after the pilot dataset itself is loaded.
"""

from unittest.mock import patch

import frappe

from sidra_realestate.finance_demo import COMPANY, FLAGS
from sidra_realestate.pilot_extras import MANIFEST, PROJECTS, create_pilot_extras
from sidra_realestate.services.pilot_dataset import PREFIX
from sidra_realestate.tests.helpers import as_user


class PilotExtrasChecks:
	def test_top_up_names_projects_and_adds_missing_records_once(self):
		# Guards: the staging flags and Administrator, as for the pilot itself.
		with as_user("Administrator"), patch.dict(frappe.conf, {flag: 0 for flag in FLAGS}):
			with self.assertRaisesRegex(frappe.ValidationError, "staging-only flags"):
				create_pilot_extras()
		with patch.dict(frappe.conf, {flag: 1 for flag in FLAGS}), as_user("sidra.manager@example.com"):
			with self.assertRaises(frappe.PermissionError):
				create_pilot_extras()

		gl_before = frappe.db.count("GL Entry")
		with as_user("Administrator"), patch.dict(frappe.conf, {flag: 1 for flag in FLAGS}):
			data = create_pilot_extras()
			self.assertTrue(data["created"])

			# Real project names on the pilot schemes; codes unchanged.
			names = set(
				frappe.get_all(
					"Sidra Scheme", filters={"scheme_code": ("like", PREFIX + "-%")}, pluck="scheme_name"
				)
			)
			self.assertEqual(names, {project[0] for project in PROJECTS.values()})

			# Jobs point at their project, with a map location.
			self.assertTrue(data["jobs"])
			for job in data["jobs"]:
				site, location = frappe.db.get_value(
					"Sidra Construction Job", job, ["site_location", "sidra_location"]
				)
				self.assertTrue(any(site.startswith(p[0]) for p in PROJECTS.values()), site)
				self.assertTrue(location)

			# Missing records now exist, unsubmitted, and nothing reached the ledger.
			self.assertTrue(data["inspections"])
			for report in data["inspections"]:
				self.assertEqual(frappe.db.get_value("Sidra Inspection Report", report, "docstatus"), 0)
			self.assertEqual(len(data["leads"]), 30)
			self.assertEqual(len(data["opportunities"]), 10)
			for lead in data["leads"]:
				self.assertTrue(frappe.db.get_value("Lead", lead, "lead_name").startswith(PREFIX + " "))
			self.assertEqual(frappe.db.count("GL Entry"), gl_before)

			# A rerun changes nothing.
			leads = frappe.db.count("Lead")
			again = create_pilot_extras()
			self.assertFalse(again["created"])
			self.assertEqual(frappe.db.count("Lead"), leads)
			self.assertEqual(
				frappe.db.count(
					"File",
					{"attached_to_doctype": "Company", "attached_to_name": COMPANY, "file_name": MANIFEST},
				),
				1,
			)
