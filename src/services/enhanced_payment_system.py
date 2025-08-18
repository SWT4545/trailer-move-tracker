"""
Enhanced Payment System
Handles both estimated payments (from Google Maps mileage) and actual payments (from client)
"""

import sqlite3
from datetime import datetime

class EnhancedPaymentSystem:
    FACTORING_FEE_RATE = 0.03  # 3% factoring fee
    BASE_RATE_PER_MILE = 2.10  # $2.10 per mile
    DEFAULT_SERVICE_FEE = 6.00  # Default service fee per submission
    
    def __init__(self, db_path='trailers.db'):
        self.db_path = db_path
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Ensure database has proper schema for payment tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add new columns to moves table if they don't exist
        try:
            cursor.execute('''ALTER TABLE moves ADD COLUMN estimated_miles REAL''')
        except:
            pass
        
        try:
            cursor.execute('''ALTER TABLE moves ADD COLUMN actual_client_payment REAL''')
        except:
            pass
        
        try:
            cursor.execute('''ALTER TABLE moves ADD COLUMN factoring_fee REAL''')
        except:
            pass
        
        try:
            cursor.execute('''ALTER TABLE moves ADD COLUMN service_fee REAL''')
        except:
            pass
        
        try:
            cursor.execute('''ALTER TABLE moves ADD COLUMN payment_status TEXT DEFAULT 'estimated' ''')
        except:
            pass
        
        conn.commit()
        conn.close()
    
    def calculate_estimated_payment(self, miles, num_drivers=1):
        """
        Calculate estimated payment based on Google Maps mileage
        
        Args:
            miles: Miles from Google Maps
            num_drivers: Number of drivers on this move
            
        Returns:
            Payment breakdown dictionary
        """
        # Step 1: Calculate gross earnings based on mileage
        gross_earnings = miles * self.BASE_RATE_PER_MILE
        
        # Step 2: Apply 3% factoring fee
        factoring_fee = gross_earnings * self.FACTORING_FEE_RATE
        
        # Step 3: Estimate service fee (using default)
        service_fee = self.DEFAULT_SERVICE_FEE
        
        # Step 4: Calculate net
        total_fees = factoring_fee + service_fee
        net_payment = gross_earnings - total_fees
        
        # Step 5: Split among drivers if needed
        net_per_driver = net_payment / num_drivers
        service_fee_per_driver = service_fee / num_drivers
        
        return {
            'payment_type': 'ESTIMATED',
            'miles': miles,
            'rate_per_mile': self.BASE_RATE_PER_MILE,
            'gross_earnings': gross_earnings,
            'factoring_fee': factoring_fee,
            'factoring_rate': self.FACTORING_FEE_RATE,
            'service_fee': service_fee,
            'total_fees': total_fees,
            'net_payment': net_payment,
            'num_drivers': num_drivers,
            'net_per_driver': net_per_driver,
            'service_fee_per_driver': service_fee_per_driver
        }
    
    def calculate_actual_payment(self, client_payment, actual_service_fee, num_drivers=1):
        """
        Calculate actual payment when client payment is received
        
        Args:
            client_payment: Actual payment from client
            actual_service_fee: Actual service fee from factoring company
            num_drivers: Number of drivers on this move
            
        Returns:
            Payment breakdown dictionary
        """
        # Step 1: Apply 3% factoring fee to client payment
        factoring_fee = client_payment * self.FACTORING_FEE_RATE
        
        # Step 2: Deduct all fees
        total_fees = factoring_fee + actual_service_fee
        net_payment = client_payment - total_fees
        
        # Step 3: Split among drivers
        net_per_driver = net_payment / num_drivers
        service_fee_per_driver = actual_service_fee / num_drivers
        
        # Step 4: Back-calculate implied miles
        implied_miles = client_payment / self.BASE_RATE_PER_MILE
        
        return {
            'payment_type': 'ACTUAL',
            'client_payment': client_payment,
            'implied_miles': round(implied_miles, 1),
            'rate_per_mile': self.BASE_RATE_PER_MILE,
            'factoring_fee': factoring_fee,
            'factoring_rate': self.FACTORING_FEE_RATE,
            'service_fee': actual_service_fee,
            'total_fees': total_fees,
            'net_payment': net_payment,
            'num_drivers': num_drivers,
            'net_per_driver': net_per_driver,
            'service_fee_per_driver': service_fee_per_driver
        }
    
    def update_move_with_estimated_payment(self, move_id, miles):
        """
        Update a move with estimated payment based on Google Maps mileage
        
        Args:
            move_id: Move identifier
            miles: Miles from Google Maps
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get number of drivers for this move
        cursor.execute("SELECT driver_name FROM moves WHERE move_id = ?", (move_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None
        
        # Calculate estimated payment
        payment = self.calculate_estimated_payment(miles)
        
        # Update move record
        cursor.execute('''
            UPDATE moves 
            SET estimated_miles = ?,
                total_miles = ?,
                driver_pay = ?,
                factoring_fee = ?,
                service_fee = ?,
                payment_status = 'estimated'
            WHERE move_id = ?
        ''', (miles, miles, payment['net_per_driver'], 
              payment['factoring_fee'], payment['service_fee'], move_id))
        
        conn.commit()
        conn.close()
        
        return payment
    
    def update_move_with_actual_payment(self, move_id, client_payment, actual_service_fee):
        """
        Update a move with actual payment from client
        
        Args:
            move_id: Move identifier
            client_payment: Actual payment received from client
            actual_service_fee: Actual service fee from factoring company
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get move details
        cursor.execute("SELECT driver_name, estimated_miles FROM moves WHERE move_id = ?", (move_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None
        
        # Calculate actual payment
        payment = self.calculate_actual_payment(client_payment, actual_service_fee)
        
        # Update move record
        cursor.execute('''
            UPDATE moves 
            SET actual_client_payment = ?,
                driver_pay = ?,
                factoring_fee = ?,
                service_fee = ?,
                payment_status = 'finalized',
                payment_date = ?
            WHERE move_id = ?
        ''', (client_payment, payment['net_per_driver'], 
              payment['factoring_fee'], actual_service_fee, 
              datetime.now().strftime('%Y-%m-%d'), move_id))
        
        conn.commit()
        conn.close()
        
        return payment
    
    def format_payment_display(self, payment_data):
        """Format payment data for display"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"PAYMENT BREAKDOWN - {payment_data['payment_type']}")
        lines.append("=" * 60)
        
        if payment_data['payment_type'] == 'ESTIMATED':
            lines.append(f"Miles (from Google Maps): {payment_data['miles']}")
            lines.append(f"Rate per Mile: ${payment_data['rate_per_mile']}")
            lines.append(f"Gross Earnings: ${payment_data['gross_earnings']:,.2f}")
        else:
            lines.append(f"Client Payment: ${payment_data['client_payment']:,.2f}")
            lines.append(f"Implied Miles: {payment_data['implied_miles']}")
        
        lines.append(f"\nFees:")
        lines.append(f"  Factoring Fee (3%): ${payment_data['factoring_fee']:,.2f}")
        lines.append(f"  Service Fee: ${payment_data['service_fee']:,.2f}")
        lines.append(f"  Total Fees: ${payment_data['total_fees']:,.2f}")
        
        lines.append(f"\nNet Payment: ${payment_data['net_payment']:,.2f}")
        
        if payment_data['num_drivers'] > 1:
            lines.append(f"\nSplit among {payment_data['num_drivers']} drivers:")
            lines.append(f"  Net per Driver: ${payment_data['net_per_driver']:,.2f}")
            lines.append(f"  Service Fee per Driver: ${payment_data['service_fee_per_driver']:,.2f}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


# Integration with Streamlit app
def show_payment_management():
    """Streamlit interface for payment management"""
    import streamlit as st
    
    st.header("💰 Payment Management")
    
    payment_system = EnhancedPaymentSystem()
    
    tab1, tab2, tab3 = st.tabs(["Calculate Estimate", "Enter Actual Payment", "View Payments"])
    
    with tab1:
        st.subheader("Calculate Estimated Payment")
        st.info("Use Google Maps mileage to estimate driver payment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            miles = st.number_input("Miles (from Google Maps)", min_value=0.0, step=1.0)
            num_drivers = st.number_input("Number of Drivers", min_value=1, value=1)
        
        with col2:
            if st.button("Calculate Estimate", type="primary"):
                if miles > 0:
                    payment = payment_system.calculate_estimated_payment(miles, num_drivers)
                    st.code(payment_system.format_payment_display(payment))
                    
                    # Show breakdown
                    st.metric("Estimated Net per Driver", f"${payment['net_per_driver']:,.2f}")
    
    with tab2:
        st.subheader("Enter Actual Payment")
        st.info("Enter actual payment received from client")
        
        # Get pending moves
        conn = sqlite3.connect('trailers.db')
        cursor = conn.cursor()
        cursor.execute("SELECT move_id, driver_name, estimated_miles FROM moves WHERE payment_status = 'estimated' OR payment_status IS NULL")
        moves = cursor.fetchall()
        conn.close()
        
        if moves:
            move_options = [f"{m[0]} - {m[1]} ({m[2]} miles est.)" if m[2] else f"{m[0]} - {m[1]}" for m in moves]
            selected_move = st.selectbox("Select Move", move_options)
            move_id = selected_move.split(" - ")[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                client_payment = st.number_input("Client Payment Amount", min_value=0.0, step=100.0)
                
            with col2:
                service_fee = st.number_input("Actual Service Fee", min_value=0.0, value=6.0, step=1.0)
            
            if st.button("Update Payment", type="primary"):
                if client_payment > 0:
                    payment = payment_system.update_move_with_actual_payment(move_id, client_payment, service_fee)
                    if payment:
                        st.success("Payment updated successfully!")
                        st.code(payment_system.format_payment_display(payment))
        else:
            st.info("No pending payments to process")
    
    with tab3:
        st.subheader("Payment History")
        
        conn = sqlite3.connect('trailers.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT move_id, driver_name, estimated_miles, actual_client_payment, 
                   driver_pay, payment_status, payment_date
            FROM moves 
            WHERE driver_pay IS NOT NULL
            ORDER BY payment_date DESC
        ''')
        payments = cursor.fetchall()
        conn.close()
        
        if payments:
            for payment in payments:
                move_id, driver, est_miles, client_pay, driver_pay, status, date = payment
                
                with st.expander(f"{move_id} - {driver} - {status or 'Pending'}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Estimated Miles:** {est_miles or 'N/A'}")
                        st.markdown(f"**Client Payment:** ${client_pay:,.2f}" if client_pay else "**Client Payment:** Pending")
                        
                    with col2:
                        st.markdown(f"**Driver Pay:** ${driver_pay:,.2f}" if driver_pay else "**Driver Pay:** Calculating...")
                        st.markdown(f"**Payment Date:** {date or 'Pending'}")
        else:
            st.info("No payment history available")


if __name__ == "__main__":
    # Test the system
    system = EnhancedPaymentSystem()
    
    print("TEST 1: Estimated Payment (Google Maps Mileage)")
    print("-" * 60)
    estimated = system.calculate_estimated_payment(miles=280, num_drivers=1)
    print(system.format_payment_display(estimated))
    
    print("\nTEST 2: Actual Payment (Client Payment Received)")
    print("-" * 60)
    actual = system.calculate_actual_payment(client_payment=588.00, actual_service_fee=6.00, num_drivers=1)
    print(system.format_payment_display(actual))
    
    print("\nTEST 3: Multiple Drivers")
    print("-" * 60)
    multi = system.calculate_actual_payment(client_payment=6693.00, actual_service_fee=6.00, num_drivers=3)
    print(system.format_payment_display(multi))