import frappe
from frappe.model.document import Document
from frappe import _

class BMSPayment(Document):
	def validate(self):
		self.validate_amount()
		self.set_customer_name()
		self.validate_refund_amount()
	
	def validate_amount(self):
		"""Validate payment amount"""
		if self.amount == 0:
			frappe.throw(_("Payment amount cannot be zero"))
		
		# For refunds, amount should be negative
		if self.payment_type == "Refund" and self.amount > 0:
			frappe.throw(_("Refund amount should be negative"))
		
		# For payments, amount should be positive
		if self.payment_type == "Payment" and self.amount < 0:
			frappe.throw(_("Payment amount should be positive"))
	
	def set_customer_name(self):
		"""Set customer name from customer link"""
		if self.customer:
			customer_doc = frappe.get_doc("BMS Customer", self.customer)
			self.customer_name = customer_doc.customer_name
	
	def validate_refund_amount(self):
		"""Validate refund amount against original payment"""
		if self.payment_type == "Refund" and self.subscription:
			# Get total payments for this subscription
			total_payments = frappe.get_all("BMS Payment",
				filters={
					"subscription": self.subscription,
					"payment_type": "Payment",
					"status": "Completed"
				},
				fields=["amount"]
			)
			
			total_refunds = frappe.get_all("BMS Payment",
				filters={
					"subscription": self.subscription,
					"payment_type": "Refund",
					"status": "Completed"
				},
				fields=["amount"]
			)
			
			total_paid = sum(payment.amount for payment in total_payments)
			total_refunded = sum(refund.amount for refund in total_refunds)
			
			# Refund amount should not exceed total paid
			if abs(self.amount) > (total_paid - total_refunded):
				frappe.throw(_("Refund amount cannot exceed total payments made"))
	
	def on_update(self):
		"""Handle payment updates"""
		if self.has_value_changed("status"):
			self.handle_status_change()
	
	def handle_status_change(self):
		"""Handle status changes"""
		if self.status == "Completed":
			self.update_subscription_status()
			self.update_invoice_status()
		elif self.status == "Failed":
			self.handle_payment_failure()
	
	def update_subscription_status(self):
		"""Update subscription status based on payment"""
		if self.subscription and self.payment_type == "Payment":
			subscription_doc = frappe.get_doc("BMS Subscription", self.subscription)
			
			# If subscription is in trial, activate it
			if subscription_doc.status == "Trial":
				subscription_doc.status = "Active"
				subscription_doc.save(ignore_permissions=True)
	
	def update_invoice_status(self):
		"""Update invoice status based on payment"""
		if self.invoice and self.payment_type == "Payment":
			invoice_doc = frappe.get_doc("BMS Invoice", self.invoice)
			
			# Check if invoice is fully paid
			payment_status = invoice_doc.get_payment_status()
			if payment_status["is_fully_paid"]:
				invoice_doc.status = "Paid"
				invoice_doc.save(ignore_permissions=True)
	
	def handle_payment_failure(self):
		"""Handle payment failure"""
		if self.subscription:
			subscription_doc = frappe.get_doc("BMS Subscription", self.subscription)
			
			# Suspend subscription if payment fails
			if subscription_doc.status == "Active":
				subscription_doc.status = "Suspended"
				subscription_doc.save(ignore_permissions=True)
	
	def process_refund(self, reason=None):
		"""Process refund"""
		if self.payment_type != "Payment":
			frappe.throw(_("Only payment records can be refunded"))
		
		if self.status != "Completed":
			frappe.throw(_("Only completed payments can be refunded"))
		
		# Create refund record
		refund_doc = frappe.new_doc("BMS Payment")
		refund_doc.customer = self.customer
		refund_doc.subscription = self.subscription
		refund_doc.plan = self.plan
		refund_doc.invoice = self.invoice
		refund_doc.payment_type = "Refund"
		refund_doc.amount = -self.amount  # Negative amount for refund
		refund_doc.currency = self.currency
		refund_doc.payment_date = frappe.utils.today()
		refund_doc.status = "Pending"
		refund_doc.payment_method = self.payment_method
		refund_doc.refund_reason = reason
		refund_doc.save(ignore_permissions=True)
		
		# Update original payment status
		self.status = "Refunded"
		self.refund_date = frappe.utils.today()
		self.save(ignore_permissions=True)
		
		return refund_doc
	
	def get_payment_summary(self):
		"""Get payment summary"""
		return {
			"amount": self.amount,
			"currency": self.currency,
			"payment_type": self.payment_type,
			"status": self.status,
			"payment_date": self.payment_date,
			"payment_method": self.payment_method
		}
	
	def can_be_refunded(self):
		"""Check if payment can be refunded"""
		return (
			self.payment_type == "Payment" and
			self.status == "Completed" and
			not self.refund_date
		)
