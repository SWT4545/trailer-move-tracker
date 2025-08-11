"""
Enhanced Email Manager with Working Preview
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import signature_manager
import branding

def show_email_center():
    """Main email center interface with live preview"""
    st.title("✉️ Email Center")
    
    # Tabs for different email functions
    tabs = st.tabs(["📤 Compose", "📝 Templates", "👥 Recipients", "📜 History", "✍️ Signatures"])
    
    with tabs[0]:
        compose_email_with_preview()
    
    with tabs[1]:
        manage_email_templates()
    
    with tabs[2]:
        manage_recipients()
    
    with tabs[3]:
        show_email_history()
    
    with tabs[4]:
        signature_manager.manage_signatures()

def compose_email_with_preview():
    """Compose email with real-time preview"""
    st.subheader("📤 Compose Email")
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ✍️ Compose Message")
        
        # Recipients section
        st.markdown("**Recipients**")
        to_email = st.text_input("To *", placeholder="recipient@example.com", key="compose_to")
        cc_email = st.text_input("CC", placeholder="cc@example.com (optional)", key="compose_cc")
        bcc_email = st.text_input("BCC", placeholder="bcc@example.com (optional)", key="compose_bcc")
        
        # Subject
        st.markdown("**Subject**")
        subject = st.text_input("Subject Line *", placeholder="Enter email subject", key="compose_subject")
        
        # Message body
        st.markdown("**Message**")
        body = st.text_area("Email Body *", height=250, placeholder="Type your message here...", key="compose_body")
        
        # Signature option
        st.markdown("**Options**")
        add_signature = st.checkbox("Add Signature", value=True)
        if add_signature:
            signature_type = st.selectbox(
                "Select Signature",
                ["Professional", "Simple", "Full Company", "Personal"],
                key="compose_signature"
            )
        else:
            signature_type = None
        
        # Attachment option
        attachment_type = st.selectbox(
            "Attachment",
            ["None", "Invoice PDF", "Move Report", "Monthly Statement"],
            key="compose_attachment"
        )
        
        # Send button
        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📤 Send Email", type="primary", use_container_width=True):
                if to_email and subject and body:
                    # Here you would send the actual email
                    st.success("✅ Email sent successfully!")
                    st.balloons()
                    # Clear the form
                    for key in ["compose_to", "compose_cc", "compose_bcc", "compose_subject", "compose_body"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                else:
                    st.error("Please fill in all required fields (To, Subject, Message)")
        
        with col_b:
            if st.button("🗑️ Clear", use_container_width=True):
                # Clear all fields
                for key in ["compose_to", "compose_cc", "compose_bcc", "compose_subject", "compose_body"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    with col2:
        st.markdown("### 📧 Live Preview")
        
        # Build the preview
        preview_to = st.session_state.get("compose_to", "")
        preview_cc = st.session_state.get("compose_cc", "")
        preview_bcc = st.session_state.get("compose_bcc", "")
        preview_subject = st.session_state.get("compose_subject", "")
        preview_body = st.session_state.get("compose_body", "")
        
        # Add signature to preview if selected
        if add_signature and signature_type and preview_body:
            sig = get_signature_text(signature_type)
            preview_body_with_sig = preview_body + "\n\n" + sig
        else:
            preview_body_with_sig = preview_body
        
        # Display the preview
        if preview_to or preview_subject or preview_body:
            st.markdown(f"""
            <div style="border: 2px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; background: white; min-height: 400px;">
                <div style="border-bottom: 2px solid #f0f0f0; padding-bottom: 1rem; margin-bottom: 1rem;">
                    <p style="margin: 0.5rem 0;"><strong>From:</strong> dispatch@smithwilliamstrucking.com</p>
                    <p style="margin: 0.5rem 0;"><strong>To:</strong> {preview_to if preview_to else '<span style="color: #999;">Enter recipient email</span>'}</p>
                    {f'<p style="margin: 0.5rem 0;"><strong>CC:</strong> {preview_cc}</p>' if preview_cc else ''}
                    {f'<p style="margin: 0.5rem 0;"><strong>BCC:</strong> {preview_bcc}</p>' if preview_bcc else ''}
                    <p style="margin: 0.5rem 0;"><strong>Subject:</strong> {preview_subject if preview_subject else '<span style="color: #999;">Enter subject</span>'}</p>
                </div>
                <div style="white-space: pre-wrap; font-family: Arial, sans-serif; line-height: 1.6; min-height: 200px;">
                    {preview_body_with_sig.replace('<', '&lt;').replace('>', '&gt;') if preview_body_with_sig else '<span style="color: #999;">Start typing your message...</span>'}
                </div>
                {f'<div style="border-top: 1px solid #f0f0f0; margin-top: 1rem; padding-top: 1rem;"><em>📎 Attachment: {attachment_type}</em></div>' if attachment_type != "None" else ''}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="border: 2px dashed #e0e0e0; border-radius: 8px; padding: 3rem; text-align: center; background: #fafafa; min-height: 400px; display: flex; align-items: center; justify-content: center;">
                <div>
                    <h3 style="color: #666; margin-bottom: 1rem;">📧 Email Preview</h3>
                    <p style="color: #999; margin: 0;">Your email will appear here as you type</p>
                    <p style="color: #999; font-size: 0.9rem; margin-top: 0.5rem;">Start composing to see a live preview</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

def get_signature_text(signature_type):
    """Get signature text based on type"""
    signatures = {
        "Professional": """
---
Best regards,

Smith & Williams Trucking Team
📧 dispatch@smithwilliamstrucking.com
📱 (555) 123-4567
🌐 www.smithwilliamstrucking.com

MC# 1276006 | DOT# 3675217
Your Trusted Transportation Partner""",
        
        "Simple": """
---
Smith & Williams Trucking
dispatch@smithwilliamstrucking.com""",
        
        "Full Company": f"""
---
{branding.COMPANY_NAME}
{branding.PRIMARY_TAGLINE}

📧 Email: dispatch@smithwilliamstrucking.com
📱 Phone: (555) 123-4567
📠 Fax: (555) 123-4568
🌐 Website: www.smithwilliamstrucking.com

📍 Address:
123 Transportation Way
Dallas, TX 75201

{branding.COMPANY_MC} | {branding.COMPANY_DOT}

{branding.EMAIL_DISCLAIMER}""",
        
        "Personal": f"""
---
{st.session_state.get('user_name', 'Your Name')}
{st.session_state.get('user_title', 'Your Title')}
Smith & Williams Trucking
{st.session_state.get('user_email', 'your.email@smithwilliamstrucking.com')}"""
    }
    
    return signatures.get(signature_type, "")

def manage_email_templates():
    """Manage email templates"""
    st.subheader("📝 Email Templates")
    
    # Display existing templates
    templates = db.get_all_email_templates()
    
    if not templates.empty:
        st.markdown("### Existing Templates")
        for _, template in templates.iterrows():
            with st.expander(f"📄 {template['template_name']}"):
                st.write(f"**Subject:** {template['subject']}")
                st.write("**Body:**")
                st.text(template['body'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Use Template", key=f"use_{template['id']}"):
                        st.session_state['compose_subject'] = template['subject']
                        st.session_state['compose_body'] = template['body']
                        st.success("Template loaded! Go to Compose tab.")
                
                with col2:
                    if st.button(f"Delete", key=f"del_{template['id']}"):
                        db.delete_email_template(template['id'])
                        st.success("Template deleted")
                        st.rerun()
    else:
        st.info("No templates saved yet. Create your first template below.")
    
    # Add new template
    st.markdown("### Create New Template")
    with st.form("add_template"):
        name = st.text_input("Template Name")
        subject = st.text_input("Subject Line")
        body = st.text_area("Template Body", height=150)
        
        if st.form_submit_button("💾 Save Template"):
            if name and subject and body:
                db.add_email_template(name, subject, body)
                st.success("Template saved!")
                st.rerun()
            else:
                st.error("Please fill in all fields")

def manage_recipients():
    """Manage email recipients"""
    st.subheader("👥 Email Recipients")
    
    recipients = db.get_email_recipients()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not recipients.empty:
            st.markdown("### Saved Recipients")
            for _, recipient in recipients.iterrows():
                with st.container():
                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    with col_a:
                        st.write(f"**{recipient['nickname'] or recipient['email']}**")
                        st.caption(f"{recipient['email']} • {recipient['company'] or 'No company'}")
                    with col_b:
                        if st.button("Use", key=f"use_r_{recipient['id']}"):
                            st.session_state['compose_to'] = recipient['email']
                            st.success("Added to compose!")
                    with col_c:
                        if st.button("Delete", key=f"del_r_{recipient['id']}"):
                            db.delete_email_recipient(recipient['id'])
                            st.rerun()
        else:
            st.info("No saved recipients")
    
    with col2:
        st.markdown("### Add Recipient")
        with st.form("add_recipient"):
            nickname = st.text_input("Nickname")
            email = st.text_input("Email *")
            company = st.text_input("Company")
            
            if st.form_submit_button("Add"):
                if email and '@' in email:
                    db.add_email_recipient(email, nickname, company)
                    st.success("Recipient added!")
                    st.rerun()
                else:
                    st.error("Valid email required")

def show_email_history():
    """Show email history"""
    st.subheader("📜 Email History")
    
    history = db.get_email_history()
    
    if not history.empty:
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            date_filter = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
        with col2:
            search = st.text_input("Search emails", placeholder="Search by recipient or subject...")
        
        # Filter history
        filtered = history.copy()
        if search:
            mask = filtered.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            filtered = filtered[mask]
        
        # Display
        for _, email in filtered.iterrows():
            with st.expander(f"📧 {email['subject']} - {email['sent_at']}"):
                st.write(f"**To:** {email['recipients']}")
                if email.get('cc'):
                    st.write(f"**CC:** {email['cc']}")
                st.write(f"**Sent:** {email['sent_at']}")
                st.write("**Message:**")
                st.text(email['body'])
    else:
        st.info("No email history yet")

def send_email(to, subject, body, cc=None, bcc=None, attachment=None):
    """Send email (placeholder function)"""
    # This would integrate with your actual email service
    # For now, just return success
    return True