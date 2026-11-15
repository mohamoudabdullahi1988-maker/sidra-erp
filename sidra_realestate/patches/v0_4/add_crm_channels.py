# Copyright (c) 2026, Mohamoud Abdullahi Sheikh
"""Add the requested CRM channels using native UTM Source records; preserve existing ones."""

import frappe

CHANNELS = ("Email", "WhatsApp", "Phone", "Website", "Walk-in", "Referral", "Facebook", "Instagram")


def execute():
	for channel in CHANNELS:
		if not frappe.db.exists("UTM Source", channel):
			frappe.get_doc({"doctype": "UTM Source", "__newname": channel, "description": channel}).insert(
				ignore_permissions=True
			)
