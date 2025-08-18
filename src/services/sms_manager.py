"""
SMS Manager using Twilio API
Handles all SMS notifications for drivers and customers
"""

import streamlit as st
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import api_config
from datetime import datetime
import database as db

def send_sms(to_phone, message):
    """Send SMS using Twilio"""
    try:
        # Check if Twilio is configured
        if not api_config.is_twilio_configured():
            st.warning("Twilio API is not configured. Please update api_config.py with your Twilio credentials.")
            return False
        
        # Get Twilio credentials
        twilio_config = api_config.get_twilio_credentials()
        
        # Initialize Twilio client
        client = Client(twilio_config['account_sid'], twilio_config['auth_token'])
        
        # Send SMS
        message = client.messages.create(
            body=message,
            from_=twilio_config['from_phone'],
            to=to_phone
        )
        
        # Log SMS to database
        log_sms(to_phone, message.body, 'sent', message.sid)
        
        return True
        
    except TwilioRestException as e:
        st.error(f"Twilio error: {str(e)}")
        log_sms(to_phone, message, 'failed', error=str(e))
        return False
    except Exception as e:
        st.error(f"Error sending SMS: {str(e)}")
        log_sms(to_phone, message, 'failed', error=str(e))
        return False

def send_driver_route_notification(driver_phone, driver_name, route_id, route_url):
    """Send route assignment notification to driver"""
    message = f"""Hi {driver_name},

You have been assigned a new route!

Route ID: {route_id}
View your route: {route_url}

Please confirm receipt and check your route details.

- Smith & Williams Trucking"""
    
    return send_sms(driver_phone, message)

def send_delivery_confirmation(customer_phone, trailer_number, delivery_status):
    """Send delivery status update to customer"""
    message = f"""Smith & Williams Trucking Update:

Trailer #{trailer_number} has been {delivery_status}.

Track your delivery at: [tracking_url]

Thank you for choosing Smith & Williams Trucking!"""
    
    return send_sms(customer_phone, message)

def send_pickup_notification(driver_phone, pickup_location, pickup_time):
    """Send pickup reminder to driver"""
    message = f"""Pickup Reminder:

Location: {pickup_location}
Time: {pickup_time}

Please confirm your arrival at the pickup location.

- Smith & Williams Trucking"""
    
    return send_sms(driver_phone, message)

def send_bulk_sms(phone_numbers, message):
    """Send SMS to multiple recipients"""
    success_count = 0
    failed_count = 0
    
    for phone in phone_numbers:
        if send_sms(phone, message):
            success_count += 1
        else:
            failed_count += 1
    
    return success_count, failed_count

def log_sms(to_phone, message, status, message_sid=None, error=None):
    """Log SMS to database for tracking"""
    try:
        # This would log to your database
        # For now, we'll just print to console
        log_entry = {
            'timestamp': datetime.now(),
            'to_phone': to_phone,
            'message': message[:100],  # First 100 chars
            'status': status,
            'message_sid': message_sid,
            'error': error
        }
        # TODO: Add to database
        return True
    except Exception as e:
        print(f"Error logging SMS: {str(e)}")
        return False

def show_sms_center():
    """SMS Management Interface for Streamlit"""
    st.title("📱 SMS Center")
    
    tabs = st.tabs(["📤 Send SMS", "📋 Templates", "📊 History", "⚙️ Settings"])
    
    with tabs[0]:
        send_sms_interface()
    
    with tabs[1]:
        manage_sms_templates()
    
    with tabs[2]:
        show_sms_history()
    
    with tabs[3]:
        sms_settings()

def send_sms_interface():
    """Interface for sending SMS messages"""
    st.subheader("📤 Send SMS")
    
    # Check if Twilio is configured
    if not api_config.is_twilio_configured():
        st.error("⚠️ Twilio is not configured. Please update api_config.py with your credentials.")
        st.info("See instructions in api_config.py for setting up Twilio")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("send_sms_form"):
            # Recipient selection
            recipient_type = st.radio("Send to:", ["Individual", "Driver", "Customer", "Bulk"])
            
            if recipient_type == "Individual":
                phone_number = st.text_input("Phone Number", placeholder="+1234567890")
                recipient_name = st.text_input("Recipient Name (Optional)")
            
            elif recipient_type == "Driver":
                # Get drivers from database
                drivers = db.get_all_drivers()
                if not drivers.empty:
                    selected_driver = st.selectbox(
                        "Select Driver",
                        drivers['driver_name'].tolist()
                    )
                    driver_data = drivers[drivers['driver_name'] == selected_driver].iloc[0]
                    phone_number = driver_data.get('phone_number', '')
                    recipient_name = selected_driver
                else:
                    st.warning("No drivers found in database")
                    phone_number = ""
                    recipient_name = ""
            
            elif recipient_type == "Customer":
                phone_number = st.text_input("Customer Phone", placeholder="+1234567890")
                recipient_name = st.text_input("Customer Name")
            
            else:  # Bulk
                phone_numbers = st.text_area(
                    "Phone Numbers (one per line)",
                    placeholder="+1234567890\n+0987654321",
                    height=100
                )
            
            # Message template
            template = st.selectbox(
                "Use Template",
                ["Custom Message", "Route Assignment", "Pickup Reminder", "Delivery Update", "General Notification"]
            )
            
            if template == "Custom Message":
                message = st.text_area("Message", height=150, max_chars=160)
                char_count = len(message) if message else 0
                st.caption(f"Characters: {char_count}/160")
            else:
                # Pre-fill with template
                message = get_sms_template(template)
                message = st.text_area("Message", value=message, height=150, max_chars=160)
            
            # Send button
            if st.form_submit_button("📤 Send SMS", type="primary", use_container_width=True):
                if recipient_type == "Bulk":
                    phones = [p.strip() for p in phone_numbers.split('\n') if p.strip()]
                    if phones and message:
                        success, failed = send_bulk_sms(phones, message)
                        st.success(f"✅ Sent: {success}, ❌ Failed: {failed}")
                    else:
                        st.error("Please enter phone numbers and message")
                else:
                    if phone_number and message:
                        if send_sms(phone_number, message):
                            st.success(f"✅ SMS sent successfully to {phone_number}")
                        else:
                            st.error("Failed to send SMS")
                    else:
                        st.error("Please enter phone number and message")
    
    with col2:
        st.subheader("📱 Preview")
        if 'message' in locals() and message:
            st.markdown(f"""
            <div style="border: 2px solid #25D366; border-radius: 10px; padding: 10px; background: #f0f0f0;">
                <div style="background: #25D366; color: white; padding: 5px; border-radius: 5px; margin-bottom: 10px;">
                    <b>SMS Message</b>
                </div>
                <div style="background: white; padding: 10px; border-radius: 5px;">
                    {message}
                </div>
                <div style="text-align: right; color: #666; font-size: 0.8em; margin-top: 5px;">
                    {len(message)}/160 characters
                </div>
            </div>
            """, unsafe_allow_html=True)

def manage_sms_templates():
    """Manage SMS templates"""
    st.subheader("📋 SMS Templates")
    
    # Display predefined templates
    templates = {
        "Route Assignment": "Hi {driver_name}, you've been assigned route #{route_id}. View details: {route_url}",
        "Pickup Reminder": "Reminder: Pickup at {location} scheduled for {time}. Please confirm arrival.",
        "Delivery Update": "Trailer #{trailer_id} has been {status}. ETA: {eta}",
        "Payment Confirmation": "Payment of ${amount} received for invoice #{invoice_id}. Thank you!",
        "Emergency Alert": "URGENT: {message}. Please respond immediately."
    }
    
    for name, template in templates.items():
        with st.expander(f"📝 {name}"):
            st.code(template)
            st.caption("Variables in {brackets} will be replaced when sending")

def show_sms_history():
    """Show SMS sending history"""
    st.subheader("📊 SMS History")
    
    # This would typically fetch from database
    st.info("SMS history will be displayed here once messages are sent")
    
    # Sample history display
    sample_data = {
        'Date': ['2024-01-15 10:30', '2024-01-15 11:45', '2024-01-15 14:20'],
        'To': ['+1234567890', '+0987654321', '+1122334455'],
        'Message': ['Route assignment...', 'Pickup reminder...', 'Delivery update...'],
        'Status': ['✅ Sent', '✅ Sent', '❌ Failed']
    }
    
    import pandas as pd
    df = pd.DataFrame(sample_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def sms_settings():
    """SMS configuration settings"""
    st.subheader("⚙️ SMS Settings")
    
    # Check configuration status
    if api_config.is_twilio_configured():
        st.success("✅ Twilio is configured and ready")
        
        twilio_config = api_config.get_twilio_credentials()
        st.info(f"From Number: {twilio_config['from_phone']}")
        
        if st.button("Test SMS Configuration"):
            test_number = st.text_input("Enter test phone number:", placeholder="+1234567890")
            if test_number:
                if send_sms(test_number, "Test message from Smith & Williams Trucking Tracker"):
                    st.success("Test SMS sent successfully!")
                else:
                    st.error("Test SMS failed")
    else:
        st.warning("⚠️ Twilio is not configured")
        st.markdown("""
        ### Setup Instructions:
        1. Open `api_config.py` in your project folder
        2. Follow the Twilio setup instructions in the file
        3. Add your Account SID, Auth Token, and Phone Number
        4. Save the file and refresh this page
        """)

def get_sms_template(template_name):
    """Get SMS template by name"""
    templates = {
        "Route Assignment": "Hi [Driver Name], you've been assigned a new route. Check your mobile portal for details.",
        "Pickup Reminder": "Reminder: You have a pickup scheduled at [Location] at [Time]. Please confirm.",
        "Delivery Update": "Your trailer has been [Status]. Thank you for using Smith & Williams Trucking.",
        "General Notification": "Smith & Williams Trucking: [Your message here]"
    }
    return templates.get(template_name, "")