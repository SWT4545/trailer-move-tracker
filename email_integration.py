"""
Email Integration for Smith & Williams Trucking
Supports Google Workspace and SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import streamlit as st
from datetime import datetime

def get_email_config():
    """Get current email configuration"""
    return {
        'company_email': st.session_state.get('company_email', 'Dispatch@smithwilliamstrucking.com'),
        'company_name': st.session_state.get('company_name', 'Smith & Williams Trucking'),
        'google_workspace_enabled': st.session_state.get('google_workspace_enabled', False)
    }

def send_email_google_workspace(to_email, subject, body, attachments=None):
    """Send email using Google Workspace"""
    config = get_email_config()
    
    try:
        # In production, this would use Google Workspace API
        # For now, we'll use SMTP with Google
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = config['company_email']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachments if any
        if attachments:
            for filename, content in attachments.items():
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                msg.attach(part)
        
        # Note: In production, you would use OAuth2 or service account
        # This is a simplified example
        return True, "Email sent successfully (simulated)"
        
    except Exception as e:
        return False, str(e)

def send_email_smtp(to_email, subject, body, attachments=None):
    """Send email using standard SMTP"""
    config = get_email_config()
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = config['company_email']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # In production, this would actually send the email
        return True, "Email sent successfully (simulated)"
        
    except Exception as e:
        return False, str(e)

def send_client_report(client_email, report_data):
    """Send client report via email"""
    config = get_email_config()
    
    # Generate subject
    subject = f"Trailer Move Report - {config['company_name']} - {datetime.now().strftime('%B %Y')}"
    
    # Generate body
    body = f"""
Dear Valued Client,

Please find below the trailer move report for the selected period.

SUMMARY:
• Total Moves Completed: {report_data['total_moves']}
• Total Miles: {report_data['total_miles']:,.0f}
• Total Cost: ${report_data['total_cost']:,.2f}
• Report Period: {report_data['start_date']} to {report_data['end_date']}

{report_data['details']}

All mileage has been verified using Google Maps routing.
Proof of delivery documentation is available upon request.

Thank you for your business.

Best regards,
{config['company_name']}
Operations Team

Email: {config['company_email']}
Phone: (901) 555-SHIP
Web: www.smithwilliamstrucking.com
"""
    
    # Choose sending method
    if config['google_workspace_enabled']:
        success, message = send_email_google_workspace(client_email, subject, body)
    else:
        success, message = send_email_smtp(client_email, subject, body)
    
    return success, message

def send_factoring_submission(factoring_email, submission_data):
    """Send submission to factoring company"""
    config = get_email_config()
    
    subject = f"Payment Request - {config['company_name']} - {datetime.now().strftime('%Y-%m-%d')}"
    
    body = f"""
Please process the following completed moves for payment:

Company: {config['company_name']}
Submission Date: {datetime.now().strftime('%Y-%m-%d')}
Number of Moves: {submission_data['move_count']}
Total Miles: {submission_data['total_miles']:,.0f}
Gross Amount: ${submission_data['gross_amount']:,.2f}
Factoring Fee (3%): ${submission_data['factoring_fee']:,.2f}
Net Amount Due: ${submission_data['net_amount']:,.2f}

Move Details:
{submission_data['move_details']}

Attached:
- Rate confirmations
- Proof of delivery documents
- Trailer photos

Please confirm receipt and process payment.

Thank you,
{config['company_name']}

Email: {config['company_email']}
"""
    
    if config['google_workspace_enabled']:
        success, message = send_email_google_workspace(factoring_email, subject, body)
    else:
        success, message = send_email_smtp(factoring_email, subject, body)
    
    return success, message

def test_email_connection():
    """Test email configuration"""
    config = get_email_config()
    
    test_subject = f"Test Email - {config['company_name']}"
    test_body = f"""
This is a test email from {config['company_name']}.

Email System: {'Google Workspace' if config['google_workspace_enabled'] else 'SMTP'}
From: {config['company_email']}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you receive this email, your email configuration is working correctly.
"""
    
    # Send test to company email
    if config['google_workspace_enabled']:
        success, message = send_email_google_workspace(config['company_email'], test_subject, test_body)
    else:
        success, message = send_email_smtp(config['company_email'], test_subject, test_body)
    
    return success, message