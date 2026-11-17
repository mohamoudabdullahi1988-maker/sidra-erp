"""Record tools on desktop and phone, using explicitly synthetic API responses.

Run with Vite on port 8080: python frontend/tests/record_operations_browser.py
"""

import copy
import json
import shutil
from urllib.parse import parse_qs, unquote, urlparse

from playwright.sync_api import expect, sync_playwright

from browser import BOOT

BASE = "http://127.0.0.1:8080/berjaya"
FIELD = {"fieldname": "customer_name", "label": "Customer name", "fieldtype": "Data", "editable": True}


def main():
	with sync_playwright() as p:
		browser = p.chromium.launch(executable_path=shutil.which("chromium") or shutil.which("google-chrome"), headless=True, args=["--no-sandbox"])
		for width in (1440, 390):
			page = browser.new_page(viewport={"width": width, "height": 900})
			boot = copy.deepcopy(BOOT)
			for key in ("customers", "contacts", "addresses"):
				boot["lists"][key] = {"read": True, "create": True}
			page.add_init_script("window.berjaya_boot = " + json.dumps(boot))
			calls, errors = [], []
			page.on("pageerror", lambda e: errors.append(e.stack))
			tags, shares, connections = [], [], []
			docs = [{"name": f"SYN-{i}", "customer_name": f"Synthetic Buyer {i}", "modified": "2026-11-16", "docstatus": 0} for i in (1, 2)]

			def respond(route):
				req = route.request
				url = urlparse(req.url)
				path, query = unquote(url.path), parse_qs(url.query)
				args = req.post_data_json if req.method == "POST" else {k: v[0] for k, v in query.items()}
				method = path.rsplit(".", 1)[-1]
				body = {}
				if req.method == "POST":
					calls.append((method, args))
				if "/api/resource/" in path:
					parts = path.split("/")
					body = {"data": docs if len(parts) == 4 and parts[-1] == "Customer" else docs[0] if len(parts) > 4 else []}
				elif path.endswith("/count"):
					body = {"data": 2}
				elif method in ("get_form", "prepare_copy"):
					new = method == "prepare_copy" or not args.get("name")
					body = {"message": {"doctype": "Customer", "name": None if new else args["name"], "is_new": new,
						"modified": "2026-11-16", "values": docs[0], "layout": [{"label": "Customer", "fields": [FIELD]}],
						"permissions": {"write": True, "duplicate": True, "rename": True}, "actions": [], "notes": []}}
					if method == "prepare_copy":
						body["message"]["copy_source"] = {"name": args["name"], "operation": args["operation"], "modified": "2026-11-16"}
				elif method == "get_timeline":
					body = {"message": {"supported": True, "stages": [{"key": "saved", "label": "Record created", "state": "completed"}], "actions": []}}
				elif method == "get_connections":
					body = {"message": {"rows": connections, "can_write": True}}
				elif method == "link_customer":
					connections[:] = [{"doctype": args["doctype"], "name": args["name"], "primary": bool(args["primary"])}]
					body = {"message": {"name": args["name"]}}
				elif method == "get_tools":
					body = {"message": {"can_print": True, "can_assign": True, "can_share": True, "can_tag": True,
						"tags": tags, "shares": shares, "assignments": [], "versions": []}}
				elif method == "get_extras":
					body = {"message": {"attachments": [], "comments": [], "can_attach": True, "can_comment": True}}
				elif method == "set_tag":
					tags.append(args["tag"])
					body = {"message": {}}
				elif method == "set_share":
					shares.append({"user": args["user"], "write": args["write"]})
					body = {"message": {}}
				elif method == "bulk_options":
					body = {"message": {"records": [{"name": n, "modified": "2026-11-16"} for n in json.loads(args["names"])], "fields": [FIELD], "can_assign": True, "can_print": True}}
				elif method == "bulk_action":
					body = {"message": {"html": "<h1>Synthetic batch print</h1>"} if args["operation"] == "print" else {"names": [r["name"] for r in args["records"]]}}
				elif method == "save_copy":
					body = {"message": {"name": "SYN-2"}}
				elif method == "rename":
					docs[0]["name"] = args["new_name"]
					body = {"message": {"name": args["new_name"]}}
				elif method == "search_link":
					body = {"message": []}
				else:
					body = {"message": []}
				route.fulfill(json=body)

			page.route("**/api/**", respond)
			page.goto(BASE + "/customers")
			page.get_by_role("checkbox", name="Select SYN-1", exact=True).check()
			page.get_by_role("checkbox", name="Select SYN-2", exact=True).check()
			page.get_by_role("button", name="Review bulk actions").click()
			page.get_by_label("Bulk action", exact=True).select_option("update")
			page.get_by_label("Bulk field", exact=True).select_option("customer_name")
			page.get_by_label("Customer name", exact=True).fill("Synthetic updated")
			page.get_by_role("button", name="Confirm update", exact=True).click()
			expect(page.get_by_text("2 records updated.")).to_be_visible()
			assert next(a for m, a in calls if m == "bulk_action")["value"] == "Synthetic updated"
			page.get_by_role("button", name="Select loaded records (up to 50)").click()
			page.get_by_role("button", name="Review bulk actions").click()
			page.get_by_label("Bulk action", exact=True).select_option("print")
			page.get_by_role("button", name="Confirm print", exact=True).click()
			expect(page.frame_locator('iframe[title="Selected records print preview"]').get_by_text("Synthetic batch print")).to_be_visible()
			page.goto(BASE + "/customers/SYN-1")
			if width < 1100:
				page.get_by_role("button", name="Open workflow").click()
			expect(page.get_by_text("Record created", exact=True)).to_be_visible()
			if width < 1100:
				page.get_by_role("button", name="Close side panel").click()
			page.get_by_label("Link Contact", exact=True).fill("SYN-CONTACT")
			page.get_by_label("Make primary for customer").check()
			page.get_by_role("button", name="Link", exact=True).click()
			expect(page.get_by_text("· Primary", exact=True)).to_be_visible()
			page.get_by_label("New tag", exact=True).fill("Review")
			page.get_by_role("button", name="Add tag").click()
			expect(page.get_by_role("button", name="Remove tag Review")).to_be_visible()
			page.get_by_label("Share with", exact=True).fill("synthetic@example.test")
			page.get_by_role("button", name="Share", exact=True).click()
			expect(page.get_by_role("button", name="Remove access")).to_be_visible()
			page.get_by_role("button", name="Duplicate", exact=True).click()
			expect(page.get_by_role("heading", name="Duplicate SYN-1", exact=True)).to_be_visible()
			expect(page.get_by_label("Customer name", exact=True)).to_have_value("Synthetic Buyer 1")
			page.get_by_role("button", name="Create", exact=True).click()
			expect(page).to_have_url(BASE + "/customers/SYN-2?saved=1")
			page.goto(BASE + "/customers/SYN-1")
			page.get_by_role("button", name="Rename", exact=True).click()
			page.get_by_label("New name", exact=True).fill("SYN-RENAMED")
			page.get_by_role("button", name="Rename", exact=True).last.click()
			expect(page).to_have_url(BASE + "/customers/SYN-RENAMED")
			page.wait_for_load_state("networkidle")
			assert not errors, errors
			print(f"PASS {width}px bulk update/print, workflow, customer link, tags, sharing, duplicate and rename")
			page.unroute_all(behavior="wait")
			page.close()
		browser.close()


if __name__ == "__main__":
	main()
