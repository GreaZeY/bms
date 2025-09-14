import frappe
from frappe.model.document import Document
from frappe import _

class BMSPlanCustomer(Document):
	def validate(self):
		self.set_customer_name()
	
	def set_customer_name(self):
		"""Set customer name from customer link"""
		if self.customer:
			customer_doc = frappe.get_doc("BMS Customer", self.customer)
			self.customer_name = customer_doc.customer_name
