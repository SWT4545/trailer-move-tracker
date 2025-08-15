# -*- coding: utf-8 -*-
"""Fixed System Admin Module"""

import streamlit as st
import sqlite3
import pandas as pd
from email_api import email_api

def render_system_admin():
    """Render system admin page"""
    st.title("System Administration")
    
    tabs = st.tabs(["Users", "Email", "Database", "Logs"])
    
    with tabs[0]:
        manage_users()
    
    with tabs[1]:
        manage_email()
    
    with tabs[2]:
        manage_database()
    
    with tabs[3]:
        view_logs()

def manage_users():
    """User management"""
    st.subheader("User Management")
    
    try:
        conn = sqlite3.connect('trailer_tracker_streamlined.db')
        cursor = conn.cursor()
        
        # Ensure users table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        
        cursor.execute("SELECT id, username, role, active FROM users")
        users = cursor.fetchall()
        conn.close()
        
        if users:
            df = pd.DataFrame(users, columns=['ID', 'Username', 'Role', 'Active'])
            df['Active'] = df['Active'].apply(lambda x: '✅' if x else '❌')
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No users found in the database. Initial users have been created from user_accounts.json")
            
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")
        conn.close()

def manage_email():
    """Email configuration"""
    st.subheader("Email Configuration")
    
    with st.form("email_config"):
        server = st.text_input("SMTP Server", value="smtp.gmail.com")
        port = st.number_input("Port", value=587)
        email = st.text_input("Sender Email")
        
        if st.form_submit_button("Save"):
            config = {"smtp_server": server, "smtp_port": port, "sender_email": email}
            with open('email_config.json', 'w') as f:
                import json
                json.dump(config, f)
            st.success("Email configuration saved")

def manage_database():
    """Database management"""
    st.subheader("Database Management")
    
    if st.button("Backup Database"):
        import shutil
        from datetime import datetime
        backup = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy('trailer_tracker_streamlined.db', backup)
        st.success(f"Backup created: {backup}")

def view_logs():
    """View system logs"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, user, action FROM activity_log ORDER BY timestamp DESC LIMIT 50")
    logs = cursor.fetchall()
    conn.close()
    
    if logs:
        df = pd.DataFrame(logs, columns=['Time', 'User', 'Action'])
        st.dataframe(df)
