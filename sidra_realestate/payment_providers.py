"""Sidra's approved payment-provider names; no ledger mappings or vouchers."""

import frappe

BANKS = ("Dahabshiil International Bank", "Salam Bank", "Premier Bank")
WALLETS = ("Edahab", "Zaad")


def ensure_payment_providers():
	"""Create missing native masters, preserving existing configuration and disabled modes.

	Called by install/migrate as Administrator. Intentionally not whitelisted. Company bank
	accounts require Finance's actual ledger mapping and are not fabricated from provider names.
	"""
	created = []
	for bank in BANKS:
		if not frappe.db.exists("Bank", bank):
			frappe.get_doc({"doctype": "Bank", "bank_name": bank}).insert(ignore_permissions=True)
			created.append({"doctype": "Bank", "name": bank})
	for provider in BANKS + WALLETS:
		if not frappe.db.exists("Mode of Payment", provider):
			frappe.get_doc(
				{
					"doctype": "Mode of Payment",
					"mode_of_payment": provider,
					"type": "Phone" if provider in WALLETS else "Bank",
					"enabled": 1,
				}
			).insert(ignore_permissions=True)
			created.append({"doctype": "Mode of Payment", "name": provider})
	return {"created": created}
