"""Install and migrate hooks.

Creates Profile A and Profile B (handover v1.0 §4.1; SRS v1.6 §5.5; SRS v2.0 §3.3) when
they are missing. Existing profiles are never overwritten: management edits them, and a
signed contract keeps its own frozen copy (INS-20).
"""

import frappe

from sidra_realestate.branding import apply_branding
from sidra_realestate.desk_setup import repair_desk
from sidra_realestate.payment_providers import ensure_payment_providers
from sidra_realestate.sidra_installments.doctype.sidra_contract_profile.sidra_contract_profile import (
	COLLECTION_RULE_DEFAULTS,
)
from sidra_realestate.sidra_sales.doctype.sidra_contract_settings.sidra_contract_settings import (
	ensure_contract_settings,
)

# Decision D4 (Mohamoud, 6 Nov 2026, issue #13; docs/CONTRACT-CAPTURE_v0.3.md §6.3): Contract B's
# title deadline is 20 days; the 14 days in its clause 6 is a typo. This resolves SRS v2.0 §1.4 and
# §9.1, so Profile B is seeded without a legal hold. Existing sites: patch
# v0_3.resolve_profile_b_title_deadline.
PROFILE_B_TITLE_DEADLINE_DAYS = 20
PROFILE_B_TITLE_DEADLINE_NOTE = "Title deadline 20 days; the 14 in Contract B is a typo (D4, issue #13)."

PROFILES = [
	{
		"profile_name": "Profile A",
		"is_default": 1,
		"active": 1,
		"legal_hold": 0,
		"installments": 14,
		"due_day": 5,
		"grace_months": 0,
		"down_payment_type": "None",
		"down_payment_value": 0,
		"markup_rate": 0,
		"early_payment": "Reduce Last Installments",
		"penalty_type": "Per Day Capped",
		"penalty_per_day": 5,
		"penalty_monthly_cap": 150,
		"notice_days": 0,
		"default_trigger_missed": 2,
		"refund_retention_type": "One Installment",
		"title_deadline_days": 20,
		"title_penalty_type": "Per Day",
		"title_penalty_amount": 5,
		"title_refund_after_days": 0,
		**COLLECTION_RULE_DEFAULTS,
	},
	{
		"profile_name": "Profile B",
		"is_default": 0,
		"active": 1,
		"legal_hold": 0,
		"installments": 24,
		"due_day": 10,
		"grace_months": 3,
		"down_payment_type": "Fixed",
		"down_payment_value": 3000,
		"markup_rate": 0,
		"early_payment": "Reduce Last Installments",
		"penalty_type": "Fixed After Notice",
		"penalty_fixed_amount": 100,
		"notice_days": 15,
		"default_trigger_missed": 0,
		"refund_retention_type": "None",
		"title_deadline_days": PROFILE_B_TITLE_DEADLINE_DAYS,
		"title_deadline_note": PROFILE_B_TITLE_DEADLINE_NOTE,
		"title_penalty_type": "Per Month",
		"title_penalty_amount": 220,
		"title_refund_after_days": 90,
		"title_refund_compensation_pct": 10,
		**COLLECTION_RULE_DEFAULTS,
	},
]


# SAL-20 and SRS v1.6 §5.5. Wording is supplied and approved by Sidra (issue #8); none is invented here.
CLAUSES = [
	("RESTRICTIONS", "Neighbourhood restrictions"),
	("INSOLVENCY", "Insolvency protection for the buyer"),
	("TITLE-COSTS", "Title costs paid by the buyer"),
	("BEACON", "Beacon / foundation at the lowest of three quotes"),
	("FIRST-RIGHT", "Sidra's first right to design and build"),
]


# Each Sidra role paired with the ERPNext role its screens need (Customer / Project lookups).
# Finance posting roles are not bundled: Finance assigns them (SRS v2.0 §5).
# Created only when missing: re-saving a Role Profile on every migrate queues a background job
# that keeps it locked until a worker runs, which breaks the next migrate.
ROLE_PROFILES = {
	"Sidra Sales Staff": ["Sidra Sales User", "Sales User"],
	"Sidra Sales Management": ["Sidra Sales Manager", "Sales User"],
	"Sidra Project Staff": ["Sidra Project Manager", "Projects User"],
	"Sidra Inspection": ["Sidra Inspector", "Projects User"],
	"Sidra General Management": ["Sidra General Manager", "Sales User"],
	"Sidra Finance Review": ["Sidra Finance Reviewer"],
}


def after_install():
	ensure_payment_providers()
	ensure_contract_profiles()
	ensure_contract_clauses()
	ensure_role_profiles()
	ensure_contract_settings()
	apply_branding()
	repair_desk()


def after_migrate():
	ensure_payment_providers()
	ensure_contract_profiles()
	ensure_contract_clauses()
	ensure_role_profiles()
	ensure_contract_settings()
	apply_branding()
	repair_desk()


def ensure_role_profiles():
	for name, roles in ROLE_PROFILES.items():
		if frappe.db.exists("Role Profile", name):
			continue
		frappe.get_doc(
			{"doctype": "Role Profile", "role_profile": name, "roles": [{"role": role} for role in roles]}
		).insert(ignore_permissions=True)


def ensure_contract_clauses():
	"""Create the clause records (no wording, not approved) when missing. Never overwrites."""
	for code, title in CLAUSES:
		if not frappe.db.exists("Sidra Contract Clause", code):
			frappe.get_doc(
				{"doctype": "Sidra Contract Clause", "clause_code": code, "title": title, "active": 1}
			).insert(ignore_permissions=True)


def ensure_contract_profiles():
	for values in PROFILES:
		if frappe.db.exists("Sidra Contract Profile", values["profile_name"]):
			continue
		doc = frappe.new_doc("Sidra Contract Profile")
		doc.update(values)
		doc.flags.seeding = True
		doc.insert(ignore_permissions=True)
