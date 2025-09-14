# Razorpay Integration Setup

## Prerequisites

1. **Razorpay Account**: Sign up at [razorpay.com](https://razorpay.com)
2. **API Keys**: Get your Key ID and Key Secret from Razorpay Dashboard

## Installation

1. **Install Razorpay Python SDK**:
   ```bash
   bench --site [your-site] install-app razorpay
   # OR
   pip install razorpay
   ```

2. **Add to requirements.txt**:
   ```
   razorpay>=1.2.0
   ```

## Configuration

### 1. Set Razorpay Credentials in Frappe

Go to **Setup > System Settings** and add:

- **razorpay_key_id**: Your Razorpay Key ID
- **razorpay_key_secret**: Your Razorpay Key Secret

### 2. Alternative: Environment Variables

Add to your site's environment:

```bash
export RAZORPAY_KEY_ID="rzp_test_xxxxxxxxxxxxx"
export RAZORPAY_KEY_SECRET="xxxxxxxxxxxxxxxxxxxx"
```

### 3. Update API Code (if using environment variables)

Modify `/home/grzy/billing/apps/bms/bms/billing_management_system/api/user_portal.py`:

```python
# Replace these lines:
razorpay_key_id = frappe.get_system_settings("razorpay_key_id")
razorpay_key_secret = frappe.get_system_settings("razorpay_key_secret")

# With:
import os
razorpay_key_id = os.getenv("RAZORPAY_KEY_ID") or frappe.get_system_settings("razorpay_key_id")
razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET") or frappe.get_system_settings("razorpay_key_secret")
```

## Testing

### 1. Test Mode
- Use Razorpay test credentials (starts with `rzp_test_`)
- Test cards: 4111 1111 1111 1111 (Visa), 5555 5555 5555 4444 (Mastercard)

### 2. Production Mode
- Use live credentials (starts with `rzp_live_`)
- Real payments will be processed

## Features Implemented

✅ **Direct Payment**: Click "Choose Plan" → Razorpay popup opens  
✅ **Payment Verification**: Server-side signature verification  
✅ **Automatic Subscription**: Creates subscription after successful payment  
✅ **Invoice Generation**: Automatic invoice creation  
✅ **Payment Tracking**: Stores Razorpay payment and order IDs  

## User Flow

1. User clicks "Choose Plan" on any plan card
2. Razorpay checkout popup opens with plan details
3. User enters payment details
4. Payment is processed by Razorpay
5. Server verifies payment signature
6. Subscription, payment, and invoice records are created
7. User sees success message and subscription appears in "My Subscriptions"

## Security Features

- ✅ **Signature Verification**: All payments are verified server-side
- ✅ **Customer Validation**: Only logged-in users can make payments
- ✅ **Plan Availability**: Only available plans can be purchased
- ✅ **Duplicate Prevention**: Prevents multiple subscriptions for same plan

## Troubleshooting

### Common Issues:

1. **"Razorpay credentials not configured"**
   - Check if Key ID and Secret are set in System Settings
   - Verify credentials are correct

2. **"Payment verification failed"**
   - Check if Key Secret is correct
   - Ensure webhook URL is configured (if using webhooks)

3. **"Failed to create payment order"**
   - Check Razorpay account status
   - Verify API keys have correct permissions

### Debug Mode:

Add logging to see detailed error messages:

```python
import frappe
frappe.log_error(f"Razorpay Error: {str(e)}")
```

## Webhook Setup (Optional)

For production, set up webhooks in Razorpay Dashboard:

1. Go to Razorpay Dashboard > Settings > Webhooks
2. Add webhook URL: `https://your-domain.com/api/method/bms.billing_management_system.api.webhooks.razorpay_webhook`
3. Select events: `payment.captured`, `payment.failed`

## Support

- **Razorpay Documentation**: [docs.razorpay.com](https://docs.razorpay.com)
- **Frappe Documentation**: [frappeframework.com](https://frappeframework.com)
- **BMS Issues**: Create issue in your BMS repository
