"""Permission-filtered cross-module search and operational report catalogue."""

import csv
import io

import frappe
from frappe import _
from frappe.utils import cint

from sidra_realestate.api.forms import FORMS

SAFE_TYPES = {"Data", "Link", "Select", "Date", "Datetime", "Currency", "Int", "Float", "Percent", "Check"}


def _schema(doctype, permission="read"):
	if doctype not in FORMS or frappe.get_meta(doctype).issingle:
		frappe.throw(_("Unknown report"), frappe.PermissionError)
	frappe.has_permission(doctype, permission, throw=True)
	meta = frappe.get_meta(doctype)
	permitted = set(meta.get_permitted_fieldnames(user=frappe.session.user))
	fields = [{"fieldname": "name", "label": "Record", "fieldtype": "Link", "options": doctype}]
	fields += [
		{"fieldname": f.fieldname, "label": f.label, "fieldtype": f.fieldtype, "options": f.options}
		for f in meta.fields
		if f.fieldname in permitted
		and not f.hidden
		and not f.is_virtual
		and f.fieldtype in SAFE_TYPES
		and f.options != "Password"
	]
	return fields


@frappe.whitelist(methods=["GET"])
def catalogue():
	return [
		{
			"doctype": dt,
			"title": dt + " report",
			"module": frappe.get_meta(dt).module,
			"columns": _schema(dt),
			"can_export": bool(frappe.has_permission(dt, "export")),
		}
		for dt in FORMS
		if not frappe.get_meta(dt).issingle
		and frappe.has_permission(dt, "read")
		and frappe.has_permission(dt, "report")
	]


def _query(doctype, filters=None, columns=None, start=0, length=51):
	schema = {f["fieldname"]: f for f in _schema(doctype)}
	columns = frappe.parse_json(columns) if isinstance(columns, str) else columns
	columns = columns or list(schema)[:8]
	if not isinstance(columns, list) or not columns or any(f not in schema for f in columns):
		frappe.throw(_("Choose readable report columns"))
	filters = frappe.parse_json(filters) if isinstance(filters, str) else filters
	filters = filters or []
	if not isinstance(filters, list) or len(filters) > 20:
		frappe.throw(_("Invalid filters"))
	for f in filters:
		if (
			not isinstance(f, list)
			or len(f) != 3
			or f[0] not in schema
			or f[1] not in ("=", "!=", "like", ">=", "<=")
		):
			frappe.throw(_("Invalid filter"))
	return frappe.get_list(
		doctype,
		fields=columns,
		filters=filters,
		order_by="modified desc, name asc",
		start=max(0, cint(start)),
		page_length=length,
	)


@frappe.whitelist(methods=["GET"])
def report(doctype, filters=None, columns=None, start=0):
	_schema(doctype, "report")
	rows = _query(doctype, filters, columns, start)
	return {"rows": rows[:50], "has_more": len(rows) > 50}


def _csv_value(value):
	text = "" if value is None else str(value)
	return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text


@frappe.whitelist(methods=["GET"])
def export_report(doctype, filters=None, columns=None):
	_schema(doctype, "report")
	_schema(doctype, "export")
	rows = _query(doctype, filters, columns, length=10001)
	if len(rows) > 10000:
		frappe.throw(_("More than 10,000 rows match. Narrow the filters before exporting."))
	selected = frappe.parse_json(columns) if isinstance(columns, str) else columns
	selected = selected or [f["fieldname"] for f in _schema(doctype)][:8]
	output = io.StringIO()
	writer = csv.writer(output)
	writer.writerow(selected)
	writer.writerows([_csv_value(row.get(f)) for f in selected] for row in rows)
	frappe.response.update(type="download", filename=f"{doctype}.csv", filecontent=output.getvalue())


@frappe.whitelist(methods=["GET"])
def search(text, doctype=None, start=0):
	text = (text or "").strip()
	if len(text) < 2 or len(text) > 100:
		frappe.throw(_("Enter between 2 and 100 characters"))
	if doctype and doctype not in FORMS:
		frappe.throw(_("Unknown record type"), frappe.PermissionError)
	groups = []
	for dt in [doctype] if doctype else FORMS:
		if frappe.get_meta(dt).issingle or not frappe.has_permission(dt, "read"):
			continue
		schema = _schema(dt)
		fields = [f["fieldname"] for f in schema if f["fieldtype"] in {"Data", "Link"}][:12]
		rows = frappe.get_list(
			dt,
			fields=["name"],
			or_filters=[[f, "like", "%" + text + "%"] for f in fields],
			order_by="modified desc, name asc",
			start=max(0, cint(start)) if doctype else 0,
			page_length=21,
		)
		if rows:
			groups.append({"doctype": dt, "rows": rows[:20], "has_more": len(rows) > 20})
	return groups
