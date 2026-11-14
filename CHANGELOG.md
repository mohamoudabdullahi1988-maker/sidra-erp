# Changelog

All notable changes to `sidra_realestate`. Versions follow `MAJOR.MINOR.PATCH`; each release is tagged in Git.

## [Unreleased]

### Added (v0.1.35 — module list tools and visual summaries)
- Expandable visual summaries, local search/sort previews, and CSV exports for loaded records in Properties, Contracts, Construction, Collections, Finance and generic Sales, Customer/KYC and Setup lists.
- Charts explicitly describe loaded-record coverage, retain unavailable values, and never imply company-wide totals or calculate financial balances.
- CSV exports include only configured columns and neutralize spreadsheet formulas. Existing workflows and server permissions are unchanged.
- Tests cover distributions, unavailable values, CSV escaping and browser interactions at desktop and phone widths.

### Changed (v0.1.34 — cutover: Sidra staff use Berjaya, Desk for administrators and finance, 14 Nov 2026; decision G24)
- **Decision G24** recorded. `sidra_realestate/cutover.py`, registered as a `before_request` hook: a signed-in Sidra staff member who opens a Desk page (`/desk`, `/app`) is sent to the matching Berjaya page with a temporary redirect (302): a bookmarked record lands on the same record (`/desk/sidra-unit/U-1` → `/berjaya/properties/U-1`), anything else on the Berjaya front page.
- Users with System Manager, Accounts Manager, Accounts User, Auditor or Sidra Finance Reviewer keep Desk, for system administration and the ERPNext ledger and its reports. Administrator, guests and non-staff users are not affected.
- Only Desk page requests (GET) are redirected. API calls, private files, print views, sign-in and Berjaya are untouched; Desk itself is not changed or removed.
- The registration screen's "Open in Desk" button is removed.
- Tests: `tests/test_cutover.py` (5 integration tests: staff sent to Berjaya, records landing on the same record, administrators and finance keeping Desk, only Desk pages redirected, non-staff and guests left alone). Checked over HTTP against a running local site: a sales user's `/desk`, `/desk/sidra-unit` and `/app/sidra-sale-contract/<name>` answer 302 to the Berjaya pages; a finance user's answer 200 from Desk; API calls answer 200 for both.

### Added (v0.1.33 — attachments, comments and map locations in Berjaya, 14 Nov 2026; decision G23, step 5a)
- **Attachments and comments** on every record page Berjaya serves (Desk's sidebar and timeline): the record's files, with those belonging to a form field marked; **Attach a file** (private) and **Remove** for users who may write the record (a field's file changes only through the form); comments, newest first, shown as plain text, which anyone who may read the record can add, as in Desk. Server: `sidra_realestate/api/record_extras.py` (`get_extras`, `add_comment`, `remove_attachment`); uploads use Frappe's `upload_file`, which checks write permission on the record.
- **Map location** on unit and construction job pages, through the existing `api/locations.py`: the recorded point, **Google Maps** and **Google Earth** links, **KML** download, and **Set location** by latitude and longitude or **Use my current position** (the device's GPS), for users who may write the record; the version check and the "point, not surveyed boundaries" note as before. Desk's tile map is not rebuilt.
- Tests: `api/test_record_extras.py` (4 integration tests: comments open to readers and stored escaped, attachments listed and removed only with write permission, field files kept to their form, only records the interface serves). Full app suite on a fresh Frappe v16 / ERPNext v16 site: 392 integration tests and 105 engine tests pass. Browser walk-through against a real local site at 1440px and 390px, 3 steps, all PASS: a manager sets a unit's location (map links and KML appear), comments, attaches a file and removes it; a sales user sees and adds comments but cannot attach or move the pin.

### Added (v0.1.32 — Berjaya setup: contract profiles, clauses, contract settings, contract import, 14 Nov 2026; decision G23, step 4)
- New **Setup** section in Berjaya (for users who may read it): **contract profiles** and **contract clauses** (lists, record pages, create and edit; the General Manager writes them as before), **contract settings** (the single record's form; read-only for everyone else), and **contract imports** (create, Validate, then Import).
- Desk's form notes appear on the record and its form: a profile's installments and the reminder that penalty, refund and title terms are recorded only; a clause's warning until both the Somali and English wording are supplied; the import's date formats with **Download template**.
- **Validate** is offered once a file is attached and **Import** only after a successful Validate, as in Desk; the result and the import's log are shown on the page. Rules audit R2 (the server does not itself require a prior Validate) is unchanged and still open.
- **Files can be attached on a new record's form.** The upload is a private, unattached file of the user's own; Frappe attaches it to the record when the record is saved with it (`attach_files_to_document`). The "save first, then attach" step is gone for KYC scans, signed copies, evidence files and the import spreadsheet (which is required to create an import).
- The form engine handles single records (no row to lock; the version check still applies; never deleted).
- Tests: `api/test_forms_setup.py` (4 integration tests: a profile by the General Manager with its note and refused for a Sales Manager; a clause warning until both languages are supplied; Contract Settings saved, stale edits refused, read-only for a Sales User; an import created with a file uploaded on the new form, attached by Frappe, validated and imported). Full app suite on a fresh Frappe v16 / ERPNext v16 site: 388 integration tests and 105 engine tests pass. Browser walk-through against a real local site: the setup run (4 steps) at 1440px and 390px, and the earlier runs again with files attached before creating (forms 8, sales 6, construction 4 steps), all PASS.

### Added (v0.1.31 — Berjaya forms for construction, 14 Nov 2026; decision G23, step 3)
- The form engine now serves **construction jobs** (create and edit, with their stages and BOQ), **construction quotations** (create, edit, issue; the client's acceptance recorded after issue), **BOQ revisions**, **variation orders** and **inspection reports** (create, edit, submit and cancel as each DocType allows; the controllers keep G11's second-person rules).
- Desk's job buttons in Berjaya: **New quotation / BOQ revision / variation order / inspection report** open that form with the job filled in, under the same conditions as Desk (a variation only once the job has a contract; nothing on a closed job); **Certify stage** asks which completed stage, for the Project Manager. On a quotation, **Approve contract** for the General Manager once the client's acceptance is recorded.
- Fields that a DocType lets change after submission (a construction quotation's client acceptance) can be edited on a submitted record; nothing else can. A job's BOQ is read-only once an approved revision controls it, as in Desk.
- A new record opened from another one is filled from the link (e.g. `?job=SCJ-…`), for fields the form lets the user set. Select fields can show labels for their values (the stage to certify).
- Construction list: **New job** in Berjaya; job pages show Saved after a save and drop the "Open in Desk" link. A "Saved." note is cleared when a later action runs.
- Tests: `api/test_forms_construction.py` (4 integration tests: a job with stages offering its records and refusing to "run" a link, Certify stage with its choices and roles, quotation acceptance after issue with the price kept and Approve contract by the General Manager, the BOQ locked by an approved revision). Full app suite on a fresh Frappe v16 / ERPNext v16 site: 384 integration tests and 105 engine tests pass. Browser walk-through against a real local site at 1440px and 390px, 4 steps, all PASS: a job with two billing stages; a quotation opened from the job, issued, then the client acceptance with its signed file; the General Manager approves the contract and the job then offers a variation order; stage 1 completed and certified.

### Added (v0.1.30 — Berjaya forms for sales: price changes, quotations, contracts, title transfers, 14 Nov 2026; decision G23, step 2)
- The form engine now also serves **price changes** (Sidra Unit Price History: create and submit; the unit's price follows), **sale quotations** (create, edit, issue), **sale contracts** (cash and generated: create, edit, sign; cancel and delete where permitted) and **title transfers** (create and edit, final payment and handover details with their evidence files).
- Desk's buttons as actions, each offered only when Desk's own conditions hold and checked again by its method: **Approve discount** (a Sales Manager up to 5 %, the General Manager above; never the person who prepared it), **Revise draft** (opens the new draft), **Confirm final payment** (a second Sales Manager, not the one who entered it), **Confirm handover** (the General Manager).
- A registered (External) contract cannot be submitted through the general form: it is confirmed on its contract page, where the acknowledgement of a schedule difference is recorded (G22). Its page now also offers Cancel and Delete where permitted.
- Link suggestions use Desk's pickers as filters (units Available or Reserved on a quotation, active profiles without legal hold, confirmed contracts on a title transfer); the controllers still check every value.
- Contracts list: **New contract** (cash or generated, in Berjaya) beside **Register external contract**; the Desk links on contract pages and lists served by the engine are removed.
- Record pages reload in place after an action, so its result stays on screen.
- Tests: `api/test_forms_sales.py` (7 integration tests: price change submitted, discount approved by a second person and the quotation issued, the preparer not offered the approval, a cash contract drafted, signed and no longer revisable, Revise draft opening the new draft, a registered contract refused by the general submit, both title transfer confirmations by the right people). Full app suite on a fresh Frappe v16 / ERPNext v16 site: 380 integration tests and 105 engine tests pass. Browser walk-through against a real local site at 1440px and 390px, 6 steps, all PASS: price change submitted and shown on the unit; quotation with a units table and a discount, approved by a second manager and issued; cash contract with parties and the signed copy drafted by a sales user (who cannot sign) and signed by a manager; title transfer final payment entered by one manager and confirmed by another.

### Added (v0.1.29 — Berjaya record forms: customers, KYC, units, schemes, reservations, 14 Nov 2026; decision G23, step 1)
- **Decision G23** recorded: Berjaya fully replaces Desk for Sidra's business records and actions; everything else is frozen.
- **Form engine** `sidra_realestate/api/forms.py`: `get_form`, `save_form`, `submit_form`, `cancel_form`, `delete_form`, `run_action`. The server describes each form from the DocType (sections, labels, types, options, help text, required marks, and the show / read-only / mandatory rules) and says which fields this user may change; every write goes through the record's own controller.
  - Only fields the form allows can be written; anything else is refused, not ignored (rules audit R7). A field that is read-only by its DocType rule for the values as they will be saved keeps its value (e.g. a unit's cash price after creation, which changes only through price history).
  - Stale edits are refused (each change carries the version the user loaded); a create carries a request key, so a retry makes one record; submit, cancel and delete repeated after they succeeded change nothing.
  - Actions are the existing server methods (`reserve_unit`, `cancel_reservation`, `verify_kyc`), offered only when Desk's own conditions hold for this user and record; each method checks its roles and state again. Desk's warning before reserving a unit without a positive price is kept (rules audit R3).
  - Served now: Customer (the fields staff use; phone and email on creation, which ERPNext turns into the primary contact), Sidra Customer KYC, Sidra Unit, Sidra Scheme, and Sidra Reservation (actions only: reservations are made and cancelled through the unit).
- **Field rules without running code** (`services/form_rules.py`): Frappe evaluates `depends_on` rules only in Desk's browser code. Each rule is parsed once into a small tree that the server and the browser evaluate the same way; nothing is executed. A pure test checks that every rule in the app is understood; a rule that is not understood makes its field read-only.
- **Screens**: New and Edit pages for every served list (`pages/RecordEdit.vue`, `components/RecordForm.vue`, `components/FormField.vue`: text, numbers, money, dates, selects, links with Frappe's own permission-checked search, checks, tables with rows, and file uploads to the record's field as private files). Record pages gain Edit, Submit, Cancel, Delete and the record's actions, each confirmed on the page (`components/RecordActions.vue`). Lists the engine serves create in Berjaya instead of Desk.
- **Units** get a record page at `/berjaya/properties/<unit>` (unit, plot and house details, its reservations and price history) and a New unit button; **Schemes** get a list and record page under Properties.
- Record pages show "—" for a field that is empty and "Unavailable" only for one the user may not read (Frappe's REST answer leaves empty fields out, so the form's values decide).
- Tests: `api/test_forms.py` (14 integration tests: form description, refused fields, read-only rule on the server, stale edits, permissions, request keys, create-only fields, delete permission, submit/cancel only for submittable types, reserve and cancel, the price warning, KYC verify), `services/tests/test_engine_form_rules.py` (7 pure tests), `frontend/tests/forms.test.mjs` (6 tests: the same rules in the browser, what a save sends). Full app suite on a fresh Frappe v16 / ERPNext v16 site: 373 integration tests and 105 engine tests pass. Browser walk-through against a real local site at 1440px and 390px, 8 steps, all PASS: a manager creates a scheme and a unit (company filled by the server), edits it (price read-only); a sales user reserves and cancels; a sales user creates a customer and a KYC and attaches the scanned ID; a manager verifies it; a sales user cannot open New unit.

### Added (v0.1.28 — additional dashboard cards and charts)
- Four operational cards for open/completed jobs, posted receipts and collection rate, using the existing permission-checked dashboard response.
- Scheduled amounts by due window and operational exception charts, with visible exact values and unavailable states.
- Risk/exposure cards and a needs-attention list linked to server-provided supporting records. Existing dashboard sections and company/period filters remain.
- Frontend tests and isolated browser checks at desktop and phone widths; no backend rule, permission or posting changes.

### Added (v0.1.27 — registration completed in Berjaya: terms, parties, Fill schedule, Print, 14 Nov 2026; implementation plan Phase 4)
- The registration screen now covers everything Desk did for a registered (External) contract, so a registration needs no Desk step:
  - **Agent and notary**: buyer's agent and phone, notary and notary reference (D5: recorded where the contract has them).
  - **Penalty, default and title terms** (D6, G2, G9), as the signed contract states them; recorded only, nothing is applied. A field appears only when it applies (e.g. Amount per Day only for "Per Day Capped"), by the rule in the DocType.
  - **Seller, guarantor and witnesses**: role, name, phone, ID number, and the pledged property for a guarantor. The controller's party rules apply at confirmation as in Desk.
  - **Fill schedule from saved terms** (CC-06): proposes rows from the saved price, installments, due day and dates; asks before replacing existing rows; disabled while there are unsaved changes.
- **Print** on the contract page opens Frappe's print view with the contract's own print format (Sidra branding, G19).
- `api/contract_registration.py`: the screen may now also set the term, signing and party fields (anything else is still refused); new `fill_registration_schedule` (stale-edit check and row lock, then the controller's `propose_schedule`) and `get_registration_form` (labels, types, options and a plain "shown when" rule read from the DocType, so the wording lives in one place; a rule it cannot read means the field is always shown). Term, signing and party fields are sent only when that form loaded, so a failed load cannot blank them.
- Tests: 19 integration tests in `api/test_contract_registration.py` (5 new); 25 frontend unit tests (4 new). Local Frappe v16.55.2 / ERPNext v16.53.0 bench: on a fresh site the full app suite passes with this change once v0.1.26 (demo test order) is in; CI is the check. Browser walk-through against that site at 1440px and 390px, 10 steps, all PASS, including terms shown by rule and kept after reload, a witness, Fill schedule with the replace prompt, and the print view.

### Fixed (v0.1.26 — the finance demo and pilot dataset tests always run in the same order, 14 Nov 2026)
- The finance demo test checks absolute totals for Sidra Homes, and its loader refuses a Company holding ledger entries it does not own, so it must run before the pilot dataset is loaded. The two were separate modules, and Frappe discovers test files in file-system order (`os.walk`, unsorted), which differs between machines: whenever the pilot ran first, the finance demo test failed (`180 != 60` units). This made CI fail at random, about half the time (seen on PR #60; PR #59 passed by luck).
- Both now run from one module, `tests/test_demo_datasets.py`, as two classes that unittest loads in name order (`TestDemo1Finance`, then `TestDemo2Pilot`), each with its own test transaction as before. The test bodies are unchanged; `test_finance_demo.py` and `test_pilot_demo.py` now hold them as `FinanceDemoChecks` and `PilotDemoChecks`, and the pilot's `_foreign_gl_refused` is renamed `_pilot_foreign_gl_refused` so the two do not clash. `test_order` guards the class names.
- Reproduced on a fresh Frappe v16 / ERPNext v16 site (pilot first: the same failure). With the fix, the full app suite passes on a fresh site: 354 integration tests and 98 engine tests.

### Added (v0.1.25 — register an External contract in Berjaya, 14 Nov 2026; implementation plan Phase 4)
- **Register external contract** at `/berjaya/contracts/new` and **Edit draft** at `/berjaya/contracts/<name>/edit`: customer, company, external reference, signing date, agreed price, profile, down payment mode and amount, installments, due day, grace months, terms summary, units with allocated prices, and the schedule row by row (type, due date, amount). Only a draft registered (External) installment contract can be edited here; penalty, default, title and party terms stay in Desk.
- **Original signed contract**: uploaded as a private file to the draft's Signed Copy field through Frappe's own upload, then set on the contract by the server after checking the file belongs to this contract only.
- **Confirm contract** on the contract page, shown only when the workflow timeline lists `confirm_contract` for the user and no stage is blocked. The Sidra Sales Manager's confirmation is the approval of the terms (D7); units become Under Contract, as in Desk. Nothing is posted to the ledger (`CLAUDE.md` rule 3).
- `sidra_realestate/api/contract_registration.py`: `save_registration_draft`, `attach_registration_copy`, `confirm_registration`. Every rule stays in the Sidra Sale Contract controller; the module only limits which fields the screen may set (rules audit R7: anything else is refused, not ignored) and adds what a second screen needs:
  - **Stale edits refused**: each change carries the `modified` value the user loaded; a change made since by someone else is named and nothing is written.
  - **Row lock** before the check and the write, so two confirmations of one draft cannot both run.
  - **Safe retries**: a create carries a request key (a retry returns the same draft); a confirmation repeated by the same user after it succeeded returns the same result and changes nothing.
  - **Schedule difference within the tolerance must be acknowledged** (rules audit R1), and the acknowledgement is recorded on the contract as a comment naming the user and the amount. Above the tolerance the controller refuses as before. Approved by Mohamoud as **decision G22** (14 Nov 2026), recorded in `docs/DECISIONS-AND-GATES_v0.1.md`; Desk keeps its own dialog unchanged.
- Totals on the edit screen are the server's, as last saved; the browser adds nothing up.
- New code follows the interim module rule of implementation plan v0.2 within the repository's existing layout: contract logic in `frontend/src/registration.js` beside `contracts.js`, the page in `pages/`, the server module in `api/`. No existing file was moved.
- **Edit draft** on the contract page appears when the server says the user may write the draft (`frappe.client.get_doc_permissions`) or the timeline lists an edit action; **Confirm contract** only when the timeline lists `confirm_contract` and no stage is blocked.
- Tests: `api/test_contract_registration.py` (14 integration tests: allowed fields, stale edits, request keys, permissions, signed copy ownership, confirmation, repeat, acknowledgement, no ledger effect); 8 new frontend unit tests (`frontend/tests/registration.test.mjs`, 21 in all). Run on a local Frappe v16.55.2 / ERPNext v16.53.0 bench: **the full app suite, 353 integration tests, passes**, plus the 98 engine tests. A browser walk-through against that real site (not synthetic answers), at 1440px and 390px: a sales user registers a draft, sees the server's refusal for a zero amount, attaches the signed copy and cannot confirm; a sales manager acknowledges a USD 3.00 difference and confirms; the timeline shows 6 of 6; the confirmed contract can no longer be edited. GitHub Actions is still not running.

### Added (v0.1.24 — Berjaya is the staff front page; Dashboard; Sales, Customers, Construction work, Titles and prices, 14 Nov 2026; decision G21)
- **Decision G21** recorded: staff land on `/berjaya` after signing in; `/sidra` and `/sidra-staff/` redirect there (302); ERPNext Desk stays for creating and editing until each Berjaya screen can; the Dashboard shows the old `/sidra-staff/` figures.
- **Sign-in lands on Berjaya**: the apps-screen entry (and so System Settings "Default App") now routes to `/berjaya`. `/sidra` sends staff to `/berjaya`, guests to sign in and others to Desk; `/sidra-staff/` sends staff to `/berjaya`. Codex's staff client files are not touched.
- **Dashboard** at `/berjaya/dashboard` (and the home page): from `get_dashboard`, unchanged. Units available, active reservations, contracts and agreed value for the period, new leads; management metrics and six-month trend for roles with executive reporting; properties by status; installments falling due; latest contracts; construction; payments; sales activity. A group the role cannot read shows the server's reason.
- **New sections**, read-only, each list and record page following the user's server permissions:
  - Customers: customers (with their KYC, reservations, quotations, contracts, title transfers and construction jobs) and KYC.
  - Sales: reservations and sale quotations (units and schedule).
  - Contracts: title transfers beside contracts.
  - Properties: unit price history beside units.
  - Construction: quotations, BOQ revisions, variation orders and inspection reports beside jobs.
- **Desk for editing**: every record page has "Open in Desk"; lists show "New in Desk" only when the server says the user may create. Record links now use `/desk/…`.
- `/berjaya` boot adds `lists` (read and create per list, computed on the server). Navigation follows the lists a user may read.
- Tests: `test_berjaya_page` (list permissions from the server), `test_shell` and `test_staff_page` (old pages redirect with 302), `test_branding` (landing route); 13 frontend unit tests; browser check of 18 screens at 1440px and 390px plus a role without KYC access. Integration suite not run here (no database; GitHub Actions refused for billing).

### Fixed (v0.1.23 — sign-in redirects are temporary, 14 Nov 2026)
- `/berjaya`, `/sidra` and `/sidra-staff/` sent a signed-out visitor to the sign-in page with Frappe's default **301 (permanent)** redirect. Browsers remember a permanent redirect, so after signing in a user could be sent back to the sign-in page instead of the screen. They now use **302 (temporary)**, because the answer depends on the session. Seen on the test server's deploy check on 14 Nov 2026. `test_berjaya_page` asserts the 302.

### Added (v0.1.22 — test server deploy script for Berjaya, 14 Nov 2026)
- **`deploy/berjaya-deploy_v0.1.sh`**: one script for the test server. `deploy` takes a backup with files first (nothing else runs if it fails), fast-forwards the app to `develop` (local changes or a diverged branch stop it), installs the frontend packages from the lockfile, runs `bench build --app sidra_realestate --force` and proves the Berjaya files are new, migrates, clears caches, restarts and checks. `check` changes nothing. `brand` sets the Berjaya logo and name in Website, Navbar and System Settings when an earlier hand-made value keeps the old logo on the sign-in page. `rollback <commit>` moves the code back after typed confirmation and prints, but never runs, the database restore.
- Checks are reported as PASS / FAIL / NOT VERIFIED: latest `develop`, built interface, processes running, sign-in page loads the Berjaya stylesheet and wordmark, assets served, `/berjaya` sends a signed-out visitor to sign in, and the timeline of `SSC-2026-00055` (saved as JSON, with the contract's `modified` unchanged by the call).
- Dry-run against a stand-in server (real git remote; bench, yarn, curl and supervisor stand-ins): deploy, failed check, `brand`, uncommitted changes, failed backup, refused and confirmed rollback, redeploy after rollback. Not yet run on the real test server.

### Added (v0.1.21 — Berjaya screens: Contracts, Collections, Construction, Finance; branded sign-in, 14 Nov 2026; decisions G17, G20)
- **Contracts** at `/berjaya/contracts`: saved sale contracts with reference, customer, property, source and status; search by reference or customer. **Contract detail** at `/berjaya/contracts/<name>` (read-only): buyer, property, signed agreement, amounts, installment schedule with its saved total.
- **Workflow panel** in the right-hand slot, fed only by `sidra_realestate.api.workflow.get_contract_timeline`: completed, current, blocked and pending stages by icon, words and colour; an unverified buyer on a registered contract is drawn as "Not verified - informational" and is not counted in "N of M stages complete"; a blocked stage shows the server's reason verbatim; evidence the user may not read says "Unavailable"; a contract with no workflow shows the server's reason. It reloads when the window regains focus and from Refresh. The Workflow button appears only on a page that has a panel.
- **Collections** at `/berjaya/collections`: one calendar month of installments from confirmed contracts (`get_installment_calendar`), with the server's totals and its notice. A passed date is labelled "Date passed", never "overdue": payments against installments are not recorded yet.
- **Construction** at `/berjaya/construction` and `/berjaya/construction/<name>`: saved construction jobs, and one job with its contract values, dates and stage rows.
- **Finance** at `/berjaya/finance`: the server's ledger position for the period (`get_dashboard` → payments) or its reason when the Finance gate is closed, and the submitted Sales Invoices and receipts the user may read.
- Every screen is read-only and reads saved records through Frappe's permission-checked API. No total is added up in the browser; a figure the server withholds reads "Unavailable". No demo or in-memory data.
- **Sign-in page** in the Berjaya look (charcoal ground, terracotta action) through `public/css/berjaya-login.css`, loaded by `web_include_css` and scoped to the login page only; Frappe's page is not edited. The wordmark, app icon and favicon are redrawn in the decided colours with the same mark as the `/berjaya` navigation (file names unchanged).
- Tests: 13 frontend unit tests (`yarn test` in `frontend/`), a browser check of every screen at 1440px and 390px against synthetic answers (`frontend/tests/browser.py`), one integration test for the sign-in stylesheet. GitHub Actions is not running (billing), so checks were run locally; the bench integration suite was not run for this version.
- Based on Codex's contract screen work (branch `feature/berjaya-contract-screen`), brought up to `develop` and completed.

### Added (v0.1.20 — Berjaya interface shell at `/berjaya`, 13 Nov 2026; decisions G17, G20)
- **`/berjaya`**: the new interface, a Vue 3 + Vite + Frappe UI app in `frontend/`, served by `www/berjaya.py`; `website_route_rules` sends every path under `/berjaya` to it. Existing Frappe session only: Guests go to the login page and come back to the page they asked for; signed-in people who are not Sidra staff are refused. No tokens, nothing in local storage.
- **Shell**: charcoal navigation (collapsible; a drawer on phones) with the product wordmark at the top and the user's Company at the bottom; a flexible workspace; a right panel slot (a drawer below 1100px), empty until the workflow panel is built. Colours and fonts are defined once in `frontend/src/tokens.css`; Space Grotesk and Inter are bundled, not fetched.
- **Navigation follows the server**: `www/berjaya.py` lists the sections the user may read (Properties: Sidra Unit; Contracts and Collections: Sidra Sale Contract; Construction: Sidra Construction Job; Finance: GL Entry, as on `/sidra`). The frontend decides no permission.
- **Properties**: a read-only list of units and their count from Frappe's REST API, with loading, empty, error and unavailable states. A field the server does not list as readable for the user reads "Unavailable", never zero. No demo or in-memory data; a failed request shows the failure. Other sections read "Not built yet".
- **Build**: `bench build --app sidra_realestate` now also builds the frontend through the root `package.json` (or `yarn install --frozen-lockfile && yarn build` at the repository root). The output, `public/berjaya/` and `www/berjaya.html`, is not committed.
- Tests: `api/test_berjaya_page.py` — Guest redirect, outsider refused, navigation for two roles against their permissions, readable unit fields, the route rule, the built page rendering with its boot data.
- **Unchanged**: every DocType, field, permission, guard, loader and posting gate; `/sidra` and `/sidra-staff/`. No migration. Known gap: `Sidra Unit.cash_price` is not a restricted field today, so every role that reads units sees it.

### Added (v0.1.19 — workflow timeline API for registered contracts, 13 Nov 2026; decisions G17, G20)
- **`sidra_realestate.api.workflow.get_contract_timeline(contract)`**: one whitelisted, read-only method that returns the ordered stages of registering an External contract for the workflow panel of the new interface. Every state is derived from saved records on each call; nothing is stored and nothing is written.
- Six stages, with the evidence approved by Mohamoud on 13 Nov 2026: buyer details verified (Sidra Customer KYC; informational for registered contracts under G12, never blocking), property allocation checked (re-derived from the units), external agreement attached (the contract's own private signed-copy File), installment schedule validated (D1 down payment mode, D3 tolerance; a confirmed contract keeps the tolerance frozen in its snapshot), terms approval by the Sales Manager (D7), registration finalized (submitted, external reference reserved).
- Each stage is `completed`, `current`, `blocked` or `pending`; exactly one is current or blocked unless all are completed. A blocked stage carries the reason in words, with both amounts when the schedule does not reconcile.
- Read permission on the contract is enforced. `allowed_actions` is computed for the signed-in user. KYC evidence is returned as unavailable to users who cannot read KYC; no contract amount is restricted today, and a figure a user may not read would be returned as unavailable, never zero.
- Stage lists are defined in one place (`PROCESSES`) so collections and construction can add theirs. Generated and Cash contracts report that no workflow is defined yet.
- No DocType, field, permission, hook, guard or posting gate is changed. `api/test_workflow.py`: 21 integration tests.

### Changed (v0.1.18 — Berjaya product name on the existing screens, 13 Nov 2026; decisions G17–G20)
- **Decisions recorded** in `docs/DECISIONS-AND-GATES_v0.1.md`: G17 (interface rebuild), G18 (product name **Berjaya**), G19 (**Sidra** stays the client and company name), G20 (rollout: `/berjaya`, charcoal and terracotta, rebrand first). `CLAUDE.md` and `AGENTS.md` carry the same naming rule.
- **Branding audit** (`docs/BERJAYA-BRANDING-AUDIT_v0.1.md`): 2,128 "sidra" lines classified — 11 product, 176 client, 1,883 internal, 58 unsure. Approved by Mohamoud on 13 Nov 2026.
- **Rules audit** (`docs/BERJAYA-RULES-AUDIT_v0.1.md`): every rule held in Desk form scripts or field conditions, with its server check. Document only; no rule moved.
- **Surfaces rebranded**: the app name on the apps screen, the system and website name (browser tab titles, login page, website footer), the `/sidra` front page title and header, the `/sidra-staff/` page title and sidebar brand, the README title and the app description. The name comes from one constant, `sidra_realestate.branding.BRAND_NAME`.
- A plain text wordmark and letter icon (`berjaya-wordmark.png`, `berjaya-icon.png`, `berjaya-favicon.png`) replace the company logo as the software's navbar logo, splash and favicon. Colours are unchanged.
- A site this app had branded "Sidra Homes" is rebranded on migrate: only that exact earlier value in System, Website and Navbar Settings is replaced. An administrator's own value is still left alone.
- **Unchanged**: Company **Sidra Homes** and every record in it; the Sidra Homes logo and letterhead on the contract and quotation prints; app, module, site, flag, DocType, role and report names; naming series; the routes `/sidra` and `/sidra-staff/`; the Desk sidebar names; the native Android and macOS apps; every guard, loader, posting gate and permission. No patch, no data migration.
- Tests: product-name source, hooks and apps-screen tile; the login page context and the front page carry Berjaya; earlier branding replaced; Company list and name unchanged by branding; contract print and a Sidra Homes sales invoice print carry no product name.

### Fixed (v0.1.17 — staff dashboard pilot sources and installment calendar, 13 Nov 2026)
- Read opted-in native financial data from either the twelve-month pilot manifest, the earlier finance demo manifest, or both. Preserve complete permission-filtered invoice/payment cohorts, currency checks and ownership validation; no grants, postings or loader calls.
- Remove the two historical demo Companies from the staff dashboard selector and prefer Sidra Homes, without changing any Company or historical record.
- Add a complete, permission-filtered monthly installment endpoint and responsive Calendar/List views with month navigation, day selection, search, date filters and exact server schedule cards. Scheduled obligations and past dates remain explicitly unreconciled; posted receipts and overdue invoice balances use their separate native sources.
- Show open construction jobs including enquiries and a status breakdown; replace the unconnected project-baseline headline with recorded overdue milestones, preserving the unavailable baseline API field. Label the existing stage-percentage average explicitly.


### Added (v0.1.15 — twelve-month pilot demonstration dataset, 13 Nov 2026; decision G16; `docs/PILOT-DEMO_v0.1.md`)
- **`sidra_realestate.pilot_demo.create_pilot_demo_data`**: one guarded, manual loader that fills the existing Company **Sidra Homes** with twelve months of fictional movement, so a client demonstration opens onto populated records in every module instead of empty screens.
  - Property: 4 schemes, 120 units across Plot / House / Apartment, ready and off-plan, with 20 submitted price reviews scheduled ahead.
  - Sales: 40 buyers with KYC (4 left unverified so the contract gate is visible), 60 quotations across Draft / Issued / Expired with discounts above and below the 5 % limit, 25 reservations created through the Reserve Unit service, 45 contracts — Cash and Installment, generated and externally registered, 3 left draft — and 20 title transfers spread across their states.
  - Installments: a schedule on every installment contract at 12, 18, 24 or 36 months; the rounding lands on the final row so the schedule equals the balance exactly.
  - Construction: 25 jobs across all four service types and six statuses, each with a BOQ, five stages and billing percentages totalling 100; a draft quotation per job past Enquiry and addition-only variation orders.
  - Finance: about 160 vouchers over twelve months — opening capital, 60 sales invoices, 35 purchase invoices and their payments — paid, part paid and open in equal thirds so AR ageing has more than one bucket.
- **Every G14 guard is kept and none relaxed**: Administrator only, all three staging flags, a private ownership manifest (`sidra-pilot-demo-v1.json`), the no-foreign-GL guard as the first read before any insert, one transaction with full rollback, reserved-identity refusals, and a rerun that verifies and writes nothing.
- The pilot and finance demo manifests are read together, so the two datasets coexist in Sidra Homes and each still refuses ledger rows neither owns.
- `services/pilot_dataset.py`: the dataset plan as pure, seeded logic with `test_engine_pilot_dataset.py` — counts, dates, schedule arithmetic and the balance-sheet identity are asserted before anything is posted. Frappe integration tests cover the guards, the rollback, the foreign-GL refusal, module coverage and the rerun.
- `docs/PILOT-DEMO_v0.1.md`, `docs/DECISIONS-AND-GATES_v0.1.md`: G16. `CLAUDE.md` and `AGENTS.md` name the pilot dataset in the scoped exception.
- Known gap: **Sidra Brokerage has no DocTypes**, so it is not populated and its sidebar section stays empty. Inspection Reports are not created — the DocType needs an inspector User the loader does not make.
- Production posting gates, refunds, penalties and title transfer are unchanged; ERPNext remains the only ledger.

### Added (v0.1.14 — one front page for staff, decision G15, 13 Nov 2026; `docs/SHELL_v0.1.md`)
- `/sidra`: a single front page with four doors (Executive Dashboard, Financials, Real Estate Sales, Construction). Each service shows its workflow as numbered steps with counts, items waiting for action, and New buttons. Doors, steps and buttons follow the user's permissions; a step the user can't read is left out, not shown as zero.
- Staff land on it after signing in: the app's apps-screen route is `/sidra` (desk route `/desk/sidra-sale-contract`) and System Settings Default App is set to this app when blank.
- Read-only and server-rendered: no new HTTP API, no posting, not cached. The staff dashboard is unchanged and linked from the page.
- `api/test_shell.py`: Frappe integration tests. `docs/DECISIONS-AND-GATES_v0.1.md`: G15.

### Changed (v0.1.13 — sample data under Sidra Homes on the test site, decision G14, 13 Nov 2026)
- Decision G14 recorded in `docs/DECISIONS-AND-GATES_v0.1.md`; `docs/FINANCE-DEMO_v0.2.md` replaces v0.1 (kept, marked superseded); `CLAUDE.md`, `AGENTS.md`, `docs/DEPLOYMENT_v0.1.md` and `docs/STAFF-DEMO_v0.1.md` name Sidra Homes.
- Finance demo loader posts the same ten vouchers (237,000 / 237,000) into the existing Company **Sidra Homes**, named in one constant. It never creates or edits the Company; demo accounts sit under marked `Fictional Demo Accounts` groups; identities are `SHD`, so the v0.1 `SFD` records and both old demo Companies are untouched.
- New no-foreign-GL guard: before the first insert, refuse a Company holding any GL entry the private manifest does not own, naming the count and first vouchers; refuse on a missing, duplicated or unreadable manifest. Also run by `verify_finance_demo`.
- Staff dashboard demo finance adapter and `demo_reporting.populate_and_verify` follow the same constant to Sidra Homes.
- Tests: finance demo tests retargeted; new tests for the guard (refusal, count in the message, nothing written), the missing Company, the unreadable manifest, and the count and checksum of 60 existing units before and after a load.
- `deploy/sidra-homes-verify_v0.2.sh`: test-site runbook and read-only verification sweep. `deploy/sidra-homes-run_v0.1.sh`: one script that backs up, fast-forwards the app to `develop`, rebuilds, restarts and then runs it.

### Added (v0.1.12 — sale quotation, P1, 12 Nov 2026; decision G13; `docs/SALE-QUOTATION_v0.1.md`)
- **Sidra Sale Quotation** (SAL-05): an offer for one or more units showing the cash option and the installment option side by side, printed on Sidra letterhead (print format *Sidra Sale Quotation*).
  - Cash option: the unit's listed price, or lower as a discount.
  - Installment option: a price entered per unit, never below the listed price; terms from a contract profile, with the number of months adjustable from 12 to 36; an indicative schedule.
  - Discounts need a second person before the quotation is issued: a Sales Manager up to 5 % of the unit's listed price, the General Manager above. Changing a price clears the approval.
  - Valid 7 days unless changed; a daily job marks issued quotations Expired.
  - Offer only: no reservation, no unit change, no contract and no posting.
- Real Estate sidebar link for Sale Quotations.
- `services/quotation.py`: pure rules with `test_engine_quotation.py`. The 5 % limit, the month range and the valid days are constants that change only with an approved spec. Frappe integration tests.
- `docs/DECISIONS-AND-GATES_v0.1.md`: G13.

### Fixed (v0.1.11 — staff sample figures, 12 Nov 2026)
- Staff Sales shows permission-filtered recorded lead statuses for the selected Company and period. Qualification/conversion remain unset.
- Add a single staging finance-demo population script with ledger and staff-source checks and correctly scoped report links.

### Added (v0.1.10 — buyer KYC and title transfer tracker, P1, 12 Nov 2026; decision G12; `docs/KYC-AND-TITLE_v0.1.md`)
- **Sidra Customer KYC** (SAL-07): one restricted record per Customer with ID or passport, phone, address, guarantor details and private scans. Sales Users enter it and a Sales Manager verifies it; the General Manager reads. No other role has access. Changing a verified record returns it to Draft.
- **Contract gate:** a contract generated from a profile can't be submitted until the buyer has verified KYC. Registered (external) contracts don't need it.
- **Sidra Title Transfer** (SAL-08, SAL-18):
  - one record per unit of a confirmed contract, with documents required, land office submission, deed number and handover;
  - the final payment date is entered with private evidence and confirmed by a second Sales Manager; the deadline is the contract's frozen title deadline days after it;
  - status is Due Soon from 5 days before the deadline and Overdue after it, with days past the deadline; a daily job keeps it current;
  - the General Manager confirms the handover, after which the record is locked;
  - record only: no change to the unit, the contract or ownership, and no late-title amount.
- Real Estate sidebar links for Title Transfers and Customer KYC; Title connection on the sale contract.
- `services/title.py`: pure deadline rules with `test_engine_title.py`. `services/files.py`: the shared private-file check. Frappe integration tests for both DocTypes and the contract gate.
- The demo loader gives its fictional buyers verified KYC so generated demo contracts can still be confirmed.
- `docs/DECISIONS-AND-GATES_v0.1.md`: G12.

### Added (v0.1.9 — construction controls, P1, 12 Nov 2026; decision G11; `docs/CONSTRUCTION-CONTROLS_v0.2.md`)
- **Sidra Construction Quotation** (CON-02, CON-03):
  - priced from a frozen copy of the job's BOQ, or as a fixed fee; printed on Sidra letterhead (print format *Sidra Construction Quotation*);
  - the Project Manager issues it; it can't be issued if the BOQ has changed since the draft or the quotation has expired; issuing moves the job to Quoted;
  - the client's acceptance is recorded with a private signed file;
  - **Approve Contract** is for the General Manager only. It sets the job's original contract value, start, duration, end and retention (0–10 %, period in months), and the job becomes Contracted. Stage Billing % must add up to exactly 100.
- **Sidra BOQ Revision** (CON-02 revisions): the Project Manager approves; revisions are numbered and copy their lines to the job. Stale drafts and revisions that change nothing are refused. Never cancelled. The job's BOQ changes only through a new revision.
- **Sidra Variation Order** (CON-06):
  - additions only, with the client's approval recorded (who, when, private signed file);
  - a second person approves: another Project Manager up to $1,000, the General Manager above $1,000, and cancelling follows the same rule;
  - the job must have an approved contract.
- **Sidra Inspection Report** (CON-05): date, inspector, stage, checklist results, overall result, defects, next action and due date, private photos. Consistency checks apply. The Inspector approves.
- **Stage certification** (CON-04): **Certify Stage** for the Project Manager on Completed, 100 %, ended stages. A certified stage is frozen and can't be removed. Not an invoice or revenue.
- **Sidra Construction Job:**
  - contract section, read-only and set only by Approve Contract;
  - Approved Variations and Current Contract Value;
  - Milestone Amount per stage (current value × Billing %; adds up to the value exactly);
  - Billing % locked after the contract;
  - Approved BOQ Revision;
  - Create buttons, Connections and Construction sidebar links.
- `services/construction.py`: pure rules with `test_engine_construction.py`. The $1,000 limit and 10 % retention ceiling are constants that change only with an approved spec. Frappe integration tests for each new DocType, contract approval and certification.
- `docs/DECISIONS-AND-GATES_v0.1.md`: G11.
- Recorded only: no invoice, Sales Order amendment or posting (`CLAUDE.md` rule 3).

### Security (v0.1.8 — ERPNext hardening, 12 Nov 2026)

- Bind contract-import spreadsheets to their own private File attachment and enforce File read permission before parsing.
- Enforce Customer access on reservations and linked-unit access on cancellation; reject malformed durations and nonfinite spreadsheet amounts before writes.
- Add regression tests, a read-only administrative site-security audit, and repeatable secret/Bandit CI checks. See `docs/SECURITY-REVIEW_v0.1.md` for findings and outstanding deployment verification; no AI runtime is bundled or added.

### Changed (v0.1.7 — Somaliland regional settings, 12 Nov 2026)
- Sidra settings, demo Companies and native setup presets use Somaliland. Create its Country master before assigning links; retain USD, DD/MM/YYYY and Africa/Mogadishu.
- Migration updates existing site defaults, Company/Address country links, the native territory and address template. Existing contracts, vouchers and customer identities are preserved. Other country selections and the upstream country catalogue remain available.

### Fixed (v0.1.6 — Desk usability)
- Consistent sidebar ownership, construction/collections/report links and count-chart formatting.
- Scheme connections and permission-filtered counts, clearer identifiers, unit list columns and house-only fields.
- Staff-facing labels without requirement codes, readable schedule columns, map fallback and import template download.
- Missing asking prices are explicit; no prices, signed terms, legal wording or financial rules are invented.


### Fixed (v0.1.5 — staff dashboard review fixes, 12 Nov 2026)
- Sidra Project Manager and Sidra Inspector no longer get a permission error on the staff dashboard: unit, contract, reservation and schedule groups their role cannot read are returned as null/empty (unknown, not zero).
- Staff dashboard money is summed as exact decimals; a missing or invalid amount makes the total null instead of being counted as zero.
- The schedule bucket "Next 30 days" now covers tomorrow through day 30, the same window as the executive `due_next_30_days`; rows due today have a separate "Due today" bucket.
- Overdue milestones use the shared `stage_overdue` rule (no actual end, completion below 100, active/on-hold jobs only), consistent with the executive stage exceptions.
- Open spec questions, not changed here: the two contract-value totals and the construction progress % (GitHub issues labelled `spec-question`).

### Added (v0.1.4 — collections rules as profile settings, decision G9, issue #3, 12 Nov 2026)
- Sidra Contract Profile: eleven new settings for the rules the installment engine had to assume: days before a per-day penalty starts, cap basis, whether payment on the last notice day is late, what a receipt pays first, how a payment beyond what is due is allocated, days before an installment counts as missed, what "one installment" means for the refund, whether penalties paid are in the refund base, and Profile B's title part month, refund-right start and compensation base
- The same settings on Sidra Sale Contract: frozen from the profile on generated contracts, prefilled and editable on registered (External) contracts, kept in the terms snapshot (INS-20). Stored only; nothing is applied (`CLAUDE.md` rule 3)
- Profiles A and B seeded with the engine's assumptions (AT-06 to AT-13); title rules the engine left open are "Pending Decision". Patch `v0_4.set_collection_rule_defaults` fills only blank settings on existing profiles; contracts are not changed
- `docs/DECISIONS-AND-GATES_v0.1.md`: G9 (issue #3) and G10 (issue #8: bilingual clauses, wording supplied by Sidra)

### Added (v0.1.3 — isolated fictional financial data, 9 Nov 2026)
- Administrator-only, staging-opt-in finance demo loader: a separate fictional Company, six demo accounts, ten submitted native ERPNext vouchers, private ownership manifest, read-only balance verification and repeat protection. Never adopts an existing Company, duplicates vouchers or changes production posting rules.
- Native GL, Trial Balance, P&L, Balance Sheet and receivable/payable reports can show real posted fictional data. Demo-only dashboard receipts/aging read permission-filtered native records and explicitly label invoice arrears separately from contract schedules.
- Reuses external contract registration with a private fictional original and three installments, available plots, leads and one recorded milestone exception. No contract document generation or construction module expansion.

### Added (v0.1.2 — read-only executive dashboard, 8 Nov 2026)
- Codex takes over the remaining dashboard backend/client implementation and tests end to end under the user's updated allocation; financial/legal gates are unchanged.
- Management-only executive snapshot on the existing staff endpoint: permission-filtered signed sales and trends, available units/verified asking prices, gross scheduled rows tomorrow through day 30, current stage date exceptions, expired active reservations and registration-age exposure. Reuses the reviewed Insights source definitions without installing another app or executing unrestricted parent SQL.
- Native **Sidra Executive Detail** Script Report provides independently authorized source rows and parent links; Company/Unit User Permissions, role restrictions, date/currency consistency, whole-contract exclusions and stale-date/project rejection are enforced server-side. No financial records or workflow states are changed.
- Gross schedules are labelled separately from unpaid balances/forecast cash. Unavailable receipt/allocation, target and approved-baseline sources remain unavailable. Reporting periods have exact inclusive 30/90-day windows in Africa/Mogadishu; signed sales and operational schedule aggregates exclude future-signed/foreign-currency contracts.

### Added (staff clients backend: locations, dashboard and staff page)
- `/sidra-staff/` (`www/sidra-staff/`): Codex's staff UI on the site's own origin for signed-in Sidra staff (guests go to login), session CSRF token injected per request into `window.SIDRA_CONFIG`, not cached; UI files published at `/assets/sidra_realestate/staff/` through the `public/staff` link to `clients/staff/web`
- `sidra_realestate/api/staff_dashboard.py`: `get_dashboard` (schema_version 1 of API-CONTRACT.md), permission-filtered through `frappe.get_list`, one Company and currency, money as decimal strings; payments and sales pipeline returned as unavailable with a reason (no receipts in ERPNext yet; no lead stages), scheduled amounts labelled as obligations; jobs from recorded stages only
- `sidra_realestate/api/locations.py` and `location_geometry.py`: Codex's plot / site location adapter, reviewed and integrated (`get_location`, `set_location` with stale-edit refusal, `export_kml`); `sidra_location` Geolocation field added to Sidra Unit and Sidra Construction Job (existing GPS text kept); integration tests with real Sidra roles

### Added (sample migration data and brokerage spec)
- `docs/samples/SAMPLE-LIVE-CONTRACTS_v0.1.csv` (also `/assets/sidra_realestate/templates/sample_live_contracts.csv`): 8 synthetic live contracts, 182 schedule rows (12 to 36 months, both down-payment modes, a fee row, a two-plot contract); the demo adds free plots DEMO-M-001 to 009 for it, and `tests/test_demo.py` imports it
- `docs/BROKERAGE_v0.1.md`: draft spec for approval: Sidra as broker for owners' plots and agent commission on Sidra's sales, 2.5 % of the plot price, due in full on the buyer's first payment, recorded not posted; acceptance tests BR-01 to BR-10

### Changed (docs)
- `docs/DEPLOYMENT_v0.1.md`: test VPS status, lessons from the first deployment (IPv6, private home folders and nginx, default site, tmux, deploy key), D4 and contract capture patches, Module Profile for staff

### Added (import capability, decision G5)
- **Sidra Contract Import** (Real Estate → Contract Import): upload a CSV or XLSX of live contracts, one row per schedule line; **Validate** runs every contract check and keeps nothing; **Import** creates draft registered contracts, all or nothing; references already registered for the Company are skipped; optional creation of missing customers. Template: `public/templates/sidra_contract_import_template.csv`. Payments to date are not imported (D8)
- `services/contract_import.py` (pure reader: DD/MM/YYYY and ISO dates, row-numbered errors) with pure tests

### Added (white-label and navigation, Mohamoud 7 Nov 2026)
- Sidra Homes branding: system and website name, navbar logo, favicon, login splash, website footer; contract print and README carry the official Sidra Homes logo (`sidra_realestate/branding.py`; `public/images/sidra-logo.png`, `sidra-icon.png`, `favicon.png`)
- One "Sidra Homes" app on the apps screen and rail with two sections from shipped Dock / Sidebar records: **Real Estate** (schemes, plots, reservations, price history, sale contracts, profiles, clauses, contract settings, customers) and **Construction** (construction jobs, customers)
- Module Profile "Sidra Staff" hides Manufacturing, Stock, Projects, Buying, Quality, Support, Assets, Subcontracting and Maintenance for staff (hidden, not deleted); demo users get it

### Added (contract capture: docs/CONTRACT-CAPTURE_v0.3.md, decisions D1–D7, issue #13)
- Register contracts prepared outside the system: `Sidra Sale Contract.source` (External (registered), the default, or Generated from profile), external reference unique per Company among confirmed contracts (transaction-safe key), original signed contract attachment, captured terms, terms summary
- Actual schedules entered row by row (Installment / Down payment / Fee, same-day and past dates allowed); Fill Schedule (`propose_schedule`) proposes rows only when asked and replaces only after confirmation
- Reconciliation: schedule total, amount due and difference (D1 down payment mode, D2 fee rows); confirmation within the Contract Settings tolerance ($5.00, D3) after acknowledgement, stored in the snapshot
- D5: External confirmation needs only the original document and validates signing data where present; Generated contracts keep the full gate
- D6: penalty, default and title terms captured on the contract (profile range checks reused), frozen at confirmation, never applied
- D7: `terms_approved_by` / `terms_approved_on` and the same in the snapshot
- `Sidra Contract Settings` (schedule tolerance); print shows "Registered copy of an external contract" and row types
- Patch `v0_3.set_contract_source`: existing installment contracts become Generated, rows typed Installment, totals back-filled

### Added (decisions of 7 Nov 2026)
- `docs/DECISIONS-AND-GATES_v0.1.md`: G1 configurable installment terms (12–36 months and between), G2 penalties as a waiting period plus an amount, G3 no Murabaha, G4 ERPNext as the only ledger, G5 import capability now and migration later, G6 merge on green CI, G7 Codex continues when Claude Code's limit is reached, G8 zip removed
- `AGENTS.md` for Codex, pointing to `CLAUDE.md`

### Removed
- `sidra-erp_v0.1.0.zip`, committed by mistake

### Changed (decision D4, issue #13: code)
- Profile B is seeded with a 20-day title deadline and no legal hold (`install.py`); the 14 days in Contract B is a typo
- Patch `v0_3.resolve_profile_b_title_deadline`: on existing sites, changes Profile B only while it still has the seeded hold values (legal hold on, deadline 0), sets 20 days, lifts the hold and adds a Comment citing issue #13; a profile already edited by management is left alone. Saved contracts keep their frozen terms (INS-20)
- Tests: the legal-hold mechanism is now tested on a held copy of Profile B (`tests.helpers.make_held_profile`); new tests for the D4 seed, the patch (seeded, edited, run twice) and a Profile B contract submitting with the AT-03 schedule

### Changed (decision D4, issue #13)
- `CLAUDE.md` rule 3 and `docs/SREMS-SRS_v2.0-DRAFT.md` (§1.4, §3.3 Profile B, §9 item 1) record that Contract B's title deadline is 20 days and that Profile B's legal hold is lifted only through the D4 seed / patch; rule 3 also records D7 for registered contracts
- Roles: Claude Code implements, including the contract capture brief; the Codex role and Task 0 in `docs/CONTRACT-CAPTURE_v0.3.md` are superseded (Mohamoud, 7 Nov 2026) Docs only: the seed and patch in `docs/CONTRACT-CAPTURE_v0.3.md` are not part of this change

### Fixed (ChatGPT review of develop @ cbce4f3)
- Signed copy: must be a private file attached to this contract's Signed Copy field, on disk, readable by the submitter and used by no other record; a pasted or re-used file URL is refused
- Lock order: units are locked first (ascending name), then reservations, in reserve, cancel, expiry and contract submit
- Notary reference: whitespace removed; `notary_reference_key` with a database unique index is set at submit, so concurrent submissions cannot share a reference; drafts may share one
- Unit scheme moves: refused across Companies when the unit has reservations, contracts or price history, and refused entirely once on a signed contract
- Clause approval is checked against the library at submit; changed wording needs Revise Draft (docs/CONTRACT-REVISION_v0.1.md, issue #11); signed snapshots never change
- Money fields named "USD" as a currency field, so amounts showed in the site default currency (INR on a bare site); they now use the Company's currency
- Profile B's legal hold is reported before missing signing data

### Added
- Reserve Unit and Cancel Reservation actions on the unit form, Cancel Reservation on the reservation form, Revise Draft on draft contracts
- Role profiles pairing each Sidra role with the ERPNext role its screens need (sales staff could not look up a Customer with Sidra roles alone)
- `site_setup.apply_regional_settings` (NFR-10: USD, DD/MM/YYYY, Africa/Mogadishu)
- `demo.create_demo_data` / `demo.export_pdfs` for private staging (guarded by `sidra_allow_demo_data`)
- Contract print format uses the Chrome PDF generator; real PDF output tested
- Patches `v0_2.set_notary_reference_keys`, `v0_2.set_document_currency`
- docs/DEPLOYMENT_v0.1.md, docs/CONTRACT-REVISION_v0.1.md; traceability CSV gains implementation status, PR and test evidence columns

### Added
- `docs/SREMS-SRS_v2.0-DRAFT.md` — ERPNext implementation specification from ChatGPT; working spec from 5 Nov 2026, with a repository note (repo `sidra-erp`, app `sidra_realestate`)
- `docs/REQUIREMENTS-TRACEABILITY_v2.0-DRAFT.csv` — requirement ID to phase and status map
- `docs/CLAUDE-CODE-HANDOFF_v2.0.md` — implementation handoff, first-PR checklist, subsequent PRs, PR template
- `docs/ENVIRONMENT_v0.1.md` — pinned versions: Frappe v16.55.2, ERPNext v16.53.0, Python 3.14, Node 24, MariaDB 11.8
- `.github/pull_request_template.md` — the handoff's PR template

- P0 prototype (SRS v2.0 §4): 10 DocTypes — Sidra Scheme, Sidra Unit, Sidra Reservation, Sidra Contract Profile, Sidra Contract Unit, Sidra Sale Contract, Sidra Installment Line, Sidra Construction Job, Sidra Project Stage, Sidra BOQ Line
- `services/reservations.py`: `reserve_unit` / `cancel_reservation` (row-locked, Sales roles only) and the daily `expire_reservations` job
- `services/schedule.py`: pure-Python installment generator (whole-dollar rounding, last installment absorbs the rest, grace months, due day 1–28)
- Profile A and Profile B created on install and migrate when missing; Profile B on legal hold (14 vs 20-day title deadline)
- Roles fixture: Sidra Sales User, Sales Manager, Project Manager, Inspector, Finance Reviewer, General Manager
- Integration tests for every DocType, including concurrent reservation; pure tests for the schedule (AT-01 to AT-04)
- CI job that builds an ERPNext v16 bench (Frappe v16.55.2, ERPNext v16.53.0, MariaDB 11.8), installs, migrates, builds and runs the tests

- Unit price history (SAL-02): submittable `Sidra Unit Price History`; new prices must take effect after the latest one; only future-dated entries can be cancelled; `Sidra Unit.cash_price` mirrors today's price and is refreshed daily; a unit created or imported with a price gets an "Initial price" entry
- Bulk import (SAL-01): Data Import enabled for Sidra Scheme, Sidra Unit and Sidra Unit Price History (Sales Manager)
- Patch `v0_2.create_initial_unit_prices`: back-fills history for units priced before this change

- Contract parties (SAL-19): child table Sidra Contract Party (Seller, Seller Guarantor with pledged property, Witness) on Sidra Sale Contract
- Clause library (SAL-20): Sidra Contract Clause with Somali and English wording, approved only by the General Manager; profiles list their clauses; a contract freezes them with its terms (INS-20, INS-21). Five clauses seeded with no wording and not attached to any profile (issue #8)
- Signed-copy gate: a contract submits only with a private signed copy, notary name and unique reference, one Seller, a Seller Guarantor with pledged property, two Witnesses with phones and approved wording for every clause
- Print format "Sidra Sale Contract" (default): units with boundaries, price, schedule, clauses in Somali and English, parties with signature lines, notary

### Changed
- `reserve_unit`, `cancel_reservation` and price entries now enforce per-Company user permissions on the unit
- `CLAUDE.md` points at SRS v2.0-DRAFT and adds the P0 prototype boundary (no postings, refunds, penalties, title transfer or overrides; Profile B legal hold)

## [0.1.1] — 2026-11-05

### Added
- `docs/HANDOVER_v1.0.md` — handover to Claude Code: roles (ChatGPT architecture / QA, Claude Code implementation), rules, fixed decisions, contract profiles A / B, phase plan, acceptance cases AT-01 to AT-13, first tasks
- `CLAUDE.md` — standing instructions loaded by Claude Code

### Changed
- Roadmap follows the agreed phase order: Foundation, Property, Sales, Collections, Construction, Finance, Release

## [0.1.0] — 2026-11-05

### Added
- Frappe app skeleton for ERPNext v16: `hooks.py`, `modules.txt`, `patches.txt`, `pyproject.toml`
- Five modules: Sidra Property, Sidra Sales, Sidra Installments, Sidra Construction, Sidra Brokerage
- `docs/SREMS-SRS_v1.6.md` — requirements specification v1.6
- `docs/ERPNEXT-MAPPING_v0.1.md` — mapping of every requirement to ERPNext standard features or custom DocTypes
- GitHub Actions CI: ruff lint and Python syntax check

