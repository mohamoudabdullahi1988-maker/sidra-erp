"""Money helpers. USD, two decimals (NFR-10). Floats are refused."""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
DOLLAR = Decimal("1")
ZERO = Decimal("0.00")


def money(value) -> Decimal:
	"""Convert int, str or Decimal to a Decimal rounded to the cent (half up)."""
	if isinstance(value, float):
		raise TypeError("Use int, str or Decimal for money, not float")
	if isinstance(value, bool):
		raise TypeError("bool is not a money value")
	return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def round_dollar(value: Decimal) -> Decimal:
	"""Round to the whole dollar, half up (SRS 5.1: installments in whole dollars)."""
	return Decimal(value).quantize(DOLLAR, rounding=ROUND_HALF_UP).quantize(CENT)
