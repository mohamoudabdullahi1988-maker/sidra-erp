# Berjaya client demonstration: click path v0.2

Tuesday 17 Nov 2026 · for Mohamoud · about 40 minutes · laptop, then phone. Built on `develop` at v0.1.42 or later. Replaces v0.1.

Order of the meeting:
1. **The picture:** sample dashboards.
2. **The proof:** live records on the same screens.
3. **The system working:**
   - capture a contract;
   - sell a plot;
   - start a construction project.

**Opening line:** "Berjaya is the system Sidra runs on, built on ERPNext. First the whole business at a glance with sample figures, then the same screens on real records, then we do real work in it."

---

## Before Tuesday (on the server, once)

1. **Deploy `develop`:** `bash /root/berjaya-deploy_v0.1.sh`
2. **Run the top-up of the test data.** It gives the projects their real names, adds map points, inspection reports, leads and opportunities, and changes nothing when run again:
   ```bash
   cd /home/frappe/sidra/frappe-bench
   sudo -u frappe bench --site sidra.local execute sidra_realestate.pilot_extras.create_pilot_extras
   ```
   It prints what it did. A second run prints `"created": false`.
3. **Demo users:** one per role, so approvals happen by a second person, as in real life. Set passwords with `bench --site sidra.local set-password <email> <password>`.

   | User | Role |
   |---|---|
   | `demo.sales@example.com` | Sales staff |
   | `demo.manager@example.com` | Sales Manager |
   | `demo.gm@example.com` | General Manager |
   | `demo.pm@example.com` | Project Manager |

   If they don't exist yet, create them with the role profiles they need. Nothing else changes, and no password is set:
   ```bash
   sudo -u frappe bench --site sidra.local execute sidra_realestate.demo.ensure_demo_users
   ```
   It prints the `set-password` commands to run. Details: `docs/DEMO-REHEARSAL-CHECKS_v0.1.md`.
4. **Browser:** use one normal window and one private window, so two users are signed in at once. Laptop at 100% zoom.
5. **Run the readiness check.** It reads only, and lists PASS, WARN or FAIL with the fix for each gap:
   ```bash
   sudo -u frappe bench --site sidra.local execute sidra_realestate.demo_readiness.check_demo_readiness
   ```
   It covers:
   - the interface;
   - the data, and the real project names;
   - a Masalaha Hagbad plot to sell;
   - an active contract profile and a verified buyer;
   - jobs, map points and inspections;
   - leads and opportunities;
   - each demo user's roles and password.
6. **Rehearse once, end to end.** Every step below creates real test records on the test site; nothing is posted to the ledger.

---

## 1. The picture: sample dashboards (6 min)

Sign in as `demo.gm`. You land on **Executive**.

- **Tiles and charts:** "Every Sidra business line on one page. These figures are samples, marked on every screen."
- **Drill-down:** click **Active projects**, then **Back**. Every tile and chart opens its list.
- **Construction:** click it in the menu.
  - Walk the tabs: Portfolio (map, health, Gantt, cash flow), Variations, Stock & materials.
  - "This is how you will run the sites."
- **Real Estate Sales → Inventory:** Masalaha Hagbad at $14,300 full and $7,150 half, from $325 a month over 22 months interest-free. Also Rayan Gardens, Safa Housing and Berbera Townhouses.

## 2. The proof: the same screens on real records (6 min)

- **Construction → Portfolio → Live records** (top of the screen):
  - the jobs in the system, with their real project sites on the map;
  - stages done, overdue stages, contract values;
  - click a job: its record opens.
- **Variations** and **Quality & inspections** tabs, still on **Live records**: real variation orders and inspection reports.
- **Real Estate Sales → Inventory → Live records:** every plot and unit by project and status.
- **Contracts & collections → Live records:**
  - real contracts;
  - the installments falling due over the next 12 months;
  - say: "amounts due; receipts come next."
- **CRM** in the menu: real leads and opportunities, with tabs for Customers, Contacts and KYC.

*Say:* "Same screens. Sample data shows what's possible; live records show what's in the system today."

## 3. The system working (20 min)

### A. Capture an existing contract (5 min, `demo.sales`, then `demo.manager`)

This is how Sidra's paper contracts come into the system.

1. **Contracts → Register external contract.**
   - Choose a customer and the plot.
   - Enter the contract reference, the date signed, the price, the down payment and the number of months.
2. **Fill schedule:** the installments are worked out from the terms, or entered as the contract states them.
3. **Add the parties, attach the signed copy, save.**
4. As `demo.manager` (private window), open the contract and **confirm** it: the Sales Manager's approval of its terms.
   - The right-hand **Workflow** panel shows each stage turning green. Only a registered (External) contract has this six-stage panel; a generated contract doesn't.

### B. Sell a plot (8 min, `demo.sales`, then `demo.manager`)

1. **CRM → Leads → New:** a walk-in buyer (fictional name). Save.
2. On the lead:
   - **Create opportunity**, optional: the interest in a project, an amount and the expected closing date.
   - **Make customer**: ERPNext's own lead-to-customer conversion. The customer appears under CRM → Customers.
   - Then **KYC → New**: the ID details, and `demo.manager` **verifies** them. A generated contract refuses an unverified buyer.
3. **Units:** open an available Masalaha Hagbad plot → **Reserve unit** → choose the customer, hold for 7 days.
   - The plot turns *Reserved* on the Inventory screen.
4. **Sales → Quotations → New:**
   - the plot and the cash price; submit it.
   - Any cash discount waits for **Approve discount**: the Sales Manager up to 5%, the General Manager above that. Installment prices can't be discounted below the listed price (G13).
5. **Contracts → New contract** (from the profile): the buyer, the plot and the profile.
   - The terms are frozen from the **profile**: Profile A gives 14 installments. The quotation's plan doesn't change them.
   - **Don't promise the 22-month plan here** unless an approved profile with those terms exists. Show it on the sample Inventory screen instead.
   - Attach the signed copy, then confirm as `demo.manager`.
   - The plot now shows *Under Contract*, and its installments appear on **Contracts & collections**.

### C. Start a construction project (7 min, `demo.pm`, then `demo.gm`)

1. **Construction → Jobs → New:**
   - the client, *Full Construction*, the plot and site;
   - the stages with their billing percentages, which must add up to 100.
   - Save.
2. On the job, **New quotation:** fixed fee or BOQ, the scope, start date, duration, retention. Issue it (submit).
3. **Record the client's acceptance** on the quotation: who accepted, the date, the signed acceptance.
4. As `demo.gm` (private window), open the quotation → **Approve contract**. The job gets its contract value, dates and retention.
5. Back on the job, as `demo.pm`:
   - **New inspection report** for the first stage. The Project Manager saves it as a **draft**; issuing it needs an Inspector. Present it as recorded, not approved.
   - **New variation order**. It needs a second person's approval: another Project Manager up to $1,000, the General Manager above. The demo has one Project Manager, so **`demo.gm` approves it** in the private window. The person who raised it can't approve it, so show that refusal first if you like.
   - **Certify stage** once a stage is complete.
6. **Construction → Portfolio → Live records:** the new job is there.

## 4. Finance and the phone (4 min)

- **Finance:** the overview (sample), then **Ledger and invoices (live)**. "ERPNext is the ledger; nothing is kept twice."
- **Phone:** open `/berjaya`. Same screens; **menu** for the business lines, **Workflow** for the steps.

## Close

"You've seen the whole business on one system, the screens on real records, and a contract, a sale and a construction project done in it. With your go-ahead we connect the remaining screens and bring in your live contracts."

---

**If something goes wrong**
- **A live screen says "No … recorded yet" or "Your role does not include …":** switch to **Sample data** and carry on. The screen tells the truth about what's in the system and what that user may see.
- **A step refuses to save:** read the message out. It is the system enforcing a rule (KYC not verified, schedule not matching the price, the same person approving their own request). That is a feature worth showing.
- **The Workflow panel is closed:** click **Workflow** at the top right.
- **Someone asks whether a number is real:** "Sample data is marked on every screen. **Live records** are what's in the system."
