# Berjaya record operations v0.1

16 November 2026. Implements the requested record workflow, customer connection, bulk action,
duplicate/amend/rename, sharing and tag gaps under G17/G23. No posting, refund, penalty,
title ownership or approval policy changes.

## Record workflows

Saved business records show their current native status and document lifecycle. KYC,
quotations, BOQ revisions, variations, title trackers and construction jobs also show their
stored approval evidence. Job stage rows show recorded progress and certification. Each
milestone requires its own evidence; a later status never implies an earlier approval.
Unreadable evidence is unavailable. Registered installment contracts retain the existing
six-stage validation timeline. These panels refresh on record changes and manual refresh;
they do not create a parallel workflow or invent collections/accounting stages.

## Customer connections

Customer, Contact and Address detail pages show permitted native Dynamic Links. Link/unlink
requires write access to both endpoints and preserves links to other customers and parties.
Unlinking a primary clears that customer's primary pointer. A customer can create a Contact
or Address and link it in the same request. Primary selectors accept only records already
linked to that customer. The generic Contact/Address links table is read-only; these controls
provide the checked write path.

## Bulk operations

Generic record lists and the property, contract and construction lists support checkboxes,
selection of up to 50 loaded rows, and a review step. Refresh/filter changes clear selection.
Review obtains current versions and fields common to all selected forms. Confirmation checks
every record again. Updates use the existing form engine and document controllers. Assignments
use native ToDo, without notification. A denied, invalid or stale record fails the complete
request; Frappe rolls back its writes. Printing checks every record's print permission and
provides a combined preview for printing/PDF. Browser/network failures require refreshing
before retrying because the outcome may be unknown.

## Document actions

Duplicate opens an unsaved form and respects Hide Copy, create permissions, no-copy and
unique fields. Approval/signing evidence and attachments are omitted. Amend requires a
cancelled submittable document, amend/create access and an `amended_from` field. Only one
active amendment is allowed; the server sets its lineage. New records still pass the
document controller. Contracts keep their approved Revise Draft action instead of generic
copying of frozen terms. Rename respects Allow Rename, checks the loaded version and uses
native rename without merging.

## Sharing and tags

Record tools use native DocShare and Tag/Tag Link. Sharing needs share permission, is limited
to enabled staff users, and cannot grant write access the caller lacks. Grant and revoke
are explicit user actions; notifications are disabled. Tags need write permission, reject
empty/comma-separated input and serialize updates to the native tag list.

## Validation and rollout

- Pure tests: `python -m unittest discover -s sidra_realestate -p 'test_engine_*.py' -t .`
- Frontend: `cd frontend && npm test && npm run build`
- Browser: Vite on port 8080, then `python frontend/tests/record_operations_browser.py`.
  All API responses in that test are synthetic. CI runs it at desktop and phone sizes.
- Bench: `bench --site <test-site> run-tests --app sidra_realestate`, including
  `sidra_realestate.api.test_record_operations`.

No schema migration or data loader. Build the frontend as part of deployment. Reverting the
change removes these controls; native links, shares, tags and created documents remain.
Live-site UAT and printing against the installed letterhead are separate from mocked browser
verification. No production deployment is performed by this change.
