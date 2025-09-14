import frappe
from frappe.model.document import Document
from frappe import _

class BMSPlanFeature(Document):
	def validate(self):
		self.validate_feature_name()
		self.validate_limit_value()
		self.validate_limit_type()
	
	def validate_feature_name(self):
		"""Validate feature name"""
		if not self.feature_name:
			frappe.throw(_("Feature name is required"))
	
	def validate_limit_value(self):
		"""Validate limit value"""
		if self.limit_value is not None and self.limit_value < 0:
			frappe.throw(_("Limit value cannot be negative"))
	
	def validate_limit_type(self):
		"""Validate limit type"""
		if self.limit_type:
			valid_types = ["Unlimited", "Per Month", "Per Year", "Total"]
			if self.limit_type not in valid_types:
				frappe.throw(_("Invalid limit type. Must be one of: {0}").format(", ".join(valid_types)))
	
	def get_feature_summary(self):
		"""Get feature summary"""
		summary = self.feature_name
		
		if self.is_included:
			if self.limit_type == "Unlimited":
				summary += " (Unlimited)"
			elif self.limit_value and self.limit_type:
				summary += f" ({self.limit_value} {self.limit_type})"
		else:
			summary += " (Not Included)"
		
		return summary
	
	def is_feature_available(self):
		"""Check if feature is available"""
		return self.is_included == 1
	
	def get_usage_limit(self):
		"""Get usage limit for this feature"""
		if not self.is_included:
			return 0
		
		if self.limit_type == "Unlimited":
			return float('inf')
		
		return self.limit_value or 0
