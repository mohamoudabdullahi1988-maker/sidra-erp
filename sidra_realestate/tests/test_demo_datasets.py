"""The finance demo (G14) and the pilot dataset (G16) both load into the Company Sidra Homes.

The finance demo checks absolute totals for that Company and its loader refuses a Company
holding ledger entries it does not own, so it must run before the pilot dataset is loaded.
Frappe's test discovery walks files in file-system order (`os.walk`, unsorted), which differs
between machines, so as two modules they ran in either order and the finance demo test failed
whenever the pilot ran first. Here both are classes of one module: unittest loads a module's
classes in name order (`TestDemo1Finance` before `TestDemo2Pilot`), and each class keeps its own
test transaction, as when they were separate modules. `test_order` guards the names.
"""

import sys

from frappe.tests import IntegrationTestCase

from sidra_realestate.tests.test_finance_demo import FinanceDemoChecks
from sidra_realestate.tests.test_pilot_approvals import PilotApprovalChecks
from sidra_realestate.tests.test_pilot_demo import PilotDemoChecks
from sidra_realestate.tests.test_pilot_extras import PilotExtrasChecks
from sidra_realestate.tests.test_pilot_risks import PilotRisksChecks


class TestDemo1Finance(FinanceDemoChecks, IntegrationTestCase):
	pass


class TestDemo2Pilot(PilotDemoChecks, IntegrationTestCase):
	def test_order(self):
		classes = [name for name in sorted(dir(sys.modules[__name__])) if name.startswith("TestDemo")]
		self.assertEqual(
			classes,
			["TestDemo1Finance", "TestDemo2Pilot", "TestDemo3Extras", "TestDemo4Risks", "TestDemo5Approvals"],
		)


class TestDemo3Extras(PilotExtrasChecks, IntegrationTestCase):
	"""The pilot top-up (real project names, inspections, CRM) needs the pilot loaded first."""


class TestDemo4Risks(PilotRisksChecks, IntegrationTestCase):
	"""Fictional risks for the risk register (G26) need the top-up loaded first."""


class TestDemo5Approvals(PilotApprovalChecks, IntegrationTestCase):
	"""Approve only the fictional construction jobs after all original loader checks."""
