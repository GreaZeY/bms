import frappe
from frappe import _

def after_install():
	"""After install setup for BMS"""
	setup_roles()
	setup_permissions()
	create_sample_data()
	frappe.db.commit()

def setup_roles():
	"""Setup BMS roles"""
	# Create BMS Admin role
	if not frappe.db.exists("Role", "BMS Admin"):
		role = frappe.new_doc("Role")
		role.role_name = "BMS Admin"
		role.desk_access = 1
		role.save()
	
	# Create BMS User role
	if not frappe.db.exists("Role", "BMS User"):
		role = frappe.new_doc("Role")
		role.role_name = "BMS User"
		role.desk_access = 1
		role.save()

def setup_permissions():
	"""Setup default permissions"""
	# BMS Admin permissions
	admin_permissions = [
		{"doctype": "BMS Customer", "permlevel": 0, "role": "BMS Admin", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 0, "cancel": 0, "amend": 0, "report": 1, "export": 1, "import": 1, "print": 1, "email": 1, "share": 1},
		{"doctype": "BMS Plan", "permlevel": 0, "role": "BMS Admin", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 0, "cancel": 0, "amend": 0, "report": 1, "export": 1, "import": 1, "print": 1, "email": 1, "share": 1},
		{"doctype": "BMS Subscription", "permlevel": 0, "role": "BMS Admin", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 0, "cancel": 0, "amend": 0, "report": 1, "export": 1, "import": 1, "print": 1, "email": 1, "share": 1},
		{"doctype": "BMS Invoice", "permlevel": 0, "role": "BMS Admin", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 0, "cancel": 0, "amend": 0, "report": 1, "export": 1, "import": 1, "print": 1, "email": 1, "share": 1},
		{"doctype": "BMS Payment", "permlevel": 0, "role": "BMS Admin", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 0, "cancel": 0, "amend": 0, "report": 1, "export": 1, "import": 1, "print": 1, "email": 1, "share": 1},
	]
	
	# BMS User permissions
	user_permissions = [
		{"doctype": "BMS Customer", "permlevel": 0, "role": "BMS User", "read": 1, "write": 0, "create": 0, "delete": 0, "submit": 0, "cancel": 0, "amend": 0, "report": 0, "export": 0, "import": 0, "print": 0, "email": 0, "share": 0},
		{"doctype": "BMS Plan", "permlevel": 0, "role": "BMS User", "read": 1, "write": 0, "create": 0, "delete": 0, "submit": 0, "cancel": 0, "amend": 0, "report": 0, "export": 0, "import": 0, "print": 0, "email": 0, "share": 0},
		{"doctype": "BMS Subscription", "permlevel": 0, "role": "BMS User", "read": 1, "write": 1, "create": 1, "delete": 0, "submit": 0, "cancel": 0, "amend": 0, "report": 0, "export": 0, "import": 0, "print": 1, "email": 0, "share": 0},
		{"doctype": "BMS Invoice", "permlevel": 0, "role": "BMS User", "read": 1, "write": 0, "create": 0, "delete": 0, "submit": 0, "cancel": 0, "amend": 0, "report": 0, "export": 1, "import": 0, "print": 1, "email": 0, "share": 0},
		{"doctype": "BMS Payment", "permlevel": 0, "role": "BMS User", "read": 1, "write": 0, "create": 0, "delete": 0, "submit": 0, "cancel": 0, "amend": 0, "report": 0, "export": 1, "import": 0, "print": 1, "email": 0, "share": 0},
	]
	
	# Apply permissions
	for perm in admin_permissions + user_permissions:
		if not frappe.db.exists("Custom DocPerm", {"doctype": perm["doctype"], "role": perm["role"]}):
			docperm = frappe.new_doc("Custom DocPerm")
			docperm.update(perm)
			docperm.save()

def create_sample_data():
	"""Create sample data for testing"""
	# Create sample plans
	create_sample_plans()
	
	# Create sample customer
	create_sample_customer()

def create_sample_plans():
	"""Create sample plans"""
	plans = [
		{
			"plan_name": "Basic Plan",
			"plan_description": "Basic subscription plan with essential features",
			"plan_type": "Basic",
			"billing_cycle": "Monthly",
			"amount": 29.99,
			"currency": "USD",
			"trial_period_days": 7,
			"is_active": 1,
			"max_users": 1,
			"storage_limit_gb": 5,
			"api_calls_limit": 1000,
			"support_level": "Basic",
			"auto_renewal": 1
		},
		{
			"plan_name": "Standard Plan",
			"plan_description": "Standard subscription plan with advanced features",
			"plan_type": "Standard",
			"billing_cycle": "Monthly",
			"amount": 59.99,
			"currency": "USD",
			"trial_period_days": 14,
			"is_active": 1,
			"max_users": 5,
			"storage_limit_gb": 25,
			"api_calls_limit": 5000,
			"support_level": "Standard",
			"auto_renewal": 1
		},
		{
			"plan_name": "Premium Plan",
			"plan_description": "Premium subscription plan with all features",
			"plan_type": "Premium",
			"billing_cycle": "Monthly",
			"amount": 99.99,
			"currency": "USD",
			"trial_period_days": 30,
			"is_active": 1,
			"max_users": 25,
			"storage_limit_gb": 100,
			"api_calls_limit": 25000,
			"support_level": "Premium",
			"auto_renewal": 1
		}
	]
	
	for plan_data in plans:
		if not frappe.db.exists("BMS Plan", {"plan_name": plan_data["plan_name"]}):
			plan = frappe.new_doc("BMS Plan")
			plan.update(plan_data)
			plan.save()

def create_sample_customer():
	"""Create sample customer"""
	if not frappe.db.exists("BMS Customer", {"customer_name": "Sample Customer"}):
		customer = frappe.new_doc("BMS Customer")
		customer.customer_name = "Sample Customer"
		customer.customer_type = "Individual"
		customer.email = "sample@example.com"
		customer.phone = "+1-555-0123"
		customer.status = "Active"
		customer.save()

def before_tests():
	"""Before tests setup"""
	pass
