"""
Factoring Document Management System
Handles Rate Confirmations, BOLs, and PODs for factoring submission
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import base64
import json

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def create_document_tables():
    """Create tables for document management"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Main document storage table
    cursor.execute('''CREATE TABLE IF NOT EXISTS factoring_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        move_id TEXT NOT NULL,
        document_type TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_data BLOB,
        file_size INTEGER,
        uploaded_by TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verified BOOLEAN DEFAULT 0,
        verified_by TEXT,
        verified_at TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (move_id) REFERENCES moves(move_id)
    )''')
    
    # Document requirements table
    cursor.execute('''CREATE TABLE IF NOT EXISTS document_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        move_id TEXT NOT NULL,
        rate_confirmation BOOLEAN DEFAULT 0,
        rate_conf_file_id INTEGER,
        bol BOOLEAN DEFAULT 0,
        bol_file_id INTEGER,
        pod BOOLEAN DEFAULT 0,
        pod_file_id INTEGER,
        all_docs_complete BOOLEAN DEFAULT 0,
        ready_for_factoring BOOLEAN DEFAULT 0,
        last_updated TIMESTAMP,
        FOREIGN KEY (move_id) REFERENCES moves(move_id)
    )''')
    
    conn.commit()
    conn.close()

def show_document_management():
    """Main document management interface"""
    st.markdown("## 📄 Factoring Document Management")
    st.info("Upload and manage Rate Confirmations, BOLs, and PODs for factoring submission")
    
    # Ensure tables exist
    create_document_tables()
    
    tabs = st.tabs([
        "📤 Upload Documents",
        "📋 Document Status",
        "✅ Verify Documents",
        "📦 Ready for Factoring",
        "🗂️ Document Archive"
    ])
    
    with tabs[0]:  # Upload Documents
        show_document_upload()
    
    with tabs[1]:  # Document Status
        show_document_status()
    
    with tabs[2]:  # Verify Documents
        show_document_verification()
    
    with tabs[3]:  # Ready for Factoring
        show_factoring_ready()
    
    with tabs[4]:  # Document Archive
        show_document_archive()

def show_document_upload():
    """Document upload interface"""
    st.markdown("### Upload Documents for Moves")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get moves that need documents
    cursor.execute('''SELECT m.move_id, m.driver_name, m.new_trailer, m.old_trailer, 
                            m.delivery_location, m.status, m.completed_date
                     FROM moves m
                     LEFT JOIN document_requirements dr ON m.move_id = dr.move_id
                     WHERE m.status IN ('completed', 'in_progress')
                     AND (dr.all_docs_complete IS NULL OR dr.all_docs_complete = 0)
                     ORDER BY m.completed_date DESC''')
    moves_needing_docs = cursor.fetchall()
    
    if moves_needing_docs:
        # Move selector
        move_options = [f"{m[0]} - {m[1]} - {m[4]}" for m in moves_needing_docs]
        selected_idx = st.selectbox(
            "Select Move",
            range(len(move_options)),
            format_func=lambda x: move_options[x]
        )
        
        selected_move = moves_needing_docs[selected_idx]
        move_id = selected_move[0]
        
        # Show move details
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            **Move Details:**
            - Move ID: {move_id}
            - Driver: {selected_move[1]}
            - Trailers: {selected_move[2]} ↔ {selected_move[3]}
            - Destination: {selected_move[4]}
            - Status: {selected_move[5]}
            """)
        
        # Check existing documents
        cursor.execute('''SELECT document_type, file_name, uploaded_at, verified
                         FROM factoring_documents
                         WHERE move_id = ?
                         ORDER BY uploaded_at DESC''', (move_id,))
        existing_docs = cursor.fetchall()
        
        with col2:
            st.markdown("**Existing Documents:**")
            if existing_docs:
                for doc in existing_docs:
                    status = "✅" if doc[3] else "⏳"
                    st.write(f"{status} {doc[0]}: {doc[1]}")
            else:
                st.write("No documents uploaded yet")
        
        st.markdown("---")
        
        # Document upload section
        st.markdown("### Upload New Documents")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Rate Confirmation")
            rate_conf = st.file_uploader(
                "Upload Rate Confirmation",
                type=['pdf', 'jpg', 'png', 'jpeg'],
                key=f"rc_{move_id}"
            )
            
            if rate_conf:
                if st.button("Save Rate Confirmation", key=f"save_rc_{move_id}"):
                    save_document(move_id, "Rate Confirmation", rate_conf)
                    st.success("✅ Rate Confirmation uploaded!")
                    st.rerun()
        
        with col2:
            st.markdown("#### Bill of Lading (BOL)")
            bol = st.file_uploader(
                "Upload BOL",
                type=['pdf', 'jpg', 'png', 'jpeg'],
                key=f"bol_{move_id}"
            )
            
            if bol:
                if st.button("Save BOL", key=f"save_bol_{move_id}"):
                    save_document(move_id, "BOL", bol)
                    st.success("✅ BOL uploaded!")
                    st.rerun()
        
        with col3:
            st.markdown("#### Proof of Delivery (POD)")
            pod = st.file_uploader(
                "Upload POD",
                type=['pdf', 'jpg', 'png', 'jpeg'],
                key=f"pod_{move_id}"
            )
            
            if pod:
                if st.button("Save POD", key=f"save_pod_{move_id}"):
                    save_document(move_id, "POD", pod)
                    st.success("✅ POD uploaded!")
                    st.rerun()
        
        # Additional documents
        st.markdown("#### Additional Documents")
        additional = st.file_uploader(
            "Upload any additional documents",
            type=['pdf', 'jpg', 'png', 'jpeg'],
            accept_multiple_files=True,
            key=f"additional_{move_id}"
        )
        
        if additional:
            doc_type = st.text_input("Document type/description")
            if st.button("Save Additional Documents") and doc_type:
                for doc in additional:
                    save_document(move_id, doc_type, doc)
                st.success(f"✅ {len(additional)} additional documents uploaded!")
                st.rerun()
    else:
        st.info("All moves have complete documentation or no moves available")
    
    conn.close()

def save_document(move_id, doc_type, file_obj):
    """Save uploaded document to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Read file data
    file_data = file_obj.read()
    file_name = file_obj.name
    file_size = len(file_data)
    
    # Save to database
    cursor.execute('''INSERT INTO factoring_documents 
                     (move_id, document_type, file_name, file_data, file_size, uploaded_by)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (move_id, doc_type, file_name, file_data, file_size, 
                   st.session_state.get('user', 'System')))
    
    # Update document requirements
    cursor.execute('''INSERT OR REPLACE INTO document_requirements (move_id)
                     VALUES (?)''', (move_id,))
    
    if doc_type == "Rate Confirmation":
        cursor.execute('''UPDATE document_requirements 
                         SET rate_confirmation = 1, rate_conf_file_id = last_insert_rowid()
                         WHERE move_id = ?''', (move_id,))
    elif doc_type == "BOL":
        cursor.execute('''UPDATE document_requirements 
                         SET bol = 1, bol_file_id = last_insert_rowid()
                         WHERE move_id = ?''', (move_id,))
    elif doc_type == "POD":
        cursor.execute('''UPDATE document_requirements 
                         SET pod = 1, pod_file_id = last_insert_rowid()
                         WHERE move_id = ?''', (move_id,))
    
    # Check if all docs complete
    cursor.execute('''UPDATE document_requirements 
                     SET all_docs_complete = (rate_confirmation AND bol AND pod),
                         last_updated = CURRENT_TIMESTAMP
                     WHERE move_id = ?''', (move_id,))
    
    conn.commit()
    conn.close()

def show_document_status():
    """Show document status for all moves"""
    st.markdown("### Document Status Overview")
    
    conn = get_connection()
    
    # Get document status for all moves
    query = '''SELECT m.move_id, m.driver_name, m.delivery_location, m.status,
                     COALESCE(dr.rate_confirmation, 0) as has_rc,
                     COALESCE(dr.bol, 0) as has_bol,
                     COALESCE(dr.pod, 0) as has_pod,
                     COALESCE(dr.all_docs_complete, 0) as complete,
                     m.completed_date
              FROM moves m
              LEFT JOIN document_requirements dr ON m.move_id = dr.move_id
              WHERE m.status IN ('completed', 'in_progress')
              ORDER BY m.completed_date DESC'''
    
    df = pd.read_sql_query(query, conn)
    
    if not df.empty:
        # Add status indicators
        df['Rate Conf'] = df['has_rc'].apply(lambda x: '✅' if x else '❌')
        df['BOL'] = df['has_bol'].apply(lambda x: '✅' if x else '❌')
        df['POD'] = df['has_pod'].apply(lambda x: '✅' if x else '❌')
        df['Ready'] = df['complete'].apply(lambda x: '✅ Ready' if x else '⏳ Pending')
        
        # Display columns
        display_df = df[['move_id', 'driver_name', 'delivery_location', 
                        'Rate Conf', 'BOL', 'POD', 'Ready']]
        display_df.columns = ['Move ID', 'Driver', 'Destination', 
                             'Rate Conf', 'BOL', 'POD', 'Status']
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Moves", len(df))
        with col2:
            complete_count = df['complete'].sum()
            st.metric("Complete", complete_count)
        with col3:
            pending_count = len(df) - complete_count
            st.metric("Pending Docs", pending_count)
        with col4:
            completion_rate = (complete_count / len(df) * 100) if len(df) > 0 else 0
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No moves to display")
    
    conn.close()

def show_document_verification():
    """Document verification interface for management"""
    st.markdown("### Verify Uploaded Documents")
    st.info("Review and verify documents before factoring submission")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get unverified documents
    cursor.execute('''SELECT fd.id, fd.move_id, fd.document_type, fd.file_name,
                            fd.uploaded_by, fd.uploaded_at, m.driver_name
                     FROM factoring_documents fd
                     JOIN moves m ON fd.move_id = m.move_id
                     WHERE fd.verified = 0
                     ORDER BY fd.uploaded_at DESC''')
    unverified = cursor.fetchall()
    
    if unverified:
        for doc in unverified:
            doc_id, move_id, doc_type, file_name, uploaded_by, uploaded_at, driver = doc
            
            with st.expander(f"📄 {move_id} - {doc_type}", expanded=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    **Document Details:**
                    - Move: {move_id}
                    - Driver: {driver}
                    - Type: {doc_type}
                    - File: {file_name}
                    - Uploaded by: {uploaded_by}
                    - Date: {uploaded_at}
                    """)
                
                with col2:
                    # View document button
                    if st.button(f"View Document", key=f"view_{doc_id}"):
                        cursor.execute('SELECT file_data FROM factoring_documents WHERE id = ?',
                                     (doc_id,))
                        file_data = cursor.fetchone()[0]
                        
                        # Create download link
                        b64 = base64.b64encode(file_data).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{file_name}">Download {file_name}</a>'
                        st.markdown(href, unsafe_allow_html=True)
                
                with col3:
                    if st.button(f"✅ Verify", key=f"verify_{doc_id}", type="primary"):
                        cursor.execute('''UPDATE factoring_documents 
                                       SET verified = 1, 
                                           verified_by = ?,
                                           verified_at = CURRENT_TIMESTAMP
                                       WHERE id = ?''',
                                     (st.session_state.get('user', 'System'), doc_id))
                        conn.commit()
                        st.success("Document verified!")
                        st.rerun()
                    
                    if st.button(f"❌ Reject", key=f"reject_{doc_id}"):
                        reason = st.text_input(f"Rejection reason", key=f"reason_{doc_id}")
                        if reason:
                            cursor.execute('''UPDATE factoring_documents 
                                           SET notes = ?
                                           WHERE id = ?''',
                                         (f"REJECTED: {reason}", doc_id))
                            conn.commit()
                            st.error("Document rejected")
                            st.rerun()
    else:
        st.success("All documents verified!")
    
    conn.close()

def show_factoring_ready():
    """Show moves ready for factoring submission"""
    st.markdown("### Moves Ready for Factoring")
    st.success("These moves have all required documents and are ready for submission")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get moves with complete, verified documents
    cursor.execute('''SELECT m.move_id, m.driver_name, m.total_miles, m.driver_pay,
                            m.delivery_location, m.completed_date,
                            COUNT(fd.id) as doc_count,
                            SUM(CASE WHEN fd.verified = 1 THEN 1 ELSE 0 END) as verified_count
                     FROM moves m
                     JOIN document_requirements dr ON m.move_id = dr.move_id
                     LEFT JOIN factoring_documents fd ON m.move_id = fd.move_id
                     WHERE dr.all_docs_complete = 1
                     AND m.payment_status != 'paid'
                     AND m.submitted_to_factoring IS NULL
                     GROUP BY m.move_id
                     HAVING verified_count >= 3''')  # At least RC, BOL, POD verified
    
    ready_moves = cursor.fetchall()
    
    if ready_moves:
        # Allow batch selection
        st.markdown("#### Select Moves for Factoring Submission")
        
        selected_moves = []
        total_amount = 0
        
        for move in ready_moves:
            move_id, driver, miles, pay, location, date, doc_count, verified = move
            
            col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
            
            with col1:
                if st.checkbox("", key=f"factor_{move_id}"):
                    selected_moves.append(move_id)
                    total_amount += pay
            
            with col2:
                st.write(f"{move_id} - {driver}")
            
            with col3:
                st.write(f"{location}")
            
            with col4:
                st.write(f"${pay:.2f}")
            
            with col5:
                st.write(f"📄 {verified}/{doc_count} docs")
        
        if selected_moves:
            st.markdown("---")
            st.markdown(f"### Batch Submission Summary")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Moves Selected", len(selected_moves))
            with col2:
                st.metric("Total Amount", f"${total_amount:.2f}")
            with col3:
                est_fee = total_amount * 0.03
                st.metric("Est. Factoring Fee (3%)", f"${est_fee:.2f}")
            
            # Submission form
            with st.form("factoring_submission"):
                col1, col2 = st.columns(2)
                
                with col1:
                    batch_number = st.text_input(
                        "Batch Number",
                        value=f"FCT-{datetime.now().strftime('%Y%m%d-%H%M')}"
                    )
                    
                    factoring_company = st.selectbox(
                        "Factoring Company",
                        ["Triumph Business Capital", "RTS Financial", "Other"]
                    )
                
                with col2:
                    submission_date = st.date_input(
                        "Submission Date",
                        value=datetime.now().date()
                    )
                    
                    notes = st.text_area("Notes")
                
                if st.form_submit_button("Submit to Factoring", type="primary"):
                    # Update moves as submitted
                    for move_id in selected_moves:
                        cursor.execute('''UPDATE moves 
                                       SET submitted_to_factoring = ?,
                                           factoring_batch = ?,
                                           factoring_company = ?
                                       WHERE move_id = ?''',
                                     (submission_date, batch_number, factoring_company, move_id))
                        
                        # Update document requirements
                        cursor.execute('''UPDATE document_requirements 
                                       SET ready_for_factoring = 1
                                       WHERE move_id = ?''', (move_id,))
                    
                    # Log the batch submission
                    cursor.execute('''INSERT INTO factoring_log 
                                   (batch_reference, submission_date, factoring_company,
                                    total_amount, moves_count, status, notes, created_by)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                 (batch_number, submission_date, factoring_company,
                                  total_amount, len(selected_moves), 'submitted', notes,
                                  st.session_state.get('user', 'System')))
                    
                    conn.commit()
                    st.success(f"""
                    ✅ Factoring Submission Complete!
                    - Batch: {batch_number}
                    - Moves: {len(selected_moves)}
                    - Amount: ${total_amount:.2f}
                    - Company: {factoring_company}
                    """)
                    st.rerun()
    else:
        st.info("No moves ready for factoring. Ensure all documents are uploaded and verified.")
    
    conn.close()

def show_document_archive():
    """Show all documents in the system"""
    st.markdown("### Document Archive")
    
    conn = get_connection()
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search_move = st.text_input("Search by Move ID")
    with col2:
        search_driver = st.text_input("Search by Driver")
    with col3:
        doc_type_filter = st.selectbox(
            "Document Type",
            ["All", "Rate Confirmation", "BOL", "POD", "Other"]
        )
    
    # Build query
    query = '''SELECT fd.id, fd.move_id, m.driver_name, fd.document_type, 
                     fd.file_name, fd.file_size, fd.uploaded_by, fd.uploaded_at,
                     fd.verified, fd.verified_by
              FROM factoring_documents fd
              JOIN moves m ON fd.move_id = m.move_id
              WHERE 1=1'''
    
    params = []
    
    if search_move:
        query += " AND fd.move_id LIKE ?"
        params.append(f"%{search_move}%")
    
    if search_driver:
        query += " AND m.driver_name LIKE ?"
        params.append(f"%{search_driver}%")
    
    if doc_type_filter != "All":
        query += " AND fd.document_type = ?"
        params.append(doc_type_filter)
    
    query += " ORDER BY fd.uploaded_at DESC"
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    documents = cursor.fetchall()
    
    if documents:
        # Display documents
        for doc in documents:
            doc_id, move_id, driver, doc_type, file_name, file_size, uploaded_by, uploaded_at, verified, verified_by = doc
            
            with st.expander(f"📄 {move_id} - {doc_type} - {file_name}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"""
                    **Document Information:**
                    - Move: {move_id}
                    - Driver: {driver}
                    - Type: {doc_type}
                    - File: {file_name}
                    - Size: {file_size:,} bytes
                    - Uploaded: {uploaded_at} by {uploaded_by}
                    """)
                    
                    if verified:
                        st.success(f"✅ Verified by {verified_by}")
                    else:
                        st.warning("⏳ Pending verification")
                
                with col2:
                    if st.button(f"Download", key=f"download_{doc_id}"):
                        cursor.execute('SELECT file_data FROM factoring_documents WHERE id = ?',
                                     (doc_id,))
                        file_data = cursor.fetchone()[0]
                        
                        st.download_button(
                            "💾 Save File",
                            file_data,
                            file_name,
                            key=f"save_{doc_id}"
                        )
                
                with col3:
                    if st.session_state.get('user_role') in ['Owner', 'Admin']:
                        if st.button(f"Delete", key=f"delete_{doc_id}"):
                            cursor.execute('DELETE FROM factoring_documents WHERE id = ?',
                                         (doc_id,))
                            conn.commit()
                            st.success("Document deleted")
                            st.rerun()
    else:
        st.info("No documents found matching your search criteria")
    
    conn.close()

# Helper function to check document completeness
def check_move_documents(move_id):
    """Check if a move has all required documents"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT rate_confirmation, bol, pod, all_docs_complete
                     FROM document_requirements
                     WHERE move_id = ?''', (move_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'rate_conf': bool(result[0]),
            'bol': bool(result[1]),
            'pod': bool(result[2]),
            'complete': bool(result[3])
        }
    else:
        return {
            'rate_conf': False,
            'bol': False,
            'pod': False,
            'complete': False
        }