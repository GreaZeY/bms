// BMS Subscription Form Script

frappe.ui.form.on('BMS Subscription', {
	refresh: function(frm) {
		// Add custom buttons based on status
		if (frm.doc.status === "Active") {
			frm.add_custom_button(__("Cancel Subscription"), function() {
				cancel_subscription(frm);
			}, __("Actions"));
			
			frm.add_custom_button(__("Renew Subscription"), function() {
				renew_subscription(frm);
			}, __("Actions"));
		}
		
		if (frm.doc.status === "Trial") {
			frm.add_custom_button(__("Activate Subscription"), function() {
				activate_subscription(frm);
			}, __("Actions"));
		}
		
		// Add button to create invoice
		if (frm.doc.name && frm.doc.status === "Active") {
			frm.add_custom_button(__("Create Invoice"), function() {
				create_invoice(frm);
			}, __("Actions"));
		}
		
		// Add button to create subscription with invoice for new documents
		if (frm.is_new() && frm.doc.customer && frm.doc.plan && frm.doc.status) {
			frm.add_custom_button(__("Save & Create Invoice"), function() {
				save_and_create_invoice(frm);
			}, __("Actions"));
		}
		
		// Add button to view related invoices
		if (frm.doc.name) {
			frm.add_custom_button(__("View Invoices"), function() {
				frappe.set_route('List', 'BMS Invoice', {
					subscription: frm.doc.name
				});
			}, __("View"));
			
			frm.add_custom_button(__("View Payments"), function() {
				frappe.set_route('List', 'BMS Payment', {
					subscription: frm.doc.name
				});
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
			
			// Clear plan selection when customer changes
			frm.set_value("plan", "");
			frm.set_value("plan_name", "");
			
			// Filter plans based on customer
			filter_plans_for_customer(frm);
		}
	},
	
	plan: function(frm) {
		// Set plan details when plan is selected
		if (frm.doc.plan) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "BMS Plan",
					name: frm.doc.plan
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value("plan_name", r.message.plan_name);
						frm.set_value("amount", r.message.amount);
						frm.set_value("currency", r.message.currency);
						frm.set_value("billing_cycle", r.message.billing_cycle);
						frm.set_value("auto_renewal", r.message.auto_renewal);
						
						// Set trial end date if trial period exists
						if (r.message.trial_period_days > 0 && !frm.doc.trial_end_date) {
							const trial_end_date = frappe.datetime.add_days(frm.doc.start_date, r.message.trial_period_days);
							frm.set_value("trial_end_date", trial_end_date);
						}
					}
				}
			});
		}
	},
	
	start_date: function(frm) {
		// Calculate end date when start date changes
		if (frm.doc.start_date && frm.doc.billing_cycle) {
			calculate_end_date(frm);
		}
	},
	
	billing_cycle: function(frm) {
		// Calculate end date when billing cycle changes
		if (frm.doc.start_date && frm.doc.billing_cycle) {
			calculate_end_date(frm);
		}
	},
	
	before_save: function(frm) {
		// Ensure invoice is created for new active subscriptions
		if (frm.is_new() && frm.doc.status && ["Active", "Trial"].includes(frm.doc.status)) {
			// This will be handled by after_insert in Python
		}
	}
});

function cancel_subscription(frm) {
	frappe.prompt([
		{
			"fieldtype": "Text",
			"label": "Cancellation Reason",
			"fieldname": "reason",
			"reqd": 1
		}
	], function(values) {
		frappe.call({
			method: "bms.billing_management_system.api.subscription.cancel_subscription",
			args: {
				subscription: frm.doc.name,
				reason: values.reason
			},
			callback: function(r) {
				if (r.message && r.message.status === "success") {
					frappe.show_alert({
						message: __("Subscription cancelled successfully"),
						indicator: "green"
					});
					frm.reload_doc();
				} else {
					frappe.msgprint(__("Error cancelling subscription: " + (r.message.message || "Unknown error")));
				}
			}
		});
	}, __("Cancel Subscription"), __("Cancel"));
}

function renew_subscription(frm) {
	frappe.confirm(
		__("Are you sure you want to renew this subscription?"),
		function() {
			frappe.call({
				method: "bms.billing_management_system.api.subscription.renew_subscription",
				args: {
					subscription: frm.doc.name
				},
				callback: function(r) {
					if (r.message && r.message.status === "success") {
						frappe.show_alert({
							message: __("Subscription renewed successfully"),
							indicator: "green"
						});
						frm.reload_doc();
					} else {
						frappe.msgprint(__("Error renewing subscription: " + (r.message.message || "Unknown error")));
					}
				}
			});
		}
	);
}

function activate_subscription(frm) {
	frappe.confirm(
		__("Are you sure you want to activate this subscription?"),
		function() {
			frm.set_value("status", "Active");
			frm.save();
		}
	);
}

function calculate_end_date(frm) {
	if (!frm.doc.start_date || !frm.doc.billing_cycle) {
		return;
	}
	
	let end_date = frm.doc.start_date;
	
	switch (frm.doc.billing_cycle) {
		case "Monthly":
			end_date = frappe.datetime.add_months(frm.doc.start_date, 1);
			break;
		case "Quarterly":
			end_date = frappe.datetime.add_months(frm.doc.start_date, 3);
			break;
		case "Semi-Annual":
			end_date = frappe.datetime.add_months(frm.doc.start_date, 6);
			break;
		case "Annual":
			end_date = frappe.datetime.add_months(frm.doc.start_date, 12);
			break;
		case "One-time":
			end_date = frm.doc.start_date;
			break;
	}
	
	frm.set_value("end_date", end_date);
}

function save_and_create_invoice(frm) {
	// First save the subscription
	frm.save().then(function() {
		// Then create the invoice
		if (frm.doc.status && ["Active", "Trial"].includes(frm.doc.status)) {
			frappe.call({
				method: "bms.billing_management_system.doctype.bms_subscription.bms_subscription.create_invoice_for_subscription",
				args: {
					subscription: frm.doc.name
				},
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({
							message: __("Subscription saved and invoice created successfully"),
							indicator: "green"
						});
						// Optionally navigate to the created invoice
						if (r.message && typeof r.message === 'string') {
							frappe.set_route('Form', 'BMS Invoice', r.message);
						}
					} else {
						frappe.msgprint(__("Subscription saved but error creating invoice"));
					}
				}
			});
		} else {
			frappe.show_alert({
				message: __("Subscription saved successfully"),
				indicator: "green"
			});
		}
	});
}

function create_invoice(frm) {
	frappe.confirm(
		__("Are you sure you want to create an invoice for this subscription?"),
		function() {
			frappe.call({
				method: "bms.billing_management_system.doctype.bms_subscription.bms_subscription.create_invoice_for_subscription",
				args: {
					subscription: frm.doc.name
				},
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({
							message: __("Invoice created successfully"),
							indicator: "green"
						});
						// Optionally navigate to the created invoice
						if (r.message && typeof r.message === 'string') {
							frappe.set_route('Form', 'BMS Invoice', r.message);
						}
					} else {
						frappe.msgprint(__("Error creating invoice"));
					}
				}
			});
		}
	);
}

function filter_plans_for_customer(frm) {
	// Set a custom query for the plan field to filter by customer
	frm.set_query("plan", function() {
		if (frm.doc.customer) {
			return {
				query: "bms.billing_management_system.doctype.bms_subscription.bms_subscription.get_available_plans_for_subscription",
				filters: {
					customer: frm.doc.customer
				}
			};
		} else {
			// If no customer selected, show no plans
			return {
				query: "bms.billing_management_system.doctype.bms_subscription.bms_subscription.get_available_plans_for_subscription",
				filters: {
					customer: ""
				}
			};
		}
	});
}
