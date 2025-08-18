"""
Enhanced Driver Management System
Fixed: Radio button responsiveness, form submission, data persistence
"""

import streamlit as st
import sqlite3
import json
import os
from datetime import datetime, date
import time
import hashlib
import pandas as pd
import vernon_sidebar

class EnhancedDriverManager:
    """Driver management with proper state handling and validation"""
    
    def __init__(self):
        self.db_path = 'trailer_tracker_streamlined.db'
        self.user_file = 'user_accounts.json'
        self.init_session_state()
        self.ensure_database_structure()
    
    def init_session_state(self):
        """Initialize session state for form handling"""
        if 'driver_form_state' not in st.session_state:
            st.session_state.driver_form_state = {
                'driver_type': 'company',
                'form_submitted': False,
                'last_submission': None,
                'submission_count': 0,
                'current_driver': None
            }
        
        # Prevent double-submission
        if 'form_lock' not in st.session_state:
            st.session_state.form_lock = False
            
    def ensure_database_structure(self):
        """Ensure all driver tables exist with proper structure"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Main drivers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    email TEXT,
                    status TEXT DEFAULT 'available',
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Extended driver information
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS drivers_extended (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT UNIQUE NOT NULL,
                    driver_type TEXT DEFAULT 'company' CHECK(driver_type IN ('company', 'contractor')),
                    phone TEXT,
                    email TEXT,
                    cdl_number TEXT,
                    cdl_expiry DATE,
                    company_name TEXT,
                    mc_number TEXT,
                    dot_number TEXT,
                    insurance_company TEXT,
                    insurance_policy TEXT,
                    insurance_expiry DATE,
                    insurance_doc BLOB,
                    insurance_doc_name TEXT,
                    status TEXT DEFAULT 'available',
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_drivers_name ON drivers(driver_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_drivers_status ON drivers(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_drivers_ext_type ON drivers_extended(driver_type)')
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Database initialization error: {e}")
            return False
    
    def load_users(self):
        """Load user accounts from JSON"""
        if os.path.exists(self.user_file):
            with open(self.user_file, 'r') as f:
                return json.load(f)
        return {'users': {}}
    
    def save_users(self, user_data):
        """Save user accounts to JSON"""
        try:
            with open(self.user_file, 'w') as f:
                json.dump(user_data, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving users: {e}")
            return False
    
    def create_driver(self, driver_data, user_credentials):
        """Create driver with proper transaction handling"""
        if st.session_state.form_lock:
            st.warning("⏳ Processing previous submission, please wait...")
            return False
            
        st.session_state.form_lock = True
        success = False
        
        try:
            # Step 1: Create user account
            user_data = self.load_users()
            
            if user_credentials['user'] in user_data['users']:
                st.error(f"Username '{user_credentials['user']}' already exists!")
                return False
            
            # Add user with driver role
            user_data['users'][user_credentials['user']] = {
                'password': user_credentials['password'],
                'roles': ['driver'],
                'driver_name': driver_data['driver_name'],
                'email': driver_data.get('email', ''),
                'phone': driver_data.get('phone', ''),
                'is_owner': False,
                'active': True,
                'created_at': datetime.now().isoformat()
            }
            
            if not self.save_users(user_data):
                st.error("Failed to save user account")
                return False
            
            # Step 2: Add to database with transaction
            conn = sqlite3.connect(self.db_path)
            conn.execute('BEGIN TRANSACTION')
            cursor = conn.cursor()
            
            try:
                # Insert into main drivers table (handle both column variations)
                try:
                    cursor.execute('''
                        INSERT INTO drivers (driver_name, phone, email, home_address, company_address, status, active, created_at)
                        VALUES (?, ?, ?, ?, ?, 'available', 1, CURRENT_TIMESTAMP)
                    ''', (driver_data['driver_name'], 
                          driver_data.get('phone', ''), 
                          driver_data.get('email', ''),
                          driver_data.get('home_address', ''),
                          driver_data.get('company_address', '')))
                except sqlite3.OperationalError:
                    # Fallback if columns don't exist
                    cursor.execute('''
                        INSERT INTO drivers (driver_name, phone, email, status)
                        VALUES (?, ?, ?, 'available')
                    ''', (driver_data['driver_name'], 
                          driver_data.get('phone', ''), 
                          driver_data.get('email', '')))
                
                # Handle insurance document if provided
                insurance_doc_data = None
                insurance_doc_name = None
                if driver_data.get('insurance_doc'):
                    insurance_doc_data = driver_data['insurance_doc'].read()
                    insurance_doc_name = driver_data['insurance_doc'].name
                
                # Insert into extended table
                cursor.execute('''
                    INSERT INTO drivers_extended 
                    (driver_name, driver_type, phone, email, home_address, company_address,
                     cdl_number, cdl_expiry, company_name, mc_number, dot_number, 
                     insurance_company, insurance_policy, insurance_expiry,
                     insurance_doc, insurance_doc_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    driver_data['driver_name'],
                    driver_data['driver_type'],
                    driver_data.get('phone', ''),
                    driver_data.get('email', ''),
                    driver_data.get('home_address', ''),
                    driver_data.get('company_address', ''),
                    driver_data.get('cdl_number', ''),
                    driver_data.get('cdl_expiry'),
                    driver_data.get('company_name', ''),
                    driver_data.get('mc_number', ''),
                    driver_data.get('dot_number', ''),
                    driver_data.get('insurance_company', ''),
                    driver_data.get('insurance_policy', ''),
                    driver_data.get('insurance_expiry'),
                    insurance_doc_data,
                    insurance_doc_name
                ))
                
                conn.commit()
                success = True
                
                # Update session state
                st.session_state.driver_form_state['last_submission'] = datetime.now()
                st.session_state.driver_form_state['submission_count'] += 1
                
            except sqlite3.IntegrityError as e:
                conn.rollback()
                if 'UNIQUE constraint failed' in str(e):
                    st.error(f"Driver '{driver_data['driver_name']}' already exists!")
                else:
                    st.error(f"Database error: {e}")
            except Exception as e:
                conn.rollback()
                st.error(f"Error creating driver: {e}")
            finally:
                conn.close()
                
        except Exception as e:
            st.error(f"System error: {e}")
        finally:
            # Release lock after short delay
            time.sleep(0.5)
            st.session_state.form_lock = False
            
        return success
    
    def update_driver(self, driver_name, updates):
        """Update driver information"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('BEGIN TRANSACTION')
            cursor = conn.cursor()
            
            # Update main table
            if any(k in updates for k in ['phone', 'email', 'status']):
                main_updates = []
                main_values = []
                
                for field in ['phone', 'email', 'status']:
                    if field in updates:
                        main_updates.append(f"{field} = ?")
                        main_values.append(updates[field])
                
                if main_updates:
                    main_values.append(datetime.now())
                    main_values.append(driver_name)
                    cursor.execute(f'''
                        UPDATE drivers 
                        SET {', '.join(main_updates)}, updated_at = ?
                        WHERE driver_name = ?
                    ''', main_values)
            
            # Update extended table
            ext_updates = []
            ext_values = []
            
            for field in ['driver_type', 'cdl_number', 'cdl_expiry', 'company_name',
                         'mc_number', 'dot_number', 'insurance_company', 
                         'insurance_policy', 'insurance_expiry']:
                if field in updates:
                    ext_updates.append(f"{field} = ?")
                    ext_values.append(updates[field])
            
            if ext_updates:
                ext_values.append(datetime.now())
                ext_values.append(driver_name)
                cursor.execute(f'''
                    UPDATE drivers_extended 
                    SET {', '.join(ext_updates)}, updated_at = ?
                    WHERE driver_name = ?
                ''', ext_values)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error updating driver: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def get_driver_info(self, driver_name):
        """Get complete driver information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT d.*, de.driver_type, de.cdl_number, de.cdl_expiry,
                       de.company_name, de.mc_number, de.dot_number,
                       de.insurance_company, de.insurance_policy, de.insurance_expiry
                FROM drivers d
                LEFT JOIN drivers_extended de ON d.driver_name = de.driver_name
                WHERE d.driver_name = ?
            ''', (driver_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None
            
        except Exception as e:
            st.error(f"Error loading driver: {e}")
            return None
    
    def get_all_drivers(self):
        """Get all drivers with their information"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # First try with active column
            try:
                query = '''
                    SELECT d.*, de.driver_type, de.company_name, de.mc_number,
                           de.insurance_company, de.insurance_expiry
                    FROM drivers d
                    LEFT JOIN drivers_extended de ON d.driver_name = de.driver_name
                    WHERE d.active = 1
                    ORDER BY d.driver_name
                '''
                df = pd.read_sql_query(query, conn)
            except sqlite3.OperationalError:
                # Fallback without active column
                query = '''
                    SELECT d.*, de.driver_type, de.company_name, de.mc_number,
                           de.insurance_company, de.insurance_expiry
                    FROM drivers d
                    LEFT JOIN drivers_extended de ON d.driver_name = de.driver_name
                    ORDER BY d.driver_name
                '''
                df = pd.read_sql_query(query, conn)
            
            conn.close()
            return df
        except Exception as e:
            # Don't show alarming error for non-critical issues
            if "no such column" in str(e).lower() or "no such table" in str(e).lower():
                # Return empty dataframe silently - not a real error
                return pd.DataFrame()
            else:
                # Only show error for real issues
                st.warning(f"Could not load drivers: {e}")
                return pd.DataFrame()
    
    def show_driver_creation_form(self):
        """Display enhanced driver creation form"""
        st.markdown("### 🚛 Create New Driver")
        
        # Initialize form state
        if 'driver_type_selected' not in st.session_state:
            st.session_state.driver_type_selected = 'company'
        
        # Driver type selection OUTSIDE form for proper reactivity
        driver_type = st.radio(
            "**Select Driver Type**",
            ["Company Driver", "Contractor/Owner-Operator"],
            key="driver_type_radio",
            horizontal=True,
            help="Select type BEFORE filling form"
        )
        
        # Update session state
        st.session_state.driver_type_selected = 'contractor' if driver_type == "Contractor/Owner-Operator" else 'company'
        
        st.divider()
        
        # Main form
        with st.form("create_driver_enhanced", clear_on_submit=True):
            st.markdown("#### 👤 Account Information")
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Username*", help="Login username")
                password = st.text_input("Password*", type="password", value="driver123")
                driver_name = st.text_input("Full Name*")
            
            with col2:
                phone = st.text_input("Phone Number")
                email = st.text_input("Email Address")
                
            st.divider()
            st.markdown("#### 📍 Address Information")
            
            if st.session_state.driver_type_selected == 'contractor':
                company_address = st.text_area("Company Address*", 
                    placeholder="Enter full company address including street, city, state, ZIP",
                    help="Business address for 1099 and correspondence")
                home_address = ""  # Empty for contractors
            else:
                home_address = st.text_area("Home Address", 
                    placeholder="Enter home address including street, city, state, ZIP",
                    help="Driver's home address")
                company_address = ""  # Empty for company drivers
            
            st.divider()
            st.markdown("#### 📋 Driver Details")
            
            col3, col4 = st.columns(2)
            
            with col3:
                cdl_number = st.text_input("CDL Number")
                cdl_expiry = st.date_input("CDL Expiry Date", value=None)
            
            with col4:
                if st.session_state.driver_type_selected == 'contractor':
                    st.markdown("**🏢 Contractor Information**")
                    company_name = st.text_input("Company Name*")
                    mc_number = st.text_input("MC Number*")
                    dot_number = st.text_input("DOT Number*")
                    insurance_company = st.text_input("Insurance Company*")
                    insurance_policy = st.text_input("Policy Number*")
                    insurance_expiry = st.date_input("Insurance Expiry*", value=None)
                    
                    # Insurance document upload
                    st.markdown("**📄 Insurance Documentation**")
                    insurance_doc = st.file_uploader(
                        "Upload Insurance Certificate",
                        type=['pdf', 'jpg', 'jpeg', 'png'],
                        help="Upload COI or insurance documentation",
                        key="insurance_doc_upload"
                    )
                    
                    # W9 document upload
                    st.markdown("**📋 W9 Form (Tax Documentation)**")
                    w9_doc = st.file_uploader(
                        "Upload W9 Form",
                        type=['pdf', 'jpg', 'jpeg', 'png'],
                        help="W9 is required for contractor tax compliance",
                        key="w9_doc_upload"
                    )
                    if not w9_doc:
                        st.warning("⚠️ W9 can be uploaded later but is required for payment processing")
                else:
                    st.success("✅ Company Driver - No additional info needed")
                    company_name = None
                    mc_number = None
                    dot_number = None
                    insurance_company = None
                    insurance_policy = None
                    insurance_expiry = None
                    insurance_doc = None
            
            # Submit button with debounce
            submit_col1, submit_col2, submit_col3 = st.columns([2, 1, 2])
            with submit_col2:
                submitted = st.form_submit_button(
                    "Create Driver",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted:
                # Validate required fields
                errors = []
                
                if not username:
                    errors.append("Username is required")
                if not password:
                    errors.append("Password is required")
                if not driver_name:
                    errors.append("Driver name is required")
                
                if st.session_state.driver_type_selected == 'contractor':
                    if not company_name:
                        errors.append("Company name is required for contractors")
                    if not company_address:
                        errors.append("Company address is required for contractors")
                    if not mc_number:
                        errors.append("MC number is required for contractors")
                    if not dot_number:
                        errors.append("DOT number is required for contractors")
                    if not insurance_company:
                        errors.append("Insurance company is required for contractors")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Prepare driver data
                    driver_data = {
                        'driver_name': driver_name,
                        'driver_type': st.session_state.driver_type_selected,
                        'phone': phone,
                        'email': email,
                        'home_address': home_address if 'home_address' in locals() else '',
                        'company_address': company_address if 'company_address' in locals() else '',
                        'cdl_number': cdl_number,
                        'cdl_expiry': cdl_expiry,
                        'company_name': company_name,
                        'mc_number': mc_number,
                        'dot_number': dot_number,
                        'insurance_company': insurance_company,
                        'insurance_policy': insurance_policy,
                        'insurance_expiry': insurance_expiry,
                        'insurance_doc': insurance_doc if st.session_state.driver_type_selected == 'contractor' else None
                    }
                    
                    user_credentials = {
                        'user': username,
                        'password': password
                    }
                    
                    # Create driver
                    if self.create_driver(driver_data, user_credentials):
                        # Handle W9 upload if provided
                        if st.session_state.driver_type_selected == 'contractor' and 'w9_doc' in locals() and w9_doc:
                            import w9_manager
                            w9_mgr = w9_manager.W9Manager()
                            success, result = w9_mgr.upload_w9(
                                driver_name,
                                w9_doc,
                                tax_year=datetime.now().year,
                                notes="Uploaded during driver creation"
                            )
                            if success:
                                st.success(f"✅ W9 document uploaded: {result}")
                        
                        st.success(f"""
                        ✅ **Driver Created Successfully!**
                        
                        **Name:** {driver_name}
                        **Type:** {driver_type}
                        **Username:** {username}
                        
                        Driver can now login to the system.
                        """)
                        time.sleep(2)
                        st.rerun()
    
    def show_driver_update_form(self):
        """Display driver update form"""
        st.markdown("### ✏️ Update Driver Information")
        
        # Get all drivers
        drivers_df = self.get_all_drivers()
        
        if drivers_df.empty:
            st.warning("No drivers found. Please create a driver first.")
            return
        
        # Driver selection
        driver_names = drivers_df['driver_name'].tolist()
        selected_driver = st.selectbox(
            "Select Driver to Update",
            driver_names,
            key="update_driver_select"
        )
        
        if selected_driver:
            driver_info = self.get_driver_info(selected_driver)
            
            if driver_info:
                # Show current info
                with st.expander("Current Driver Information", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Name:** {driver_info['driver_name']}")
                        st.write(f"**Type:** {'Contractor' if driver_info.get('driver_type') == 'contractor' else 'Company'}")
                        st.write(f"**Status:** {driver_info.get('status', 'Unknown')}")
                    
                    with col2:
                        st.write(f"**Phone:** {driver_info.get('phone', 'Not set')}")
                        st.write(f"**Email:** {driver_info.get('email', 'Not set')}")
                        st.write(f"**CDL:** {driver_info.get('cdl_number', 'Not set')}")
                
                # Update form
                with st.form("update_driver_form"):
                    st.markdown("#### Update Information")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_phone = st.text_input("Phone", value=driver_info.get('phone', ''))
                        new_email = st.text_input("Email", value=driver_info.get('email', ''))
                        new_cdl = st.text_input("CDL Number", value=driver_info.get('cdl_number', ''))
                        
                        cdl_exp = driver_info.get('cdl_expiry')
                        if cdl_exp and isinstance(cdl_exp, str):
                            try:
                                cdl_exp = datetime.strptime(cdl_exp, '%Y-%m-%d').date()
                            except:
                                cdl_exp = None
                        new_cdl_expiry = st.date_input("CDL Expiry", value=cdl_exp)
                    
                    with col2:
                        new_status = st.selectbox(
                            "Status",
                            ["available", "on_trip", "unavailable"],
                            index=["available", "on_trip", "unavailable"].index(driver_info.get('status', 'available'))
                        )
                        
                        if driver_info.get('driver_type') == 'contractor':
                            st.markdown("**Contractor Information**")
                            new_company = st.text_input("Company", value=driver_info.get('company_name', ''))
                            new_mc = st.text_input("MC Number", value=driver_info.get('mc_number', ''))
                            new_dot = st.text_input("DOT Number", value=driver_info.get('dot_number', ''))
                            new_insurance = st.text_input("Insurance Company", value=driver_info.get('insurance_company', ''))
                        else:
                            new_company = None
                            new_mc = None
                            new_dot = None
                            new_insurance = None
                    
                    if st.form_submit_button("Update Driver", type="primary"):
                        updates = {
                            'phone': new_phone,
                            'email': new_email,
                            'cdl_number': new_cdl,
                            'cdl_expiry': new_cdl_expiry,
                            'status': new_status
                        }
                        
                        if driver_info.get('driver_type') == 'contractor':
                            updates.update({
                                'company_name': new_company,
                                'mc_number': new_mc,
                                'dot_number': new_dot,
                                'insurance_company': new_insurance
                            })
                        
                        if self.update_driver(selected_driver, updates):
                            st.success(f"✅ Driver '{selected_driver}' updated successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to update driver")
    
    def show_driver_list(self):
        """Display all drivers in an organized view"""
        st.markdown("### 📋 All Drivers")
        
        try:
            drivers_df = self.get_all_drivers()
        except Exception as e:
            st.error(f"Error loading drivers: {e}")
            # Fallback to basic query
            try:
                conn = sqlite3.connect(self.db_path)
                drivers_df = pd.read_sql_query("SELECT * FROM drivers ORDER BY driver_name", conn)
                conn.close()
            except:
                drivers_df = pd.DataFrame()
        
        if drivers_df.empty:
            st.info("No drivers registered yet.")
            # Run Vernon sync check
            st.info("Vernon is checking for driver sync issues...")
            if st.button("Run Driver Sync"):
                vernon_sidebar.VernonSidebar().fix_driver_sync()
                st.rerun()
            return
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Drivers", len(drivers_df))
        
        with col2:
            available = len(drivers_df[drivers_df['status'] == 'available'])
            st.metric("Available", available)
        
        with col3:
            if 'driver_type' in drivers_df.columns:
                contractors = len(drivers_df[drivers_df['driver_type'] == 'contractor'])
            else:
                contractors = 0
            st.metric("Contractors", contractors)
        
        with col4:
            if 'driver_type' in drivers_df.columns:
                company = len(drivers_df[drivers_df['driver_type'] == 'company'])
            else:
                company = len(drivers_df)
            st.metric("Company Drivers", company)
        
        st.divider()
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            type_filter = st.selectbox(
                "Filter by Type",
                ["All", "Company", "Contractor"],
                key="driver_type_filter"
            )
        
        with col2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Available", "On Trip", "Unavailable"],
                key="driver_status_filter"
            )
        
        with col3:
            search = st.text_input("Search Driver", key="driver_search")
        
        # Apply filters
        filtered_df = drivers_df.copy()
        
        if type_filter != "All" and 'driver_type' in filtered_df.columns:
            filter_val = 'contractor' if type_filter == "Contractor" else 'company'
            filtered_df = filtered_df[filtered_df['driver_type'] == filter_val]
        
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['status'] == status_filter.lower()]
        
        if search:
            filtered_df = filtered_df[
                filtered_df['driver_name'].str.contains(search, case=False, na=False)
            ]
        
        # Display drivers
        for _, driver in filtered_df.iterrows():
            with st.expander(f"🚛 {driver['driver_name']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    driver_type = "Contractor" if driver.get('driver_type') == 'contractor' else "Company"
                    st.write(f"**Type:** {driver_type}")
                    st.write(f"**Phone:** {driver.get('phone', 'Not set')}")
                    st.write(f"**Email:** {driver.get('email', 'Not set')}")
                
                with col2:
                    status_color = {
                        'available': '🟢',
                        'on_trip': '🟡',
                        'unavailable': '🔴'
                    }
                    status_icon = status_color.get(driver.get('status', 'available'), '⚫')
                    st.write(f"**Status:** {status_icon} {driver.get('status', 'Unknown').title()}")
                    
                    if driver.get('driver_type') == 'contractor':
                        st.write(f"**Company:** {driver.get('company_name', 'Not set')}")
                        st.write(f"**MC #:** {driver.get('mc_number', 'Not set')}")
                
                with col3:
                    if driver.get('driver_type') == 'contractor' and driver.get('insurance_expiry'):
                        try:
                            exp_date = pd.to_datetime(driver['insurance_expiry']).date()
                            days_until = (exp_date - date.today()).days
                            
                            if days_until < 0:
                                st.error(f"⚠️ Insurance EXPIRED {abs(days_until)} days ago")
                            elif days_until < 30:
                                st.warning(f"⚠️ Insurance expires in {days_until} days")
                            else:
                                st.success(f"✅ Insurance valid ({days_until} days)")
                        except:
                            pass

def show_enhanced_driver_management():
    """Main entry point for enhanced driver management"""
    manager = EnhancedDriverManager()
    
    st.title("🚛 Enhanced Driver Management")
    
    tabs = st.tabs(["➕ Create Driver", "✏️ Update Driver", "📋 View All Drivers", "📄 W9 Documents"])
    
    with tabs[0]:
        manager.show_driver_creation_form()
    
    with tabs[1]:
        manager.show_driver_update_form()
    
    with tabs[2]:
        manager.show_driver_list()
    
    with tabs[3]:
        # Import W9 manager
        import w9_manager
        
        # Check if user is admin
        if st.session_state.get('user_role') == 'business_administrator':
            # Show full W9 management for admins
            w9_manager.show_w9_management_interface()
        else:
            # Show upload interface only for non-admins
            st.markdown("### 📄 W9 Document Upload")
            st.info("W9 forms are required for all contract drivers for tax compliance.")
            w9_manager.show_w9_upload_interface()

# Export for use in main app
__all__ = ['EnhancedDriverManager', 'show_enhanced_driver_management']