# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Permission-filtered CRM counts; no communications are sent."""

from collections import Counter

import frappe
from frappe import _

from sidra_realestate.api.staff_dashboard import _staff_only


@frappe.whitelist(methods=["GET"])
def get_crm_live(company: str) -> dict:
	_staff_only()
	if not company or not frappe.db.exists("Company", company):
		frappe.throw(_("Choose a Company"))
	result = {"company": company}
	for key, doctype in (("leads", "Lead"), ("opportunities", "Opportunity")):
		if not frappe.has_permission(doctype, "read"):
			result[key] = {"available": False, "reason": _("Your role does not include {0}.").format(doctype)}
			continue
		fields = ["name", "status", "utm_source"]
		rows = frappe.get_list(doctype, filters={"company": company}, fields=fields, limit_page_length=0)
		result[key] = {
			"available": True,
			"total": len(rows),
			"status_counts": dict(Counter(r.status or _("Not set") for r in rows)),
			"channel_counts": dict(Counter(r.utm_source or _("Not set") for r in rows)),
		}
	return result
