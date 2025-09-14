import frappe
from frappe import _

@frappe.whitelist()
def get_available_plans_for_customer(customer):
	"""Get plans available for a specific customer"""
	try:
		# Validate customer
		if not frappe.db.exists("BMS Customer", customer):
			frappe.throw(_("Customer not found"))
		
		# Get all active plans
		all_plans = frappe.get_all("BMS Plan",
			filters={"is_active": 1},
			fields=["name", "plan_name", "plan_description", "plan_type", 
					"billing_cycle", "amount", "currency", "trial_period_days",
					"plan_visibility", "max_users", "storage_limit_gb", 
					"api_calls_limit", "support_level"]
		)
		
		available_plans = []
		
		for plan in all_plans:
			plan_doc = frappe.get_doc("BMS Plan", plan.name)
			
			# Check if plan is available for this customer
			if plan_doc.is_available_for_customer(customer):
				# Get plan features
				features = []
				if plan_doc.features:
					for feature in plan_doc.features:
						features.append({
							"name": feature.feature_name,
							"description": feature.feature_description,
							"included": feature.is_included,
							"limit_value": feature.limit_value,
							"limit_type": feature.limit_type
						})
				
				plan_data = {
					"name": plan.name,
					"plan_name": plan.plan_name,
					"plan_description": plan.plan_description,
					"plan_type": plan.plan_type,
					"billing_cycle": plan.billing_cycle,
					"amount": plan.amount,
					"currency": plan.currency,
					"trial_period_days": plan.trial_period_days,
					"max_users": plan.max_users,
					"storage_limit_gb": plan.storage_limit_gb,
					"api_calls_limit": plan.api_calls_limit,
					"support_level": plan.support_level,
					"features": features
				}
				
				available_plans.append(plan_data)
		
		return {
			"status": "success",
			"data": available_plans
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Plan Availability Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_plan_details(plan):
	"""Get detailed plan information"""
	try:
		if not frappe.db.exists("BMS Plan", plan):
			frappe.throw(_("Plan not found"))
		
		plan_doc = frappe.get_doc("BMS Plan", plan)
		
		# Get plan features
		features = []
		if plan_doc.features:
			for feature in plan_doc.features:
				features.append({
					"name": feature.feature_name,
					"description": feature.feature_description,
					"included": feature.is_included,
					"limit_value": feature.limit_value,
					"limit_type": feature.limit_type
				})
		
		plan_data = {
			"name": plan_doc.name,
			"plan_name": plan_doc.plan_name,
			"plan_description": plan_doc.plan_description,
			"plan_type": plan_doc.plan_type,
			"billing_cycle": plan_doc.billing_cycle,
			"amount": plan_doc.amount,
			"currency": plan_doc.currency,
			"trial_period_days": plan_doc.trial_period_days,
			"max_users": plan_doc.max_users,
			"storage_limit_gb": plan_doc.storage_limit_gb,
			"api_calls_limit": plan_doc.api_calls_limit,
			"support_level": plan_doc.support_level,
			"auto_renewal": plan_doc.auto_renewal,
			"cancellation_policy": plan_doc.cancellation_policy,
			"refund_policy": plan_doc.refund_policy,
			"features": features
		}
		
		return {
			"status": "success",
			"data": plan_data
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Plan Details Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def check_plan_availability(plan, customer):
	"""Check if a plan is available for a specific customer"""
	try:
		if not frappe.db.exists("BMS Plan", plan):
			frappe.throw(_("Plan not found"))
		
		if not frappe.db.exists("BMS Customer", customer):
			frappe.throw(_("Customer not found"))
		
		plan_doc = frappe.get_doc("BMS Plan", plan)
		is_available = plan_doc.is_available_for_customer(customer)
		
		return {
			"status": "success",
			"data": {
				"plan": plan,
				"customer": customer,
				"is_available": is_available
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "BMS Plan Availability Check Error")
		return {
			"status": "error",
			"message": str(e)
		}
