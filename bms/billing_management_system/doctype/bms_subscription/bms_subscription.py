import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta
import calendar

class BMSSubscription(Document):
	def validate(self):
		self.validate_dates()
		self.validate_plan_availability()
		self.set_plan_details()
		self.calculate_end_date()
		self.set_customer_name()
	
	def validate_dates(self):
		"""Validate subscription dates"""
		if self.start_date and self.end_date:
			if self.start_date >= self.end_date:
				frappe.throw(_("Start date must be before end date"))
	
	def validate_plan_availability(self):
		"""Validate that the plan is available for the customer"""
		if self.plan and self.customer:
			plan_doc = frappe.get_doc("BMS Plan", self.plan)
			if not plan_doc.is_available_for_customer(self.customer):
				frappe.throw(_("This plan is not available for the selected customer"))
	
	def set_plan_details(self):
		"""Set plan details from selected plan"""
		if self.plan:
			plan_doc = frappe.get_doc("BMS Plan", self.plan)
			self.plan_name = plan_doc.plan_name
			self.amount = plan_doc.amount
			self.currency = plan_doc.currency
			self.billing_cycle = plan_doc.billing_cycle
			self.auto_renewal = plan_doc.auto_renewal
			
			# Set trial end date if trial period exists
			if plan_doc.trial_period_days > 0 and not self.trial_end_date:
				# Convert start_date to date object if it's a string
				start_date = self.start_date
				if isinstance(start_date, str):
					start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
				self.trial_end_date = start_date + timedelta(days=plan_doc.trial_period_days)
	
	def calculate_end_date(self):
		"""Calculate end date based on billing cycle"""
		if self.start_date and self.billing_cycle and not self.end_date:
			# Convert start_date to date object if it's a string
			start_date = self.start_date
			if isinstance(start_date, str):
				start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
			
			if self.billing_cycle == "Monthly":
				self.end_date = self.add_months(start_date, 1)
			elif self.billing_cycle == "Quarterly":
				self.end_date = self.add_months(start_date, 3)
			elif self.billing_cycle == "Semi-Annual":
				self.end_date = self.add_months(start_date, 6)
			elif self.billing_cycle == "Annual":
				self.end_date = self.add_months(start_date, 12)
			elif self.billing_cycle == "One-time":
				self.end_date = start_date
	
	def set_customer_name(self):
		"""Set customer name from customer link"""
		if self.customer:
			customer_doc = frappe.get_doc("BMS Customer", self.customer)
			self.customer_name = customer_doc.customer_name
	
	def add_months(self, date, months):
		"""Add months to a date"""
		# Convert string to date object if needed
		if isinstance(date, str):
			date = datetime.strptime(date, '%Y-%m-%d').date()
		
		month = date.month - 1 + months
		year = date.year + month // 12
		month = month % 12 + 1
		day = min(date.day, calendar.monthrange(year, month)[1])
		return datetime(year, month, day).date()
	
	def after_insert(self):
		"""Handle new subscription creation"""
		# Create initial invoice when subscription is created and active
		if self.status in ["Active", "Trial"]:
			try:
				frappe.log_error(f"Creating invoice for new subscription {self.name} with status {self.status}")
				self.create_invoice()
			except Exception as e:
				frappe.log_error(f"Error in after_insert for subscription {self.name}: {str(e)}")
	
	def on_update(self):
		"""Handle subscription updates"""
		if self.has_value_changed("status"):
			self.handle_status_change()
	
	def handle_status_change(self):
		"""Handle status changes"""
		if self.status == "Cancelled":
			self.cancellation_date = frappe.utils.today()
			self.auto_renewal = 0
		elif self.status == "Active":
			self.calculate_next_billing_date()
	
	def calculate_next_billing_date(self):
		"""Calculate next billing date"""
		if self.billing_cycle and self.end_date:
			# Convert end_date to date object if it's a string
			end_date = self.end_date
			if isinstance(end_date, str):
				end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
			
			if self.billing_cycle == "Monthly":
				self.next_billing_date = self.add_months(end_date, 1)
			elif self.billing_cycle == "Quarterly":
				self.next_billing_date = self.add_months(end_date, 3)
			elif self.billing_cycle == "Semi-Annual":
				self.next_billing_date = self.add_months(end_date, 6)
			elif self.billing_cycle == "Annual":
				self.next_billing_date = self.add_months(end_date, 12)
	
	def cancel_subscription(self, reason=None):
		"""Cancel subscription"""
		if self.status in ["Cancelled", "Expired"]:
			frappe.throw(_("Subscription is already cancelled or expired"))
		
		self.status = "Cancelled"
		self.cancellation_date = frappe.utils.today()
		self.cancellation_reason = reason or "Cancelled by user"
		self.auto_renewal = 0
		self.save(ignore_permissions=True)
		
		# Create refund request if applicable
		self.create_refund_request()
	
	def create_refund_request(self):
		"""Create refund request for cancelled subscription"""
		# Calculate refund amount based on unused period
		if self.amount and self.start_date and self.end_date:
			days_used = (frappe.utils.today() - self.start_date).days
			total_days = (self.end_date - self.start_date).days
			
			if days_used < total_days:
				unused_ratio = (total_days - days_used) / total_days
				self.refund_amount = self.amount * unused_ratio
				self.refund_status = "Requested"
				
				# Create payment record for refund
				payment_doc = frappe.new_doc("BMS Payment")
				payment_doc.customer = self.customer
				payment_doc.subscription = self.name
				payment_doc.plan = self.plan
				payment_doc.amount = -self.refund_amount  # Negative for refund
				payment_doc.payment_type = "Refund"
				payment_doc.status = "Pending"
				payment_doc.payment_method = self.payment_method
				payment_doc.save(ignore_permissions=True)
	
	def renew_subscription(self):
		"""Renew subscription"""
		if self.status != "Active":
			frappe.throw(_("Only active subscriptions can be renewed"))
		
		# Calculate new dates
		old_end_date = self.end_date
		if isinstance(old_end_date, str):
			old_end_date = datetime.strptime(old_end_date, '%Y-%m-%d').date()
		
		self.start_date = old_end_date + timedelta(days=1)
		self.calculate_end_date()
		self.calculate_next_billing_date()
		
		# Create new invoice
		self.create_invoice()
		
		self.save(ignore_permissions=True)
	
	@frappe.whitelist()
	def create_invoice(self):
		"""Create invoice for subscription"""
		try:
			# Check if invoice already exists for this subscription
			existing_invoice = frappe.get_all("BMS Invoice", 
				filters={"subscription": self.name, "status": ["!=", "Cancelled"]},
				limit=1
			)
			
			if existing_invoice:
				frappe.msgprint(_("Invoice already exists for this subscription"))
				return existing_invoice[0].name
			
			# Create new invoice
			invoice_doc = frappe.new_doc("BMS Invoice")
			invoice_doc.customer = self.customer
			invoice_doc.subscription = self.name
			invoice_doc.plan = self.plan
			invoice_doc.amount = self.amount
			invoice_doc.currency = self.currency
			invoice_doc.invoice_date = frappe.utils.today()
			invoice_doc.due_date = self.start_date
			invoice_doc.status = "Draft"
			
			# Add invoice item
			invoice_doc.append("items", {
				"item_name": f"Subscription - {self.plan_name}",
				"description": f"Subscription for {self.billing_cycle} billing cycle",
				"quantity": 1,
				"rate": self.amount,
				"amount": self.amount
			})
			
			invoice_doc.save(ignore_permissions=True)
			frappe.msgprint(_("Invoice {0} created successfully").format(invoice_doc.name))
			
			return invoice_doc.name
		except Exception as e:
			frappe.log_error(f"Error creating invoice for subscription {self.name}: {str(e)}")
			frappe.throw(_("Error creating invoice: {0}").format(str(e)))
	
	def get_usage_summary(self):
		"""Get usage summary for subscription"""
		return {
			"start_date": self.start_date,
			"end_date": self.end_date,
			"days_remaining": (self.end_date - frappe.utils.today()).days if self.end_date else 0,
			"amount": self.amount,
			"status": self.status
		}

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_available_plans_for_subscription(doctype, txt, searchfield, start, page_len, filters):
	"""Get available plans for subscription creation"""
	customer = filters.get('customer') if filters else None
	
	if not customer:
		return []
	
	# Get all active plans
	all_plans = frappe.get_all("BMS Plan",
		filters={"is_active": 1},
		fields=["name", "plan_name"]
	)
	
	available_plans = []
	
	for plan in all_plans:
		plan_doc = frappe.get_doc("BMS Plan", plan.name)
		if plan_doc.is_available_for_customer(customer):
			# Check if the plan matches the search text
			if txt and txt.lower() not in plan.plan_name.lower():
				continue
			available_plans.append([plan.name, plan.plan_name])
	
	return available_plans

@frappe.whitelist()
def create_invoice_for_subscription(subscription):
	"""Create invoice for a subscription (standalone function)"""
	subscription_doc = frappe.get_doc("BMS Subscription", subscription)
	return subscription_doc.create_invoice()
