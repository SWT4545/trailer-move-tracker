"""
Enhanced Document Management System
Handles POD (Fleet receipt for returned trailer), BOL, and Rate Con
Properly separated by role responsibilities
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import database as db
import json
import base64
import sqlite3

class DocumentManager:
    """Manages all document uploads and tracking"""
    
    def __init__(self):
        self.ensure_document_tables()
    
    def ensure_document_tables(self):
        """Ensure document tracking tables exist"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create documents table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS move_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    move_id TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    file_name TEXT,
                    file_data BLOB,
                    file_url TEXT,
                    uploaded_by TEXT,
                    uploaded_by_role TEXT,
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified BOOLEAN DEFAULT 0,
                    verified_by TEXT,
                    verified_at TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (move_id) REFERENCES moves(move_id)
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_move_documents_move_id 
                ON move_documents(move_id, document_type)
            """)
            
            # Add document tracking columns to moves table if not exist
            cursor.execute("PRAGMA table_info(moves)")
            columns = [col[1] for col in cursor.fetchall()]
            
            doc_columns = [
                ('pod_fleet_receipt_uploaded', 'BOOLEAN DEFAULT 0'),
                ('pod_fleet_receipt_time', 'TIMESTAMP'),
                ('bol_uploaded', 'BOOLEAN DEFAULT 0'),
                ('bol_upload_time', 'TIMESTAMP'),
                ('rate_con_uploaded', 'BOOLEAN DEFAULT 0'),
                ('rate_con_upload_time', 'TIMESTAMP'),
                ('pickup_photo_uploaded', 'BOOLEAN DEFAULT 0'),
                ('delivery_photo_uploaded', 'BOOLEAN DEFAULT 0'),
                ('documents_complete', 'BOOLEAN DEFAULT 0')
            ]
            
            for col_name, col_type in doc_columns:
                if col_name not in columns:
                    cursor.execute(f"ALTER TABLE moves ADD COLUMN {col_name} {col_type}")
            
            conn.commit()
        except Exception as e:
            print(f"Error creating document tables: {e}")
        finally:
            conn.close()
    
    def upload_document(self, move_id, doc_type, file_data, file_name, uploaded_by, user_role):
        """Upload a document for a move"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Insert document record
            cursor.execute("""
                INSERT INTO move_documents (
                    move_id, document_type, file_name, file_data,
                    uploaded_by, uploaded_by_role
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (move_id, doc_type, file_name, file_data, uploaded_by, user_role))
            
            # Update move record based on document type
            if doc_type == 'pod_fleet_receipt':
                cursor.execute("""
                    UPDATE moves 
                    SET pod_fleet_receipt_uploaded = 1,
                        pod_fleet_receipt_time = ?
                    WHERE move_id = ?
                """, (datetime.now(), move_id))
                
            elif doc_type == 'pickup_photo':
                cursor.execute("""
                    UPDATE moves 
                    SET pickup_photo_uploaded = 1
                    WHERE move_id = ?
                """, (move_id,))
                
            elif doc_type == 'delivery_photo':
                cursor.execute("""
                    UPDATE moves 
                    SET delivery_photo_uploaded = 1
                    WHERE move_id = ?
                """, (move_id,))
                
            elif doc_type == 'bol':
                cursor.execute("""
                    UPDATE moves 
                    SET bol_uploaded = 1,
                        bol_upload_time = ?
                    WHERE move_id = ?
                """, (datetime.now(), move_id))
                
            elif doc_type == 'rate_con':
                cursor.execute("""
                    UPDATE moves 
                    SET rate_con_uploaded = 1,
                        rate_con_upload_time = ?
                    WHERE move_id = ?
                """, (datetime.now(), move_id))
            
            # Check if all required documents are complete
            self.check_document_completion(cursor, move_id)
            
            conn.commit()
            return True, "Document uploaded successfully"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def check_document_completion(self, cursor, move_id):
        """Check if all required documents are uploaded"""
        cursor.execute("""
            SELECT 
                pod_fleet_receipt_uploaded,
                pickup_photo_uploaded,
                delivery_photo_uploaded,
                bol_uploaded,
                rate_con_uploaded
            FROM moves
            WHERE move_id = ?
        """, (move_id,))
        
        result = cursor.fetchone()
        if result:
            pod, pickup, delivery, bol, rate_con = result
            
            # Driver required: POD, pickup photo, delivery photo
            driver_complete = all([pod, pickup, delivery])
            
            # Admin/Coordinator required: BOL and Rate Con
            admin_complete = all([bol, rate_con])
            
            # Mark as complete if all documents are present
            if driver_complete and admin_complete:
                cursor.execute("""
                    UPDATE moves 
                    SET documents_complete = 1
                    WHERE move_id = ?
                """, (move_id,))
    
    def get_move_documents(self, move_id):
        """Get all documents for a move"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                document_type,
                file_name,
                uploaded_by,
                uploaded_by_role,
                upload_timestamp,
                verified
            FROM move_documents
            WHERE move_id = ?
            ORDER BY upload_timestamp DESC
        """, (move_id,))
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                'type': row[0],
                'file_name': row[1],
                'uploaded_by': row[2],
                'role': row[3],
                'timestamp': row[4],
                'verified': row[5]
            })
        
        conn.close()
        return documents


def show_driver_document_upload(driver_name, move_id):
    """Driver document upload interface - POD and photos only"""
    
    st.markdown("### 📸 Upload Move Documents")
    
    if not move_id:
        st.warning("No active move. Complete a pickup to upload documents.")
        return
    
    doc_manager = DocumentManager()
    
    # Get move details
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            new_trailer, old_trailer, status,
            pod_fleet_receipt_uploaded, pickup_photo_uploaded, delivery_photo_uploaded
        FROM moves
        WHERE move_id = ?
    """, (move_id,))
    
    move = cursor.fetchone()
    conn.close()
    
    if not move:
        st.error("Move not found")
        return
    
    new_trailer, old_trailer, status, pod_uploaded, pickup_uploaded, delivery_uploaded = move
    
    st.info(f"📦 Move: {new_trailer} ↔ {old_trailer}")
    
    # Document upload tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📸 Pickup Photo",
        "📸 Delivery Photo", 
        "📄 POD (Fleet Receipt)",
        "📊 Status"
    ])
    
    with tab1:
        st.markdown("#### Pickup Photo")
        st.info("Take a photo of the NEW trailer after pickup")
        
        if pickup_uploaded:
            st.success("✅ Pickup photo already uploaded")
        else:
            uploaded_file = st.file_uploader(
                "Select or take photo",
                type=['jpg', 'jpeg', 'png'],
                key="pickup_photo",
                help="Use your iPhone camera for best results"
            )
            
            if uploaded_file:
                if st.button("📤 Upload Pickup Photo", type="primary", use_container_width=True):
                    file_data = uploaded_file.read()
                    success, msg = doc_manager.upload_document(
                        move_id, 'pickup_photo', file_data,
                        uploaded_file.name, driver_name, 'Driver'
                    )
                    if success:
                        st.success("Pickup photo uploaded!")
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {msg}")
    
    with tab2:
        st.markdown("#### Delivery Photo")
        st.info("Take a photo of the OLD trailer at delivery location")
        
        if delivery_uploaded:
            st.success("✅ Delivery photo already uploaded")
        elif status not in ['pickup_complete', 'completed']:
            st.warning("Complete pickup first before uploading delivery photo")
        else:
            uploaded_file = st.file_uploader(
                "Select or take photo",
                type=['jpg', 'jpeg', 'png'],
                key="delivery_photo",
                help="Use your iPhone camera for best results"
            )
            
            if uploaded_file:
                if st.button("📤 Upload Delivery Photo", type="primary", use_container_width=True):
                    file_data = uploaded_file.read()
                    success, msg = doc_manager.upload_document(
                        move_id, 'delivery_photo', file_data,
                        uploaded_file.name, driver_name, 'Driver'
                    )
                    if success:
                        st.success("Delivery photo uploaded!")
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {msg}")
    
    with tab3:
        st.markdown("#### POD - Fleet Receipt")
        st.info("Upload the receipt from Fleet when returning the OLD trailer")
        
        if pod_uploaded:
            st.success("✅ POD (Fleet receipt) already uploaded")
        elif status != 'completed':
            st.warning("Complete delivery first before uploading POD")
        else:
            uploaded_file = st.file_uploader(
                "Select POD/Fleet Receipt",
                type=['jpg', 'jpeg', 'png', 'pdf'],
                key="pod_receipt",
                help="This is the receipt from Fleet Memphis confirming OLD trailer return"
            )
            
            if uploaded_file:
                if st.button("📤 Upload POD Receipt", type="primary", use_container_width=True):
                    file_data = uploaded_file.read()
                    success, msg = doc_manager.upload_document(
                        move_id, 'pod_fleet_receipt', file_data,
                        uploaded_file.name, driver_name, 'Driver'
                    )
                    if success:
                        st.success("POD receipt uploaded!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {msg}")
    
    with tab4:
        st.markdown("#### Document Status")
        
        # Status indicators
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Driver Documents:**")
            st.write(f"{'✅' if pickup_uploaded else '⏳'} Pickup Photo")
            st.write(f"{'✅' if delivery_uploaded else '⏳'} Delivery Photo")
            st.write(f"{'✅' if pod_uploaded else '⏳'} POD (Fleet Receipt)")
        
        with col2:
            st.markdown("**Office will add:**")
            st.write("⏳ Bill of Lading (BOL)")
            st.write("⏳ Rate Confirmation")
            st.write("*Added by coordinator/admin*")
        
        # Show all uploaded documents
        documents = doc_manager.get_move_documents(move_id)
        if documents:
            st.markdown("---")
            st.markdown("**Upload History:**")
            for doc in documents:
                doc_emoji = {
                    'pickup_photo': '📸',
                    'delivery_photo': '📸',
                    'pod_fleet_receipt': '📄',
                    'bol': '📋',
                    'rate_con': '💰'
                }.get(doc['type'], '📄')
                
                st.write(f"{doc_emoji} {doc['type'].replace('_', ' ').title()}")
                st.caption(f"By: {doc['uploaded_by']} ({doc['role']}) - {doc['timestamp']}")


def show_admin_document_management(move_id):
    """Admin/Coordinator interface for BOL and Rate Con"""
    
    st.markdown("### 📋 Document Management")
    
    doc_manager = DocumentManager()
    
    # Get move details
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            new_trailer, old_trailer, driver_name,
            pod_fleet_receipt_uploaded, pickup_photo_uploaded, 
            delivery_photo_uploaded, bol_uploaded, rate_con_uploaded,
            documents_complete
        FROM moves
        WHERE move_id = ?
    """, (move_id,))
    
    move = cursor.fetchone()
    conn.close()
    
    if not move:
        st.error("Move not found")
        return
    
    (new_trailer, old_trailer, driver_name, pod_uploaded, 
     pickup_uploaded, delivery_uploaded, bol_uploaded, 
     rate_con_uploaded, docs_complete) = move
    
    # Status overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Move ID", move_id)
        st.caption(f"{new_trailer} ↔ {old_trailer}")
    
    with col2:
        st.metric("Driver", driver_name)
    
    with col3:
        if docs_complete:
            st.success("✅ Complete")
        else:
            st.warning("⏳ Pending Docs")
    
    st.markdown("---")
    
    # Document status and upload
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Driver Documents")
        st.write(f"{'✅' if pickup_uploaded else '❌'} Pickup Photo")
        st.write(f"{'✅' if delivery_uploaded else '❌'} Delivery Photo")
        st.write(f"{'✅' if pod_uploaded else '❌'} POD (Fleet Receipt)")
        
        if not all([pickup_uploaded, delivery_uploaded, pod_uploaded]):
            st.warning("Driver still needs to upload documents")
    
    with col2:
        st.markdown("#### Office Documents")
        
        # BOL Upload
        if bol_uploaded:
            st.success("✅ BOL uploaded")
        else:
            with st.expander("📋 Upload Bill of Lading"):
                bol_file = st.file_uploader(
                    "Select BOL",
                    type=['pdf', 'jpg', 'jpeg', 'png'],
                    key=f"bol_{move_id}"
                )
                
                if bol_file:
                    if st.button("Upload BOL", key=f"upload_bol_{move_id}"):
                        file_data = bol_file.read()
                        success, msg = doc_manager.upload_document(
                            move_id, 'bol', file_data,
                            bol_file.name, 
                            st.session_state.get('username', 'Admin'),
                            st.session_state.get('user_role', 'Admin')
                        )
                        if success:
                            st.success("BOL uploaded!")
                            st.rerun()
        
        # Rate Con Upload
        if rate_con_uploaded:
            st.success("✅ Rate Confirmation uploaded")
        else:
            with st.expander("💰 Upload Rate Confirmation"):
                rate_con_file = st.file_uploader(
                    "Select Rate Con",
                    type=['pdf', 'jpg', 'jpeg', 'png'],
                    key=f"rate_con_{move_id}"
                )
                
                if rate_con_file:
                    if st.button("Upload Rate Con", key=f"upload_rate_con_{move_id}"):
                        file_data = rate_con_file.read()
                        success, msg = doc_manager.upload_document(
                            move_id, 'rate_con', file_data,
                            rate_con_file.name,
                            st.session_state.get('username', 'Admin'),
                            st.session_state.get('user_role', 'Admin')
                        )
                        if success:
                            st.success("Rate Confirmation uploaded!")
                            st.rerun()
    
    # Document checklist
    st.markdown("---")
    st.markdown("#### Document Checklist")
    
    checklist = {
        "Driver uploads pickup photo": pickup_uploaded,
        "Driver completes delivery": delivery_uploaded,
        "Driver uploads POD (Fleet receipt)": pod_uploaded,
        "Office uploads BOL": bol_uploaded,
        "Office uploads Rate Confirmation": rate_con_uploaded
    }
    
    for item, completed in checklist.items():
        st.checkbox(item, value=completed, disabled=True, key=f"check_{item}_{move_id}")
    
    if all(checklist.values()):
        st.success("🎉 All documents complete! Ready for payment processing.")
    else:
        missing = [item for item, done in checklist.items() if not done]
        st.info(f"Waiting for: {', '.join(missing)}")


def show_document_dashboard():
    """Dashboard showing all moves and their document status"""
    
    st.markdown("### 📊 Document Status Dashboard")
    
    # Get all recent moves
    conn = db.get_connection()
    
    query = """
        SELECT 
            move_id,
            driver_name,
            new_trailer || ' ↔ ' || old_trailer as trailers,
            move_date,
            status,
            pod_fleet_receipt_uploaded,
            pickup_photo_uploaded,
            delivery_photo_uploaded,
            bol_uploaded,
            rate_con_uploaded,
            documents_complete
        FROM moves
        WHERE move_date >= date('now', '-30 days')
        ORDER BY move_date DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        # Add status columns
        df['Driver Docs'] = df.apply(
            lambda x: '✅' if all([x['pod_fleet_receipt_uploaded'], 
                                  x['pickup_photo_uploaded'],
                                  x['delivery_photo_uploaded']]) else '⏳',
            axis=1
        )
        
        df['Office Docs'] = df.apply(
            lambda x: '✅' if all([x['bol_uploaded'], 
                                  x['rate_con_uploaded']]) else '⏳',
            axis=1
        )
        
        df['Complete'] = df['documents_complete'].apply(lambda x: '✅' if x else '❌')
        
        # Display columns
        display_cols = ['move_id', 'driver_name', 'trailers', 'move_date', 
                       'status', 'Driver Docs', 'Office Docs', 'Complete']
        
        st.dataframe(
            df[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "move_id": "Move ID",
                "driver_name": "Driver",
                "trailers": "Route",
                "move_date": "Date",
                "status": "Status",
                "Driver Docs": st.column_config.TextColumn("Driver Docs", help="Pickup/Delivery photos + POD"),
                "Office Docs": st.column_config.TextColumn("Office Docs", help="BOL + Rate Con"),
                "Complete": "All Docs"
            }
        )
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = len(df)
            st.metric("Total Moves", total)
        
        with col2:
            complete = df['documents_complete'].sum()
            st.metric("Complete", complete)
        
        with col3:
            driver_pending = len(df[df['Driver Docs'] == '⏳'])
            st.metric("Driver Pending", driver_pending)
        
        with col4:
            office_pending = len(df[df['Office Docs'] == '⏳'])
            st.metric("Office Pending", office_pending)
    else:
        st.info("No moves in the last 30 days")


# Export functions for use in main app
__all__ = [
    'DocumentManager',
    'show_driver_document_upload',
    'show_admin_document_management',
    'show_document_dashboard'
]