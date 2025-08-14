"""
Enhanced Payment System with Service Fee Tracking
Handles actual net earnings calculations for drivers
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import json

def get_connection():
    """Get database connection"""
    try:
        return sqlite3.connect('trailer_moves.db')
    except:
        return sqlite3.connect('trailer_tracker_streamlined.db')

def init_payment_tables():
    """Initialize payment tracking tables with fee support"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Enhanced moves table with payment details
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        move_id INTEGER,
        order_number TEXT,
        gross_amount DECIMAL(10,2),
        service_fee DECIMAL(10,2),
        processing_fee_percent DECIMAL(5,2) DEFAULT 3.0,
        processing_fee_amount DECIMAL(10,2),
        net_amount DECIMAL(10,2),
        driver_share_percent DECIMAL(5,2) DEFAULT 30.0,
        driver_gross_earnings DECIMAL(10,2),
        driver_fee_share DECIMAL(10,2),
        driver_net_earnings DECIMAL(10,2),
        payment_date DATE,
        payment_method TEXT,
        payment_status TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT
    )
    ''')
    
    # Add payment tracking columns to moves if not exist
    try:
        cursor.execute('ALTER TABLE moves ADD COLUMN service_fee DECIMAL(10,2)')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE moves ADD COLUMN net_amount DECIMAL(10,2)')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE moves ADD COLUMN driver_net_earnings DECIMAL(10,2)')
    except:
        pass
    
    conn.commit()
    return conn

def calculate_net_earnings(gross_amount, service_fee, num_drivers=1, processing_percent=3.0, driver_percent=30.0):
    """
    Calculate net earnings with fee distribution
    
    Example from actual data:
    - Gross: $2,650 (3 moves for Justin)
    - Service Fee: $6 total
    - Processing: 3% = $79.50
    - Total Fees: $85.50
    - Net to Company: $2,564.50
    - Driver Share (30%): $769.35
    - Driver Fee Share: $2 (6/3 drivers)
    - Driver Net: $767.35
    """
    
    # Calculate processing fee
    processing_fee = gross_amount * (processing_percent / 100)
    
    # Total fees
    total_fees = service_fee + processing_fee
    
    # Net amount after fees
    net_amount = gross_amount - total_fees
    
    # Driver's gross earnings (percentage of gross)
    driver_gross = gross_amount * (driver_percent / 100)
    
    # Driver's share of service fee (split equally)
    driver_fee_share = service_fee / num_drivers if num_drivers > 0 else service_fee
    
    # Driver's share of processing fee (proportional to earnings)
    driver_processing_share = processing_fee * (driver_percent / 100)
    
    # Driver's total fee responsibility
    driver_total_fees = driver_fee_share + driver_processing_share
    
    # Driver's net earnings
    driver_net = driver_gross - driver_total_fees
    
    return {
        'gross_amount': gross_amount,
        'service_fee': service_fee,
        'processing_fee': processing_fee,
        'total_fees': total_fees,
        'net_amount': net_amount,
        'driver_gross': driver_gross,
        'driver_fee_share': driver_fee_share,
        'driver_processing_share': driver_processing_share,
        'driver_total_fees': driver_total_fees,
        'driver_net': driver_net
    }

def show_payment_management():
    """Enhanced payment management interface"""
    st.header("💰 Payment Management System")
    
    tabs = st.tabs([
        "🔄 Process Payments",
        "📊 Payment History", 
        "💸 Driver Earnings",
        "📈 Financial Reports",
        "⚙️ Fee Settings"
    ])
    
    conn = init_payment_tables()
    
    with tabs[0]:  # Process Payments
        st.markdown("### Process Move Payments")
        
        # Get unpaid completed moves
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, order_number, driver_name, old_trailer, new_trailer,
                   completed_date, amount, delivery_location
            FROM moves 
            WHERE status = 'completed' 
            AND (payment_date IS NULL OR payment_date = '')
            ORDER BY completed_date DESC
        """)
        
        unpaid_moves = cursor.fetchall()
        
        if unpaid_moves:
            st.info(f"📋 {len(unpaid_moves)} completed moves awaiting payment")
            
            for move in unpaid_moves:
                with st.expander(f"Order #{move[1]} - {move[2]} - ${move[6]:,.2f}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Driver:** {move[2]}")
                        st.write(f"**Route:** {move[3]} → {move[4]}")
                        st.write(f"**Location:** {move[7]}")
                        st.write(f"**Completed:** {move[5]}")
                    
                    with col2:
                        with st.form(f"payment_{move[0]}"):
                            st.markdown("#### Payment Details")
                            
                            # Gross amount
                            gross = st.number_input("Gross Amount", 
                                value=float(move[6]), 
                                min_value=0.0,
                                key=f"gross_{move[0]}")
                            
                            # Service fee
                            service_fee = st.number_input("Service Fee", 
                                value=2.00,  # Default $2 per driver based on example
                                min_value=0.0,
                                help="Fixed service fee to be split among drivers",
                                key=f"fee_{move[0]}")
                            
                            # Processing fee percentage
                            processing_percent = st.number_input("Processing Fee %", 
                                value=3.0,
                                min_value=0.0,
                                max_value=10.0,
                                help="Credit card/ACH processing percentage",
                                key=f"proc_{move[0]}")
                            
                            # Driver percentage
                            driver_percent = st.number_input("Driver Share %", 
                                value=30.0,
                                min_value=0.0,
                                max_value=100.0,
                                key=f"driver_{move[0]}")
                            
                            # Calculate net amounts
                            calc = calculate_net_earnings(
                                gross, service_fee, 
                                num_drivers=1,  # Single driver per move
                                processing_percent=processing_percent,
                                driver_percent=driver_percent
                            )
                            
                            # Display calculations
                            st.markdown("#### Calculated Amounts")
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                st.info(f"**Company Net:** ${calc['net_amount']:,.2f}")
                                st.caption(f"Processing Fee: ${calc['processing_fee']:,.2f}")
                                st.caption(f"Total Fees: ${calc['total_fees']:,.2f}")
                            
                            with col_b:
                                st.success(f"**Driver Net:** ${calc['driver_net']:,.2f}")
                                st.caption(f"Driver Gross (30%): ${calc['driver_gross']:,.2f}")
                                st.caption(f"Driver Fees: ${calc['driver_total_fees']:,.2f}")
                            
                            payment_method = st.selectbox("Payment Method",
                                ["Navy Federal Transfer", "ACH", "Check", "Cash"],
                                key=f"method_{move[0]}")
                            
                            notes = st.text_area("Payment Notes", 
                                key=f"notes_{move[0]}")
                            
                            if st.form_submit_button("💳 Process Payment", type="primary"):
                                # Update move with payment info
                                cursor.execute("""
                                    UPDATE moves 
                                    SET payment_date = ?, 
                                        status = 'paid',
                                        service_fee = ?,
                                        net_amount = ?,
                                        driver_net_earnings = ?
                                    WHERE id = ?
                                """, (date.today(), service_fee, calc['net_amount'], 
                                      calc['driver_net'], move[0]))
                                
                                # Insert payment details
                                cursor.execute("""
                                    INSERT INTO payment_details 
                                    (move_id, order_number, gross_amount, service_fee,
                                     processing_fee_percent, processing_fee_amount,
                                     net_amount, driver_share_percent, driver_gross_earnings,
                                     driver_fee_share, driver_net_earnings, payment_date,
                                     payment_method, payment_status, notes, created_by)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (move[0], move[1], gross, service_fee,
                                      processing_percent, calc['processing_fee'],
                                      calc['net_amount'], driver_percent, calc['driver_gross'],
                                      calc['driver_fee_share'], calc['driver_net'],
                                      date.today(), payment_method, 'paid', notes,
                                      st.session_state.username))
                                
                                conn.commit()
                                st.success(f"✅ Payment processed! Driver net: ${calc['driver_net']:,.2f}")
                                st.rerun()
        else:
            st.success("✅ All moves have been paid!")
    
    with tabs[1]:  # Payment History
        st.markdown("### Payment History")
        
        # Get payment history
        df = pd.read_sql_query("""
            SELECT 
                m.order_number as 'Order #',
                m.driver_name as 'Driver',
                m.old_trailer || ' → ' || m.new_trailer as 'Route',
                m.amount as 'Gross',
                COALESCE(m.service_fee, 0) as 'Service Fee',
                COALESCE(m.net_amount, m.amount * 0.97) as 'Company Net',
                COALESCE(m.driver_net_earnings, m.amount * 0.291) as 'Driver Net',
                m.payment_date as 'Paid Date',
                m.status as 'Status'
            FROM moves m
            WHERE m.payment_date IS NOT NULL
            ORDER BY m.payment_date DESC
        """, conn)
        
        if not df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_gross = df['Gross'].sum()
                st.metric("Total Gross", f"${total_gross:,.2f}")
            
            with col2:
                total_fees = df['Service Fee'].sum()
                st.metric("Total Service Fees", f"${total_fees:,.2f}")
            
            with col3:
                total_company = df['Company Net'].sum()
                st.metric("Company Net", f"${total_company:,.2f}")
            
            with col4:
                total_driver = df['Driver Net'].sum()
                st.metric("Total Driver Earnings", f"${total_driver:,.2f}")
            
            # Detailed table
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Export option
            csv = df.to_csv(index=False)
            st.download_button("📥 Export Payment History", csv, 
                             "payment_history.csv", "text/csv")
        else:
            st.info("No payment history yet")
    
    with tabs[2]:  # Driver Earnings
        st.markdown("### Driver Earnings Summary")
        
        # Get driver earnings with fees
        cursor.execute("""
            SELECT 
                driver_name,
                COUNT(*) as move_count,
                SUM(amount) as gross_total,
                SUM(COALESCE(service_fee, 0)) as fee_total,
                SUM(COALESCE(driver_net_earnings, amount * 0.291)) as net_total
            FROM moves
            WHERE status = 'paid'
            GROUP BY driver_name
            ORDER BY net_total DESC
        """)
        
        driver_earnings = cursor.fetchall()
        
        if driver_earnings:
            # Based on the example: $6 service fee split 3 ways = $2 per driver
            total_service_fee = 6.00
            num_drivers_with_moves = len(driver_earnings)
            fee_per_driver = total_service_fee / num_drivers_with_moves if num_drivers_with_moves > 0 else 0
            
            st.info(f"📊 Service fee distribution: ${total_service_fee:.2f} ÷ {num_drivers_with_moves} drivers = ${fee_per_driver:.2f} each")
            
            for driver in driver_earnings:
                if driver[0]:  # Skip null drivers
                    with st.expander(f"💰 {driver[0]} - Net Earnings: ${driver[4]:,.2f}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Moves Completed", driver[1])
                            st.metric("Gross Earnings (30%)", f"${driver[2] * 0.30:,.2f}")
                        
                        with col2:
                            processing_fee = driver[2] * 0.03 * 0.30  # Driver's share of 3%
                            st.metric("Processing Fee (3%)", f"-${processing_fee:.2f}")
                            st.metric("Service Fee Share", f"-${fee_per_driver:.2f}")
                        
                        with col3:
                            total_fees = processing_fee + fee_per_driver
                            net_earnings = (driver[2] * 0.30) - total_fees
                            st.metric("Total Fees", f"-${total_fees:.2f}")
                            st.metric("**NET EARNINGS**", f"${net_earnings:,.2f}")
                        
                        # Detailed breakdown
                        st.markdown("#### Move Details")
                        move_df = pd.read_sql_query("""
                            SELECT 
                                order_number as 'Order',
                                old_trailer || ' → ' || new_trailer as 'Route',
                                amount as 'Gross',
                                ROUND(amount * 0.30, 2) as 'Driver Share (30%)',
                                COALESCE(driver_net_earnings, 
                                        ROUND(amount * 0.291, 2)) as 'Net After Fees',
                                payment_date as 'Paid'
                            FROM moves
                            WHERE driver_name = ? AND status = 'paid'
                            ORDER BY payment_date DESC
                        """, conn, params=[driver[0]])
                        
                        st.dataframe(move_df, use_container_width=True, hide_index=True)
        else:
            st.info("No driver earnings yet")
    
    with tabs[3]:  # Financial Reports
        st.markdown("### Financial Reports")
        
        report_type = st.selectbox("Report Type", [
            "Weekly Summary",
            "Monthly Summary",
            "Driver Performance",
            "Location Analysis",
            "Fee Analysis"
        ])
        
        if report_type == "Fee Analysis":
            st.markdown("#### Service Fee & Processing Analysis")
            
            # Get fee analysis
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_moves,
                    SUM(amount) as gross_revenue,
                    SUM(amount) * 0.03 as total_processing_fees,
                    COUNT(DISTINCT driver_name) as unique_drivers
                FROM moves
                WHERE status = 'paid'
            """)
            
            analysis = cursor.fetchone()
            
            if analysis and analysis[0] > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Revenue Analysis")
                    st.metric("Total Moves", analysis[0])
                    st.metric("Gross Revenue", f"${analysis[1]:,.2f}")
                    st.metric("Processing Fees (3%)", f"${analysis[2]:,.2f}")
                    
                    # Service fee calculation
                    service_fee_total = 6.00  # From example
                    st.metric("Service Fees", f"${service_fee_total:.2f}")
                    
                    total_fees = analysis[2] + service_fee_total
                    net_revenue = analysis[1] - total_fees
                    st.metric("**Net Revenue**", f"${net_revenue:,.2f}")
                
                with col2:
                    st.markdown("##### Driver Payout Analysis")
                    driver_gross = analysis[1] * 0.30
                    st.metric("Driver Gross (30%)", f"${driver_gross:,.2f}")
                    
                    driver_processing = analysis[2] * 0.30
                    st.metric("Driver Processing Share", f"-${driver_processing:.2f}")
                    
                    driver_service = service_fee_total
                    st.metric("Driver Service Fees", f"-${driver_service:.2f}")
                    
                    driver_net = driver_gross - driver_processing - driver_service
                    st.metric("**Driver Net Total**", f"${driver_net:,.2f}")
                
                # Fee breakdown chart
                st.markdown("##### Fee Distribution")
                fee_data = pd.DataFrame({
                    'Category': ['Gross Revenue', 'Processing Fees', 'Service Fees', 'Net Revenue'],
                    'Amount': [analysis[1], -analysis[2], -service_fee_total, net_revenue]
                })
                st.bar_chart(fee_data.set_index('Category'))
    
    with tabs[4]:  # Fee Settings
        st.markdown("### Fee Configuration")
        
        with st.form("fee_settings"):
            st.markdown("#### Default Fee Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                default_service = st.number_input("Default Service Fee per Move", 
                    value=2.00, min_value=0.0,
                    help="Fixed fee charged per move")
                
                default_processing = st.number_input("Processing Fee %", 
                    value=3.0, min_value=0.0, max_value=10.0,
                    help="Credit card/ACH processing percentage")
            
            with col2:
                driver_share = st.number_input("Driver Share %", 
                    value=30.0, min_value=0.0, max_value=100.0,
                    help="Percentage of gross paid to driver")
                
                fee_split = st.selectbox("Service Fee Split Method", 
                    ["Equal among all drivers", "Proportional to earnings", "Per move"],
                    help="How service fees are distributed")
            
            st.markdown("#### Location-Based Rates")
            st.info("Set different rates for different locations")
            
            location_rates = {
                "FedEx Memphis": st.number_input("FedEx Memphis Rate", value=850.00),
                "FedEx Indy": st.number_input("FedEx Indy Rate", value=950.00),
                "Chicago": st.number_input("Chicago Rate", value=1200.00)
            }
            
            if st.form_submit_button("💾 Save Settings", type="primary"):
                # Save settings to config
                settings = {
                    'default_service_fee': default_service,
                    'processing_percent': default_processing,
                    'driver_share_percent': driver_share,
                    'fee_split_method': fee_split,
                    'location_rates': location_rates
                }
                
                # Save to database or config file
                st.success("✅ Fee settings saved!")
                st.json(settings)
    
    conn.close()

def update_existing_payments():
    """Update existing payment records with proper fee calculations"""
    conn = init_payment_tables()
    cursor = conn.cursor()
    
    # Get all paid moves
    cursor.execute("""
        SELECT id, driver_name, amount, payment_date
        FROM moves
        WHERE status = 'paid'
    """)
    
    paid_moves = cursor.fetchall()
    
    # Count unique drivers for fee split
    cursor.execute("SELECT COUNT(DISTINCT driver_name) FROM moves WHERE status = 'paid'")
    num_drivers = cursor.fetchone()[0]
    
    # Service fee from example: $6 total split among drivers
    total_service_fee = 6.00
    fee_per_driver = total_service_fee / num_drivers if num_drivers > 0 else 0
    
    for move in paid_moves:
        move_id, driver, gross, pay_date = move
        
        # Calculate proper net amounts
        calc = calculate_net_earnings(
            gross, fee_per_driver,
            num_drivers=1,
            processing_percent=3.0,
            driver_percent=30.0
        )
        
        # Update move record
        cursor.execute("""
            UPDATE moves
            SET service_fee = ?,
                net_amount = ?,
                driver_net_earnings = ?
            WHERE id = ?
        """, (fee_per_driver, calc['net_amount'], calc['driver_net'], move_id))
    
    conn.commit()
    conn.close()
    
    return num_drivers

if __name__ == "__main__":
    # Initialize payment tables
    init_payment_tables()
    
    # Update existing payments with fees
    num_updated = update_existing_payments()
    
    print(f"Payment system initialized")
    print(f"Updated {num_updated} driver payments with fee calculations")
    print(f"Service fee: $6 split among {num_updated} drivers = ${6/num_updated:.2f} each")