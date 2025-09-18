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

frappe.listview_settings['BMS Payment'] = {
	add_fields: ["status", "customer", "payment_type", "amount", "currency", "payment_date"],
	get_indicator: function(doc) {
		if (doc.status == "Completed") {
			return [__("Completed"), "green", "status,=,Completed"];
		} else if (doc.status == "Pending") {
			return [__("Pending"), "orange", "status,=,Pending"];
		} else if (doc.status == "Failed") {
			return [__("Failed"), "red", "status,=,Failed"];
		} else if (doc.status == "Cancelled") {
			return [__("Cancelled"), "grey", "status,=,Cancelled"];
		} else if (doc.status == "Refunded") {
			return [__("Refunded"), "blue", "status,=,Refunded"];
		}
	},
	formatters: {
		amount: function(value, field, doc) {
			if (!value) return '';
			const symbol = getCurrencySymbol(doc.currency);
			const colorClass = doc.payment_type === 'Refund' ? 'color: #d32f2f;' : 'color: #2e7d32;';
			const prefix = doc.payment_type === 'Refund' ? '-' : '';
			return `<span style="font-weight: 600; ${colorClass}">${prefix}${symbol}${Math.abs(value)}</span>`;
		}
	},
	onload: function(listview) {
		// Add custom button for refund processing
		listview.page.add_menu_item(__("Process Refund"), function() {
			let selected = listview.get_checked_items();
			if (selected.length === 0) {
				frappe.msgprint(__("Please select payments to refund"));
				return;
			}
			
			// Check if all selected payments can be refunded
			let can_refund = selected.every(function(item) {
				return item.payment_type === "Payment" && item.status === "Completed";
			});
			
			if (!can_refund) {
				frappe.msgprint(__("Only completed payment records can be refunded"));
				return;
			}
			
			frappe.prompt([
				{
					"fieldtype": "Text",
					"label": "Refund Reason",
					"fieldname": "reason",
					"reqd": 1
				}
			], function(values) {
				selected.forEach(function(item) {
					frappe.call({
						method: "bms.billing_management_system.doctype.bms_payment.bms_payment.process_refund",
						args: {
							payment: item.name,
							reason: values.reason
						},
						callback: function(r) {
							if (r.message) {
								listview.refresh();
							}
						}
					});
				});
			}, __("Process Refund"), __("Refund"));
		});
	}
};
