// Currency symbol mapping function
function getCurrencySymbol(currencyCode) {
	const currencySymbols = {
		'USD': '$', 'EUR': '€', 'GBP': '£', 'INR': '₹', 'JPY': '¥',
		'CNY': '¥', 'AUD': 'A$', 'CAD': 'C$', 'CHF': 'CHF', 'SGD': 'S$',
		'HKD': 'HK$', 'NZD': 'NZ$', 'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr',
		'PLN': 'zł', 'CZK': 'Kč', 'HUF': 'Ft', 'RUB': '₽', 'BRL': 'R$',
		'ZAR': 'R', 'MXN': '$', 'KRW': '₩', 'THB': '฿', 'MYR': 'RM',
		'PHP': '₱', 'IDR': 'Rp', 'VND': '₫'
	};
	
	return currencySymbols[currencyCode] || currencyCode || '$';
}

frappe.listview_settings['BMS Invoice'] = {
	add_fields: ["status", "customer", "subscription", "amount", "currency", "total_amount", "invoice_date", "due_date"],
	get_indicator: function(doc) {
		if (doc.status == "Paid") {
			return [__("Paid"), "green", "status,=,Paid"];
		} else if (doc.status == "Sent") {
			return [__("Sent"), "blue", "status,=,Sent"];
		} else if (doc.status == "Overdue") {
			return [__("Overdue"), "red", "status,=,Overdue"];
		} else if (doc.status == "Draft") {
			return [__("Draft"), "orange", "status,=,Draft"];
		} else if (doc.status == "Cancelled") {
			return [__("Cancelled"), "grey", "status,=,Cancelled"];
		}
	},
	formatters: {
		amount: function(value, field, doc) {
			if (!value) return '';
			const symbol = getCurrencySymbol(doc.currency);
			return `<span style="font-weight: 600; color: #2e7d32;">${symbol}${value}</span>`;
		},
		total_amount: function(value, field, doc) {
			if (!value) return '';
			const symbol = getCurrencySymbol(doc.currency);
			return `<span style="font-weight: 600; color: #1976d2;">${symbol}${value}</span>`;
		}
	},
	onload: function(listview) {
		// Add custom button for sending invoices
		listview.page.add_menu_item(__("Send Selected"), function() {
			let selected = listview.get_checked_items();
			if (selected.length === 0) {
				frappe.msgprint(__("Please select invoices to send"));
				return;
			}
			
			// Check if all selected invoices are in draft status
			let can_send = selected.every(function(item) {
				return item.status === "Draft";
			});
			
			if (!can_send) {
				frappe.msgprint(__("Only draft invoices can be sent"));
				return;
			}
			
			frappe.confirm(
				__("Are you sure you want to send {0} invoice(s)?", [selected.length]),
				function() {
					selected.forEach(function(item) {
						frappe.call({
							method: "frappe.client.set_value",
							args: {
								doctype: "BMS Invoice",
								name: item.name,
								fieldname: "status",
								value: "Sent"
							},
							callback: function(r) {
								if (r.message) {
									listview.refresh();
								}
							}
						});
					});
				}
			);
		});
		
		// Add button for marking as paid
		listview.page.add_menu_item(__("Mark as Paid"), function() {
			let selected = listview.get_checked_items();
			if (selected.length === 0) {
				frappe.msgprint(__("Please select invoices to mark as paid"));
				return;
			}
			
			// Check if all selected invoices can be marked as paid
			let can_pay = selected.every(function(item) {
				return item.status === "Sent" || item.status === "Overdue";
			});
			
			if (!can_pay) {
				frappe.msgprint(__("Only sent or overdue invoices can be marked as paid"));
				return;
			}
			
			frappe.prompt([
				{
					"fieldtype": "Select",
					"label": "Payment Method",
					"fieldname": "payment_method",
					"options": "Credit Card\nDebit Card\nBank Transfer\nUPI\nWallet\nCash\nOther",
					"reqd": 1,
					"default": "Credit Card"
				},
				{
					"fieldtype": "Data",
					"label": "Reference",
					"fieldname": "reference"
				}
			], function(values) {
				selected.forEach(function(item) {
					frappe.call({
						method: "bms.billing_management_system.api.invoice.mark_invoice_as_paid",
						args: {
							invoice: item.name,
							payment_method: values.payment_method,
							reference: values.reference
						},
						callback: function(r) {
							if (r.message && r.message.status === "success") {
								listview.refresh();
							}
						}
					});
				});
				
				frappe.show_alert({
					message: __("Processing payment for {0} invoice(s)", [selected.length]),
					indicator: "green"
				});
			}, __("Mark as Paid"), __("Mark Paid"));
		});
		
		// Add button for downloading invoices
		listview.page.add_menu_item(__("Download Selected"), function() {
			let selected = listview.get_checked_items();
			if (selected.length === 0) {
				frappe.msgprint(__("Please select invoices to download"));
				return;
			}
			
			selected.forEach(function(item) {
				frappe.call({
					method: "bms.billing_management_system.api.invoice.download_invoice",
					args: {
						invoice: item.name
					},
					callback: function(r) {
						if (r.message && r.message.status === "success") {
							// Create download link
							const link = document.createElement('a');
							link.href = 'data:application/pdf;base64,' + r.message.pdf_content;
							link.download = r.message.filename || `invoice_${item.name}.pdf`;
							link.click();
						}
					}
				});
			});
			
			frappe.show_alert({
				message: __("Downloading {0} invoice(s)", [selected.length]),
				indicator: "blue"
			});
		});
	}
};

