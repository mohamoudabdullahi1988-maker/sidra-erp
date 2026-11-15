# Demo rehearsal checks v0.1

15 November 2026 · issue #79 · companion to `DEMO-SCRIPT_v0.2.md`.

## Standalone demo accounts

As the bench owner on the already marked staging site:

```bash
bench --site sidra.local execute sidra_realestate.demo.ensure_demo_users
```

This requires Administrator and `sidra_allow_demo_data = 1`. It reuses the existing
account setup, assigns the existing profiles, and does not load sample business
records or set passwords. It prints interactive `bench --site … set-password …`
commands for the five profiled accounts. The existing helper also ensures the
unprivileged `demo.outsider@example.com` account; no password command is printed for it.
Repeated execution leaves already configured users unchanged.

No role profile is widened. Sales staff/management and General Management already
include ERPNext Sales User for CRM/Customer access. Project Staff includes Projects
User. Finance Review remains read-only; it does not gain posting rights.

## Walkthrough details

- Capture: the Sales User saves the External contract, fills its schedule and attaches
  its private signed copy. Only the Sales Manager confirms. All six timeline stages
  complete on confirmation; units become Under Contract.
- Sell a plot: until #81 lands, create the Customer separately after the Lead. This
  is not lead conversion. Cash discount approval up to 5% is by a second Sales Manager;
  above 5% requires the General Manager. Installment prices cannot be discounted below
  the listed price (G13).
- Generated contracts: the test uses the unchanged Profile A (14 installments).
  A 22-month quotation does not override its terms. For a 22-month demonstration,
  select an already approved profile with those terms; do not edit a profile or imply
  that quotation terms are automatically copied. Generated contracts return the explicit
  no-workflow-defined reason; only External registration has the six-stage timeline.
- KYC: the Sales Manager verifies the private ID evidence before a generated contract
  can submit. The generic integration fixture's SALES_MANAGER has only the custom role;
  this test adds Sales User inside its test transaction to match the existing demo role
  profile. Production roles are unchanged.
- Construction: New quotation is a navigation action, followed by save/submit on the
  quotation form. Billing percentages are checked at contract approval and must total 100.
- The Project Manager creates an inspection draft. Submission requires Sidra Inspector;
  the four-account walkthrough does not include one. Do not describe a saved draft as approved.
- A variation raised by `demo.pm` cannot be approved by that same user. For the ≤$1,000
  path, an administrator needs to provision a second Project Manager through normal user
  administration. The command deliberately keeps the existing five profiled accounts.
  Alternatively the existing General Manager may approve this amount. Above $1,000 the
  General Manager is required. Tests exercise a second PM and the GM respectively.
- Certification requires a completed stage, 100% recorded completion and an actual end date.
  It records certification, not an invoice.

## Verification

`sidra_realestate/tests/test_demo_flows.py` exercises all three journeys through
Berjaya's registration/form/action APIs using the test role users. It includes
permission/rule refusals and verifies that ledger document counts do not change.
Base units/users and uploaded synthetic PDFs are fixtures; business transitions
are not performed with ignored permissions. `test_demo_users.py` checks guards,
repeatability, existing role profiles and CRM reads.

```bash
bench --site <test-site> run-tests --app sidra_realestate --module sidra_realestate.tests.test_demo_flows
bench --site <test-site> run-tests --app sidra_realestate --module sidra_realestate.tests.test_demo_users
```

These are server integration tests, not a claim that browser rehearsal or live-site
verification has passed. The existing CI bench job discovers both test modules.
