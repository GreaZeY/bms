// BMS Plan Form Script

frappe.ui.form.on('BMS Plan', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.name) {
			frm.add_custom_button(__("View Subscriptions"), function() {
				frappe.set_route('List', 'BMS Subscription', {
					plan: frm.doc.name
				});
			}, __("View"));
			
			frm.add_custom_button(__("Create Subscription"), function() {
				frappe.new_doc('BMS Subscription', {
					plan: frm.doc.name
				});
			}, __("Create"));
		}
	},
	
	amount: function(frm) {
		// Validate amount
		if (frm.doc.amount && frm.doc.amount <= 0) {
			frappe.msgprint(__("Plan amount must be greater than 0"));
		}
	},
	
	trial_period_days: function(frm) {
		// Validate trial period
		if (frm.doc.trial_period_days && frm.doc.trial_period_days < 0) {
			frappe.msgprint(__("Trial period cannot be negative"));
		}
	},
	
	max_users: function(frm) {
		// Validate max users
		if (frm.doc.max_users && frm.doc.max_users <= 0) {
			frappe.msgprint(__("Max users must be greater than 0"));
		}
	},
	
	storage_limit_gb: function(frm) {
		// Validate storage limit
		if (frm.doc.storage_limit_gb && frm.doc.storage_limit_gb <= 0) {
			frappe.msgprint(__("Storage limit must be greater than 0"));
		}
	},
	
	api_calls_limit: function(frm) {
		// Validate API calls limit
		if (frm.doc.api_calls_limit && frm.doc.api_calls_limit <= 0) {
			frappe.msgprint(__("API calls limit must be greater than 0"));
		}
	},
	
	plan_visibility: function(frm) {
		// Show/hide target customers field based on plan visibility
		if (frm.doc.plan_visibility === "Specific Customers") {
			frm.set_df_property("target_customers", "reqd", 1);
		} else {
			frm.set_df_property("target_customers", "reqd", 0);
		}
	}
});
