"""
W9 Document Management System
Handles W9 uploads and storage for contract drivers
"""

import streamlit as st
import sqlite3
import os
import base64
from datetime import datetime
import pandas as pd
from database_connection_manager import db_manager

class W9Manager:
    def __init__(self):
        self.db_path = 'trailer_tracker_streamlined.db' if os.path.exists('trailer_tracker_streamlined.db') else 'trailer_data.db'
        self.ensure_w9_table()
        self.ensure_w9_folder()
    
    def ensure_w9_table(self):
        """Create W9 documents table if it doesn't exist"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS w9_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        driver_name TEXT NOT NULL,
                        driver_id INTEGER,
                        file_name TEXT,
                        file_path TEXT,
                        file_size INTEGER,
                        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        tax_year INTEGER,
                        ein_or_ssn TEXT,
                        business_name TEXT,
                        status TEXT DEFAULT 'active',
                        verified_by TEXT,
                        verified_date TIMESTAMP,
                        notes TEXT,
                        FOREIGN KEY (driver_id) REFERENCES drivers(id)
                    )
                """)
                
                conn.commit()
        except Exception as e:
            st.warning(f"Could not create W9 table: {e}")
    
    def ensure_w9_folder(self):
        """Create W9 storage folder if it doesn't exist"""
        os.makedirs('w9_documents', exist_ok=True)
    
    def upload_w9(self, driver_name, file, tax_year=None, notes=""):
        """Upload a W9 document for a driver"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_extension = file.name.split('.')[-1]
            safe_driver_name = "".join(c for c in driver_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            file_name = f"W9_{safe_driver_name}_{timestamp}.{file_extension}"
            file_path = os.path.join('w9_documents', file_name)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file.getbuffer())
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Save to database
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get driver ID if exists
                cursor.execute("SELECT id FROM drivers WHERE driver_name = ? OR name = ?", 
                             (driver_name, driver_name))
                driver_result = cursor.fetchone()
                driver_id = driver_result[0] if driver_result else None
                
                # Insert W9 record
                cursor.execute("""
                    INSERT INTO w9_documents 
                    (driver_name, driver_id, file_name, file_path, file_size, tax_year, notes, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
                """, (driver_name, driver_id, file_name, file_path, file_size, 
                     tax_year or datetime.now().year, notes))
                
                conn.commit()
                
            return True, file_name
        except Exception as e:
            return False, str(e)
    
    def get_driver_w9(self, driver_name):
        """Get W9 documents for a specific driver"""
        try:
            with db_manager.get_connection() as conn:
                query = """
                    SELECT * FROM w9_documents 
                    WHERE driver_name = ? AND status = 'active'
                    ORDER BY upload_date DESC
                """
                df = pd.read_sql_query(query, conn, params=(driver_name,))
                return df
        except:
            return pd.DataFrame()
    
    def get_all_w9s(self):
        """Get all W9 documents"""
        try:
            with db_manager.get_connection() as conn:
                query = """
                    SELECT * FROM w9_documents 
                    ORDER BY upload_date DESC
                """
                df = pd.read_sql_query(query, conn)
                return df
        except:
            return pd.DataFrame()
    
    def mark_w9_verified(self, w9_id, verified_by):
        """Mark a W9 as verified"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE w9_documents 
                    SET verified_by = ?, verified_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (verified_by, w9_id))
                conn.commit()
                return True
        except:
            return False
    
    def deactivate_w9(self, w9_id):
        """Deactivate an old W9"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE w9_documents 
                    SET status = 'inactive'
                    WHERE id = ?
                """, (w9_id,))
                conn.commit()
                return True
        except:
            return False

def show_w9_upload_interface(driver_name=None):
    """Show W9 upload interface"""
    w9_manager = W9Manager()
    
    st.markdown("### 📋 W9 Document Upload")
    
    # If no driver specified, allow selection
    if not driver_name:
        # Get list of contract drivers
        try:
            conn = sqlite3.connect(w9_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT d.driver_name 
                FROM drivers d
                LEFT JOIN driver_extended de ON d.id = de.driver_id
                WHERE de.driver_type = 'contractor' OR de.driver_type = 'owner_operator'
                ORDER BY d.driver_name
            """)
            contract_drivers = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if contract_drivers:
                driver_name = st.selectbox("Select Contract Driver", [""] + contract_drivers)
            else:
                st.info("No contract drivers found. W9s are only required for contractors.")
                # Allow manual entry
                driver_name = st.text_input("Or enter driver name manually")
        except:
            driver_name = st.text_input("Enter driver name")
    
    if driver_name:
        # Check for existing W9
        existing_w9s = w9_manager.get_driver_w9(driver_name)
        
        if not existing_w9s.empty:
            st.success(f"✅ W9 on file for {driver_name}")
            
            # Show existing W9s
            with st.expander("View existing W9 documents"):
                for _, w9 in existing_w9s.iterrows():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"📄 {w9['file_name']}")
                        st.caption(f"Uploaded: {w9['upload_date']}")
                    with col2:
                        if w9['verified_by']:
                            st.success(f"✓ Verified by {w9['verified_by']}")
                        else:
                            st.warning("Pending verification")
                    with col3:
                        st.caption(f"Tax Year: {w9.get('tax_year', 'N/A')}")
        
        # Upload new W9
        st.markdown("#### Upload New W9")
        
        with st.form("w9_upload_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                w9_file = st.file_uploader(
                    "Select W9 Document",
                    type=['pdf', 'png', 'jpg', 'jpeg'],
                    help="Upload the completed W9 form"
                )
                
                tax_year = st.number_input(
                    "Tax Year",
                    min_value=2020,
                    max_value=2030,
                    value=datetime.now().year,
                    help="Tax year this W9 applies to"
                )
            
            with col2:
                # Optional fields
                ein_ssn = st.text_input(
                    "EIN/SSN (Last 4 digits only)",
                    max_chars=4,
                    help="Optional - for verification purposes"
                )
                
                business_name = st.text_input(
                    "Business Name",
                    help="Optional - contractor's business name"
                )
                
                notes = st.text_area(
                    "Notes",
                    placeholder="Any additional notes about this W9"
                )
            
            submitted = st.form_submit_button(
                "📤 Upload W9",
                type="primary",
                use_container_width=True
            )
            
            if submitted and w9_file:
                success, result = w9_manager.upload_w9(
                    driver_name,
                    w9_file,
                    tax_year,
                    notes
                )
                
                if success:
                    st.success(f"✅ W9 uploaded successfully: {result}")
                    st.balloons()
                    
                    # Update driver record if needed
                    if ein_ssn or business_name:
                        try:
                            conn = sqlite3.connect(w9_manager.db_path)
                            cursor = conn.cursor()
                            
                            if business_name:
                                cursor.execute("""
                                    UPDATE driver_extended 
                                    SET company_name = ?
                                    WHERE driver_id = (SELECT id FROM drivers WHERE driver_name = ?)
                                """, (business_name, driver_name))
                            
                            conn.commit()
                            conn.close()
                        except:
                            pass
                    
                    st.rerun()
                else:
                    st.error(f"Upload failed: {result}")
            elif submitted:
                st.error("Please select a file to upload")

def show_w9_management_interface():
    """Show W9 management interface for administrators"""
    w9_manager = W9Manager()
    
    st.markdown("### 📋 W9 Document Management")
    
    # Get all W9s
    all_w9s = w9_manager.get_all_w9s()
    
    if not all_w9s.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_w9s = len(all_w9s)
            st.metric("Total W9s", total_w9s)
        
        with col2:
            active_w9s = len(all_w9s[all_w9s['status'] == 'active'])
            st.metric("Active", active_w9s)
        
        with col3:
            verified_w9s = len(all_w9s[all_w9s['verified_by'].notna()])
            st.metric("Verified", verified_w9s)
        
        with col4:
            pending_w9s = len(all_w9s[all_w9s['verified_by'].isna()])
            st.metric("Pending Verification", pending_w9s)
        
        st.divider()
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("Status", ["All", "Active", "Inactive", "Pending Verification"])
        
        with col2:
            year_filter = st.selectbox("Tax Year", ["All"] + sorted(all_w9s['tax_year'].dropna().unique().tolist(), reverse=True))
        
        with col3:
            search = st.text_input("Search Driver", placeholder="Driver name...")
        
        # Apply filters
        filtered_w9s = all_w9s.copy()
        
        if status_filter == "Active":
            filtered_w9s = filtered_w9s[filtered_w9s['status'] == 'active']
        elif status_filter == "Inactive":
            filtered_w9s = filtered_w9s[filtered_w9s['status'] == 'inactive']
        elif status_filter == "Pending Verification":
            filtered_w9s = filtered_w9s[filtered_w9s['verified_by'].isna()]
        
        if year_filter != "All":
            filtered_w9s = filtered_w9s[filtered_w9s['tax_year'] == int(year_filter)]
        
        if search:
            filtered_w9s = filtered_w9s[filtered_w9s['driver_name'].str.contains(search, case=False, na=False)]
        
        # Display W9s
        if not filtered_w9s.empty:
            for _, w9 in filtered_w9s.iterrows():
                with st.expander(f"📄 {w9['driver_name']} - {w9['file_name']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Driver:** {w9['driver_name']}")
                        st.write(f"**Tax Year:** {w9.get('tax_year', 'N/A')}")
                        st.write(f"**Uploaded:** {w9['upload_date']}")
                    
                    with col2:
                        st.write(f"**Status:** {w9['status'].title()}")
                        if w9['verified_by']:
                            st.success(f"✓ Verified by {w9['verified_by']}")
                            st.caption(f"On {w9['verified_date']}")
                        else:
                            st.warning("⏳ Pending verification")
                            
                            if st.button(f"✓ Verify", key=f"verify_{w9['id']}"):
                                if w9_manager.mark_w9_verified(w9['id'], st.session_state.get('user_name', 'Admin')):
                                    st.success("Verified!")
                                    st.rerun()
                    
                    with col3:
                        if w9['notes']:
                            st.write(f"**Notes:** {w9['notes']}")
                        
                        if w9['status'] == 'active':
                            if st.button(f"🗑️ Deactivate", key=f"deactivate_{w9['id']}"):
                                if w9_manager.deactivate_w9(w9['id']):
                                    st.success("Deactivated")
                                    st.rerun()
        else:
            st.info("No W9 documents found matching filters")
    else:
        st.info("No W9 documents uploaded yet")
    
    # Quick upload section
    st.divider()
    with st.expander("📤 Quick W9 Upload"):
        show_w9_upload_interface()

# Export functions
__all__ = ['W9Manager', 'show_w9_upload_interface', 'show_w9_management_interface']