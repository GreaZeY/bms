import frappe
from frappe import _
from frappe.utils import today, add_days, get_datetime
from datetime import datetime, timedelta

@frappe.whitelist()
def get_dashboard_data():
	"""Get dashboard data for BMS"""
	try:
		user = frappe.session.user
		
		# Check if user is admin or regular user
		if "BMS Admin" in frappe.get_roles(user):
			return get_admin_dashboard_data()
		elif "BMS User" in frappe.get_roles(user):
			return get_user_dashboard_data()
		else:
			return {
				"status": "error",
				"message": _("Access denied")
			}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Dashboard Data Error")
		return {
			"status": "error",
			"message": str(e)
		}

def get_admin_dashboard_data():
	"""Get admin dashboard data"""
	try:
		# Get subscription statistics
		subscription_stats = get_subscription_statistics()
		
		# Get revenue statistics
		revenue_stats = get_revenue_statistics()
		
		# Get payment statistics
		payment_stats = get_payment_statistics()
		
		# Get recent activities
		recent_activities = get_recent_activities()
		
		# Get upcoming renewals
		upcoming_renewals = get_upcoming_renewals()
		
		# Get overdue invoices
		overdue_invoices = get_overdue_invoices()
		
		return {
			"status": "success",
			"data": {
				"subscriptions": subscription_stats,
				"revenue": revenue_stats,
				"payments": payment_stats,
				"recent_activities": recent_activities,
				"upcoming_renewals": upcoming_renewals,
				"overdue_invoices": overdue_invoices
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Admin Dashboard Error")
		return {
			"status": "error",
			"message": str(e)
		}

def get_user_dashboard_data():
	"""Get user dashboard data"""
	try:
		# Get customer for this user
		customer = get_customer_for_user(frappe.session.user)
		if not customer:
			return {
				"status": "error",
				"message": _("Customer not found for this user")
			}
		
		# Get user's subscriptions
		user_subscriptions = get_user_subscriptions(customer)
		
		# Get user's payments
		user_payments = get_user_payments(customer)
		
		# Get user's invoices
		user_invoices = get_user_invoices(customer)
		
		# Get payment summary
		payment_summary = get_user_payment_summary(customer)
		
		return {
			"status": "success",
			"data": {
				"subscriptions": user_subscriptions,
				"payments": user_payments,
				"invoices": user_invoices,
				"payment_summary": payment_summary
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS User Dashboard Error")
		return {
			"status": "error",
			"message": str(e)
		}

def get_subscription_statistics():
	"""Get subscription statistics"""
	total = frappe.db.count("BMS Subscription")
	active = frappe.db.count("BMS Subscription", {"status": "Active"})
	trial = frappe.db.count("BMS Subscription", {"status": "Trial"})
	cancelled = frappe.db.count("BMS Subscription", {"status": "Cancelled"})
	expired = frappe.db.count("BMS Subscription", {"status": "Expired"})
	suspended = frappe.db.count("BMS Subscription", {"status": "Suspended"})
	
	return {
		"total": total,
		"active": active,
		"trial": trial,
		"cancelled": cancelled,
		"expired": expired,
		"suspended": suspended
	}

def get_revenue_statistics():
	"""Get revenue statistics"""
	# Total revenue
	total_payments = frappe.get_all("BMS Payment",
		filters={
			"payment_type": "Payment",
			"status": "Completed"
		},
		fields=["amount"]
	)
	total_revenue = sum(payment.amount for payment in total_payments)
	
	# Monthly revenue
	current_month = today().strftime("%Y-%m")
	monthly_payments = frappe.get_all("BMS Payment",
		filters={
			"payment_type": "Payment",
			"status": "Completed",
			"payment_date": ["like", f"{current_month}%"]
		},
		fields=["amount"]
	)
	monthly_revenue = sum(payment.amount for payment in monthly_payments)
	
	# Refunds
	total_refunds = frappe.get_all("BMS Payment",
		filters={
			"payment_type": "Refund",
			"status": "Completed"
		},
		fields=["amount"]
	)
	total_refunded = sum(refund.amount for refund in total_refunds)
	
	return {
		"total": total_revenue,
		"monthly": monthly_revenue,
		"refunded": total_refunded,
		"net": total_revenue - total_refunded
	}

def get_payment_statistics():
	"""Get payment statistics"""
	total = frappe.db.count("BMS Payment")
	completed = frappe.db.count("BMS Payment", {"status": "Completed"})
	pending = frappe.db.count("BMS Payment", {"status": "Pending"})
	failed = frappe.db.count("BMS Payment", {"status": "Failed"})
	refunded = frappe.db.count("BMS Payment", {"status": "Refunded"})
	
	return {
		"total": total,
		"completed": completed,
		"pending": pending,
		"failed": failed,
		"refunded": refunded
	}

def get_recent_activities():
	"""Get recent activities"""
	activities = []
	
	# Recent subscriptions
	recent_subscriptions = frappe.get_all("BMS Subscription",
		filters={},
		fields=["name", "customer", "plan", "status", "creation"],
		order_by="creation desc",
		limit=5
	)
	
	for sub in recent_subscriptions:
		activities.append({
			"type": "subscription",
			"action": "created",
			"description": f"Subscription {sub.name} created for {sub.customer}",
			"date": sub.creation,
			"status": sub.status
		})
	
	# Recent payments
	recent_payments = frappe.get_all("BMS Payment",
		filters={},
		fields=["name", "customer", "amount", "payment_type", "status", "creation"],
		order_by="creation desc",
		limit=5
	)
	
	for payment in recent_payments:
		activities.append({
			"type": "payment",
			"action": "processed",
			"description": f"Payment {payment.name} of {payment.amount} processed",
			"date": payment.creation,
			"status": payment.status
		})
	
	# Sort by date
	activities.sort(key=lambda x: x["date"], reverse=True)
	
	return activities[:10]

def get_upcoming_renewals():
	"""Get upcoming renewals"""
	upcoming_date = add_days(today(), 7)  # Next 7 days
	
	upcoming_renewals = frappe.get_all("BMS Subscription",
		filters={
			"status": "Active",
			"auto_renewal": 1,
			"next_billing_date": ["<=", upcoming_date]
		},
		fields=["name", "customer", "plan", "amount", "next_billing_date"],
		order_by="next_billing_date asc"
	)
	
	return upcoming_renewals

def get_overdue_invoices():
	"""Get overdue invoices"""
	overdue_invoices = frappe.get_all("BMS Invoice",
		filters={
			"status": "Overdue"
		},
		fields=["name", "customer", "amount", "due_date"],
		order_by="due_date asc"
	)
	
	return overdue_invoices

def get_user_subscriptions(customer):
	"""Get user's subscriptions"""
	subscriptions = frappe.get_all("BMS Subscription",
		filters={"customer": customer},
		fields=["name", "plan", "status", "start_date", "end_date", "amount", "currency", "billing_cycle"],
		order_by="creation desc"
	)
	
	return subscriptions

def get_user_payments(customer):
	"""Get user's payments"""
	payments = frappe.get_all("BMS Payment",
		filters={"customer": customer},
		fields=["name", "subscription", "amount", "currency", "payment_type", "status", "payment_date"],
		order_by="payment_date desc",
		limit=10
	)
	
	return payments

def get_user_invoices(customer):
	"""Get user's invoices"""
	invoices = frappe.get_all("BMS Invoice",
		filters={"customer": customer},
		fields=["name", "subscription", "amount", "currency", "status", "invoice_date", "due_date"],
		order_by="invoice_date desc",
		limit=10
	)
	
	return invoices

def get_user_payment_summary(customer):
	"""Get user's payment summary"""
	# Total payments
	total_payments = frappe.get_all("BMS Payment",
		filters={
			"customer": customer,
			"payment_type": "Payment",
			"status": "Completed"
		},
		fields=["amount"]
	)
	total_paid = sum(payment.amount for payment in total_payments)
	
	# Total refunds
	total_refunds = frappe.get_all("BMS Payment",
		filters={
			"customer": customer,
			"payment_type": "Refund",
			"status": "Completed"
		},
		fields=["amount"]
	)
	total_refunded = sum(refund.amount for refund in total_refunds)
	
	return {
		"total_paid": total_paid,
		"total_refunded": total_refunded,
		"net_amount": total_paid - total_refunded
	}

def get_customer_for_user(user):
	"""Get customer linked to user"""
	customer = frappe.db.get_value("BMS Customer", {"email": user}, "name")
	return customer
