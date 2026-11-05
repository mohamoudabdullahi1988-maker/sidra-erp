"""Murabaha pricing (SRS 5.1, 5.4).

	F = P - D
	Profit = F x r x n / 12
	S = P + Profit
	M = (F + Profit) / n, rounded to the whole dollar; the last installment absorbs the difference.

A zero markup gives Profit = 0 and S = P, which is how both Sidra contracts work (5.4).
"""

from dataclasses import dataclass
from decimal import Decimal

from sidra_realestate.sidra_installments.engine.money import money, round_dollar
from sidra_realestate.sidra_installments.engine.terms import ContractTerms


@dataclass(frozen=True)
class Pricing:
	cash_price: Decimal  # P
	down_payment: Decimal  # D
	financed: Decimal  # F
	profit: Decimal
	sale_price: Decimal  # S
	installments: int  # n
	installment: Decimal  # M, whole dollars
	last_installment: Decimal  # absorbs rounding

	@property
	def installment_total(self) -> Decimal:
		"""F + Profit: the amount the schedule collects."""
		return self.financed + self.profit


def price_contract(cash_price, terms: ContractTerms) -> Pricing:
	p = money(cash_price)
	if p <= 0:
		raise ValueError("cash_price must be positive")

	d = _down_payment(p, terms)
	if d > p:
		raise ValueError("down payment cannot exceed the cash price")
	f = p - d
	n = terms.installments
	profit = money(f * terms.markup_rate * n / Decimal(12))
	total = f + profit

	m = round_dollar(total / n)
	last = total - m * (n - 1)
	if last <= 0:
		raise ValueError(
			f"Rounding leaves a last installment of {last} for {total} over {n} months; "
			"the amount is too small to split in whole dollars"
		)
	return Pricing(
		cash_price=p,
		down_payment=d,
		financed=f,
		profit=profit,
		sale_price=p + profit,
		installments=n,
		installment=m,
		last_installment=last,
	)


def _down_payment(price: Decimal, terms: ContractTerms) -> Decimal:
	if terms.down_payment_type == "none":
		return money(0)
	if terms.down_payment_type == "fixed":
		return money(terms.down_payment_value)
	# percent
	return money(price * terms.down_payment_value / Decimal(100))
