"""Contract terms: the frozen snapshot a contract is signed under (SRS 5.5, INS-19, INS-20).

A profile (Profile A, Profile B, or one management adds) is a mapping of settings.
`snapshot_terms` copies it, applies approved per-contract overrides and returns an
immutable ContractTerms. Editing the profile afterwards cannot reach the snapshot (AT-12).
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from decimal import Decimal

DOWN_PAYMENT_TYPES = ("none", "fixed", "percent")
PENALTY_TYPES = ("none", "per_day_capped", "fixed_after_notice")
PENALTY_ACCOUNTS = ("income", "charity")
REFUND_RETENTION_TYPES = ("none", "one_installment", "fixed", "percent")
TITLE_PENALTY_TYPES = ("none", "per_day", "per_month")


@dataclass(frozen=True)
class ContractTerms:
	# Payment plan
	installments: int
	due_day: int
	grace_months: int = 0
	down_payment_type: str = "none"
	down_payment_value: Decimal = Decimal("0")
	markup_rate: Decimal = Decimal("0")  # annual rate, e.g. Decimal("0.10")

	# Buyer late penalty (INS-15)
	penalty_type: str = "none"
	penalty_per_day: Decimal = Decimal("0")
	penalty_monthly_cap: Decimal = Decimal("0")
	penalty_fixed_amount: Decimal = Decimal("0")
	notice_days: int = 0
	penalty_account: str = "income"

	# Default and refund (INS-11, INS-16); None = default trigger off
	default_trigger_missed: int | None = None
	refund_retention_type: str = "none"
	refund_retention_value: Decimal = Decimal("0")

	# Title (SAL-18)
	title_deadline_days: int = 20
	title_penalty_type: str = "none"
	title_penalty_amount: Decimal = Decimal("0")
	title_refund_after_days: int | None = None
	title_refund_compensation_pct: Decimal = Decimal("0")

	def __post_init__(self):
		_check_range("installments", self.installments, 1, 60)
		_check_range("due_day", self.due_day, 1, 28)
		_check_range("grace_months", self.grace_months, 0, 12)
		_check_range("notice_days", self.notice_days, 0, 60)
		_check_choice("down_payment_type", self.down_payment_type, DOWN_PAYMENT_TYPES)
		_check_choice("penalty_type", self.penalty_type, PENALTY_TYPES)
		_check_choice("penalty_account", self.penalty_account, PENALTY_ACCOUNTS)
		_check_choice("refund_retention_type", self.refund_retention_type, REFUND_RETENTION_TYPES)
		_check_choice("title_penalty_type", self.title_penalty_type, TITLE_PENALTY_TYPES)
		if self.default_trigger_missed is not None and self.default_trigger_missed < 1:
			raise ValueError("default_trigger_missed must be 1 or more, or None for off")
		if self.title_deadline_days < 0:
			raise ValueError("title_deadline_days cannot be negative")
		for name in (
			"down_payment_value",
			"markup_rate",
			"penalty_per_day",
			"penalty_monthly_cap",
			"penalty_fixed_amount",
			"refund_retention_value",
			"title_penalty_amount",
			"title_refund_compensation_pct",
		):
			value = getattr(self, name)
			if not isinstance(value, Decimal):
				# frozen dataclass: normalise through object.__setattr__
				object.__setattr__(self, name, _decimal(name, value))
			if getattr(self, name) < 0:
				raise ValueError(f"{name} cannot be negative")


def snapshot_terms(profile: Mapping, overrides: Mapping | None = None) -> ContractTerms:
	"""Freeze a profile's settings plus approved overrides into a contract's terms.

	Unknown keys are rejected so a typo in a profile or override cannot be silently ignored.
	"""
	known = {f.name for f in fields(ContractTerms)}
	values = dict(profile)
	values.update(overrides or {})
	unknown = set(values) - known
	if unknown:
		raise ValueError(f"Unknown contract term(s): {', '.join(sorted(unknown))}")
	return ContractTerms(**values)


def _decimal(name, value) -> Decimal:
	if isinstance(value, float):
		raise TypeError(f"{name}: use int, str or Decimal, not float")
	return Decimal(value)


def _check_range(name, value, low, high):
	if not isinstance(value, int) or not low <= value <= high:
		raise ValueError(f"{name} must be an integer from {low} to {high}, got {value!r}")


def _check_choice(name, value, choices):
	if value not in choices:
		raise ValueError(f"{name} must be one of {choices}, got {value!r}")

