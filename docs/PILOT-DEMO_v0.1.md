# Pilot demonstration dataset v0.1

**Document version:** v0.1 · **Date:** 13 Nov 2026 · **Decision:** G16
**Applies to:** the marked test site only — `http://5.253.233.218`, site `sidra.local`, Company **Sidra Homes**
**Supersedes nothing.** `FINANCE-DEMO_v0.2.md` (G14) stays in force; this widens its voucher set.

---

## 1. Why this exists

The system is shown to a prospective client module by module. A loader that posts ten vouchers
into a single month leaves the Profit and Loss, Trial Balance, AR and AP reports almost empty,
and leaves Property, Sales, Installments and Construction with a handful of records each. The
client sees empty screens, not a working system.

**Decision G16 (Mohamoud, 13 Nov 2026).** The fictional dataset on the test site is expanded to
twelve months of movement across every module that has DocTypes, under the Company **Sidra
Homes**. The widened voucher set replaces the fixed ten of `FINANCE-DEMO_v0.2.md` *for this
loader only*; the finance demo loader and its ten vouchers are unchanged and still run.

### What this does not change

Production posting gates are unchanged. ERPNext remains the only ledger (G4). Nothing here
recognises land-sale revenue, maps a contract to the ledger, executes a refund, applies a
penalty or transfers a title. Construction stays recorded only (G11). The P0 prototype
boundary in `CLAUDE.md` rule 3 is otherwise untouched.

---

## 2. Guards — none relaxed

Every guard of `FINANCE-DEMO_v0.2.md` applies to this loader:

- **Administrator only**, manual `bench execute` only — never a migration hook, scheduler job or
  whitelisted HTTP API.
- **All three staging flags** required: `sidra_allow_demo_data`, `sidra_finance_demo_site`,
  `sidra_allow_finance_demo_vouchers`.
- **Private ownership manifest** `sidra-pilot-demo-v1.json`, attached to the Company.
- **No-foreign-GL guard**, the first database read of the run, before any insert, inside the
  run's transaction. It refuses any Company holding a non-cancelled GL entry that neither the
  pilot manifest nor the finance demo manifest owns, naming the count and the first three
  vouchers. It **fails closed**: a missing, duplicated, unreadable or malformed manifest is a
  refusal, never "proceed".
- **One transaction**, full rollback on failure, private-file callbacks included.
- **Repeat protection:** a rerun reads the manifest, verifies, and returns it. It posts nothing,
  repairs nothing and advances no date.
- **Reserved identities:** the loader refuses if any pilot supplier, item, price list, contract
  profile, scheme or account already exists.

The two manifests are read together, so the finance demo and the pilot can coexist in Sidra
Homes and each still refuses ledger rows neither owns.

### What the loader never touches

- The Company itself — never created, renamed, merged or edited.
- The Company's own units, schemes and records. Every pilot record carries the `SHP-` prefix or
  the `SHP ` customer prefix; an integration test checksums the Company's own units before and
  after a load.
- The finance demo's `SHD` records and its ten vouchers.

---

## 3. The dataset

Deterministic from a fixed seed and the load date, so two runs of the same version produce the
same records. Twelve months back from the load date.

| Module | Records | What the client sees |
| --- | ---: | --- |
| Property — Schemes | 4 | Hargeisa East, Hargeisa North Ridge, Berbera Coastal, Burco West |
| Property — Units | 120 | 30 per scheme; Plot, House and Apartment; ready and off-plan; priced 5,500–28,000 |
| Property — Price History | 20 | Submitted price reviews scheduled 15–180 days ahead (a unit records its price the day it is created, and a new one must take effect after that) |
| Sales — Customers + KYC | 40 | 36 verified, 4 unverified so the KYC contract gate is visible |
| Sales — Quotations | 60 | Draft, Issued and Expired; a quarter carry discounts, some above the 5 % Sales Manager limit |
| Sales — Reservations | 25 | Active, Expired and Cancelled; created and closed through the Reserve Unit service, so each is dated the load day |
| Sales — Contracts | 45 | Cash and Installment; generated and externally registered; 42 submitted, 3 draft |
| Installments — Schedules | on every installment contract | 12, 18, 24 and 36 months; rounding lands on the final row |
| Sales — Title Transfers | 20 | Spread across In Progress, Due Soon, Overdue and deed issued |
| Construction — Jobs | 25 | All four service types; Enquiry through Completed; BOQ, five stages, billing % totalling 100 |
| Construction — Quotations | 1 per job past Enquiry | Draft, priced from the job's BOQ, with retention |
| Construction — Variation Orders | ~9 | Addition-only drafts |
| Finance — Vouchers | ~160 | 1 capital journal, 60 sales invoices, 35 purchase invoices, ~64 payments |

### Financial shape

| Measure | Approximate USD |
| --- | ---: |
| Owner capital | 500,000 |
| Revenue over twelve months | 554,250 |
| Expenses over twelve months | 99,750 |
| Customer receipts | 223,650 |
| Supplier payments | 51,625 |
| Receivables outstanding | 330,600 |
| Payables outstanding | 48,125 |
| Bank | 672,025 |

Sales invoices are paid in full, part paid or open in equal thirds, so Accounts Receivable shows
a real ageing profile rather than one bucket. Assets equal liabilities plus capital plus profit;
a pure test asserts the identity, so the Balance Sheet balances before anything is posted.

### Not covered

**Sidra Brokerage has no DocTypes in the app**, so there is nothing to populate. Its sidebar
section will be empty at the demonstration. This is a gap in the build, not in the dataset —
raise it as a `spec-question` issue if brokerage must be shown.

Inspection Reports are planned per job but not created: the DocType requires a checklist and an
inspector User, and the loader does not create staff users. Add them with `demo.py`'s
`_ensure_users` if the inspection screen must be shown.

---

## 4. Running it

As the bench operator, from `/home/frappe/sidra/frappe-bench`. **Back up first.**

```bash
bench --site sidra.local backup --with-files
bench --site sidra.local set-config sidra_allow_demo_data 1
bench --site sidra.local set-config sidra_finance_demo_site 1
bench --site sidra.local set-config sidra_allow_finance_demo_vouchers 1
bench --site sidra.local execute sidra_realestate.pilot_demo.create_pilot_demo_data
```

Read-only re-check at any time:

```bash
bench --site sidra.local execute sidra_realestate.pilot_demo.verify_pilot_demo
```

**If a guard refuses, stop and report the exact message.** Do not retry, do not loosen a flag,
do not work around a guard. The most likely first refusal on a Company that already holds
masters is the abbreviation or reserved-identity check.

### Verification — report each as pass/fail with the observed number

| # | Check | Expected |
| --- | --- | --- |
| 1 | The Company's own units, unchanged | count and checksum identical to before the load |
| 2 | Pilot schemes / units | 4 / 120 |
| 3 | Pilot customers with KYC | 40, of which 36 verified |
| 4 | Sale quotations / reservations / contracts | 60 / 25 / 45 |
| 5 | Construction jobs | 25, covering all four service types |
| 6 | Submitted pilot vouchers | ~160, debits equal credits |
| 7 | Profit and Loss, twelve-month range | revenue and expenses non-zero |
| 8 | Accounts Receivable | outstanding across more than one ageing bucket |
| 9 | Accounts Payable | outstanding greater than zero |
| 10 | `/sidra-staff/`, Company Sidra Homes | **persisted** records, not `?demo=1` |
| 11 | GL, Trial Balance, P&L, Balance Sheet, AR, AP | all open for Sidra Homes |
| 12 | Every Real Estate sidebar link | opens onto populated records, except Brokerage |

Items 10 to 12 need an authenticated browser session and are **manual**. Anything not verified is
reported as "not verified" — never inferred from a neighbouring check.

---

## 5. Removing it

There is no unload script. The dataset is removed by restoring the backup taken before the load.
Deleting a Company, merging one, or editing GL tables directly remains forbidden.

## Demo accounts for rehearsal (15 Nov 2026)

Run `bench --site sidra.local execute sidra_realestate.demo.ensure_demo_users` as the bench owner. Administrator and the staging flag are required. This creates no business data and sets no passwords; it prints the interactive password commands. See [Demo rehearsal checks v0.1](DEMO-REHEARSAL-CHECKS_v0.1.md) for role limits and the three flow tests.
