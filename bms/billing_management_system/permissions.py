import frappe
from frappe import _

def get_subscription_permission_query_conditions(user):
	"""Get permission query conditions for BMS Subscription"""
	if not user:
		user = frappe.session.user
	
	# Admin can see all subscriptions
	if "BMS Admin" in frappe.get_roles(user):
		return ""
	
	# User can only see their own subscriptions
	if "BMS User" in frappe.get_roles(user):
		# Get customer linked to this user
		customer = get_customer_for_user(user)
		if customer:
			return f"`tabBMS Subscription`.customer = '{customer}'"
	
	return "1=0"  # No access

def get_invoice_permission_query_conditions(user):
	"""Get permission query conditions for BMS Invoice"""
	if not user:
		user = frappe.session.user
	
	# Admin can see all invoices
	if "BMS Admin" in frappe.get_roles(user):
		return ""
	
	# User can only see their own invoices
	if "BMS User" in frappe.get_roles(user):
		customer = get_customer_for_user(user)
		if customer:
			return f"`tabBMS Invoice`.customer = '{customer}'"
	
	return "1=0"  # No access

def get_payment_permission_query_conditions(user):
	"""Get permission query conditions for BMS Payment"""
	if not user:
		user = frappe.session.user
	
	# Admin can see all payments
	if "BMS Admin" in frappe.get_roles(user):
		return ""
	
	# User can only see their own payments
	if "BMS User" in frappe.get_roles(user):
		customer = get_customer_for_user(user)
		if customer:
			return f"`tabBMS Payment`.customer = '{customer}'"
	
	return "1=0"  # No access

def has_subscription_permission(doc, ptype, user=None):
	"""Check if user has permission for BMS Subscription"""
	if not user:
		user = frappe.session.user
	
	# Admin has all permissions
	if "BMS Admin" in frappe.get_roles(user):
		return True
	
	# User can only access their own subscriptions
	if "BMS User" in frappe.get_roles(user):
		customer = get_customer_for_user(user)
		if customer and doc.customer == customer:
			# User can read and write their own subscriptions
			return ptype in ["read", "write"]
	
	return False

def has_invoice_permission(doc, ptype, user=None):
	"""Check if user has permission for BMS Invoice"""
	if not user:
		user = frappe.session.user
	
	# Admin has all permissions
	if "BMS Admin" in frappe.get_roles(user):
		return True
	
	# User can only read their own invoices
	if "BMS User" in frappe.get_roles(user):
		customer = get_customer_for_user(user)
		if customer and doc.customer == customer:
			return ptype == "read"
	
	return False

def has_payment_permission(doc, ptype, user=None):
	"""Check if user has permission for BMS Payment"""
	if not user:
		user = frappe.session.user
	
	# Admin has all permissions
	if "BMS Admin" in frappe.get_roles(user):
		return True
	
	# User can only read their own payments
	if "BMS User" in frappe.get_roles(user):
		customer = get_customer_for_user(user)
		if customer and doc.customer == customer:
			return ptype == "read"
	
	return False

def get_customer_for_user(user):
	"""Get customer linked to user"""
	# This assumes there's a link between User and BMS Customer
	# You might need to modify this based on your user-customer relationship
	customer = frappe.db.get_value("BMS Customer", {"email": user}, "name")
	return customer
