"""
Trailer Data Entry System with Vernon IT Guidance
For Data Entry Specialists to manage trailer locations efficiently
Smith & Williams Trucking
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import sqlite3
import json

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def show_vernon_guidance(step, context=""):
    """Vernon provides non-annoying, helpful guidance"""
    guidance = {
        "welcome": """
        🦸‍♂️ **Vernon Here - Your IT Superhero!**
        
        Welcome to the Trailer Management Center! I'm here to help you succeed.
        You're doing important work tracking our trailers. Let me guide you through it!
        
        💡 **Quick Tips:**
        - Use the search to find trailers quickly
        - Double-check trailer numbers before saving
        - I'll help validate your entries automatically
        """,
        
        "add_trailer": """
        ✨ **Adding a New Trailer**
        
        Enter the trailer number carefully - it's like the trailer's ID card!
        Location is super important - be specific (e.g., "Memphis Yard Bay 5")
        """,
        
        "bulk_upload": """
        📊 **Bulk Upload Power Mode!**
        
        You can upload many trailers at once using CSV!
        Download my template first - it shows the exact format needed.
        I'll check everything before we save it.
        """,
        
        "location_update": """
        📍 **Updating Locations**
        
        Great job keeping locations current! Remember:
        - Use consistent naming (e.g., always "Memphis" not "memphis" or "MEM")
        - Include specific spots when possible (Bay, Row, Section numbers)
        """,
        
        "validation_error": f"""
        ⚠️ **Oops! Let me help fix this:**
        
        {context}
        
        No worries - we all make mistakes! Just adjust and try again.
        I'm here to help you succeed! 💪
        """,
        
        "success": """
        🎉 **Excellent Work!**
        
        Your data has been saved successfully!
        The system is now updated across all profiles.
        Keep up the amazing work! You're a data entry champion! 🏆
        """
    }
    
    return guidance.get(step, "I'm here to help! Contact me at ext. 1337 if you need assistance.")

def validate_trailer_number(trailer_number):
    """Validate trailer number format"""
    if not trailer_number:
        return False, "Trailer number is required"
    
    if len(trailer_number) < 3:
        return False, "Trailer number too short (minimum 3 characters)"
    
    if len(trailer_number) > 20:
        return False, "Trailer number too long (maximum 20 characters)"
    
    # Check for invalid characters
    invalid_chars = ['#', '@', '!', '$', '%', '^', '&', '*']
    for char in invalid_chars:
        if char in trailer_number:
            return False, f"Invalid character '{char}' in trailer number"
    
    return True, "Valid"

def validate_location(location):
    """Validate location entry"""
    if not location:
        return False, "Location is required"
    
    if len(location) < 2:
        return False, "Location too short - please be more specific"
    
    return True, "Valid"

def show_trailer_data_entry_interface(username):
    """Main interface for data entry specialists"""
    
    # Header with Vernon
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea, #764ba2); 
                    padding: 1rem; border-radius: 8px; text-align: center;'>
            <h3 style='color: white; margin: 0;'>🦸‍♂️</h3>
            <p style='color: white; margin: 0; font-weight: bold;'>Vernon IT</p>
            <p style='color: white; margin: 0; font-size: 0.8em;'>Here to Help!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("## 📝 Trailer Data Management Center")
        st.markdown(f"*Data Entry Specialist: {username}*")
    
    with col3:
        # Quick stats
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trailers")
        total_trailers = cursor.fetchone()[0]
        conn.close()
        
        st.metric("Total Trailers", total_trailers)
    
    # Vernon's Welcome
    with st.expander("🦸‍♂️ Vernon's Guidance", expanded=True):
        st.info(show_vernon_guidance("welcome"))
    
    # Main tabs
    tabs = st.tabs([
        "➕ Add Trailer",
        "📍 Update Locations", 
        "📊 Bulk Upload",
        "🔍 Search & Edit",
        "📈 Status Overview",
        "💾 Export Data"
    ])
    
    # Add Trailer Tab
    with tabs[0]:
        st.markdown("### Add New Trailer")
        st.info(show_vernon_guidance("add_trailer"))
        
        with st.form("add_trailer_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                trailer_number = st.text_input(
                    "Trailer Number *",
                    placeholder="e.g., TR-001, SMITH-123",
                    help="Unique identifier for the trailer"
                ).upper()
                
                trailer_type = st.selectbox(
                    "Trailer Type *",
                    ["Roller Bed", "Dry Van", "Flatbed", "Reefer", "Step Deck", 
                     "Double Drop", "Lowboy", "Conestoga", "Tanker", "Car Hauler",
                     "Dump Trailer", "Hopper Bottom", "Livestock", "Pneumatic",
                     "Stretch Trailer", "Side Kit", "Other"],
                    help="Select the trailer type"
                )
                
                condition = st.selectbox(
                    "Condition *",
                    ["Excellent", "Good", "Fair", "Poor", "Needs Repair"],
                    help="Current condition of the trailer"
                )
            
            with col2:
                location = st.text_input(
                    "Current Location *",
                    placeholder="e.g., Memphis Yard Bay 5",
                    help="Be specific about the location"
                )
                
                status = st.selectbox(
                    "Status *",
                    ["available", "in_use", "maintenance", "reserved", "retired"],
                    help="Current operational status"
                )
                
                owner = st.text_input(
                    "Owner/Customer",
                    placeholder="Leave blank if company-owned",
                    help="Customer name if not owned by S&W"
                )
            
            notes = st.text_area(
                "Notes",
                placeholder="Any additional information about this trailer",
                help="Optional notes or special instructions"
            )
            
            submitted = st.form_submit_button("➕ Add Trailer", type="primary", use_container_width=True)
            
            if submitted:
                # Validate inputs
                valid_number, number_msg = validate_trailer_number(trailer_number)
                valid_location, location_msg = validate_location(location)
                
                if not valid_number:
                    st.error(show_vernon_guidance("validation_error", number_msg))
                elif not valid_location:
                    st.error(show_vernon_guidance("validation_error", location_msg))
                else:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        # Check if trailer exists
                        cursor.execute("SELECT id FROM trailers WHERE trailer_number = ?", (trailer_number,))
                        if cursor.fetchone():
                            st.error(f"Trailer {trailer_number} already exists! Use the Edit tab to update it.")
                        else:
                            cursor.execute("""
                                INSERT INTO trailers 
                                (trailer_number, trailer_type, condition, location, status, owner, notes, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (trailer_number, trailer_type, condition, location, status, owner, notes, datetime.now()))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(show_vernon_guidance("success"))
                            st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    # Update Locations Tab
    with tabs[1]:
        st.markdown("### Batch Location Update")
        st.info(show_vernon_guidance("location_update"))
        
        # Get all trailers
        conn = get_connection()
        df = pd.read_sql_query("""
            SELECT trailer_number, location, status 
            FROM trailers 
            ORDER BY trailer_number
        """, conn)
        conn.close()
        
        if not df.empty:
            # Allow editing
            st.markdown("#### Edit Locations Below:")
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="fixed",
                column_config={
                    "trailer_number": st.column_config.TextColumn(
                        "Trailer #",
                        disabled=True,
                        width="small"
                    ),
                    "location": st.column_config.TextColumn(
                        "Location",
                        help="Update location here",
                        width="medium"
                    ),
                    "status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["available", "in_use", "maintenance", "reserved", "retired"],
                        width="small"
                    )
                }
            )
            
            if st.button("💾 Save All Changes", type="primary"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    for index, row in edited_df.iterrows():
                        cursor.execute("""
                            UPDATE trailers 
                            SET location = ?, status = ?
                            WHERE trailer_number = ?
                        """, (row['location'], row['status'], row['trailer_number']))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(show_vernon_guidance("success"))
                except Exception as e:
                    st.error(f"Error updating: {e}")
    
    # Bulk Upload Tab
    with tabs[2]:
        st.markdown("### Bulk CSV Upload")
        st.info(show_vernon_guidance("bulk_upload"))
        
        # Download template
        template_data = pd.DataFrame({
            'trailer_number': ['TR-001', 'TR-002', 'TR-003'],
            'trailer_type': ['Dry Van', 'Flatbed', 'Reefer'],
            'condition': ['Good', 'Excellent', 'Fair'],
            'location': ['Memphis Yard Bay 1', 'Nashville Depot', 'Memphis Yard Bay 3'],
            'status': ['available', 'in_use', 'available'],
            'owner': ['', 'Customer ABC', ''],
            'notes': ['', 'Long-term lease', 'Recently serviced']
        })
        
        csv = template_data.to_csv(index=False)
        st.download_button(
            "📥 Download CSV Template",
            csv,
            "trailer_upload_template.csv",
            "text/csv",
            help="Use this template for bulk upload"
        )
        
        # Upload file
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df, use_container_width=True)
                
                if st.button("✅ Import All Trailers", type="primary"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    success_count = 0
                    error_count = 0
                    errors = []
                    
                    for index, row in df.iterrows():
                        try:
                            # Check if trailer exists
                            cursor.execute("SELECT id FROM trailers WHERE trailer_number = ?", 
                                         (row['trailer_number'],))
                            if cursor.fetchone():
                                errors.append(f"Trailer {row['trailer_number']} already exists")
                                error_count += 1
                            else:
                                cursor.execute("""
                                    INSERT INTO trailers 
                                    (trailer_number, trailer_type, condition, location, status, owner, notes, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    row['trailer_number'],
                                    row.get('trailer_type', 'Dry Van'),
                                    row.get('condition', 'Good'),
                                    row.get('location', 'Unknown'),
                                    row.get('status', 'available'),
                                    row.get('owner', ''),
                                    row.get('notes', ''),
                                    datetime.now()
                                ))
                                success_count += 1
                        except Exception as e:
                            errors.append(f"Row {index + 1}: {str(e)}")
                            error_count += 1
                    
                    conn.commit()
                    conn.close()
                    
                    if success_count > 0:
                        st.success(f"✅ Successfully imported {success_count} trailers!")
                    
                    if error_count > 0:
                        st.warning(f"⚠️ {error_count} trailers could not be imported")
                        for error in errors:
                            st.error(error)
                    
                    if success_count > 0:
                        st.balloons()
                        st.info(show_vernon_guidance("success"))
                        
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    # Search & Edit Tab
    with tabs[3]:
        st.markdown("### Search and Edit Trailers")
        
        search_term = st.text_input("🔍 Search trailers", placeholder="Enter trailer number or location")
        
        conn = get_connection()
        if search_term:
            query = """
                SELECT * FROM trailers 
                WHERE trailer_number LIKE ? OR location LIKE ?
                ORDER BY trailer_number
            """
            df = pd.read_sql_query(query, conn, params=[f"%{search_term}%", f"%{search_term}%"])
        else:
            df = pd.read_sql_query("SELECT * FROM trailers ORDER BY trailer_number LIMIT 50", conn)
        conn.close()
        
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Edit specific trailer
            st.markdown("#### Edit Trailer")
            trailer_to_edit = st.selectbox("Select trailer to edit", df['trailer_number'].tolist())
            
            if trailer_to_edit:
                trailer_data = df[df['trailer_number'] == trailer_to_edit].iloc[0]
                
                with st.form("edit_trailer_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_type = st.selectbox("Type", 
                            ["Roller Bed", "Dry Van", "Flatbed", "Reefer", "Step Deck", "Other"],
                            index=["Roller Bed", "Dry Van", "Flatbed", "Reefer", "Step Deck", "Other"].index(
                                trailer_data['trailer_type']) if trailer_data['trailer_type'] in 
                                ["Roller Bed", "Dry Van", "Flatbed", "Reefer", "Step Deck", "Other"] else 0
                        )
                        new_condition = st.selectbox("Condition",
                            ["Excellent", "Good", "Fair", "Poor", "Needs Repair"],
                            index=["Excellent", "Good", "Fair", "Poor", "Needs Repair"].index(
                                trailer_data['condition']) if trailer_data['condition'] in
                                ["Excellent", "Good", "Fair", "Poor", "Needs Repair"] else 1
                        )
                    
                    with col2:
                        new_location = st.text_input("Location", value=trailer_data['location'])
                        new_status = st.selectbox("Status",
                            ["available", "in_use", "maintenance", "reserved", "retired"],
                            index=["available", "in_use", "maintenance", "reserved", "retired"].index(
                                trailer_data['status']) if trailer_data['status'] in
                                ["available", "in_use", "maintenance", "reserved", "retired"] else 0
                        )
                    
                    new_notes = st.text_area("Notes", value=trailer_data['notes'] if trailer_data['notes'] else "")
                    
                    if st.form_submit_button("💾 Update Trailer", type="primary"):
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE trailers 
                                SET trailer_type = ?, condition = ?, location = ?, 
                                    status = ?, notes = ?
                                WHERE trailer_number = ?
                            """, (new_type, new_condition, new_location, new_status, 
                                  new_notes, trailer_to_edit))
                            conn.commit()
                            conn.close()
                            
                            st.success(f"✅ Trailer {trailer_to_edit} updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    
    # Status Overview Tab
    with tabs[4]:
        st.markdown("### Trailer Status Overview")
        
        conn = get_connection()
        
        # Status summary
        status_df = pd.read_sql_query("""
            SELECT status, COUNT(*) as count 
            FROM trailers 
            GROUP BY status 
            ORDER BY count DESC
        """, conn)
        
        # Location summary
        location_df = pd.read_sql_query("""
            SELECT location, COUNT(*) as count 
            FROM trailers 
            GROUP BY location 
            ORDER BY count DESC 
            LIMIT 10
        """, conn)
        
        # Type summary
        type_df = pd.read_sql_query("""
            SELECT trailer_type, COUNT(*) as count 
            FROM trailers 
            GROUP BY trailer_type 
            ORDER BY count DESC
        """, conn)
        
        conn.close()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### By Status")
            if not status_df.empty:
                for index, row in status_df.iterrows():
                    st.metric(row['status'].title(), row['count'])
        
        with col2:
            st.markdown("#### Top Locations")
            if not location_df.empty:
                st.dataframe(location_df, use_container_width=True, hide_index=True)
        
        with col3:
            st.markdown("#### By Type")
            if not type_df.empty:
                st.dataframe(type_df, use_container_width=True, hide_index=True)
    
    # Export Data Tab
    with tabs[5]:
        st.markdown("### Export Trailer Data")
        
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM trailers ORDER BY trailer_number", conn)
        conn.close()
        
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download as CSV",
                    csv,
                    f"trailers_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col2:
                json_str = df.to_json(orient='records', indent=2)
                st.download_button(
                    "📥 Download as JSON",
                    json_str,
                    f"trailers_export_{datetime.now().strftime('%Y%m%d')}.json",
                    "application/json",
                    use_container_width=True
                )
            
            st.markdown("### Data Preview")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Show Vernon's success message
            st.success(f"""
            🦸‍♂️ **Great Job, {username}!**
            
            You're managing {len(df)} trailers like a champion!
            Your accurate data entry keeps our entire operation running smoothly.
            
            Remember: I'm always here at ext. 1337 if you need help!
            
            - Vernon, Your IT Superhero
            """)

# For backward compatibility
class TrailerDataEntrySystem:
    def show_interface(self, username):
        show_trailer_data_entry_interface(username)