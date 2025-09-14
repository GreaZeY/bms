import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta

class BMSInvoice(Document):
	def validate(self):
		self.validate_dates()
		self.set_customer_name()
		self.set_plan_name()
		self.calculate_total_amount()
		self.validate_amount()
	
	def validate_dates(self):
		"""Validate invoice dates"""
		if self.invoice_date and self.due_date:
			if self.invoice_date > self.due_date:
				frappe.throw(_("Invoice date cannot be after due date"))
	
	def set_customer_name(self):
		"""Set customer name from customer link"""
		if self.customer:
			customer_doc = frappe.get_doc("BMS Customer", self.customer)
			self.customer_name = customer_doc.customer_name
	
	def set_plan_name(self):
		"""Set plan name from plan link"""
		if self.plan:
			plan_doc = frappe.get_doc("BMS Plan", self.plan)
			self.plan_name = plan_doc.plan_name
	
	def calculate_total_amount(self):
		"""Calculate total amount including tax"""
		self.total_amount = self.amount + (self.tax_amount or 0)
	
	def validate_amount(self):
		"""Validate invoice amount"""
		if self.amount <= 0:
			frappe.throw(_("Invoice amount must be greater than 0"))
	
	def on_update(self):
		"""Handle invoice updates"""
		if self.has_value_changed("status"):
			self.handle_status_change()
	
	def handle_status_change(self):
		"""Handle status changes"""
		if self.status == "Paid":
			self.create_payment_record()
		elif self.status == "Overdue":
			self.send_overdue_notification()
	
	def create_payment_record(self):
		"""Create payment record when invoice is marked as paid"""
		if not self.subscription:
			return
		
		# Check if payment record already exists
		existing_payment = frappe.get_all("BMS Payment",
			filters={
				"invoice": self.name,
				"status": "Completed"
			}
		)
		
		if not existing_payment:
			payment_doc = frappe.new_doc("BMS Payment")
			payment_doc.customer = self.customer
			payment_doc.subscription = self.subscription
			payment_doc.plan = self.plan
			payment_doc.invoice = self.name
			payment_doc.amount = self.total_amount
			payment_doc.currency = self.currency
			payment_doc.payment_type = "Payment"
			payment_doc.status = "Completed"
			payment_doc.payment_date = frappe.utils.today()
			payment_doc.save(ignore_permissions=True)
	
	def send_overdue_notification(self):
		"""Send overdue notification to customer"""
		# This would integrate with email system
		pass
	
	def mark_as_sent(self):
		"""Mark invoice as sent"""
		self.status = "Sent"
		self.save(ignore_permissions=True)
	
	def mark_as_paid(self):
		"""Mark invoice as paid"""
		self.status = "Paid"
		self.save(ignore_permissions=True)
	
	def cancel_invoice(self):
		"""Cancel invoice"""
		if self.status == "Paid":
			frappe.throw(_("Cannot cancel paid invoice"))
		
		self.status = "Cancelled"
		self.save(ignore_permissions=True)
	
	def generate_pdf(self):
		"""Generate PDF for invoice"""
		# This would integrate with Frappe's print format system
		pass
	
	def get_payment_status(self):
		"""Get payment status"""
		paid_amount = 0
		if self.payments:
			for payment in self.payments:
				if payment.status == "Completed":
					paid_amount += payment.amount
		
		remaining_amount = self.total_amount - paid_amount
		
		return {
			"total_amount": self.total_amount,
			"paid_amount": paid_amount,
			"remaining_amount": remaining_amount,
			"is_fully_paid": remaining_amount <= 0
		}
	
	def add_payment(self, amount, payment_method, reference=None):
		"""Add payment to invoice"""
		payment_row = self.append("payments", {})
		payment_row.amount = amount
		payment_row.payment_method = payment_method
		payment_row.reference = reference
		payment_row.payment_date = frappe.utils.today()
		payment_row.status = "Completed"
		
		self.save(ignore_permissions=True)
		
		# Check if fully paid
		payment_status = self.get_payment_status()
		if payment_status["is_fully_paid"]:
			self.status = "Paid"
			self.save(ignore_permissions=True)
