"""
Maintenance Scheduler Module
Vernon AI - Trailer and Vehicle Maintenance Management
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

def show_maintenance_interface():
    """Main interface for maintenance scheduling"""
    st.markdown("### 🔧 Maintenance Scheduler")
    
    # Initialize database
    init_maintenance_tables()
    
    tabs = st.tabs(["Schedule Maintenance", "Maintenance History", "Upcoming Services"])
    
    with tabs[0]:
        show_schedule_maintenance()
    
    with tabs[1]:
        show_maintenance_history()
    
    with tabs[2]:
        show_upcoming_services()

def init_maintenance_tables():
    """Initialize maintenance tracking tables"""
    conn = sqlite3.connect('trailer_data.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_type TEXT NOT NULL,
            equipment_id TEXT NOT NULL,
            service_type TEXT NOT NULL,
            scheduled_date DATE NOT NULL,
            completed_date DATE,
            status TEXT DEFAULT 'scheduled',
            notes TEXT,
            cost REAL,
            vendor TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_type TEXT NOT NULL,
            equipment_id TEXT NOT NULL,
            service_type TEXT NOT NULL,
            service_date DATE NOT NULL,
            mileage INTEGER,
            cost REAL,
            vendor TEXT,
            invoice_number TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def show_schedule_maintenance():
    """Interface for scheduling maintenance"""
    st.markdown("#### 📅 Schedule New Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        equipment_type = st.selectbox(
            "Equipment Type",
            ["Trailer", "Truck", "Other"]
        )
        
        # Get equipment list based on type
        equipment_id = st.text_input(
            f"{equipment_type} ID/Number",
            placeholder="Enter equipment identifier"
        )
        
        service_type = st.selectbox(
            "Service Type",
            ["Annual Inspection", "Tire Replacement", "Brake Service", 
             "Oil Change", "General Maintenance", "Repair", "Other"]
        )
    
    with col2:
        scheduled_date = st.date_input(
            "Scheduled Date",
            min_value=datetime.now().date()
        )
        
        vendor = st.text_input("Vendor/Shop Name")
        
        estimated_cost = st.number_input(
            "Estimated Cost",
            min_value=0.0,
            format="%.2f"
        )
    
    notes = st.text_area("Notes")
    
    if st.button("📅 Schedule Maintenance", type="primary"):
        if equipment_id and service_type:
            conn = sqlite3.connect('trailer_data.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO maintenance_schedule 
                (equipment_type, equipment_id, service_type, scheduled_date, 
                 vendor, cost, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (equipment_type, equipment_id, service_type, scheduled_date,
                  vendor, estimated_cost, notes, st.session_state.get('username', 'System')))
            
            conn.commit()
            conn.close()
            
            st.success(f"✅ Maintenance scheduled for {equipment_id}")
        else:
            st.error("Please fill in required fields")

def show_maintenance_history():
    """Show maintenance history"""
    st.markdown("#### 📜 Maintenance History")
    
    conn = sqlite3.connect('trailer_data.db')
    
    # Get maintenance history
    history_df = pd.read_sql_query("""
        SELECT * FROM maintenance_schedule 
        WHERE status = 'completed'
        ORDER BY completed_date DESC
        LIMIT 50
    """, conn)
    
    if not history_df.empty:
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            total_cost = history_df['cost'].sum()
            st.metric("Total Maintenance Cost", f"${total_cost:,.2f}")
        with col2:
            avg_cost = history_df['cost'].mean()
            st.metric("Average Cost", f"${avg_cost:,.2f}")
        with col3:
            service_count = len(history_df)
            st.metric("Services Completed", service_count)
        
        # Display history table
        st.dataframe(
            history_df[['equipment_id', 'service_type', 'completed_date', 
                       'vendor', 'cost', 'notes']],
            hide_index=True
        )
    else:
        st.info("No maintenance history available")
    
    conn.close()

def show_upcoming_services():
    """Show upcoming scheduled services"""
    st.markdown("#### 🔔 Upcoming Services")
    
    conn = sqlite3.connect('trailer_data.db')
    
    # Get upcoming services
    upcoming_df = pd.read_sql_query("""
        SELECT * FROM maintenance_schedule 
        WHERE status = 'scheduled' 
        AND scheduled_date >= date('now')
        ORDER BY scheduled_date ASC
    """, conn)
    
    if not upcoming_df.empty:
        # Highlight overdue services
        today = datetime.now().date()
        
        for _, service in upcoming_df.iterrows():
            scheduled = pd.to_datetime(service['scheduled_date']).date()
            days_until = (scheduled - today).days
            
            if days_until < 0:
                st.error(f"⚠️ OVERDUE: {service['equipment_id']} - {service['service_type']} (Was due {abs(days_until)} days ago)")
            elif days_until <= 7:
                st.warning(f"📢 Due Soon: {service['equipment_id']} - {service['service_type']} (Due in {days_until} days)")
            else:
                st.info(f"📅 Scheduled: {service['equipment_id']} - {service['service_type']} ({scheduled})")
            
            # Mark as complete button
            if st.button(f"✅ Mark Complete", key=f"complete_{service['id']}"):
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE maintenance_schedule 
                    SET status = 'completed', completed_date = ?
                    WHERE id = ?
                """, (datetime.now().date(), service['id']))
                conn.commit()
                st.success("Service marked as complete")
                st.rerun()
    else:
        st.success("✨ No upcoming maintenance scheduled")
    
    conn.close()