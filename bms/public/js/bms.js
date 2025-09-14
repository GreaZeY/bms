// BMS JavaScript Functions

$(document).ready(function() {
    // Wait for Frappe to be available
    if (typeof frappe !== 'undefined' && frappe.ready) {
        frappe.ready(function() {
            // Initialize BMS dashboard
            if (window.location.pathname.includes('/bms')) {
                initialize_bms_dashboard();
            }
            
            // Add custom buttons to doctype forms
            add_custom_buttons();
            
            // Initialize list view customizations
            initialize_list_views();
        });
    } else {
        // Fallback if frappe.ready is not available
        setTimeout(function() {
            // Initialize BMS dashboard
            if (window.location.pathname.includes('/bms')) {
                initialize_bms_dashboard();
            }
            
            // Add custom buttons to doctype forms
            add_custom_buttons();
            
            // Initialize list view customizations
            initialize_list_views();
        }, 1000);
    }
});

function initialize_bms_dashboard() {
    // Load dashboard data
    load_dashboard_data();
    
    // Set up auto-refresh
    setInterval(load_dashboard_data, 300000); // Refresh every 5 minutes
}

function load_dashboard_data() {
    // Load subscription statistics
    frappe.call({
        method: "bms.billing_management_system.api.dashboard.get_dashboard_data",
        callback: function(r) {
            if (r.message && r.message.status === "success") {
                update_dashboard_stats(r.message.data);
            }
        }
    });
}

function update_dashboard_stats(data) {
    // Update statistics cards
    if (data.subscriptions) {
        update_stat_card('total-subscriptions', data.subscriptions.total);
        update_stat_card('active-subscriptions', data.subscriptions.active);
        update_stat_card('cancelled-subscriptions', data.subscriptions.cancelled);
    }
    
    if (data.revenue) {
        update_stat_card('total-revenue', format_currency(data.revenue.total));
        update_stat_card('monthly-revenue', format_currency(data.revenue.monthly));
    }
    
    if (data.payments) {
        update_stat_card('total-payments', data.payments.total);
        update_stat_card('pending-payments', data.payments.pending);
    }
}

function update_stat_card(element_id, value) {
    const element = document.getElementById(element_id);
    if (element) {
        element.textContent = value;
    }
}

function add_custom_buttons() {
    // Add custom buttons to subscription form
    if (cur_frm && cur_frm.doctype === "BMS Subscription") {
        add_subscription_buttons();
    }
    
    // Add custom buttons to payment form
    if (cur_frm && cur_frm.doctype === "BMS Payment") {
        add_payment_buttons();
    }
    
    // Add custom buttons to invoice form
    if (cur_frm && cur_frm.doctype === "BMS Invoice") {
        add_invoice_buttons();
    }
}

function add_subscription_buttons() {
    if (cur_frm.doc.status === "Active") {
        cur_frm.add_custom_button(__("Cancel Subscription"), function() {
            cancel_subscription();
        }, __("Actions"));
        
        cur_frm.add_custom_button(__("Renew Subscription"), function() {
            renew_subscription();
        }, __("Actions"));
    }
    
    if (cur_frm.doc.status === "Trial") {
        cur_frm.add_custom_button(__("Activate Subscription"), function() {
            activate_subscription();
        }, __("Actions"));
    }
}

function add_payment_buttons() {
    if (cur_frm.doc.payment_type === "Payment" && cur_frm.doc.status === "Completed") {
        cur_frm.add_custom_button(__("Process Refund"), function() {
            process_refund();
        }, __("Actions"));
    }
}

function add_invoice_buttons() {
    cur_frm.add_custom_button(__("Download PDF"), function() {
        download_invoice_pdf();
    }, __("Actions"));
    
    if (cur_frm.doc.status === "Draft") {
        cur_frm.add_custom_button(__("Send Invoice"), function() {
            send_invoice();
        }, __("Actions"));
    }
    
    if (cur_frm.doc.status === "Sent") {
        cur_frm.add_custom_button(__("Mark as Paid"), function() {
            mark_invoice_paid();
        }, __("Actions"));
    }
}

function cancel_subscription() {
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
                subscription: cur_frm.doc.name,
                reason: values.reason
            },
            callback: function(r) {
                if (r.message && r.message.status === "success") {
                    frappe.show_alert({
                        message: __("Subscription cancelled successfully"),
                        indicator: "green"
                    });
                    cur_frm.reload_doc();
                } else {
                    frappe.msgprint(__("Error cancelling subscription: " + (r.message.message || "Unknown error")));
                }
            }
        });
    }, __("Cancel Subscription"), __("Cancel"));
}

function renew_subscription() {
    frappe.confirm(
        __("Are you sure you want to renew this subscription?"),
        function() {
            frappe.call({
                method: "bms.billing_management_system.api.subscription.renew_subscription",
                args: {
                    subscription: cur_frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        frappe.show_alert({
                            message: __("Subscription renewed successfully"),
                            indicator: "green"
                        });
                        cur_frm.reload_doc();
                    } else {
                        frappe.msgprint(__("Error renewing subscription: " + (r.message.message || "Unknown error")));
                    }
                }
            });
        }
    );
}

function activate_subscription() {
    frappe.confirm(
        __("Are you sure you want to activate this subscription?"),
        function() {
            frappe.call({
                method: "bms.billing_management_system.api.subscription.activate_subscription",
                args: {
                    subscription: cur_frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        frappe.show_alert({
                            message: __("Subscription activated successfully"),
                            indicator: "green"
                        });
                        cur_frm.reload_doc();
                    } else {
                        frappe.msgprint(__("Error activating subscription: " + (r.message.message || "Unknown error")));
                    }
                }
            });
        }
    );
}

function process_refund() {
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
                payment: cur_frm.doc.name,
                reason: values.reason
            },
            callback: function(r) {
                if (r.message && r.message.status === "success") {
                    frappe.show_alert({
                        message: __("Refund processed successfully"),
                        indicator: "green"
                    });
                    cur_frm.reload_doc();
                } else {
                    frappe.msgprint(__("Error processing refund: " + (r.message.message || "Unknown error")));
                }
            }
        });
    }, __("Process Refund"), __("Refund"));
}

function download_invoice_pdf() {
    frappe.call({
        method: "bms.billing_management_system.api.invoice.download_invoice",
        args: {
            invoice: cur_frm.doc.name
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

function send_invoice() {
    frappe.confirm(
        __("Are you sure you want to send this invoice?"),
        function() {
            frappe.call({
                method: "bms.billing_management_system.api.invoice.send_invoice",
                args: {
                    invoice: cur_frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.status === "success") {
                        frappe.show_alert({
                            message: __("Invoice sent successfully"),
                            indicator: "green"
                        });
                        cur_frm.reload_doc();
                    } else {
                        frappe.msgprint(__("Error sending invoice: " + (r.message.message || "Unknown error")));
                    }
                }
            });
        }
    );
}

function mark_invoice_paid() {
    frappe.prompt([
        {
            "fieldtype": "Select",
            "label": "Payment Method",
            "fieldname": "payment_method",
            "options": "Credit Card\nBank Transfer\nPayPal\nStripe\nCash\nOther",
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
                invoice: cur_frm.doc.name,
                payment_method: values.payment_method,
                reference: values.reference
            },
            callback: function(r) {
                if (r.message && r.message.status === "success") {
                    frappe.show_alert({
                        message: __("Invoice marked as paid"),
                        indicator: "green"
                    });
                    cur_frm.reload_doc();
                } else {
                    frappe.msgprint(__("Error marking invoice as paid: " + (r.message.message || "Unknown error")));
                }
            }
        });
    }, __("Mark as Paid"), __("Mark Paid"));
}

function initialize_list_views() {
    // Add custom filters to subscription list
    if (frappe.route_options && frappe.route_options.doctype === "BMS Subscription") {
        add_subscription_filters();
    }
    
    // Add custom filters to payment list
    if (frappe.route_options && frappe.route_options.doctype === "BMS Payment") {
        add_payment_filters();
    }
}

function add_subscription_filters() {
    // Add status filter
    const status_filter = frappe.ui.form.make_control({
        parent: $('.list-sidebar'),
        df: {
            fieldtype: "Select",
            fieldname: "status_filter",
            label: __("Status"),
            options: "All\nActive\nTrial\nCancelled\nExpired\nSuspended",
            default: "All"
        },
        render_input: true
    });
    
    status_filter.$input.on('change', function() {
        const status = $(this).val();
        if (status === "All") {
            frappe.route_options = {};
        } else {
            frappe.route_options = { status: status };
        }
        frappe.set_route('List', 'BMS Subscription');
    });
}

function add_payment_filters() {
    // Add payment type filter
    const type_filter = frappe.ui.form.make_control({
        parent: $('.list-sidebar'),
        df: {
            fieldtype: "Select",
            fieldname: "type_filter",
            label: __("Payment Type"),
            options: "All\nPayment\nRefund\nChargeback",
            default: "All"
        },
        render_input: true
    });
    
    type_filter.$input.on('change', function() {
        const payment_type = $(this).val();
        if (payment_type === "All") {
            frappe.route_options = {};
        } else {
            frappe.route_options = { payment_type: payment_type };
        }
        frappe.set_route('List', 'BMS Payment');
    });
}

// Utility functions
function format_currency(amount) {
    if (!amount) return '$0.00';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function format_date(date) {
    if (!date) return '';
    
    // Handle different date formats
    let dateObj;
    if (typeof date === 'string') {
        // Handle DD/MM/YYYY format
        if (date.includes('/')) {
            const parts = date.split('/');
            if (parts.length === 3) {
                // Convert DD/MM/YYYY to YYYY-MM-DD
                date = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
            }
        }
        dateObj = new Date(date);
    } else {
        dateObj = date;
    }
    
    if (isNaN(dateObj.getTime())) {
        return date; // Return original if invalid
    }
    
    return dateObj.toLocaleDateString();
}

function show_loading() {
    frappe.show_alert({
        message: __("Loading..."),
        indicator: "blue"
    });
}

function show_success(message) {
    frappe.show_alert({
        message: message,
        indicator: "green"
    });
}

function show_error(message) {
    frappe.show_alert({
        message: message,
        indicator: "red"
    });
}

// Export functions for global use
window.bms = {
    cancel_subscription: cancel_subscription,
    renew_subscription: renew_subscription,
    process_refund: process_refund,
    download_invoice_pdf: download_invoice_pdf,
    format_currency: format_currency,
    format_date: format_date,
    show_loading: show_loading,
    show_success: show_success,
    show_error: show_error
};
