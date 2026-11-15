# Staff record tools v0.1

15 Nov 2026 · v0.1.57 · issue #96 and interface parity follow-up.

Claude owns dashboard dates and module submenus. This change adds Contact/Address forms, Lead Company/contact preferences, Customer primary Contact/Address links, contact-app links, Print/PDF, native document assignments/due dates and tracked field changes. Version history requires DocType change tracking and write permission. Assignments require document write permission and use Frappe's native service. Email/WhatsApp buttons only open the user's app; inbox sync is not provided. Contact/Address party-link child rows still require fuller Dynamic Link support.

Retired demo Company choices are hidden without deleting records. Unapproved construction contract values show unknown rather than zero. Claude's existing approval loader is preserved; this PR does not run it or approve more documents.

Remaining audit work: workflow access on all transaction pages, personal tasks/notification queue, native email conversations, sharing, complete linked-record views, general filters/saved views and exports/imports, selected bulk controls, duplicate/amend where permitted, report catalogue, and global search. Finance and admin remain in Desk; Architecture/Civil and Brokerage decisions remain pending.
