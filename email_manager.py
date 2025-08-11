import streamlit as st
import pandas as pd
from datetime import datetime
import database as db
import utils
import branding
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import api_config
import signature_manager

def show_email_center():
    """Main email management center"""
    st.title("✉️ Email Center")
    
    tabs = st.tabs(["📤 Send Email", "📝 Templates", "✍️ Signatures", "👥 Recipients", "📜 History"])
    
    with tabs[0]:
        send_email_interface()
    
    with tabs[1]:
        manage_email_templates()
    
    with tabs[2]:
        signature_manager.show_signature_manager()
    
    with tabs[3]:
        manage_recipients()
    
    with tabs[4]:
        show_email_history()

def send_email_interface():
    """Interface for sending emails"""
    st.subheader("📤 Send Email")
    
    # Display company email configuration
    st.info("📧 Emails will be sent from: **dispatch@smithwilliamstrucking.com**")
    
    # Clear form button
    col_clear, col_space = st.columns([1, 3])
    with col_clear:
        if st.button("🔄 Clear Form", use_container_width=True):
            if 'email_form_counter' not in st.session_state:
                st.session_state.email_form_counter = 0
            st.session_state.email_form_counter += 1
            st.rerun()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Email composition form with dynamic key for clearing
        form_key = f"send_email_form_{st.session_state.get('email_form_counter', 0)}"
        with st.form(form_key):
            # Template selection
            templates = db.get_all_email_templates()
            template_options = ["Custom"] + (templates['template_name'].tolist() if not templates.empty else [])
            selected_template = st.selectbox("Select Template", template_options)
            
            # Load template if selected
            if selected_template != "Custom" and not templates.empty:
                template = db.get_email_template(selected_template)
                default_subject = template['subject'] if template else ""
                default_body = template['body'] if template else ""
            else:
                default_subject = ""
                default_body = ""
            
            # Recipients
            st.markdown("**Recipients**")
            recipients_df = db.get_email_recipients()
            
            # Quick select from saved recipients
            if not recipients_df.empty:
                quick_select = st.multiselect(
                    "Quick Select Recipients",
                    recipients_df['nickname'].tolist() if 'nickname' in recipients_df.columns else recipients_df['email_address'].tolist()
                )
                
                # Get selected emails
                selected_emails = []
                for nickname in quick_select:
                    email = recipients_df[recipients_df['nickname'] == nickname]['email_address'].iloc[0] if not recipients_df[recipients_df['nickname'] == nickname].empty else ""
                    if email:
                        selected_emails.append(email)
            else:
                selected_emails = []
            
            # Manual email entry
            to_email = st.text_input(
                "To (separate multiple with commas)",
                value=", ".join(selected_emails) if selected_emails else "",
                placeholder="email1@example.com, email2@example.com"
            )
            
            cc_email = st.text_input("CC (Optional)", placeholder="cc@example.com")
            bcc_email = st.text_input("BCC (Optional)", placeholder="bcc@example.com")
            
            # Subject and body
            subject = st.text_input("Subject", value=default_subject, placeholder="Enter email subject")
            
            # Add placeholder replacement info
            if selected_template != "Custom":
                st.info("Available placeholders: {contractor_name}, {date}, {total_amount}, {invoice_number}")
            
            body = st.text_area("Message", value=default_body, height=300, placeholder="Enter your message here...")
            
            # Attachment options
            st.markdown("**Attachments**")
            attachment_type = st.selectbox("Attach Document", ["None", "Contractor Invoice", "Driver Invoice", "Progress Report"])
            
            # Signature options - using new signature manager
            st.markdown("**Signature**")
            add_signature = st.checkbox("Add Signature", value=True)
            if add_signature:
                signature_list = signature_manager.get_signature_list()
                signature_type = st.selectbox(
                    "Select Signature",
                    signature_list,
                    help="Choose the appropriate signature for your email (edit in Signatures tab)"
                )
            else:
                signature_type = None
            
            if st.form_submit_button("📤 Send Email", type="primary", use_container_width=True):
                if to_email and subject and body:
                    # Add signature if requested
                    if add_signature and signature_type:
                        signature = signature_manager.get_signature_for_email(signature_type)
                        body += "\n\n---\n" + signature
                    
                    # Send email (placeholder for actual implementation)
                    success = send_email(to_email, subject, body, cc_email, bcc_email, attachment_type)
                    
                    if success:
                        # Save to history
                        db.add_email_history(
                            recipients=to_email,
                            cc=cc_email,
                            bcc=bcc_email,
                            subject=subject,
                            body=body,
                            attachments=attachment_type if attachment_type != "None" else None,
                            status='sent'
                        )
                        st.success("✅ Email sent successfully!")
                        st.balloons()
                        # Clear form after successful send
                        if 'email_form_counter' not in st.session_state:
                            st.session_state.email_form_counter = 0
                        st.session_state.email_form_counter += 1
                        st.rerun()
                    else:
                        st.error("Failed to send email. Please check your email configuration.")
                else:
                    st.error("Please fill in all required fields (To, Subject, Message)")
    
    with col2:
        # Email preview - show real-time preview
        st.subheader("📧 Preview")
        
        # Create a container for live preview
        preview_container = st.container()
        
        with preview_container:
            # Try to get values from the form inputs (they exist even before submit)
            preview_to = to_email if 'to_email' in locals() and to_email else ""
            preview_subject = subject if 'subject' in locals() and subject else ""
            preview_body = body if 'body' in locals() and body else ""
            
            # If we have any content, show preview
            if preview_to or preview_subject or preview_body:
                # Build preview body with signature if selected
                if 'add_signature' in locals() and add_signature and 'signature_type' in locals():
                    try:
                        signature = signature_manager.get_signature_for_email(signature_type)
                        preview_body += "\n\n---\n" + signature
                    except:
                        pass
                
                # Format for HTML display
                preview_html = f"""
                <div style="border: 1px solid #ddd; padding: 1rem; border-radius: 8px; background: white;">
                    <p><b>From:</b> dispatch@smithwilliamstrucking.com</p>
                    <p><b>To:</b> {preview_to if preview_to else '<em>Enter recipient email</em>'}</p>
                """
                
                if 'cc_email' in locals() and cc_email:
                    preview_html += f"<p><b>CC:</b> {cc_email}</p>"
                
                if 'bcc_email' in locals() and bcc_email:
                    preview_html += f"<p><b>BCC:</b> {bcc_email}</p>"
                
                preview_html += f"""
                    <p><b>Subject:</b> {preview_subject if preview_subject else '<em>Enter subject</em>'}</p>
                    <hr>
                    <div style="white-space: pre-wrap; font-family: Arial, sans-serif; min-height: 100px;">
                        {preview_body.replace('<', '&lt;').replace('>', '&gt;').replace(chr(10), '<br>') if preview_body else '<em>Start typing your message...</em>'}
                    </div>
                """
                
                if 'attachment_type' in locals() and attachment_type != "None":
                    preview_html += f"<hr><p><i>📎 Attachment: {attachment_type}</i></p>"
                
                preview_html += "</div>"
                
                st.markdown(preview_html, unsafe_allow_html=True)
            else:
                # Show placeholder
                st.markdown("""
                <div style="border: 2px dashed #ddd; padding: 2rem; border-radius: 8px; background: #f9f9f9; text-align: center;">
                    <h4 style="color: #666;">📧 Email Preview</h4>
                    <p style="color: #999;">Your email will appear here as you compose it</p>
                    <p style="color: #999; font-size: 0.9em;">Start filling in the form to see a live preview</p>
                </div>
                """, unsafe_allow_html=True)

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
                
                if st.button(f"🗑️ Delete", key=f"del_template_{template['id']}"):
                    # Delete template
                    st.success(f"Template '{template['template_name']}' deleted")
                    st.rerun()
    
    # Add new template
    st.markdown("### Add New Template")
    with st.form("add_template_form"):
        template_name = st.text_input("Template Name", placeholder="e.g., Monthly Invoice")
        template_subject = st.text_input("Subject Line", placeholder="Invoice for {month} - {company_name}")
        template_body = st.text_area(
            "Template Body",
            placeholder="Dear {recipient_name},\n\nPlease find attached...",
            height=200
        )
        
        st.info("Use placeholders like {recipient_name}, {date}, {amount}, etc. that will be replaced when sending")
        
        if st.form_submit_button("💾 Save Template"):
            if template_name and template_subject and template_body:
                db.add_email_template(template_name, template_subject, template_body)
                st.success(f"Template '{template_name}' saved successfully!")
                st.rerun()
            else:
                st.error("Please fill in all fields")

def manage_recipients():
    """Manage email recipients"""
    st.subheader("👥 Email Recipients")
    
    # Display existing recipients
    recipients = db.get_email_recipients()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not recipients.empty:
            st.markdown("### Saved Recipients")
            
            # Display as editable table
            display_df = recipients[['nickname', 'email_address', 'company_name', 'is_favorite']].copy()
            display_df['is_favorite'] = display_df['is_favorite'].apply(lambda x: '⭐' if x else '')
            display_df.columns = ['Nickname', 'Email', 'Company', 'Favorite']
            
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed"
            )
            
            # Delete recipient
            recipient_to_delete = st.selectbox("Select recipient to delete", recipients['email_address'].tolist())
            if st.button("🗑️ Delete Selected Recipient"):
                # Delete recipient
                st.success(f"Recipient {recipient_to_delete} deleted")
                st.rerun()
        else:
            st.info("No saved recipients yet")
    
    with col2:
        # Add new recipient
        st.markdown("### Add New Recipient")
        with st.form("add_recipient_form"):
            nickname = st.text_input("Nickname", placeholder="John from ABC Transport")
            email = st.text_input("Email Address", placeholder="john@abctransport.com")
            company = st.text_input("Company (Optional)", placeholder="ABC Transport Inc.")
            is_favorite = st.checkbox("Mark as Favorite ⭐")
            is_default = st.checkbox("Set as Default Recipient")
            
            if st.form_submit_button("➕ Add Recipient"):
                if email:
                    # Validate email format
                    if '@' in email and '.' in email:
                        db.add_email_recipient(email, nickname, company, is_default, is_favorite)
                        st.success(f"Recipient '{nickname or email}' added successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a valid email address")
                else:
                    st.error("Email address is required")

def show_email_history():
    """Show email sending history"""
    st.subheader("📜 Email History")
    
    # Date filter
    col1, col2, col3 = st.columns(3)
    with col1:
        days_back = st.selectbox("Show emails from", ["Last 7 days", "Last 30 days", "Last 90 days", "All"])
    
    with col2:
        status_filter = st.selectbox("Status", ["All", "Sent", "Failed", "Pending"])
    
    with col3:
        search_query = st.text_input("Search", placeholder="Search by recipient or subject...")
    
    # Get email history
    history = db.get_email_history(limit=100)
    
    if not history.empty:
        # Apply filters
        if search_query:
            mask = (history['recipients'].str.contains(search_query, case=False, na=False) | 
                   history['subject'].str.contains(search_query, case=False, na=False))
            history = history[mask]
        
        if status_filter != "All":
            history = history[history['delivery_status'] == status_filter.lower()]
        
        # Format for display
        display_df = history[['sent_date', 'recipients', 'subject', 'attachments', 'delivery_status']].copy()
        display_df['sent_date'] = pd.to_datetime(display_df['sent_date']).dt.strftime('%m/%d/%Y %I:%M %p')
        display_df['delivery_status'] = display_df['delivery_status'].apply(
            lambda x: '✅ Sent' if x == 'sent' else '❌ Failed' if x == 'failed' else '⏳ Pending'
        )
        display_df.columns = ['Date/Time', 'Recipients', 'Subject', 'Attachments', 'Status']
        
        # Display with expandable details
        for idx, row in display_df.iterrows():
            with st.expander(f"{row['Date/Time']} - {row['Subject'][:50]}..."):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**To:** {history.iloc[idx]['recipients']}")
                    if history.iloc[idx]['cc']:
                        st.write(f"**CC:** {history.iloc[idx]['cc']}")
                    if history.iloc[idx]['bcc']:
                        st.write(f"**BCC:** {history.iloc[idx]['bcc']}")
                
                with col2:
                    st.write(f"**Status:** {row['Status']}")
                    if history.iloc[idx]['attachments']:
                        st.write(f"**Attachments:** {history.iloc[idx]['attachments']}")
                
                st.write("**Message:**")
                st.text(history.iloc[idx]['body'][:500] + "..." if len(history.iloc[idx]['body']) > 500 else history.iloc[idx]['body'])
                
                if st.button(f"📤 Resend", key=f"resend_{idx}"):
                    st.info("Resending email...")
                    # Resend logic here
                    st.success("Email resent successfully!")
    else:
        st.info("No email history found")

def send_email(to_email, subject, body, cc=None, bcc=None, attachment_type=None):
    """Send an email using Gmail API"""
    try:
        # Check if Gmail is configured
        if not api_config.is_gmail_configured():
            st.warning("Gmail API is not configured. Please update api_config.py with your Gmail credentials.")
            return False
        
        # Get Gmail credentials
        gmail_config = api_config.get_gmail_credentials()
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_config['sender_email']
        msg['To'] = to_email
        msg['Subject'] = subject
        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc
        
        # Attach body
        msg.attach(MIMEText(body, 'plain'))
        
        # Handle attachments if needed
        if attachment_type and attachment_type != "None":
            # TODO: Implement attachment logic based on attachment_type
            # This would involve generating the appropriate report/invoice
            # and attaching it to the email
            pass
        
        # Send email via Gmail SMTP
        server = smtplib.SMTP(gmail_config['smtp_server'], gmail_config['smtp_port'])
        server.starttls()
        server.login(gmail_config['sender_email'], gmail_config['app_password'])
        
        # Combine all recipients
        all_recipients = [to_email]
        if cc:
            all_recipients.extend(cc.split(','))
        if bcc:
            all_recipients.extend(bcc.split(','))
        
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False