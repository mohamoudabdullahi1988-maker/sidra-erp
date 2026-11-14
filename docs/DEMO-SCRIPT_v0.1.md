# Berjaya client demonstration: click path v0.1

15 Nov 2026 · for Mohamoud · about 25 minutes · laptop first, phone at the end. Built on `develop` at v0.1.37 (decision G25).

**One line to say before you start:** "Everything you see is Berjaya running on ERPNext. Today's figures are sample data, marked on every screen. After your go-ahead we connect each screen to your real records."

**Before the meeting**
- Deploy `develop` to the test server and sign in as a staff user.
- Open `/berjaya` once on the laptop and once on the phone, so the first load is quick.
- Laptop browser at full screen, zoom 100%. The workflow panel on the right opens by itself on a wide screen.

---

## 1. Executive overview (3 min)
**Click:** sign in. You land on **Executive**.

- **Figure tiles across the top:** group income, installments collected, construction portfolio, active projects, units available, overdue.
  - *Say:* "One page for the whole group. Every tile is a door."
- **Click "Active projects".** The list of seven projects opens. Click **Back**.
- **Income by business line chart:** stacked bars for real estate, construction, design and brokerage, with a running total.
- **Needs attention list:** click **"Sheikh Road Culverts is three weeks behind"**. It opens that project's milestones. Click **Back**.
- **Right-hand panel:** "How work flows at Sidra", with buttons to the real records.
  - Optional: show **Live dashboard (real records)**, then come back with **Executive** in the menu.

## 2. Construction, the main act (10 min)
**Click:** **Construction** in the menu. It opens on **Portfolio**.

- **Portfolio**
  - *Tiles:* Budget $14.6m, Committed, Forecast, Variance to budget, Paid to date.
  - *Map:* sites across Somaliland. Click a pin to open that project.
  - *Projects by phase donut:* click **Construction**. The list filters to four projects.
  - *Project health table:* scope, time, cost, quality and safety dots for each project.
  - *Gantt and cash flow:* "Where each project stands today, and money out, actual against forecast."
- **Schedule:** the Rayan Gardens milestone plan, and the delayed and at-risk milestones.
- **Cost & budget:** budget against spent against forecast by category, and monthly spend.
- **Variations:**
  - Click **Awaiting approval** in the donut. Three orders open.
  - In the panel, point at the rule: a second approval, another Project Manager up to $1,000 and the General Manager above that.
- **Quality & inspections:** pass, remarks and fail results; open defects by project.
- **Risk:** register by rating, with owners and pending decisions.
- **Stock & materials:** click **Below reorder level**. Four materials open, including cement. The Risk tab links it to the delayed shipments at Berbera port.
- **Subcontractors:** contract value, paid, and retention held.

*Say:* "This is where you run the sites: every number here will come from your BOQs, inspections and stores."

## 3. Real Estate Sales (5 min)
**Click:** **Real Estate Sales**.

- **Inventory**
  - Masalaha Hagbad plots at $14,300 full and $7,150 half, interest-free from $325 a month over 22 months. Also Rayan Gardens, Safa Housing and Berbera Townhouses.
  - Click **Available** in the donut. The available plots and units open.
- **Pipeline**
  - The funnel from lead to site visit, quotation, reservation and contract, and where leads come from.
  - **Diaspora buyer support:** remote viewings, remote signing and title deeds handed over, plus buyers by country.
- **Contracts & collections**
  - Scheduled against collected each month.
  - Click **90+ days** in the overdue donut to show the five late contracts.
  - The panel shows the contract steps through to title transfer.
- **Real records:** the **Contracts** and **Collections** buttons at the top open the working screens, with the real contract register and installment calendar.

## 4. Design & Engineering, and Brokerage (3 min)
- **Design & Engineering:** overview, then the **Architecture**, **Civil engineering** and **Inspection services** tabs. Each shows jobs by stage, fees per month and workload.
- **Brokerage:** listings by type and area, commission at 2.5%, and deals. The panel ends with title deed transfer once paid.

## 5. Finance and the phone (3 min)
- **Finance:** the native ERPNext figures from the twelve-month test dataset. This needs the pilot dataset loaded on the test site; check it before the meeting.
  - *Say:* "The ledger is ERPNext itself. Nothing is kept twice."
- **Phone:** open `/berjaya` on your phone.
  - Same screens; the tiles stack two across.
  - Tap the **menu** icon for the business lines and **Workflow** for the steps.

## Close
"This is the surface: every business line on one system, in your colours, on laptop and phone. With your go-ahead we connect each screen to live records, starting with construction."

---

**If something goes wrong**
- **A screen is blank:** reload. If it still fails, carry on from the menu; each screen stands alone.
- **The Workflow panel is closed:** click **Workflow** at the top right.
- **Someone asks whether a number is real:** "Sample data, marked on every screen. Your real figures go in after approval."
