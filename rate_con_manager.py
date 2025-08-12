"""
Rate Confirmation Management System
Handles Rate Con uploads, matching, and verification
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os
import base64
import hashlib

def init_rate_con_tables():
    """Initialize Rate Con related database tables"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    # Add Rate Con fields to moves table
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN mlbl_number TEXT")
    except:
        pass  # Column may already exist
    
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN rate_con_number TEXT")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN rate_con_status TEXT DEFAULT 'pending'")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN client_miles REAL")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN client_rate REAL")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN client_total REAL")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN miles_delta REAL")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE moves ADD COLUMN delta_percentage REAL")
    except:
        pass
    
    # Create Rate Cons table with BOL support (one per move)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_cons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mlbl_number TEXT,
            rate_con_number TEXT,
            client_name TEXT,
            client_miles REAL,
            client_rate REAL,
            client_total REAL,
            factoring_fee REAL,
            driver_net REAL,
            rate_con_file_path TEXT,
            bol_file_path TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            matched_to_move_id INTEGER UNIQUE,
            matched_date TIMESTAMP,
            matched_by TEXT,
            status TEXT DEFAULT 'unmatched',
            notes TEXT,
            FOREIGN KEY (matched_to_move_id) REFERENCES moves(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def upload_rate_con(mlbl_number, client_miles, client_rate, client_total, rate_con_file=None, bol_file=None, notes=""):
    """Upload a new Rate Con with BOL to the system (one per move)"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    # Calculate driver net (after 3% factoring fee)
    factoring_fee = client_total * 0.03
    driver_net = client_total - factoring_fee
    
    # Save Rate Con file if provided
    rate_con_path = None
    if rate_con_file:
        os.makedirs('rate_cons', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Use timestamp as primary identifier if no MLBL
        file_prefix = mlbl_number.replace('/', '_').replace('\\', '_') if mlbl_number else f"RC_{timestamp}"
        rate_con_path = f"rate_cons/{file_prefix}_rate_con.pdf"
        with open(rate_con_path, 'wb') as f:
            f.write(rate_con_file.getbuffer() if hasattr(rate_con_file, 'getbuffer') else rate_con_file)
    
    # Save BOL file if provided
    bol_path = None
    if bol_file:
        os.makedirs('rate_cons/bol', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_prefix = mlbl_number.replace('/', '_').replace('\\', '_') if mlbl_number else f"BOL_{timestamp}"
        bol_path = f"rate_cons/bol/{file_prefix}_bol.pdf"
        with open(bol_path, 'wb') as f:
            f.write(bol_file.getbuffer() if hasattr(bol_file, 'getbuffer') else bol_file)
    
    try:
        cursor.execute('''
            INSERT INTO rate_cons (mlbl_number, client_miles, client_rate, client_total, 
                                   factoring_fee, driver_net, rate_con_file_path, bol_file_path, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unmatched')
        ''', (mlbl_number if mlbl_number else None, client_miles, client_rate, client_total, 
              factoring_fee, driver_net, rate_con_path, bol_path, notes))
        
        conn.commit()
        rate_con_id = cursor.lastrowid
        conn.close()
        return rate_con_id
    except Exception as e:
        conn.close()
        print(f"Error uploading rate con: {e}")
        return None

def get_unmatched_rate_cons():
    """Get all unmatched Rate Cons"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    query = """
        SELECT id, mlbl_number, client_miles, client_rate, client_total, 
               factoring_fee, driver_net, upload_date, notes,
               rate_con_file_path, bol_file_path
        FROM rate_cons
        WHERE status = 'unmatched'
        ORDER BY upload_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_moves_without_rate_cons():
    """Get all moves that don't have Rate Cons attached"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    query = """
        SELECT id, new_trailer, old_trailer, pickup_location, delivery_location,
               driver_name, move_date, total_miles, driver_pay, status, mlbl_number
        FROM moves
        WHERE rate_con_status IS NULL OR rate_con_status = 'pending'
        ORDER BY move_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def match_rate_con_to_move(rate_con_id, move_id, matched_by):
    """Match a Rate Con to a Move"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    # Get Rate Con details
    cursor.execute("""
        SELECT mlbl_number, client_miles, client_rate, client_total
        FROM rate_cons WHERE id = ?
    """, (rate_con_id,))
    rate_con = cursor.fetchone()
    
    if rate_con:
        mlbl_number, client_miles, client_rate, client_total = rate_con
        
        # Update the Rate Con
        cursor.execute("""
            UPDATE rate_cons
            SET matched_to_move_id = ?, 
                matched_date = CURRENT_TIMESTAMP,
                matched_by = ?,
                status = 'matched'
            WHERE id = ?
        """, (move_id, matched_by, rate_con_id))
        
        # Get our calculated miles for the move
        cursor.execute("SELECT total_miles FROM moves WHERE id = ?", (move_id,))
        our_miles = cursor.fetchone()[0] or 0
        
        # Calculate delta
        miles_delta = client_miles - our_miles if client_miles and our_miles else 0
        delta_percentage = (miles_delta / our_miles * 100) if our_miles > 0 else 0
        
        # Update the Move with Rate Con info
        cursor.execute("""
            UPDATE moves
            SET mlbl_number = ?,
                rate_con_status = 'matched',
                client_miles = ?,
                client_rate = ?,
                client_total = ?,
                miles_delta = ?,
                delta_percentage = ?
            WHERE id = ?
        """, (mlbl_number, client_miles, client_rate, client_total, 
              miles_delta, delta_percentage, move_id))
        
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def get_verification_dashboard_data():
    """Get data for verification dashboard"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    query = """
        SELECT m.id, m.new_trailer, m.old_trailer, m.driver_name,
               m.mlbl_number, m.move_date,
               m.total_miles as our_miles, 
               m.client_miles,
               m.client_rate,
               m.client_total,
               m.miles_delta,
               m.delta_percentage,
               m.rate_con_status,
               r.upload_date as rate_con_received
        FROM moves m
        LEFT JOIN rate_cons r ON r.matched_to_move_id = m.id
        WHERE m.rate_con_status = 'matched'
        ORDER BY m.move_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def show_rate_con_management():
    """Main Rate Con Management Interface"""
    st.title("📄 Rate Confirmation Management")
    
    # Initialize tables
    init_rate_con_tables()
    
    tabs = st.tabs(["📥 Inbox", "🔄 Match Rate Cons", "✅ Verification Dashboard", "📊 Analytics"])
    
    with tabs[0]:  # Inbox
        show_rate_con_inbox()
    
    with tabs[1]:  # Matching
        show_rate_con_matching()
    
    with tabs[2]:  # Verification
        show_verification_dashboard()
    
    with tabs[3]:  # Analytics
        show_rate_con_analytics()

def update_rate_con_mlbl(rate_con_id, new_mlbl):
    """Update the MLBL number for an existing Rate Con"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE rate_cons 
        SET mlbl_number = ?
        WHERE id = ?
    """, (new_mlbl if new_mlbl else None, rate_con_id))
    
    # Also update the move if it's matched
    cursor.execute("""
        UPDATE moves 
        SET mlbl_number = ?
        WHERE id = (SELECT matched_to_move_id FROM rate_cons WHERE id = ?)
    """, (new_mlbl if new_mlbl else None, rate_con_id))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def show_rate_con_inbox():
    """Rate Con and BOL upload interface (one per move)"""
    st.markdown("### 📥 Rate Confirmation & BOL Inbox")
    st.info("💡 Each move has ONE Rate Con and ONE BOL. Upload both documents here.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 📄 Document Entry")
        
        # Input method selection (outside form for dynamic behavior)
        calc_method = st.radio("How to calculate?", 
                               ["Enter miles and rate", "Calculate from total amount"],
                               help="If miles aren't on Rate Con, calculate from total")
        
        with st.form("rate_con_entry", clear_on_submit=True):
            mlbl = st.text_input("MLBL Number (Optional)", placeholder="MLBL-58064 or leave blank", help="Master Load Bill Number - can be added/changed later")
            
            col_a, col_b = st.columns(2)
            
            if calc_method == "Enter miles and rate":
                with col_a:
                    client_miles = st.number_input("Client Miles", min_value=0.0, step=1.0)
                    client_rate = st.number_input("Rate per Mile ($)", min_value=0.0, step=0.01, value=2.10)
                
                with col_b:
                    # Auto-calculate total
                    if client_miles > 0 and client_rate > 0:
                        client_total = client_miles * client_rate
                        st.markdown(f"**Total Amount**")
                        st.markdown(f"<p style='font-size: 1.2rem; margin: 0;'>${client_total:.2f}</p>", unsafe_allow_html=True)
                    else:
                        client_total = 0.0
                        st.markdown(f"**Total Amount**")
                        st.markdown(f"<p style='font-size: 1.2rem; margin: 0;'>$0.00</p>", unsafe_allow_html=True)
                    
                    # Show factoring calculation
                    if client_total > 0:
                        factoring_fee = client_total * 0.03
                        driver_net = client_total - factoring_fee
                        st.markdown(f"<p style='font-size: 0.9rem; color: #4CAF50; margin-top: 10px;'>Driver Net: ${driver_net:.2f}<br>(After 3% factoring)</p>", unsafe_allow_html=True)
            else:
                # Calculate from total amount
                with col_a:
                    client_total = st.number_input("Total Amount ($)", min_value=0.0, step=0.01,
                                                   help="Enter the gross amount from Rate Con")
                    client_rate = st.number_input("Rate per Mile ($)", min_value=0.0, step=0.01, value=2.10,
                                                  help="Standard rate to calculate miles")
                
                with col_b:
                    # Auto-calculate miles with live preview
                    st.markdown("**📊 Live Preview**")
                    if client_total > 0 and client_rate > 0:
                        client_miles = client_total / client_rate
                        # Enhanced preview box
                        st.info(f"""
                        **Calculated Miles:** {client_miles:.1f} miles
                        
                        **Calculation:** ${client_total:.2f} ÷ ${client_rate:.2f}/mile
                        """)
                        
                        # Show factoring calculation
                        factoring_fee = client_total * 0.03
                        driver_net = client_total - factoring_fee
                        st.success(f"""
                        **Driver Net:** ${driver_net:.2f}
                        **Factoring (3%):** -${factoring_fee:.2f}
                        """)
                    else:
                        client_miles = 0.0
                        st.info("Enter amount and rate to see preview")
            
            # File uploads
            st.markdown("**📎 Attach Documents**")
            rate_con_file = st.file_uploader("Rate Confirmation", type=['pdf', 'png', 'jpg', 'jpeg'], key="rc_file")
            bol_file = st.file_uploader("Bill of Lading (BOL)", type=['pdf', 'png', 'jpg', 'jpeg'], key="bol_file")
            
            notes = st.text_area("Notes", placeholder="Any special notes")
            
            if st.form_submit_button("➕ Add Documents", type="primary", use_container_width=True):
                # Validate based on calculation method
                if calc_method == "Calculate from total amount":
                    if client_total > 0:
                        # Ensure we have valid values
                        if client_rate == 0:
                            client_rate = 2.10  # Use default if not specified
                        if client_miles == 0:
                            client_miles = client_total / client_rate
                    else:
                        st.error("Please enter the total amount")
                        st.stop()
                else:
                    # Regular validation for miles and rate method
                    if client_miles == 0 or client_rate == 0:
                        st.error("Please enter miles and rate")
                        st.stop()
                    if client_total == 0:
                        client_total = client_miles * client_rate
                
                # Upload the Rate Con
                if client_total > 0:
                    rate_con_id = upload_rate_con(mlbl if mlbl else "", client_miles, client_rate, client_total, 
                                                   rate_con_file, bol_file, notes)
                    if rate_con_id:
                        display_name = mlbl if mlbl else f"Rate Con #{rate_con_id}"
                        st.success(f"✅ {display_name} added successfully!")
                        if calc_method == "Calculate from total amount":
                            st.info(f"📊 Calculated: {client_miles:.1f} miles @ ${client_rate:.2f}/mile = ${client_total:.2f}")
                        if rate_con_file:
                            st.success("📄 Rate Con uploaded")
                        if bol_file:
                            st.success("📋 BOL uploaded")
                        st.rerun()
                    else:
                        st.error(f"Error adding Rate Con")
                else:
                    st.error("Please fill in required fields")
    
    with col2:
        st.markdown("#### Unmatched Rate Cons")
        unmatched_df = get_unmatched_rate_cons()
        
        if not unmatched_df.empty:
            for _, rate_con in unmatched_df.iterrows():
                display_name = rate_con['mlbl_number'] if rate_con['mlbl_number'] else f"Rate Con #{rate_con['id']}"
                with st.expander(f"📄 {display_name} - ${rate_con['client_total']:.2f}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"**Miles:** {rate_con['client_miles']:.0f}")
                        st.write(f"**Rate:** ${rate_con['client_rate']:.2f}/mi")
                        st.write(f"**Total:** ${rate_con['client_total']:.2f}")
                        st.write(f"**Driver Net:** ${rate_con['driver_net']:.2f}")
                    with col2:
                        st.write(f"**Uploaded:** {rate_con['upload_date']}")
                        if rate_con['notes']:
                            st.write(f"**Notes:** {rate_con['notes']}")
                        # Edit MLBL
                        new_mlbl = st.text_input(f"MLBL", value=rate_con['mlbl_number'] if rate_con['mlbl_number'] else "", 
                                                  key=f"mlbl_edit_{rate_con['id']}", placeholder="Enter MLBL")
                        if st.button("Update MLBL", key=f"update_mlbl_{rate_con['id']}"):
                            if update_rate_con_mlbl(rate_con['id'], new_mlbl):
                                st.success("MLBL updated!")
                                st.rerun()
                    with col3:
                        # Quick match button
                        if st.button(f"Match", key=f"match_{rate_con['id']}"):
                            st.session_state[f'matching_rate_con'] = rate_con['id']
                            st.info("Go to Match tab")
        else:
            st.success("✅ All Rate Cons have been matched!")

def show_rate_con_matching():
    """Interface for matching Rate Cons to Moves (1:1 relationship)"""
    st.markdown("### 🔄 Match Rate Confirmations to Moves")
    st.info("📌 Each move has exactly ONE Rate Con and ONE BOL")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📥 Unmatched Rate Cons")
        unmatched_rate_cons = get_unmatched_rate_cons()
        if not unmatched_rate_cons.empty:
            # Create display names for Rate Cons
            rate_con_options = []
            for _, rc in unmatched_rate_cons.iterrows():
                display_name = rc['mlbl_number'] if rc['mlbl_number'] else f"Rate Con #{rc['id']}"
                rate_con_options.append((rc['id'], f"{display_name} - ${rc['client_total']:.2f}"))
            
            selected_option = st.selectbox(
                "Select Rate Con",
                [opt for _, opt in rate_con_options],
                key="rate_con_selector"
            )
            
            # Get the selected Rate Con ID
            selected_rate_con = None
            for rc_id, display in rate_con_options:
                if display == selected_option:
                    selected_rate_con = rc_id
                    break
            
            if selected_rate_con:
                rate_con_data = unmatched_rate_cons[unmatched_rate_cons['id']==selected_rate_con].iloc[0]
                display_name = rate_con_data['mlbl_number'] if rate_con_data['mlbl_number'] else f"Rate Con #{selected_rate_con}"
                st.info(f"**Selected:** {display_name}")
                st.write(f"Miles: {rate_con_data['client_miles']:.0f} @ ${rate_con_data['client_rate']:.2f} = ${rate_con_data['client_total']:.2f}")
                st.caption(f"Driver Net: ${rate_con_data['driver_net']:.2f} (after 3% factoring)")
        else:
            st.success("✅ No unmatched Rate Cons")
            selected_rate_con = None
    
    with col2:
        st.markdown("#### 🚛 Moves Without Rate Cons")
        moves_without_rc = get_moves_without_rate_cons()
        if not moves_without_rc.empty:
            # Format move display with addresses for matching
            move_options = []
            for _, move in moves_without_rc.iterrows():
                move_desc = f"Move #{move['id']} - {move['new_trailer']}/{move['old_trailer']} - {move['driver_name']} - {move['pickup_location']} to {move['delivery_location']} - {move['move_date']}"
                move_options.append((move['id'], move_desc))
            
            selected_move_desc = st.selectbox(
                "Select Move to Match (check addresses)",
                [desc for _, desc in move_options],
                key="move_selector",
                help="Match based on pickup/delivery addresses"
            )
            
            # Get the selected move ID
            selected_move_id = None
            for move_id, desc in move_options:
                if desc == selected_move_desc:
                    selected_move_id = move_id
                    break
            
            if selected_move_id:
                move_data = moves_without_rc[moves_without_rc['id']==selected_move_id].iloc[0]
                st.info(f"**Selected Move #{selected_move_id}**")
                st.write(f"📍 {move_data['pickup_location']} → {move_data['delivery_location']}")
                st.write(f"Our Miles: {move_data['total_miles']:.0f}")
                st.write(f"Driver Pay: ${move_data['driver_pay']:.2f}")
        else:
            st.success("✅ All moves have Rate Cons!")
            selected_move_id = None
    
    # Match button
    if selected_rate_con and selected_move_id:
        st.divider()
        st.markdown("### 🔗 Confirm Match")
        st.warning("⚠️ Once matched, a move cannot have another Rate Con attached")
        if st.button("✅ Confirm Match", type="primary", use_container_width=True):
            # Perform matching (selected_rate_con is already the ID)
            if match_rate_con_to_move(selected_rate_con, selected_move_id, st.session_state.get('user_name', 'Admin')):
                st.success(f"✅ Matched Rate Con #{selected_rate_con} to Move #{selected_move_id}")
                st.balloons()
                st.rerun()
            else:
                st.error("Failed to match Rate Con to Move (may already have a Rate Con)")

def show_verification_dashboard():
    """Dashboard showing rate verification and deltas"""
    st.markdown("### ✅ Rate Verification Dashboard")
    
    # Get verification data
    verification_df = get_verification_dashboard_data()
    
    if verification_df.empty:
        st.info("No matched Rate Cons to verify yet")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_moves = len(verification_df)
        st.metric("Total Verified", total_moves)
    
    with col2:
        avg_delta = verification_df['delta_percentage'].mean()
        st.metric("Avg Delta", f"{avg_delta:.1f}%")
    
    with col3:
        flagged = len(verification_df[abs(verification_df['delta_percentage']) > 5])
        st.metric("Flagged (>5%)", flagged, delta=None if flagged == 0 else f"+{flagged}")
    
    with col4:
        total_client = verification_df['client_total'].sum()
        st.metric("Total Billing", f"${total_client:,.2f}")
    
    st.divider()
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        delta_filter = st.selectbox(
            "Filter by Delta",
            ["All", "Green (≤2%)", "Yellow (2-5%)", "Red (>5%)"]
        )
    
    with col2:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            key="date_filter"
        )
    
    with col3:
        driver_filter = st.selectbox(
            "Filter by Driver",
            ["All"] + verification_df['driver_name'].unique().tolist()
        )
    
    # Apply filters
    filtered_df = verification_df.copy()
    
    if delta_filter == "Green (≤2%)":
        filtered_df = filtered_df[abs(filtered_df['delta_percentage']) <= 2]
    elif delta_filter == "Yellow (2-5%)":
        filtered_df = filtered_df[(abs(filtered_df['delta_percentage']) > 2) & (abs(filtered_df['delta_percentage']) <= 5)]
    elif delta_filter == "Red (>5%)":
        filtered_df = filtered_df[abs(filtered_df['delta_percentage']) > 5]
    
    if driver_filter != "All":
        filtered_df = filtered_df[filtered_df['driver_name'] == driver_filter]
    
    # Display results
    st.markdown("#### Verification Details")
    
    for _, row in filtered_df.iterrows():
        # Determine status color
        delta_pct = abs(row['delta_percentage'])
        if delta_pct <= 2:
            status_color = "🟢"
            container = st.success
        elif delta_pct <= 5:
            status_color = "🟡"
            container = st.warning
        else:
            status_color = "🔴"
            container = st.error
        
        with st.expander(f"{status_color} Move #{row['id']} | {row['mlbl_number']} | Delta: {row['delta_percentage']:.1f}%"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Move Details**")
                st.write(f"Date: {row['move_date']}")
                st.write(f"Driver: {row['driver_name']}")
                st.write(f"Trailers: {row['new_trailer']}/{row['old_trailer']}")
            
            with col2:
                st.markdown("**Client Rate Con**")
                st.write(f"Miles: {row['client_miles']:.0f}")
                st.write(f"Rate: ${row['client_rate']:.2f}")
                st.write(f"Total: ${row['client_total']:.2f}")
            
            with col3:
                st.markdown("**Our Calculation**")
                st.write(f"Miles: {row['our_miles']:.0f}")
                st.write(f"Delta: {row['miles_delta']:.0f} mi ({row['delta_percentage']:.1f}%)")
                
                if delta_pct > 5:
                    if st.button(f"🚩 Flag for Review", key=f"flag_{row['id']}"):
                        st.warning("Flagged for review")

def show_rate_con_analytics():
    """Analytics and reporting for Rate Cons"""
    st.markdown("### 📊 Rate Confirmation Analytics")
    
    verification_df = get_verification_dashboard_data()
    
    if verification_df.empty:
        st.info("No data available for analytics yet")
        return
    
    # Time period selector
    period = st.selectbox("Select Period", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])
    
    # Filter by period
    if period == "Last 7 Days":
        cutoff = datetime.now() - timedelta(days=7)
    elif period == "Last 30 Days":
        cutoff = datetime.now() - timedelta(days=30)
    elif period == "Last 90 Days":
        cutoff = datetime.now() - timedelta(days=90)
    else:
        cutoff = datetime.min
    
    # Convert move_date to datetime if it's not already
    verification_df['move_date'] = pd.to_datetime(verification_df['move_date'])
    filtered_df = verification_df[verification_df['move_date'] >= cutoff]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Moves", len(filtered_df))
        st.metric("Total Billed", f"${filtered_df['client_total'].sum():,.2f}")
    
    with col2:
        avg_client_miles = filtered_df['client_miles'].mean()
        avg_our_miles = filtered_df['our_miles'].mean()
        st.metric("Avg Client Miles", f"{avg_client_miles:.0f}")
        st.metric("Avg Our Miles", f"{avg_our_miles:.0f}")
    
    with col3:
        perfect_matches = len(filtered_df[filtered_df['miles_delta'] == 0])
        st.metric("Perfect Matches", perfect_matches)
        st.metric("Match Rate", f"{(perfect_matches/len(filtered_df)*100):.1f}%")
    
    with col4:
        disputes = len(filtered_df[abs(filtered_df['delta_percentage']) > 5])
        st.metric("Potential Disputes", disputes)
        st.metric("Dispute Rate", f"{(disputes/len(filtered_df)*100):.1f}%")
    
    # Charts
    st.divider()
    
    # Delta distribution
    st.markdown("#### Mileage Delta Distribution")
    delta_bins = pd.cut(filtered_df['delta_percentage'], 
                        bins=[-100, -5, -2, 2, 5, 100],
                        labels=['< -5%', '-5% to -2%', '-2% to 2%', '2% to 5%', '> 5%'])
    
    delta_counts = delta_bins.value_counts().sort_index()
    
    # Create a simple bar chart representation
    for label, count in delta_counts.items():
        bar_length = int(count / len(filtered_df) * 50)
        bar = "█" * bar_length
        st.write(f"{label}: {bar} {count} ({count/len(filtered_df)*100:.1f}%)")
    
    # Top discrepancies
    st.divider()
    st.markdown("#### Top Discrepancies (Require Review)")
    
    top_discrepancies = filtered_df.nlargest(5, 'delta_percentage')[
        ['id', 'mlbl_number', 'driver_name', 'client_miles', 'our_miles', 'miles_delta', 'delta_percentage']
    ]
    
    if not top_discrepancies.empty:
        for _, row in top_discrepancies.iterrows():
            st.warning(
                f"Move #{row['id']} | {row['mlbl_number']} | "
                f"Client: {row['client_miles']:.0f} mi | "
                f"Our: {row['our_miles']:.0f} mi | "
                f"Delta: {row['miles_delta']:.0f} mi ({row['delta_percentage']:.1f}%)"
            )

def show_driver_rate_cons(driver_name):
    """Show Rate Cons for a specific driver with net pay after factoring"""
    st.title(f"💰 Your Rate Confirmations")
    st.markdown(f"**Driver:** {driver_name}")
    
    # Get driver's Rate Cons
    rate_cons_df = get_driver_rate_cons(driver_name)
    
    if rate_cons_df.empty:
        st.info("No Rate Confirmations available yet.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_moves = len(rate_cons_df)
        st.metric("Total Moves", total_moves)
    
    with col2:
        total_gross = rate_cons_df['client_total'].sum()
        st.metric("Gross Pay", f"${total_gross:,.2f}")
    
    with col3:
        total_factoring = rate_cons_df['factoring_fee'].sum()
        st.metric("Factoring Fees (3%)", f"${total_factoring:,.2f}")
    
    with col4:
        total_net = rate_cons_df['driver_net'].sum()
        st.metric("**NET PAY**", f"${total_net:,.2f}", delta=f"-${total_factoring:.2f}")
    
    st.divider()
    
    # Show individual Rate Cons
    st.markdown("### 📋 Your Completed Moves")
    
    for _, row in rate_cons_df.iterrows():
        with st.expander(f"📄 {row['mlbl_number']} - {row['move_date']} - NET: ${row['driver_net']:.2f}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Move Details**")
                st.write(f"Date: {row['move_date']}")
                st.write(f"New Trailer: {row['new_trailer']}")
                st.write(f"Old Trailer: {row['old_trailer']}")
                st.write(f"From: {row['pickup_location']}")
                st.write(f"To: {row['delivery_location']}")
            
            with col2:
                st.markdown("**Rate Information**")
                st.write(f"Client Miles: {row['client_miles']:.0f}")
                st.write(f"Rate/Mile: ${row['client_rate']:.2f}")
                st.write(f"Gross Total: ${row['client_total']:.2f}")
                st.write(f"Factoring (3%): -${row['factoring_fee']:.2f}")
                st.success(f"**Your Net Pay: ${row['driver_net']:.2f}**")
            
            with col3:
                st.markdown("**Documents**")
                if row.get('rate_con_file_path'):
                    if st.button(f"📄 View Rate Con", key=f"rc_{row['move_id']}"):
                        try:
                            with open(row['rate_con_file_path'], 'rb') as f:
                                st.download_button(
                                    "⬇️ Download Rate Con",
                                    data=f.read(),
                                    file_name=f"rate_con_{row['mlbl_number']}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_rc_{row['move_id']}"
                                )
                        except:
                            st.error("Rate Con file not found")
                else:
                    st.caption("No Rate Con uploaded")
                
                if row.get('bol_file_path'):
                    if st.button(f"📋 View BOL", key=f"bol_{row['move_id']}"):
                        try:
                            with open(row['bol_file_path'], 'rb') as f:
                                st.download_button(
                                    "⬇️ Download BOL",
                                    data=f.read(),
                                    file_name=f"bol_{row['mlbl_number']}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_bol_{row['move_id']}"
                                )
                        except:
                            st.error("BOL file not found")
                else:
                    st.caption("No BOL uploaded")
    
    # Payment summary at bottom
    st.divider()
    st.markdown("### 💳 Payment Summary")
    st.info(
        f"**Total Gross Pay:** ${rate_cons_df['client_total'].sum():,.2f}\n\n"
        f"**Total Factoring Fees (3%):** -${rate_cons_df['factoring_fee'].sum():,.2f}\n\n"
        f"**TOTAL NET PAY:** ${rate_cons_df['driver_net'].sum():,.2f}"
    )

def get_driver_rate_cons(driver_name):
    """Get all Rate Cons for a specific driver showing net pay"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    query = """
        SELECT 
            m.id as move_id,
            m.new_trailer,
            m.old_trailer,
            m.pickup_location,
            m.delivery_location,
            m.move_date,
            r.mlbl_number,
            r.client_miles,
            r.client_rate,
            r.client_total,
            r.factoring_fee,
            r.driver_net,
            r.rate_con_file_path,
            r.bol_file_path
        FROM moves m
        INNER JOIN rate_cons r ON r.matched_to_move_id = m.id
        WHERE m.driver_name = ?
        ORDER BY m.move_date DESC
    """
    df = pd.read_sql_query(query, conn, params=(driver_name,))
    conn.close()
    return df

# Export function for use in main app
def add_rate_con_to_menu():
    """Add Rate Con management to navigation menu"""
    return "📄 Rate Cons"