import frappe
from frappe.model.document import Document
from frappe import _

class BMSRole(Document):
	def validate(self):
		self.validate_role_name()
		self.validate_permissions()
	
	def validate_role_name(self):
		"""Validate role name"""
		if not self.role_name:
			frappe.throw(_("Role name is required"))
		
		# Check if role name already exists
		if frappe.db.exists("BMS Role", {"role_name": self.role_name, "name": ["!=", self.name]}):
			frappe.throw(_("Role name already exists"))
	
	def validate_permissions(self):
		"""Validate permissions"""
		if self.permissions:
			for permission in self.permissions:
				if not permission.doctype:
					frappe.throw(_("DocType is required for all permissions"))
				if not permission.permission_type:
					frappe.throw(_("Permission type is required for all permissions"))
	
	def get_permissions_for_doctype(self, doctype):
		"""Get permissions for a specific doctype"""
		permissions = []
		if self.permissions:
			for permission in self.permissions:
				if permission.doctype == doctype:
					permissions.append({
						"permission_type": permission.permission_type,
						"allowed": permission.allowed
					})
		return permissions
	
	def has_permission(self, doctype, permission_type):
		"""Check if role has specific permission"""
		if self.permissions:
			for permission in self.permissions:
				if permission.doctype == doctype and permission.permission_type == permission_type:
					return permission.allowed
		return False