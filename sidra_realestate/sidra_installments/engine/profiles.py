"""Reference values for Profile A and Profile B, from HANDOVER_v1.0 section 4.1 and SRS 5.5.

These are the engine's test reference. The Sidra Contract Profile DocType fixtures
(Phase 2) must carry the same values; change them only through an approved spec version.

Not encoded here, because the spec leaves them open (see the spec-question issues):
- Profile B title deadline: 20 days used; contract text also says 14.
- Profile B title refund right: after 90 days, refund + 10%; the amount rule is not defined.
"""

from types import MappingProxyType

PROFILE_A = MappingProxyType(
	{
		"installments": 14,
		"due_day": 5,
		"grace_months": 0,
		"down_payment_type": "none",
		"markup_rate": "0",
		"penalty_type": "per_day_capped",
		"penalty_per_day": "5",
		"penalty_monthly_cap": "150",
		"notice_days": 0,
		"penalty_account": "income",
		"default_trigger_missed": 2,
		"refund_retention_type": "one_installment",
		"title_deadline_days": 20,
		"title_penalty_type": "per_day",
		"title_penalty_amount": "5",
		"title_refund_after_days": None,
	}
)

PROFILE_B = MappingProxyType(
	{
		"installments": 24,
		"due_day": 10,
		"grace_months": 3,
		"down_payment_type": "fixed",
		"down_payment_value": "3000",
		"markup_rate": "0",
		"penalty_type": "fixed_after_notice",
		"penalty_fixed_amount": "100",
		"notice_days": 15,
		"penalty_account": "income",
		"default_trigger_missed": None,
		"refund_retention_type": "none",
		"title_deadline_days": 20,
		"title_penalty_type": "per_month",
		"title_penalty_amount": "220",
		"title_refund_after_days": 90,
		"title_refund_compensation_pct": "10",
	}
)
