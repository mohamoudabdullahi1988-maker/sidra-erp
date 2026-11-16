# Berjaya Conversations and Discovery v0.1

16 November 2026. Scope assigned to this Codex chat: email conversations, global search,
report catalogue, richer history. Other interface work remains on the other chat's branch.

Email on saved business records uses native Communication, configured Email Accounts and
Frappe's outgoing queue. Compose, reply, CC, private uploads and selection of existing record
attachments are supported. Linked incoming messages and native delivery status are displayed.
An incoming account must already be configured and messages linked to the record to appear.
No new mailbox ingestion or mail server is introduced. No real messages are sent by tests.
Native email permission is checked; foreign-record attachments and reply references are refused.
HTML email is rendered as plain text. Opted-out Leads cannot be emailed here.

Search is available in the top bar across the form engine's business record types, with more
results per type. It searches IDs and readable text/link fields, respects record/User Permissions,
and opens the existing Berjaya record screen. It does not index attachment contents.

Reports is available in the left navigation. Operational reports expose readable scalar fields
of business records, selected columns and comparison filters, paginated rows and record links.
Native General Ledger, Accounts Receivable and Accounts Payable run through Frappe's report
engine and permissions. Their accounting document links retain the finance Desk exception G24.
Other custom/native report definitions are not automatically imported into the catalogue.
CSV export rechecks report/export permissions and reruns exactly the selected filters; exports
above 10,000 rows are refused with instructions to narrow filters, never silently truncated.
Spreadsheet formula prefixes are escaped. No new ledger, totals, posting or business policy.

The activity timeline pages through retained comments (including native workflow/assignment
comments), Communications, attachments, versions, milestones, tracked views and record creation/last update. Version detail retains
its existing write-access requirement and removes fields outside the readable schema, including
child fields. Additions, removals and edits are shown. History cannot reconstruct changes made
before tracking was enabled or deleted source events. Email bodies remain in Conversations.

Validation: 63 frontend tests and 105 pure calculation tests pass; Ruff and frontend production
build pass. Integration coverage checks denial, search/report filters, exports, email routing and
foreign attachments, activity pagination and child-field redaction. Browser checks use synthetic
API responses only; live email delivery still depends on the server's account configuration.
