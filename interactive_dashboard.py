"""
Interactive Progress Dashboard
Real-time visualization of moves, documents, and payment status
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def show_interactive_dashboard(role="Owner"):
    """Display interactive progress dashboard based on user role"""
    
    if role in ["Owner", "Admin", "business_administrator"]:
        show_management_dashboard()
    elif role == "driver":
        show_driver_progress()
    elif role in ["coordinator", "dispatcher"]:
        show_coordinator_dashboard()
    else:
        show_basic_dashboard()

def show_management_dashboard():
    """Management's comprehensive interactive dashboard with priority alerts"""
    st.markdown("# 📊 Management Operations Dashboard")
    
    # Check time for factoring deadline
    current_time = datetime.now()
    current_hour = current_time.hour
    is_business_day = current_time.weekday() < 5  # Monday-Friday
    
    # Priority Alerts Section
    if is_business_day and current_hour < 11:
        time_to_deadline = 11 - current_hour
        st.error(f"⚠️ FACTORING DEADLINE: {time_to_deadline} hours remaining - Submit by 11AM EST for next-day payout!")
    elif is_business_day and current_hour >= 11:
        st.warning("⏰ Factoring deadline passed - Submissions will process next business day")
    
    st.caption(f"Real-time as of {current_time.strftime('%I:%M %p EST')}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Main metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Get current metrics
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'in_progress'")
    active_moves = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed' AND payment_status != 'paid'")
    pending_payment = cursor.fetchone()[0]
    
    cursor.execute('''SELECT COUNT(*) FROM moves m 
                     JOIN document_requirements dr ON m.move_id = dr.move_id 
                     WHERE m.status = 'completed' AND dr.all_docs_complete = 0''')
    pending_docs = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(net_pay) FROM moves WHERE payment_status = 'paid' AND payment_date >= date('now', '-30 days')")
    monthly_revenue = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(DISTINCT driver_name) FROM moves WHERE status = 'in_progress'")
    active_drivers = cursor.fetchone()[0]
    
    with col1:
        st.metric("🚚 Active Moves", active_moves, delta="+2 today")
    with col2:
        st.metric("👥 Active Drivers", active_drivers)
    with col3:
        st.metric("📄 Pending Docs", pending_docs, delta_color="inverse")
    with col4:
        st.metric("💳 Awaiting Payment", pending_payment)
    with col5:
        st.metric("💰 30-Day Revenue", f"${monthly_revenue:,.0f}")
    
    st.markdown("---")
    
    # Progress Pipeline
    st.markdown("## 🔄 Move Pipeline Progress")
    
    # Get move pipeline data
    cursor.execute('''SELECT 
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'assigned' THEN 1 ELSE 0 END) as assigned,
                        SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                        SUM(CASE WHEN status = 'completed' AND payment_status != 'paid' THEN 1 ELSE 0 END) as awaiting_payment,
                        SUM(CASE WHEN payment_status = 'paid' THEN 1 ELSE 0 END) as paid
                     FROM moves''')
    pipeline = cursor.fetchone()
    
    # Create pipeline visualization
    fig = go.Figure()
    
    stages = ['Pending', 'Assigned', 'In Progress', 'Awaiting Payment', 'Paid']
    values = list(pipeline)
    colors = ['#FFA500', '#FFD700', '#4169E1', '#DC143C', '#28a745']
    
    for i, (stage, value, color) in enumerate(zip(stages, values, colors)):
        fig.add_trace(go.Bar(
            name=stage,
            x=[stage],
            y=[value],
            text=value,
            textposition='auto',
            marker_color=color,
            hovertemplate=f'{stage}: {value} moves<extra></extra>'
        ))
    
    fig.update_layout(
        title="Move Status Pipeline",
        showlegend=False,
        height=300,
        margin=dict(t=50, b=0, l=0, r=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Two column layout for detailed sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Active Moves Progress")
        
        # Get active moves with progress
        cursor.execute('''SELECT m.move_id, m.driver_name, m.delivery_location,
                                m.status, dr.rate_confirmation, dr.bol, dr.pod
                         FROM moves m
                         LEFT JOIN document_requirements dr ON m.move_id = dr.move_id
                         WHERE m.status IN ('assigned', 'in_progress', 'completed')
                         AND m.payment_status != 'paid'
                         ORDER BY m.move_date DESC
                         LIMIT 10''')
        active_moves_list = cursor.fetchall()
        
        for move in active_moves_list:
            move_id, driver, location, status, has_rc, has_bol, has_pod = move
            
            # Calculate progress
            progress_steps = {
                'assigned': 25,
                'in_progress': 50,
                'completed': 75
            }
            base_progress = progress_steps.get(status, 0)
            
            # Add document progress
            doc_progress = 0
            if status == 'completed':
                if has_rc: doc_progress += 8
                if has_bol: doc_progress += 8
                if has_pod: doc_progress += 9
            
            total_progress = min(base_progress + doc_progress, 100)
            
            with st.container():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{move_id}** - {driver}")
                    st.caption(f"→ {location}")
                with col_b:
                    st.caption(status.upper())
                
                # Progress bar
                progress_bar = st.progress(total_progress / 100)
                
                # Document indicators
                if status == 'completed':
                    doc_cols = st.columns(3)
                    with doc_cols[0]:
                        st.caption("RC: " + ("✅" if has_rc else "❌"))
                    with doc_cols[1]:
                        st.caption("BOL: " + ("✅" if has_bol else "❌"))
                    with doc_cols[2]:
                        st.caption("POD: " + ("✅" if has_pod else "❌"))
    
    with col2:
        st.markdown("### 💰 Payment Processing Queue")
        
        # Get payment queue
        cursor.execute('''SELECT m.move_id, m.driver_name, m.driver_pay,
                                m.completed_date, dr.all_docs_complete,
                                m.submitted_to_factoring
                         FROM moves m
                         LEFT JOIN document_requirements dr ON m.move_id = dr.move_id
                         WHERE m.status = 'completed' 
                         AND m.payment_status != 'paid'
                         ORDER BY m.completed_date
                         LIMIT 10''')
        payment_queue = cursor.fetchall()
        
        for payment in payment_queue:
            move_id, driver, amount, comp_date, docs_complete, factoring = payment
            
            # Determine payment stage
            if not docs_complete:
                stage = "📄 Awaiting Docs"
                color = "🔴"
            elif not factoring:
                stage = "💳 Ready for Factoring"
                color = "🟡"
            else:
                stage = "✅ Ready to Pay"
                color = "🟢"
            
            with st.container():
                col_a, col_b, col_c = st.columns([2, 1, 1])
                with col_a:
                    st.markdown(f"{color} **{move_id}**")
                    st.caption(driver)
                with col_b:
                    est_net = amount * 0.97  # 3% fee
                    st.caption(f"${est_net:.2f}")
                with col_c:
                    st.caption(stage)
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Weekly Move Completion")
        
        # Get weekly completion data
        cursor.execute('''SELECT DATE(completed_date) as date, COUNT(*) as count
                         FROM moves
                         WHERE status = 'completed'
                         AND completed_date >= date('now', '-7 days')
                         GROUP BY DATE(completed_date)
                         ORDER BY date''')
        weekly_data = cursor.fetchall()
        
        if weekly_data:
            df = pd.DataFrame(weekly_data, columns=['Date', 'Completed'])
            fig = px.line(df, x='Date', y='Completed', 
                         markers=True, 
                         title="7-Day Completion Trend")
            fig.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🚛 Driver Performance")
        
        # Get driver performance
        cursor.execute('''SELECT driver_name, COUNT(*) as moves, 
                                SUM(total_miles) as miles
                         FROM moves
                         WHERE status = 'completed'
                         AND completed_date >= date('now', '-30 days')
                         GROUP BY driver_name
                         ORDER BY moves DESC
                         LIMIT 5''')
        driver_perf = cursor.fetchall()
        
        if driver_perf:
            df = pd.DataFrame(driver_perf, columns=['Driver', 'Moves', 'Miles'])
            fig = px.bar(df, x='Driver', y='Moves', 
                        title="Top Drivers (30 Days)",
                        color='Moves',
                        color_continuous_scale='Blues')
            fig.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
    
    # Priority Actions Section
    st.markdown("---")
    st.markdown("## 🚨 Priority Actions Required")
    
    # Get urgent factoring submissions
    cursor.execute('''SELECT COUNT(*) FROM moves m
                     JOIN document_requirements dr ON m.move_id = dr.move_id
                     WHERE m.status = 'completed' 
                     AND dr.all_docs_complete = 1
                     AND (m.submitted_to_factoring IS NULL OR m.submitted_to_factoring = '')
                     AND m.completed_date <= date('now', '-1 day')''')
    urgent_factoring = cursor.fetchone()[0]
    
    if urgent_factoring > 0 and current_hour < 11:
        with st.container():
            st.error(f"🚨 HIGH PRIORITY: {urgent_factoring} moves ready for factoring - Submit before 11AM EST!")
            if st.button("Go to Factoring Submission", type="primary"):
                st.session_state['page'] = 'factoring'
    
    # Real-time alerts section
    st.markdown("---")
    st.markdown("## 🔔 Real-Time Task Alerts")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### ⚠️ Urgent Actions")
        
        # Check for urgent items
        cursor.execute('''SELECT COUNT(*) FROM moves 
                         WHERE status = 'completed' 
                         AND completed_date < date('now', '-3 days')
                         AND payment_status != 'paid' ''')
        old_unpaid = cursor.fetchone()[0]
        
        if old_unpaid > 0:
            st.error(f"🚨 {old_unpaid} moves pending payment >3 days")
        
        cursor.execute('''SELECT COUNT(*) FROM moves 
                         WHERE status = 'pending' 
                         AND move_date <= date('now')''')
        unassigned_today = cursor.fetchone()[0]
        
        if unassigned_today > 0:
            st.warning(f"📋 {unassigned_today} moves need assignment today")
    
    with col2:
        st.markdown("#### 📄 Document Status")
        
        cursor.execute('''SELECT COUNT(*) FROM moves m
                         LEFT JOIN document_requirements dr ON m.move_id = dr.move_id
                         WHERE m.status = 'completed'
                         AND (dr.rate_confirmation = 0 OR dr.bol = 0)''')
        missing_docs = cursor.fetchone()[0]
        
        if missing_docs > 0:
            st.info(f"📁 {missing_docs} moves missing critical docs")
        else:
            st.success("✅ All critical documents received")
    
    with col3:
        st.markdown("#### 💵 Payment Status")
        
        cursor.execute('''SELECT SUM(driver_pay * 0.97) 
                         FROM moves 
                         WHERE status = 'completed' 
                         AND payment_status != 'paid' ''')
        pending_amount = cursor.fetchone()[0] or 0
        
        st.info(f"💰 ${pending_amount:,.2f} pending payment")
        
        if pending_amount > 10000:
            st.warning("Consider processing payments")
    
    conn.close()

def show_driver_progress():
    """Driver's personal progress dashboard"""
    st.markdown("# 🚛 Driver Dashboard")
    
    driver_name = st.session_state.get('username', 'Driver')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get driver metrics with both paid and pending amounts
    cursor.execute('''SELECT 
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                        COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active,
                        SUM(CASE WHEN status = 'completed' THEN total_miles ELSE 0 END) as total_miles,
                        SUM(CASE WHEN payment_status = 'paid' THEN net_pay ELSE 0 END) as total_earned,
                        SUM(CASE WHEN status = 'completed' AND payment_status != 'paid' THEN driver_pay * 0.97 ELSE 0 END) as pending_earnings
                     FROM moves
                     WHERE driver_name = ?''', (driver_name,))
    
    metrics = cursor.fetchone()
    completed, active, miles, earned, pending = metrics
    total_to_date = (earned or 0) + (pending or 0)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("✅ Completed", completed or 0)
    with col2:
        st.metric("🚚 Active", active or 0)
    with col3:
        st.metric("📍 Total Miles", f"{int(miles or 0):,}")
    with col4:
        st.metric("💰 Paid", f"${earned or 0:,.2f}")
    
    st.markdown("---")
    
    # Money Bag - Total Earnings to Date
    st.markdown("### 💰 Your Money Bag")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Create visual money bag indicator
        st.markdown("#### 💰 Total Earned to Date")
        # Visual progress indicator
        if total_to_date > 0:
            if total_to_date < 5000:
                bag_emoji = "💵"
                bag_status = "Getting Started"
            elif total_to_date < 10000:
                bag_emoji = "💰"
                bag_status = "Building Up"
            elif total_to_date < 25000:
                bag_emoji = "💰💰"
                bag_status = "Strong Earner"
            else:
                bag_emoji = "💰💰💰"
                bag_status = "Top Performer"
            
            st.markdown(f"### {bag_emoji}")
            st.metric("Total in Your Bag", f"${total_to_date:,.2f}", delta=f"{bag_status}")
        else:
            st.metric("Total in Your Bag", "$0.00", delta="Start earning today!")
    
    with col2:
        st.markdown("#### 💵 Breakdown")
        st.success(f"Paid: ${earned or 0:,.2f}")
        st.warning(f"Pending: ${pending or 0:,.2f}")
        
        # Calculate weekly average
        cursor.execute('''SELECT AVG(weekly_total) FROM (
                            SELECT SUM(net_pay) as weekly_total
                            FROM moves
                            WHERE driver_name = ?
                            AND payment_status = 'paid'
                            AND payment_date >= date('now', '-30 days')
                            GROUP BY strftime('%W', payment_date)
                        )''', (driver_name,))
        weekly_avg = cursor.fetchone()[0] or 0
        st.info(f"Weekly Avg: ${weekly_avg:,.2f}")
    
    with col3:
        st.markdown("#### 📈 This Week")
        cursor.execute('''SELECT SUM(driver_pay * 0.97)
                         FROM moves
                         WHERE driver_name = ?
                         AND completed_date >= date('now', 'weekday 0', '-7 days')
                         AND status = 'completed' ''', (driver_name,))
        this_week = cursor.fetchone()[0] or 0
        
        cursor.execute('''SELECT SUM(driver_pay * 0.97)
                         FROM moves
                         WHERE driver_name = ?
                         AND completed_date >= date('now', 'weekday 0', '-14 days')
                         AND completed_date < date('now', 'weekday 0', '-7 days')
                         AND status = 'completed' ''', (driver_name,))
        last_week = cursor.fetchone()[0] or 0
        
        week_delta = this_week - last_week
        week_delta_str = f"+${week_delta:.2f}" if week_delta >= 0 else f"-${abs(week_delta):.2f}"
        
        st.metric("This Week's Earnings", f"${this_week:,.2f}", delta=week_delta_str)
        
        # Progress to next milestone
        milestones = [5000, 10000, 25000, 50000, 100000]
        next_milestone = next((m for m in milestones if m > total_to_date), 100000)
        progress_to_milestone = (total_to_date / next_milestone) * 100
        
        st.markdown(f"**Progress to ${next_milestone:,}**")
        st.progress(progress_to_milestone / 100)
        st.caption(f"${next_milestone - total_to_date:,.2f} to go!")
    
    st.markdown("---")
    
    # Current moves progress
    st.markdown("### 📋 My Active Moves")
    
    cursor.execute('''SELECT move_id, pickup_location, delivery_location, 
                            status, total_miles, driver_pay
                     FROM moves
                     WHERE driver_name = ?
                     AND status IN ('assigned', 'in_progress')
                     ORDER BY move_date''', (driver_name,))
    
    active_moves = cursor.fetchall()
    
    if active_moves:
        for move in active_moves:
            move_id, pickup, delivery, status, miles, pay = move
            
            # Progress calculation
            progress = 33 if status == 'assigned' else 66
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{move_id}**")
                st.caption(f"{pickup} → {delivery}")
                st.progress(progress / 100)
            with col2:
                est_net = pay * 0.97 if pay else 0
                st.metric("Est. Pay", f"${est_net:.2f}")
                st.caption(f"{miles} miles")
    else:
        st.info("No active moves. Check available moves for new assignments!")
    
    # Payment status
    st.markdown("---")
    st.markdown("### 💳 Payment Status")
    
    cursor.execute('''SELECT move_id, completed_date, driver_pay, payment_status
                     FROM moves
                     WHERE driver_name = ?
                     AND status = 'completed'
                     ORDER BY completed_date DESC
                     LIMIT 5''', (driver_name,))
    
    recent_completed = cursor.fetchall()
    
    if recent_completed:
        for move in recent_completed:
            move_id, comp_date, pay, pay_status = move
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{move_id}**")
                st.caption(f"Completed: {comp_date}")
            with col2:
                est_net = pay * 0.97
                st.caption(f"${est_net:.2f}")
            with col3:
                if pay_status == 'paid':
                    st.success("✅ Paid")
                else:
                    st.warning("⏳ Pending")
    
    conn.close()

def show_basic_dashboard():
    """Basic dashboard for other roles"""
    st.markdown("# 📊 Operations Dashboard")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Basic metrics
    col1, col2, col3, col4 = st.columns(4)
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'in_progress'")
    active = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE status = 'available'")
    available_trailers = cursor.fetchone()[0]
    
    with col1:
        st.metric("📋 Pending", pending)
    with col2:
        st.metric("🚚 Active", active)
    with col3:
        st.metric("✅ Completed", completed)
    with col4:
        st.metric("🚛 Available Trailers", available_trailers)
    
    conn.close()

def show_coordinator_dashboard():
    """Coordinator dashboard without financial information"""
    st.markdown("# 📊 Coordinator Dashboard")
    st.caption(f"Real-time as of {datetime.now().strftime('%I:%M %p')}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Main metrics (no financial data)
    col1, col2, col3, col4 = st.columns(4)
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'in_progress'")
    active_moves = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'pending'")
    pending_moves = cursor.fetchone()[0]
    
    cursor.execute('''SELECT COUNT(*) FROM moves m
                     JOIN document_requirements dr ON m.move_id = dr.move_id
                     WHERE m.status = 'completed' AND dr.all_docs_complete = 0''')
    pending_docs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT driver_name) FROM moves WHERE status = 'in_progress'")
    active_drivers = cursor.fetchone()[0]
    
    with col1:
        st.metric("🚚 Active Moves", active_moves)
    with col2:
        st.metric("📋 Pending Moves", pending_moves)
    with col3:
        st.metric("📄 Pending Docs", pending_docs)
    with col4:
        st.metric("👥 Active Drivers", active_drivers)
    
    st.markdown("---")
    
    # Document Collection Tasks
    st.markdown("## 📄 Document Collection Tasks")
    
    cursor.execute('''SELECT m.move_id, m.driver_name, m.delivery_location,
                            dr.rate_confirmation, dr.bol, dr.pod
                     FROM moves m
                     LEFT JOIN document_requirements dr ON m.move_id = dr.move_id
                     WHERE m.status = 'completed'
                     AND (dr.all_docs_complete = 0 OR dr.all_docs_complete IS NULL)
                     ORDER BY m.completed_date DESC
                     LIMIT 10''')
    
    docs_needed = cursor.fetchall()
    
    if docs_needed:
        st.markdown("### Moves Needing Documents")
        for move in docs_needed:
            move_id, driver, location, has_rc, has_bol, has_pod = move
            
            missing = []
            if not has_rc: missing.append("Rate Conf")
            if not has_bol: missing.append("BOL") 
            if not has_pod: missing.append("POD")
            
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.markdown(f"**{move_id}**")
            with col2:
                st.caption(f"{driver}")
            with col3:
                st.caption(f"Missing: {', '.join(missing)}")
            with col4:
                if st.button("📤 Upload", key=f"upload_{move_id}"):
                    st.session_state['upload_move'] = move_id
                    st.session_state['page'] = 'documents'
    else:
        st.success("✅ All documents collected")
    
    # Move Assignment Section
    st.markdown("---")
    st.markdown("## 🚛 Move Assignment Status")
    
    cursor.execute('''SELECT move_id, pickup_location, delivery_location, move_date
                     FROM moves
                     WHERE status = 'pending'
                     ORDER BY move_date
                     LIMIT 10''')
    
    unassigned = cursor.fetchall()
    
    if unassigned:
        st.markdown("### Unassigned Moves")
        for move in unassigned:
            move_id, pickup, delivery, date = move
            
            col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
            with col1:
                st.markdown(f"**{move_id}**")
            with col2:
                st.caption(f"{pickup} → {delivery}")
            with col3:
                st.caption(date)
            with col4:
                if st.button("Assign", key=f"assign_{move_id}"):
                    st.session_state['assign_move'] = move_id
                    st.session_state['page'] = 'assignment'
    else:
        st.success("✅ All moves assigned")
    
    # Active Moves Progress (no financial data)
    st.markdown("---")
    st.markdown("## 📊 Active Move Progress")
    
    cursor.execute('''SELECT move_id, driver_name, delivery_location, status
                     FROM moves
                     WHERE status IN ('assigned', 'in_progress')
                     ORDER BY move_date
                     LIMIT 10''')
    
    active = cursor.fetchall()
    
    if active:
        for move in active:
            move_id, driver, location, status = move
            
            progress = 33 if status == 'assigned' else 66
            
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**{move_id}** - {driver}")
            with col2:
                st.caption(f"→ {location}")
            with col3:
                st.caption(status.upper())
            
            st.progress(progress / 100)
    
    conn.close()

# Function to be integrated into main app
def display_dashboard():
    """Main function to display appropriate dashboard"""
    role = st.session_state.get('user_role', 'viewer')
    show_interactive_dashboard(role)