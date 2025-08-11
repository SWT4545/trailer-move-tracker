"""
Initial Setup Wizard for Smith & Williams Trucking System
Run this ONCE to set up your admin account and initial users
"""

import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime

def hash_password(password):
    """Hash a password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_database():
    """Create the initial database with users table"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT,
            email TEXT,
            phone TEXT,
            active BOOLEAN DEFAULT 1,
            is_owner BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

def check_if_setup_complete():
    """Check if initial setup has been done"""
    if os.path.exists('trailer_tracker_streamlined.db'):
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_owner = 1")
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except:
            conn.close()
            return False
    return False

def main():
    st.set_page_config(page_title="Initial Setup - Smith & Williams Trucking", page_icon="🚛")
    
    # Check if setup is already done
    if check_if_setup_complete():
        st.success("✅ Setup is already complete!")
        st.info("You can now run the main app with: streamlit run app.py")
        st.warning("If you need to reset, delete the database file: trailer_tracker_streamlined.db")
        return
    
    st.title("🚛 Smith & Williams Trucking")
    st.header("Initial System Setup")
    st.info("Welcome! Let's set up your system with secure credentials.")
    
    with st.form("setup_form"):
        st.subheader("👑 Owner Account (You)")
        col1, col2 = st.columns(2)
        
        with col1:
            owner_username = st.text_input(
                "Your Username", 
                value="brandon_smith",
                help="This will be your login username"
            )
            owner_password = st.text_input(
                "Your Password", 
                type="password",
                help="Choose a strong password (minimum 8 characters)"
            )
            owner_password_confirm = st.text_input(
                "Confirm Password", 
                type="password"
            )
        
        with col2:
            owner_name = st.text_input(
                "Your Full Name", 
                value="Brandon Smith"
            )
            owner_email = st.text_input(
                "Your Email", 
                value="swtruckingceo@gmail.com"
            )
            owner_phone = st.text_input(
                "Your Phone", 
                value="(901) 555-0001"
            )
        
        st.divider()
        
        st.subheader("👤 Create Initial Staff Accounts")
        st.caption("You can add more users later from the admin panel")
        
        # Admin account
        with st.expander("Business Administrator Account", expanded=True):
            admin_username = st.text_input("Admin Username", value="admin")
            admin_password = st.text_input("Admin Password", type="password", value="")
            admin_name = st.text_input("Admin Name", value="Office Manager")
        
        # Coordinator account
        with st.expander("Operations Coordinator Account", expanded=True):
            coord_username = st.text_input("Coordinator Username", value="coordinator")
            coord_password = st.text_input("Coordinator Password", type="password", value="")
            coord_name = st.text_input("Coordinator Name", value="Dispatcher")
        
        # Driver account
        with st.expander("Sample Driver Account", expanded=True):
            driver_username = st.text_input("Driver Username", value="driver1")
            driver_password = st.text_input("Driver Password", type="password", value="")
            driver_name = st.text_input("Driver Name", value="John Driver")
        
        st.divider()
        
        # Google Maps API Key
        st.subheader("🗺️ Google Maps API Key (Optional)")
        st.caption("You can add this later in .streamlit/secrets.toml")
        google_api_key = st.text_input(
            "Google Maps API Key",
            type="password",
            help="For automatic mileage calculation"
        )
        
        submitted = st.form_submit_button("🚀 Complete Setup", type="primary", use_container_width=True)
        
        if submitted:
            # Validate owner account
            errors = []
            
            if not owner_username:
                errors.append("Owner username is required")
            if not owner_password:
                errors.append("Owner password is required")
            elif len(owner_password) < 8:
                errors.append("Owner password must be at least 8 characters")
            elif owner_password != owner_password_confirm:
                errors.append("Owner passwords do not match")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Create database and add users
                conn = create_database()
                cursor = conn.cursor()
                
                try:
                    # Add owner account
                    cursor.execute('''
                        INSERT INTO users (username, password, role, name, email, phone, is_owner, active)
                        VALUES (?, ?, ?, ?, ?, ?, 1, 1)
                    ''', (
                        owner_username,
                        hash_password(owner_password),
                        'business_administrator',
                        owner_name,
                        owner_email,
                        owner_phone
                    ))
                    
                    # Add admin account if provided
                    if admin_username and admin_password:
                        cursor.execute('''
                            INSERT INTO users (username, password, role, name, active)
                            VALUES (?, ?, ?, ?, 1)
                        ''', (
                            admin_username,
                            hash_password(admin_password),
                            'business_administrator',
                            admin_name
                        ))
                    
                    # Add coordinator account if provided
                    if coord_username and coord_password:
                        cursor.execute('''
                            INSERT INTO users (username, password, role, name, active)
                            VALUES (?, ?, ?, ?, 1)
                        ''', (
                            coord_username,
                            hash_password(coord_password),
                            'operations_coordinator',
                            coord_name
                        ))
                    
                    # Add driver account if provided
                    if driver_username and driver_password:
                        cursor.execute('''
                            INSERT INTO users (username, password, role, name, active)
                            VALUES (?, ?, ?, ?, 1)
                        ''', (
                            driver_username,
                            hash_password(driver_password),
                            'driver',
                            driver_name
                        ))
                    
                    conn.commit()
                    
                    # Save Google API key if provided
                    if google_api_key:
                        os.makedirs('.streamlit', exist_ok=True)
                        with open('.streamlit/secrets.toml', 'w') as f:
                            f.write(f'GOOGLE_MAPS_API_KEY = "{google_api_key}"\n')
                    
                    st.success("✅ Setup Complete!")
                    st.balloons()
                    
                    # Show credentials summary
                    st.markdown("### 📋 Your Login Credentials")
                    st.info(f"""
                    **Owner Account (You):**
                    - Username: `{owner_username}`
                    - Password: (the password you just set)
                    - Role: Full System Control + Owner Override
                    """)
                    
                    if admin_username and admin_password:
                        st.info(f"""
                        **Admin Account:**
                        - Username: `{admin_username}`
                        - Password: (the password you just set)
                        """)
                    
                    st.markdown("### 🚀 Next Steps")
                    st.markdown("""
                    1. Run the main application:
                       ```
                       streamlit run app.py
                       ```
                    2. Login with your owner credentials
                    3. Go to System Admin → User Management to add more users
                    4. Start using your system!
                    """)
                    
                    # Create init file to prevent re-running setup
                    with open('.setup_complete', 'w') as f:
                        f.write(f"Setup completed at {datetime.now()}")
                    
                except sqlite3.IntegrityError as e:
                    st.error(f"❌ Error: Username already exists. {str(e)}")
                except Exception as e:
                    st.error(f"❌ Setup failed: {str(e)}")
                finally:
                    conn.close()

if __name__ == "__main__":
    main()