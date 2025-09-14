// BMS Customer Form Script

frappe.ui.form.on('BMS Customer', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.name) {
			frm.add_custom_button(__("View Subscriptions"), function() {
				frappe.set_route('List', 'BMS Subscription', {
					customer: frm.doc.name
				});
			}, __("View"));
			
			frm.add_custom_button(__("View Invoices"), function() {
				frappe.set_route('List', 'BMS Invoice', {
					customer: frm.doc.name
				});
			}, __("View"));
			
			frm.add_custom_button(__("View Payments"), function() {
				frappe.set_route('List', 'BMS Payment', {
					customer: frm.doc.name
				});
			}, __("View"));
			
			frm.add_custom_button(__("Create Subscription"), function() {
				frappe.new_doc('BMS Subscription', {
					customer: frm.doc.name
				});
			}, __("Create"));
		}
	},
	
	customer_type: function(frm) {
		// Show/hide company-specific fields
		if (frm.doc.customer_type === "Company") {
			frm.set_df_property("company_name", "reqd", 1);
			frm.set_df_property("contact_person", "reqd", 1);
		} else {
			frm.set_df_property("company_name", "reqd", 0);
			frm.set_df_property("contact_person", "reqd", 0);
		}
	},
	
});

