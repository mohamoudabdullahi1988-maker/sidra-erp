# Staff record tools v0.1

15 Nov 2026 · v0.1.58 · issue #96 and interface parity follow-up.

Claude’s dashboard dates and module submenus are integrated from v0.1.57. This change adds Contact/Address forms, Lead Company/contact preferences, Customer primary Contact/Address links, contact-app links, Print/PDF, native document assignments/due dates and tracked field changes. Version history requires DocType change tracking and write permission. Assignments require document write permission and use Frappe's native service. Email/WhatsApp buttons only open the user's app; inbox sync is not provided. Contact/Address party-link child rows still require fuller Dynamic Link support.

Retired demo Company choices are hidden without deleting records. Unapproved construction contract values show unknown rather than zero. Claude's existing approval loader is preserved; this PR does not run it or approve more documents.

Remaining audit work: workflow access on all transaction pages, personal tasks/notification queue, native email conversations, sharing, complete linked-record views, general filters/saved views and exports/imports, selected bulk controls, duplicate/amend where permitted, report catalogue, and global search. Finance and admin remain in Desk; Architecture/Civil and Brokerage decisions remain pending.

Transaction lists, generic details/edit forms, construction jobs, properties, contracts, collections and finance now offer the Workflow panel with a clearly labelled process guide and permission-filtered transaction links. Sale Contract detail keeps its actual six-stage timeline. The guide does not claim completion or invent a new approval state.

My work (`/berjaya/my-work`) lists up to 100 personal open ToDos and notifications. Only the allocated user can complete a task or mark their notification read. Linked task descriptions are omitted when the reference record is no longer readable. List filtering/sorting runs on the server; saved view settings stay on the browser. General export/import, bulk actions and email threads remain outstanding.
