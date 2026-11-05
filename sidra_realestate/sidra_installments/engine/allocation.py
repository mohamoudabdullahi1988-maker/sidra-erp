"""Payment allocation (INS-05, INS-13).

Two modes:

- "regular": oldest unpaid installment first, including installments not yet due
  (advance payment). This is INS-05 and AT-10.
- "early_payment": the cashier marks the receipt as an extra / early payment. It first
  clears anything already due (oldest first), then reduces the LAST installments,
  newest first, so the contract ends sooner (INS-13, AT-13).

The cashier chooses the mode on the receipt. Without that choice a buyer who pays next
month's installment a few days early would have it applied to the final month and still
show next month as unpaid. Pending confirmation in a spec-question issue.

Allocation covers installments only. Penalties are separate receivables (Sidra Penalty);
whether a receipt pays penalties before installments is an open spec question.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sidra_realestate.sidra_installments.engine.money import ZERO, money
from sidra_realestate.sidra_installments.engine.schedule import Line

MODES = ("regular", "early_payment")


@dataclass(frozen=True)
class Allocation:
	parts: tuple[tuple[int, Decimal], ...]  # (installment seq, amount)
	unallocated: Decimal  # overpayment beyond the whole schedule, held as customer credit

	@property
	def allocated(self) -> Decimal:
		return sum((amount for _, amount in self.parts), ZERO)


def allocate(lines: Sequence[Line], amount, paid_on: date, mode: str = "regular") -> Allocation:
	if mode not in MODES:
		raise ValueError(f"mode must be one of {MODES}")
	remaining = money(amount)
	if remaining <= 0:
		raise ValueError("payment amount must be positive")

	ordered = sorted(lines, key=lambda line: line.seq)
	if mode == "regular":
		order = ordered
	else:
		due = [line for line in ordered if line.due_date <= paid_on]
		not_due = [line for line in ordered if line.due_date > paid_on]
		order = due + list(reversed(not_due))

	parts = []
	for line in order:
		if remaining <= 0:
			break
		take = min(line.outstanding, remaining)
		if take > 0:
			parts.append((line.seq, take))
			remaining -= take
	return Allocation(parts=tuple(parts), unallocated=remaining)


def apply_allocation(lines: Sequence[Line], allocation: Allocation) -> list[Line]:
	"""Return new lines with the allocation added to `paid`."""
	extra = {}
	for seq, amount in allocation.parts:
		extra[seq] = extra.get(seq, ZERO) + amount
	return [line.with_paid(line.paid + extra[line.seq]) if line.seq in extra else line for line in lines]


def final_due_date(lines: Sequence[Line]) -> date | None:
	"""Due date of the last installment that still has money outstanding."""
	open_lines = [line for line in lines if not line.is_paid]
	return max((line.due_date for line in open_lines), default=None)
