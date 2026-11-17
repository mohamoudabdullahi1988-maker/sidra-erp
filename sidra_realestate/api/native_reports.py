"""Run supported native accounting reports through Frappe's report permission boundary."""

import csv
import io

import frappe
from frappe import _
from frappe.utils import cint, getdate

from sidra_realestate.api.discovery import _csv_value

REPORTS = {
	"General Ledger": ["company", "from_date", "to_date"],
	"Accounts Receivable": ["company", "report_date"],
	"Accounts Payable": ["company", "report_date"],
}


def _report(name):
	from frappe.desk.query_report import get_report_doc

	if name not in REPORTS:
		frappe.throw(_("Unsupported report"), frappe.PermissionError)
	return get_report_doc(name)


@frappe.whitelist(methods=["GET"])
def catalogue():
	result = []
	for name, fields in REPORTS.items():
		if frappe.db.get_value("Report", name, "disabled"):
			continue
		try:
			doc = _report(name)
		except frappe.PermissionError, frappe.DoesNotExistError:
			continue
		result.append(
			{
				"name": name,
				"filters": fields,
				"can_export": bool(frappe.has_permission(doc.ref_doctype, "export")),
			}
		)
	return result


def _run(name, filters):
	from frappe.desk.query_report import run

	_report(name)
	filters = frappe.parse_json(filters) if isinstance(filters, str) else filters
	if not isinstance(filters, dict) or set(filters) != set(REPORTS[name]) or not all(filters.values()):
		frappe.throw(_("Complete all report filters"))
	frappe.get_doc("Company", filters["company"]).check_permission("read")
	for key, value in filters.items():
		if key != "company":
			getdate(value)
	if name == "General Ledger" and getdate(filters["from_date"]) > getdate(filters["to_date"]):
		frappe.throw(_("From date must be on or before To date"))
	if name != "General Ledger":
		filters = {**filters, "ageing_based_on": "Due Date", "range": "30, 60, 90, 120"}
	return run(name, filters=filters, ignore_prepared_report=True, are_default_filters=False)


@frappe.whitelist(methods=["GET"])
def run_report(name, filters, start=0):
	data = _run(name, filters)
	rows = data.get("result") or []
	start = max(0, cint(start))
	return {
		"columns": data.get("columns") or [],
		"rows": rows[start : start + 100],
		"has_more": len(rows) > start + 100,
	}


@frappe.whitelist(methods=["GET"])
def export_report(name, filters):
	doc = _report(name)
	frappe.has_permission(doc.ref_doctype, "export", throw=True)
	data = _run(name, filters)
	rows = data.get("result") or []
	if len(rows) > 10000:
		frappe.throw(_("More than 10,000 rows match. Narrow the dates before exporting."))
	columns = [c for c in data.get("columns", []) if not c.get("hidden")]
	output = io.StringIO()
	writer = csv.writer(output)
	writer.writerow([c.get("label", c["fieldname"]) for c in columns])
	writer.writerows([_csv_value(row.get(c["fieldname"])) for c in columns] for row in rows)
	frappe.response.update(type="download", filename=name + ".csv", filecontent=output.getvalue())
