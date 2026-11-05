"""Default and refund (INS-11, INS-16).

An installment counts as missed once its due date has passed (`due_date < as_of`) and
it is not fully paid. A contract is flagged for cancellation review when the longest
run of consecutive missed installments reaches the profile's trigger (Profile A: 2).
Flagging starts a review; it never cancels a contract on its own.

Refund = installment payments received less the retained charge, never below zero.
"One installment" retains the regular installment amount (the first line's amount, so
$786 not $782 for the Hagbad full plot). Penalties paid are not part of the refund base.
Both points are pending confirmation in a spec-question issue.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sidra_realestate.sidra_installments.engine.money import ZERO, money
from sidra_realestate.sidra_installments.engine.schedule import Line
from sidra_realestate.sidra_installments.engine.terms import ContractTerms


@dataclass(frozen=True)
class DefaultCheck:
	flagged: bool
	consecutive_missed: int
	paid_total: Decimal
	retained: Decimal
	refund: Decimal


def check_default(terms: ContractTerms, lines: Sequence[Line], as_of: date) -> DefaultCheck:
	ordered = sorted(lines, key=lambda line: line.seq)
	run = longest = 0
	for line in ordered:
		if line.due_date < as_of and not line.is_paid:
			run += 1
			longest = max(longest, run)
		else:
			run = 0

	paid_total = sum((line.paid for line in ordered), ZERO)
	retained = _retained(terms, ordered, paid_total)
	flagged = terms.default_trigger_missed is not None and longest >= terms.default_trigger_missed
	return DefaultCheck(
		flagged=flagged,
		consecutive_missed=longest,
		paid_total=paid_total,
		retained=retained,
		refund=max(ZERO, paid_total - retained),
	)


def _retained(terms: ContractTerms, lines: Sequence[Line], paid_total: Decimal) -> Decimal:
	kind = terms.refund_retention_type
	if kind == "none":
		return ZERO
	if kind == "one_installment":
		return lines[0].amount if lines else ZERO
	if kind == "fixed":
		return money(terms.refund_retention_value)
	return money(paid_total * terms.refund_retention_value / Decimal(100))
