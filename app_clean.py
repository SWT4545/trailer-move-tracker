"""
Clean Trailer Move Tracker with Simple Dark Theme
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import database as db
import auth_config

# Page configuration
st.set_page_config(
    page_title="Smith & Williams Trucking",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
db.init_database()

def apply_clean_dark_theme():
    """Apply clean dark theme without conflicts"""
    st.markdown("""
    <style>
        /* Main background */
        .stApp {
            background-color: #0A0A0A;
        }
        
        /* Sidebar background */
        section[data-testid="stSidebar"] {
            background-color: #1A1A1A;
            border-right: 2px solid #8B0000;
        }
        
        /* Headers */
        h1 {
            color: #FFD700;
            font-size: 2.5rem;
            border-bottom: 2px solid #8B0000;
            padding-bottom: 0.5rem;
        }
        
        h2 {
            color: #FFD700;
            font-size: 1.8rem;
        }
        
        h3 {
            color: #FFFFFF;
            font-size: 1.3rem;
        }
        
        /* Metric containers */
        div[data-testid="metric-container"] {
            background-color: #1A1A1A;
            border: 1px solid #8B0000;
            border-radius: 8px;
            padding: 1rem;
        }
        
        div[data-testid="metric-container"] label {
            color: #FFD700;
            font-size: 0.9rem;
        }
        
        div[data-testid="metric-container"] [data-testid="metric-container-value"] {
            color: #FFFFFF;
            font-size: 1.8rem;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #8B0000;
            color: white;
            border: 1px solid #DC143C;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            font-weight: 600;
        }
        
        .stButton > button:hover {
            background-color: #DC143C;
            border-color: #FF0000;
        }
        
        /* Text inputs */
        .stTextInput > div > div > input {
            background-color: #2A2A2A;
            color: white;
            border: 1px solid #444;
            border-radius: 5px;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #8B0000;
        }
        
        /* Select boxes */
        .stSelectbox > div > div {
            background-color: #2A2A2A;
            color: white;
        }
        
        /* Labels */
        .stTextInput > label,
        .stSelectbox > label,
        .stTextArea > label {
            color: #FFD700;
            font-size: 0.9rem;
        }
        
        /* Text color */
        .stMarkdown {
            color: #FFFFFF;
        }
        
        /* Info boxes */
        .stAlert {
            background-color: #1A1A1A;
            color: white;
            border: 1px solid #444;
        }
        
        /* Dataframes */
        .stDataFrame {
            background-color: #1A1A1A;
        }
        
        /* Dividers */
        hr {
            border-color: #8B0000;
        }
    </style>
    """, unsafe_allow_html=True)

def show_login():
    """Simple login form"""
    st.title("🚛 Smith & Williams Trucking")
    st.subheader("Trailer Move Tracker")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if auth_config.validate_user(username, password):
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = username
                    
                    if username in auth_config.USERS:
                        user_data = auth_config.USERS[username]
                        st.session_state["user_role"] = user_data.get('role', 'viewer')
                        st.session_state["user_name"] = user_data.get('name', username)
                        st.session_state["user_email"] = user_data.get('email', '')
                    
                    st.success("✅ Login successful!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        st.info("Login: **demo** / **demo**")

def show_dashboard():
    """Main dashboard"""
    st.title("📊 Dashboard")
    
    stats = db.get_summary_stats()
    df = db.get_all_trailer_moves()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Moves", f"{stats.get('total_moves', 0):,}")
    
    with col2:
        st.metric("Total Revenue", f"${stats.get('total_revenue', 0):,.2f}")
    
    with col3:
        st.metric("Unpaid Amount", f"${stats.get('total_unpaid', 0):,.2f}")
    
    with col4:
        st.metric("Average Pay", f"${stats.get('avg_load_pay', 0):,.2f}")
    
    st.markdown("---")
    
    # Data table
    st.subheader("Recent Trailer Moves")
    
    if not df.empty:
        st.dataframe(
            df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
    else:
        st.info("No trailer moves found. Add your first move to get started!")

def show_add_move():
    """Add new move form"""
    st.title("➕ Add New Move")
    
    with st.form("add_move"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_trailer = st.text_input("New Trailer Number *")
            pickup_location = st.text_input("Pickup Location *")
            pickup_date = st.date_input("Pickup Date")
        
        with col2:
            used_trailer = st.text_input("Used Trailer Number")
            delivery_location = st.text_input("Delivery Location *")
            delivery_date = st.date_input("Delivery Date")
        
        driver_name = st.text_input("Driver Name")
        load_pay = st.number_input("Load Pay ($)", min_value=0.0, step=100.0)
        notes = st.text_area("Notes", height=100)
        
        submitted = st.form_submit_button("Add Move", type="primary", use_container_width=True)
        
        if submitted:
            if new_trailer and pickup_location and delivery_location:
                try:
                    db.add_trailer_move(
                        new_trailer=new_trailer,
                        used_trailer=used_trailer or "",
                        pickup_location=pickup_location,
                        delivery_location=delivery_location,
                        pickup_date=pickup_date,
                        delivery_date=delivery_date,
                        driver_name=driver_name or "",
                        load_pay=load_pay,
                        notes=notes or ""
                    )
                    st.success("✅ Move added successfully!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Please fill in all required fields")

def show_email_center():
    """Email center"""
    st.title("✉️ Email Center")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Compose")
        
        to_email = st.text_input("To")
        subject = st.text_input("Subject")
        body = st.text_area("Message", height=200)
        
        if st.button("Send Email", type="primary", use_container_width=True):
            if to_email and subject and body:
                st.success(f"Email sent to {to_email}")
            else:
                st.error("Please fill in all fields")
    
    with col2:
        st.subheader("Preview")
        
        with st.container():
            st.write(f"**To:** {to_email if to_email else 'Enter recipient'}")
            st.write(f"**Subject:** {subject if subject else 'Enter subject'}")
            st.write("---")
            st.write(body if body else "Your message will appear here...")

def show_settings():
    """Settings page"""
    st.title("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("User Information")
        st.write(f"**Username:** {st.session_state.get('user', 'N/A')}")
        st.write(f"**Name:** {st.session_state.get('user_name', 'N/A')}")
        st.write(f"**Role:** {st.session_state.get('user_role', 'N/A')}")
        st.write(f"**Email:** {st.session_state.get('user_email', 'N/A')}")
    
    with col2:
        st.subheader("System Information")
        st.write(f"**Version:** 1.0.0")
        st.write(f"**Database:** SQLite")
        st.write(f"**Theme:** Dark")
        st.write(f"**Last Login:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

def main():
    """Main application"""
    
    # Apply theme
    apply_clean_dark_theme()
    
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    # Check authentication
    if not st.session_state["authenticated"]:
        show_login()
    else:
        # Sidebar
        with st.sidebar:
            # User info
            st.markdown(f"""
            ### 👤 {st.session_state.get('user_name', 'User')}
            **Role:** {st.session_state.get('user_role', 'User').title()}
            """)
            
            st.markdown("---")
            
            # Navigation
            page = st.selectbox(
                "Navigation",
                ["🏠 Dashboard", "➕ Add Move", "✉️ Email Center", "⚙️ Settings"]
            )
            
            st.markdown("---")
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
            
            # Footer
            st.markdown("---")
            st.caption("MC# 1276006 | DOT# 3675217")
            st.caption("© 2024 Smith & Williams")
        
        # Main content
        if page == "🏠 Dashboard":
            show_dashboard()
        elif page == "➕ Add Move":
            show_add_move()
        elif page == "✉️ Email Center":
            show_email_center()
        elif page == "⚙️ Settings":
            show_settings()

if __name__ == "__main__":
    main()