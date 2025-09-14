// BMS Plan List View Script

frappe.listview_settings['BMS Plan'] = {
	add_fields: ["plan_name", "amount", "currency", "billing_cycle", "is_active", "plan_visibility"],
	get_indicator: function(doc) {
		if (doc.is_active == 1) {
			return [__("Active"), "green", "is_active,=,1"];
		} else {
			return [__("Inactive"), "grey", "is_active,=,0"];
		}
	},
	onload: function(listview) {
		// Add toggle button for pricing view
		listview.page.add_menu_item(__("Toggle Pricing View"), function() {
			togglePricingView(listview);
		});
		
		// Add button to create new plan
		listview.page.add_menu_item(__("Create New Plan"), function() {
			frappe.new_doc("BMS Plan");
		});
		
		// Add button to toggle plan status
		listview.page.add_menu_item(__("Toggle Status"), function() {
			let selected = listview.get_checked_items();
			if (selected.length === 0) {
				frappe.msgprint(__("Please select plans to toggle status"));
				return;
			}
			
			selected.forEach(function(item) {
				frappe.call({
					method: "frappe.client.set_value",
					args: {
						doctype: "BMS Plan",
						name: item.name,
						fieldname: "is_active",
						value: item.is_active ? 0 : 1
					},
					callback: function(r) {
						if (r.message) {
							listview.refresh();
						}
					}
				});
			});
		});
	}
};

// Global variable to track view state
if (typeof window.bmsPricingView === 'undefined') {
	window.bmsPricingView = {
		isPricingView: false,
		originalListView: null
	};
}

function togglePricingView(listview) {
	if (!window.bmsPricingView.isPricingView) {
		// Switch to pricing view
		showPricingView(listview);
	} else {
		// Switch back to list view
		showListView(listview);
	}
}

function showPricingView(listview) {
	// Store original list view
	window.bmsPricingView.originalListView = listview.$result.html();
	
	// Create pricing view container
	const pricingContainer = $(`
		<div class="pricing-plans-container">
			<div class="pricing-header">
				<h2><i class="fa fa-tags"></i> Choose Your Plan</h2>
				<p>Select the perfect plan for your business needs</p>
			</div>
			<div class="customer-filter-section">
				<div class="form-group">
					<label for="customer-filter">Filter plans for customer:</label>
					<select id="customer-filter" class="form-control">
						<option value="">All Customers</option>
					</select>
				</div>
			</div>
			<div class="pricing-cards-container">
				<div class="loading-spinner">
					<div class="spinner-border" role="status">
						<span class="sr-only">Loading...</span>
					</div>
					<p>Loading pricing plans...</p>
				</div>
			</div>
		</div>
	`);
	
	// Replace list view with pricing view
	listview.$result.html(pricingContainer);
	
	// Load and display plans
	loadPricingPlans(listview);
	
	// Update button text
	listview.page.menu.find('[data-label="Toggle Pricing View"]').text(__("Toggle List View"));
	
	window.bmsPricingView.isPricingView = true;
}

function showListView(listview) {
	// Restore original list view
	listview.$result.html(window.bmsPricingView.originalListView);
	
	// Update button text
	listview.page.menu.find('[data-label="Toggle List View"]').text(__("Toggle Pricing View"));
	
	window.bmsPricingView.isPricingView = false;
}

function loadPricingPlans(listview) {
	frappe.call({
		method: 'bms.billing_management_system.doctype.bms_plan.bms_plan.get_pricing_plans_view_data',
		callback: function(r) {
			if (r.message) {
				renderPricingPlans(r.message, listview);
				loadCustomers(listview);
			} else {
				showPricingError('Failed to load pricing plans');
			}
		}
	});
}

function loadCustomers(listview) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'BMS Customer',
			fields: ['name', 'customer_name'],
			limit_page_length: 100
		},
		callback: function(r) {
			if (r.message) {
				populateCustomerFilter(r.message, listview);
			}
		}
	});
}

function populateCustomerFilter(customers, listview) {
	const select = listview.$result.find('#customer-filter');
	customers.forEach(customer => {
		select.append(`<option value="${customer.name}">${customer.customer_name}</option>`);
	});
	
	// Add change handler
	select.on('change', function() {
		filterPricingPlans($(this).val(), listview);
	});
}

function renderPricingPlans(plans, listview) {
	const container = listview.$result.find('.pricing-cards-container');
	container.empty();
	
	plans.forEach((plan, index) => {
		const card = createPricingCard(plan, index);
		container.append(card);
	});
	
	// Store plans for filtering
	listview.pricingPlans = plans;
}

function createPricingCard(plan, index) {
	const is_featured = index === 1; // Make second plan featured
	const features = plan.plan_description ? plan.plan_description.split('\n').filter(f => f.trim()) : [];
	
	// Add default features
	features.push(`${plan.max_users} Users`);
	features.push(`${plan.storage_limit_gb} GB Storage`);
	features.push(`${plan.api_calls_limit} API Calls`);
	if (plan.trial_period_days > 0) {
		features.push(`${plan.trial_period_days} Days Free Trial`);
	}

	return $(`
		<div class="pricing-card ${is_featured ? 'featured' : ''}">
			${is_featured ? '<div class="pricing-badge">Most Popular</div>' : ''}
			<div class="plan-name">${plan.plan_name}</div>
			<div class="plan-description">${plan.plan_description || 'Perfect for your business needs'}</div>
			
			<div class="plan-price">
				<div class="price-amount">
					<span class="price-currency">${plan.currency || '$'}</span>${plan.amount || '0'}
				</div>
				<div class="price-period">per ${plan.billing_cycle ? plan.billing_cycle.toLowerCase() : 'month'}</div>
			</div>
			
			<ul class="plan-features">
				${features.map(feature => `
					<li><i class="fa fa-check"></i> ${feature.trim()}</li>
				`).join('')}
				<li><i class="fa fa-check"></i> 24/7 Customer Support</li>
				<li><i class="fa fa-check"></i> Secure & Reliable</li>
			</ul>
			
			<button class="btn btn-primary plan-button" onclick="selectPlan('${plan.name}')">
				<i class="fa fa-arrow-right"></i> Choose Plan
			</button>
		</div>
	`);
}

function filterPricingPlans(selectedCustomer, listview) {
	if (!listview.pricingPlans) return;
	
	let filtered_plans = listview.pricingPlans.filter(plan => {
		if (plan.plan_visibility === 'All Customers') {
			return true;
		} else if (plan.plan_visibility === 'Specific Customers') {
			if (!selectedCustomer) return false;
			return plan.target_customers.some(tc => tc.customer === selectedCustomer);
		}
		return false;
	});
	
	renderPricingPlans(filtered_plans, listview);
}

function showPricingError(message) {
	const container = $('.pricing-cards-container');
	container.html(`
		<div class="error-message">
			<i class="fa fa-exclamation-triangle"></i>
			<span>${message}</span>
		</div>
	`);
}

// Global function for plan selection
window.selectPlan = function(planName) {
	frappe.msgprint(`Selected plan: ${planName}\\n\\nThis would typically redirect to subscription creation or checkout.`);
};

// Add CSS styles when the page loads
$(document).ready(function() {
	if (!$('#pricing-view-styles').length) {
		$('<style id="pricing-view-styles">')
			.prop('type', 'text/css')
			.html(`
				.pricing-plans-container {
					padding: 20px;
					background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
					min-height: 100vh;
				}
				
				.pricing-header {
					text-align: center;
					margin-bottom: 40px;
					color: white;
				}
				
				.pricing-header h2 {
					font-size: 2.5rem;
					font-weight: 700;
					margin-bottom: 15px;
					text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
				}
				
				.pricing-header p {
					font-size: 1.1rem;
					opacity: 0.9;
				}
				
				.customer-filter-section {
					background: rgba(255, 255, 255, 0.1);
					border-radius: 10px;
					padding: 20px;
					margin-bottom: 30px;
					backdrop-filter: blur(10px);
				}
				
				.customer-filter-section label {
					color: white;
					font-weight: 600;
					margin-bottom: 10px;
				}
				
				.pricing-cards-container {
					display: grid;
					grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
					gap: 30px;
					margin-top: 30px;
				}
				
				.pricing-card {
					background: white;
					border-radius: 15px;
					padding: 30px 25px;
					text-align: center;
					box-shadow: 0 15px 35px rgba(0,0,0,0.1);
					transition: all 0.3s ease;
					position: relative;
					overflow: hidden;
				}
				
				.pricing-card:hover {
					transform: translateY(-8px);
					box-shadow: 0 25px 50px rgba(0,0,0,0.2);
				}
				
				.pricing-card.featured {
					border: 3px solid #667eea;
					transform: scale(1.05);
				}
				
				.pricing-card.featured:hover {
					transform: scale(1.05) translateY(-8px);
				}
				
				.pricing-badge {
					position: absolute;
					top: 15px;
					right: 15px;
					background: linear-gradient(45deg, #667eea, #764ba2);
					color: white;
					padding: 6px 12px;
					border-radius: 15px;
					font-size: 0.75rem;
					font-weight: 600;
				}
				
				.plan-name {
					font-size: 1.5rem;
					font-weight: 700;
					color: #333;
					margin-bottom: 8px;
				}
				
				.plan-description {
					color: #666;
					margin-bottom: 25px;
					font-size: 0.95rem;
					line-height: 1.5;
				}
				
				.plan-price {
					margin-bottom: 25px;
				}
				
				.price-amount {
					font-size: 2.5rem;
					font-weight: 700;
					color: #667eea;
					line-height: 1;
				}
				
				.price-currency {
					font-size: 1.2rem;
					color: #666;
					vertical-align: top;
				}
				
				.price-period {
					color: #666;
					font-size: 0.9rem;
					margin-top: 8px;
				}
				
				.plan-features {
					list-style: none;
					padding: 0;
					margin: 25px 0;
				}
				
				.plan-features li {
					padding: 8px 0;
					border-bottom: 1px solid #f0f0f0;
					color: #555;
					font-size: 0.9rem;
				}
				
				.plan-features li:last-child {
					border-bottom: none;
				}
				
				.plan-features li i {
					color: #28a745;
					margin-right: 8px;
					width: 16px;
				}
				
				.plan-button {
					background: linear-gradient(45deg, #667eea, #764ba2);
					border: none;
					color: white;
					padding: 12px 30px;
					border-radius: 25px;
					font-size: 1rem;
					font-weight: 600;
					transition: all 0.3s ease;
					margin-top: 15px;
				}
				
				.plan-button:hover {
					transform: translateY(-2px);
					box-shadow: 0 8px 15px rgba(102, 126, 234, 0.4);
					color: white;
				}
				
				.loading-spinner {
					text-align: center;
					padding: 40px 0;
					color: white;
				}
				
				.spinner-border {
					width: 2.5rem;
					height: 2.5rem;
				}
				
				.error-message {
					background: rgba(255, 255, 255, 0.1);
					border: 1px solid rgba(255, 255, 255, 0.3);
					color: white;
					padding: 30px;
					border-radius: 10px;
					text-align: center;
					margin: 20px 0;
				}
				
				@media (max-width: 768px) {
					.pricing-header h2 {
						font-size: 2rem;
					}
					
					.pricing-cards-container {
						grid-template-columns: 1fr;
						gap: 20px;
					}
					
					.pricing-card.featured {
						transform: none;
					}
					
					.pricing-card.featured:hover {
						transform: translateY(-8px);
					}
				}
			`)
			.appendTo('head');
	}
});
