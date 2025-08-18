"""
Driver Portal - Login and Dashboard for Drivers
Smith and Williams Trucking
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import database as db
import branding
import utils
import hashlib

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def show_driver_login():
    """Driver login page"""
    st.markdown(branding.CUSTOM_CSS, unsafe_allow_html=True)
    
    # Header with branding
    st.markdown(f"""
    <div class="main-header">
        <div class="company-logo">
            {branding.get_logo_html(width=80)}
            <div>
                <h1 style="margin: 0; font-size: 2rem;">Smith and Williams Trucking</h1>
                <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">Driver Portal</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🚛 Driver Login")
        
        with st.form("driver_login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me")
            
            col_a, col_b = st.columns(2)
            with col_a:
                submitted = st.form_submit_button("🔓 Login", use_container_width=True)
            with col_b:
                if st.form_submit_button("❓ Forgot Password", use_container_width=True):
                    st.info("Please contact your dispatcher to reset your password")
            
            if submitted:
                if username and password:
                    # Authenticate driver
                    password_hash = hash_password(password)
                    driver = db.authenticate_driver(username, password_hash)
                    
                    if driver:
                        st.session_state['driver_authenticated'] = True
                        st.session_state['driver_id'] = driver['id']
                        st.session_state['driver_name'] = driver['driver_name']
                        st.session_state['driver_type'] = driver.get('driver_type', 'contractor')
                        st.success(f"Welcome back, {driver['driver_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
        
        with st.expander("ℹ️ First Time Login?"):
            st.markdown("""
            If this is your first time logging in:
            1. Your username was provided by your dispatcher
            2. Your temporary password was sent via text
            3. You'll be prompted to change your password on first login
            4. Contact dispatch if you need assistance
            """)

def show_driver_dashboard(driver_id):
    """Main dashboard for logged-in drivers"""
    driver = db.get_driver_by_id(driver_id)
    if not driver:
        st.error("Driver not found")
        return
    
    # Apply branding
    st.markdown(branding.CUSTOM_CSS, unsafe_allow_html=True)
    
    # Header
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"""
        <div style="padding: 1rem; background: #f8f9fa; border-radius: 8px; border: 2px solid #000;">
            <h2 style="margin: 0;">Welcome, {driver['driver_name']}</h2>
            <p style="margin: 0; color: #666;">{driver.get('driver_type', 'Contractor').title()} Driver</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🔒 Logout"):
            st.session_state['driver_authenticated'] = False
            st.session_state.pop('driver_id', None)
            st.session_state.pop('driver_name', None)
            st.rerun()
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard",
        "🚛 My Routes", 
        "💰 My Earnings",
        "📈 Performance",
        "👤 Profile"
    ])
    
    with tab1:
        show_driver_overview(driver_id)
    
    with tab2:
        show_driver_routes(driver_id)
    
    with tab3:
        show_driver_earnings(driver_id)
    
    with tab4:
        show_driver_performance(driver_id)
    
    with tab5:
        show_driver_profile(driver_id)

def show_driver_overview(driver_id):
    """Dashboard overview for driver"""
    st.subheader("📊 Dashboard Overview")
    
    # Get driver's moves
    all_moves = db.get_all_trailer_moves()
    driver_moves = all_moves[all_moves['assigned_driver'] == db.get_driver_by_id(driver_id)['driver_name']]
    
    # Calculate metrics
    completed_moves = driver_moves[driver_moves['completion_date'].notna()]
    active_moves = driver_moves[driver_moves['completion_date'].isna()]
    
    # This week's data
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_moves = completed_moves[pd.to_datetime(completed_moves['completion_date']) >= week_start]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_routes = len(completed_moves)
        st.metric("Total Routes", total_routes)
    
    with col2:
        active_routes = len(active_moves)
        st.metric("Active Routes", active_routes)
    
    with col3:
        week_miles = week_moves['miles'].sum() if not week_moves.empty else 0
        st.metric("Miles This Week", f"{week_miles:,.0f}")
    
    with col4:
        week_earnings = week_moves['load_pay'].sum() if not week_moves.empty else 0
        st.metric("This Week", utils.format_currency(week_earnings))
    
    # Current active route
    if not active_moves.empty:
        st.markdown("### 🚛 Current Active Route")
        current = active_moves.iloc[0]
        
        st.markdown(f"""
        <div style="background: #e7f3ff; border-left: 5px solid #17a2b8; border: 2px solid #000;
                    padding: 1.5rem; border-radius: 8px;">
            <h3 style="margin: 0;">Route #{current['id']}</h3>
            <p style="margin: 0.5rem 0; font-size: 1.1rem;">
                📍 <strong>From:</strong> {current['pickup_location']}<br>
                📍 <strong>To:</strong> {current['destination']}
            </p>
            <p style="margin: 0.5rem 0;">
                📦 <strong>New Trailer:</strong> {current['new_trailer']}<br>
                🔄 <strong>Old Trailer:</strong> {current['old_trailer'] if current['old_trailer'] else 'TBD'}
            </p>
            <p style="margin: 0.5rem 0;">
                🛣️ <strong>Miles:</strong> {current['miles']:,.0f}<br>
                💰 <strong>Pay:</strong> {utils.format_currency(current['load_pay'])}
            </p>
            <p style="margin: 0; color: #666;">
                Assigned: {pd.to_datetime(current['date_assigned']).strftime('%m/%d/%Y')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add button to access route via link
        if current.get('driver_link'):
            st.markdown(f"[📱 Open Route on Mobile]({current['driver_link']})")
    
    # Recent completed routes
    if not completed_moves.empty:
        st.markdown("### ✅ Recent Completed Routes")
        recent = completed_moves.nlargest(5, 'completion_date')
        
        for _, route in recent.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                st.markdown(f"**Route #{route['id']}** - {route['pickup_location']} → {route['destination']}")
            with col2:
                st.markdown(f"Completed: {pd.to_datetime(route['completion_date']).strftime('%m/%d/%Y')}")
            with col3:
                st.markdown(f"{route['miles']:,.0f} miles")
            with col4:
                st.markdown(f"{utils.format_currency(route['load_pay'])}")

def show_driver_routes(driver_id):
    """Show all routes for a driver"""
    st.subheader("🚛 My Routes")
    
    driver = db.get_driver_by_id(driver_id)
    all_moves = db.get_all_trailer_moves()
    driver_moves = all_moves[all_moves['assigned_driver'] == driver['driver_name']]
    
    if driver_moves.empty:
        st.info("No routes assigned yet")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Active", "Completed"])
    with col2:
        date_from = st.date_input("From", value=datetime.now() - timedelta(days=30))
    with col3:
        date_to = st.date_input("To", value=datetime.now())
    
    # Apply filters
    filtered_moves = driver_moves.copy()
    
    if status_filter == "Active":
        filtered_moves = filtered_moves[filtered_moves['completion_date'].isna()]
    elif status_filter == "Completed":
        filtered_moves = filtered_moves[filtered_moves['completion_date'].notna()]
    
    # Date filter
    filtered_moves['date_assigned'] = pd.to_datetime(filtered_moves['date_assigned'])
    filtered_moves = filtered_moves[
        (filtered_moves['date_assigned'].dt.date >= date_from) &
        (filtered_moves['date_assigned'].dt.date <= date_to)
    ]
    
    if filtered_moves.empty:
        st.info("No routes found for selected filters")
        return
    
    # Display routes
    st.markdown(f"### Found {len(filtered_moves)} routes")
    
    for _, route in filtered_moves.iterrows():
        status_color = "#28a745" if pd.notna(route['completion_date']) else "#ffc107"
        status_text = "Completed" if pd.notna(route['completion_date']) else "Active"
        
        with st.expander(f"Route #{route['id']} - {status_text} - {route['pickup_location']} → {route['destination']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Route Details**")
                st.markdown(f"""
                - **From:** {route['pickup_location']}
                - **To:** {route['destination']}
                - **New Trailer:** {route['new_trailer']}
                - **Old Trailer:** {route['old_trailer'] if route['old_trailer'] else 'N/A'}
                - **Miles:** {route['miles']:,.0f}
                """)
            
            with col2:
                st.markdown("**Status & Payment**")
                st.markdown(f"""
                - **Status:** <span style='color: {status_color}'>{status_text}</span>
                - **Assigned:** {pd.to_datetime(route['date_assigned']).strftime('%m/%d/%Y')}
                - **Completed:** {pd.to_datetime(route['completion_date']).strftime('%m/%d/%Y') if pd.notna(route['completion_date']) else 'In Progress'}
                - **Load Pay:** {utils.format_currency(route['load_pay'])}
                - **Paid:** {'Yes ✅' if route['paid'] else 'Pending ⏳'}
                """, unsafe_allow_html=True)
            
            if route['comments']:
                st.markdown(f"**Notes:** {route['comments']}")

def show_driver_earnings(driver_id):
    """Show earnings breakdown for driver"""
    st.subheader("💰 My Earnings")
    
    driver = db.get_driver_by_id(driver_id)
    all_moves = db.get_all_trailer_moves()
    driver_moves = all_moves[all_moves['assigned_driver'] == driver['driver_name']]
    completed_moves = driver_moves[driver_moves['completion_date'].notna()]
    
    if completed_moves.empty:
        st.info("No completed routes yet")
        return
    
    # Time period selector
    period = st.selectbox("View Period", ["This Week", "Last Week", "This Month", "Last Month", "Year to Date", "Custom"])
    
    if period == "Custom":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
    else:
        # Calculate date ranges
        today = datetime.now()
        if period == "This Week":
            start_date = today - timedelta(days=today.weekday())
            end_date = today
        elif period == "Last Week":
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = today - timedelta(days=today.weekday() + 1)
        elif period == "This Month":
            start_date = datetime(today.year, today.month, 1)
            end_date = today
        elif period == "Last Month":
            last_month = today.replace(day=1) - timedelta(days=1)
            start_date = datetime(last_month.year, last_month.month, 1)
            end_date = last_month
        else:  # Year to Date
            start_date = datetime(today.year, 1, 1)
            end_date = today
    
    # Filter moves by date
    completed_moves['completion_date'] = pd.to_datetime(completed_moves['completion_date'])
    period_moves = completed_moves[
        (completed_moves['completion_date'].dt.date >= start_date.date() if isinstance(start_date, datetime) else start_date) &
        (completed_moves['completion_date'].dt.date <= end_date.date() if isinstance(end_date, datetime) else end_date)
    ]
    
    # Calculate earnings
    total_miles = period_moves['miles'].sum()
    gross_pay = period_moves['load_pay'].sum()
    paid_amount = period_moves[period_moves['paid'] == True]['load_pay'].sum()
    pending_amount = period_moves[period_moves['paid'] == False]['load_pay'].sum()
    
    # Display summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Earned", utils.format_currency(gross_pay))
    with col2:
        st.metric("Paid", utils.format_currency(paid_amount))
    with col3:
        st.metric("Pending", utils.format_currency(pending_amount))
    with col4:
        st.metric("Total Miles", f"{total_miles:,.0f}")
    
    st.divider()
    
    # Detailed breakdown
    st.markdown("### 📋 Earnings Breakdown")
    
    if not period_moves.empty:
        # Prepare display data
        display_df = period_moves[['id', 'completion_date', 'pickup_location', 'destination', 'miles', 'load_pay', 'paid']].copy()
        display_df['completion_date'] = display_df['completion_date'].dt.strftime('%m/%d/%Y')
        display_df['route'] = display_df['pickup_location'] + ' → ' + display_df['destination']
        display_df['status'] = display_df['paid'].map({True: '✅ Paid', False: '⏳ Pending'})
        display_df['load_pay_display'] = display_df['load_pay'].apply(utils.format_currency)
        
        # Select columns to display
        display_df = display_df[['id', 'completion_date', 'route', 'miles', 'load_pay_display', 'status']]
        display_df.columns = ['Route #', 'Date', 'Route', 'Miles', 'Pay', 'Status']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Weekly summary
        st.markdown("### 📊 Weekly Summary")
        period_moves['week'] = period_moves['completion_date'].dt.to_period('W')
        weekly_summary = period_moves.groupby('week').agg({
            'miles': 'sum',
            'load_pay': 'sum',
            'id': 'count'
        }).rename(columns={'id': 'routes'})
        
        if not weekly_summary.empty:
            weekly_summary.index = weekly_summary.index.astype(str)
            weekly_summary['miles'] = weekly_summary['miles'].apply(lambda x: f"{x:,.0f}")
            weekly_summary['load_pay'] = weekly_summary['load_pay'].apply(utils.format_currency)
            weekly_summary.columns = ['Total Miles', 'Total Pay', 'Routes']
            
            st.dataframe(weekly_summary, use_container_width=True)
    else:
        st.info(f"No completed routes found for {period}")

def show_driver_performance(driver_id):
    """Show performance metrics for driver"""
    st.subheader("📈 My Performance")
    
    driver = db.get_driver_by_id(driver_id)
    all_moves = db.get_all_trailer_moves()
    driver_moves = all_moves[all_moves['assigned_driver'] == driver['driver_name']]
    completed_moves = driver_moves[driver_moves['completion_date'].notna()]
    
    if completed_moves.empty:
        st.info("Complete routes to see your performance metrics")
        return
    
    # Calculate performance metrics
    total_routes = len(completed_moves)
    total_miles = completed_moves['miles'].sum()
    
    # Calculate on-time percentage (simplified - assumes routes completed same day are on-time)
    completed_moves['date_assigned'] = pd.to_datetime(completed_moves['date_assigned'])
    completed_moves['completion_date'] = pd.to_datetime(completed_moves['completion_date'])
    completed_moves['days_to_complete'] = (completed_moves['completion_date'] - completed_moves['date_assigned']).dt.days
    on_time = len(completed_moves[completed_moves['days_to_complete'] <= 1])
    on_time_percentage = (on_time / total_routes * 100) if total_routes > 0 else 0
    
    # Average miles per route
    avg_miles = total_miles / total_routes if total_routes > 0 else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Routes", total_routes)
    
    with col2:
        st.metric("Total Miles", f"{total_miles:,.0f}")
    
    with col3:
        st.metric("On-Time Rate", f"{on_time_percentage:.1f}%")
    
    with col4:
        st.metric("Avg Miles/Route", f"{avg_miles:.0f}")
    
    st.divider()
    
    # Performance over time
    st.markdown("### 📊 Performance Trends")
    
    # Monthly performance
    completed_moves['month'] = completed_moves['completion_date'].dt.to_period('M')
    monthly_stats = completed_moves.groupby('month').agg({
        'id': 'count',
        'miles': 'sum',
        'load_pay': 'sum'
    }).rename(columns={'id': 'routes'})
    
    if not monthly_stats.empty:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Routes per Month', 'Miles per Month', 'Earnings per Month', 'Average Miles per Route'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'scatter'}]]
        )
        
        months = monthly_stats.index.astype(str)
        
        # Routes per month
        fig.add_trace(
            go.Bar(x=months, y=monthly_stats['routes'], name='Routes', marker_color='#DC143C'),
            row=1, col=1
        )
        
        # Miles per month
        fig.add_trace(
            go.Bar(x=months, y=monthly_stats['miles'], name='Miles', marker_color='#17a2b8'),
            row=1, col=2
        )
        
        # Earnings per month
        fig.add_trace(
            go.Bar(x=months, y=monthly_stats['load_pay'], name='Earnings', marker_color='#28a745'),
            row=2, col=1
        )
        
        # Average miles per route
        avg_miles_monthly = monthly_stats['miles'] / monthly_stats['routes']
        fig.add_trace(
            go.Scatter(x=months, y=avg_miles_monthly, name='Avg Miles', 
                      mode='lines+markers', marker_color='#ffc107'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False, title_text="Performance Analysis")
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent performance
    st.markdown("### 🏆 Recent Performance")
    
    # Last 10 routes
    recent = completed_moves.nlargest(10, 'completion_date')[['completion_date', 'pickup_location', 'destination', 'miles', 'days_to_complete']]
    recent['completion_date'] = recent['completion_date'].dt.strftime('%m/%d/%Y')
    recent['route'] = recent['pickup_location'] + ' → ' + recent['destination']
    recent['performance'] = recent['days_to_complete'].apply(lambda x: '✅ On-Time' if x <= 1 else '⚠️ Late')
    
    display_df = recent[['completion_date', 'route', 'miles', 'performance']]
    display_df.columns = ['Date', 'Route', 'Miles', 'Status']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

def show_driver_profile(driver_id):
    """Show and edit driver profile"""
    st.subheader("👤 My Profile")
    
    driver = db.get_driver_by_id(driver_id)
    if not driver:
        st.error("Driver profile not found")
        return
    
    # Display current profile
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Contact Information")
        with st.form("update_contact"):
            phone = st.text_input("Phone Number", value=driver.get('phone_number', ''))
            email = st.text_input("Email Address", value=driver.get('email', ''))
            emergency_contact = st.text_input("Emergency Contact", value=driver.get('emergency_contact', ''))
            
            if st.form_submit_button("Update Contact Info"):
                update_data = {
                    'phone_number': phone,
                    'email': email,
                    'emergency_contact': emergency_contact
                }
                db.update_driver_profile(driver_id, update_data)
                st.success("Contact information updated successfully!")
                st.rerun()
    
    with col2:
        st.markdown("### Driver Information")
        st.markdown(f"""
        **Name:** {driver['driver_name']}  
        **Type:** {driver.get('driver_type', 'Contractor').title()}  
        **CDL Number:** {driver.get('cdl_number', 'Not provided')}  
        **CDL Expiration:** {driver.get('cdl_expiration', 'Not provided')}  
        """)
        
        if driver.get('driver_type') == 'contractor':
            st.markdown(f"""
            **Company:** {driver.get('company_name', 'Not provided')}  
            **DOT Number:** {driver.get('dot', 'Not provided')}  
            **MC Number:** {driver.get('mc', 'Not provided')}  
            """)
        else:
            st.markdown(f"""
            **Employee ID:** {driver.get('employee_id', 'Not provided')}  
            **Hire Date:** {driver.get('hire_date', 'Not provided')}  
            **Home Terminal:** {driver.get('home_terminal', 'Not provided')}  
            """)
    
    st.divider()
    
    # Password change
    st.markdown("### 🔐 Change Password")
    with st.form("change_password"):
        col1, col2 = st.columns(2)
        with col1:
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
        with col2:
            confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Change Password"):
            if not all([current_password, new_password, confirm_password]):
                st.error("Please fill in all password fields")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long")
            else:
                # Verify current password
                current_hash = hash_password(current_password)
                if db.authenticate_driver(driver.get('user'), current_hash):
                    # Update password
                    new_hash = hash_password(new_password)
                    db.update_driver_profile(driver_id, {'password_hash': new_hash})
                    st.success("Password changed successfully!")
                else:
                    st.error("Current password is incorrect")
    
    st.divider()
    
    # Notification preferences
    st.markdown("### 🔔 Notification Preferences")
    col1, col2 = st.columns(2)
    
    with col1:
        text_notifications = st.checkbox("Receive text notifications", value=True)
        email_notifications = st.checkbox("Receive email notifications", value=True)
    
    with col2:
        notification_types = st.multiselect(
            "Notify me about:",
            ["New route assignments", "Route changes", "Payment updates", "Performance reports"],
            default=["New route assignments", "Payment updates"]
        )
    
    if st.button("Save Preferences"):
        st.success("Notification preferences saved!")

# Main driver portal app
def driver_portal_app():
    """Main driver portal application"""
    if 'driver_authenticated' not in st.session_state:
        st.session_state['driver_authenticated'] = False
    
    if not st.session_state['driver_authenticated']:
        show_driver_login()
    else:
        show_driver_dashboard(st.session_state['driver_id'])

if __name__ == "__main__":
    driver_portal_app()