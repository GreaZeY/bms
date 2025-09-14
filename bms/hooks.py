app_name = "bms"
app_title = "Billing Management System"
app_publisher = "me"
app_description = "same"
app_email = "bms@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "bms",
		"logo": "/assets/bms/images/bms.png",
		"title": "Billing Management System",
		"route": "/app/billing",
		# "has_permission": "bms.api.permission.has_app_permission"
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/bms/css/bms.css"
app_include_js = "/assets/bms/js/bms.js"

# include js, css files in header of web template
# web_include_css = "/assets/bms/css/bms.css"
# web_include_js = "/assets/bms/js/bms.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "bms/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"BMS Subscription": "billing_management_system/doctype/bms_subscription/bms_subscription.js",
	"BMS Payment": "billing_management_system/doctype/bms_payment/bms_payment.js",
	"BMS Invoice": "billing_management_system/doctype/bms_invoice/bms_invoice.js",
	"BMS Plan": "billing_management_system/doctype/bms_plan/bms_plan.js"
}

doctype_list_js = {
	"BMS Subscription": "billing_management_system/doctype/bms_subscription/bms_subscription_list.js",
	"BMS Payment": "billing_management_system/doctype/bms_payment/bms_payment_list.js",
	"BMS Plan": "billing_management_system/doctype/bms_plan/bms_plan_list.js"
}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "bms/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "bms.utils.jinja_methods",
# 	"filters": "bms.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "bms.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "bms.uninstall.before_uninstall"
# after_uninstall = "bms.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "bms.utils.before_app_install"
# after_app_install = "bms.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "bms.utils.before_app_uninstall"
# after_app_uninstall = "bms.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "bms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"BMS Subscription": "bms.billing_management_system.permissions.get_subscription_permission_query_conditions",
	"BMS Invoice": "bms.billing_management_system.permissions.get_invoice_permission_query_conditions",
	"BMS Payment": "bms.billing_management_system.permissions.get_payment_permission_query_conditions"
}

has_permission = {
	"BMS Subscription": "bms.billing_management_system.permissions.has_subscription_permission",
	"BMS Invoice": "bms.billing_management_system.permissions.has_invoice_permission",
	"BMS Payment": "bms.billing_management_system.permissions.has_payment_permission"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"bms.billing_management_system.tasks.daily_tasks"
	],
	"monthly": [
		"bms.billing_management_system.tasks.monthly_tasks"
	],
}

# Testing
# -------

# before_tests = "bms.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "bms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "bms.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["bms.utils.before_request"]
# after_request = ["bms.utils.after_request"]

# Job Events
# ----------
# before_job = ["bms.utils.before_job"]
# after_job = ["bms.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"bms.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
# fixtures = ["Workspace"]

