"""
Manager Payment Entry System
Manager enters gross payment for each driver
System calculates net after factoring and service fees
"""

import streamlit as st
import sqlite3
from datetime import datetime
from typing import Dict, List

class ManagerPaymentEntry:
    """
    Correct Workflow:
    1. Manager selects moves to process
    2. Manager enters GROSS amount for EACH driver
    3. Manager enters total service fee from factoring company
    4. System automatically calculates:
       - 3% factoring fee on each driver's gross
       - Service fee split among drivers
       - Net payment for each driver
    """
    
    FACTORING_RATE = 0.03
    
    def __init__(self):
        self.conn = sqlite3.connect('trailers.db')
        self.cursor = self.conn.cursor()
    
    def get_pending_moves_by_driver(self):
        """Get pending moves grouped by driver"""
        self.cursor.execute('''
            SELECT driver_name, GROUP_CONCAT(move_id), COUNT(*), 
                   GROUP_CONCAT(pickup_location || ' → ' || delivery_location)
            FROM moves 
            WHERE payment_status = 'pending' OR payment_status IS NULL
            GROUP BY driver_name
            ORDER BY driver_name
        ''')
        return self.cursor.fetchall()
    
    def get_detailed_moves(self, driver_name):
        """Get detailed moves for a specific driver"""
        self.cursor.execute('''
            SELECT move_id, old_trailer, new_trailer, pickup_location, 
                   delivery_location, created_date
            FROM moves 
            WHERE driver_name = ? AND (payment_status = 'pending' OR payment_status IS NULL)
            ORDER BY created_date
        '''), (driver_name,)
        return self.cursor.fetchall()
    
    def calculate_driver_payment(self, gross_amount: float, service_fee_share: float):
        """
        Calculate net payment for a driver
        
        Args:
            gross_amount: Gross amount driver earned
            service_fee_share: Driver's share of the service fee
        
        Returns:
            Payment breakdown for the driver
        """
        factoring_fee = gross_amount * self.FACTORING_RATE
        net_payment = gross_amount - factoring_fee - service_fee_share
        
        return {
            'gross_amount': gross_amount,
            'factoring_fee': factoring_fee,
            'service_fee_share': service_fee_share,
            'net_payment': net_payment
        }
    
    def save_payment_batch(self, driver_payments: Dict, total_service_fee: float, payment_date: str = None):
        """
        Save payment batch to database
        
        Args:
            driver_payments: {driver_name: {'gross': amount, 'moves': [move_ids]}}
            total_service_fee: Total service fee from factoring company
            payment_date: Date of payment
        """
        if not payment_date:
            payment_date = datetime.now().strftime('%Y-%m-%d')
        
        # Generate batch ID
        batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate totals
        total_gross = sum(d['gross'] for d in driver_payments.values())
        total_factoring = total_gross * self.FACTORING_RATE
        num_drivers = len(driver_payments)
        service_fee_per_driver = total_service_fee / num_drivers if num_drivers > 0 else 0
        
        # Save submission record
        self.cursor.execute('''
            INSERT INTO submissions (submission_id, client_payment, factoring_fee, 
                                   service_fee, num_drivers, submission_date, payment_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (batch_id, total_gross, total_factoring, total_service_fee, num_drivers,
              datetime.now().strftime('%Y-%m-%d'), payment_date, 'processed'))
        
        # Process each driver
        for driver_name, data in driver_payments.items():
            gross = data['gross']
            moves = data['moves']
            
            # Calculate payment
            payment = self.calculate_driver_payment(gross, service_fee_per_driver)
            
            # Update moves
            for move_id in moves:
                self.cursor.execute('''
                    UPDATE moves 
                    SET payment_status = 'paid',
                        payment_date = ?,
                        actual_client_payment = ?,
                        driver_pay = ?,
                        factoring_fee = ?,
                        service_fee = ?
                    WHERE move_id = ?
                ''', (payment_date, gross/len(moves), payment['net_payment']/len(moves),
                      payment['factoring_fee']/len(moves), service_fee_per_driver/len(moves), move_id))
            
            # Create payment record
            self.cursor.execute('''
                INSERT INTO payments (driver_name, payment_date, amount, service_fee, status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (driver_name, payment_date, payment['net_payment'], service_fee_per_driver,
                  'processed', f"Batch {batch_id}: {len(moves)} moves - Gross: ${gross:.2f}"))
        
        self.conn.commit()
        return batch_id
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def show_manager_payment_interface():
    """Streamlit interface for manager payment entry"""
    st.header("💰 Manager Payment Entry")
    st.info("Enter the gross amount for each driver. The system will calculate net payments after fees.")
    
    payment_system = ManagerPaymentEntry()
    
    # Get pending moves by driver
    driver_moves = payment_system.get_pending_moves_by_driver()
    
    if not driver_moves:
        st.warning("No pending moves to process")
        payment_system.close()
        return
    
    # Initialize session state for driver payments
    if 'driver_payments' not in st.session_state:
        st.session_state.driver_payments = {}
    
    # Payment date and service fee
    col1, col2 = st.columns(2)
    with col1:
        payment_date = st.date_input("Payment Date", value=datetime.now())
    with col2:
        total_service_fee = st.number_input(
            "Total Service Fee (from factoring)",
            min_value=0.0,
            value=6.00,
            step=1.0,
            help="Total service fee to be split among drivers"
        )
    
    st.divider()
    
    # Driver payment entry section
    st.subheader("👥 Enter Gross Payments by Driver")
    
    num_drivers = len(driver_moves)
    service_fee_per_driver = total_service_fee / num_drivers if num_drivers > 0 else 0
    
    st.info(f"Service fee will be split: ${service_fee_per_driver:.2f} per driver")
    
    driver_data = {}
    total_gross = 0
    total_net = 0
    
    for driver_name, move_ids_str, move_count, routes_str in driver_moves:
        move_ids = move_ids_str.split(',')
        routes = routes_str.split(',')
        
        with st.expander(f"💼 {driver_name} - {move_count} moves", expanded=True):
            # Show move details
            st.markdown("**Moves to be paid:**")
            for i, route in enumerate(routes[:5]):  # Show first 5 routes
                st.markdown(f"  • {route}")
            if len(routes) > 5:
                st.markdown(f"  • ... and {len(routes)-5} more")
            
            # Gross payment input
            col1, col2 = st.columns(2)
            
            with col1:
                # Provide guidance on typical rates
                if "Memphis" in routes_str and "Chicago" in routes_str:
                    suggested = 2373.00
                elif "Memphis" in routes_str and "Indy" in routes_str:
                    suggested = 1960.00 * move_count
                elif "FedEx Memphis" in routes_str and "Fleet Memphis" in routes_str:
                    suggested = 200.00 * move_count
                else:
                    suggested = 0.0
                
                gross = st.number_input(
                    f"Gross Payment for {driver_name}",
                    min_value=0.0,
                    value=suggested,
                    step=100.0,
                    key=f"gross_{driver_name}",
                    help=f"Enter the total gross amount for {move_count} moves"
                )
            
            with col2:
                if gross > 0:
                    # Calculate and display net
                    payment = payment_system.calculate_driver_payment(gross, service_fee_per_driver)
                    
                    st.markdown("**Payment Breakdown:**")
                    st.markdown(f"Gross: ${gross:,.2f}")
                    st.markdown(f"Factoring (3%): -${payment['factoring_fee']:,.2f}")
                    st.markdown(f"Service Fee: -${service_fee_per_driver:.2f}")
                    st.markdown(f"**NET: ${payment['net_payment']:,.2f}**")
                    
                    driver_data[driver_name] = {
                        'gross': gross,
                        'moves': move_ids,
                        'net': payment['net_payment']
                    }
                    
                    total_gross += gross
                    total_net += payment['net_payment']
    
    # Summary section
    if driver_data:
        st.divider()
        st.subheader("📊 Payment Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Gross", f"${total_gross:,.2f}")
        with col2:
            total_factoring = total_gross * 0.03
            st.metric("Total Factoring (3%)", f"-${total_factoring:,.2f}")
        with col3:
            st.metric("Total Service Fee", f"-${total_service_fee:.2f}")
        with col4:
            st.metric("Total Net to Drivers", f"${total_net:,.2f}")
        
        # Verification - using your example
        st.divider()
        
        # Example verification
        with st.expander("📋 Verify Against Example", expanded=False):
            st.markdown("""
            **Example from your data:**
            - Justin: Gross $2,360 → Net $2,287.20
            - Carl: Gross $1,960 → Net $1,899.20
            - Brandon: Gross $2,373 → Net $2,299.81
            - Total: $6,693 gross, $6 service fee split 3 ways
            """)
        
        # Save button
        if st.button("💾 Process Payments", type="primary", disabled=len(driver_data) == 0):
            batch_id = payment_system.save_payment_batch(
                driver_data,
                total_service_fee,
                payment_date.strftime('%Y-%m-%d')
            )
            st.success(f"✅ Payment batch {batch_id} processed successfully!")
            st.balloons()
            
            # Show final breakdown
            st.markdown("### Final Payments Processed:")
            for driver, data in driver_data.items():
                st.markdown(f"**{driver}**: Gross ${data['gross']:,.2f} → Net ${data['net']:,.2f}")
            
            # Clear session state
            if 'driver_payments' in st.session_state:
                del st.session_state['driver_payments']
            
            # Rerun to refresh
            st.rerun()
    
    payment_system.close()


# Test the calculation with your example
def test_payment_calculation():
    """Test with your exact numbers"""
    system = ManagerPaymentEntry()
    
    print("TEST WITH YOUR EXACT DATA")
    print("=" * 70)
    
    # Your data
    drivers = [
        ("Justin Duckett", 2360.00, 3),  # 3 moves total
        ("Carl Strikland", 1960.00, 1),  # 1 move
        ("Brandon Smith", 2373.00, 1),   # 1 move
    ]
    
    total_service_fee = 6.00
    num_drivers = len(drivers)
    service_fee_per_driver = total_service_fee / num_drivers
    
    print(f"Total Service Fee: ${total_service_fee:.2f}")
    print(f"Service Fee per Driver: ${service_fee_per_driver:.2f}")
    print("-" * 70)
    
    for driver_name, gross, moves in drivers:
        payment = system.calculate_driver_payment(gross, service_fee_per_driver)
        
        print(f"\n{driver_name} ({moves} moves):")
        print(f"  Gross Amount: ${gross:,.2f}")
        print(f"  Factoring Fee (3%): -${payment['factoring_fee']:.2f}")
        print(f"  Service Fee Share: -${payment['service_fee_share']:.2f}")
        print(f"  NET PAYMENT: ${payment['net_payment']:.2f}")
        
        # Verify against your expected values
        expected = {
            "Justin Duckett": 2287.20,
            "Carl Strikland": 1899.20,
            "Brandon Smith": 2299.81
        }
        
        if driver_name in expected:
            match = abs(payment['net_payment'] - expected[driver_name]) < 0.01
            print(f"  Expected: ${expected[driver_name]:.2f} - {'✓ MATCH' if match else '✗ MISMATCH'}")
    
    system.close()


if __name__ == "__main__":
    # Run test
    test_payment_calculation()
    
    print("\n" + "=" * 70)
    print("To use in Streamlit, import and call: show_manager_payment_interface()")