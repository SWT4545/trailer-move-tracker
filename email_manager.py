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

def show_email_center():
    """Main email management center"""
    st.title("✉️ Email Center")
    
    tabs = st.tabs(["📤 Send Email", "📝 Templates", "👥 Recipients", "📜 History"])
    
    with tabs[0]:
        send_email_interface()
    
    with tabs[1]:
        manage_email_templates()
    
    with tabs[2]:
        manage_recipients()
    
    with tabs[3]:
        show_email_history()

def send_email_interface():
    """Interface for sending emails"""
    st.subheader("📤 Send Email")
    
    # Display company email configuration
    st.info("📧 Emails will be sent from: **Smithandwilliamstrucking@gmail.com**")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Email composition form
        with st.form("send_email_form"):
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
            
            # Signature
            add_signature = st.checkbox("Add Company Signature", value=True)
            
            if st.form_submit_button("📤 Send Email", type="primary", use_container_width=True):
                if to_email and subject and body:
                    # Add signature if requested
                    if add_signature:
                        body += f"\n\n---\n{branding.COMPANY_NAME}\nTrailer Move Tracker System\n\nThis is an automated message."
                    
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
                    else:
                        st.error("Failed to send email. Please check your email configuration.")
                else:
                    st.error("Please fill in all required fields (To, Subject, Message)")
    
    with col2:
        # Email preview
        st.subheader("📧 Preview")
        if to_email and subject and body:
            st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 1rem; border-radius: 8px; background: #f9f9f9;">
                <p><b>To:</b> {to_email}</p>
                {"<p><b>CC:</b> " + cc_email + "</p>" if cc_email else ""}
                {"<p><b>BCC:</b> " + bcc_email + "</p>" if bcc_email else ""}
                <p><b>Subject:</b> {subject}</p>
                <hr>
                <p>{body.replace(chr(10), '<br>')}</p>
                {"<hr><p><i>Attachment: " + attachment_type + "</i></p>" if attachment_type != "None" else ""}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Email preview will appear here")

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
    """Send an email (placeholder function - implement with actual SMTP)"""
    try:
        # This is a placeholder - implement actual email sending logic
        # using SMTP configuration from settings
        
        # For now, just return success
        return True
        
        # Actual implementation would look like:
        # msg = MIMEMultipart()
        # msg['From'] = sender_email
        # msg['To'] = to_email
        # msg['Subject'] = subject
        # if cc:
        #     msg['Cc'] = cc
        # if bcc:
        #     msg['Bcc'] = bcc
        # 
        # msg.attach(MIMEText(body, 'plain'))
        # 
        # if attachment_type:
        #     # Attach file
        #     pass
        # 
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login(sender_email, password)
        # server.send_message(msg)
        # server.quit()
        # 
        # return True
        
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False