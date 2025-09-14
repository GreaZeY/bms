import frappe
import unittest
from frappe.tests.utils import FrappeTestCase

class TestBMS(FrappeTestCase):
	def setUp(self):
		"""Set up test data"""
		self.customer = self.create_test_customer()
		self.plan = self.create_test_plan()
	
	def create_test_customer(self):
		"""Create test customer"""
		customer = frappe.new_doc("BMS Customer")
		customer.customer_name = "Test Customer"
		customer.customer_type = "Individual"
		customer.email = "test@example.com"
		customer.status = "Active"
		customer.save()
		return customer
	
	def create_test_plan(self):
		"""Create test plan"""
		plan = frappe.new_doc("BMS Plan")
		plan.plan_name = "Test Plan"
		plan.plan_type = "Basic"
		plan.billing_cycle = "Monthly"
		plan.amount = 29.99
		plan.currency = "USD"
		plan.is_active = 1
		plan.save()
		return plan
	
	def test_customer_creation(self):
		"""Test customer creation"""
		self.assertEqual(self.customer.customer_name, "Test Customer")
		self.assertEqual(self.customer.customer_type, "Individual")
		self.assertEqual(self.customer.status, "Active")
	
	def test_plan_creation(self):
		"""Test plan creation"""
		self.assertEqual(self.plan.plan_name, "Test Plan")
		self.assertEqual(self.plan.plan_type, "Basic")
		self.assertEqual(self.plan.amount, 29.99)
	
	def test_subscription_creation(self):
		"""Test subscription creation"""
		subscription = frappe.new_doc("BMS Subscription")
		subscription.customer = self.customer.name
		subscription.plan = self.plan.name
		subscription.start_date = frappe.utils.today()
		subscription.status = "Active"
		subscription.save()
		
		self.assertEqual(subscription.customer, self.customer.name)
		self.assertEqual(subscription.plan, self.plan.name)
		self.assertEqual(subscription.status, "Active")
	
	def test_invoice_creation(self):
		"""Test invoice creation"""
		subscription = frappe.new_doc("BMS Subscription")
		subscription.customer = self.customer.name
		subscription.plan = self.plan.name
		subscription.start_date = frappe.utils.today()
		subscription.status = "Active"
		subscription.save()
		
		invoice = frappe.new_doc("BMS Invoice")
		invoice.customer = self.customer.name
		invoice.subscription = subscription.name
		invoice.plan = self.plan.name
		invoice.amount = 29.99
		invoice.currency = "USD"
		invoice.invoice_date = frappe.utils.today()
		invoice.due_date = frappe.utils.today()
		invoice.status = "Draft"
		invoice.save()
		
		self.assertEqual(invoice.customer, self.customer.name)
		self.assertEqual(invoice.amount, 29.99)
		self.assertEqual(invoice.status, "Draft")
	
	def test_payment_creation(self):
		"""Test payment creation"""
		subscription = frappe.new_doc("BMS Subscription")
		subscription.customer = self.customer.name
		subscription.plan = self.plan.name
		subscription.start_date = frappe.utils.today()
		subscription.status = "Active"
		subscription.save()
		
		payment = frappe.new_doc("BMS Payment")
		payment.customer = self.customer.name
		payment.subscription = subscription.name
		payment.plan = self.plan.name
		payment.amount = 29.99
		payment.currency = "USD"
		payment.payment_type = "Payment"
		payment.payment_date = frappe.utils.today()
		payment.status = "Completed"
		payment.payment_method = "Credit Card"
		payment.save()
		
		self.assertEqual(payment.customer, self.customer.name)
		self.assertEqual(payment.amount, 29.99)
		self.assertEqual(payment.status, "Completed")
	
	def test_subscription_cancellation(self):
		"""Test subscription cancellation"""
		subscription = frappe.new_doc("BMS Subscription")
		subscription.customer = self.customer.name
		subscription.plan = self.plan.name
		subscription.start_date = frappe.utils.today()
		subscription.status = "Active"
		subscription.save()
		
		# Cancel subscription
		subscription.cancel_subscription("Test cancellation")
		
		self.assertEqual(subscription.status, "Cancelled")
		self.assertIsNotNone(subscription.cancellation_date)
		self.assertEqual(subscription.cancellation_reason, "Test cancellation")
	
	def test_refund_processing(self):
		"""Test refund processing"""
		subscription = frappe.new_doc("BMS Subscription")
		subscription.customer = self.customer.name
		subscription.plan = self.plan.name
		subscription.start_date = frappe.utils.today()
		subscription.status = "Active"
		subscription.save()
		
		payment = frappe.new_doc("BMS Payment")
		payment.customer = self.customer.name
		payment.subscription = subscription.name
		payment.plan = self.plan.name
		payment.amount = 29.99
		payment.currency = "USD"
		payment.payment_type = "Payment"
		payment.payment_date = frappe.utils.today()
		payment.status = "Completed"
		payment.payment_method = "Credit Card"
		payment.save()
		
		# Process refund
		refund = payment.process_refund("Test refund")
		
		self.assertEqual(refund.payment_type, "Refund")
		self.assertEqual(refund.amount, -29.99)
		self.assertEqual(payment.status, "Refunded")
	
	def tearDown(self):
		"""Clean up test data"""
		frappe.db.rollback()

if __name__ == "__main__":
	unittest.main()
