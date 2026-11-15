# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""The period a live dashboard shows (Mohamoud, 15 Nov 2026: "dashboards must have date selection").

Every live method takes optional `from_date` and `to_date`. Without them the period is the last 12
whole months up to today, as before. Dated activity (records raised, signed, inspected, posted or
created) is filtered to the period; snapshots (units by status, stock on hand, open risks, amounts
still owed) stay as they are today, and each method says which is which in its `period` block.
"""

import frappe
from frappe import _
from frappe.utils import add_days, add_months, getdate, nowdate

DEFAULT_MONTHS = 12
MAX_DAYS = 366 * 5


def period(from_date=None, to_date=None) -> tuple:
	"""(from, to) as dates; refuses a reversed or over-long range."""
	today = getdate(nowdate())
	to = getdate(to_date) if to_date else today
	start = getdate(from_date) if from_date else add_months(to.replace(day=1), -(DEFAULT_MONTHS - 1))
	if start > to:
		frappe.throw(_("The period's start is after its end"))
	if (to - start).days > MAX_DAYS:
		frappe.throw(_("Choose a period of at most five years"))
	return start, to


def within(field, start, to) -> list:
	"""get_list conditions for `field` falling in the period (inclusive; Datetime fields too)."""
	return [[field, ">=", str(start)], [field, "<", str(add_days(to, 1))]]


def months(start, to) -> list[str]:
	"""'YYYY-MM' for every month the period touches, oldest first."""
	first, last = start.replace(day=1), to.replace(day=1)
	out = []
	while first <= last:
		out.append(str(first)[:7])
		first = add_months(first, 1)
	return out


def block(start, to, dated, snapshot) -> dict:
	return {"from": str(start), "to": str(to), "dated": list(dated), "as_of_today": list(snapshot)}
