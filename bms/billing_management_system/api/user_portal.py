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

def get_currency_conversion_rate(from_currency, to_currency):
	"""Get currency conversion rate - for now return 1:1 for same currency or basic USD to INR"""
	if from_currency == to_currency:
		return 1.0
	
	# Basic conversion rates - in production, use a real currency API
	conversion_rates = {
		"USD_INR": 83.0,  # 1 USD = 83 INR (approximate)
		"INR_USD": 0.012,  # 1 INR = 0.012 USD (approximate)
	}
	
	rate_key = f"{from_currency}_{to_currency}"
	return conversion_rates.get(rate_key, 1.0)

def convert_currency_amount(amount, from_currency, to_currency):
	"""Convert amount from one currency to another"""
	if from_currency == to_currency:
		return amount
	
	rate = get_currency_conversion_rate(from_currency, to_currency)
	return round(amount * rate, 2)

def get_razorpay_currency_for_plan(plan_doc):
	"""Determine the appropriate currency for Razorpay based on plan currency"""
	# Razorpay supports multiple currencies, but INR is most common
	# For USD plans, we can use USD if Razorpay account supports it
	# Otherwise, convert to INR
	
	# Check if plan currency is supported by Razorpay
	razorpay_supported_currencies = ["INR", "USD", "EUR", "GBP", "AUD", "CAD", "SGD"]
	
	if plan_doc.currency in razorpay_supported_currencies:
		return plan_doc.currency
	else:
		# Default to INR if currency not supported
		return "INR"

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
			# Check if customer has any subscription for this plan
			existing_subscription = frappe.get_all("BMS Subscription",
				filters={
					"customer": customer_id,
					"plan": plan.name,
					"status": ["in", ["Active", "Trial", "Cancelled"]]
				},
				fields=["name", "status", "start_date", "end_date", "next_billing_date", "auto_renewal"],
				order_by="creation desc",
				limit=1
			)
			
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
			
			# Add subscription status information
			if existing_subscription:
				subscription_data = existing_subscription[0]
				plan.has_active_subscription = subscription_data.status in ["Active", "Trial"]
				plan.has_cancelled_subscription = subscription_data.status == "Cancelled"
				plan.subscription = subscription_data
				
				# Check if cancelled subscription can be reactivated (not expired)
				if plan.has_cancelled_subscription:
					today_date = frappe.utils.getdate(frappe.utils.today())
					end_date = frappe.utils.getdate(subscription_data.end_date)
					plan.can_reactivate = today_date <= end_date
				else:
					plan.can_reactivate = False
			else:
				plan.has_active_subscription = False
				plan.has_cancelled_subscription = False
				plan.can_reactivate = False
				plan.subscription = None
			
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
	# Set flag to prevent auto-invoice creation
	frappe.flags.via_api = True
	
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
		subscription_doc.payment_gateway = ""  # No gateway for manual purchases
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
		payment_doc.payment_gateway = ""  # No gateway for manual purchases
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
			"payment_method": payment_method or "Credit Card",
			"payment_gateway": "",
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
	
	# Use the new graceful cancellation method
	subscription_doc.cancel_subscription(reason)
	
	return {
		"status": "success",
		"message": "Subscription cancelled successfully"
	}

@frappe.whitelist()
def reactivate_subscription(subscription, customer_email=None):
	"""Reactivate a cancelled subscription"""
	if not customer_email:
		customer_email = frappe.session.user
	
	subscription_doc = frappe.get_doc("BMS Subscription", subscription)
	
	# Check if user has permission to reactivate this subscription
	user_customer = get_customer_for_user(customer_email)
	if subscription_doc.customer != user_customer:
		frappe.throw(_("You don't have permission to reactivate this subscription"))
	
	subscription_doc.reactivate_subscription()
	
	return {
		"status": "success",
		"message": "Subscription reactivated successfully"
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
def create_razorpay_subscription(plan, customer_email=None, currency=None):
	"""Create a Razorpay subscription for recurring billing"""
	try:
		frappe.log_error(f"Starting create_razorpay_subscription with plan: {plan}, customer_email: {customer_email}")
		
		if not RAZORPAY_AVAILABLE:
			frappe.log_error("Razorpay module not available")
			frappe.throw(_("Razorpay module not installed. Please install it with: pip install razorpay"))
		
		if not customer_email:
			customer_email = frappe.session.user
		
		frappe.log_error(f"Using customer_email: {customer_email}")
		
		# Find customer record by email
		customer_records = frappe.get_all("BMS Customer",
			filters={"email": customer_email},
			limit=1
		)
		
		if not customer_records:
			frappe.throw(_("No customer record found for email: {0}").format(customer_email))
		
		customer = customer_records[0].name
		customer_doc = frappe.get_doc("BMS Customer", customer)
		frappe.log_error(f"Found customer: {customer}")
		
		if not plan:
			frappe.throw(_("Plan is required"))
		
		# Get plan details
		plan_doc = frappe.get_doc("BMS Plan", plan)
		frappe.log_error(f"Plan doc loaded: {plan_doc.plan_name}, amount: {plan_doc.amount}")
		
		# Use plan's currency if not provided, but ensure it's supported by Razorpay
		if not currency:
			currency = get_razorpay_currency_for_plan(plan_doc)
		
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
		
		# Create or get Razorpay plan
		razorpay_plan_id = create_or_get_razorpay_plan(client, plan_doc, currency)
		
		# Calculate converted amount for response
		converted_amount = convert_currency_amount(plan_doc.amount, plan_doc.currency, currency)
		
		# Create Razorpay customer if not exists
		razorpay_customer_id = create_or_get_razorpay_customer(client, customer_doc)
		
		# Determine total count based on billing cycle for a reasonable long-term subscription
		if plan_doc.billing_cycle.lower() == "monthly":
			total_count = 120  # 10 years
		elif plan_doc.billing_cycle.lower() == "yearly":
			total_count = 10   # 10 years
		elif plan_doc.billing_cycle.lower() == "weekly":
			total_count = 520  # 10 years
		else:
			total_count = 120  # Default to 10 years worth of monthly cycles
		
		# Create subscription
		subscription_data = {
			"plan_id": razorpay_plan_id,
			"customer_id": razorpay_customer_id,
			"total_count": total_count,
			"quantity": 1,
			"notes": {
				"bms_plan": plan,
				"bms_customer": customer,
				"plan_name": plan_doc.plan_name
			}
		}
		
		frappe.log_error(f"Creating Razorpay subscription with data: {subscription_data}")
		
		subscription = client.subscription.create(data=subscription_data)
		
		frappe.log_error(f"Razorpay subscription created successfully: {subscription['id']}")
		
		return {
			"status": "success",
			"subscription": {
				"id": subscription["id"],
				"key_id": razorpay_key_id,
				"plan_id": razorpay_plan_id,
				"customer_id": razorpay_customer_id,
				"amount": int(float(converted_amount) * 100),  # Amount in smallest currency unit (converted)
				"display_amount": converted_amount,  # Converted amount for display
				"original_amount": plan_doc.amount,  # Original plan amount
				"currency": currency,  # Target currency (for Razorpay)
				"original_currency": plan_doc.currency,  # Plan's original currency
				"short_url": subscription.get("short_url")
			}
		}
		
	except Exception as e:
		error_msg = str(e)
		frappe.log_error(f"Razorpay subscription creation failed: {error_msg}")
		frappe.throw(_("Failed to create subscription: {0}").format(error_msg))

def create_or_get_razorpay_plan(client, plan_doc, currency=None):
	"""Create or get existing Razorpay plan"""
	frappe.log_error(f"Creating Razorpay plan for: {plan_doc.plan_name}")
	
	# Use plan's currency if not provided, but ensure it's supported by Razorpay
	if not currency:
		currency = get_razorpay_currency_for_plan(plan_doc)
	
	# Check if we already have a Razorpay plan ID stored
	try:
		existing_razorpay_id = frappe.db.get_value("BMS Plan", plan_doc.name, "razorpay_plan_id")
		if existing_razorpay_id:
			try:
				existing_plan = client.plan.fetch(existing_razorpay_id)
				frappe.log_error(f"Using existing Razorpay plan: {existing_razorpay_id}")
				return existing_razorpay_id
			except Exception as e:
				frappe.log_error(f"Razorpay plan {existing_razorpay_id} not found, creating new one")
	except Exception as e:
		frappe.log_error(f"Error checking existing plan: {str(e)}")
	
	# Convert billing cycle to Razorpay format
	if plan_doc.billing_cycle.lower() == "monthly":
		period = "monthly"
		interval = 1
	elif plan_doc.billing_cycle.lower() == "yearly":
		period = "yearly"
		interval = 1
	elif plan_doc.billing_cycle.lower() == "weekly":
		period = "weekly"
		interval = 1
	else:
		period = "monthly"
		interval = 1
	
	# Convert the plan amount to the target currency if needed
	converted_amount = convert_currency_amount(plan_doc.amount, plan_doc.currency, currency)
	
	# Convert amount to smallest currency unit
	# For USD: dollars to cents (*100)
	# For INR: rupees to paise (*100)
	# For other currencies: assume *100 conversion
	amount_in_smallest_unit = int(float(converted_amount) * 100)
	
	frappe.log_error(f"Currency conversion: {plan_doc.amount} {plan_doc.currency} -> {converted_amount} {currency} -> {amount_in_smallest_unit} smallest units")
	
	plan_data = {
		"period": period,
		"interval": interval,
		"item": {
			"name": plan_doc.plan_name,
			"amount": amount_in_smallest_unit,
			"currency": currency,
			"description": plan_doc.plan_description or f"{plan_doc.plan_name} subscription"
		},
		"notes": {
			"bms_plan": plan_doc.name,
			"plan_name": plan_doc.plan_name,
			"original_amount": plan_doc.amount,
			"original_currency": plan_doc.currency,
			"converted_amount": converted_amount,
			"target_currency": currency
		}
	}
	
	created_plan = client.plan.create(data=plan_data)
	razorpay_plan_id = created_plan["id"]
	
	frappe.log_error(f"Razorpay plan created: {razorpay_plan_id}")
	
	# Save the Razorpay plan ID to database
	try:
		frappe.db.set_value("BMS Plan", plan_doc.name, "razorpay_plan_id", razorpay_plan_id)
		frappe.db.commit()
	except Exception as db_error:
		frappe.log_error(f"Failed to save razorpay_plan_id to database: {str(db_error)}")
	
	return razorpay_plan_id

def create_or_get_razorpay_customer(client, customer_doc):
	"""Create or get existing Razorpay customer"""
	frappe.log_error(f"Creating Razorpay customer for: {customer_doc.customer_name}")
	
	# Check if we already have a Razorpay customer ID stored
	try:
		existing_razorpay_id = frappe.db.get_value("BMS Customer", customer_doc.name, "razorpay_customer_id")
		if existing_razorpay_id:
			try:
				existing_customer = client.customer.fetch(existing_razorpay_id)
				frappe.log_error(f"Using existing Razorpay customer: {existing_razorpay_id}")
				return existing_razorpay_id
			except Exception as e:
				frappe.log_error(f"Razorpay customer {existing_razorpay_id} not found, creating new one")
	except Exception as e:
		frappe.log_error(f"Error checking existing customer: {str(e)}")
	
	# Import time for unique email generation if needed
	import time
	
	# Try to create customer with original email first
	customer_data = {
		"name": customer_doc.customer_name,
		"email": customer_doc.email,
		"contact": customer_doc.phone or "",
		"notes": {
			"bms_customer": customer_doc.name,
			"customer_type": customer_doc.customer_type,
			"original_email": customer_doc.email
		}
	}
	
	try:
		created_customer = client.customer.create(data=customer_data)
		razorpay_customer_id = created_customer["id"]
		frappe.log_error(f"Razorpay customer created: {razorpay_customer_id}")
		
		# Save the Razorpay customer ID to database
		try:
			frappe.db.set_value("BMS Customer", customer_doc.name, "razorpay_customer_id", razorpay_customer_id)
			frappe.db.commit()
		except Exception as db_error:
			frappe.log_error(f"Failed to save razorpay_customer_id to database: {str(db_error)}")
		
		return razorpay_customer_id
		
	except Exception as e:
		error_msg = str(e)
		
		if "Customer already exists" in error_msg or "already exists" in error_msg:
			frappe.log_error(f"Customer already exists, creating with timestamp-based email")
			
			# Create a unique email by adding timestamp
			timestamp = str(int(time.time()))
			email_parts = customer_doc.email.split('@')
			unique_email = f"{email_parts[0]}+{timestamp}@{email_parts[1]}"
			
			customer_data["email"] = unique_email
			
			try:
				created_customer = client.customer.create(data=customer_data)
				razorpay_customer_id = created_customer["id"]
				frappe.log_error(f"Razorpay customer created with unique email: {razorpay_customer_id}")
				
				# Save the Razorpay customer ID to database
				try:
					frappe.db.set_value("BMS Customer", customer_doc.name, "razorpay_customer_id", razorpay_customer_id)
					frappe.db.commit()
				except Exception as db_error:
					frappe.log_error(f"Failed to save razorpay_customer_id to database: {str(db_error)}")
				
				return razorpay_customer_id
				
			except Exception as retry_error:
				frappe.log_error(f"Failed to create customer even with unique email: {str(retry_error)}")
				frappe.throw(_("Failed to create customer on Razorpay: {0}").format(str(retry_error)))
		else:
			frappe.log_error(f"Unexpected error creating Razorpay customer: {error_msg}")
			frappe.throw(_("Failed to create customer on Razorpay: {0}").format(error_msg))


@frappe.whitelist()
def test_order_creation(plan, customer_email=None):
	"""Test method to debug order creation issues"""
	try:
		result = {
			"plan": plan,
			"customer_email": customer_email or frappe.session.user,
			"razorpay_available": RAZORPAY_AVAILABLE,
			"session_user": frappe.session.user
		}
		
		# Test customer lookup
		customer_records = frappe.get_all("BMS Customer",
			filters={"email": customer_email or frappe.session.user},
			limit=1
		)
		result["customer_found"] = len(customer_records) > 0
		if customer_records:
			result["customer_id"] = customer_records[0].name
		
		# Test plan lookup
		try:
			plan_doc = frappe.get_doc("BMS Plan", plan)
			result["plan_found"] = True
			result["plan_name"] = plan_doc.plan_name
			result["plan_amount"] = plan_doc.amount
			result["plan_visibility"] = plan_doc.plan_visibility
			
			if customer_records:
				result["plan_available"] = plan_doc.is_available_for_customer(customer_records[0].name)
		except Exception as e:
			result["plan_found"] = False
			result["plan_error"] = str(e)
		
		return result
		
	except Exception as e:
		return {"error": str(e)}

@frappe.whitelist()
def handle_razorpay_subscription_success(subscription_id, razorpay_payment_id, razorpay_signature, plan, customer_email=None):
	"""Handle successful Razorpay subscription creation"""
	try:
		frappe.log_error(f"Handling subscription success: {subscription_id}")
		
		# Set flag to prevent auto-invoice creation
		frappe.flags.via_api = True
		
		if not customer_email:
			customer_email = frappe.session.user
		
		customer = get_customer_for_user(customer_email)
		
		# Get plan details
		plan_doc = frappe.get_doc("BMS Plan", plan)
		
		# Create BMS Subscription record
		subscription_doc = frappe.new_doc("BMS Subscription")
		subscription_doc.naming_series = "SUB-.YYYY.-.MM.-.#####"
		subscription_doc.customer = customer
		subscription_doc.plan = plan
		subscription_doc.status = "Active"
		subscription_doc.start_date = today()
		subscription_doc.payment_method = "Credit Card"  # Payment method (what the customer used)
		subscription_doc.payment_gateway = "Razorpay"   # Gateway that processed it
		subscription_doc.razorpay_subscription_id = subscription_id
		subscription_doc.save(ignore_permissions=True)
		
		# Check for existing payment with same Razorpay payment ID to prevent duplicates
		existing_payment = frappe.get_all("BMS Payment",
			filters={"razorpay_payment_id": razorpay_payment_id},
			limit=1
		)
		
		if existing_payment:
			frappe.log_error(f"Payment already exists for razorpay_payment_id: {razorpay_payment_id}")
			payment_doc = frappe.get_doc("BMS Payment", existing_payment[0].name)
		else:
			# Create payment record for first payment
			payment_doc = frappe.new_doc("BMS Payment")
			payment_doc.naming_series = "PAY-.YYYY.-.MM.-.#####"
			payment_doc.customer = customer
			payment_doc.subscription = subscription_doc.name
			payment_doc.plan = plan
			payment_doc.amount = plan_doc.amount
			payment_doc.currency = plan_doc.currency
			payment_doc.payment_date = today()
			payment_doc.payment_method = "Credit Card"  # Payment method (what the customer used)
			payment_doc.payment_gateway = "Razorpay"   # Gateway that processed it
			payment_doc.status = "Completed"
			payment_doc.payment_type = "Payment"
			payment_doc.razorpay_payment_id = razorpay_payment_id
			payment_doc.razorpay_subscription_id = subscription_id
			payment_doc.notes = f"Initial subscription payment - Subscription ID: {subscription_id}"
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
			"description": f"Initial subscription for {plan_doc.billing_cycle} billing cycle",
			"quantity": 1,
			"rate": plan_doc.amount,
			"amount": plan_doc.amount
		})
		
		# Add payment link
		invoice_doc.append("payments", {
			"payment": payment_doc.name,
			"amount": plan_doc.amount,
			"payment_date": today(),
			"payment_method": "Credit Card",
			"payment_gateway": "Razorpay",
			"status": "Completed"
		})
		
		invoice_doc.save(ignore_permissions=True)
		
		return {
			"status": "success",
			"message": "Subscription created successfully",
			"subscription": subscription_doc.name,
			"payment": payment_doc.name,
			"invoice": invoice_doc.name
		}
		
	except Exception as e:
		frappe.log_error(f"Error handling subscription success: {str(e)}")
		frappe.throw(_("Error processing subscription: {0}").format(str(e)))

@frappe.whitelist(allow_guest=True)
def razorpay_webhook():
	"""Handle Razorpay webhooks for subscription events"""
	try:
		# Get webhook data
		webhook_body = frappe.request.get_data(as_text=True)
		webhook_signature = frappe.get_request_header("X-Razorpay-Signature")
		
		# Verify webhook signature
		razorpay_key_secret = "DAzu38mqdRSnkgtv83WdWe6O"
		
		import hmac
		import hashlib
		
		expected_signature = hmac.new(
			razorpay_key_secret.encode('utf-8'),
			webhook_body.encode('utf-8'),
			hashlib.sha256
		).hexdigest()
		
		if not hmac.compare_digest(expected_signature, webhook_signature):
			frappe.throw(_("Invalid webhook signature"))
		
		# Parse webhook data
		webhook_data = json.loads(webhook_body)
		event = webhook_data.get('event')
		payload = webhook_data.get('payload', {})
		
		frappe.log_error(f"Razorpay webhook received: {event}")
		
		if event == 'subscription.charged':
			handle_subscription_charged(payload)
		elif event == 'subscription.completed':
			handle_subscription_completed(payload)
		elif event == 'subscription.cancelled':
			handle_subscription_cancelled(payload)
		elif event == 'subscription.paused':
			handle_subscription_paused(payload)
		elif event == 'subscription.resumed':
			handle_subscription_resumed(payload)
		
		return {"status": "success"}
		
	except Exception as e:
		frappe.log_error(f"Webhook error: {str(e)}")
		return {"status": "error", "message": str(e)}

def handle_subscription_charged(payload):
	"""Handle successful subscription payment"""
	subscription = payload.get('subscription', {})
	payment = payload.get('payment', {})
	
	razorpay_subscription_id = subscription.get('id')
	razorpay_payment_id = payment.get('id')
	amount = payment.get('amount', 0) / 100  # Convert from paise
	
	# Find BMS subscription
	bms_subscriptions = frappe.get_all("BMS Subscription",
		filters={"razorpay_subscription_id": razorpay_subscription_id},
		limit=1
	)
	
	if not bms_subscriptions:
		frappe.log_error(f"BMS Subscription not found for Razorpay ID: {razorpay_subscription_id}")
		return
	
	bms_subscription = frappe.get_doc("BMS Subscription", bms_subscriptions[0].name)
	
	# Check for existing payment with same Razorpay payment ID to prevent duplicates
	existing_payment = frappe.get_all("BMS Payment",
		filters={"razorpay_payment_id": razorpay_payment_id},
		limit=1
	)
	
	if existing_payment:
		frappe.log_error(f"Payment already exists for razorpay_payment_id: {razorpay_payment_id}")
		return  # Skip creating duplicate payment
	
	# Create payment record
	payment_doc = frappe.new_doc("BMS Payment")
	payment_doc.naming_series = "PAY-.YYYY.-.MM.-.#####"
	payment_doc.customer = bms_subscription.customer
	payment_doc.subscription = bms_subscription.name
	payment_doc.plan = bms_subscription.plan
	payment_doc.amount = amount
	payment_doc.currency = bms_subscription.currency or "USD"
	payment_doc.payment_date = today()
	payment_doc.payment_method = bms_subscription.payment_method or "Credit Card"  # Use same method as subscription
	payment_doc.payment_gateway = bms_subscription.payment_gateway or "Razorpay"   # Use same gateway as subscription
	payment_doc.status = "Completed"
	payment_doc.payment_type = "Payment"
	payment_doc.razorpay_payment_id = razorpay_payment_id
	payment_doc.razorpay_subscription_id = razorpay_subscription_id
	payment_doc.notes = f"Recurring subscription payment - Payment ID: {razorpay_payment_id}"
	payment_doc.save(ignore_permissions=True)
	
	# Create invoice for this billing cycle
	plan_doc = frappe.get_doc("BMS Plan", bms_subscription.plan)
	
	invoice_doc = frappe.new_doc("BMS Invoice")
	invoice_doc.naming_series = "INV-.YYYY.-.MM.-.#####"
	invoice_doc.customer = bms_subscription.customer
	invoice_doc.subscription = bms_subscription.name
	invoice_doc.plan = bms_subscription.plan
	invoice_doc.amount = amount
	invoice_doc.currency = bms_subscription.currency or "USD"
	invoice_doc.invoice_date = today()
	invoice_doc.due_date = today()
	invoice_doc.status = "Paid"
	
	# Add invoice item
	invoice_doc.append("items", {
		"item_name": f"Subscription - {plan_doc.plan_name}",
		"description": f"Recurring payment for {plan_doc.billing_cycle} billing cycle",
		"quantity": 1,
		"rate": amount,
		"amount": amount
	})
	
	# Add payment link
	invoice_doc.append("payments", {
		"payment": payment_doc.name,
		"amount": amount,
		"payment_date": today(),
		"payment_method": payment_doc.payment_method,
		"payment_gateway": payment_doc.payment_gateway,
		"status": "Completed"
	})
	
	invoice_doc.save(ignore_permissions=True)
	
	frappe.log_error(f"Subscription payment processed: {payment_doc.name}")

def handle_subscription_completed(payload):
	"""Handle subscription completion"""
	subscription = payload.get('subscription', {})
	razorpay_subscription_id = subscription.get('id')
	
	# Find and update BMS subscription
	bms_subscriptions = frappe.get_all("BMS Subscription",
		filters={"razorpay_subscription_id": razorpay_subscription_id},
		limit=1
	)
	
	if bms_subscriptions:
		bms_subscription = frappe.get_doc("BMS Subscription", bms_subscriptions[0].name)
		bms_subscription.status = "Completed"
		bms_subscription.save(ignore_permissions=True)
		frappe.log_error(f"Subscription completed: {bms_subscription.name}")

def handle_subscription_cancelled(payload):
	"""Handle subscription cancellation"""
	subscription = payload.get('subscription', {})
	razorpay_subscription_id = subscription.get('id')
	
	# Find and update BMS subscription
	bms_subscriptions = frappe.get_all("BMS Subscription",
		filters={"razorpay_subscription_id": razorpay_subscription_id},
		limit=1
	)
	
	if bms_subscriptions:
		bms_subscription = frappe.get_doc("BMS Subscription", bms_subscriptions[0].name)
		bms_subscription.status = "Cancelled"
		bms_subscription.save(ignore_permissions=True)
		frappe.log_error(f"Subscription cancelled: {bms_subscription.name}")

def handle_subscription_paused(payload):
	"""Handle subscription pause"""
	subscription = payload.get('subscription', {})
	razorpay_subscription_id = subscription.get('id')
	
	# Find and update BMS subscription
	bms_subscriptions = frappe.get_all("BMS Subscription",
		filters={"razorpay_subscription_id": razorpay_subscription_id},
		limit=1
	)
	
	if bms_subscriptions:
		bms_subscription = frappe.get_doc("BMS Subscription", bms_subscriptions[0].name)
		bms_subscription.status = "Paused"
		bms_subscription.save(ignore_permissions=True)
		frappe.log_error(f"Subscription paused: {bms_subscription.name}")

def handle_subscription_resumed(payload):
	"""Handle subscription resume"""
	subscription = payload.get('subscription', {})
	razorpay_subscription_id = subscription.get('id')
	
	# Find and update BMS subscription
	bms_subscriptions = frappe.get_all("BMS Subscription",
		filters={"razorpay_subscription_id": razorpay_subscription_id},
		limit=1
	)
	
	if bms_subscriptions:
		bms_subscription = frappe.get_doc("BMS Subscription", bms_subscriptions[0].name)
		bms_subscription.status = "Active"
		bms_subscription.save(ignore_permissions=True)
		frappe.log_error(f"Subscription resumed: {bms_subscription.name}")

# Keep the old function for backward compatibility (but deprecated)
@frappe.whitelist()
def verify_payment_and_create_subscription(plan, customer_email=None, payment_id=None, order_id=None, signature=None, payment_method="Credit Card", payment_gateway="Razorpay"):
	"""Verify Razorpay payment and create subscription"""
	if not RAZORPAY_AVAILABLE:
		frappe.throw(_("Razorpay module not installed. Please install it with: pip install razorpay"))
	
	# Set flag to prevent auto-invoice creation
	frappe.flags.via_api = True
	
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
		subscription_doc.payment_gateway = payment_gateway
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
		payment_doc.payment_gateway = payment_gateway
		payment_doc.status = "Completed"
		payment_doc.payment_type = "Payment"
		payment_doc.razorpay_payment_id = payment_id
		payment_doc.razorpay_order_id = order_id
		payment_doc.notes = f"Payment via {payment_gateway} - Payment ID: {payment_id}, Order ID: {order_id}"
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
			"payment_gateway": payment_gateway,
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
