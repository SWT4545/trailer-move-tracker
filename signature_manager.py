"""
Signature Manager - Edit and save email signatures
"""
import streamlit as st
import json
import os
import branding

SIGNATURES_FILE = 'email_signatures_custom.json'

def load_custom_signatures():
    """Load custom signatures from file"""
    if os.path.exists(SIGNATURES_FILE):
        with open(SIGNATURES_FILE, 'r') as f:
            return json.load(f)
    else:
        # Default signatures
        return {
            "default": {
                "name": "Default",
                "content": f"""
Best regards,

Smith & Williams Trucking
Dispatch Department
"{branding.PRIMARY_TAGLINE}"

📧 dispatch@smithwilliamstrucking.com
📱 (555) 123-4567
🌐 www.smithwilliamstrucking.com

📍 123 Trucking Way, Your City, State 12345

---
{branding.EMAIL_DISCLAIMER}"""
            },
            "executive": {
                "name": "Executive (Brandon Smith)",
                "content": f"""
Sincerely,

Brandon Smith
CEO | Smith & Williams Trucking Solutions, LLC
"{branding.SECONDARY_TAGLINE}"

📧 Brandon@smithwilliamstrucking.com
📧 dispatch@smithwilliamstrucking.com
📱 Direct: 951.437.5474
🏢 MC#: 1276006 | DOT#: 3675217
🌐 www.smithwilliamstrucking.com

"{branding.PRIMARY_TAGLINE}"

---
{branding.EMAIL_DISCLAIMER}"""
            },
            "operations": {
                "name": "Operations",
                "content": f"""
Thank you,

Operations Team
Smith & Williams Trucking
"{branding.SHORT_TAGLINE}"

📧 operations@smithwilliamstrucking.com
📱 Operations: (555) 123-4568
📱 24/7 Dispatch: (555) 123-4567

Track your shipment: www.smithwilliamstrucking.com/track

---
{branding.SHORT_DISCLAIMER}"""
            },
            "billing": {
                "name": "Billing",
                "content": f"""
Regards,

Accounts Department
Smith & Williams Trucking
"{branding.SECONDARY_TAGLINE}"

📧 billing@smithwilliamstrucking.com
📱 Billing: (555) 123-4569

Payment Portal: www.smithwilliamstrucking.com/pay

---
{branding.EMAIL_DISCLAIMER}"""
            },
            "minimal": {
                "name": "Minimal",
                "content": f"""
Smith & Williams Trucking | {branding.SHORT_TAGLINE}
dispatch@smithwilliamstrucking.com | (555) 123-4567

{branding.SHORT_DISCLAIMER}"""
            }
        }

def save_custom_signatures(signatures):
    """Save custom signatures to file"""
    with open(SIGNATURES_FILE, 'w') as f:
        json.dump(signatures, f, indent=2)
    return True

def show_signature_manager():
    """Show signature management interface"""
    st.title("✍️ Signature Manager")
    
    # Load current signatures
    if 'signatures' not in st.session_state:
        st.session_state.signatures = load_custom_signatures()
    
    tabs = st.tabs(["📝 Edit Signatures", "➕ Add New", "👁️ Preview"])
    
    with tabs[0]:
        edit_signatures()
    
    with tabs[1]:
        add_new_signature()
    
    with tabs[2]:
        preview_signatures()

def edit_signatures():
    """Edit existing signatures"""
    st.subheader("Edit Email Signatures")
    
    # Select signature to edit
    signature_names = list(st.session_state.signatures.keys())
    selected_sig = st.selectbox(
        "Select signature to edit",
        signature_names,
        format_func=lambda x: st.session_state.signatures[x]['name']
    )
    
    if selected_sig:
        sig_data = st.session_state.signatures[selected_sig]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Edit form
            with st.form(f"edit_{selected_sig}"):
                new_name = st.text_input("Signature Name", value=sig_data['name'])
                new_content = st.text_area(
                    "Signature Content",
                    value=sig_data['content'],
                    height=300,
                    help="Edit your signature here. You can use emojis and formatting."
                )
                
                col_save, col_delete = st.columns(2)
                with col_save:
                    if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                        st.session_state.signatures[selected_sig]['name'] = new_name
                        st.session_state.signatures[selected_sig]['content'] = new_content
                        save_custom_signatures(st.session_state.signatures)
                        st.success(f"✅ Signature '{new_name}' saved!")
                        st.rerun()
                
                with col_delete:
                    if st.form_submit_button("🗑️ Delete Signature", use_container_width=True):
                        if len(st.session_state.signatures) > 1:
                            del st.session_state.signatures[selected_sig]
                            save_custom_signatures(st.session_state.signatures)
                            st.success("Signature deleted!")
                            st.rerun()
                        else:
                            st.error("Cannot delete the last signature")
        
        with col2:
            st.markdown("### Preview")
            st.text(new_content if 'new_content' in locals() else sig_data['content'])

def add_new_signature():
    """Add a new signature"""
    st.subheader("Add New Signature")
    
    with st.form("add_signature"):
        sig_id = st.text_input("Signature ID", placeholder="e.g., customer_service", help="Unique identifier (lowercase, no spaces)")
        sig_name = st.text_input("Signature Name", placeholder="e.g., Customer Service")
        sig_content = st.text_area(
            "Signature Content",
            height=250,
            placeholder="""Your Name
Your Title
Smith & Williams Trucking

📧 email@smithwilliamstrucking.com
📱 (555) 123-4567"""
        )
        
        if st.form_submit_button("➕ Add Signature", type="primary"):
            if sig_id and sig_name and sig_content:
                # Clean up the ID
                sig_id = sig_id.lower().replace(' ', '_')
                
                if sig_id not in st.session_state.signatures:
                    st.session_state.signatures[sig_id] = {
                        'name': sig_name,
                        'content': sig_content
                    }
                    save_custom_signatures(st.session_state.signatures)
                    st.success(f"✅ Signature '{sig_name}' added!")
                    st.rerun()
                else:
                    st.error("A signature with this ID already exists")
            else:
                st.error("Please fill in all fields")

def preview_signatures():
    """Preview all signatures"""
    st.subheader("Preview All Signatures")
    
    for sig_id, sig_data in st.session_state.signatures.items():
        with st.expander(f"📧 {sig_data['name']}"):
            st.text(sig_data['content'])
            st.markdown("---")
            st.caption(f"ID: {sig_id}")

def get_signature_for_email(signature_type):
    """Get a signature for use in email"""
    signatures = load_custom_signatures()
    sig_key = signature_type.lower().replace(' ', '_')
    
    if sig_key in signatures:
        return signatures[sig_key]['content']
    elif signature_type.lower() in signatures:
        return signatures[signature_type.lower()]['content']
    else:
        # Return default if not found
        return signatures.get('default', {}).get('content', '')

def get_signature_list():
    """Get list of signature names for dropdown"""
    signatures = load_custom_signatures()
    return [sig['name'] for sig in signatures.values()]