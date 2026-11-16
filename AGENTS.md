# AGENTS.md — sidra-erp

Instructions for Codex and any other coding agent. Latest user allocation (8 Nov 2026): Codex owns the remaining dashboard backend, shared staff web UI, Android/macOS clients, supporting reports and relevant integration tests end to end. Do not defer this dashboard work to Claude; the user explicitly reassigned it to Codex. This task allocation supersedes older role allocations, including decision G7, for this work. Keep backend business logic on the server and preserve the remaining repository rules, financial gates and existing records.

Follow `CLAUDE.md` exactly: it is the single source of rules, commands and the current task. Read `docs/DECISIONS-AND-GATES_v0.2.md` before any work; its decisions win over older documents.

Scoped user authorization (9 Nov 2026): populate fictional financial reports and dashboards. On an explicitly marked test site, the guarded finance demo loader targets the Company **Sidra Homes** (decision G14, 12 Nov 2026; `docs/FINANCE-DEMO_v0.2.md`). On that site the dataset is the twelve-month pilot set of `docs/PILOT-DEMO_v0.1.md` (decision G16, 13 Nov 2026), loaded by the same guards. It remains Administrator-only, requires the three staging flags, and refuses any Company holding GL entries its own manifest does not own. Production posting gates are unchanged; ERPNext remains the only ledger. This does not authorize production contract posting, refunds, penalties or a new accounting policy.

## Product and client names (decisions G17–G19, 13 Nov 2026)
Users see **Berjaya** as the software and **Sidra** as the company using it. Test for any string: does it name the software or the business?
- Software (application branding, navigation, login screens, page titles, help text, product documentation) → **Berjaya**. Take the name from `sidra_realestate/branding.py`; do not scatter the literal.
- Business (company records such as Company **Sidra Homes**, contracts, invoices, receipts, statements, letterheads) → **Sidra**. Never renamed, merged or rebranded.
- Internal identifier a user does not read as branding (app `sidra_realestate`, site `sidra.local`, `sidra_*` flags, DocType, field and role names, naming series such as `SSC-…`, routes, the repository) → unchanged.

Before starting, check open pull requests and branches from Claude Code, and continue the unfinished one instead of starting over. Merge into `develop` only when CI is green (decision G6).
