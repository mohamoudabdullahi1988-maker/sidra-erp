import unittest

from sidra_realestate.services.record_progress import record_stages


class TestRecordProgress(unittest.TestCase):
	def test_approval_is_not_inferred_from_status_or_submission(self):
		rows = record_stages(
			"Sidra BOQ Revision", {"status": "Approved", "docstatus": 1, "approved_on": None}, True
		)
		self.assertEqual(next(r for r in rows if r["key"] == "approved_on")["state"], "pending")
		self.assertEqual(rows[-1]["state"], "completed")

	def test_hidden_evidence_is_unavailable(self):
		rows = record_stages("Sidra Customer KYC", {})
		self.assertTrue(rows[-1]["unavailable"])
		self.assertEqual(rows[-1]["state"], "pending")

	def test_real_evidence_preserves_actor_and_date(self):
		rows = record_stages(
			"Sidra Customer KYC", {"verified_on": "2026-11-16", "verified_by": "synthetic@example.test"}
		)
		self.assertEqual(rows[-1]["state"], "completed")
		self.assertEqual(rows[-1]["responsible"], "synthetic@example.test")

	def test_cancelled_document_is_never_shown_as_submitted(self):
		self.assertEqual(record_stages("Example", {"docstatus": 2}, True)[-1]["state"], "blocked")

	def test_completed_job_stage_requires_certification(self):
		rows = record_stages(
			"Sidra Construction Job",
			{
				"stages": [
					{"name": "one", "status": "Completed", "completion_pct": 100, "certified": 0},
					{"name": "two", "status": "Completed", "completion_pct": 100, "certified": 1},
				]
			},
		)
		self.assertEqual([r["state"] for r in rows[-2:]], ["pending", "completed"])

	def test_discount_not_required_does_not_show_approval(self):
		rows = record_stages("Sidra Sale Quotation", {"discount_approval": "Not Needed"})
		self.assertNotIn("discount_approved_on", [r["key"] for r in rows])
