import frappe
from frappe.model.document import Document
from frappe import _

class BMSInvoicePayment(Document):
	def validate(self):
		self.validate_payment_date()
		self.validate_amount()
		self.validate_payment_method()
		self.validate_status()
	
	def validate_payment_date(self):
		"""Validate payment date"""
		if not self.payment_date:
			frappe.throw(_("Payment date is required"))
	
	def validate_amount(self):
		"""Validate amount"""
		if not self.amount or self.amount <= 0:
			frappe.throw(_("Amount must be greater than 0"))
	
	def validate_payment_method(self):
		"""Validate payment method"""
		if not self.payment_method:
			frappe.throw(_("Payment method is required"))
		
		valid_methods = [
			"Credit Card", "Debit Card", "Bank Transfer", "UPI", "Wallet", "Cash", "Other"
		]
		
		if self.payment_method not in valid_methods:
			frappe.throw(_("Invalid payment method. Must be one of: {0}").format(", ".join(valid_methods)))
	
	def validate_status(self):
		"""Validate status"""
		if not self.status:
			frappe.throw(_("Status is required"))
		
		valid_statuses = ["Pending", "Completed", "Failed", "Cancelled"]
		
		if self.status not in valid_statuses:
			frappe.throw(_("Invalid status. Must be one of: {0}").format(", ".join(valid_statuses)))
	
	def get_payment_summary(self):
		"""Get payment summary"""
		summary = f"{self.payment_method}: {self.amount}"
		
		if self.reference:
			summary += f" (Ref: {self.reference})"
		
		summary += f" - {self.status}"
		
		return summary
	
	def is_completed(self):
		"""Check if payment is completed"""
		return self.status == "Completed"
	
	def is_pending(self):
		"""Check if payment is pending"""
		return self.status == "Pending"
	
	def is_failed(self):
		"""Check if payment failed"""
		return self.status == "Failed"
