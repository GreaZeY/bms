import frappe
from frappe.model.document import Document
from frappe import _

class BMSInvoiceItem(Document):
	def validate(self):
		self.validate_item_name()
		self.validate_quantity()
		self.validate_rate()
		self.calculate_amount()
	
	def validate_item_name(self):
		"""Validate item name"""
		if not self.item_name:
			frappe.throw(_("Item name is required"))
	
	def validate_quantity(self):
		"""Validate quantity"""
		if not self.quantity or self.quantity <= 0:
			frappe.throw(_("Quantity must be greater than 0"))
	
	def validate_rate(self):
		"""Validate rate"""
		if not self.rate or self.rate < 0:
			frappe.throw(_("Rate must be greater than or equal to 0"))
	
	def calculate_amount(self):
		"""Calculate amount based on quantity and rate"""
		if self.quantity and self.rate:
			self.amount = self.quantity * self.rate
		else:
			self.amount = 0
	
	def get_item_summary(self):
		"""Get item summary"""
		summary = f"{self.item_name}"
		
		if self.quantity and self.quantity != 1:
			summary += f" (Qty: {self.quantity})"
		
		if self.rate:
			summary += f" @ {self.rate}"
		
		if self.amount:
			summary += f" = {self.amount}"
		
		return summary
