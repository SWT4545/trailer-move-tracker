"""
Comprehensive Document Management System
Handles all file uploads: BOLs, PODs, Rate Confirmations, Photos, W9s, Insurance, etc.
Links documents to drivers, moves, and trailers
"""

import streamlit as st
import sqlite3
import os
import shutil
from datetime import datetime
import base64
import pandas as pd
from PIL import Image
import io

class DocumentManagementSystem:
    """Complete document management for all system needs"""
    
    def __init__(self):
        self.db_path = 'trailer_tracker_streamlined.db'
        self.ensure_document_tables()
        self.ensure_storage_folders()
    
    def ensure_document_tables(self):
        """Create all document-related tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type TEXT NOT NULL,
                document_category TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                mime_type TEXT,
                
                -- Relationships
                driver_id INTEGER,
                driver_name TEXT,
                move_id TEXT,
                trailer_number TEXT,
                customer_name TEXT,
                
                -- Document specifics
                expiry_date DATE,
                effective_date DATE,
                reference_number TEXT,
                
                -- Status tracking
                status TEXT DEFAULT 'active',
                verified INTEGER DEFAULT 0,
                verified_by TEXT,
                verified_date TIMESTAMP,
                
                -- Metadata
                uploaded_by TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                tags TEXT,
                
                -- Foreign keys
                FOREIGN KEY (driver_id) REFERENCES drivers(id),
                FOREIGN KEY (move_id) REFERENCES moves(move_id)
            )
        ''')
        
        # BOL (Bill of Lading) specific table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bol_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                move_id TEXT NOT NULL,
                bol_number TEXT UNIQUE,
                shipper_name TEXT,
                consignee_name TEXT,
                pickup_date DATE,
                delivery_date DATE,
                commodity TEXT,
                weight TEXT,
                pieces INTEGER,
                driver_signature INTEGER DEFAULT 0,
                shipper_signature INTEGER DEFAULT 0,
                consignee_signature INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (move_id) REFERENCES moves(move_id)
            )
        ''')
        
        # POD (Proof of Delivery) specific table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pod_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                move_id TEXT NOT NULL,
                delivery_date DATE,
                delivery_time TIME,
                receiver_name TEXT,
                receiver_signature INTEGER DEFAULT 0,
                delivery_notes TEXT,
                condition_notes TEXT,
                photos_attached INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (move_id) REFERENCES moves(move_id)
            )
        ''')
        
        # Rate Confirmation specific table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_confirmations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                move_id TEXT,
                confirmation_number TEXT UNIQUE,
                broker_name TEXT,
                broker_mc TEXT,
                agreed_rate REAL,
                fuel_surcharge REAL,
                total_rate REAL,
                payment_terms TEXT,
                pickup_date DATE,
                delivery_date DATE,
                commodity TEXT,
                special_instructions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        ''')
        
        # Photo documentation table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photo_documentation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                related_to TEXT, -- 'move', 'trailer', 'incident', 'inspection'
                related_id TEXT,
                photo_type TEXT, -- 'damage', 'loading', 'delivery', 'inspection', 'incident'
                location TEXT,
                timestamp TIMESTAMP,
                gps_coordinates TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        ''')
        
        # Insurance documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insurance_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                driver_id INTEGER,
                insurance_type TEXT, -- 'liability', 'cargo', 'physical_damage', 'workers_comp'
                policy_number TEXT,
                provider_name TEXT,
                coverage_amount REAL,
                deductible REAL,
                effective_date DATE,
                expiry_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (driver_id) REFERENCES drivers(id)
            )
        ''')
        
        # Document audit trail
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                action TEXT, -- 'uploaded', 'viewed', 'downloaded', 'edited', 'deleted', 'verified'
                performed_by TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        ''')
        
        # Document links (for linking multiple documents)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_document_id INTEGER,
                linked_document_id INTEGER,
                link_type TEXT, -- 'related', 'supersedes', 'attachment', 'revision'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_document_id) REFERENCES documents(id),
                FOREIGN KEY (linked_document_id) REFERENCES documents(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def ensure_storage_folders(self):
        """Create folder structure for document storage"""
        folders = [
            'documents',
            'documents/bol',
            'documents/pod',
            'documents/rate_confirmations',
            'documents/photos',
            'documents/w9',
            'documents/insurance',
            'documents/cdl',
            'documents/medical',
            'documents/inspections',
            'documents/incidents',
            'documents/contracts',
            'documents/misc'
        ]
        
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
    
    def upload_document(self, file, document_type, category, **kwargs):
        """Upload any type of document with metadata"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_extension = file.name.split('.')[-1]
            safe_name = "".join(c for c in file.name.split('.')[0] if c.isalnum() or c in (' ', '-', '_'))
            unique_filename = f"{safe_name}_{timestamp}.{file_extension}"
            
            # Determine storage folder
            folder_map = {
                'BOL': 'bol',
                'POD': 'pod',
                'Rate Confirmation': 'rate_confirmations',
                'Photo': 'photos',
                'W9': 'w9',
                'Insurance': 'insurance',
                'CDL': 'cdl',
                'Medical Certificate': 'medical',
                'Inspection': 'inspections',
                'Incident': 'incidents',
                'Contract': 'contracts'
            }
            
            folder = folder_map.get(document_type, 'misc')
            file_path = f"documents/{folder}/{unique_filename}"
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file.getbuffer())
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Determine MIME type
            mime_map = {
                'pdf': 'application/pdf',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'doc': 'application/msword',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'xls': 'application/vnd.ms-excel',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            mime_type = mime_map.get(file_extension.lower(), 'application/octet-stream')
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO documents (
                    document_type, document_category, file_name, file_path, 
                    file_size, mime_type, driver_id, driver_name, move_id, 
                    trailer_number, customer_name, expiry_date, reference_number,
                    uploaded_by, notes, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_type, category, unique_filename, file_path,
                file_size, mime_type, kwargs.get('driver_id'), kwargs.get('driver_name'),
                kwargs.get('move_id'), kwargs.get('trailer_number'), kwargs.get('customer_name'),
                kwargs.get('expiry_date'), kwargs.get('reference_number'),
                kwargs.get('uploaded_by', 'System'), kwargs.get('notes'), kwargs.get('tags')
            ))
            
            document_id = cursor.lastrowid
            
            # Log audit trail
            cursor.execute('''
                INSERT INTO document_audit (document_id, action, performed_by, details)
                VALUES (?, 'uploaded', ?, ?)
            ''', (document_id, kwargs.get('uploaded_by', 'System'), f"Uploaded {document_type}"))
            
            conn.commit()
            conn.close()
            
            return True, document_id, file_path
            
        except Exception as e:
            return False, None, str(e)
    
    def link_document_to_move(self, document_id, move_id):
        """Link a document to a specific move"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE documents SET move_id = ? WHERE id = ?
        ''', (move_id, document_id))
        
        conn.commit()
        conn.close()
    
    def link_document_to_driver(self, document_id, driver_id, driver_name):
        """Link a document to a specific driver"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE documents SET driver_id = ?, driver_name = ? WHERE id = ?
        ''', (driver_id, driver_name, document_id))
        
        conn.commit()
        conn.close()
    
    def get_move_documents(self, move_id):
        """Get all documents for a specific move"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM documents 
            WHERE move_id = ? 
            ORDER BY upload_date DESC
        '''
        df = pd.read_sql_query(query, conn, params=(move_id,))
        conn.close()
        return df
    
    def get_driver_documents(self, driver_name):
        """Get all documents for a specific driver"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM documents 
            WHERE driver_name = ? 
            ORDER BY upload_date DESC
        '''
        df = pd.read_sql_query(query, conn, params=(driver_name,))
        conn.close()
        return df
    
    def get_expiring_documents(self, days_ahead=30):
        """Get documents expiring within specified days"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM documents 
            WHERE expiry_date IS NOT NULL 
            AND expiry_date <= date('now', '+' || ? || ' days')
            AND status = 'active'
            ORDER BY expiry_date
        '''
        df = pd.read_sql_query(query, conn, params=(days_ahead,))
        conn.close()
        return df
    
    def verify_document(self, document_id, verified_by):
        """Mark a document as verified"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE documents 
            SET verified = 1, verified_by = ?, verified_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (verified_by, document_id))
        
        # Log audit
        cursor.execute('''
            INSERT INTO document_audit (document_id, action, performed_by, details)
            VALUES (?, 'verified', ?, 'Document verified')
        ''', (document_id, verified_by))
        
        conn.commit()
        conn.close()
    
    def download_document(self, document_id, user):
        """Get document for download and log access"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get document info
        cursor.execute('SELECT file_path, file_name FROM documents WHERE id = ?', (document_id,))
        result = cursor.fetchone()
        
        if result:
            file_path, file_name = result
            
            # Log audit
            cursor.execute('''
                INSERT INTO document_audit (document_id, action, performed_by, details)
                VALUES (?, 'downloaded', ?, ?)
            ''', (document_id, user, f"Downloaded {file_name}"))
            
            conn.commit()
            conn.close()
            
            # Read file
            with open(file_path, 'rb') as f:
                return f.read(), file_name
        
        conn.close()
        return None, None


def show_document_management_interface():
    """Main interface for document management"""
    st.header("📁 Document Management System")
    
    doc_system = DocumentManagementSystem()
    
    tabs = st.tabs([
        "📤 Upload Documents",
        "📋 Move Documents",
        "👤 Driver Documents",
        "⚠️ Expiring Documents",
        "🔍 Search Documents",
        "📊 Document Analytics"
    ])
    
    with tabs[0]:
        st.subheader("Upload New Document")
        
        col1, col2 = st.columns(2)
        
        with col1:
            doc_type = st.selectbox("Document Type", [
                "BOL", "POD", "Rate Confirmation", "Photo",
                "W9", "Insurance", "CDL", "Medical Certificate",
                "Inspection Report", "Incident Report", "Contract", "Other"
            ])
            
            category = st.selectbox("Category", [
                "Operations", "Compliance", "Financial", "Safety", "Administrative"
            ])
            
            uploaded_file = st.file_uploader(
                f"Upload {doc_type}",
                type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx']
            )
        
        with col2:
            # Relationship fields
            st.write("**Link Document To:**")
            
            link_type = st.radio("Link Type", ["Move", "Driver", "Trailer", "Customer", "None"])
            
            if link_type == "Move":
                move_id = st.text_input("Move ID")
            elif link_type == "Driver":
                driver_name = st.text_input("Driver Name")
                driver_id = st.number_input("Driver ID", min_value=0)
            elif link_type == "Trailer":
                trailer_number = st.text_input("Trailer Number")
            elif link_type == "Customer":
                customer_name = st.text_input("Customer Name")
            
            # Additional metadata
            if doc_type in ["Insurance", "CDL", "Medical Certificate", "W9"]:
                expiry_date = st.date_input("Expiry Date")
            
            reference_number = st.text_input("Reference Number (Optional)")
            notes = st.text_area("Notes")
            tags = st.text_input("Tags (comma-separated)")
        
        if st.button("📤 Upload Document", type="primary", use_container_width=True):
            if uploaded_file:
                # Prepare kwargs
                kwargs = {
                    'uploaded_by': st.session_state.get('user', 'System'),
                    'notes': notes,
                    'tags': tags,
                    'reference_number': reference_number
                }
                
                if link_type == "Move" and 'move_id' in locals():
                    kwargs['move_id'] = move_id
                elif link_type == "Driver" and 'driver_name' in locals():
                    kwargs['driver_name'] = driver_name
                    kwargs['driver_id'] = driver_id if 'driver_id' in locals() else None
                elif link_type == "Trailer" and 'trailer_number' in locals():
                    kwargs['trailer_number'] = trailer_number
                elif link_type == "Customer" and 'customer_name' in locals():
                    kwargs['customer_name'] = customer_name
                
                if 'expiry_date' in locals():
                    kwargs['expiry_date'] = expiry_date
                
                # Upload document
                success, doc_id, result = doc_system.upload_document(
                    uploaded_file, doc_type, category, **kwargs
                )
                
                if success:
                    st.success(f"✅ Document uploaded successfully! ID: {doc_id}")
                    st.balloons()
                else:
                    st.error(f"Upload failed: {result}")
            else:
                st.error("Please select a file to upload")
    
    with tabs[1]:
        st.subheader("Move Documents")
        
        move_search = st.text_input("Enter Move ID")
        
        if move_search:
            docs = doc_system.get_move_documents(move_search)
            
            if not docs.empty:
                st.write(f"**Found {len(docs)} documents for Move {move_search}**")
                
                for _, doc in docs.iterrows():
                    with st.expander(f"📄 {doc['document_type']} - {doc['file_name']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Type:** {doc['document_type']}")
                            st.write(f"**Uploaded:** {doc['upload_date']}")
                        
                        with col2:
                            st.write(f"**Size:** {doc['file_size']} bytes")
                            if doc['verified']:
                                st.success(f"✅ Verified by {doc['verified_by']}")
                            else:
                                if st.button(f"Verify", key=f"verify_{doc['id']}"):
                                    doc_system.verify_document(doc['id'], st.session_state.get('user', 'System'))
                                    st.success("Document verified!")
                                    st.rerun()
                        
                        with col3:
                            if st.button(f"📥 Download", key=f"download_{doc['id']}"):
                                file_data, file_name = doc_system.download_document(
                                    doc['id'], st.session_state.get('user', 'System')
                                )
                                if file_data:
                                    st.download_button(
                                        "Download File",
                                        file_data,
                                        file_name,
                                        key=f"dl_btn_{doc['id']}"
                                    )
            else:
                st.info(f"No documents found for Move {move_search}")
    
    with tabs[2]:
        st.subheader("Driver Documents")
        
        # Get list of drivers
        conn = sqlite3.connect(doc_system.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT driver_name FROM drivers WHERE driver_name IS NOT NULL ORDER BY driver_name")
        drivers = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if drivers:
            selected_driver = st.selectbox("Select Driver", [""] + drivers)
            
            if selected_driver:
                docs = doc_system.get_driver_documents(selected_driver)
                
                if not docs.empty:
                    # Group by document type
                    doc_types = docs['document_type'].unique()
                    
                    for doc_type in doc_types:
                        st.write(f"**{doc_type}**")
                        type_docs = docs[docs['document_type'] == doc_type]
                        
                        for _, doc in type_docs.iterrows():
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.write(f"📄 {doc['file_name']}")
                            
                            with col2:
                                if doc['expiry_date']:
                                    st.write(f"Expires: {doc['expiry_date']}")
                            
                            with col3:
                                if doc['verified']:
                                    st.success("✅ Verified")
                                else:
                                    st.warning("⏳ Pending")
                            
                            with col4:
                                st.write(f"Uploaded: {doc['upload_date']}")
                else:
                    st.info(f"No documents found for {selected_driver}")
    
    with tabs[3]:
        st.subheader("Expiring Documents")
        
        days = st.slider("Days ahead to check", 7, 90, 30)
        
        expiring = doc_system.get_expiring_documents(days)
        
        if not expiring.empty:
            st.warning(f"⚠️ {len(expiring)} documents expiring within {days} days")
            
            # Group by driver
            if 'driver_name' in expiring.columns:
                for driver in expiring['driver_name'].unique():
                    if driver:
                        driver_docs = expiring[expiring['driver_name'] == driver]
                        
                        with st.expander(f"👤 {driver} - {len(driver_docs)} documents"):
                            for _, doc in driver_docs.iterrows():
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.write(f"**{doc['document_type']}**")
                                
                                with col2:
                                    st.write(f"Expires: {doc['expiry_date']}")
                                
                                with col3:
                                    days_left = (pd.to_datetime(doc['expiry_date']) - pd.Timestamp.now()).days
                                    if days_left <= 7:
                                        st.error(f"🚨 {days_left} days")
                                    elif days_left <= 14:
                                        st.warning(f"⚠️ {days_left} days")
                                    else:
                                        st.info(f"📅 {days_left} days")
        else:
            st.success(f"✅ No documents expiring within {days} days")
    
    with tabs[4]:
        st.subheader("Search Documents")
        
        search_query = st.text_input("Search documents (by type, name, reference, etc.)")
        
        if search_query:
            conn = sqlite3.connect(doc_system.db_path)
            query = '''
                SELECT * FROM documents 
                WHERE document_type LIKE ? 
                OR file_name LIKE ? 
                OR reference_number LIKE ?
                OR notes LIKE ?
                OR tags LIKE ?
                ORDER BY upload_date DESC
                LIMIT 50
            '''
            search_param = f"%{search_query}%"
            df = pd.read_sql_query(query, conn, params=(search_param, search_param, search_param, search_param, search_param))
            conn.close()
            
            if not df.empty:
                st.write(f"**Found {len(df)} documents**")
                st.dataframe(df[['document_type', 'file_name', 'driver_name', 'move_id', 'upload_date']], use_container_width=True)
            else:
                st.info("No documents found matching your search")
    
    with tabs[5]:
        st.subheader("Document Analytics")
        
        conn = sqlite3.connect(doc_system.db_path)
        
        # Document counts by type
        type_counts = pd.read_sql_query('''
            SELECT document_type, COUNT(*) as count 
            FROM documents 
            GROUP BY document_type 
            ORDER BY count DESC
        ''', conn)
        
        if not type_counts.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Documents by Type**")
                st.dataframe(type_counts, use_container_width=True, hide_index=True)
            
            with col2:
                st.write("**Document Statistics**")
                
                total_docs = pd.read_sql_query('SELECT COUNT(*) as total FROM documents', conn)['total'][0]
                verified_docs = pd.read_sql_query('SELECT COUNT(*) as verified FROM documents WHERE verified = 1', conn)['verified'][0]
                
                st.metric("Total Documents", total_docs)
                st.metric("Verified Documents", verified_docs)
                st.metric("Verification Rate", f"{(verified_docs/total_docs*100 if total_docs > 0 else 0):.1f}%")
        
        conn.close()


# Export functions
__all__ = ['DocumentManagementSystem', 'show_document_management_interface']