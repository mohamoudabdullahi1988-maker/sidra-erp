"""Acceptance cases AT-01 to AT-13 (docs/HANDOVER_v1.0.md section 6).

Plain unittest, no Frappe: run with
	python -m unittest discover -s sidra_realestate -t .
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal

from sidra_realestate.sidra_installments.engine import (
	allocate,
	apply_allocation,
	buyer_late_penalty,
	check_default,
	final_due_date,
	generate_schedule,
	price_contract,
	snapshot_terms,
	title_delay,
)
from sidra_realestate.sidra_installments.engine.profiles import PROFILE_A, PROFILE_B

D = Decimal


def pay_in_full(lines, count):
	"""Mark the first `count` installments as fully paid."""
	return [line.with_paid(line.amount) if line.seq <= count else line for line in lines]


class TestAcceptance(unittest.TestCase):
	def test_at01_profile_a_14000_over_14_months(self):
		terms = snapshot_terms(PROFILE_A)
		pricing = price_contract(14000, terms)
		lines = generate_schedule(pricing, terms, date(2025, 8, 31))

		self.assertEqual(len(lines), 14)
		self.assertTrue(all(line.amount == D("1000.00") for line in lines))
		self.assertTrue(all(line.due_date.day == 5 for line in lines))
		self.assertEqual(lines[0].due_date, date(2025, 9, 5))
		self.assertEqual(lines[-1].due_date, date(2026, 10, 5))
		self.assertEqual(pricing.down_payment, D("0.00"))

	def test_at02_hagbad_full_plot_rounding(self):
		terms = snapshot_terms(PROFILE_A)
		pricing = price_contract(11000, terms)
		lines = generate_schedule(pricing, terms, date(2026, 11, 5))

		self.assertEqual([line.amount for line in lines[:13]], [D("786.00")] * 13)
		self.assertEqual(lines[13].amount, D("782.00"))
		self.assertEqual(sum(line.amount for line in lines), D("11000.00"))

	def test_at03_profile_b_down_payment_and_grace(self):
		terms = snapshot_terms(PROFILE_B)
		pricing = price_contract(9000, terms)
		lines = generate_schedule(pricing, terms, date(2026, 1, 15))

		self.assertEqual(pricing.down_payment, D("3000.00"))
		self.assertEqual(len(lines), 24)
		self.assertTrue(all(line.amount == D("250.00") for line in lines))
		self.assertTrue(all(line.due_date.day == 10 for line in lines))
		self.assertEqual(lines[0].due_date, date(2026, 4, 10))
		self.assertEqual(lines[-1].due_date, date(2028, 3, 10))

	def test_at04_hagbad_half_plot(self):
		terms = snapshot_terms(PROFILE_A, {"installments": 22})
		pricing = price_contract(5500, terms)
		lines = generate_schedule(pricing, terms, date(2026, 11, 5))

		self.assertEqual(len(lines), 22)
		self.assertTrue(all(line.amount == D("250.00") for line in lines))

	def test_at05_murabaha_worked_example(self):
		terms = snapshot_terms(
			PROFILE_A,
			{"installments": 24, "down_payment_type": "fixed", "down_payment_value": "9000", "markup_rate": "0.10"},
		)
		pricing = price_contract(30000, terms)

		self.assertEqual(pricing.financed, D("21000.00"))
		self.assertEqual(pricing.profit, D("4200.00"))
		self.assertEqual(pricing.sale_price, D("34200.00"))
		self.assertEqual(pricing.installment, D("1050.00"))
		self.assertEqual(pricing.last_installment, D("1050.00"))

		# SRS 5.2: each installment splits $875 cost recovery + $175 profit
		lines = generate_schedule(pricing, terms, date(2026, 11, 1))
		self.assertTrue(all(line.cost_part == D("875.00") for line in lines))
		self.assertTrue(all(line.profit_part == D("175.00") for line in lines))

	def test_at06_profile_a_three_days_late(self):
		terms = snapshot_terms(PROFILE_A)
		due = date(2025, 9, 5)
		penalty = buyer_late_penalty(terms, due, as_of=date(2025, 9, 30), settled_on=date(2025, 9, 8))
		self.assertEqual(penalty, D("15.00"))

	def test_at07_profile_a_penalty_capped(self):
		terms = snapshot_terms(PROFILE_A)
		due = date(2025, 9, 5)
		penalty = buyer_late_penalty(terms, due, as_of=due + timedelta(days=40))
		self.assertEqual(penalty, D("150.00"))

	def test_at08_default_flag_and_refund(self):
		terms = snapshot_terms(PROFILE_A)
		pricing = price_contract(14000, terms)
		lines = pay_in_full(generate_schedule(pricing, terms, date(2025, 8, 31)), 5)
		# installments 6 (2026-02-05) and 7 (2026-03-05) missed
		result = check_default(terms, lines, as_of=date(2026, 3, 6))

		self.assertEqual(result.paid_total, D("5000.00"))
		self.assertEqual(result.consecutive_missed, 2)
		self.assertTrue(result.flagged)
		self.assertEqual(result.refund, D("4000.00"))

	def test_at09_profile_b_fixed_penalty_after_notice(self):
		terms = snapshot_terms(PROFILE_B)
		due = date(2026, 4, 10)
		notice = date(2026, 4, 20)
		penalty = buyer_late_penalty(terms, due, as_of=notice + timedelta(days=15), notice_served_on=notice)
		self.assertEqual(penalty, D("100.00"))

	def test_at10_oldest_first_allocation(self):
		terms = snapshot_terms(PROFILE_A)
		pricing = price_contract(14000, terms)
		lines = generate_schedule(pricing, terms, date(2025, 8, 31))
		allocation = allocate(lines, 1500, paid_on=date(2025, 10, 20))
		lines = apply_allocation(lines, allocation)

		self.assertEqual(allocation.parts, ((1, D("1000.00")), (2, D("500.00"))))
		self.assertTrue(lines[0].is_paid)
		self.assertEqual(lines[1].paid, D("500.00"))
		self.assertEqual(lines[1].outstanding, D("500.00"))

	def test_at11_title_delay_penalty_profile_a(self):
		terms = snapshot_terms(PROFILE_A)
		final = date(2026, 10, 5)
		result = title_delay(terms, final, as_of=final + timedelta(days=23))
		self.assertEqual(result.deadline, date(2026, 10, 25))
		self.assertEqual(result.days_late, 3)
		self.assertEqual(result.penalty, D("15.00"))

	def test_at12_profile_edit_does_not_reach_signed_contract(self):
		profile = dict(PROFILE_A)
		signed = snapshot_terms(profile)
		before = generate_schedule(price_contract(14000, signed), signed, date(2025, 8, 31))

		profile.update({"installments": 24, "due_day": 10, "penalty_per_day": "10"})
		after = generate_schedule(price_contract(14000, signed), signed, date(2025, 8, 31))

		self.assertEqual(signed.installments, 14)
		self.assertEqual(signed.due_day, 5)
		self.assertEqual(signed.penalty_per_day, D("5"))
		self.assertEqual(before, after)
		with self.assertRaises(AttributeError):
			signed.installments = 24  # frozen

	def test_at13_extra_payment_clears_last_installments(self):
		terms = snapshot_terms(PROFILE_A)
		pricing = price_contract(14000, terms)
		lines = pay_in_full(generate_schedule(pricing, terms, date(2025, 8, 31)), 6)
		self.assertEqual(final_due_date(lines), date(2026, 10, 5))

		allocation = allocate(lines, 2000, paid_on=date(2026, 2, 20), mode="early_payment")
		lines = apply_allocation(lines, allocation)

		self.assertEqual(allocation.parts, ((14, D("1000.00")), (13, D("1000.00"))))
		self.assertTrue(lines[12].is_paid and lines[13].is_paid)
		self.assertFalse(lines[6].is_paid)
		self.assertEqual(final_due_date(lines), date(2026, 8, 5))  # two months early


if __name__ == "__main__":
	unittest.main()
