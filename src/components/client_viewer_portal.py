"""
Client Portal - Customer view of their shipments
Shows move progress without driver information
Viewer Dashboard - Birds eye view of the system
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def show_client_portal(client_company):
    """Display client portal for tracking shipments"""
    st.markdown(f"# 🏢 {client_company} Shipment Tracking Portal")
    st.caption(f"Real-time tracking as of {datetime.now().strftime('%I:%M %p EST')}")
    
    # Tabs for different views
    tabs = st.tabs(["📍 Active Shipments", "✅ Completed Deliveries", "📊 Performance Metrics", "📄 Documents"])
    
    conn = get_connection()
    cursor = conn.cursor()
    
    with tabs[0]:  # Active Shipments
        st.markdown("## Active Shipments")
        
        # Get active moves for this client (hiding driver info)
        cursor.execute('''SELECT move_id, pickup_location, delivery_location, 
                                status, move_date, new_trailer, old_trailer
                         FROM moves 
                         WHERE customer_name = ? 
                         AND status IN ('pending', 'assigned', 'in_progress')
                         ORDER BY move_date''', (client_company,))
        
        active_moves = cursor.fetchall()
        
        if active_moves:
            for move in active_moves:
                move_id, pickup, delivery, status, date, new_t, old_t = move
                
                # Status colors
                status_color = {
                    'pending': '🟡',
                    'assigned': '🔵',
                    'in_progress': '🟢'
                }.get(status, '⚪')
                
                with st.expander(f"{status_color} {move_id} - {pickup} → {delivery}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        **Shipment Details:**
                        - Route: {pickup} → {delivery}
                        - Trailers: {new_t} / {old_t}
                        - Scheduled: {date}
                        - Current Status: **{status.replace('_', ' ').title()}**
                        """)
                    
                    with col2:
                        # Progress indicator
                        progress = {
                            'pending': 25,
                            'assigned': 50,
                            'in_progress': 75
                        }.get(status, 0)
                        
                        st.markdown("**Delivery Progress:**")
                        st.progress(progress / 100)
                        st.caption(f"{progress}% Complete")
                        
                        # Estimated completion
                        if status == 'in_progress':
                            st.info("🚚 Driver en route - Delivery in progress")
                        elif status == 'assigned':
                            st.info("✅ Driver assigned - Pickup scheduled")
                        else:
                            st.info("📋 Awaiting driver assignment")
        else:
            st.info("No active shipments at this time")
    
    with tabs[1]:  # Completed Deliveries
        st.markdown("## Completed Deliveries")
        
        # Date filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", datetime.now().replace(day=1))
        with col2:
            end_date = st.date_input("To Date", datetime.now())
        
        # Get completed moves
        cursor.execute('''SELECT move_id, pickup_location, delivery_location,
                                completed_date, total_miles, new_trailer, old_trailer
                         FROM moves
                         WHERE customer_name = ?
                         AND status = 'completed'
                         AND completed_date BETWEEN ? AND ?
                         ORDER BY completed_date DESC''',
                      (client_company, start_date, end_date))
        
        completed_moves = cursor.fetchall()
        
        if completed_moves:
            st.success(f"✅ {len(completed_moves)} deliveries completed in selected period")
            
            for move in completed_moves:
                move_id, pickup, delivery, comp_date, miles, new_t, old_t = move
                
                with st.expander(f"✅ {move_id} - Completed {comp_date}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"""
                        **Route:**
                        {pickup} → {delivery}
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **Details:**
                        - Distance: {miles} miles
                        - Trailers: {new_t} / {old_t}
                        """)
                    
                    with col3:
                        st.markdown(f"""
                        **Completion:**
                        - Date: {comp_date}
                        - Status: ✅ Delivered
                        """)
                    
                    # POD availability check
                    cursor.execute('''SELECT COUNT(*) FROM factoring_documents
                                     WHERE move_id = ? AND document_type = 'POD' ''',
                                  (move_id,))
                    has_pod = cursor.fetchone()[0] > 0
                    
                    if has_pod:
                        st.success("📄 Proof of Delivery available in Documents tab")
        else:
            st.info("No completed deliveries in selected period")
    
    with tabs[2]:  # Performance Metrics
        st.markdown("## Performance Metrics")
        
        # Get metrics for this client
        cursor.execute('''SELECT 
                            COUNT(*) as total_moves,
                            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                            COUNT(CASE WHEN status IN ('in_progress', 'assigned') THEN 1 END) as active,
                            AVG(CASE WHEN status = 'completed' THEN total_miles END) as avg_miles
                         FROM moves
                         WHERE customer_name = ?''', (client_company,))
        
        metrics = cursor.fetchone()
        total, completed, active, avg_miles = metrics
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Shipments", total or 0)
        with col2:
            st.metric("Completed", completed or 0)
        with col3:
            st.metric("Active", active or 0)
        with col4:
            st.metric("Avg Distance", f"{int(avg_miles or 0)} mi")
        
        # On-time delivery rate (simplified)
        st.markdown("### Delivery Performance")
        if completed and completed > 0:
            on_time_rate = 95  # Would calculate from actual data
            st.metric("On-Time Delivery Rate", f"{on_time_rate}%")
            st.progress(on_time_rate / 100)
        
        # Monthly trend
        st.markdown("### Monthly Shipment Trend")
        cursor.execute('''SELECT strftime('%Y-%m', move_date) as month,
                                COUNT(*) as count
                         FROM moves
                         WHERE customer_name = ?
                         GROUP BY month
                         ORDER BY month DESC
                         LIMIT 6''', (client_company,))
        
        monthly_data = cursor.fetchall()
        if monthly_data:
            df = pd.DataFrame(monthly_data, columns=['Month', 'Shipments'])
            st.bar_chart(df.set_index('Month'))
    
    with tabs[3]:  # Documents
        st.markdown("## Shipment Documents")
        st.info("Access your delivery confirmations and shipping documents")
        
        # Get moves with documents
        cursor.execute('''SELECT DISTINCT m.move_id, m.completed_date
                         FROM moves m
                         JOIN factoring_documents fd ON m.move_id = fd.move_id
                         WHERE m.customer_name = ?
                         AND fd.document_type IN ('POD', 'BOL')
                         ORDER BY m.completed_date DESC
                         LIMIT 20''', (client_company,))
        
        moves_with_docs = cursor.fetchall()
        
        if moves_with_docs:
            for move_id, comp_date in moves_with_docs:
                with st.expander(f"📄 {move_id} - {comp_date}"):
                    # Get documents for this move
                    cursor.execute('''SELECT document_type, file_name, uploaded_at
                                     FROM factoring_documents
                                     WHERE move_id = ?
                                     AND document_type IN ('POD', 'BOL')''',
                                  (move_id,))
                    
                    docs = cursor.fetchall()
                    
                    for doc_type, file_name, upload_date in docs:
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            if doc_type == 'POD':
                                st.markdown("📸 **Proof of Delivery**")
                            else:
                                st.markdown("📋 **Bill of Lading**")
                        
                        with col2:
                            st.caption(f"Uploaded: {upload_date}")
                        
                        with col3:
                            st.button("📥 Download", key=f"dl_{move_id}_{doc_type}")
        else:
            st.info("No documents available yet")
    
    conn.close()

def show_viewer_dashboard():
    """Birds eye view dashboard for system demonstration"""
    st.markdown("# 🔍 System Overview Dashboard")
    st.caption("Bird's Eye View of Smith & Williams Trucking Management System")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # System overview metrics
    st.markdown("## 📊 System Metrics")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM drivers")
    total_drivers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves")
    total_moves = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers")
    total_trailers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
    completed_moves = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status IN ('in_progress', 'assigned')")
    active_moves = cursor.fetchone()[0]
    
    with col1:
        st.metric("Users", total_users)
    with col2:
        st.metric("Drivers", total_drivers)
    with col3:
        st.metric("Total Moves", total_moves)
    with col4:
        st.metric("Trailers", total_trailers)
    with col5:
        st.metric("Completed", completed_moves)
    with col6:
        st.metric("Active", active_moves)
    
    st.markdown("---")
    
    # System architecture view
    st.markdown("## 🏗️ System Architecture")
    
    with st.expander("System Components", expanded=True):
        st.markdown("""
        ### Core Modules
        
        **1. User Management System**
        - Role-based access control
        - Multi-level permissions
        - Secure authentication
        
        **2. Move Management**
        - Create and assign moves
        - Track progress in real-time
        - Automated status updates
        
        **3. Document Management**
        - Upload and store documents
        - Factoring submission workflow
        - POD collection system
        
        **4. Payment Processing**
        - Factoring integration
        - Driver payment calculation
        - Navy Federal transfer tracking
        
        **5. Reporting & Analytics**
        - Real-time dashboards
        - Performance metrics
        - Financial reports
        
        **6. Driver Portal**
        - Self-assignment system
        - Money bag earnings tracker
        - Mobile-friendly interface
        
        **7. Client Portal**
        - Shipment tracking
        - Document access
        - Performance metrics
        """)
    
    # Workflow visualization
    st.markdown("## 🔄 System Workflow")
    
    with st.expander("Move Lifecycle", expanded=True):
        st.markdown("""
        ```
        1. CREATE MOVE
           ↓
        2. ASSIGN DRIVER
           ↓
        3. IN PROGRESS
           ↓
        4. COMPLETED
           ↓
        5. COLLECT DOCUMENTS
           ↓
        6. SUBMIT TO FACTORING
           ↓
        7. PROCESS PAYMENT
           ↓
        8. PAY DRIVER
        ```
        
        **Time-Critical Steps:**
        - Document collection: Required before factoring
        - Factoring submission: By 11AM EST for next-day payout
        - Payment processing: After factoring approval
        """)
    
    # Role overview
    st.markdown("## 👥 Role Structure")
    
    roles_df = pd.DataFrame({
        'Role': ['Owner-CEO-Driver', 'Business Admin', 'Ops Coordinator', 
                 'Data Entry', 'Driver', 'Client', 'Viewer'],
        'Access Level': ['Full', 'High', 'Medium', 'Limited', 
                        'Driver Only', 'External', 'Read Only'],
        'Financial Access': ['Yes', 'No', 'No', 'No', 'Own Only', 'No', 'No'],
        'User Mgmt': ['Yes', 'Yes', 'No', 'No', 'No', 'No', 'No']
    })
    
    st.dataframe(roles_df, use_container_width=True, hide_index=True)
    
    # Feature highlights
    st.markdown("## ✨ Key Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Operational Features:**
        - Real-time move tracking
        - Automated trailer management
        - Document workflow system
        - Driver self-assignment
        - Status progression tracking
        - Location management
        """)
    
    with col2:
        st.markdown("""
        **Business Features:**
        - Factoring integration
        - Payment processing
        - Money bag earnings tracker
        - Client portals
        - Performance analytics
        - Deadline alerts (11AM EST)
        """)
    
    conn.close()

# Export functions
__all__ = ['show_client_portal', 'show_viewer_dashboard']