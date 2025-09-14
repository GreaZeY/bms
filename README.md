# Billing Management System (BMS)

A comprehensive billing management system built for Frappe v15 and Bench v5, designed to handle subscription-based billing with admin and user modes.

## Features

### Admin Features
- **Customer Management**: Create and manage individual and company customers
- **Plan Management**: Create customer-specific plans with different features and pricing
- **Subscription Management**: Manage all subscriptions, renewals, and cancellations
- **Invoice Management**: Generate, send, and track invoices
- **Payment Processing**: Process payments and handle refunds
- **Dashboard**: Comprehensive admin dashboard with statistics and recent activities
- **Reports**: Generate revenue and subscription reports

### User Features
- **Subscription Management**: View and manage own subscriptions
- **Payment History**: View payment history and download receipts
- **Invoice Management**: View invoices and download PDF copies
- **Self-Service**: Cancel subscriptions and request refunds
- **Dashboard**: Personal dashboard with subscription and payment overview

## Installation

1. **Install the app**:
   ```bash
   bench get-app bms
   bench install-app bms
   ```

2. **Set up roles** (automatically done during installation):
   - BMS Admin: Full access to all features
   - BMS User: Limited access to own data only

3. **Access the system**:
   - Admin Dashboard: `/admin_dashboard`
   - User Dashboard: `/user_dashboard`

## DocTypes

### Core DocTypes

1. **BMS Customer**
   - Individual and company customers
   - Contact information and billing details
   - Status management (Active, Inactive, Suspended)

2. **BMS Plan**
   - Customer-specific plans
   - Billing cycles (Monthly, Quarterly, Annual, One-time)
   - Feature definitions and limits
   - Trial period support

3. **BMS Subscription**
   - Links customers to plans
   - Status tracking (Trial, Active, Cancelled, Expired, Suspended)
   - Auto-renewal management
   - Billing date calculations

4. **BMS Invoice**
   - Generated from subscriptions
   - Payment tracking
   - PDF generation and download
   - Status management (Draft, Sent, Paid, Overdue, Cancelled)

5. **BMS Payment**
   - Payment and refund processing
   - Multiple payment methods
   - Status tracking (Pending, Completed, Failed, Cancelled, Refunded)
   - Gateway integration support

### Child DocTypes

- **BMS Plan Feature**: Features included in plans
- **BMS Invoice Item**: Line items in invoices
- **BMS Invoice Payment**: Payment records for invoices

## API Endpoints

### Subscription API
- `create_subscription(customer, plan, start_date)`
- `cancel_subscription(subscription, reason)`
- `renew_subscription(subscription)`
- `get_subscription_details(subscription)`
- `get_customer_subscriptions(customer)`

### Payment API
- `process_payment(customer, subscription, amount, payment_method, reference)`
- `process_refund(payment, reason)`
- `get_payment_history(customer)`
- `get_payment_summary(customer)`

### Invoice API
- `create_invoice(customer, subscription, amount, currency)`
- `get_invoice_details(invoice)`
- `get_customer_invoices(customer)`
- `download_invoice(invoice)`
- `mark_invoice_as_paid(invoice, payment_method, reference)`

### Dashboard API
- `get_dashboard_data()` - Returns different data based on user role

## Permissions

### BMS Admin
- Full access to all DocTypes
- Can create, read, update, delete all records
- Access to reports and exports
- Can manage all customers and subscriptions

### BMS User
- Read-only access to customers and plans
- Can manage own subscriptions (create, update, cancel)
- Can view own invoices and payments
- Can download own invoices
- Cannot access other users' data

## Automated Tasks

### Daily Tasks
- Check for expired subscriptions
- Update subscription statuses
- Check for overdue invoices
- Process auto-renewals

### Monthly Tasks
- Generate revenue reports
- Generate subscription reports
- Cleanup old data

## Refund System

### Automatic Refunds
- Triggered when subscription is cancelled
- Calculates refund amount based on unused period
- Creates refund payment record
- Updates subscription refund status

### Manual Refunds
- Admin can process refunds manually
- Available in payment records
- Requires reason and approval
- Updates original payment status

## Customization

### Adding New Features
1. Create new DocType in `billing_management_system/doctype/`
2. Add API endpoints in `billing_management_system/api/`
3. Update permissions in `permissions.py`
4. Add to hooks.py configuration

### Custom Views
- List views can be customized in `*_list.js` files
- Form views can be customized in `*.js` files
- Dashboard views are in `www/` directory

## Integration

### CRM Integration
- Customers can be imported from CRM systems
- Customer data is linked via email field
- Supports both individual and company customers

### Payment Gateway Integration
- Supports multiple payment methods
- Gateway transaction ID tracking
- Webhook support for payment status updates

## Security

### Data Access Control
- Role-based permissions
- User can only access own data
- Admin has full access
- API endpoints are protected with whitelist

### Data Validation
- Input validation on all forms
- Business logic validation in Python
- Date and amount validations
- Email format validation

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Check user roles
   - Verify permission settings
   - Ensure user has BMS Admin or BMS User role

2. **Subscription Not Renewing**
   - Check auto-renewal setting
   - Verify billing cycle configuration
   - Check scheduled tasks are running

3. **Invoice Not Generating**
   - Verify subscription status
   - Check plan configuration
   - Ensure customer is active

### Logs
- Check Frappe logs for errors
- BMS-specific errors are logged with "BMS" prefix
- API errors are logged with method names

## Support

For support and questions:
- Email: support@bms.com
- Documentation: [Link to documentation]
- Issues: [Link to issue tracker]

## License

MIT License - see LICENSE file for details.

## Version History

- v1.0.0: Initial release with core functionality
- v1.1.0: Added refund system and improved dashboards
- v1.2.0: Enhanced API endpoints and permission system