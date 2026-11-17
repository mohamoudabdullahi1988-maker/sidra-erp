"""Email conversations use native Communications, Email Accounts and delivery queues."""

import html

import frappe
from frappe import _
from frappe.utils import cint, strip_html_tags

from sidra_realestate.api.record_extras import _record


def _plain(value):
	return html.unescape(strip_html_tags(value or ""))


def _communication(name, doctype, record):
	doc = frappe.get_doc("Communication", name)
	if (doc.reference_doctype, doc.reference_name) != (doctype, record):
		frappe.throw(_("This email belongs to another record"), frappe.PermissionError)
	doc.check_permission("read")
	return doc


@frappe.whitelist(methods=["GET"])
def messages(doctype, name, start=0):
	doc = _record(doctype, name)
	rows = frappe.get_list(
		"Communication",
		filters={"reference_doctype": doctype, "reference_name": name, "communication_medium": "Email"},
		fields=["name"],
		order_by="creation desc, name desc",
		start=max(0, cint(start)),
		page_length=21,
	)
	result = []
	for row in rows[:20]:
		comm = _communication(row.name, doctype, name)
		files = frappe.get_all(
			"File",
			filters={"attached_to_doctype": "Communication", "attached_to_name": comm.name},
			fields=["name", "file_name", "file_url"],
		)
		result.append(
			{
				"name": comm.name,
				"subject": comm.subject,
				"sender": comm.sender,
				"recipients": comm.recipients,
				"cc": comm.cc,
				"direction": comm.sent_or_received,
				"on": comm.creation,
				"content": _plain(comm.content),
				"status": comm.delivery_status,
				"attachments": [f for f in files if frappe.get_doc("File", f.name).has_permission("read")],
			}
		)
	return {"rows": result, "has_more": len(rows) > 20, "can_send": bool(doc.has_permission("email"))}


@frappe.whitelist(methods=["POST"])
def send(doctype, name, recipients, subject, content, cc=None, attachments=None, in_reply_to=None):
	from frappe.core.doctype.communication.email import make

	doc = _record(doctype, name, "email")
	if doc.get("unsubscribed") or doc.get("status") == "Do Not Contact":
		frappe.throw(_("This record has opted out of contact"))
	if not recipients or not (subject or "").strip() or not (content or "").strip():
		frappe.throw(_("Recipient, subject and message are required"))
	if len(content) > 100000 or len(subject) > 500:
		frappe.throw(_("Message is too long"))
	attachments = frappe.parse_json(attachments) if isinstance(attachments, str) else attachments
	attachments = attachments or []
	if not isinstance(attachments, list) or len(attachments) > 20:
		frappe.throw(_("Select up to 20 attached files"))
	for file in attachments:
		if not isinstance(file, str):
			frappe.throw(_("Choose an attached file"))
		attached = frappe.get_doc("File", file)
		attached.check_permission("read")
		if (attached.attached_to_doctype, attached.attached_to_name) != (doctype, name):
			frappe.throw(_("Only files attached to this record may be sent"), frappe.PermissionError)
	if in_reply_to:
		_communication(in_reply_to, doctype, name)
	return make(
		doctype=doctype,
		name=name,
		recipients=recipients,
		cc=cc,
		subject=subject,
		content=frappe.utils.escape_html(content).replace("\n", "<br>"),
		attachments=attachments,
		in_reply_to=in_reply_to,
		send_email=True,
	)
