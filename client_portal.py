"""
Client Portal Module - Production-Ready with Full Error Handling
Smith & Williams Trucking
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib
import os
import io
from typing import Dict, List, Optional, Tuple
import database_streamlined as db

# File size limits (in MB)
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = ['pdf', 'jpg', 'jpeg', 'png']

class ClientPortal:
    """Secure client portal with comprehensive error handling"""
    
    def __init__(self):
        self.conn = None
        self.initialize_client_tables()
    
    def initialize_client_tables(self):
        """Create/update database tables for client functionality"""
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # First ensure users table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    client_company TEXT,
                    active BOOLEAN DEFAULT 1,
                    is_owner BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check if client_company field exists (for existing databases)
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'client_company' not in columns:
                try:
                    cursor.execute("""
                        ALTER TABLE users 
                        ADD COLUMN client_company TEXT
                    """)
                except:
                    pass  # Column might already exist
            
            # Create document uploads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    move_id INTEGER NOT NULL,
                    document_type TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_data BLOB,
                    file_size INTEGER,
                    uploaded_by TEXT NOT NULL,
                    client_company TEXT,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    verified_by TEXT,
                    verified_time TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (move_id) REFERENCES moves(id)
                )
            """)
            
            # Create audit trail table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    client_company TEXT,
                    action TEXT NOT NULL,
                    move_id INTEGER,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Database initialization error: {str(e)}")
    
    def log_client_action(self, username: str, company: str, action: str, 
                         move_id: Optional[int] = None, details: Optional[str] = None):
        """Log all client actions for audit trail"""
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO client_audit_log (username, client_company, action, move_id, details)
                VALUES (?, ?, ?, ?, ?)
            """, (username, company, action, move_id, details))
            
            conn.commit()
            conn.close()
        except Exception as e:
            # Don't show error to client, but log it internally
            print(f"Audit log error: {str(e)}")
    
    def get_client_moves(self, client_company: str) -> pd.DataFrame:
        """Get moves for a specific client with proper error handling"""
        try:
            # Validate input
            if not client_company:
                return pd.DataFrame()
            
            # Sanitize company name for SQL
            client_company = client_company.strip()
            
            # Get moves from database
            moves_df = db.get_all_trailer_moves()
            
            if moves_df.empty:
                return pd.DataFrame()
            
            # Filter by client company in locations (case-insensitive)
            # Using pandas filtering to avoid SQL injection
            client_moves = moves_df[
                (moves_df['delivery_location'].str.contains(client_company, case=False, na=False)) |
                (moves_df['pickup_location'].str.contains(client_company, case=False, na=False))
            ].copy()
            
            # Sort by date (most recent first)
            if not client_moves.empty:
                client_moves['move_date'] = pd.to_datetime(client_moves['move_date'])
                client_moves = client_moves.sort_values('move_date', ascending=False)
            
            return client_moves
            
        except Exception as e:
            st.error("Unable to retrieve moves. Please contact support.")
            self.log_client_action(
                st.session_state.get('username', 'unknown'),
                client_company,
                'ERROR_FETCHING_MOVES',
                details=str(e)
            )
            return pd.DataFrame()
    
    def validate_file_upload(self, file) -> Tuple[bool, str]:
        """Validate uploaded file for security and size"""
        try:
            if not file:
                return False, "No file selected"
            
            # Check file size
            file_size = file.size
            max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
            
            if file_size > max_size_bytes:
                return False, f"File size exceeds {MAX_FILE_SIZE_MB}MB limit"
            
            # Check file type
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in ALLOWED_FILE_TYPES:
                return False, f"File type .{file_extension} not allowed. Use: {', '.join(ALLOWED_FILE_TYPES)}"
            
            # Validate file name for security
            if '..' in file.name or '/' in file.name or '\\' in file.name:
                return False, "Invalid file name"
            
            return True, "Valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def save_document(self, move_id: int, doc_type: str, file, username: str, company: str) -> bool:
        """Save uploaded document with full error handling"""
        try:
            # Validate file first
            is_valid, message = self.validate_file_upload(file)
            if not is_valid:
                st.error(message)
                return False
            
            # Read file data
            file_data = file.read()
            file_size = len(file_data)
            
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Save document
            cursor.execute("""
                INSERT INTO document_uploads 
                (move_id, document_type, file_name, file_data, file_size, 
                 uploaded_by, client_company, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (move_id, doc_type, file.name, file_data, file_size, username, company))
            
            # Update move status based on document type
            if doc_type == 'rate_confirmation':
                cursor.execute("""
                    UPDATE moves 
                    SET rate_confirmation_sent = 1
                    WHERE id = ?
                """, (move_id,))
            elif doc_type == 'bol':
                # Mark BOL as received (you may want to add a bol_received field)
                pass
            
            conn.commit()
            conn.close()
            
            # Log the action
            self.log_client_action(
                username, company, f'UPLOADED_{doc_type.upper()}',
                move_id, f"File: {file.name}, Size: {file_size} bytes"
            )
            
            return True
            
        except Exception as e:
            st.error(f"Failed to save document. Please try again or contact support.")
            self.log_client_action(
                username, company, 'ERROR_UPLOADING_DOCUMENT',
                move_id, str(e)
            )
            return False
    
    def show_client_dashboard(self):
        """Main client dashboard with comprehensive error handling"""
        try:
            st.title("📋 Move Status Portal")
            
            # Get client info from session
            username = st.session_state.get('username', 'Client')
            client_company = st.session_state.get('client_company', username)
            
            # Security check - ensure user has client_viewer role
            user_role = st.session_state.get('user_role', '')
            if user_role != 'client_viewer':
                st.error("Access denied. This portal is for clients only.")
                self.log_client_action(
                    username, client_company, 'UNAUTHORIZED_ACCESS_ATTEMPT'
                )
                return
            
            st.caption(f"Welcome, {client_company}")
            
            # Session timeout warning
            if 'last_activity' in st.session_state:
                last_activity = st.session_state['last_activity']
                time_since = datetime.now() - last_activity
                if time_since.seconds > 1800:  # 30 minutes
                    st.warning("⚠️ Your session will expire soon. Please save your work.")
            
            st.session_state['last_activity'] = datetime.now()
            
            # Get client moves with error handling
            client_moves = self.get_client_moves(client_company)
            
            if client_moves.empty:
                st.info("No moves found for your account. If you believe this is an error, please contact your coordinator.")
                self.log_client_action(username, client_company, 'VIEW_DASHBOARD_NO_MOVES')
                return
            
            # Log dashboard access
            self.log_client_action(username, client_company, 'VIEW_DASHBOARD', 
                                  details=f"Found {len(client_moves)} moves")
            
            # Display metrics with error handling
            try:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    pending = len(client_moves[client_moves['status'] == 'assigned'])
                    st.metric("🟡 Pending", pending)
                
                with col2:
                    in_progress = len(client_moves[client_moves['status'] == 'in_progress'])
                    st.metric("🔵 In Transit", in_progress)
                
                with col3:
                    awaiting_docs = len(client_moves[
                        (client_moves['status'] == 'completed') & 
                        (client_moves.get('pod_uploaded', False) != True)
                    ])
                    st.metric("📄 Awaiting Docs", awaiting_docs)
                
                with col4:
                    completed = len(client_moves[client_moves['status'] == 'completed'])
                    st.metric("✅ Completed", completed)
                
            except Exception as e:
                st.error("Error loading metrics. Refreshing may help.")
                self.log_client_action(username, client_company, 'ERROR_LOADING_METRICS', details=str(e))
            
            st.divider()
            
            # Document management section
            self.show_document_management(client_moves, username, client_company)
            
            st.divider()
            
            # Move details section
            self.show_move_details(client_moves, username, client_company)
            
        except Exception as e:
            st.error("An unexpected error occurred. Please refresh the page or contact support.")
            self.log_client_action(
                st.session_state.get('username', 'unknown'),
                st.session_state.get('client_company', 'unknown'),
                'CRITICAL_ERROR',
                details=str(e)
            )
    
    def show_document_management(self, client_moves: pd.DataFrame, username: str, client_company: str):
        """Document upload section with full validation"""
        try:
            st.markdown("### 📄 Document Management")
            
            doc_tabs = st.tabs(["📤 Upload Documents (Optional)", "⏳ Pending Actions"])
            
            with doc_tabs[0]:
                st.info("📧 **Option 1**: Email documents to your coordinator as usual\n\n💻 **Option 2**: Upload directly here for faster processing")
                
                st.warning("⚠️ **File Requirements**: PDF, JPG, PNG only. Max size: 10MB")
                
                upload_col1, upload_col2 = st.columns(2)
                
                # Rate Confirmation Upload
                with upload_col1:
                    st.markdown("**📝 Rate Confirmation Upload**")
                    
                    rc_eligible = client_moves[client_moves['status'] == 'assigned']
                    
                    if not rc_eligible.empty:
                        rc_options = {}
                        for _, move in rc_eligible.iterrows():
                            move_label = f"Move #{move['id']}: {move.get('new_trailer', 'N/A')} ↔️ {move.get('old_trailer', 'N/A')}"
                            rc_options[move_label] = move['id']
                        
                        selected_rc_move = st.selectbox(
                            "Select move for Rate Con:",
                            options=list(rc_options.keys()),
                            key="rc_move_select"
                        )
                        
                        rc_file = st.file_uploader(
                            "Drag & drop Rate Confirmation",
                            type=ALLOWED_FILE_TYPES,
                            key="rc_upload",
                            help="Upload signed Rate Confirmation"
                        )
                        
                        if rc_file and st.button("📤 Submit Rate Con", type="primary", key="rc_submit"):
                            move_id = rc_options[selected_rc_move]
                            
                            with st.spinner("Uploading document..."):
                                if self.save_document(move_id, 'rate_confirmation', 
                                                    rc_file, username, client_company):
                                    st.success(f"✅ Rate Confirmation uploaded for Move #{move_id}")
                                    st.balloons()
                                    
                                    # Log successful upload
                                    self.log_client_action(username, client_company, 
                                                         'RATE_CON_UPLOADED', move_id)
                                    
                                    # Refresh in 2 seconds
                                    st.info("Page will refresh in 2 seconds...")
                                    st.rerun()
                    else:
                        st.info("No moves awaiting Rate Confirmation")
                
                # BOL Upload
                with upload_col2:
                    st.markdown("**📋 BOL Upload**")
                    
                    bol_eligible = client_moves[
                        (client_moves['status'] == 'completed') &
                        (client_moves.get('pod_uploaded', False) == True)
                    ]
                    
                    if not bol_eligible.empty:
                        bol_options = {}
                        for _, move in bol_eligible.iterrows():
                            move_label = f"Move #{move['id']}: {move.get('delivery_location', 'N/A')}"
                            bol_options[move_label] = move['id']
                        
                        selected_bol_move = st.selectbox(
                            "Select completed move:",
                            options=list(bol_options.keys()),
                            key="bol_move_select"
                        )
                        
                        bol_file = st.file_uploader(
                            "Drag & drop signed BOL",
                            type=ALLOWED_FILE_TYPES,
                            key="bol_upload",
                            help="Upload signed Bill of Lading"
                        )
                        
                        if bol_file and st.button("📤 Submit BOL", type="primary", key="bol_submit"):
                            move_id = bol_options[selected_bol_move]
                            
                            with st.spinner("Uploading document..."):
                                if self.save_document(move_id, 'bol', 
                                                    bol_file, username, client_company):
                                    st.success(f"✅ BOL uploaded for Move #{move_id}")
                                    st.balloons()
                                    
                                    # Log successful upload
                                    self.log_client_action(username, client_company, 
                                                         'BOL_UPLOADED', move_id)
                                    
                                    # Refresh in 2 seconds
                                    st.info("Page will refresh in 2 seconds...")
                                    st.rerun()
                    else:
                        st.info("No moves awaiting BOL")
            
            # Pending Actions Tab
            with doc_tabs[1]:
                self.show_pending_actions(client_moves, username, client_company)
                
        except Exception as e:
            st.error("Error in document management. Please try again.")
            self.log_client_action(username, client_company, 'ERROR_DOCUMENT_SECTION', details=str(e))
    
    def show_pending_actions(self, client_moves: pd.DataFrame, username: str, client_company: str):
        """Show pending document requirements"""
        try:
            needs_ratecon = client_moves[
                (client_moves['status'] == 'assigned') &
                (client_moves.get('rate_confirmation_sent', False) != True)
            ]
            
            needs_bol = client_moves[
                (client_moves['status'] == 'completed') &
                (client_moves.get('pod_uploaded', False) == True)
            ]
            
            if not needs_ratecon.empty:
                st.warning("📤 **Action Required: Rate Confirmations**")
                for _, move in needs_ratecon.iterrows():
                    with st.container():
                        st.write(f"• Move #{move['id']}: {move.get('new_trailer', 'N/A')} ↔️ {move.get('old_trailer', 'N/A')}")
                        st.write(f"  📍 Route assigned - Please upload Rate Confirmation in Upload tab")
            
            if not needs_bol.empty:
                st.info("✅ **Action Required: BOL Signatures**")
                for _, move in needs_bol.iterrows():
                    with st.container():
                        st.write(f"• Move #{move['id']}: Delivered to {move.get('delivery_location', 'N/A')}")
                        st.write(f"  ✅ POD received - Please upload signed BOL in Upload tab")
            
            if needs_ratecon.empty and needs_bol.empty:
                st.success("✅ All documents up to date! No actions required.")
                
        except Exception as e:
            st.error("Error loading pending actions.")
            self.log_client_action(username, client_company, 'ERROR_PENDING_ACTIONS', details=str(e))
    
    def show_move_details(self, client_moves: pd.DataFrame, username: str, client_company: str):
        """Display move details with filtering"""
        try:
            st.markdown("### 🚛 Your Moves")
            
            # Status filter
            status_filter = st.selectbox(
                "Filter by status:",
                ["All", "Pending", "In Transit", "Completed"],
                index=0
            )
            
            if status_filter != "All":
                status_map = {
                    "Pending": "assigned",
                    "In Transit": "in_progress",
                    "Completed": "completed"
                }
                filtered_moves = client_moves[client_moves['status'] == status_map[status_filter]]
            else:
                filtered_moves = client_moves
            
            if filtered_moves.empty:
                st.info(f"No {status_filter.lower()} moves found.")
                return
            
            # Display moves
            for _, move in filtered_moves.iterrows():
                status_emoji = {
                    'assigned': '🟡',
                    'in_progress': '🔵',
                    'completed': '✅',
                    'awaiting_pod': '📸'
                }.get(move.get('status', ''), '⏳')
                
                move_status = move.get('status', 'unknown').replace('_', ' ').title()
                
                with st.expander(f"{status_emoji} Move #{move['id']} - {move_status}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Move Details:**")
                        st.write(f"📦 New Trailer: {move.get('new_trailer', 'N/A')}")
                        st.write(f"📦 Old Trailer: {move.get('old_trailer', 'N/A')}")
                        st.write(f"📅 Date: {move.get('move_date', 'N/A')}")
                    
                    with col2:
                        st.write("**Locations:**")
                        st.write(f"📍 From: {move.get('pickup_location', 'N/A')}")
                        st.write(f"📍 To: {move.get('delivery_location', 'N/A')}")
                        
                        # Progress indicator
                        self.show_progress_bar(move.get('status', ''))
                    
                    # Document status
                    st.divider()
                    self.show_document_status(move)
                    
                    # Log view
                    self.log_client_action(username, client_company, 'VIEW_MOVE_DETAILS', 
                                         move['id'], f"Status: {move_status}")
                    
        except Exception as e:
            st.error("Error displaying move details.")
            self.log_client_action(username, client_company, 'ERROR_MOVE_DETAILS', details=str(e))
    
    def show_progress_bar(self, status: str):
        """Show visual progress indicator"""
        try:
            if status == 'assigned':
                st.progress(0.25, "Awaiting driver dispatch")
            elif status == 'in_progress':
                st.progress(0.50, "Driver en route")
            elif status == 'awaiting_pod':
                st.progress(0.75, "Delivered - awaiting documentation")
            elif status == 'completed':
                st.progress(1.0, "Move complete")
            else:
                st.progress(0.0, "Status unknown")
        except:
            pass  # Don't break the UI for progress bar errors
    
    def show_document_status(self, move: pd.Series):
        """Show document status for a move"""
        try:
            doc_col1, doc_col2 = st.columns(2)
            
            with doc_col1:
                if move.get('rate_confirmation_sent'):
                    st.success("✅ Rate Confirmation Received")
                else:
                    st.warning("⏳ Rate Confirmation Pending")
            
            with doc_col2:
                if move.get('pod_uploaded'):
                    st.success("✅ POD Received")
                else:
                    st.info("⏳ Awaiting POD from Driver")
        except:
            st.info("Document status unavailable")

# Initialize client portal
client_portal = ClientPortal()