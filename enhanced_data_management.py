"""
Enhanced Data Management with Remove Functions and Sync
Ensures data persistence across updates
"""

import streamlit as st
import sqlite3
import json
import os
import pandas as pd
from datetime import datetime
import shutil

class DataManager:
    """Comprehensive data management with backup and sync"""
    
    def __init__(self):
        self.db_path = 'trailer_tracker_streamlined.db'
        self.user_file = 'user_accounts.json'
        self.backup_dir = 'data_backups'
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Create backup directory if it doesn't exist"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def backup_database(self):
        """Create a backup of the database before operations"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.backup_dir, f'db_backup_{timestamp}.db')
            shutil.copy2(self.db_path, backup_path)
            # Keep only last 10 backups
            self.cleanup_old_backups()
            return True
        except Exception as e:
            st.error(f"Backup failed: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Keep only the last 10 backups"""
        try:
            backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('db_backup_')])
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    os.remove(os.path.join(self.backup_dir, old_backup))
        except:
            pass
    
    def sync_drivers(self):
        """Sync drivers between JSON and database"""
        try:
            synced = 0
            errors = []
            
            # Load user accounts
            if not os.path.exists(self.user_file):
                return False, "No user accounts file found"
            
            with open(self.user_file, 'r') as f:
                users = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure columns exist
            self.ensure_driver_columns(conn)
            
            # Get existing drivers
            cursor.execute("SELECT driver_name FROM drivers")
            existing_drivers = [row[0] for row in cursor.fetchall()]
            
            # Sync each driver user
            for username, info in users.get('users', {}).items():
                if 'driver' in info.get('roles', []):
                    driver_name = info.get('name', username)
                    
                    if driver_name not in existing_drivers:
                        try:
                            # Add to drivers table
                            cursor.execute('''
                                INSERT INTO drivers (driver_name, phone, email, username, status, active)
                                VALUES (?, ?, ?, ?, 'available', 1)
                            ''', (driver_name, info.get('phone', ''), info.get('email', ''), username))
                            
                            # Also add to drivers_extended
                            cursor.execute('''
                                INSERT OR IGNORE INTO drivers_extended 
                                (driver_name, driver_type, phone, email, status, active)
                                VALUES (?, 'company', ?, ?, 'available', 1)
                            ''', (driver_name, info.get('phone', ''), info.get('email', '')))
                            
                            synced += 1
                        except Exception as e:
                            errors.append(f"Error syncing {driver_name}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            if errors:
                return False, f"Synced {synced} drivers with {len(errors)} errors"
            return True, f"Successfully synced {synced} new drivers"
            
        except Exception as e:
            return False, f"Sync error: {str(e)}"
    
    def ensure_driver_columns(self, conn):
        """Ensure all required columns exist in drivers table"""
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(drivers)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Required columns - SAFE VERSION with defaults
        required_columns = {
            'active': ('INTEGER', 1),
            'created_at': ('TIMESTAMP', 'CURRENT_TIMESTAMP'),
            'updated_at': ('TIMESTAMP', 'CURRENT_TIMESTAMP'),
            'username': ('TEXT', "''"),
            'home_address': ('TEXT', "''"),
            'business_address': ('TEXT', "''"),
            'is_owner': ('INTEGER', 0)
        }
        
        for col_name, (col_type, default_val) in required_columns.items():
            if col_name not in existing_columns:
                try:
                    # Build ALTER TABLE statement with proper default
                    if isinstance(default_val, str) and default_val not in ['CURRENT_TIMESTAMP']:
                        default_clause = f" DEFAULT {default_val}"
                    elif default_val == 'CURRENT_TIMESTAMP':
                        default_clause = f" DEFAULT {default_val}"
                    else:
                        default_clause = f" DEFAULT {default_val}"
                    
                    cursor.execute(f"ALTER TABLE drivers ADD COLUMN {col_name} {col_type}{default_clause}")
                    conn.commit()
                except Exception as e:
                    # Silently continue if column exists
                    if "duplicate column" not in str(e).lower():
                        pass
    
    def remove_driver(self, driver_name):
        """Remove a driver from the system"""
        try:
            self.backup_database()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if driver has active moves
            cursor.execute("""
                SELECT COUNT(*) FROM moves 
                WHERE driver_name = ? AND status IN ('assigned', 'in_progress')
            """, (driver_name,))
            
            active_moves = cursor.fetchone()[0]
            if active_moves > 0:
                conn.close()
                return False, f"Cannot remove driver with {active_moves} active moves"
            
            # Mark as inactive instead of deleting (soft delete)
            cursor.execute("""
                UPDATE drivers SET active = 0, updated_at = CURRENT_TIMESTAMP 
                WHERE driver_name = ?
            """, (driver_name,))
            
            # Also update extended table
            cursor.execute("""
                UPDATE drivers_extended SET active = 0, updated_at = CURRENT_TIMESTAMP 
                WHERE driver_name = ?
            """, (driver_name,))
            
            # Remove from user accounts
            with open(self.user_file, 'r') as f:
                users = json.load(f)
            
            # Find and remove user
            user_to_remove = None
            for username, info in users.get('users', {}).items():
                if info.get('name') == driver_name and 'driver' in info.get('roles', []):
                    user_to_remove = username
                    break
            
            if user_to_remove:
                del users['users'][user_to_remove]
                with open(self.user_file, 'w') as f:
                    json.dump(users, f, indent=2)
            
            conn.commit()
            conn.close()
            return True, f"Driver '{driver_name}' removed successfully"
            
        except Exception as e:
            return False, f"Error removing driver: {str(e)}"
    
    def remove_trailer(self, trailer_number):
        """Remove a trailer from the system"""
        try:
            self.backup_database()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if trailer is in active moves
            cursor.execute("""
                SELECT COUNT(*) FROM moves 
                WHERE (new_trailer = ? OR old_trailer = ?) 
                AND status IN ('assigned', 'in_progress')
            """, (trailer_number, trailer_number))
            
            active_moves = cursor.fetchone()[0]
            if active_moves > 0:
                conn.close()
                return False, f"Cannot remove trailer with {active_moves} active moves"
            
            # Delete trailer
            cursor.execute("DELETE FROM trailers WHERE trailer_number = ?", (trailer_number,))
            
            conn.commit()
            conn.close()
            return True, f"Trailer '{trailer_number}' removed successfully"
            
        except Exception as e:
            return False, f"Error removing trailer: {str(e)}"
    
    def remove_location(self, location_title):
        """Remove a location from the system"""
        try:
            self.backup_database()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if location is used in active moves
            cursor.execute("""
                SELECT COUNT(*) FROM moves 
                WHERE (pickup_location = ? OR delivery_location = ?) 
                AND status IN ('assigned', 'in_progress')
            """, (location_title, location_title))
            
            active_moves = cursor.fetchone()[0]
            if active_moves > 0:
                conn.close()
                return False, f"Cannot remove location with {active_moves} active moves"
            
            # Check if location has trailers
            cursor.execute("""
                SELECT COUNT(*) FROM trailers 
                WHERE current_location = ?
            """, (location_title,))
            
            trailers_at_location = cursor.fetchone()[0]
            if trailers_at_location > 0:
                conn.close()
                return False, f"Cannot remove location with {trailers_at_location} trailers present"
            
            # Delete location
            cursor.execute("DELETE FROM locations WHERE location_title = ?", (location_title,))
            
            # Also remove from mileage cache
            cursor.execute("DELETE FROM mileage_cache WHERE destination = ?", (location_title,))
            
            conn.commit()
            conn.close()
            return True, f"Location '{location_title}' removed successfully"
            
        except Exception as e:
            return False, f"Error removing location: {str(e)}"

def show_driver_management_with_sync():
    """Enhanced driver management with sync, edit and remove functions"""
    manager = DataManager()
    
    st.markdown("### 👤 Driver Management")
    
    # Action buttons
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        if st.button("🔄 Sync", use_container_width=True, key="sync_drivers_admin", help="Sync with user accounts"):
            success, message = manager.sync_drivers()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        if st.button("📊 View", use_container_width=True, key="view_drivers_admin"):
            st.session_state.show_drivers = True
            st.session_state.show_edit_driver = False
            st.session_state.show_remove_driver = False
            st.session_state.show_add_owner = False
    
    with col3:
        if st.button("➕ Add", use_container_width=True, key="add_driver_admin"):
            st.session_state.show_add_driver = True
            st.session_state.show_edit_driver = False
            st.session_state.show_remove_driver = False
            st.session_state.show_add_owner = False
    
    with col4:
        if st.button("👑 Add Me", use_container_width=True, key="add_owner_admin", help="Add yourself as owner/driver"):
            st.session_state.show_add_owner = True
            st.session_state.show_add_driver = False
            st.session_state.show_edit_driver = False
            st.session_state.show_remove_driver = False
    
    with col5:
        if st.button("✏️ Edit", use_container_width=True, key="edit_driver_admin"):
            st.session_state.show_edit_driver = True
            st.session_state.show_drivers = False
            st.session_state.show_remove_driver = False
            st.session_state.show_add_owner = False
    
    with col6:
        if st.button("🗑️ Remove", use_container_width=True, key="remove_driver_admin"):
            st.session_state.show_remove_driver = True
            st.session_state.show_drivers = False
            st.session_state.show_edit_driver = False
            st.session_state.show_add_owner = False
    
    # Show drivers list
    if st.session_state.get('show_drivers', False):
        try:
            conn = sqlite3.connect(manager.db_path)
            drivers_df = pd.read_sql_query("""
                SELECT d.driver_name, d.phone, d.email, d.status,
                       de.driver_type, de.company_name
                FROM drivers d
                LEFT JOIN drivers_extended de ON d.driver_name = de.driver_name
                WHERE d.active = 1 OR d.active IS NULL
                ORDER BY d.driver_name
            """, conn)
            conn.close()
            
            if not drivers_df.empty:
                st.dataframe(drivers_df, use_container_width=True, hide_index=True)
            else:
                st.info("No drivers found. Click 'Sync Drivers' to import from user accounts.")
        except Exception as e:
            st.error(f"Error loading drivers: {e}")
    
    # Remove driver interface
    if st.session_state.get('show_remove_driver', False):
        with st.form("remove_driver_form"):
            st.markdown("#### Remove Driver")
            
            try:
                conn = sqlite3.connect(manager.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT driver_name FROM drivers 
                    WHERE active = 1 OR active IS NULL 
                    ORDER BY driver_name
                """)
                drivers = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                if drivers:
                    selected_driver = st.selectbox("Select Driver to Remove", drivers)
                    st.warning("⚠️ This will deactivate the driver and remove their login access")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Remove", type="primary"):
                            success, message = manager.remove_driver(selected_driver)
                            if success:
                                st.success(message)
                                st.session_state.show_remove_driver = False
                                st.rerun()
                            else:
                                st.error(message)
                    with col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state.show_remove_driver = False
                            st.rerun()
                else:
                    st.info("No drivers to remove")
                    if st.form_submit_button("Close"):
                        st.session_state.show_remove_driver = False
                        st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Add owner/self interface
    if st.session_state.get('show_add_owner', False):
        show_add_owner_interface(manager)
    
    # Edit driver interface
    if st.session_state.get('show_edit_driver', False):
        show_edit_driver_interface(manager)

def show_add_owner_interface(manager):
    """Interface for adding owner/self as a driver"""
    st.markdown("#### 👑 Add Yourself as Owner/Driver")
    st.info("This will add you to the driver list so you can be assigned to moves")
    
    with st.form("add_owner_driver_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Personal Information**")
            owner_name = st.text_input("Your Name*", value=st.session_state.get('user_name', ''))
            owner_phone = st.text_input("Phone Number*", placeholder="(555) 123-4567")
            owner_email = st.text_input("Email*", value=st.session_state.get('company_email', ''))
            owner_cdl = st.text_input("CDL Number", placeholder="CDL123456789")
            
            driver_type = st.selectbox(
                "Driver Type",
                ["company", "contractor"],
                index=0,
                help="Are you driving as a company driver or owner-operator?"
            )
        
        with col2:
            if driver_type == "contractor":
                st.markdown("**Business Information**")
                owner_company = st.text_input("Company Name", value="Smith & Williams Trucking")
                owner_mc = st.text_input("MC Number", placeholder="MC-123456")
                owner_dot = st.text_input("DOT Number", placeholder="1234567")
                owner_insurance = st.text_input("Insurance Company")
            else:
                st.markdown("**Company Driver**")
                st.info("No additional business information needed")
                owner_company = None
                owner_mc = None
                owner_dot = None
                owner_insurance = None
        
        st.divider()
        st.markdown("**Address Information**")
        
        col3, col4 = st.columns(2)
        with col3:
            if driver_type == "company":
                owner_home_address = st.text_area(
                    "Home Address",
                    placeholder="123 Main St\nCity, State ZIP",
                    help="Your personal address"
                )
                owner_business_address = None
            else:
                owner_home_address = None
        
        with col4:
            if driver_type == "contractor":
                owner_business_address = st.text_area(
                    "Business Address", 
                    placeholder="456 Business Ave\nCity, State ZIP",
                    help="Your business/company address"
                )
            else:
                owner_business_address = None
        
        col_submit, col_cancel = st.columns(2)
        with col_submit:
            if st.form_submit_button("➕ Add Me as Driver", type="primary"):
                if owner_name and owner_phone and owner_email:
                    try:
                        conn = sqlite3.connect(manager.db_path)
                        cursor = conn.cursor()
                        
                        # Ensure columns exist
                        manager.ensure_driver_columns(conn)
                        
                        # Check if already exists
                        cursor.execute("SELECT driver_name FROM drivers WHERE driver_name = ?", (owner_name,))
                        if cursor.fetchone():
                            st.error(f"Driver '{owner_name}' already exists. Use Edit to update.")
                        else:
                            # Add to drivers table
                            cursor.execute("""
                                INSERT INTO drivers (driver_name, phone, email, status, active, 
                                                   home_address, business_address, is_owner, username)
                                VALUES (?, ?, ?, 'available', 1, ?, ?, 1, ?)
                            """, (owner_name, owner_phone, owner_email, owner_home_address, 
                                  owner_business_address, st.session_state.get('username', '')))
                            
                            # Add to drivers_extended if contractor
                            if driver_type == "contractor":
                                cursor.execute("""
                                    INSERT OR IGNORE INTO drivers_extended 
                                    (driver_name, driver_type, phone, email, status, active,
                                     company_name, mc_number, dot_number, cdl_number, insurance_company)
                                    VALUES (?, 'contractor', ?, ?, 'available', 1, ?, ?, ?, ?, ?)
                                """, (owner_name, owner_phone, owner_email, owner_company, 
                                      owner_mc, owner_dot, owner_cdl, owner_insurance))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"✅ Successfully added '{owner_name}' as owner/driver!")
                            st.session_state.show_add_owner = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error adding owner: {str(e)}")
                else:
                    st.error("Please fill all required fields (*)")
        
        with col_cancel:
            if st.form_submit_button("Cancel"):
                st.session_state.show_add_owner = False
                st.rerun()

def show_edit_driver_interface(manager):
    """Interface for editing driver information"""
    st.markdown("#### ✏️ Edit Driver Information")
    
    try:
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        # Ensure new columns exist
        manager.ensure_driver_columns(conn)
        
        # Get all drivers with their full info including addresses
        try:
            cursor.execute("""
                SELECT d.driver_name, d.phone, d.email, d.status,
                       de.driver_type, de.company_name, de.mc_number, 
                       de.dot_number, de.cdl_number, de.insurance_company,
                       d.home_address, d.business_address, d.is_owner
                FROM drivers d
                LEFT JOIN drivers_extended de ON d.driver_name = de.driver_name
                WHERE d.active = 1 OR d.active IS NULL
                ORDER BY d.driver_name
            """)
        except:
            cursor.execute("""
                SELECT driver_name, phone, email, status, 
                       NULL, NULL, NULL, NULL, NULL, NULL,
                       home_address, business_address, is_owner
                FROM drivers
                ORDER BY driver_name
            """)
        
        drivers = cursor.fetchall()
        conn.close()
        
        if drivers:
            # Select driver to edit
            driver_names = [d[0] for d in drivers]
            selected_index = st.selectbox(
                "Select Driver to Edit",
                range(len(driver_names)),
                format_func=lambda x: driver_names[x],
                key="edit_driver_select"
            )
            
            if selected_index is not None:
                driver_data = drivers[selected_index]
                driver_name = driver_data[0]
                
                with st.form("edit_driver_form"):
                    st.markdown(f"**Editing: {driver_name}**")
                    
                    # Check if owner
                    is_owner = driver_data[12] if len(driver_data) > 12 else False
                    if is_owner:
                        st.info("👑 Owner/Self Driver")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Contact Information**")
                        new_phone = st.text_input("Phone", value=driver_data[1] or "")
                        new_email = st.text_input("Email", value=driver_data[2] or "")
                        new_status = st.selectbox(
                            "Status",
                            ["available", "on_trip", "unavailable"],
                            index=["available", "on_trip", "unavailable"].index(driver_data[3] or "available")
                        )
                        
                        new_cdl = st.text_input("CDL Number", value=driver_data[8] if len(driver_data) > 8 else "")
                        
                        # Mark as owner option
                        new_is_owner = st.checkbox("This is me (Owner/Self)", value=bool(is_owner))
                    
                    with col2:
                        driver_type = driver_data[4] if len(driver_data) > 4 else "company"
                        
                        if driver_type == "contractor":
                            st.markdown("**Contractor Information**")
                            new_company = st.text_input("Company Name", value=driver_data[5] if len(driver_data) > 5 else "")
                            new_mc = st.text_input("MC Number", value=driver_data[6] if len(driver_data) > 6 else "")
                            new_dot = st.text_input("DOT Number", value=driver_data[7] if len(driver_data) > 7 else "")
                            new_insurance = st.text_input("Insurance Company", value=driver_data[9] if len(driver_data) > 9 else "")
                        else:
                            st.markdown("**Company Driver Information**")
                            new_company = None
                            new_mc = None
                            new_dot = None
                            new_insurance = None
                    
                    st.divider()
                    
                    # Address section
                    st.markdown("**Address Information**")
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        if driver_type == "company":
                            new_home_address = st.text_area(
                                "Home Address",
                                value=driver_data[10] if len(driver_data) > 10 else "",
                                help="Driver's home address"
                            )
                            new_business_address = None
                        else:
                            st.info("Contractor - Business address required")
                            new_home_address = None
                    
                    with col4:
                        if driver_type == "contractor":
                            new_business_address = st.text_area(
                                "Business Address",
                                value=driver_data[11] if len(driver_data) > 11 else "",
                                help="Contractor's business address"
                            )
                        else:
                            new_business_address = None
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes", type="primary"):
                            success = update_driver_info(
                                manager, driver_name, new_phone, new_email, 
                                new_status, new_cdl, new_company, new_mc, 
                                new_dot, new_insurance, new_home_address,
                                new_business_address, new_is_owner
                            )
                            if success:
                                st.success(f"Driver '{driver_name}' updated successfully!")
                                st.session_state.show_edit_driver = False
                                st.rerun()
                            else:
                                st.error("Failed to update driver")
                    
                    with col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state.show_edit_driver = False
                            st.rerun()
        else:
            st.info("No drivers found to edit")
    except Exception as e:
        st.error(f"Error loading drivers: {e}")

def update_driver_info(manager, driver_name, phone, email, status, cdl, company, mc, dot, insurance, 
                      home_address=None, business_address=None, is_owner=False):
    """Update driver information in database"""
    try:
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        # Ensure columns exist
        manager.ensure_driver_columns(conn)
        
        # Update main drivers table with addresses and owner flag
        cursor.execute("""
            UPDATE drivers 
            SET phone = ?, email = ?, status = ?, home_address = ?, 
                business_address = ?, is_owner = ?, updated_at = CURRENT_TIMESTAMP
            WHERE driver_name = ?
        """, (phone, email, status, home_address, business_address, 
              1 if is_owner else 0, driver_name))
        
        # Update extended table if exists
        cursor.execute("""
            UPDATE drivers_extended
            SET phone = ?, email = ?, status = ?, cdl_number = ?,
                company_name = ?, mc_number = ?, dot_number = ?, 
                insurance_company = ?, updated_at = CURRENT_TIMESTAMP
            WHERE driver_name = ?
        """, (phone, email, status, cdl, company, mc, dot, insurance, driver_name))
        
        # Also update user accounts
        with open(manager.user_file, 'r') as f:
            users = json.load(f)
        
        # Find and update user
        for username, info in users.get('users', {}).items():
            if info.get('name') == driver_name:
                info['phone'] = phone
                info['email'] = email
                break
        
        with open(manager.user_file, 'w') as f:
            json.dump(users, f, indent=2)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Update error: {e}")
        return False

def show_trailer_management_with_remove():
    """Enhanced trailer management with remove function"""
    manager = DataManager()
    
    st.markdown("### 🚛 Trailer Management")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View All", use_container_width=True, key="view_trailers"):
            st.session_state.show_trailers = True
    
    with col2:
        if st.button("➕ Add Trailer", use_container_width=True, key="add_trailer"):
            st.session_state.show_add_trailer = True
    
    with col3:
        if st.button("🗑️ Remove Trailer", use_container_width=True, key="remove_trailer"):
            st.session_state.show_remove_trailer = True
    
    # Remove trailer interface
    if st.session_state.get('show_remove_trailer', False):
        with st.form("remove_trailer_form"):
            st.markdown("#### Remove Trailer")
            
            try:
                conn = sqlite3.connect(manager.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT trailer_number, trailer_type, current_location FROM trailers ORDER BY trailer_number")
                trailers = cursor.fetchall()
                conn.close()
                
                if trailers:
                    trailer_options = [f"{t[0]} ({t[1]}) at {t[2]}" for t in trailers]
                    selected_index = st.selectbox("Select Trailer to Remove", range(len(trailer_options)), 
                                                 format_func=lambda x: trailer_options[x])
                    selected_trailer = trailers[selected_index][0]
                    
                    st.warning("⚠️ This will permanently remove the trailer from the system")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Remove", type="primary"):
                            success, message = manager.remove_trailer(selected_trailer)
                            if success:
                                st.success(message)
                                st.session_state.show_remove_trailer = False
                                st.rerun()
                            else:
                                st.error(message)
                    with col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state.show_remove_trailer = False
                            st.rerun()
                else:
                    st.info("No trailers to remove")
                    if st.form_submit_button("Close"):
                        st.session_state.show_remove_trailer = False
                        st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

def show_location_management_with_remove():
    """Enhanced location management with remove function"""
    manager = DataManager()
    
    st.markdown("### 📍 Location Management")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View All", use_container_width=True, key="view_locations"):
            st.session_state.show_locations = True
    
    with col2:
        if st.button("➕ Add Location", use_container_width=True, key="add_location"):
            st.session_state.show_add_location = True
    
    with col3:
        if st.button("🗑️ Remove Location", use_container_width=True, key="remove_location"):
            st.session_state.show_remove_location = True
    
    # Remove location interface
    if st.session_state.get('show_remove_location', False):
        with st.form("remove_location_form"):
            st.markdown("#### Remove Location")
            
            try:
                conn = sqlite3.connect(manager.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT location_title, location_address FROM locations ORDER BY location_title")
                locations = cursor.fetchall()
                conn.close()
                
                if locations:
                    location_options = [f"{l[0]} - {l[1]}" for l in locations]
                    selected_index = st.selectbox("Select Location to Remove", range(len(location_options)), 
                                                 format_func=lambda x: location_options[x])
                    selected_location = locations[selected_index][0]
                    
                    st.warning("⚠️ This will permanently remove the location from the system")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Remove", type="primary"):
                            success, message = manager.remove_location(selected_location)
                            if success:
                                st.success(message)
                                st.session_state.show_remove_location = False
                                st.rerun()
                            else:
                                st.error(message)
                    with col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state.show_remove_location = False
                            st.rerun()
                else:
                    st.info("No locations to remove")
                    if st.form_submit_button("Close"):
                        st.session_state.show_remove_location = False
                        st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# Export for use in main app
__all__ = ['DataManager', 'show_driver_management_with_sync', 
           'show_trailer_management_with_remove', 'show_location_management_with_remove']