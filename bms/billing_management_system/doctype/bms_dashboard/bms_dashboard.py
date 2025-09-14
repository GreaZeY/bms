import frappe
from frappe.model.document import Document
from frappe import _

class BMSDashboard(Document):
	def validate(self):
		self.validate_dashboard_name()
		self.validate_dashboard_type()
		self.validate_charts()
	
	def validate_dashboard_name(self):
		"""Validate dashboard name"""
		if not self.dashboard_name:
			frappe.throw(_("Dashboard name is required"))
		
		# Check if dashboard name already exists
		if frappe.db.exists("BMS Dashboard", {"dashboard_name": self.dashboard_name, "name": ["!=", self.name]}):
			frappe.throw(_("Dashboard name already exists"))
	
	def validate_dashboard_type(self):
		"""Validate dashboard type"""
		if not self.dashboard_type:
			frappe.throw(_("Dashboard type is required"))
		
		valid_types = ["Admin", "User"]
		if self.dashboard_type not in valid_types:
			frappe.throw(_("Invalid dashboard type. Must be Admin or User"))
	
	def validate_charts(self):
		"""Validate charts"""
		if self.charts:
			for chart in self.charts:
				if not chart.chart_name:
					frappe.throw(_("Chart name is required for all charts"))
				if not chart.chart_type:
					frappe.throw(_("Chart type is required for all charts"))
	
	def get_chart_data(self, chart_name):
		"""Get data for a specific chart"""
		if self.charts:
			for chart in self.charts:
				if chart.chart_name == chart_name:
					return self.generate_chart_data(chart)
		return None
	
	def generate_chart_data(self, chart):
		"""Generate data for a chart"""
		# This would be implemented based on the chart type and data source
		# For now, return empty data
		return {
			"labels": [],
			"datasets": []
		}
	
	def get_dashboard_config(self):
		"""Get dashboard configuration"""
		config = {
			"name": self.dashboard_name,
			"type": self.dashboard_type,
			"is_active": self.is_active,
			"charts": []
		}
		
		if self.charts:
			for chart in self.charts:
				config["charts"].append({
					"name": chart.chart_name,
					"type": chart.chart_type,
					"title": chart.chart_title,
					"data_source": chart.data_source,
					"position": chart.position
				})
		
		return config
