// BMS Invoice Form Script

frappe.ui.form.on('BMS Invoice', {
	refresh: function(frm) {
		// Add custom buttons based on status
		if (frm.doc.status === "Draft") {
			frm.add_custom_button(__("Send Invoice"), function() {
				send_invoice(frm);
			}, __("Actions"));
		}
		
		if (frm.doc.status === "Sent") {
			frm.add_custom_button(__("Mark as Paid"), function() {
				mark_invoice_paid(frm);
			}, __("Actions"));
		}
		
		// Add download button
		if (frm.doc.name) {
			frm.add_custom_button(__("Download PDF"), function() {
				download_invoice_pdf(frm);
			}, __("Actions"));
		}
		
		// Add button to view related subscription
		if (frm.doc.subscription) {
			frm.add_custom_button(__("View Subscription"), function() {
				frappe.set_route('Form', 'BMS Subscription', frm.doc.subscription);
			}, __("View"));
		}
		
		// Add button to view related payments
		if (frm.doc.name) {
			frm.add_custom_button(__("View Payments"), function() {
				frappe.set_route('List', 'BMS Payment', {
					invoice: frm.doc.name
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
	
	plan: function(frm) {
		// Set plan name when plan is selected
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
					}
				}
			});
		}
	},
	
	amount: function(frm) {
		// Calculate total amount when amount changes
		calculate_total_amount(frm);
	},
	
	tax_amount: function(frm) {
		// Calculate total amount when tax amount changes
		calculate_total_amount(frm);
	}
});

function send_invoice(frm) {
	frappe.confirm(
		__("Are you sure you want to send this invoice?"),
		function() {
			frm.set_value("status", "Sent");
			frm.save();
			
			frappe.show_alert({
				message: __("Invoice sent successfully"),
				indicator: "green"
			});
		}
	);
}

function mark_invoice_paid(frm) {
	frappe.prompt([
		{
			"fieldtype": "Select",
			"label": "Payment Method",
			"fieldname": "payment_method",
			"options": "Credit Card\nBank Transfer\nPayPal\nStripe\nRazorpay\nCash\nOther",
			"reqd": 1
		},
		{
			"fieldtype": "Data",
			"label": "Reference",
			"fieldname": "reference"
		}
	], function(values) {
		frappe.call({
			method: "bms.billing_management_system.api.invoice.mark_invoice_as_paid",
			args: {
				invoice: frm.doc.name,
				payment_method: values.payment_method,
				reference: values.reference
			},
			callback: function(r) {
				if (r.message && r.message.status === "success") {
					frappe.show_alert({
						message: __("Invoice marked as paid"),
						indicator: "green"
					});
					frm.reload_doc();
				} else {
					frappe.msgprint(__("Error marking invoice as paid: " + (r.message.message || "Unknown error")));
				}
			}
		});
	}, __("Mark as Paid"), __("Mark Paid"));
}

function download_invoice_pdf(frm) {
	frappe.call({
		method: "bms.billing_management_system.api.invoice.download_invoice",
		args: {
			invoice: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.status === "success") {
				// Create download link
				const link = document.createElement('a');
				link.href = 'data:application/pdf;base64,' + r.message.pdf_content;
				link.download = r.message.filename;
				link.click();
				
				frappe.show_alert({
					message: __("Invoice downloaded successfully"),
					indicator: "green"
				});
			} else {
				frappe.msgprint(__("Error downloading invoice: " + (r.message.message || "Unknown error")));
			}
		}
	});
}

function calculate_total_amount(frm) {
	let total = frm.doc.amount || 0;
	total += frm.doc.tax_amount || 0;
	frm.set_value("total_amount", total);
}
