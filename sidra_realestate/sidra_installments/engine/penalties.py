"""Buyer late penalty (INS-15) and Sidra's title delay penalty (SAL-18).

Buyer late penalty, per installment:

- per_day_capped (Profile A): rate x days late, where days late = days from the due
  date to the date the installment is settled (or `as_of` while unpaid), capped at
  the monthly cap. The cap is applied per installment: AT-07 (40 days late -> $150)
  rules out a cap per 30-day period or per calendar month of lateness. Whether the cap
  restarts for an installment that stays unpaid into a second month is open.
- fixed_after_notice (Profile B): one fixed amount when the installment is still unpaid
  `notice_days` after the written notice was served (AT-09). Day 15 itself counts as
  unpaid; the exact boundary is open.

Title delay: the deadline is `title_deadline_days` after final payment. Per-day penalty
(Profile A) is implemented. Per-month (Profile B, $220 a month) raises SpecPending
because the spec does not say whether a part month counts.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sidra_realestate.sidra_installments.engine.errors import SpecPending
from sidra_realestate.sidra_installments.engine.money import ZERO, money
from sidra_realestate.sidra_installments.engine.terms import ContractTerms


def buyer_late_penalty(
	terms: ContractTerms,
	due_date: date,
	as_of: date,
	settled_on: date | None = None,
	notice_served_on: date | None = None,
) -> Decimal:
	end = settled_on if settled_on is not None else as_of
	if end <= due_date or terms.penalty_type == "none":
		return ZERO

	if terms.penalty_type == "per_day_capped":
		days = (end - due_date).days
		return money(min(terms.penalty_per_day * days, terms.penalty_monthly_cap))

	# fixed_after_notice
	if notice_served_on is None:
		return ZERO
	if notice_served_on < due_date:
		raise ValueError("a late-payment notice cannot be served before the due date")
	deadline = notice_served_on + timedelta(days=terms.notice_days)
	return money(terms.penalty_fixed_amount) if end >= deadline else ZERO


@dataclass(frozen=True)
class TitleDelay:
	deadline: date
	days_late: int
	penalty: Decimal


def title_delay(
	terms: ContractTerms,
	final_payment_on: date,
	as_of: date,
	title_issued_on: date | None = None,
) -> TitleDelay:
	deadline = final_payment_on + timedelta(days=terms.title_deadline_days)
	end = title_issued_on if title_issued_on is not None else as_of
	days_late = max(0, (end - deadline).days)

	if terms.title_penalty_type == "none" or days_late == 0:
		penalty = ZERO
	elif terms.title_penalty_type == "per_day":
		penalty = money(terms.title_penalty_amount * days_late)
	else:
		raise SpecPending(
			"Title delay penalty per month (Profile B, $220 a month): the spec does not say "
			"whether a part month counts. See spec-question: title delay per month."
		)
	return TitleDelay(deadline=deadline, days_late=days_late, penalty=penalty)
