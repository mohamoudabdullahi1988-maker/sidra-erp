# Berjaya rehearsal fixes v0.1

15 Nov 2026 · v0.1.56 · issue #96 · user feedback after v0.1.54–55.

The Company picker hides Sidra Demo Homes and Sidra Finance Demo - Fictional. Their records are retained. CRM opens a live dashboard and its transaction lists are in the sidebar. ERPNext v16 source fields are `utm_source`, backed by UTM Source; migration adds missing Email, WhatsApp, Phone, Website, Walk-in, Referral, Facebook and Instagram sources without editing existing ones. Source is an acquisition channel, not an inbox connection. Email/call/WhatsApp buttons open the user's app; messages are not automatically sent or synced. Do Not Contact suppresses them. WhatsApp requires an explicit international number.

Every transaction route offers Workflow. Lists/forms show a process guide and permission-filtered record/report links. Saved generic records show the server's status and available actions. This is not a newly invented stage-completion model; registered sale contracts keep their six-stage timeline. Architecture/Civil remain sample-only pending #100 and Brokerage pending #95.

## Demo approval, explicitly authorised by Mohamoud

The user requested approved quotations and authorised fictional demo acceptance so the demonstration has live values. This does not approve real transactions. The loader covers **pilot-owned construction quotations only**, including Design Only and Inspection Only jobs. Existing approved jobs are preserved. New quotations for owned jobs use their recorded BOQ, planned dates and zero retention; no price is guessed. Existing drafts keep their pricing and terms (expired drafts extend validity to 30 days from the run). Human-issued quotations, acceptance evidence and non-owned quotations cause refusal for manual review. Sales contracts, variations, inspection reports and financial vouchers are not bulk-approved.

Run after deploying v0.1.56, as root on the test server:

```bash
sudo -u frappe -H bash -lc 'cd /home/frappe/sidra/frappe-bench && bench --site sidra.local execute sidra_realestate.pilot_approvals.approve_pilot_quotations'
sudo -u frappe -H bash -lc 'cd /home/frappe/sidra/frappe-bench && bench --site sidra.local execute sidra_realestate.demo_readiness.check_demo_readiness'
```

Administrator, all three existing staging flags, the pilot ownership manifest and the existing no-foreign-GL guard are required. The loader uses normal submit and General Manager approval controls; no validation or guard is bypassed. Acceptance attachments explicitly say FICTIONAL DEMO and are private. A separate private manifest (`sidra-pilot-approvals-v1.json`) lists quotations, acceptance files and skipped already-contracted jobs. The original manifests are not changed. Failure rolls back the transaction; a rerun changes nothing.

Refresh Construction and Design Live records after the loader succeeds. Jobs move to Contracted and contract values equal their approved quotations. Before approval they show a dash, with the reason, not a false zero. Recorded stage completion remains unchanged. Check CRM Leads, the Source picker, both dashboard charts, submenus, and Workflow on lists/details/edit forms at laptop and phone widths.

Code deployment does not run this loader automatically. Server execution remains unverified until its output is returned.
