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

   If they don't exist yet, they come from the demo setup (`demo.py`); ask Claude for the exact command.
4. **Browser:** use one normal window and one private window, so two users are signed in at once. Laptop at 100% zoom.
5. **Rehearse once, end to end.** Every step below creates real test records on the test site; nothing is posted to the ledger.

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
   - The right-hand **Workflow** panel shows each stage turning green.

### B. Sell a plot (8 min, `demo.sales`, then `demo.manager`)

1. **CRM → Leads → New:** a walk-in buyer (fictional name). Save.
2. **CRM → Customers:** make the buyer a customer. Then **KYC → New**: the ID details, and the Sales Manager **verifies** them.
3. **Units:** open an available Masalaha Hagbad plot → **Reserve unit** → choose the customer, hold for 7 days.
   - The plot turns *Reserved* on the Inventory screen.
4. **Sales → Quotations → New:**
   - the plot, cash price or the 22-month plan;
   - submit it.
   - A discount above the Sales staff limit waits for **Approve discount** by the Sales Manager.
5. **Contracts → New contract** (from the profile): the buyer, the plot, the plan.
   - The terms are frozen from the profile.
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
   - **New inspection report** for the first stage;
   - **New variation order** (approved by another Project Manager up to $1,000, the General Manager above);
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
