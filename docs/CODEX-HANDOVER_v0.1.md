# Codex handover v0.1

15 Nov 2026 · from Claude Code to Codex · state at `develop` **v0.1.52** (PR #94 merged).

Rules are unchanged: `CLAUDE.md` and `AGENTS.md`, then `docs/DECISIONS-AND-GATES_v0.1.md` (decisions G1–G26 win over older documents). The work happens in this order:

1. demo-readiness support;
2. the remaining live screens;
3. Brokerage records, which are blocked until issue #95 is answered.

Each has its own GitHub issue.

---

## 1. Where things stand

### The client demonstration
- **When:** Tuesday 17 Nov 2026. Mohamoud presents.
- **Click path:** `docs/DEMO-SCRIPT_v0.2.md`. Server checks: `docs/DEMO-REHEARSAL-CHECKS_v0.1.md`.
- **Order:**
  - sample dashboards;
  - the same screens on live records;
  - real work: capture a contract, sell a plot, start a construction project.

### Test server
- **Site:** `sidra.local` at `http://5.253.233.218`, bench at `/home/frappe/sidra/frappe-bench`.
- **Running bench:** always as the frappe user through its login shell. `sudo -u frappe bench` fails with "command not found".
  ```bash
  sudo -u frappe -H bash -lc 'cd /home/frappe/sidra/frappe-bench && bench --site sidra.local <command>'
  ```
- **Deploy script:** `bash /root/berjaya-deploy_v0.2.sh` (deploy, `check`, `brand`, `rollback`).
  - The copy in `/root` must be refreshed from `apps/sidra_realestate/deploy/` after each deploy.
  - On 15 Nov, an old copy reported a false app_name FAIL that #92 had already fixed.
- **Last known state (15 Nov, afternoon):**
  - **Deployed:** v0.1.49 is confirmed. Mohamoud was deploying v0.1.52 when this was written; the outcome is not yet known.
  - **Readiness check:** 15 PASS, 4 FAIL. All four failures are "no password set" for `demo.sales`, `demo.manager`, `demo.gm` and `demo.pm`.
  - **Deploy check:** two FAILs on the last run, neither a real problem.
    - "sign-in page does not load berjaya-login.css": a stale website cache. Fix with `clear-website-cache`.
    - "app_name could not be verified": the old script copy in `/root`.
  - **Pending:** the risk loader `sidra_realestate.pilot_risks.create_pilot_risks` has not run on the server yet. It failed with `ModuleNotFoundError` because v0.1.52 wasn't deployed.

### Test data on the site (Company **Sidra Homes**, all fictional)
Every loader is guarded:
- Administrator only;
- the three staging flags;
- a private manifest;
- running it again changes nothing.

| Loader | What it adds |
|---|---|
| `pilot_demo.create_pilot_demo_data` (G16) | Twelve months: schemes, 120 units, buyers with KYC, quotations, reservations, 45 contracts, 25 construction jobs, about 160 vouchers |
| `pilot_extras.create_pilot_extras` | Real project names (Masalaha Hagbad, Rayan Gardens, Safa Housing, Berbera Townhouses), job map points, draft inspections, 30 leads, 10 opportunities, sales stages |
| `pilot_risks.create_pilot_risks` (G26) | 12 project risks |
| `demo.ensure_demo_users` | The four demo users and their role profiles (no passwords) |

Read-only check, as Administrator: `sidra_realestate.demo_readiness.check_demo_readiness`.

### Berjaya sample screens and live records
- **Where the code is:** sample screens are config-driven in `frontend/src/showcase/`:
  - `pages.js` holds the sample pages;
  - `live.js` builds the live pages;
  - `Showcase.vue` holds the "Sample data / Live records" switch (`?source=live`).
- **Rules for live pages:**
  - They come from read-only, permission-filtered server methods (`frappe.get_list`).
  - Money is an exact decimal string.
  - Unknown is a dash, never zero.
  - An unreadable group is returned as `{available: false, reason}`.

| Module | Tabs (\* = live records available) | Server method |
|---|---|---|
| Executive | overview\* | `staff_dashboard.get_dashboard` plus the construction and real estate methods |
| Construction | portfolio\*, schedule\*, cost\*, variations\*, quality\*, risk\*, stock\*, subcontractors\* | `construction_live.get_construction_live`; stock and subcontractors use `finance_live.get_operations_live` |
| Design & Engineering | overview\*, **architecture**, **civil**, inspection\* | `construction_live` (Design Only / Inspection Only jobs) |
| Real Estate Sales | inventory\*, pipeline\*, contracts\* | `realestate_live.get_realestate_live` |
| **Brokerage** | **overview** | none: there are no DocTypes yet |
| Finance | overview\* | `finance_live.get_finance_live` |

Still sample-only: **Design → Architecture**, **Design → Civil** and **Brokerage → Overview** (issues 2 and 3 below).

### Recent releases (all merged into `develop`, CI green)
| Version | PR | What |
|---|---|---|
| 0.1.52 | #94 | Risk register: **Sidra Project Risk** DocType (G26), live Risk tab, `pilot_risks` loader, readiness warning |
| 0.1.51 | #93 | Live Finance, Design & Engineering, Subcontractors, Stock |
| 0.1.50 | #92 | Deploy check reads the bare app name; bench commands in the `bash -lc` form |
| 0.1.49 | #90 | Live Executive overview |
| 0.1.48 | #89 | Live Construction Schedule and Cost & budget |
| 0.1.46–47 | #85, #86 | Codex: CRM forms (Lead, Opportunity, Dynamic Link, lead actions) |

### Open questions and gates
- **#95 `spec-question`:** brokerage commission, three money questions:
  1. the commission base;
  2. who receives the first payment in journey A;
  3. whether a confirmed rate is frozen.

  Do not build commission logic until Mohamoud answers (rule 1).
- **Still open (section 2 of the decisions file):** penalties, the posting matrix, and unsigned drafts locking a plot.

---

## 2. Tasks for Codex

### Task 1: Demo-readiness support (until Tuesday): issue #96
1. When Mohamoud pastes server output, diagnose it against this document. Expected sequence:
   - deploy v0.1.52;
   - refresh `/root/berjaya-deploy_v0.2.sh`;
   - `clear-cache` and `clear-website-cache`;
   - `check`;
   - `pilot_risks.create_pilot_risks`;
   - `set-password` for the four demo users;
   - the readiness check reaching 0 FAIL.
2. Fix any defect the rehearsal of `DEMO-SCRIPT_v0.2.md` finds, as a normal PR with tests.
3. Keep `DEMO-SCRIPT_v0.2.md` accurate. If a step changes, update the script in the same PR.
4. **Do not:**
   - set passwords or create users from code;
   - relax a loader guard;
   - post anything to the ledger.

### Task 2: Remaining live screens (Design → Architecture and Civil): issue #97
- **The gap:** the records can't tell architecture work from civil engineering. `Sidra Construction Job.service_type` has Full Construction, Design Only, Inspection Only and Beacon / Foundation.
- **Step 1, propose:** suggest the smallest data change in a `spec-question` issue, for example a "Design discipline" Select on the job (Architecture / Civil / Both) shown when the service type is Design Only.
  - It is not a money rule, but it changes the data model. Get Mohamoud's yes and record it as a decision.
- **Step 2, build:** then build the field, the `pilot_extras`-style guarded top-up for existing Design Only test jobs (a new manifest, never editing the existing ones), and the live builders in `live.js` with tests in `frontend/tests/showcase.test.mjs`.
- **If no answer comes before Tuesday:** leave both tabs as sample data. Showing them is fine; they are labelled.

### Task 3: Brokerage records (blocked on #95): issue #98
- **Spec:** `docs/BROKERAGE_v0.1.md`:
  - Sidra Agent;
  - Sidra Brokerage Listing;
  - commission fields on the sale contract, frozen in the snapshot;
  - acceptance tests BR-01 to BR-09.
- **Before #95 is answered:** nothing that computes or stores a commission amount.
- **After it is answered:**
  - record the answers as a decision;
  - bump the spec to v0.2;
  - build it on one branch, with Frappe integration tests for every BR case;
  - add a `brokerage` entry to `LISTS` and `NAV` in `www/berjaya.py`, matching `frontend/src/records.js`, and its cutover routes;
  - add a live Brokerage overview;
  - add a guarded fictional loader like `pilot_risks.py`.
- **Out of scope until Finance approves (spec §6):** no invoice, payment, GL entry or payout.

### Task 4: Keep this snapshot current
When a task finishes, update section 1 here and publish it as `CODEX-HANDOVER_v0.2.md`. Docs carry their version in the file name.

---

## 3. How the work is done here
- **Branch and merge:** branch, open a PR into `develop` using `.github/pull_request_template.md`, and merge when CI is green (G6).
- **Version:** keep `sidra_realestate/__init__.py` and `CHANGELOG.md` in step: one version per PR.
- **Checks before pushing:**
  - `ruff check sidra_realestate` and `ruff format sidra_realestate`;
  - `cd frontend && npm test`;
  - integration tests run in CI ("ERPNext bench install and integration tests").
- **DocType tests:** a new DocType test that links to jobs, schemes, companies or customers needs:
  ```python
  IGNORE_TEST_RECORD_DEPENDENCIES = ["Sidra Construction Job", "Sidra Scheme", "Company", "Customer", "User", "UOM"]
  ```
  Without it, Frappe's record generator tries to build ERPNext's sample Items and fails (seen on PR #94). Inside `api/` test files that variable raises an error; leave it out there.
- **Demo-loader tests:** they run in `tests/test_demo_datasets.py` as ordered classes (`TestDemo1Finance`, `TestDemo2Pilot`, …). A new loader adds the next class and updates `test_order`.
- **Data:** synthetic names only; no real customer data or secrets.
