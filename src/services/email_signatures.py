"""
Email Signature Templates for Smith & Williams Trucking
"""

# Default company signature
DEFAULT_SIGNATURE = """
---
Best regards,

Smith & Williams Trucking
Dispatch Department

📧 dispatch@smithwilliamstrucking.com
📱 (555) 123-4567
🌐 www.smithwilliamstrucking.com

📍 123 Trucking Way, Your City, State 12345

This email and any attachments are confidential and intended solely for the addressee.
"""

# CEO/Executive signature
EXECUTIVE_SIGNATURE = """
---
Sincerely,

Brandon Smith
CEO, Smith & Williams Trucking

📧 brandon@smithwilliamstrucking.com
📱 Direct: (555) 123-4500
📱 Mobile: (555) 987-6543
🌐 www.smithwilliamstrucking.com

📍 Executive Office
123 Trucking Way, Your City, State 12345

"Moving Your Business Forward"
"""

# Operations signature
OPERATIONS_SIGNATURE = """
---
Thank you,

Operations Team
Smith & Williams Trucking

📧 operations@smithwilliamstrucking.com
📱 Operations: (555) 123-4568
📱 24/7 Dispatch: (555) 123-4567
🌐 www.smithwilliamstrucking.com

Track your shipment: www.smithwilliamstrucking.com/track
"""

# Billing/Invoice signature
BILLING_SIGNATURE = """
---
Regards,

Accounts Department
Smith & Williams Trucking

📧 billing@smithwilliamstrucking.com
📱 Billing: (555) 123-4569
📠 Fax: (555) 123-4570

Payment Portal: www.smithwilliamstrucking.com/pay
Tax ID: XX-XXXXXXX

Please remit payments to:
Smith & Williams Trucking
PO Box 12345
Your City, State 12345
"""

# Driver communication signature
DRIVER_SIGNATURE = """
---
Safe travels,

Driver Support Team
Smith & Williams Trucking

📧 drivers@smithwilliamstrucking.com
📱 Driver Support: (555) 123-4571
📱 Emergency: (555) 123-9999

Driver Portal: www.smithwilliamstrucking.com/drivers
"""

# Customer service signature
CUSTOMER_SIGNATURE = """
---
Thank you for choosing Smith & Williams Trucking!

Customer Service Team

📧 support@smithwilliamstrucking.com
📱 Customer Service: (555) 123-4567
📱 Hours: Mon-Fri 8AM-8PM, Sat 9AM-5PM EST

Track your shipment: www.smithwilliamstrucking.com/track
File a claim: www.smithwilliamstrucking.com/claims
"""

# Minimal signature for SMS/text notifications
MINIMAL_SIGNATURE = """
- Smith & Williams Trucking
dispatch@smithwilliamstrucking.com | (555) 123-4567
"""

# HTML signatures (for rich email clients)
HTML_SIGNATURE = """
<div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #1e3a8a; font-family: Arial, sans-serif;">
    <p style="margin: 5px 0; color: #333;">Best regards,</p>
    <p style="margin: 10px 0 5px 0; font-weight: bold; color: #1e3a8a; font-size: 16px;">Smith & Williams Trucking</p>
    <p style="margin: 5px 0; color: #666; font-size: 14px;">Dispatch Department</p>
    
    <table style="margin-top: 10px;">
        <tr>
            <td style="padding-right: 10px; color: #1e3a8a;">📧</td>
            <td><a href="mailto:dispatch@smithwilliamstrucking.com" style="color: #1e3a8a; text-decoration: none;">dispatch@smithwilliamstrucking.com</a></td>
        </tr>
        <tr>
            <td style="padding-right: 10px; color: #1e3a8a;">📱</td>
            <td style="color: #666;">(555) 123-4567</td>
        </tr>
        <tr>
            <td style="padding-right: 10px; color: #1e3a8a;">🌐</td>
            <td><a href="https://www.smithwilliamstrucking.com" style="color: #1e3a8a; text-decoration: none;">www.smithwilliamstrucking.com</a></td>
        </tr>
    </table>
    
    <p style="margin-top: 15px; font-size: 11px; color: #999; font-style: italic;">
        This email and any attachments are confidential and intended solely for the addressee.
    </p>
</div>
"""

def get_signature(signature_type='default', user_name=None, title=None):
    """
    Get appropriate email signature based on type
    
    Args:
        signature_type: Type of signature (default, executive, operations, billing, driver, customer, minimal)
        user_name: Optional user name to personalize signature
        title: Optional title to include
    
    Returns:
        String containing the email signature
    """
    signatures = {
        'default': DEFAULT_SIGNATURE,
        'executive': EXECUTIVE_SIGNATURE,
        'operations': OPERATIONS_SIGNATURE,
        'billing': BILLING_SIGNATURE,
        'driver': DRIVER_SIGNATURE,
        'customer': CUSTOMER_SIGNATURE,
        'minimal': MINIMAL_SIGNATURE,
        'html': HTML_SIGNATURE
    }
    
    signature = signatures.get(signature_type, DEFAULT_SIGNATURE)
    
    # Personalize if user info provided
    if user_name and signature_type == 'default':
        personalized = f"""
---
Best regards,

{user_name}
{title if title else 'Smith & Williams Trucking'}

📧 dispatch@smithwilliamstrucking.com
📱 (555) 123-4567
🌐 www.smithwilliamstrucking.com

📍 123 Trucking Way, Your City, State 12345

This email and any attachments are confidential and intended solely for the addressee.
"""
        return personalized
    
    return signature

def get_signature_by_department(department):
    """Get signature based on department"""
    department_map = {
        'dispatch': 'default',
        'executive': 'executive',
        'operations': 'operations',
        'billing': 'billing',
        'accounting': 'billing',
        'driver': 'driver',
        'customer_service': 'customer',
        'support': 'customer'
    }
    
    signature_type = department_map.get(department.lower(), 'default')
    return get_signature(signature_type)