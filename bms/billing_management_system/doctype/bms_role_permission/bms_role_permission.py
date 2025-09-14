import frappe
from frappe.model.document import Document
from frappe import _

class BMSRolePermission(Document):
	def validate(self):
		self.validate_doctype()
		self.validate_permission_type()
	
	def validate_doctype(self):
		"""Validate doctype"""
		if not self.doctype:
			frappe.throw(_("DocType is required"))
		
		# Check if doctype exists
		if not frappe.db.exists("DocType", self.doctype):
			frappe.throw(_("DocType {0} does not exist").format(self.doctype))
	
	def validate_permission_type(self):
		"""Validate permission type"""
		if not self.permission_type:
			frappe.throw(_("Permission type is required"))
		
		valid_permissions = [
			"Read", "Write", "Create", "Delete", "Submit", "Cancel", 
			"Amend", "Report", "Export", "Import", "Print", "Email", "Share"
		]
		
		if self.permission_type not in valid_permissions:
			frappe.throw(_("Invalid permission type: {0}").format(self.permission_type))
