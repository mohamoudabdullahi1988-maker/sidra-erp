import frappe
from frappe.tests import IntegrationTestCase

from sidra_realestate.payment_providers import BANKS, WALLETS, ensure_payment_providers
from sidra_realestate.tests.helpers import as_user


class TestPaymentProviders(IntegrationTestCase):
	def test_native_names_and_preservation(self):
		with as_user("Administrator"):
			ensure_payment_providers()
			for bank in BANKS:
				self.assertTrue(frappe.db.exists("Bank", bank))
			for name in BANKS + WALLETS:
				self.assertTrue(frappe.db.exists("Mode of Payment", name))
			mode = frappe.get_doc("Mode of Payment", "Edahab")
			self.assertEqual(mode.type, "Phone")
			mode.enabled = 0
			mode.save()
			self.assertEqual(ensure_payment_providers(), {"created": []})
			self.assertEqual(frappe.db.get_value("Mode of Payment", "Edahab", "enabled"), 0)
