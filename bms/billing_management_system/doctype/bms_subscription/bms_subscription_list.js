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

frappe.listview_settings['BMS Subscription'] = {
	add_fields: ["status", "customer", "plan", "amount", "currency", "start_date", "end_date"],
	get_indicator: function (doc) {
		if (doc.status == "Active") {
			return [__("Active"), "green", "status,=,Active"];
		} else if (doc.status == "Trial") {
			return [__("Trial"), "orange", "status,=,Trial"];
		} else if (doc.status == "Cancelled") {
			return [__("Cancelled"), "red", "status,=,Cancelled"];
		} else if (doc.status == "Expired") {
			return [__("Expired"), "grey", "status,=,Expired"];
		}
	},
	formatters: {
		amount: function (value, field, doc) {
			if (!value) return '';
			const symbol = getCurrencySymbol(doc.currency);
			return `<span style="font-weight: 600; color: #2e7d32;">${symbol}${value}</span>`;
		}
	},
	onload: function (listview) {
		// Add custom button for subscription actions
		listview.page.add_menu_item(__("Cancel Selected"), function () {
			let selected = listview.get_checked_items();
			if (selected.length === 0) {
				frappe.msgprint(__("Please select subscriptions to cancel"));
				return;
			}

			frappe.confirm(
				__("Are you sure you want to cancel {0} subscription(s)?", [selected.length]),
				function () {
					selected.forEach(function (item) {
						frappe.call({
							method: "bms.billing_management_system.doctype.bms_subscription.bms_subscription.cancel_subscription",
							args: {
								subscription: item.name,
								reason: "Cancelled by admin"
							},
							callback: function (r) {
								if (r.message) {
									listview.refresh();
								}
							}
						});
					});
				}
			);
		});

		// Add button for renewing subscriptions
		listview.page.add_menu_item(__("Renew Selected"), function () {
			let selected = listview.get_checked_items();
			if (selected.length === 0) {
				frappe.msgprint(__("Please select subscriptions to renew"));
				return;
			}

			selected.forEach(function (item) {
				frappe.call({
					method: "bms.billing_management_system.doctype.bms_subscription.bms_subscription.renew_subscription",
					args: {
						subscription: item.name
					},
					callback: function (r) {
						if (r.message) {
							listview.refresh();
						}
					}
				});
			});
		});
	}
};
