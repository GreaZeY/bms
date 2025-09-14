import frappe
from frappe import _
from frappe.utils import today, add_days, get_datetime
import json

@frappe.whitelist()
def create_subscription(customer, plan, start_date=None):
	"""Create a new subscription"""
	try:
		# Validate customer and plan
		if not frappe.db.exists("BMS Customer", customer):
			frappe.throw(_("Customer not found"))
		
		if not frappe.db.exists("BMS Plan", plan):
			frappe.throw(_("Plan not found"))
		
		# Get plan details
		plan_doc = frappe.get_doc("BMS Plan", plan)
		
		# Create subscription
		subscription_doc = frappe.new_doc("BMS Subscription")
		subscription_doc.customer = customer
		subscription_doc.plan = plan
		subscription_doc.start_date = start_date or today()
		subscription_doc.status = "Trial" if plan_doc.trial_period_days > 0 else "Active"
		subscription_doc.save()
		
		return {
			"status": "success",
			"subscription": subscription_doc.name,
			"message": _("Subscription created successfully")
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Subscription Creation Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def cancel_subscription(subscription, reason=None):
	"""Cancel a subscription"""
	try:
		subscription_doc = frappe.get_doc("BMS Subscription", subscription)
		subscription_doc.cancel_subscription(reason)
		
		return {
			"status": "success",
			"message": _("Subscription cancelled successfully")
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Subscription Cancellation Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def renew_subscription(subscription):
	"""Renew a subscription"""
	try:
		subscription_doc = frappe.get_doc("BMS Subscription", subscription)
		subscription_doc.renew_subscription()
		
		return {
			"status": "success",
			"message": _("Subscription renewed successfully")
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Subscription Renewal Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_subscription_details(subscription):
	"""Get subscription details"""
	try:
		subscription_doc = frappe.get_doc("BMS Subscription", subscription)
		
		return {
			"status": "success",
			"data": {
				"name": subscription_doc.name,
				"customer": subscription_doc.customer,
				"plan": subscription_doc.plan,
				"status": subscription_doc.status,
				"start_date": subscription_doc.start_date,
				"end_date": subscription_doc.end_date,
				"amount": subscription_doc.amount,
				"currency": subscription_doc.currency,
				"billing_cycle": subscription_doc.billing_cycle,
				"auto_renewal": subscription_doc.auto_renewal,
				"next_billing_date": subscription_doc.next_billing_date
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Subscription Details Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_customer_subscriptions(customer):
	"""Get all subscriptions for a customer"""
	try:
		subscriptions = frappe.get_all("BMS Subscription",
			filters={"customer": customer},
			fields=["name", "plan", "status", "start_date", "end_date", "amount", "currency"]
		)
		
		return {
			"status": "success",
			"data": subscriptions
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Customer Subscriptions Error")
		return {
			"status": "error",
			"message": str(e)
		}
