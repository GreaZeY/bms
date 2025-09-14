import frappe
from frappe.model.document import Document
from frappe import _

class BMSCustomer(Document):
	def validate(self):
		self.validate_email()
		self.validate_company_fields()
		self.set_creation_info()
	
	def validate_email(self):
		"""Validate email format"""
		if self.email and not self.is_valid_email(self.email):
			frappe.throw(_("Please enter a valid email address"))
	
	def is_valid_email(self, email):
		"""Check if email is valid"""
		import re
		pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
		return re.match(pattern, email) is not None
	
	def validate_company_fields(self):
		"""Validate company-specific fields"""
		if self.customer_type == "Company":
			if not self.company_name:
				frappe.throw(_("Company Name is required for Company type customers"))
			if not self.contact_person:
				frappe.throw(_("Contact Person is required for Company type customers"))
	
	def set_creation_info(self):
		"""Set creation and modification info"""
		if self.is_new():
			self.created_by = frappe.session.user
			self.creation_date = frappe.utils.now()
		else:
			self.modified_by = frappe.session.user
			self.modified_date = frappe.utils.now()
	
	def on_update(self):
		"""Update related documents when customer is updated"""
		self.update_related_subscriptions()
	
	def update_related_subscriptions(self):
		"""Update customer name in related subscriptions"""
		subscriptions = frappe.get_all("BMS Subscription", 
			filters={"customer": self.name}, 
			fields=["name"])
		
		for subscription in subscriptions:
			doc = frappe.get_doc("BMS Subscription", subscription.name)
			doc.customer_name = self.customer_name
			doc.save(ignore_permissions=True)
	
	def get_active_subscriptions(self):
		"""Get all active subscriptions for this customer"""
		return frappe.get_all("BMS Subscription",
			filters={
				"customer": self.name,
				"status": "Active"
			},
			fields=["name", "plan", "start_date", "end_date", "amount"]
		)
	
	def get_total_revenue(self):
		"""Calculate total revenue from this customer"""
		payments = frappe.get_all("BMS Payment",
			filters={
				"customer": self.name,
				"status": "Completed"
			},
			fields=["amount"]
		)
		return sum(payment.amount for payment in payments)
