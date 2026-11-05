class SpecPending(NotImplementedError):
	"""Raised where the approved spec does not yet define the rule.

	The engine refuses to guess on money, dates, penalties or refunds
	(handover rule 1). The message names the open spec-question.
	"""
