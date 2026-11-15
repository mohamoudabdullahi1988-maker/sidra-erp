# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Project risk register (decision G26, 15 Nov 2026).

A record of a risk, who owns it, how serious it is and what is being done about it. Record only:
it changes no job, contract, schedule or amount, and holds no money.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class SidraProjectRisk(Document):
	def validate(self):
		self._check_company()
		if self.status == "Closed":
			self.closed_on = self.closed_on or getdate(nowdate())
		else:
			self.closed_on = None

	def _check_company(self):
		for doctype, name in (("Sidra Construction Job", self.job), ("Sidra Scheme", self.scheme)):
			if not name:
				continue
			company = frappe.db.get_value(doctype, name, "company")
			if company and company != self.company:
				frappe.throw(
					_("{0} {1} belongs to {2}, not {3}").format(_(doctype), name, company, self.company)
				)
