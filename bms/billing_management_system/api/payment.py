import frappe
from frappe import _
from frappe.utils import today
import json

@frappe.whitelist()
def process_payment(customer, subscription, amount, payment_method, reference=None):
	"""Process a payment"""
	try:
		# Validate inputs
		if not frappe.db.exists("BMS Customer", customer):
			frappe.throw(_("Customer not found"))
		
		if not frappe.db.exists("BMS Subscription", subscription):
			frappe.throw(_("Subscription not found"))
		
		# Get subscription details
		subscription_doc = frappe.get_doc("BMS Subscription", subscription)
		
		# Create payment record
		payment_doc = frappe.new_doc("BMS Payment")
		payment_doc.customer = customer
		payment_doc.subscription = subscription
		payment_doc.plan = subscription_doc.plan
		payment_doc.amount = amount
		payment_doc.currency = subscription_doc.currency
		payment_doc.payment_type = "Payment"
		payment_doc.payment_date = today()
		payment_doc.status = "Completed"
		payment_doc.payment_method = payment_method
		payment_doc.reference = reference
		payment_doc.save()
		
		# Update subscription status
		if subscription_doc.status == "Trial":
			subscription_doc.status = "Active"
			subscription_doc.save()
		
		return {
			"status": "success",
			"payment": payment_doc.name,
			"message": _("Payment processed successfully")
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Payment Processing Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def process_refund(payment, reason=None):
	"""Process a refund"""
	try:
		payment_doc = frappe.get_doc("BMS Payment", payment)
		refund_doc = payment_doc.process_refund(reason)
		
		return {
			"status": "success",
			"refund": refund_doc.name,
			"message": _("Refund processed successfully")
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Refund Processing Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_payment_history(customer):
	"""Get payment history for a customer"""
	try:
		payments = frappe.get_all("BMS Payment",
			filters={"customer": customer},
			fields=["name", "subscription", "plan", "amount", "currency", 
					"payment_type", "payment_date", "status", "payment_method"],
			order_by="payment_date desc"
		)
		
		return {
			"status": "success",
			"data": payments
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Payment History Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_payment_summary(customer):
	"""Get payment summary for a customer"""
	try:
		# Get total payments
		total_payments = frappe.get_all("BMS Payment",
			filters={
				"customer": customer,
				"payment_type": "Payment",
				"status": "Completed"
			},
			fields=["amount"]
		)
		
		# Get total refunds
		total_refunds = frappe.get_all("BMS Payment",
			filters={
				"customer": customer,
				"payment_type": "Refund",
				"status": "Completed"
			},
			fields=["amount"]
		)
		
		total_paid = sum(payment.amount for payment in total_payments)
		total_refunded = sum(refund.amount for refund in total_refunds)
		
		return {
			"status": "success",
			"data": {
				"total_paid": total_paid,
				"total_refunded": total_refunded,
				"net_amount": total_paid - total_refunded
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Payment Summary Error")
		return {
			"status": "error",
			"message": str(e)
		}
