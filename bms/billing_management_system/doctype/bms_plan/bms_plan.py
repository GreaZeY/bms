import frappe
from frappe.model.document import Document
from frappe import _

class BMSPlan(Document):
	def validate(self):
		self.validate_amount()
		self.validate_trial_period()
		self.validate_target_customers()
	
	def validate_amount(self):
		"""Validate plan amount"""
		if self.amount <= 0:
			frappe.throw(_("Plan amount must be greater than 0"))
	
	def validate_trial_period(self):
		"""Validate trial period"""
		if self.trial_period_days < 0:
			frappe.throw(_("Trial period cannot be negative"))
	
	
	def on_update(self):
		"""Update related subscriptions when plan is updated"""
		if self.has_value_changed("amount") or self.has_value_changed("billing_cycle"):
			self.update_related_subscriptions()
	
	def update_related_subscriptions(self):
		"""Update amount in active subscriptions"""
		active_subscriptions = frappe.get_all("BMS Subscription",
			filters={
				"plan": self.name,
				"status": "Active"
			},
			fields=["name"]
		)
		
		for subscription in active_subscriptions:
			doc = frappe.get_doc("BMS Subscription", subscription.name)
			doc.amount = self.amount
			doc.billing_cycle = self.billing_cycle
			doc.save(ignore_permissions=True)
	
	def get_active_subscriptions_count(self):
		"""Get count of active subscriptions for this plan"""
		return frappe.db.count("BMS Subscription", {
			"plan": self.name,
			"status": "Active"
		})
	
	def get_total_revenue(self):
		"""Calculate total revenue from this plan"""
		payments = frappe.get_all("BMS Payment",
			filters={
				"plan": self.name,
				"status": "Completed"
			},
			fields=["amount"]
		)
		return sum(payment.amount for payment in payments)
	
	def validate_target_customers(self):
		"""Validate target customers"""
		if self.plan_visibility == "Specific Customers":
			if not self.target_customers:
				frappe.throw(_("Please select at least one customer for specific customer plans"))
	
	def get_available_customers(self):
		"""Get list of customers who can see this plan"""
		if self.plan_visibility == "All Customers":
			# Return all active customers
			return frappe.get_all("BMS Customer",
				filters={"status": "Active"},
				fields=["name", "customer_name"]
			)
		else:
			# Return only specific customers
			customers = []
			if self.target_customers:
				for customer in self.target_customers:
					customers.append({
						"name": customer.customer,
						"customer_name": customer.customer_name
					})
			return customers
	
	def is_available_for_customer(self, customer):
		"""Check if plan is available for specific customer"""
		if self.plan_visibility == "All Customers":
			return True
		elif self.plan_visibility == "Specific Customers":
			if self.target_customers:
				for target_customer in self.target_customers:
					if target_customer.customer == customer:
						return True
		return False
	
	def can_be_deleted(self):
		"""Check if plan can be deleted"""
		active_subscriptions = self.get_active_subscriptions_count()
		if active_subscriptions > 0:
			frappe.throw(_("Cannot delete plan with active subscriptions. Please deactivate it instead."))
		return True

@frappe.whitelist()
def get_pricing_plans_view_data():
	"""Get data for pricing plans view"""
	plans = frappe.get_all("BMS Plan",
		filters={"is_active": 1},
		fields=[
			"name", "plan_name", "plan_description", "amount", 
			"currency", "billing_cycle", "plan_visibility", 
			"trial_period_days", "max_users", "storage_limit_gb", 
			"api_calls_limit"
		],
		order_by="amount asc"
	)
	
	# Get target customers for each plan
	for plan in plans:
		if plan.plan_visibility == "Specific Customers":
			target_customers = frappe.get_all("BMS Plan Customer",
				filters={"parent": plan.name},
				fields=["customer", "customer_name"]
			)
			plan.target_customers = target_customers
		else:
			plan.target_customers = []
	
	return plans
