from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.api.activity import timeline, version_changes
from sidra_realestate.api.conversations import messages, send
from sidra_realestate.api.discovery import _csv_value, catalogue, export_report, report, search
from sidra_realestate.tests.helpers import OUTSIDER, as_user, ensure_base_records, make_job


class TestDiscoveryActivity(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_base_records()

	def test_search_report_and_denial(self):
		job = make_job()
		with as_user("Administrator"):
			self.assertTrue(any(row["doctype"] == job.doctype for row in catalogue()))
			self.assertTrue(
				any(row["name"] == job.name for group in search(job.name) for row in group["rows"])
			)
			rows = report(job.doctype, [["name", "=", job.name]], ["name"])["rows"]
			self.assertEqual([r.name for r in rows], [job.name])
			with self.assertRaises(frappe.ValidationError):
				report(job.doctype, columns=["password"])
			with self.assertRaises(frappe.ValidationError):
				report(job.doctype, filters=[["name", "injected", job.name]])
		with as_user(OUTSIDER):
			self.assertFalse(search(job.name))
			with self.assertRaises(frappe.PermissionError):
				report(job.doctype)
			with self.assertRaises(frappe.PermissionError):
				export_report(job.doctype)
			with self.assertRaises(frappe.PermissionError):
				timeline(job.doctype, job.name)
			with self.assertRaises(frappe.PermissionError):
				messages(job.doctype, job.name)

	def test_timeline_pages_and_child_redaction(self):
		job = make_job()
		with as_user("Administrator"):
			for i in range(55):
				job.add_comment("Info", f"Synthetic event {i}")
			first = timeline(job.doctype, job.name)
			second = timeline(job.doctype, job.name, 50)
			self.assertTrue(first["has_more"])
			self.assertFalse({r["key"] for r in first["rows"]} & {r["key"] for r in second["rows"]})
			self.assertTrue(any(r["kind"] == "Created" for r in second["rows"]))
			field = next(f for f in frappe.get_meta(job.doctype).fields if f.fieldtype == "Table")
			child_field = next(
				f.fieldname
				for f in frappe.get_meta(field.options).fields
				if f.fieldtype == "Data" and not f.hidden
			)
			changes = version_changes(
				job.doctype,
				{
					"added": [[field.fieldname, {child_field: "visible", "unreadable_field": "SECRET"}]],
					"row_changed": [
						[
							field.fieldname,
							1,
							"ROW",
							[[child_field, "old", "new"], ["unreadable_field", "SECRET", "SECRET2"]],
						]
					],
				},
			)
			self.assertIn("visible", str(changes))
			self.assertIn("old → new", str(changes))
			self.assertNotIn("SECRET", str(changes))

	def test_send_uses_native_mail_and_rejects_foreign_attachments(self):
		job, other = make_job(), make_job()
		with as_user("Administrator"):
			file = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": "synthetic.txt",
					"content": "Synthetic only",
					"is_private": 1,
					"attached_to_doctype": other.doctype,
					"attached_to_name": other.name,
				}
			).insert()
			with patch("frappe.core.doctype.communication.email.make") as native:
				with self.assertRaises(frappe.PermissionError):
					send(
						job.doctype,
						job.name,
						"synthetic@example.invalid",
						"Test",
						"Message",
						attachments=[file.name],
					)
				native.assert_not_called()
				send(job.doctype, job.name, "synthetic@example.invalid", "Test", "<script>literal</script>")
				self.assertTrue(native.call_args.kwargs["send_email"])
				self.assertIn("&lt;script&gt;", native.call_args.kwargs["content"])
				self.assertEqual(native.call_args.kwargs["name"], job.name)
		with as_user(OUTSIDER), patch("frappe.core.doctype.communication.email.make") as native:
			with self.assertRaises(frappe.PermissionError):
				send(job.doctype, job.name, "synthetic@example.invalid", "Test", "Message")
			native.assert_not_called()

	def test_csv_formula_cells_are_literal(self):
		for value in ("=1+1", "+SUM(A1)", "@call", "  =1"):
			self.assertTrue(_csv_value(value).startswith("'"))
		self.assertEqual(_csv_value("plain"), "plain")

	def test_native_accounting_reports_keep_native_permissions(self):
		from sidra_realestate.api.native_reports import catalogue as native_catalogue, run_report
		from sidra_realestate.tests.helpers import COMPANY

		with as_user("Administrator"):
			available = native_catalogue()
			self.assertEqual(len(available), 3)
			for name in ("General Ledger", "Accounts Receivable", "Accounts Payable"):
				filters = {"company": COMPANY}
				if name == "General Ledger":
					filters.update(from_date="2026-01-01", to_date="2026-12-31")
				else:
					filters["report_date"] = "2026-12-31"
				result = run_report(name, filters)
				self.assertIsInstance(result["rows"], list)
				self.assertTrue(result["columns"])
		with as_user(OUTSIDER):
			self.assertFalse(native_catalogue())
			with self.assertRaises(frappe.PermissionError):
				run_report(
					"General Ledger", {"company": COMPANY, "from_date": "2026-01-01", "to_date": "2026-12-31"}
				)
