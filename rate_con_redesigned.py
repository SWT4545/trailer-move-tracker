"""
Rate Confirmation Management - Redesigned Interface
Clean, modern layout with improved workflow and user experience
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import base64
from database_connection_manager import db_manager

class RateConRedesigned:
    def __init__(self):
        self.db_path = 'trailer_tracker_streamlined.db' if os.path.exists('trailer_tracker_streamlined.db') else 'trailer_data.db'
        self.ensure_tables()
    
    def ensure_tables(self):
        """Ensure Rate Con tables exist"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS rate_cons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        mlbl_number TEXT,
                        rate_con_number TEXT,
                        client_name TEXT,
                        client_miles REAL,
                        client_rate REAL,
                        client_total REAL,
                        factoring_fee REAL,
                        driver_net REAL,
                        rate_con_file_path TEXT,
                        bol_file_path TEXT,
                        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        matched_to_move_id INTEGER UNIQUE,
                        matched_date TIMESTAMP,
                        matched_by TEXT,
                        status TEXT DEFAULT 'unmatched',
                        notes TEXT
                    )
                """)
                
                conn.commit()
        except:
            pass

def show_rate_con_redesigned():
    """Main Rate Con Interface - Redesigned"""
    st.title("📄 Rate Confirmations")
    
    # Quick stats bar
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pending = get_pending_count()
        st.metric("📥 Pending", pending, delta=f"+{get_today_count()} today")
    
    with col2:
        matched = get_matched_count()
        st.metric("✅ Matched", matched)
    
    with col3:
        verified = get_verified_count()
        st.metric("🔍 Verified", verified)
    
    with col4:
        total_value = get_total_value()
        st.metric("💰 Total Value", f"${total_value:,.2f}")
    
    st.divider()
    
    # Main interface with sidebar navigation
    view_mode = st.radio(
        "Select View",
        ["🆕 Quick Upload", "📋 Manage Documents", "🔄 Match to Moves", "📊 Analytics"],
        horizontal=True
    )
    
    if view_mode == "🆕 Quick Upload":
        show_quick_upload()
    elif view_mode == "📋 Manage Documents":
        show_document_manager()
    elif view_mode == "🔄 Match to Moves":
        show_matching_interface()
    elif view_mode == "📊 Analytics":
        show_analytics_dashboard()

def show_quick_upload():
    """Streamlined upload interface"""
    st.markdown("## 🆕 Quick Upload")
    
    # Create a clean 2-column layout
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.markdown("### 📝 Move Details")
        
        # Simple calculation toggle
        use_total = st.toggle("Calculate from total amount", value=False)
        
        with st.form("quick_upload", clear_on_submit=True):
            # MLBL Number (optional)
            mlbl = st.text_input(
                "MLBL Number", 
                placeholder="Optional - e.g., MLBL-58064"
            )
            
            if not use_total:
                # Enter miles and rate
                miles = st.number_input("Miles", min_value=0.0, step=1.0)
                rate = st.number_input("Rate ($/mile)", min_value=0.0, step=0.01, value=2.10)
                total = miles * rate
            else:
                # Enter total and calculate miles
                total = st.number_input("Total Amount ($)", min_value=0.0, step=0.01)
                rate = st.number_input("Rate ($/mile)", min_value=0.0, step=0.01, value=2.10)
                miles = total / rate if rate > 0 else 0
            
            # File uploads in a cleaner layout
            st.markdown("### 📎 Documents")
            rate_con_file = st.file_uploader(
                "Rate Confirmation",
                type=['pdf', 'png', 'jpg', 'jpeg'],
                key="rc_upload"
            )
            
            bol_file = st.file_uploader(
                "Bill of Lading (BOL)",
                type=['pdf', 'png', 'jpg', 'jpeg'],
                key="bol_upload"
            )
            
            notes = st.text_area("Notes", placeholder="Optional notes...")
            
            submitted = st.form_submit_button(
                "📤 Upload Documents",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                if miles > 0 and rate > 0:
                    # Save the documents
                    save_rate_con(mlbl, miles, rate, total, rate_con_file, bol_file, notes)
                    st.success("✅ Documents uploaded successfully!")
                    st.balloons()
                else:
                    st.error("Please enter miles and rate")
    
    with col2:
        st.markdown("### 💡 Live Preview")
        
        # Show calculation preview
        if miles > 0 and rate > 0:
            # Create a nice preview card
            st.markdown("""
                <div style='
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem;
                    border-radius: 1rem;
                    color: white;
                '>
                    <h3 style='color: white; margin: 0;'>📋 Rate Con Summary</h3>
                    <hr style='border-color: rgba(255,255,255,0.3);'>
            """, unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**Distance**")
                st.markdown(f"# {miles:.1f} mi")
                
                st.markdown("**Rate**")
                st.markdown(f"# ${rate:.2f}/mi")
            
            with col_b:
                st.markdown("**Gross Total**")
                st.markdown(f"# ${total:.2f}")
                
                factoring = total * 0.03
                net = total - factoring
                
                st.markdown("**Driver Net (97%)**")
                st.markdown(f"# ${net:.2f}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Show recent uploads
            st.markdown("### 📜 Recent Uploads")
            recent = get_recent_uploads(5)
            if not recent.empty:
                for _, upload in recent.iterrows():
                    with st.expander(f"📄 {upload['mlbl_number'] or 'No MLBL'} - ${upload['client_total']:.2f}"):
                        st.write(f"**Miles:** {upload['client_miles']:.1f}")
                        st.write(f"**Rate:** ${upload['client_rate']:.2f}")
                        st.write(f"**Uploaded:** {upload['upload_date']}")
        else:
            # Empty state
            st.info("👈 Enter move details to see preview")

def show_document_manager():
    """Document management interface"""
    st.markdown("## 📋 Document Manager")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "Unmatched", "Matched", "Verified"]
        )
    
    with col2:
        date_filter = st.date_input(
            "From Date",
            value=datetime.now() - timedelta(days=7)
        )
    
    with col3:
        search = st.text_input("Search MLBL/Driver", placeholder="Search...")
    
    # Get filtered documents
    documents = get_filtered_documents(status_filter, date_filter, search)
    
    if not documents.empty:
        # Show documents in a clean table
        st.dataframe(
            documents[['mlbl_number', 'client_miles', 'client_rate', 'client_total', 'status', 'upload_date']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "mlbl_number": "MLBL",
                "client_miles": st.column_config.NumberColumn("Miles", format="%.1f"),
                "client_rate": st.column_config.NumberColumn("Rate", format="$%.2f"),
                "client_total": st.column_config.NumberColumn("Total", format="$%.2f"),
                "status": st.column_config.SelectboxColumn("Status", options=["unmatched", "matched", "verified"]),
                "upload_date": st.column_config.DatetimeColumn("Uploaded", format="MM/DD HH:mm")
            }
        )
    else:
        st.info("No documents found matching your filters")

def show_matching_interface():
    """Interface for matching Rate Cons to moves"""
    st.markdown("## 🔄 Match Documents to Moves")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📄 Unmatched Documents")
        
        unmatched = get_unmatched_rate_cons()
        
        if not unmatched.empty:
            selected_rc = st.selectbox(
                "Select Document",
                unmatched['id'].tolist(),
                format_func=lambda x: f"MLBL: {unmatched[unmatched['id']==x]['mlbl_number'].iloc[0] or 'None'} - ${unmatched[unmatched['id']==x]['client_total'].iloc[0]:.2f}"
            )
            
            if selected_rc:
                rc_details = unmatched[unmatched['id'] == selected_rc].iloc[0]
                
                # Show document details
                st.info(f"""
                **Miles:** {rc_details['client_miles']:.1f}  
                **Rate:** ${rc_details['client_rate']:.2f}  
                **Total:** ${rc_details['client_total']:.2f}  
                **Driver Net:** ${rc_details['driver_net']:.2f}
                """)
        else:
            st.success("✅ All documents matched!")
    
    with col2:
        st.markdown("### 🚛 Available Moves")
        
        unmatched_moves = get_unmatched_moves()
        
        if not unmatched_moves.empty:
            selected_move = st.selectbox(
                "Select Move",
                unmatched_moves['id'].tolist(),
                format_func=lambda x: f"Move #{x} - {unmatched_moves[unmatched_moves['id']==x]['driver_name'].iloc[0]} - {unmatched_moves[unmatched_moves['id']==x]['delivery_location'].iloc[0]}"
            )
            
            if selected_move:
                move_details = unmatched_moves[unmatched_moves['id'] == selected_move].iloc[0]
                
                # Show move details
                st.info(f"""
                **Driver:** {move_details['driver_name']}  
                **Location:** {move_details['delivery_location']}  
                **Our Miles:** {move_details.get('total_miles', 0):.1f}  
                **Date:** {move_details['move_date']}
                """)
                
                # Match button
                if st.button("🔗 Match Documents", type="primary", use_container_width=True):
                    if match_rate_con_to_move(selected_rc, selected_move):
                        st.success("✅ Documents matched successfully!")
                        st.rerun()
        else:
            st.info("No unmatched moves available")

def show_analytics_dashboard():
    """Analytics and insights"""
    st.markdown("## 📊 Analytics Dashboard")
    
    # Date range selector
    col1, col2 = st.columns([1, 3])
    
    with col1:
        date_range = st.selectbox(
            "Time Period",
            ["Last 7 Days", "Last 30 Days", "This Month", "All Time"]
        )
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_miles = get_average_miles(date_range)
        st.metric("📏 Avg Miles", f"{avg_miles:.1f}")
    
    with col2:
        avg_rate = get_average_rate(date_range)
        st.metric("💵 Avg Rate", f"${avg_rate:.2f}")
    
    with col3:
        total_revenue = get_total_revenue(date_range)
        st.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
    
    with col4:
        accuracy = get_mileage_accuracy(date_range)
        st.metric("🎯 Mileage Accuracy", f"{accuracy:.1f}%")
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Revenue Trend")
        revenue_data = get_revenue_trend(date_range)
        if not revenue_data.empty:
            st.line_chart(revenue_data.set_index('date')['revenue'])
    
    with col2:
        st.markdown("### 📊 Mileage Variance")
        variance_data = get_mileage_variance(date_range)
        if not variance_data.empty:
            st.bar_chart(variance_data.set_index('move_id')['variance'])

# Helper functions (stubs - implement with actual database queries)

def get_pending_count():
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rate_cons WHERE status = 'unmatched'")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_today_count():
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rate_cons WHERE DATE(upload_date) = DATE('now')")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_matched_count():
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rate_cons WHERE status = 'matched'")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_verified_count():
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rate_cons WHERE status = 'verified'")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_total_value():
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(client_total) FROM rate_cons WHERE status != 'cancelled'")
        total = cursor.fetchone()[0] or 0
        conn.close()
        return total
    except:
        return 0

def get_recent_uploads(limit=5):
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        query = f"SELECT * FROM rate_cons ORDER BY upload_date DESC LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def get_filtered_documents(status, date, search):
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        query = "SELECT * FROM rate_cons WHERE 1=1"
        params = []
        
        if status != "All":
            query += " AND status = ?"
            params.append(status.lower())
        
        if date:
            query += " AND DATE(upload_date) >= ?"
            params.append(date)
        
        if search:
            query += " AND (mlbl_number LIKE ? OR notes LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY upload_date DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def get_unmatched_rate_cons():
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        query = "SELECT * FROM rate_cons WHERE status = 'unmatched' ORDER BY upload_date DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def get_unmatched_moves():
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        query = """
            SELECT * FROM trailer_moves 
            WHERE id NOT IN (SELECT matched_to_move_id FROM rate_cons WHERE matched_to_move_id IS NOT NULL)
            AND status IN ('completed', 'in_progress')
            ORDER BY move_date DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def save_rate_con(mlbl, miles, rate, total, rc_file, bol_file, notes):
    """Save rate con to database"""
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        factoring_fee = total * 0.03
        driver_net = total - factoring_fee
        
        cursor.execute("""
            INSERT INTO rate_cons (mlbl_number, client_miles, client_rate, client_total, 
                                  factoring_fee, driver_net, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'unmatched')
        """, (mlbl, miles, rate, total, factoring_fee, driver_net, notes))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving: {e}")
        return False

def match_rate_con_to_move(rc_id, move_id):
    """Match rate con to move"""
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE rate_cons 
            SET matched_to_move_id = ?, status = 'matched', matched_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (move_id, rc_id))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_average_miles(period):
    return 245.5  # Placeholder

def get_average_rate(period):
    return 2.10  # Placeholder

def get_total_revenue(period):
    return 45678.90  # Placeholder

def get_mileage_accuracy(period):
    return 94.5  # Placeholder

def get_revenue_trend(period):
    return pd.DataFrame()  # Placeholder

def get_mileage_variance(period):
    return pd.DataFrame()  # Placeholder

# Export main function
__all__ = ['show_rate_con_redesigned', 'RateConRedesigned']