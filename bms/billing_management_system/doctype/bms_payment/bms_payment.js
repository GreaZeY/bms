// BMS Payment Form Script

frappe.ui.form.on('BMS Payment', {
	refresh: function(frm) {
		// Add custom buttons based on payment type and status
		if (frm.doc.payment_type === "Payment" && frm.doc.status === "Completed") {
			frm.add_custom_button(__("Process Refund"), function() {
				process_refund(frm);
			}, __("Actions"));
		}
		
		// Add button to view related subscription
		if (frm.doc.subscription) {
			frm.add_custom_button(__("View Subscription"), function() {
				frappe.set_route('Form', 'BMS Subscription', frm.doc.subscription);
			}, __("View"));
		}
		
		// Add button to view related invoice
		if (frm.doc.invoice) {
			frm.add_custom_button(__("View Invoice"), function() {
				frappe.set_route('Form', 'BMS Invoice', frm.doc.invoice);
			}, __("View"));
		}
	},
	
	customer: function(frm) {
		// Set customer name when customer is selected
		if (frm.doc.customer) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "BMS Customer",
					name: frm.doc.customer
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value("customer_name", r.message.customer_name);
					}
				}
			});
		}
	},
	
	subscription: function(frm) {
		// Set plan when subscription is selected
		if (frm.doc.subscription) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "BMS Subscription",
					name: frm.doc.subscription
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value("plan", r.message.plan);
					}
				}
			});
		}
	},
	
	payment_type: function(frm) {
		// Set default values based on payment type
		if (frm.doc.payment_type === "Refund") {
			if (frm.doc.amount > 0) {
				frm.set_value("amount", -frm.doc.amount);
			}
		} else if (frm.doc.payment_type === "Payment") {
			if (frm.doc.amount < 0) {
				frm.set_value("amount", -frm.doc.amount);
			}
		}
	},
	
	amount: function(frm) {
		// Validate amount based on payment type
		if (frm.doc.payment_type === "Payment" && frm.doc.amount < 0) {
			frappe.msgprint(__("Payment amount should be positive"));
			frm.set_value("amount", -frm.doc.amount);
		} else if (frm.doc.payment_type === "Refund" && frm.doc.amount > 0) {
			frappe.msgprint(__("Refund amount should be negative"));
			frm.set_value("amount", -frm.doc.amount);
		}
	}
});

function process_refund(frm) {
	frappe.prompt([
		{
			"fieldtype": "Text",
			"label": "Refund Reason",
			"fieldname": "reason",
			"reqd": 1
		}
	], function(values) {
		frappe.call({
			method: "bms.billing_management_system.api.payment.process_refund",
			args: {
				payment: frm.doc.name,
				reason: values.reason
			},
			callback: function(r) {
				if (r.message && r.message.status === "success") {
					frappe.show_alert({
						message: __("Refund processed successfully"),
						indicator: "green"
					});
					frm.reload_doc();
				} else {
					frappe.msgprint(__("Error processing refund: " + (r.message.message || "Unknown error")));
				}
			}
		});
	}, __("Process Refund"), __("Refund"));
}
