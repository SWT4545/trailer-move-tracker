"""
Company Configuration Management
Centralized company information and branding
"""

import streamlit as st
from datetime import datetime

def get_default_company_info():
    """Get default company information"""
    return {
        'company_name': 'Smith & Williams Trucking',
        'company_email': 'Dispatch@smithwilliamstrucking.com',
        'company_phone': '(901) 555-SHIP',
        'company_website': 'www.smithwilliamstrucking.com',
        'company_address': '3716 Hwy 78, Memphis, TN 38109',
        'company_tagline': 'Your cargo. Our mission. Moving forward.',
        'company_tagline_alt': 'Your freight, our commitment',
        'company_logo': 'swt_logo_white.png',
        'base_location': 'Fleet Memphis',
        'rate_per_mile': 2.10,
        'factoring_fee': 0.03,
        'factoring_company_email': 'factoring@example.com',
        'client_email': 'client@example.com',
        'dot_number': 'DOT #1234567',
        'mc_number': 'MC #987654',
        'ein': '12-3456789'
    }

def get_company_info():
    """Get current company information from session state"""
    defaults = get_default_company_info()
    info = {}
    for key, default_value in defaults.items():
        info[key] = st.session_state.get(key, default_value)
    return info

def update_company_info(updates):
    """Update company information in session state"""
    for key, value in updates.items():
        st.session_state[key] = value

def get_email_signature(signature_type='default'):
    """Get email signature based on type"""
    info = get_company_info()
    
    signatures = {
        'default': f"""
Best regards,

{info['company_name']}
Operations Team

"{info['company_tagline']}"

📧 Email: {info['company_email']}
📞 Phone: {info['company_phone']}
🌐 Web: {info['company_website']}
📍 Address: {info['company_address']}

{info['dot_number']} | {info['mc_number']}
""",
        'formal': f"""
Sincerely,

{info['company_name']}
Professional Transportation Services

"{info.get('company_tagline_alt', 'Your freight, our commitment')}"

{info['company_address']}
Email: {info['company_email']}
Phone: {info['company_phone']}
Website: {info['company_website']}

{info['dot_number']} | {info['mc_number']} | EIN: {info['ein']}

This email and any attachments are confidential and intended solely for the addressee.
""",
        'brief': f"""
Thanks,
{info['company_name']}

{info['company_email']} | {info['company_phone']}
""",
        'invoice': f"""
{info['company_name']}
{info['company_address']}

Email: {info['company_email']}
Phone: {info['company_phone']}

{info['dot_number']} | {info['mc_number']} | EIN: {info['ein']}

Payment Terms: Net 30 days
""",
        'driver': f"""
{info['company_name']}
Dispatch Team

📱 {info['company_phone']}
📧 {info['company_email']}

Safe travels!
"""
    }
    
    # Get custom signature if set
    custom_signature = st.session_state.get('custom_email_signature', '')
    if custom_signature:
        return custom_signature
    
    return signatures.get(signature_type, signatures['default'])

def get_report_header():
    """Get formatted report header with company info"""
    info = get_company_info()
    return f"""
<div style='text-align: center; padding: 20px; border-bottom: 3px solid #DC143C;'>
    <h1 style='color: #FFFFFF; margin: 0;'>{info['company_name']}</h1>
    <p style='color: #DC143C; margin: 5px 0; font-style: italic; font-size: 1.1em;'>
        "{info['company_tagline']}"
    </p>
    <p style='color: #666; font-size: 0.9em;'>
        {info['company_address']} | {info['company_phone']} | {info['company_email']}
    </p>
    <p style='color: #666; font-size: 0.8em;'>
        {info['dot_number']} | {info['mc_number']}
    </p>
</div>
"""

def get_invoice_header():
    """Get invoice header with company details"""
    info = get_company_info()
    return {
        'company_name': info['company_name'],
        'address': info['company_address'],
        'phone': info['company_phone'],
        'email': info['company_email'],
        'website': info['company_website'],
        'dot': info['dot_number'],
        'mc': info['mc_number'],
        'ein': info['ein']
    }

def show_company_settings():
    """Show company settings interface"""
    st.markdown("### 🏢 Company Information Management")
    
    tabs = st.tabs(["Basic Info", "Contact Details", "Legal/Compliance", "Email Signatures", "Branding"])
    
    with tabs[0]:  # Basic Info
        st.markdown("#### Basic Company Information")
        with st.form("basic_info"):
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input(
                    "Company Name *",
                    value=st.session_state.get('company_name', 'Smith & Williams Trucking'),
                    help="Legal business name"
                )
                
                # Tagline selection
                tagline_options = [
                    "Your cargo. Our mission. Moving forward.",
                    "Your freight, our commitment"
                ]
                current_tagline = st.session_state.get('company_tagline', tagline_options[0])
                company_tagline = st.selectbox(
                    "Primary Tagline",
                    tagline_options,
                    index=tagline_options.index(current_tagline) if current_tagline in tagline_options else 0,
                    help="Main tagline for reports and communications"
                )
                
                base_location = st.text_input(
                    "Base Location",
                    value=st.session_state.get('base_location', 'Fleet Memphis'),
                    help="Primary operating location"
                )
            
            with col2:
                rate_per_mile = st.number_input(
                    "Rate per Mile ($)",
                    value=st.session_state.get('rate_per_mile', 2.10),
                    step=0.01,
                    format="%.2f"
                )
                factoring_fee = st.number_input(
                    "Factoring Fee (%)",
                    value=st.session_state.get('factoring_fee', 3.0),
                    step=0.1,
                    format="%.1f"
                )
            
            if st.form_submit_button("Update Basic Info", type="primary"):
                update_company_info({
                    'company_name': company_name,
                    'company_tagline': company_tagline,
                    'base_location': base_location,
                    'rate_per_mile': rate_per_mile,
                    'factoring_fee': factoring_fee / 100
                })
                st.success("✅ Basic information updated!")
    
    with tabs[1]:  # Contact Details
        st.markdown("#### Contact Information")
        with st.form("contact_info"):
            col1, col2 = st.columns(2)
            
            with col1:
                company_email = st.text_input(
                    "Primary Email *",
                    value=st.session_state.get('company_email', 'Dispatch@smithwilliamstrucking.com'),
                    help="Main company email for all communications"
                )
                company_phone = st.text_input(
                    "Phone Number *",
                    value=st.session_state.get('company_phone', '(901) 555-SHIP'),
                    help="Primary contact number"
                )
                company_website = st.text_input(
                    "Website",
                    value=st.session_state.get('company_website', 'www.smithwilliamstrucking.com'),
                    help="Company website URL"
                )
            
            with col2:
                company_address = st.text_area(
                    "Physical Address *",
                    value=st.session_state.get('company_address', '3716 Hwy 78, Memphis, TN 38109'),
                    help="Complete mailing address"
                )
                factoring_email = st.text_input(
                    "Factoring Company Email",
                    value=st.session_state.get('factoring_company_email', 'factoring@example.com'),
                    help="Email for factoring submissions"
                )
            
            if st.form_submit_button("Update Contact Info", type="primary"):
                update_company_info({
                    'company_email': company_email,
                    'company_phone': company_phone,
                    'company_website': company_website,
                    'company_address': company_address,
                    'factoring_company_email': factoring_email
                })
                st.success("✅ Contact information updated!")
    
    with tabs[2]:  # Legal/Compliance
        st.markdown("#### Legal & Compliance Information")
        with st.form("legal_info"):
            col1, col2 = st.columns(2)
            
            with col1:
                dot_number = st.text_input(
                    "DOT Number",
                    value=st.session_state.get('dot_number', 'DOT #1234567'),
                    help="Department of Transportation number"
                )
                mc_number = st.text_input(
                    "MC Number",
                    value=st.session_state.get('mc_number', 'MC #987654'),
                    help="Motor Carrier number"
                )
            
            with col2:
                ein = st.text_input(
                    "EIN",
                    value=st.session_state.get('ein', '12-3456789'),
                    help="Employer Identification Number"
                )
                insurance_info = st.text_input(
                    "Insurance Policy",
                    value=st.session_state.get('insurance_policy', 'Policy #INS-2024-001'),
                    help="Insurance policy number"
                )
            
            if st.form_submit_button("Update Legal Info", type="primary"):
                update_company_info({
                    'dot_number': dot_number,
                    'mc_number': mc_number,
                    'ein': ein,
                    'insurance_policy': insurance_info
                })
                st.success("✅ Legal information updated!")
    
    with tabs[3]:  # Email Signatures
        st.markdown("#### Email Signature Configuration")
        
        # Signature type selector
        sig_type = st.selectbox(
            "Select Signature Type",
            ["Default", "Formal", "Brief", "Invoice", "Driver", "Custom"]
        )
        
        # Show preview
        st.markdown("##### Preview:")
        if sig_type == "Custom":
            custom_sig = st.text_area(
                "Custom Signature",
                value=st.session_state.get('custom_email_signature', ''),
                height=200,
                help="Create your own signature template"
            )
            if st.button("Save Custom Signature"):
                st.session_state.custom_email_signature = custom_sig
                st.success("✅ Custom signature saved!")
            st.code(custom_sig if custom_sig else "Enter custom signature above")
        else:
            st.code(get_email_signature(sig_type.lower()))
        
        # Set as default
        if st.button(f"Set {sig_type} as Default Signature", type="primary"):
            st.session_state.default_signature_type = sig_type.lower()
            st.success(f"✅ {sig_type} signature set as default!")
    
    with tabs[4]:  # Branding
        st.markdown("#### Company Branding")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Logo Upload")
            uploaded_logo = st.file_uploader(
                "Company Logo",
                type=['png', 'jpg', 'jpeg'],
                help="Upload company logo (recommended: white/transparent background)"
            )
            if uploaded_logo:
                st.image(uploaded_logo, width=200)
                if st.button("Save Logo"):
                    # In production, save the file
                    st.success("✅ Logo updated!")
        
        with col2:
            st.markdown("##### Brand Colors")
            primary_color = st.color_picker(
                "Primary Color",
                value="#DC143C",
                help="Main brand color"
            )
            secondary_color = st.color_picker(
                "Secondary Color", 
                value="#8B0000",
                help="Accent color"
            )
            
            if st.button("Update Brand Colors"):
                st.session_state.primary_color = primary_color
                st.session_state.secondary_color = secondary_color
                st.success("✅ Brand colors updated!")

def format_phone_number(phone):
    """Format phone number for display"""
    # Remove all non-digits
    digits = ''.join(filter(str.isdigit, phone))
    
    # Format as (XXX) XXX-XXXX
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone

def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None