import frappe
from frappe.model.document import Document
from frappe import _

class BMSDashboardChart(Document):
	def validate(self):
		self.validate_chart_name()
		self.validate_chart_type()
		self.validate_data_source()
	
	def validate_chart_name(self):
		"""Validate chart name"""
		if not self.chart_name:
			frappe.throw(_("Chart name is required"))
	
	def validate_chart_type(self):
		"""Validate chart type"""
		if not self.chart_type:
			frappe.throw(_("Chart type is required"))
		
		valid_types = ["Bar", "Line", "Pie", "Doughnut", "Area", "Scatter"]
		if self.chart_type not in valid_types:
			frappe.throw(_("Invalid chart type. Must be one of: {0}").format(", ".join(valid_types)))
	
	def validate_data_source(self):
		"""Validate data source"""
		if self.data_source:
			valid_sources = [
				"Subscription Statistics",
				"Revenue Statistics", 
				"Payment Statistics",
				"Customer Statistics"
			]
			if self.data_source not in valid_sources:
				frappe.throw(_("Invalid data source. Must be one of: {0}").format(", ".join(valid_sources)))
	
	def get_chart_config(self):
		"""Get chart configuration"""
		return {
			"name": self.chart_name,
			"title": self.chart_title or self.chart_name,
			"type": self.chart_type,
			"data_source": self.data_source,
			"position": self.position or 1
		}
