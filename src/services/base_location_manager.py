"""
Base Location Management System
For Executive and Admin control of base locations
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import database as db
import json

def init_base_locations_table():
    """Initialize base locations table"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Create base_locations table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS base_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name TEXT UNIQUE NOT NULL,
                street_address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                full_address TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                notes TEXT
            )
        ''')
        
        # Ensure Fleet Memphis exists as default
        cursor.execute('''
            INSERT OR IGNORE INTO base_locations 
            (location_name, street_address, city, state, zip_code, full_address, is_default, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "Fleet Memphis",
            "3691 Pilot Dr",
            "Memphis",
            "TN",
            "38118",
            "3691 Pilot Dr, Memphis, TN 38118, USA",
            1,
            "System"
        ))
        conn.commit()

def get_base_locations():
    """Get all base locations from database"""
    init_base_locations_table()  # Ensure table exists
    with db.get_connection() as conn:
        
        # Get all base locations
        return pd.read_sql_query('''
            SELECT * FROM base_locations 
            WHERE is_active = 1 
            ORDER BY is_default DESC, location_name
        ''', conn)

def get_default_base_location():
    """Get the current default base location"""
    init_base_locations_table()  # Ensure table exists
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT location_name FROM base_locations 
            WHERE is_default = 1 AND is_active = 1
            LIMIT 1
        ''')
        result = cursor.fetchone()
        return result[0] if result else "Fleet Memphis"

def set_default_base_location(location_name, changed_by):
    """Set a new default base location"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Remove current default
        cursor.execute('UPDATE base_locations SET is_default = 0')
        
        # Set new default
        cursor.execute('''
            UPDATE base_locations 
            SET is_default = 1 
            WHERE location_name = ? AND is_active = 1
        ''', (location_name,))
        
        # Log the change
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS base_location_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name TEXT,
                change_type TEXT,
                changed_by TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        ''')
        
        cursor.execute('''
            INSERT INTO base_location_changes (location_name, change_type, changed_by, details)
            VALUES (?, 'set_default', ?, 'Changed default base location')
        ''', (location_name, changed_by))
        
        conn.commit()
        return True

def add_base_location(data, added_by):
    """Add a new base location"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Build full address
        full_address = f"{data['street_address']}, {data['city']}, {data['state']} {data['zip_code']}, USA"
        
        cursor.execute('''
            INSERT INTO base_locations 
            (location_name, street_address, city, state, zip_code, full_address, created_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['location_name'],
            data['street_address'],
            data['city'],
            data['state'],
            data['zip_code'],
            full_address,
            added_by,
            data.get('notes', '')
        ))
        
        # Also add to regular locations table
        cursor.execute('''
            INSERT OR IGNORE INTO locations 
            (location_title, location_address, street_address, city, state, zip_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['location_name'],
            full_address,
            data['street_address'],
            data['city'],
            data['state'],
            data['zip_code']
        ))
        
        conn.commit()
        return cursor.lastrowid

def update_base_location(location_id, data, updated_by):
    """Update an existing base location"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Build full address
        full_address = f"{data['street_address']}, {data['city']}, {data['state']} {data['zip_code']}, USA"
        
        cursor.execute('''
            UPDATE base_locations 
            SET street_address = ?, city = ?, state = ?, zip_code = ?, 
                full_address = ?, notes = ?
            WHERE id = ?
        ''', (
            data['street_address'],
            data['city'],
            data['state'],
            data['zip_code'],
            full_address,
            data.get('notes', ''),
            location_id
        ))
        
        # Log the change
        cursor.execute('''
            INSERT INTO base_location_changes (location_name, change_type, changed_by, details)
            VALUES (?, 'updated', ?, ?)
        ''', (
            data['location_name'],
            updated_by,
            json.dumps(data)
        ))
        
        conn.commit()
        return True

def deactivate_base_location(location_name, deactivated_by):
    """Deactivate a base location (soft delete)"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if it's the default
        cursor.execute('SELECT is_default FROM base_locations WHERE location_name = ?', (location_name,))
        result = cursor.fetchone()
        
        if result and result[0]:
            return False, "Cannot deactivate the default base location. Set a different default first."
        
        # Deactivate
        cursor.execute('''
            UPDATE base_locations 
            SET is_active = 0 
            WHERE location_name = ? AND is_default = 0
        ''', (location_name,))
        
        # Log the change
        cursor.execute('''
            INSERT INTO base_location_changes (location_name, change_type, changed_by, details)
            VALUES (?, 'deactivated', ?, 'Location deactivated')
        ''', (location_name, deactivated_by))
        
        conn.commit()
        return True, "Location deactivated successfully"

def show_base_location_management():
    """Base Location Management Interface for Executives/Admins"""
    st.title("🏢 Base Locations")
    st.caption("Manage vendor base locations")
    
    user_role = st.session_state.get('user_role', '')
    user_name = st.session_state.get('user_name', 'Unknown')
    
    # Check permissions
    if user_role not in ['executive', 'admin']:
        st.error("⛔ Access Denied: Executive or Admin role required")
        return
    
    # Get current base locations
    base_locations_df = get_base_locations()
    current_default = get_default_base_location()
    
    # Display current status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Default Base", current_default)
    with col2:
        st.metric("Total Base Locations", len(base_locations_df))
    with col3:
        st.metric("Active Locations", len(base_locations_df[base_locations_df['is_active'] == 1]))
    
    # Tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs([
        "📍 Current",
        "➕ Add New",
        "🔄 Set Default",
        "📊 History"
    ])
    
    with tab1:
        st.markdown("### Active Base Locations")
        
        if not base_locations_df.empty:
            # Display with edit capabilities
            for idx, location in base_locations_df.iterrows():
                with st.expander(
                    f"{'🏆 DEFAULT - ' if location['is_default'] else ''}{location['location_name']}"
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Location Details**")
                        st.write(f"📍 Address: {location['street_address']}")
                        st.write(f"🏙️ City: {location['city']}, {location['state']} {location['zip_code']}")
                        st.write(f"📝 Notes: {location.get('notes', 'None')}")
                        st.write(f"👤 Created by: {location.get('created_by', 'System')}")
                    
                    with col2:
                        st.markdown("**Actions**")
                        
                        if not location['is_default']:
                            if st.button(f"Set as Default", key=f"default_{location['id']}"):
                                if set_default_base_location(location['location_name'], user_name):
                                    st.success(f"✅ {location['location_name']} is now the default base")
                                    st.rerun()
                        
                        if user_role == 'executive' and not location['is_default']:
                            if st.button(f"🗑️ Deactivate", key=f"deactivate_{location['id']}"):
                                success, message = deactivate_base_location(location['location_name'], user_name)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
        else:
            st.info("No base locations configured")
    
    with tab2:
        st.markdown("### Add New Base Location")
        
        with st.form("add_base_location_form"):
            location_name = st.text_input("Location Name *", placeholder="e.g., Fleet Dallas")
            
            col1, col2 = st.columns(2)
            with col1:
                street_address = st.text_input("Street Address *", placeholder="123 Main St")
                city = st.text_input("City *", placeholder="Dallas")
            
            with col2:
                state = st.text_input("State *", placeholder="TX", max_chars=2)
                zip_code = st.text_input("ZIP Code *", placeholder="75201")
            
            notes = st.text_area("Notes", placeholder="Any special instructions or details")
            
            make_default = st.checkbox("Set as default base location")
            
            submitted = st.form_submit_button("➕ Add Base Location", type="primary")
            
            if submitted:
                if location_name and street_address and city and state and zip_code:
                    try:
                        data = {
                            'location_name': location_name,
                            'street_address': street_address,
                            'city': city,
                            'state': state.upper(),
                            'zip_code': zip_code,
                            'notes': notes
                        }
                        
                        location_id = add_base_location(data, user_name)
                        
                        if make_default:
                            set_default_base_location(location_name, user_name)
                        
                        st.success(f"✅ Base location '{location_name}' added successfully!")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error adding base location: {e}")
                else:
                    st.error("Please fill all required fields")
    
    with tab3:
        st.markdown("### Change Default Base Location")
        st.info(f"Current default: **{current_default}**")
        
        if len(base_locations_df) > 1:
            with st.form("change_default_form"):
                new_default = st.selectbox(
                    "Select New Default Base Location",
                    base_locations_df['location_name'].tolist()
                )
                
                st.warning("⚠️ Changing the default base will affect all new trailer moves")
                
                reason = st.text_area(
                    "Reason for Change (Required)",
                    placeholder="Explain why the default base is being changed"
                )
                
                submitted = st.form_submit_button("🔄 Change Default", type="primary")
                
                if submitted:
                    if reason:
                        if set_default_base_location(new_default, f"{user_name}: {reason}"):
                            st.success(f"✅ Default base changed to {new_default}")
                            st.rerun()
                    else:
                        st.error("Please provide a reason for the change")
        else:
            st.info("Add more base locations to change the default")
    
    with tab4:
        st.markdown("### Base Location Change History")
        
        with db.get_connection() as conn:
            try:
                history_df = pd.read_sql_query('''
                    SELECT * FROM base_location_changes 
                    ORDER BY changed_at DESC 
                    LIMIT 50
                ''', conn)
                
                if not history_df.empty:
                    st.dataframe(history_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No change history available")
            except:
                st.info("No change history available yet")

def get_system_settings():
    """Get system-wide settings including base location"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Create settings table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT,
                setting_type TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT
            )
        ''')
        
        # Get all settings
        cursor.execute('SELECT setting_key, setting_value FROM system_settings')
        settings = dict(cursor.fetchall())
        
        # Ensure default base location is set
        if 'default_base_location' not in settings:
            settings['default_base_location'] = get_default_base_location()
        
        return settings

def update_system_setting(key, value, updated_by):
    """Update a system setting"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO system_settings 
            (setting_key, setting_value, updated_at, updated_by)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?)
        ''', (key, value, updated_by))
        conn.commit()
        return True