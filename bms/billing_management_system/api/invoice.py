import frappe
from frappe import _
from frappe.utils import today
import json

@frappe.whitelist()
def create_invoice(customer, subscription, amount, currency):
	"""Create an invoice"""
	try:
		# Validate inputs
		if not frappe.db.exists("BMS Customer", customer):
			frappe.throw(_("Customer not found"))
		
		if not frappe.db.exists("BMS Subscription", subscription):
			frappe.throw(_("Subscription not found"))
		
		# Get subscription details
		subscription_doc = frappe.get_doc("BMS Subscription", subscription)
		
		# Create invoice
		invoice_doc = frappe.new_doc("BMS Invoice")
		invoice_doc.customer = customer
		invoice_doc.subscription = subscription
		invoice_doc.plan = subscription_doc.plan
		invoice_doc.amount = amount
		invoice_doc.currency = currency
		invoice_doc.invoice_date = today()
		invoice_doc.due_date = today()
		invoice_doc.status = "Draft"
		invoice_doc.save()
		
		return {
			"status": "success",
			"invoice": invoice_doc.name,
			"message": _("Invoice created successfully")
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Invoice Creation Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_invoice_details(invoice):
	"""Get invoice details"""
	try:
		invoice_doc = frappe.get_doc("BMS Invoice", invoice)
		
		return {
			"status": "success",
			"data": {
				"name": invoice_doc.name,
				"customer": invoice_doc.customer,
				"subscription": invoice_doc.subscription,
				"amount": invoice_doc.amount,
				"currency": invoice_doc.currency,
				"status": invoice_doc.status,
				"invoice_date": invoice_doc.invoice_date,
				"due_date": invoice_doc.due_date,
				"payment_status": invoice_doc.get_payment_status()
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Invoice Details Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_customer_invoices(customer):
	"""Get all invoices for a customer"""
	try:
		invoices = frappe.get_all("BMS Invoice",
			filters={"customer": customer},
			fields=["name", "subscription", "amount", "currency", 
					"status", "invoice_date", "due_date"],
			order_by="invoice_date desc"
		)
		
		return {
			"status": "success",
			"data": invoices
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Customer Invoices Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def download_invoice(invoice):
	"""Download invoice as PDF"""
	try:
		invoice_doc = frappe.get_doc("BMS Invoice", invoice)
		
		# Generate PDF
		pdf_content = invoice_doc.generate_pdf()
		
		return {
			"status": "success",
			"pdf_content": pdf_content,
			"filename": f"invoice_{invoice}.pdf"
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Invoice Download Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def mark_invoice_as_paid(invoice, payment_method, reference=None):
	"""Mark invoice as paid"""
	try:
		invoice_doc = frappe.get_doc("BMS Invoice", invoice)
		invoice_doc.add_payment(invoice_doc.total_amount, payment_method, reference)
		
		return {
			"status": "success",
			"message": _("Invoice marked as paid")
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Invoice Payment Error")
		return {
			"status": "error",
			"message": str(e)
		}
