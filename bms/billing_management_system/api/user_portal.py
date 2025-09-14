import frappe
from frappe import _
from frappe.utils import today, add_months, getdate
import json
import hashlib
import hmac
import os

# Optional Razorpay import
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    razorpay = None

def get_customer_for_user(user_email=None):
	"""Helper function to get BMS Customer record for a user"""
	if not user_email:
		user_email = frappe.session.user
	
	customer_records = frappe.get_all("BMS Customer",
		filters={"email": user_email},
		limit=1
	)
	
	if not customer_records:
		frappe.throw(_("No customer record found for user: {0}").format(user_email))
	
	return customer_records[0].name

@frappe.whitelist()
def get_current_customer():
	"""Get current customer ID for the logged-in user"""
	try:
		customer_id = get_customer_for_user()
		customer_doc = frappe.get_doc("BMS Customer", customer_id)
		return {
			"customer_id": customer_id,
			"customer_name": customer_doc.customer_name,
			"email": customer_doc.email
		}
	except Exception as e:
		frappe.throw(_("No customer record found for user: {0}").format(frappe.session.user))

@frappe.whitelist()
def get_user_plans(customer_email=None):
	"""Get available plans for a specific customer by email"""
	if not customer_email:
		customer_email = frappe.session.user
	
	# Find customer record by email
	customer_records = frappe.get_all("BMS Customer",
		filters={"email": customer_email},
		limit=1
	)
	
	if not customer_records:
		frappe.throw(_("No customer record found for email: {0}").format(customer_email))
	
	customer_id = customer_records[0].name
	
	# Get all active plans
	all_plans = frappe.get_all("BMS Plan",
		filters={"is_active": 1},
		fields=[
			"name", "plan_name", "plan_description", "amount", 
			"currency", "billing_cycle", "plan_visibility", 
			"trial_period_days", "max_users", "storage_limit_gb", 
			"api_calls_limit"
		],
		order_by="amount asc"
	)
	
	available_plans = []
	
	for plan in all_plans:
		plan_doc = frappe.get_doc("BMS Plan", plan.name)
		if plan_doc.is_available_for_customer(customer_id):
			# Get plan features
			features = []
			if plan.plan_description:
				features.extend(plan.plan_description.split('\n'))
			features.append(f"{plan.max_users} Users")
			features.append(f"{plan.storage_limit_gb} GB Storage")
			features.append(f"{plan.api_calls_limit} API Calls")
			if plan.trial_period_days > 0:
				features.append(f"{plan.trial_period_days} Days Free Trial")
			
			plan.features = [f.strip() for f in features if f.strip()]
			available_plans.append(plan)
	
	return available_plans

@frappe.whitelist()
def get_user_subscriptions(customer_email=None):
	"""Get subscriptions for a specific customer by email"""
	if not customer_email:
		customer_email = frappe.session.user
	
	# Find customer record by email
	customer_records = frappe.get_all("BMS Customer",
		filters={"email": customer_email},
		limit=1
	)
	
	if not customer_records:
		frappe.throw(_("No customer record found for email: {0}").format(customer_email))
	
	customer = customer_records[0].name
	
	subscriptions = frappe.get_all("BMS Subscription",
		filters={"customer": customer},
		fields=[
			"name", "plan", "plan_name", "status", "start_date", 
			"end_date", "amount", "billing_cycle", "next_billing_date",
			"auto_renewal", "cancellation_date", "cancellation_reason"
		],
		order_by="creation desc"
	)
	
	return subscriptions

@frappe.whitelist()
def get_user_invoices(customer_email=None):
	"""Get invoices for a specific customer by email"""
	if not customer_email:
		customer_email = frappe.session.user
	
	# Find customer record by email
	customer_records = frappe.get_all("BMS Customer",
		filters={"email": customer_email},
		limit=1
	)
	
	if not customer_records:
		frappe.throw(_("No customer record found for email: {0}").format(customer_email))
	
	customer = customer_records[0].name
	
	invoices = frappe.get_all("BMS Invoice",
		filters={"customer": customer},
		fields=[
			"name", "subscription", "plan", "amount", "currency",
			"invoice_date", "due_date", "status"
		],
		order_by="creation desc"
	)
	
	return invoices

@frappe.whitelist()
def get_user_payments(customer_email=None):
	"""Get payments for a specific customer by email"""
	if not customer_email:
		customer_email = frappe.session.user
	
	# Find customer record by email
	customer_records = frappe.get_all("BMS Customer",
		filters={"email": customer_email},
		limit=1
	)
	
	if not customer_records:
		frappe.throw(_("No customer record found for email: {0}").format(customer_email))
	
	customer = customer_records[0].name
	
	payments = frappe.get_all("BMS Payment",
		filters={"customer": customer},
		fields=[
			"name", "subscription", "plan", "amount", "currency",
			"payment_date", "payment_method", "status", "payment_type"
		],
		order_by="creation desc"
	)
	
	return payments

@frappe.whitelist()
def purchase_plan(plan, customer_email=None, payment_method=None, billing_address=None):
	"""Purchase a plan for a customer by email"""
	if not customer_email:
		customer_email = frappe.session.user
	
	# Find customer record by email
	customer_records = frappe.get_all("BMS Customer",
		filters={"email": customer_email},
		limit=1
	)
	
	if not customer_records:
		frappe.throw(_("No customer record found for email: {0}").format(customer_email))
	
	customer = customer_records[0].name
	
	if not plan:
		frappe.throw(_("Plan is required"))
	
	# Get plan details
	plan_doc = frappe.get_doc("BMS Plan", plan)
	
	# Check if plan is available for customer
	if not plan_doc.is_available_for_customer(customer):
		frappe.throw(_("This plan is not available for you"))
	
	# Check if customer already has an active subscription for this plan
	existing_subscription = frappe.get_all("BMS Subscription",
		filters={
			"customer": customer,
			"plan": plan,
			"status": ["in", ["Active", "Trial"]]
		},
		limit=1
	)
	
	if existing_subscription:
		frappe.throw(_("You already have an active subscription for this plan"))
	
	try:
		# Create subscription
		subscription_doc = frappe.new_doc("BMS Subscription")
		subscription_doc.naming_series = "SUB-.YYYY.-.MM.-.#####"
		subscription_doc.customer = customer
		subscription_doc.plan = plan
		subscription_doc.status = "Active"
		subscription_doc.start_date = today()
		subscription_doc.payment_method = payment_method or "Credit Card"
		subscription_doc.save(ignore_permissions=True)
		
		# Create payment record
		payment_doc = frappe.new_doc("BMS Payment")
		payment_doc.naming_series = "PAY-.YYYY.-.MM.-.#####"
		payment_doc.customer = customer
		payment_doc.subscription = subscription_doc.name
		payment_doc.plan = plan
		payment_doc.amount = plan_doc.amount
		payment_doc.currency = plan_doc.currency
		payment_doc.payment_date = today()
		payment_doc.payment_method = payment_method or "Credit Card"
		payment_doc.status = "Completed"
		payment_doc.payment_type = "Payment"
		payment_doc.save(ignore_permissions=True)
		
		# Create invoice
		invoice_doc = frappe.new_doc("BMS Invoice")
		invoice_doc.naming_series = "INV-.YYYY.-.MM.-.#####"
		invoice_doc.customer = customer
		invoice_doc.subscription = subscription_doc.name
		invoice_doc.plan = plan
		invoice_doc.amount = plan_doc.amount
		invoice_doc.currency = plan_doc.currency
		invoice_doc.invoice_date = today()
		invoice_doc.due_date = today()
		invoice_doc.status = "Paid"
		
		# Add invoice item
		invoice_doc.append("items", {
			"item_name": f"Subscription - {plan_doc.plan_name}",
			"description": f"Subscription for {plan_doc.billing_cycle} billing cycle",
			"quantity": 1,
			"rate": plan_doc.amount,
			"amount": plan_doc.amount
		})
		
		# Add payment link
		invoice_doc.append("payments", {
			"payment": payment_doc.name,
			"amount": plan_doc.amount,
			"payment_date": today(),
			"payment_method": payment_method,
			"status": "Completed"
		})
		
		invoice_doc.save(ignore_permissions=True)
		
		return {
			"status": "success",
			"message": "Plan purchased successfully!",
			"subscription": subscription_doc.name,
			"payment": payment_doc.name,
			"invoice": invoice_doc.name
		}
		
	except Exception as e:
		frappe.log_error(f"Error purchasing plan: {str(e)}")
		frappe.throw(_("Error purchasing plan: {0}").format(str(e)))

@frappe.whitelist()
def cancel_subscription(subscription, reason=None):
	"""Cancel a subscription"""
	subscription_doc = frappe.get_doc("BMS Subscription", subscription)
	
	# Check if user has permission to cancel this subscription
	user_customer = get_customer_for_user()
	if subscription_doc.customer != user_customer:
		frappe.throw(_("You don't have permission to cancel this subscription"))
	
	if subscription_doc.status in ["Cancelled", "Expired"]:
		frappe.throw(_("Subscription is already cancelled or expired"))
	
	subscription_doc.status = "Cancelled"
	subscription_doc.cancellation_date = today()
	subscription_doc.cancellation_reason = reason or "Cancelled by user"
	subscription_doc.auto_renewal = 0
	subscription_doc.save(ignore_permissions=True)
	
	# Create refund request if applicable
	subscription_doc.create_refund_request()
	
	return {
		"status": "success",
		"message": "Subscription cancelled successfully"
	}

@frappe.whitelist()
def download_invoice(invoice):
	"""Generate download link for invoice"""
	invoice_doc = frappe.get_doc("BMS Invoice", invoice)
	
	# Check if user has permission to download this invoice
	user_customer = get_customer_for_user()
	if invoice_doc.customer != user_customer:
		frappe.throw(_("You don't have permission to download this invoice"))
	
	# In a real implementation, this would generate a PDF and return download URL
	# For now, we'll return a success message
	return {
		"status": "success",
		"message": "Invoice download prepared",
		"download_url": f"/api/method/bms.billing_management_system.api.user_portal.get_invoice_pdf?invoice={invoice}"
	}

@frappe.whitelist()
def get_invoice_pdf(invoice):
	"""Generate PDF for invoice"""
	invoice_doc = frappe.get_doc("BMS Invoice", invoice)
	
	# Check if user has permission to download this invoice
	user_customer = get_customer_for_user()
	if invoice_doc.customer != user_customer:
		frappe.throw(_("You don't have permission to download this invoice"))
	
	# In a real implementation, this would generate and return the PDF
	# For now, we'll return invoice data
	return {
		"invoice": invoice_doc.name,
		"customer": invoice_doc.customer,
		"amount": invoice_doc.amount,
		"date": invoice_doc.invoice_date,
		"status": invoice_doc.status
	}

@frappe.whitelist()
def get_user_dashboard_data(customer_email=None):
	"""Get comprehensive dashboard data for user by email"""
	if not customer_email:
		customer_email = frappe.session.user
	
	# Find customer record by email
	customer_records = frappe.get_all("BMS Customer",
		filters={"email": customer_email},
		limit=1
	)
	
	if not customer_records:
		frappe.throw(_("No customer record found for email: {0}").format(customer_email))
	
	customer = customer_records[0].name
	
	# Get customer info
	customer_doc = frappe.get_doc("BMS Customer", customer)
	
	# Get subscription summary
	active_subscriptions = frappe.db.count("BMS Subscription", {
		"customer": customer,
		"status": "Active"
	})
	
	trial_subscriptions = frappe.db.count("BMS Subscription", {
		"customer": customer,
		"status": "Trial"
	})
	
	# Get payment summary
	total_paid = frappe.db.sql("""
		SELECT SUM(amount) 
		FROM `tabBMS Payment` 
		WHERE customer = %s AND status = 'Completed' AND payment_type = 'Payment'
	""", (customer,))[0][0] or 0
	
	# Get recent activity
	recent_subscriptions = frappe.get_all("BMS Subscription",
		filters={"customer": customer},
		fields=["name", "plan_name", "status", "creation"],
		order_by="creation desc",
		limit=5
	)
	
	recent_payments = frappe.get_all("BMS Payment",
		filters={"customer": customer},
		fields=["name", "amount", "status", "payment_date"],
		order_by="creation desc",
		limit=5
	)
	
	return {
		"customer": {
			"name": customer_doc.customer_name,
			"email": customer_doc.email,
			"status": customer_doc.status
		},
		"summary": {
			"active_subscriptions": active_subscriptions,
			"trial_subscriptions": trial_subscriptions,
			"total_paid": total_paid
		},
		"recent_activity": {
			"subscriptions": recent_subscriptions,
			"payments": recent_payments
		}
	}

@frappe.whitelist()
def create_razorpay_order(plan, customer_email=None, amount=None, currency="INR"):
	"""Create a Razorpay order for payment"""
	if not RAZORPAY_AVAILABLE:
		frappe.throw(_("Razorpay module not installed. Please install it with: pip install razorpay"))
	
	if not customer_email:
		customer_email = frappe.session.user
	
	# Find customer record by email
	customer_records = frappe.get_all("BMS Customer",
		filters={"email": customer_email},
		limit=1
	)
	
	if not customer_records:
		frappe.throw(_("No customer record found for email: {0}").format(customer_email))
	
	customer = customer_records[0].name
	
	if not plan:
		frappe.throw(_("Plan is required"))
	
	# Get plan details
	plan_doc = frappe.get_doc("BMS Plan", plan)
	
	# Check if plan is available for customer
	if not plan_doc.is_available_for_customer(customer):
		frappe.throw(_("This plan is not available for you"))
	
	# Get Razorpay credentials from site config
	razorpay_key_id = "rzp_test_RHC1S9293wovjQ"
	razorpay_key_secret = "DAzu38mqdRSnkgtv83WdWe6O"
	
	if not razorpay_key_id or not razorpay_key_secret:
		frappe.throw(_("Razorpay credentials not configured"))
	
	# Initialize Razorpay client
	client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
	
	# Create order
	# Generate a short receipt (max 40 chars for Razorpay)
	from datetime import datetime
	now = datetime.now()
	receipt_id = f"BMS_{plan[:8]}_{customer[:8]}_{now.strftime('%m%d%H%M')}"
	if len(receipt_id) > 40:
		receipt_id = receipt_id[:40]
	
	order_data = {
		"amount": amount or (plan_doc.amount * 100),  # Convert to paise
		"currency": currency,
		"receipt": receipt_id,
		"notes": {
			"plan": plan,
			"customer": customer,
			"plan_name": plan_doc.plan_name
		}
	}
	
	try:
		order = client.order.create(data=order_data)
		
		return {
			"order_id": order["id"],
			"key_id": razorpay_key_id,
			"amount": order["amount"],
			"currency": order["currency"]
		}
		
	except Exception as e:
		frappe.log_error(f"Razorpay order creation failed: {str(e)}")
		frappe.throw(_("Failed to create payment order: {0}").format(str(e)))

@frappe.whitelist()
def verify_payment_and_create_subscription(plan, customer_email=None, payment_id=None, order_id=None, signature=None, payment_method="Razorpay"):
	"""Verify Razorpay payment and create subscription"""
	if not RAZORPAY_AVAILABLE:
		frappe.throw(_("Razorpay module not installed. Please install it with: pip install razorpay"))
	
	if not customer_email:
		customer_email = frappe.session.user
	
	# Find customer record by email
	customer_records = frappe.get_all("BMS Customer",
		filters={"email": customer_email},
		limit=1
	)
	
	if not customer_records:
		frappe.throw(_("No customer record found for email: {0}").format(customer_email))
	
	customer = customer_records[0].name
	
	if not all([plan, payment_id, order_id, signature]):
		frappe.throw(_("Payment verification data is incomplete"))
	
	# Get Razorpay credentials
	razorpay_key_secret = 'DAzu38mqdRSnkgtv83WdWe6O'
	
	if not razorpay_key_secret:
		frappe.throw(_("Razorpay credentials not configured"))
	
	# Verify payment signature
	body = f"{order_id}|{payment_id}"
	generated_signature = hmac.new(
		razorpay_key_secret.encode(),
		body.encode(),
		hashlib.sha256
	).hexdigest()
	
	if generated_signature != signature:
		frappe.throw(_("Payment verification failed"))
	
	# Get plan details
	plan_doc = frappe.get_doc("BMS Plan", plan)
	
	# Check if customer already has an active subscription for this plan
	existing_subscription = frappe.get_all("BMS Subscription",
		filters={
			"customer": customer,
			"plan": plan,
			"status": ["in", ["Active", "Trial"]]
		},
		limit=1
	)
	
	if existing_subscription:
		frappe.throw(_("You already have an active subscription for this plan"))
	
	try:
		# Create subscription
		subscription_doc = frappe.new_doc("BMS Subscription")
		subscription_doc.naming_series = "SUB-.YYYY.-.MM.-.#####"
		subscription_doc.customer = customer
		subscription_doc.plan = plan
		subscription_doc.status = "Active"
		subscription_doc.start_date = today()
		subscription_doc.payment_method = payment_method
		subscription_doc.save(ignore_permissions=True)
		
		# Create payment record
		payment_doc = frappe.new_doc("BMS Payment")
		payment_doc.naming_series = "PAY-.YYYY.-.MM.-.#####"
		payment_doc.customer = customer
		payment_doc.subscription = subscription_doc.name
		payment_doc.plan = plan
		payment_doc.amount = plan_doc.amount
		payment_doc.currency = plan_doc.currency
		payment_doc.payment_date = today()
		payment_doc.payment_method = payment_method
		payment_doc.status = "Completed"
		payment_doc.payment_type = "Payment"
		payment_doc.razorpay_payment_id = payment_id
		payment_doc.razorpay_order_id = order_id
		payment_doc.notes = f"Payment via {payment_method} - Payment ID: {payment_id}, Order ID: {order_id}"
		payment_doc.save(ignore_permissions=True)
		
		# Create invoice
		invoice_doc = frappe.new_doc("BMS Invoice")
		invoice_doc.naming_series = "INV-.YYYY.-.MM.-.#####"
		invoice_doc.customer = customer
		invoice_doc.subscription = subscription_doc.name
		invoice_doc.plan = plan
		invoice_doc.amount = plan_doc.amount
		invoice_doc.currency = plan_doc.currency
		invoice_doc.invoice_date = today()
		invoice_doc.due_date = today()
		invoice_doc.status = "Paid"
		
		# Add invoice item
		invoice_doc.append("items", {
			"item_name": f"Subscription - {plan_doc.plan_name}",
			"description": f"Subscription for {plan_doc.billing_cycle} billing cycle",
			"quantity": 1,
			"rate": plan_doc.amount,
			"amount": plan_doc.amount
		})
		
		# Add payment link
		invoice_doc.append("payments", {
			"payment": payment_doc.name,
			"amount": plan_doc.amount,
			"payment_date": today(),
			"payment_method": payment_method,
			"status": "Completed"
		})
		
		invoice_doc.save(ignore_permissions=True)
		
		return {
			"status": "success",
			"message": "Payment successful! Your subscription is now active.",
			"subscription": subscription_doc.name,
			"payment": payment_doc.name,
			"invoice": invoice_doc.name
		}
		
	except Exception as e:
		frappe.log_error(f"Error creating subscription after payment: {str(e)}")
		frappe.throw(_(" method {0}").format(str(e)))
