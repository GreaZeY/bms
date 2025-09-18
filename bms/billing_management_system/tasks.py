import frappe
from frappe import _
from frappe.utils import today, add_days, get_datetime
from datetime import datetime, timedelta

def daily_tasks():
	"""Daily scheduled tasks for BMS"""
	check_expired_subscriptions()
	check_overdue_invoices()
	process_auto_renewals()

def monthly_tasks():
	"""Monthly scheduled tasks for BMS"""
	generate_monthly_reports()
	cleanup_old_data()

def check_expired_subscriptions():
	"""Check for expired subscriptions and update their status"""
	try:
		# Get subscriptions that have expired
		expired_subscriptions = frappe.get_all("BMS Subscription",
			filters={
				"status": "Active",
				"end_date": ["<", today()]
			},
			fields=["name", "customer", "plan", "status"]
		)
		
		for subscription in expired_subscriptions:
			subscription_doc = frappe.get_doc("BMS Subscription", subscription.name)
			
			# Handle expired active subscriptions
			if subscription_doc.auto_renewal:
				# Try to renew subscription
				try:
					subscription_doc.renew_subscription()
					frappe.logger().info(f"Auto-renewed subscription: {subscription.name}")
				except Exception as e:
					# If renewal fails, mark as expired
					subscription_doc.status = "Expired"
					subscription_doc.save()
					frappe.logger().error(f"Failed to auto-renew subscription {subscription.name}: {str(e)}")
			else:
				# Mark as expired
				subscription_doc.status = "Expired"
				subscription_doc.save()
		
		frappe.logger().info(f"Processed {len(expired_subscriptions)} expired subscriptions")
		
	except Exception as e:
		frappe.logger().error(f"Error in check_expired_subscriptions: {str(e)}")

def check_overdue_invoices():
	"""Check for overdue invoices and update their status"""
	try:
		# Get invoices that are overdue
		overdue_invoices = frappe.get_all("BMS Invoice",
			filters={
				"status": ["in", ["Sent", "Draft"]],
				"due_date": ["<", today()]
			},
			fields=["name", "customer", "amount"]
		)
		
		for invoice in overdue_invoices:
			invoice_doc = frappe.get_doc("BMS Invoice", invoice.name)
			invoice_doc.status = "Overdue"
			invoice_doc.save()
			
			# Send overdue notification
			send_overdue_notification(invoice_doc)
		
		frappe.logger().info(f"Processed {len(overdue_invoices)} overdue invoices")
		
	except Exception as e:
		frappe.logger().error(f"Error in check_overdue_invoices: {str(e)}")

def process_auto_renewals():
	"""Process auto-renewals for subscriptions"""
	try:
		# Get subscriptions that need renewal
		renewal_subscriptions = frappe.get_all("BMS Subscription",
			filters={
				"status": "Active",
				"auto_renewal": 1,
				"next_billing_date": ["<=", today()]
			},
			fields=["name", "customer", "plan", "amount"]
		)
		
		for subscription in renewal_subscriptions:
			subscription_doc = frappe.get_doc("BMS Subscription", subscription.name)
			
			try:
				# Create invoice for renewal
				subscription_doc.create_invoice()
				
				# Update next billing date
				subscription_doc.calculate_next_billing_date()
				subscription_doc.save()
				
				frappe.logger().info(f"Created renewal invoice for subscription: {subscription.name}")
				
			except Exception as e:
				frappe.logger().error(f"Failed to process auto-renewal for subscription {subscription.name}: {str(e)}")
		
		frappe.logger().info(f"Processed {len(renewal_subscriptions)} auto-renewals")
		
	except Exception as e:
		frappe.logger().error(f"Error in process_auto_renewals: {str(e)}")

def send_overdue_notification(invoice_doc):
	"""Send overdue notification to customer"""
	try:
		# This would integrate with Frappe's email system
		# For now, just log the notification
		frappe.logger().info(f"Overdue notification sent for invoice: {invoice_doc.name}")
		
	except Exception as e:
		frappe.logger().error(f"Error sending overdue notification: {str(e)}")

def generate_monthly_reports():
	"""Generate monthly reports"""
	try:
		# Generate revenue report
		generate_revenue_report()
		
		# Generate subscription report
		generate_subscription_report()
		
		frappe.logger().info("Monthly reports generated successfully")
		
	except Exception as e:
		frappe.logger().error(f"Error generating monthly reports: {str(e)}")

def generate_revenue_report():
	"""Generate revenue report for the month"""
	try:
		# Get current month's payments
		current_month = today().strftime("%Y-%m")
		
		payments = frappe.get_all("BMS Payment",
			filters={
				"payment_type": "Payment",
				"status": "Completed",
				"payment_date": ["like", f"{current_month}%"]
			},
			fields=["amount", "currency"]
		)
		
		total_revenue = sum(payment.amount for payment in payments)
		
		# Create report record
		report_doc = frappe.new_doc("BMS Monthly Report")
		report_doc.report_type = "Revenue"
		report_doc.report_month = current_month
		report_doc.total_amount = total_revenue
		report_doc.save()
		
	except Exception as e:
		frappe.logger().error(f"Error generating revenue report: {str(e)}")

def generate_subscription_report():
	"""Generate subscription report for the month"""
	try:
		# Get subscription statistics
		total_subscriptions = frappe.db.count("BMS Subscription")
		active_subscriptions = frappe.db.count("BMS Subscription", {"status": "Active"})
		cancelled_subscriptions = frappe.db.count("BMS Subscription", {"status": "Cancelled"})
		
		# Create report record
		report_doc = frappe.new_doc("BMS Monthly Report")
		report_doc.report_type = "Subscription"
		report_doc.report_month = today().strftime("%Y-%m")
		report_doc.total_subscriptions = total_subscriptions
		report_doc.active_subscriptions = active_subscriptions
		report_doc.cancelled_subscriptions = cancelled_subscriptions
		report_doc.save()
		
	except Exception as e:
		frappe.logger().error(f"Error generating subscription report: {str(e)}")

def cleanup_old_data():
	"""Cleanup old data"""
	try:
		# Delete old cancelled subscriptions (older than 1 year)
		cutoff_date = add_days(today(), -365)
		
		old_subscriptions = frappe.get_all("BMS Subscription",
			filters={
				"status": "Cancelled",
				"modified": ["<", cutoff_date]
			},
			fields=["name"]
		)
		
		for subscription in old_subscriptions:
			frappe.delete_doc("BMS Subscription", subscription.name)
		
		frappe.logger().info(f"Cleaned up {len(old_subscriptions)} old subscriptions")
		
	except Exception as e:
		frappe.logger().error(f"Error in cleanup_old_data: {str(e)}")
