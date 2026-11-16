"""Saved-record progress and the same allowed actions as the record form."""

import frappe

from sidra_realestate.api.forms import _readable_values, get_form
from sidra_realestate.api.record_extras import _record
from sidra_realestate.services.record_progress import record_stages


@frappe.whitelist(methods=["GET"])
def get_timeline(doctype, name):
	doc = _record(doctype, name)
	if (
		doctype == "Sidra Sale Contract"
		and doc.get("source") == "External (registered)"
		and doc.get("contract_type") == "Installment"
	):
		from sidra_realestate.api.workflow import get_contract_timeline

		return get_contract_timeline(name)
	form = get_form(doctype, name)
	return {
		"supported": True,
		"record": {"doctype": doctype, "name": name},
		"stages": record_stages(doctype, _readable_values(doc), frappe.get_meta(doctype).is_submittable),
		"actions": [a["label"] for a in form["actions"]]
		+ [key.capitalize() for key in ("submit", "cancel") if form["permissions"].get(key)],
	}
