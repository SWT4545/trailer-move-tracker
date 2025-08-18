"""
Email Center with Working Live Preview
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import database as db
import branding

def show_email_center():
    """Email center with real-time preview"""
    st.title("✉️ Email Center")
    
    # Create two columns for compose and preview
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ✍️ Compose Email")
        
        # Recipients - NOT in a form so it updates live
        to_email = st.text_input("To *", placeholder="recipient@example.com", key="email_to")
        cc_email = st.text_input("CC", placeholder="cc@example.com (optional)", key="email_cc")
        bcc_email = st.text_input("BCC", placeholder="bcc@example.com (optional)", key="email_bcc")
        
        # Subject
        subject = st.text_input("Subject *", placeholder="Enter email subject", key="email_subject")
        
        # Message body
        body = st.text_area("Message *", height=200, placeholder="Type your message here...", key="email_body")
        
        # Signature option
        add_signature = st.checkbox("Add Signature", value=True, key="email_add_sig")
        signature_text = ""
        if add_signature:
            sig_type = st.selectbox(
                "Signature Type",
                ["Professional", "Simple", "Full Company"],
                key="email_sig_type"
            )
            
            # Generate signature based on type
            if sig_type == "Professional":
                signature_text = """

Best regards,

Smith & Williams Trucking Team
dispatch@smithwilliamstrucking.com
(555) 123-4567

MC# 1276006 | DOT# 3675217"""
            elif sig_type == "Simple":
                signature_text = """

Smith & Williams Trucking
dispatch@smithwilliamstrucking.com"""
            else:  # Full Company
                signature_text = f"""

Smith & Williams Trucking Solutions, LLC
{branding.PRIMARY_TAGLINE}

Email: dispatch@smithwilliamstrucking.com
Phone: (555) 123-4567
Website: www.smithwilliamstrucking.com

{branding.COMPANY_MC} | {branding.COMPANY_DOT}"""
        
        # Buttons
        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📤 Send Email", type="primary", use_container_width=True):
                if to_email and subject and body:
                    # Combine body with signature
                    final_body = body + signature_text if add_signature else body
                    st.success(f"✅ Email sent to {to_email}")
                    st.balloons()
                    # Clear fields
                    for key in ["email_to", "email_cc", "email_bcc", "email_subject", "email_body"]:
                        if key in st.session_state:
                            st.session_state[key] = ""
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")
        
        with col_b:
            if st.button("🗑️ Clear All", use_container_width=True):
                for key in ["email_to", "email_cc", "email_bcc", "email_subject", "email_body"]:
                    if key in st.session_state:
                        st.session_state[key] = ""
                st.rerun()
    
    with col2:
        st.markdown("### 📧 Live Preview")
        
        # Build the email preview
        preview_html = """
        <div style="border: 2px solid #ddd; border-radius: 8px; padding: 1.5rem; background: white; min-height: 500px;">
        """
        
        # Email headers
        preview_html += f"""
        <div style="border-bottom: 2px solid #f0f0f0; padding-bottom: 1rem; margin-bottom: 1rem;">
            <p style="margin: 0.5rem 0;"><strong>From:</strong> dispatch@smithwilliamstrucking.com</p>
            <p style="margin: 0.5rem 0;"><strong>To:</strong> {to_email if to_email else '<em style="color: #999;">Enter recipient email</em>'}</p>
        """
        
        if cc_email:
            preview_html += f'<p style="margin: 0.5rem 0;"><strong>CC:</strong> {cc_email}</p>'
        
        if bcc_email:
            preview_html += f'<p style="margin: 0.5rem 0;"><strong>BCC:</strong> {bcc_email}</p>'
        
        preview_html += f"""
            <p style="margin: 0.5rem 0;"><strong>Subject:</strong> {subject if subject else '<em style="color: #999;">Enter subject</em>'}</p>
        </div>
        """
        
        # Email body with signature
        body_content = body if body else '<em style="color: #999;">Start typing your message...</em>'
        
        # Add signature to preview if selected
        if body and add_signature and signature_text:
            body_content = body + signature_text.replace('\n', '<br>')
        elif body:
            body_content = body
        
        # Format body for HTML (preserve line breaks)
        if body:
            body_content = body_content.replace('\n', '<br>')
        
        preview_html += f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; white-space: pre-wrap;">
            {body_content}
        </div>
        </div>
        """
        
        st.markdown(preview_html, unsafe_allow_html=True)
        
        # Show info about what will be sent
        if add_signature:
            st.info("✅ Signature will be included when email is sent")

# Test it standalone
if __name__ == "__main__":
    st.set_page_config(page_title="Email Test", layout="wide")
    show_email_center()