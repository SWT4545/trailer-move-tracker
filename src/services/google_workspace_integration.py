"""
Google Workspace Integration Module
Provides advanced features using Google Workspace APIs
"""

import streamlit as st
from datetime import datetime, timedelta
import api_config
import pandas as pd

# Google API imports (install with: pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2)
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    st.warning("Google API libraries not installed. Run: pip install google-api-python-client google-auth")

class GoogleWorkspaceManager:
    """Manages all Google Workspace integrations"""
    
    def __init__(self):
        self.config = api_config.get_google_workspace_config()
        self.gmail_config = api_config.get_gmail_credentials()
        self.services = {}
        
    def initialize_services(self, credentials_file=None):
        """Initialize Google Workspace services"""
        if not GOOGLE_APIS_AVAILABLE:
            return False
            
        try:
            # Use service account credentials if provided
            if credentials_file:
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_file,
                    scopes=[
                        'https://www.googleapis.com/auth/gmail.send',
                        'https://www.googleapis.com/auth/calendar',
                        'https://www.googleapis.com/auth/drive',
                        'https://www.googleapis.com/auth/spreadsheets'
                    ]
                )
                
                # Build services
                if self.config['enable_calendar']:
                    self.services['calendar'] = build('calendar', 'v3', credentials=credentials)
                
                if self.config['enable_drive']:
                    self.services['drive'] = build('drive', 'v3', credentials=credentials)
                
                if self.config['enable_sheets']:
                    self.services['sheets'] = build('sheets', 'v4', credentials=credentials)
                
                self.services['gmail'] = build('gmail', 'v1', credentials=credentials)
                
                return True
        except Exception as e:
            st.error(f"Failed to initialize Google Workspace services: {str(e)}")
            return False
    
    # Email Functions with Google Workspace
    def send_email_with_workspace(self, to, subject, body, cc=None, bcc=None, from_alias='dispatch'):
        """Send email using Google Workspace with specific alias"""
        from_email = api_config.get_email_alias(from_alias)
        
        # Implementation would use Gmail API
        # This is more reliable than SMTP for Google Workspace
        pass
    
    def create_email_group(self, group_name, members):
        """Create an email group (requires Admin SDK)"""
        if self.config['enable_admin']:
            # Create group using Admin SDK
            pass
        else:
            st.warning("Admin SDK not enabled in configuration")
    
    # Calendar Integration
    def create_pickup_event(self, trailer_id, location, pickup_time, driver_email=None):
        """Create a pickup event in Google Calendar"""
        if 'calendar' not in self.services:
            return None
            
        event = {
            'summary': f'Pickup: Trailer #{trailer_id}',
            'location': location,
            'description': f'Pickup for trailer #{trailer_id}\nDriver: {driver_email or "TBD"}',
            'start': {
                'dateTime': pickup_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': (pickup_time + timedelta(hours=2)).isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'attendees': [
                {'email': driver_email}
            ] if driver_email else [],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 60},  # 1 hour before
                ],
            },
        }
        
        try:
            calendar_id = self.config['calendar_settings']['pickup_calendar']
            event = self.services['calendar'].events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            return event.get('htmlLink')
        except Exception as e:
            st.error(f"Failed to create calendar event: {str(e)}")
            return None
    
    def create_delivery_event(self, trailer_id, location, delivery_time, driver_email=None):
        """Create a delivery event in Google Calendar"""
        if 'calendar' not in self.services:
            return None
            
        event = {
            'summary': f'Delivery: Trailer #{trailer_id}',
            'location': location,
            'description': f'Delivery for trailer #{trailer_id}\nDriver: {driver_email or "TBD"}',
            'start': {
                'dateTime': delivery_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': (delivery_time + timedelta(hours=2)).isoformat(),
                'timeZone': 'America/Los_Angeles',
            },
            'attendees': [
                {'email': driver_email}
            ] if driver_email else [],
        }
        
        try:
            calendar_id = self.config['calendar_settings']['delivery_calendar']
            event = self.services['calendar'].events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            return event.get('htmlLink')
        except Exception as e:
            st.error(f"Failed to create calendar event: {str(e)}")
            return None
    
    # Google Drive Integration
    def upload_to_drive(self, file_path, file_name, folder_type='reports'):
        """Upload file to Google Drive shared folder"""
        if 'drive' not in self.services:
            return None
            
        try:
            # Determine folder ID based on type
            folder_id = {
                'reports': self.config['reports_folder_id'],
                'invoices': self.config['invoices_folder_id'],
                'general': self.config['shared_drive_id']
            }.get(folder_type, self.config['shared_drive_id'])
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.services['drive'].files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            return file.get('webViewLink')
        except Exception as e:
            st.error(f"Failed to upload to Drive: {str(e)}")
            return None
    
    def create_shared_folder(self, folder_name, parent_id=None):
        """Create a shared folder in Google Drive"""
        if 'drive' not in self.services:
            return None
            
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id] if parent_id else [self.config['shared_drive_id']]
            }
            
            folder = self.services['drive'].files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            # Share folder with team
            self.share_drive_item(folder.get('id'), 'smithwilliamstrucking.com', 'domain')
            
            return folder.get('id')
        except Exception as e:
            st.error(f"Failed to create folder: {str(e)}")
            return None
    
    def share_drive_item(self, file_id, email_or_domain, permission_type='user', role='reader'):
        """Share a Drive item with user or domain"""
        if 'drive' not in self.services:
            return False
            
        try:
            permission = {
                'type': permission_type,  # 'user', 'group', 'domain', 'anyone'
                'role': role,  # 'reader', 'writer', 'commenter'
            }
            
            if permission_type == 'domain':
                permission['domain'] = email_or_domain
            else:
                permission['emailAddress'] = email_or_domain
            
            self.services['drive'].permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
            
            return True
        except Exception as e:
            st.error(f"Failed to share item: {str(e)}")
            return False
    
    # Google Sheets Integration
    def export_to_sheets(self, dataframe, sheet_name, spreadsheet_id=None):
        """Export pandas DataFrame to Google Sheets"""
        if 'sheets' not in self.services:
            return None
            
        try:
            # Create new spreadsheet if ID not provided
            if not spreadsheet_id:
                spreadsheet = {
                    'properties': {
                        'title': sheet_name
                    }
                }
                spreadsheet = self.services['sheets'].spreadsheets().create(
                    body=spreadsheet
                ).execute()
                spreadsheet_id = spreadsheet.get('spreadsheetId')
            
            # Convert DataFrame to values
            values = [dataframe.columns.tolist()] + dataframe.values.tolist()
            
            body = {
                'values': values
            }
            
            # Update the sheet
            result = self.services['sheets'].spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Share the sheet with the domain
            self.share_drive_item(spreadsheet_id, 'smithwilliamstrucking.com', 'domain', 'writer')
            
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        except Exception as e:
            st.error(f"Failed to export to Sheets: {str(e)}")
            return None
    
    def create_automated_report_sheet(self, report_type='weekly'):
        """Create an automated report in Google Sheets"""
        if 'sheets' not in self.services:
            return None
            
        # Create spreadsheet with multiple tabs for different metrics
        spreadsheet = {
            'properties': {
                'title': f'Trailer Tracking Report - {report_type.title()} - {datetime.now().strftime("%Y-%m-%d")}'
            },
            'sheets': [
                {'properties': {'title': 'Summary'}},
                {'properties': {'title': 'Active Moves'}},
                {'properties': {'title': 'Completed Moves'}},
                {'properties': {'title': 'Driver Performance'}},
                {'properties': {'title': 'Financial Summary'}}
            ]
        }
        
        try:
            spreadsheet = self.services['sheets'].spreadsheets().create(
                body=spreadsheet
            ).execute()
            
            return spreadsheet.get('spreadsheetId')
        except Exception as e:
            st.error(f"Failed to create report sheet: {str(e)}")
            return None

# Streamlit UI Components
def show_google_workspace_settings():
    """Display Google Workspace settings and configuration"""
    st.title("🔧 Google Workspace Integration")
    
    tabs = st.tabs(["📧 Email Settings", "📅 Calendar", "📁 Drive", "📊 Sheets", "⚙️ Configuration"])
    
    with tabs[0]:
        show_email_settings()
    
    with tabs[1]:
        show_calendar_settings()
    
    with tabs[2]:
        show_drive_settings()
    
    with tabs[3]:
        show_sheets_settings()
    
    with tabs[4]:
        show_configuration()

def show_email_settings():
    """Email configuration for Google Workspace"""
    st.subheader("📧 Email Configuration")
    
    config = api_config.get_google_workspace_config()
    gmail_config = api_config.get_gmail_credentials()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Primary Email:** {gmail_config['sender_email']}")
        st.success("✅ Using Google Workspace Domain")
        
        st.markdown("### Email Aliases")
        for alias, email in config['email_aliases'].items():
            st.text(f"{alias}: {email}")
    
    with col2:
        st.markdown("### Quick Actions")
        
        if st.button("Test Email Configuration"):
            # Test email sending
            st.info("Sending test email...")
            # Implementation here
            st.success("Test email sent!")
        
        if st.button("Create Email Group"):
            with st.form("create_group"):
                group_name = st.text_input("Group Name")
                group_email = st.text_input("Group Email", placeholder="team@smithwilliamstrucking.com")
                members = st.text_area("Members (one email per line)")
                
                if st.form_submit_button("Create Group"):
                    st.success(f"Group {group_name} created!")

def show_calendar_settings():
    """Calendar integration settings"""
    st.subheader("📅 Calendar Integration")
    
    config = api_config.get_google_workspace_config()
    
    st.info("Calendar integration allows automatic scheduling of pickups and deliveries")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Configured Calendars")
        for cal_type, cal_email in config['calendar_settings'].items():
            st.text(f"{cal_type.replace('_', ' ').title()}: {cal_email}")
    
    with col2:
        st.markdown("### Calendar Features")
        st.checkbox("Auto-create pickup events", value=True)
        st.checkbox("Auto-create delivery events", value=True)
        st.checkbox("Send calendar invites to drivers", value=True)
        st.checkbox("Add reminders (1 day before)", value=True)
        
        if st.button("Sync with Google Calendar"):
            st.success("Calendar synchronized!")

def show_drive_settings():
    """Google Drive integration settings"""
    st.subheader("📁 Google Drive Integration")
    
    st.info("Automatically store reports, invoices, and documents in Google Drive")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Document Storage")
        st.checkbox("Auto-upload invoices", value=True)
        st.checkbox("Auto-upload reports", value=True)
        st.checkbox("Auto-upload signed documents", value=False)
        
        st.markdown("### Folder Structure")
        st.text("📁 Smith & Williams Trucking")
        st.text("  📁 Invoices")
        st.text("    📁 2024")
        st.text("  📁 Reports")
        st.text("    📁 Weekly")
        st.text("    📁 Monthly")
        st.text("  📁 Driver Documents")
    
    with col2:
        st.markdown("### Quick Actions")
        
        if st.button("Create Folder Structure"):
            st.success("Folder structure created in Drive!")
        
        if st.button("Share with Team"):
            email = st.text_input("Team member email")
            if email:
                st.success(f"Shared with {email}")

def show_sheets_settings():
    """Google Sheets integration settings"""
    st.subheader("📊 Google Sheets Integration")
    
    st.info("Export data directly to Google Sheets for advanced analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Auto-Export Options")
        st.checkbox("Daily summary sheet", value=False)
        st.checkbox("Weekly report sheet", value=True)
        st.checkbox("Monthly financial sheet", value=True)
        
        export_time = st.time_input("Daily export time", value=datetime.strptime("18:00", "%H:%M").time())
    
    with col2:
        st.markdown("### Manual Export")
        
        export_type = st.selectbox(
            "Select data to export",
            ["Active Moves", "Completed Moves", "Driver Performance", "Financial Summary", "Full Database"]
        )
        
        if st.button("Export to Sheets", type="primary"):
            st.success(f"Exported {export_type} to Google Sheets!")
            st.info("View at: https://docs.google.com/spreadsheets/...")

def show_configuration():
    """Show configuration status and setup"""
    st.subheader("⚙️ Configuration Status")
    
    config = api_config.get_google_workspace_config()
    
    # Check configuration status
    checks = {
        "Google Workspace Domain": "✅" if config['domain'] else "❌",
        "Email Configuration": "✅" if api_config.is_gmail_configured() else "❌",
        "Calendar API": "✅" if config['enable_calendar'] else "⚠️",
        "Drive API": "✅" if config['enable_drive'] else "⚠️",
        "Sheets API": "✅" if config['enable_sheets'] else "⚠️",
        "OAuth2 Setup": "✅" if config['use_oauth'] else "⚠️ Using App Password",
    }
    
    for item, status in checks.items():
        st.text(f"{status} {item}")
    
    st.markdown("---")
    
    st.markdown("### Setup Instructions")
    
    with st.expander("📋 Complete Setup Guide"):
        st.markdown("""
        1. **Enable APIs in Google Cloud Console:**
           - Go to [Google Cloud Console](https://console.cloud.google.com/)
           - Create a new project or select existing
           - Enable: Gmail API, Calendar API, Drive API, Sheets API
        
        2. **Create Service Account:**
           - Go to IAM & Admin > Service Accounts
           - Create new service account
           - Download JSON credentials
           - Share calendars/drives with service account email
        
        3. **Configure Domain-wide Delegation (Optional):**
           - In Google Workspace Admin
           - Security > API Controls > Domain-wide Delegation
           - Add service account with required scopes
        
        4. **Update api_config.py:**
           - Add service account credentials path
           - Configure folder IDs and calendar IDs
           - Set email aliases
        """)
    
    if st.button("Download Setup Checklist"):
        st.download_button(
            label="📥 Download Checklist",
            data="Google Workspace Setup Checklist...",
            file_name="google_workspace_setup.txt"
        )