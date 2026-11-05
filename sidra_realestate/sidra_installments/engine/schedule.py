"""Installment schedule generation (INS-02, INS-14).

First due date: the due day in (signing month + grace months). If that date is on or
before the signing date, the schedule starts one month later. This is the one rule
that fits both AT-01 (signed 31 Aug, due 5th, no grace -> 5 Sep) and AT-03 (signed
15 Jan, due 10th, 3 months grace -> 10 Apr). It is pending confirmation in a
spec-question issue, as is the treatment of a contract signed on the due day itself.
"""

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from sidra_realestate.sidra_installments.engine.money import ZERO, money
from sidra_realestate.sidra_installments.engine.pricing import Pricing
from sidra_realestate.sidra_installments.engine.terms import ContractTerms


@dataclass(frozen=True)
class Line:
	"""One scheduled installment and how much of it is paid."""

	seq: int
	due_date: date
	amount: Decimal
	cost_part: Decimal
	profit_part: Decimal
	paid: Decimal = ZERO

	@property
	def outstanding(self) -> Decimal:
		return self.amount - self.paid

	@property
	def is_paid(self) -> bool:
		return self.outstanding <= 0

	def with_paid(self, paid: Decimal) -> "Line":
		if paid < 0 or paid > self.amount:
			raise ValueError(f"Installment {self.seq}: paid {paid} outside 0..{self.amount}")
		return replace(self, paid=paid)


def add_months(year: int, month: int, months: int) -> tuple[int, int]:
	index = year * 12 + (month - 1) + months
	return index // 12, index % 12 + 1


def first_due_date(signed_on: date, terms: ContractTerms) -> date:
	year, month = add_months(signed_on.year, signed_on.month, terms.grace_months)
	first = date(year, month, terms.due_day)
	if first <= signed_on:
		year, month = add_months(year, month, 1)
		first = date(year, month, terms.due_day)
	return first


def generate_schedule(pricing: Pricing, terms: ContractTerms, signed_on: date) -> list[Line]:
	"""Return n lines: n-1 at the rounded installment, the last absorbing the difference.

	Each line is split into cost recovery and profit in proportion to F : Profit
	(SRS 5.2 shows $875 + $175 of $1,050); the last line absorbs split rounding.
	"""
	if pricing.installments != terms.installments:
		raise ValueError("pricing and terms disagree on the number of installments")

	n = pricing.installments
	first = first_due_date(signed_on, terms)
	total = pricing.installment_total
	lines = []
	profit_so_far = ZERO
	for i in range(n):
		is_last = i == n - 1
		amount = pricing.last_installment if is_last else pricing.installment
		if is_last:
			profit_part = pricing.profit - profit_so_far
		elif pricing.profit:
			profit_part = money(amount * pricing.profit / total)
		else:
			profit_part = ZERO
		profit_so_far += profit_part
		year, month = add_months(first.year, first.month, i)
		lines.append(
			Line(
				seq=i + 1,
				due_date=date(year, month, terms.due_day),
				amount=amount,
				cost_part=amount - profit_part,
				profit_part=profit_part,
			)
		)
	return lines
