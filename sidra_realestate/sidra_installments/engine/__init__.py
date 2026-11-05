"""Installment engine: pure Python, no Frappe imports.

Pricing, schedules, payment allocation, buyer late penalties, default and refund,
early payment and Sidra's title delay penalty. DocTypes call into this package;
nothing here touches the database, so every rule is unit-tested on its own
against the acceptance cases AT-01 to AT-13 in docs/HANDOVER_v1.0.md.

Spec: SREMS-SRS v1.6 sections 5.1, 5.4, 5.5; INS-02, INS-05, INS-11, INS-13 to INS-16,
INS-20; SAL-18.
"""

from sidra_realestate.sidra_installments.engine.allocation import (
	Allocation,
	allocate,
	apply_allocation,
	final_due_date,
)
from sidra_realestate.sidra_installments.engine.default import DefaultCheck, check_default
from sidra_realestate.sidra_installments.engine.errors import SpecPending
from sidra_realestate.sidra_installments.engine.money import money
from sidra_realestate.sidra_installments.engine.penalties import TitleDelay, buyer_late_penalty, title_delay
from sidra_realestate.sidra_installments.engine.pricing import Pricing, price_contract
from sidra_realestate.sidra_installments.engine.schedule import Line, first_due_date, generate_schedule
from sidra_realestate.sidra_installments.engine.terms import ContractTerms, snapshot_terms

__all__ = [
	"Allocation",
	"ContractTerms",
	"DefaultCheck",
	"Line",
	"Pricing",
	"SpecPending",
	"TitleDelay",
	"allocate",
	"apply_allocation",
	"buyer_late_penalty",
	"check_default",
	"final_due_date",
	"first_due_date",
	"generate_schedule",
	"money",
	"price_contract",
	"snapshot_terms",
	"title_delay",
]
