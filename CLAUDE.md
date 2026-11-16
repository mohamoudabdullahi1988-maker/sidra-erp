# CLAUDE.md — sidra-erp

You are the **implementation** agent for Sidra Real Estate's ERPNext system. Read `docs/DECISIONS-AND-GATES_v0.2.md` (decisions win over older documents), `docs/SREMS-SRS_v2.0-DRAFT.md`, `docs/CLAUDE-CODE-HANDOFF_v2.0.md` and `docs/HANDOVER_v1.0.md` before any work.

## Project
- Custom Frappe app `sidra_realestate` on **ERPNext v16 / Frappe v16**, Python 3.14, Node 24, MariaDB 11.8. Pinned patch versions: see `docs/ENVIRONMENT_v0.1.md`.
- Modules: Sidra Property, Sidra Sales, Sidra Installments, Sidra Construction, Sidra Brokerage.
- Working spec: `docs/SREMS-SRS_v2.0-DRAFT.md` (decided 5 Nov 2026). Business requirements and IDs come from `docs/SREMS-SRS_v1.6.md`; traceability in `docs/REQUIREMENTS-TRACEABILITY_v2.0-DRAFT.csv`. Handover v1.0 applies where v2.0 is silent.
- The repository stays `sidra-erp` and the app stays `sidra_realestate` (v2.0 writes `sidra_real_estate`).

## Product and client names (decisions G17–G19, 13 Nov 2026)
Users see **Berjaya** as the software and **Sidra** as the company using it. Test for any string: does it name the software or the business?
- Software (application branding, navigation, login screens, page titles, help text, product documentation) → **Berjaya**. Take the name from `sidra_realestate/branding.py`; do not scatter the literal.
- Business (company records such as Company **Sidra Homes**, contracts, invoices, receipts, statements, letterheads) → **Sidra**. Never renamed, merged or rebranded.
- Internal identifier a user does not read as branding (app `sidra_realestate`, site `sidra.local`, `sidra_*` flags, DocType, field and role names, naming series such as `SSC-…`, routes, the repository) → unchanged.

## Roles
- Current dashboard assignment (Mohamoud, 8 Nov 2026): Codex implements the dashboard backend, staff web/native clients, supporting reports and integration tests end to end. This supersedes the older dashboard role allocations below; no Claude handoff is required to continue this work. Other repository rules and business gates remain in force. The staff front page at `/sidra` (decision G15, `docs/SHELL_v0.1.md`) is Claude Code's.
- ChatGPT: architecture, specs, acceptance criteria, security and code review.
- Claude Code (you): code, DocTypes, UI, tests, pull requests. Confirmed by Mohamoud on 7 Nov 2026, including the contract capture brief (`docs/CONTRACT-CAPTURE_v0.3.md`), whose Codex role is superseded. When Claude Code's usage limit is reached, Codex continues the same work under the same rules (`AGENTS.md`; decision G7).
- Mohamoud / Sidra management: final approval.

## Hard rules
1. Build only against the working spec. Ambiguity or conflict → open a GitHub issue labelled `spec-question`; never guess on money, dates, penalties, refunds or ownership.
2. Never change contract profile values, posting rules, penalty / refund formulas or approval limits without an approved spec version.
3. P0 prototype boundary (SRS v2.0 sections 3.3, 3.4, 9): post no financial vouchers, execute no refunds, apply no late penalties, transfer no title, and allow no per-contract overrides except as decided in issue #13 (D7: for registered External contracts, Sidra Sales Manager confirmation is the INS-19 approval of the contract's own terms). Profile B's legal hold is lifted only as decision D4 specifies (title deadline 20 days; issue #13, `docs/CONTRACT-CAPTURE_v0.3.md`): through the reviewed seed / patch, never by hand or by any other code path.
   Scoped user exception (9 Nov 2026): the requested fictional financial demo may submit native vouchers **only** via the guarded loader. On an explicitly marked test site, the guarded finance demo loader targets the Company **Sidra Homes** (decision G14, 12 Nov 2026; `docs/FINANCE-DEMO_v0.2.md`). On that site the dataset is the twelve-month pilot set of `docs/PILOT-DEMO_v0.1.md` (decision G16, 13 Nov 2026), loaded by the same guards. It remains Administrator-only, requires the three staging flags, and refuses any Company holding GL entries its own manifest does not own. Production posting gates are unchanged; ERPNext remains the only ledger; demo service revenue is not approval of land-sale recognition or contract-to-ledger mapping.
4. Never edit ERPNext or Frappe core; use DocTypes, Custom Fields, Property Setters, hooks, fixtures, patches in this app.
5. Branch `feature/<module>-<item>` from `develop`; PR into `develop`; merge when CI is green (decision G6). `main` only gets release merges.
6. Every feature PR has unit tests and, for DocTypes, Frappe integration tests. Money logic is tested against acceptance cases AT-01 to AT-13 in the handover.
7. Keep `sidra_realestate/__init__.py` version and `CHANGELOG.md` in step. Docs carry their version in the file name and inside.
8. No real customer data or secrets in the repo. Use synthetic names only.
9. PR description follows the template in `.github/pull_request_template.md`.

## Commands
```bash
ruff check sidra_realestate
python -m unittest discover -s sidra_realestate -p "test_engine_*.py" -t .
bench --site sidra.local run-tests --app sidra_realestate
bench --site sidra.local migrate
bench --site sidra.local export-fixtures --app sidra_realestate
```

## Next task
P0 prototype (SRS v2.0 section 7): 10 DocTypes, reservation, Profile A / B, contract snapshot, installment generator, construction job; bench CI. Then the handoff's subsequent PRs.
