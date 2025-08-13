"""
Trailer Data Entry System with Vernon Guidance
Specialized interface for trailer location management and data entry
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3
import json
import uuid

class TrailerDataEntrySystem:
    def __init__(self):
        self.conn = sqlite3.connect('trailer_tracker_streamlined.db')
        self.ensure_tables()
        
    def ensure_tables(self):
        """Ensure trailer tables exist with all necessary columns"""
        cursor = self.conn.cursor()
        
        # Enhanced trailer inventory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trailer_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trailer_number TEXT UNIQUE NOT NULL,
                trailer_type TEXT,
                status TEXT DEFAULT 'available',
                condition TEXT DEFAULT 'good',
                current_location TEXT,
                location_lat REAL,
                location_lng REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT,
                notes TEXT,
                customer_owner TEXT,
                year_manufactured INTEGER,
                last_inspection DATE,
                next_inspection DATE,
                photos TEXT,
                qr_code TEXT,
                is_old_trailer BOOLEAN DEFAULT 0,
                found_by_driver TEXT,
                approval_status TEXT DEFAULT 'pending',
                approved_by TEXT,
                approval_date TIMESTAMP
            )
        ''')
        
        # Trailer location history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trailer_location_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trailer_number TEXT,
                location TEXT,
                lat REAL,
                lng REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT,
                reason TEXT,
                notes TEXT,
                FOREIGN KEY (trailer_number) REFERENCES trailer_inventory(trailer_number)
            )
        ''')
        
        # Trailer status changes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trailer_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trailer_number TEXT,
                old_status TEXT,
                new_status TEXT,
                changed_by TEXT,
                change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason TEXT,
                FOREIGN KEY (trailer_number) REFERENCES trailer_inventory(trailer_number)
            )
        ''')
        
        self.conn.commit()

    def show_data_entry_interface(self, username):
        """Main interface for trailer data entry"""
        st.title("🚛 Trailer Data Management Center")
        
        # Vernon's helpful guidance
        self.show_vernon_helper()
        
        # Tab interface
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📝 Add/Update Trailer",
            "📍 Update Locations",
            "📊 Bulk Operations",
            "🔍 Search & View",
            "📈 Reports"
        ])
        
        with tab1:
            self.show_trailer_entry_form(username)
            
        with tab2:
            self.show_location_update_interface(username)
            
        with tab3:
            self.show_bulk_operations(username)
            
        with tab4:
            self.show_search_interface()
            
        with tab5:
            self.show_data_entry_reports(username)

    def show_vernon_helper(self):
        """Vernon's helpful guidance system"""
        with st.sidebar:
            st.markdown("### 🦸‍♂️ Vernon IT Support")
            st.info("""
            👋 Hi! I'm Vernon, your IT superhero!
            
            I'm here to help you manage trailer data efficiently:
            
            **Quick Tips:**
            • Use Tab key to move between fields
            • Press Enter to submit forms
            • Click 📍 to auto-detect location
            • Use bulk upload for multiple trailers
            
            **Need Help?**
            Click any ❓ icon for instant guidance!
            """)
            
            if st.button("🆘 Get Help from Vernon", use_container_width=True):
                st.balloons()
                st.success("Vernon is here to help! What do you need assistance with?")

    def show_trailer_entry_form(self, username):
        """Form for adding or updating trailer information"""
        st.subheader("Add or Update Trailer Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            trailer_number = st.text_input(
                "Trailer Number*",
                help="Enter the trailer ID (e.g., TR-001, SWT-123)",
                placeholder="TR-001"
            )
            
            trailer_type = st.selectbox(
                "Trailer Type",
                ["Dry Van", "Reefer", "Flatbed", "Step Deck", "Double Drop", "Other"],
                help="Select the type of trailer"
            )
            
            condition = st.selectbox(
                "Condition",
                ["Excellent", "Good", "Fair", "Poor", "Needs Repair"],
                index=1,
                help="Current condition of the trailer"
            )
            
            is_old = st.checkbox(
                "This is an OLD trailer (found/abandoned)",
                help="Check if this trailer was found or is abandoned"
            )
            
        with col2:
            current_location = st.text_input(
                "Current Location*",
                help="Enter the current location (address or landmark)",
                placeholder="123 Main St, City, State"
            )
            
            col2a, col2b = st.columns(2)
            with col2a:
                lat = st.number_input("Latitude", value=0.0, format="%.6f")
            with col2b:
                lng = st.number_input("Longitude", value=0.0, format="%.6f")
            
            if st.button("📍 Auto-Detect Location"):
                st.info("Vernon says: Location detection would use device GPS in production!")
                lat = 33.7490  # Example: Atlanta
                lng = -84.3880
                st.success(f"Location detected: {lat}, {lng}")
            
            customer_owner = st.text_input(
                "Customer/Owner",
                help="Who owns or is assigned this trailer?",
                placeholder="Customer name or 'Company'"
            )
        
        # Additional Information
        with st.expander("📋 Additional Information"):
            col3, col4 = st.columns(2)
            
            with col3:
                year_manufactured = st.number_input(
                    "Year Manufactured",
                    min_value=1990,
                    max_value=2025,
                    value=2020
                )
                
                last_inspection = st.date_input(
                    "Last Inspection Date",
                    value=None
                )
                
                next_inspection = st.date_input(
                    "Next Inspection Due",
                    value=None
                )
            
            with col4:
                notes = st.text_area(
                    "Notes",
                    placeholder="Any additional information about this trailer...",
                    height=120
                )
                
                photos = st.file_uploader(
                    "Upload Photos",
                    accept_multiple_files=True,
                    type=['png', 'jpg', 'jpeg']
                )
        
        # Submit buttons
        col5, col6, col7 = st.columns(3)
        
        with col5:
            if st.button("💾 Save Trailer", type="primary", use_container_width=True):
                if trailer_number and current_location:
                    self.save_trailer_data(
                        trailer_number, trailer_type, condition, current_location,
                        lat, lng, customer_owner, is_old, year_manufactured,
                        last_inspection, next_inspection, notes, username
                    )
                    st.success(f"✅ Trailer {trailer_number} saved successfully!")
                    st.balloons()
                else:
                    st.error("Please fill in required fields (Trailer Number and Location)")
        
        with col6:
            if st.button("🔄 Clear Form", use_container_width=True):
                st.rerun()
        
        with col7:
            if st.button("❓ Help", use_container_width=True):
                st.info("""
                Vernon's Quick Guide:
                1. Enter trailer number (required)
                2. Select trailer type and condition
                3. Enter current location (required)
                4. Optionally add GPS coordinates
                5. Fill additional info if available
                6. Click Save to submit
                """)

    def show_location_update_interface(self, username):
        """Interface for updating trailer locations"""
        st.subheader("📍 Update Trailer Locations")
        
        # Quick location update
        st.markdown("### Quick Location Update")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Get list of trailers
            cursor = self.conn.cursor()
            cursor.execute("SELECT trailer_number FROM trailer_inventory ORDER BY trailer_number")
            trailers = [row[0] for row in cursor.fetchall()]
            
            selected_trailer = st.selectbox(
                "Select Trailer",
                [""] + trailers,
                help="Choose the trailer to update"
            )
        
        with col2:
            new_location = st.text_input(
                "New Location",
                placeholder="Enter new location"
            )
        
        with col3:
            reason = st.selectbox(
                "Reason for Move",
                ["Delivery", "Pickup", "Storage", "Maintenance", "Transfer", "Other"]
            )
        
        if st.button("📍 Update Location", type="primary", use_container_width=True):
            if selected_trailer and new_location:
                self.update_trailer_location(selected_trailer, new_location, reason, username)
                st.success(f"✅ Location updated for {selected_trailer}")
            else:
                st.error("Please select a trailer and enter new location")
        
        # Batch location updates
        st.markdown("### Batch Location Updates")
        st.info("Vernon says: You can update multiple trailers at once! Upload a CSV with columns: trailer_number, new_location, reason")
        
        uploaded_file = st.file_uploader("Upload CSV for batch updates", type=['csv'])
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
            
            if st.button("🚀 Process Batch Update"):
                with st.spinner("Processing batch updates..."):
                    success_count = 0
                    for _, row in df.iterrows():
                        try:
                            self.update_trailer_location(
                                row['trailer_number'],
                                row['new_location'],
                                row.get('reason', 'Batch Update'),
                                username
                            )
                            success_count += 1
                        except Exception as e:
                            st.warning(f"Failed to update {row['trailer_number']}: {e}")
                    
                    st.success(f"✅ Successfully updated {success_count} trailers!")

    def show_bulk_operations(self, username):
        """Bulk operations interface"""
        st.subheader("📊 Bulk Operations")
        
        operation = st.radio(
            "Select Operation",
            ["Import Trailers", "Export Data", "Update Status", "Delete Old Records"]
        )
        
        if operation == "Import Trailers":
            st.markdown("### Import Multiple Trailers")
            st.info("Upload a CSV file with trailer information")
            
            # Show template
            if st.button("📥 Download Template"):
                template_df = pd.DataFrame({
                    'trailer_number': ['TR-001', 'TR-002'],
                    'trailer_type': ['Dry Van', 'Reefer'],
                    'condition': ['Good', 'Excellent'],
                    'current_location': ['Location 1', 'Location 2'],
                    'customer_owner': ['Customer A', 'Customer B']
                })
                csv = template_df.to_csv(index=False)
                st.download_button(
                    "Download CSV Template",
                    csv,
                    "trailer_import_template.csv",
                    "text/csv"
                )
            
            uploaded = st.file_uploader("Choose CSV file", type=['csv'])
            if uploaded:
                df = pd.read_csv(uploaded)
                st.dataframe(df)
                
                if st.button("🚀 Import Trailers", type="primary"):
                    self.import_trailers_bulk(df, username)
                    st.success(f"✅ Imported {len(df)} trailers successfully!")
        
        elif operation == "Export Data":
            st.markdown("### Export Trailer Data")
            
            export_format = st.selectbox("Export Format", ["CSV", "Excel", "JSON"])
            
            if st.button("📤 Export All Trailers"):
                df = self.get_all_trailers()
                
                if export_format == "CSV":
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"trailers_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )
                elif export_format == "JSON":
                    json_str = df.to_json(orient='records')
                    st.download_button(
                        "Download JSON",
                        json_str,
                        f"trailers_export_{datetime.now().strftime('%Y%m%d')}.json",
                        "application/json"
                    )
        
        elif operation == "Update Status":
            st.markdown("### Bulk Status Update")
            
            status_filter = st.selectbox(
                "Current Status",
                ["available", "in_use", "maintenance", "retired"]
            )
            
            new_status = st.selectbox(
                "New Status",
                ["available", "in_use", "maintenance", "retired"]
            )
            
            if st.button("🔄 Update All Matching Trailers"):
                count = self.bulk_update_status(status_filter, new_status, username)
                st.success(f"✅ Updated {count} trailers from {status_filter} to {new_status}")

    def show_search_interface(self):
        """Search and view trailers"""
        st.subheader("🔍 Search Trailers")
        
        # Search filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input(
                "Search",
                placeholder="Trailer number or location..."
            )
        
        with col2:
            status_filter = st.selectbox(
                "Status",
                ["All", "available", "in_use", "maintenance", "retired"]
            )
        
        with col3:
            condition_filter = st.selectbox(
                "Condition",
                ["All", "Excellent", "Good", "Fair", "Poor", "Needs Repair"]
            )
        
        # Search results
        df = self.search_trailers(search_term, status_filter, condition_filter)
        
        if not df.empty:
            st.markdown(f"### Found {len(df)} trailers")
            
            # Display options
            view_mode = st.radio(
                "View Mode",
                ["Table", "Cards", "Map"],
                horizontal=True
            )
            
            if view_mode == "Table":
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "trailer_number": st.column_config.TextColumn("Trailer #"),
                        "current_location": st.column_config.TextColumn("Location"),
                        "status": st.column_config.SelectboxColumn("Status"),
                        "condition": st.column_config.SelectboxColumn("Condition"),
                        "last_updated": st.column_config.DatetimeColumn("Last Updated")
                    }
                )
            
            elif view_mode == "Cards":
                for _, trailer in df.iterrows():
                    with st.expander(f"🚛 {trailer['trailer_number']} - {trailer['status']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Type:** {trailer['trailer_type']}")
                            st.write(f"**Condition:** {trailer['condition']}")
                            st.write(f"**Location:** {trailer['current_location']}")
                        with col2:
                            st.write(f"**Owner:** {trailer['customer_owner']}")
                            st.write(f"**Updated:** {trailer['last_updated']}")
                            st.write(f"**By:** {trailer['updated_by']}")
            
            elif view_mode == "Map":
                st.info("Vernon says: Map view would show trailer locations on an interactive map!")
        else:
            st.info("No trailers found matching your criteria")

    def show_data_entry_reports(self, username):
        """Reports for data entry activities"""
        st.subheader("📈 Data Entry Reports")
        
        # Activity summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = self.get_trailer_count()
            st.metric("Total Trailers", total)
        
        with col2:
            available = self.get_trailer_count("available")
            st.metric("Available", available)
        
        with col3:
            in_use = self.get_trailer_count("in_use")
            st.metric("In Use", in_use)
        
        with col4:
            maintenance = self.get_trailer_count("maintenance")
            st.metric("Maintenance", maintenance)
        
        # Recent activities
        st.markdown("### Recent Updates by You")
        recent_df = self.get_recent_updates(username)
        if not recent_df.empty:
            st.dataframe(recent_df, use_container_width=True, hide_index=True)
        else:
            st.info("No recent updates")
        
        # Generate PDF report
        if st.button("📄 Generate PDF Report", type="primary"):
            st.info("Generating trailer inventory report...")
            # Would integrate with pdf_report_generator.py here

    # Database operations
    def save_trailer_data(self, trailer_number, trailer_type, condition, location,
                         lat, lng, owner, is_old, year, last_insp, next_insp, notes, username):
        """Save trailer data to database"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO trailer_inventory
            (trailer_number, trailer_type, condition, current_location, location_lat, location_lng,
             customer_owner, is_old_trailer, year_manufactured, last_inspection, next_inspection,
             notes, updated_by, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (trailer_number, trailer_type, condition, location, lat, lng,
              owner, is_old, year, last_insp, next_insp, notes, username, datetime.now()))
        
        self.conn.commit()
        
        # Log location history
        self.log_location_history(trailer_number, location, lat, lng, username, "Initial Entry")

    def update_trailer_location(self, trailer_number, new_location, reason, username):
        """Update trailer location"""
        cursor = self.conn.cursor()
        
        # Get current location for history
        cursor.execute("SELECT current_location FROM trailer_inventory WHERE trailer_number = ?",
                      (trailer_number,))
        old_location = cursor.fetchone()
        
        # Update location
        cursor.execute('''
            UPDATE trailer_inventory
            SET current_location = ?, last_updated = ?, updated_by = ?
            WHERE trailer_number = ?
        ''', (new_location, datetime.now(), username, trailer_number))
        
        self.conn.commit()
        
        # Log history
        self.log_location_history(trailer_number, new_location, 0, 0, username, reason)

    def log_location_history(self, trailer_number, location, lat, lng, username, reason):
        """Log location change history"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO trailer_location_history
            (trailer_number, location, lat, lng, updated_by, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (trailer_number, location, lat, lng, username, reason))
        self.conn.commit()

    def import_trailers_bulk(self, df, username):
        """Import multiple trailers from DataFrame"""
        for _, row in df.iterrows():
            self.save_trailer_data(
                row.get('trailer_number'),
                row.get('trailer_type', 'Dry Van'),
                row.get('condition', 'Good'),
                row.get('current_location', 'Unknown'),
                row.get('lat', 0),
                row.get('lng', 0),
                row.get('customer_owner', ''),
                row.get('is_old', False),
                row.get('year_manufactured', 2020),
                None, None,
                row.get('notes', ''),
                username
            )

    def get_all_trailers(self):
        """Get all trailers as DataFrame"""
        query = "SELECT * FROM trailer_inventory ORDER BY trailer_number"
        return pd.read_sql_query(query, self.conn)

    def search_trailers(self, search_term, status, condition):
        """Search trailers with filters"""
        query = "SELECT * FROM trailer_inventory WHERE 1=1"
        params = []
        
        if search_term:
            query += " AND (trailer_number LIKE ? OR current_location LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if status != "All":
            query += " AND status = ?"
            params.append(status)
        
        if condition != "All":
            query += " AND condition = ?"
            params.append(condition)
        
        query += " ORDER BY last_updated DESC"
        
        return pd.read_sql_query(query, self.conn, params=params)

    def get_trailer_count(self, status=None):
        """Get count of trailers"""
        cursor = self.conn.cursor()
        if status:
            cursor.execute("SELECT COUNT(*) FROM trailer_inventory WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT COUNT(*) FROM trailer_inventory")
        return cursor.fetchone()[0]

    def get_recent_updates(self, username, limit=10):
        """Get recent updates by user"""
        query = """
        SELECT trailer_number, current_location, last_updated, condition, status
        FROM trailer_inventory
        WHERE updated_by = ?
        ORDER BY last_updated DESC
        LIMIT ?
        """
        return pd.read_sql_query(query, self.conn, params=(username, limit))

    def bulk_update_status(self, old_status, new_status, username):
        """Bulk update trailer status"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE trailer_inventory
            SET status = ?, updated_by = ?, last_updated = ?
            WHERE status = ?
        ''', (new_status, username, datetime.now(), old_status))
        
        count = cursor.rowcount
        self.conn.commit()
        return count

def show_trailer_data_entry_interface(username):
    """Main entry point for trailer data entry system"""
    system = TrailerDataEntrySystem()
    system.show_data_entry_interface(username)

if __name__ == "__main__":
    # Test the system
    st.set_page_config(page_title="Trailer Data Entry", page_icon="🚛", layout="wide")
    show_trailer_data_entry_interface("test_user")