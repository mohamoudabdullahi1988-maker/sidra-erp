"""Record evidence, not inferred business status transitions or financial posting."""

# Each tuple names evidence already stored by the existing controllers.
MILESTONES = {
	"Sidra Customer KYC": [("verified_on", "Buyer verified", "verified_by")],
	"Sidra Sale Quotation": [("discount_approved_on", "Discount approved", "discount_approved_by")],
	"Sidra Title Transfer": [
		("final_payment_date", "Final payment evidence entered", "final_payment_entered_by"),
		("final_payment_confirmed_on", "Final payment confirmed", "final_payment_confirmed_by"),
		("handed_over_on", "Deed handover recorded", None),
		("handover_confirmed_on", "Deed handover confirmed", "handover_confirmed_by"),
	],
	"Sidra Construction Quotation": [
		("client_accepted_on", "Client acceptance recorded", "client_accepted_by"),
		("contract_approved_on", "Contract approved", "contract_approved_by"),
	],
	"Sidra Construction Job": [("contract_approved_on", "Contract approved", "contract_approved_by")],
	"Sidra BOQ Revision": [("approved_on", "BOQ approved", "approved_by")],
	"Sidra Variation Order": [
		("client_approved_on", "Client approval recorded", "client_approved_by"),
		("approved_on", "Variation approved", "approved_by"),
	],
}


def record_stages(doctype, values, submittable=False):
	"""Only mark milestones complete when their own readable evidence exists."""
	stages = [
		{
			"key": "saved",
			"label": "Record created",
			"state": "completed",
			"timestamp": values.get("creation"),
			"responsible": values.get("owner"),
		}
	]
	if values.get("status"):
		stages.append(
			{
				"key": "status",
				"label": f"Saved status: {values['status']}",
				"state": "current",
				"detail": "The current saved status; earlier status changes are in change history.",
			}
		)
	for field, label, actor in MILESTONES.get(doctype, []):
		if doctype == "Sidra Sale Quotation" and values.get("discount_approval") == "Not Needed":
			continue
		stages.append(
			{
				"key": field,
				"label": label,
				"state": "completed" if values.get(field) else "pending",
				"unavailable": field not in values,
				"timestamp": values.get(field),
				"responsible": values.get(actor) if actor else None,
			}
		)
	if doctype == "Sidra Construction Job":
		for row in values.get("stages") or []:
			stages.append(
				{
					"key": row.get("name") or str(row.get("idx")),
					"label": row.get("stage_name") or "Project stage",
					"state": "completed"
					if row.get("certified")
					else "current"
					if row.get("status") == "In Progress"
					else "pending",
					"detail": f"{row.get('status') or 'Not recorded'} · {row.get('completion_pct') or 0}% recorded",
					"timestamp": row.get("certified_on"),
					"responsible": row.get("certified_by"),
				}
			)
	if submittable:
		state = values.get("docstatus", 0)
		stages.append(
			{
				"key": "submission",
				"label": "Cancelled" if state == 2 else "Submitted",
				"state": "blocked" if state == 2 else "completed" if state == 1 else "pending",
				"detail": "This document is cancelled." if state == 2 else None,
			}
		)
	return stages
