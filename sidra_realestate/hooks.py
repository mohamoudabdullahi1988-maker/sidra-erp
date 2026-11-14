# Underscore name: Frappe reads every public module attribute as a hook.
from sidra_realestate import branding as _branding

app_name = "sidra_realestate"
# Product name and wordmark come from branding.py only (decisions G17-G19).
app_title = _branding.BRAND_NAME
app_logo_url = _branding.LOGO
app_publisher = "Mohamoud Abdullahi Sheikh"
app_description = (
	"Berjaya: real estate on ERPNext for Sidra Homes - land and house sales, Murabaha / "
	"installment contracts, construction projects, brokerage"
)
app_email = "mohamoud.abdullahi1988@gmail.com"
app_license = "proprietary"

# ERPNext must be installed on the site before this app.
required_apps = ["erpnext"]

# ------------------------------------------------------------------
# Fixtures: roles from SRS v2.0 section 5. Contract profiles are created
# by install.py (only when missing), never overwritten on migrate.
# ------------------------------------------------------------------
fixtures = [
	{"dt": "Role", "filters": [["role_name", "like", "Sidra %"]]},
]

# White-label (sidra_realestate/branding.py): the product icon on the apps screen and rail,
# with the Real Estate and Construction sections from dock/ and sidebar/.
add_to_apps_screen = [
	{
		"name": app_name,
		"logo": _branding.APP_ICON,
		"title": _branding.BRAND_NAME,
		# The staff front page: the Berjaya interface (www/berjaya.py, decision G21; it replaces /sidra
		# of G15). With System Settings "Default App" set to this app (branding.py), staff land on it
		# after signing in.
		"route": "/berjaya",
		# The app's door back into the desk, shown under its icon on the apps screen.
		"desk_route": "/desk/sidra-sale-contract",
		"has_permission": "sidra_realestate.branding.has_app_permission",
		"sequence_id": 0,
	}
]

website_context = {
	"favicon": _branding.ICON,
	"splash_image": _branding.LOGO,
}

# Berjaya look for the sign-in pages (decision G20: charcoal and terracotta). The stylesheet is
# scoped to the login page, so other website pages are unchanged; Frappe's page is not edited.
web_include_css = ["/assets/sidra_realestate/css/berjaya-login.css"]

# The Berjaya interface (www/berjaya.py, frontend/): a single-page app, so every path under
# /berjaya is served by the one page and routed in the browser.
website_route_rules = [
	{"from_route": "/berjaya/<path:app_path>", "to_route": "berjaya"},
]

after_install = "sidra_realestate.install.after_install"
after_migrate = "sidra_realestate.install.after_migrate"

# ------------------------------------------------------------------
# Scheduled jobs
# ------------------------------------------------------------------
scheduler_events = {
	"daily": [
		"sidra_realestate.services.reservations.expire_reservations",
		"sidra_realestate.services.prices.refresh_current_prices",
		"sidra_realestate.sidra_sales.doctype.sidra_title_transfer.sidra_title_transfer.refresh_title_states",
		"sidra_realestate.sidra_sales.doctype.sidra_sale_quotation.sidra_sale_quotation.expire_quotations",
	],
}


# Scoped Desk presentation fixes, loaded without changing Frappe core.
app_include_js = ["/assets/sidra_realestate/js/desk_forms.js"]

# Decision G24: Sidra staff opening Desk are sent to Berjaya; administrators and finance keep Desk.
before_request = ["sidra_realestate.cutover.before_request"]
