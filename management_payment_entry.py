"""
Management Payment Entry System
Allows management to enter total client payment and service fee
System automatically calculates individual driver payments
"""

import streamlit as st
import sqlite3
from datetime import datetime
from typing import Dict, List

class ManagementPaymentEntry:
    """
    Workflow:
    1. Manager selects moves to process as a batch
    2. Manager enters total amount client paid for the batch
    3. Manager enters service fee from factoring company
    4. System automatically calculates:
       - 3% factoring fee on total
       - Individual driver payments based on route rates
       - Service fee split among drivers
    """
    
    FACTORING_RATE = 0.03
    
    # Standard route rates (what each route is worth)
    ROUTE_RATES = {
        ('FedEx Memphis', 'Fleet Memphis'): 200.00,
        ('Memphis', 'FedEx Indy'): 1960.00,
        ('Memphis', 'Chicago'): 2373.00,
        ('FedEx Indy', 'Memphis'): 1960.00,
        ('Chicago', 'Memphis'): 2373.00,
    }
    
    def __init__(self):
        self.conn = sqlite3.connect('trailers.db')
        self.cursor = self.conn.cursor()
    
    def get_pending_moves(self):
        """Get all moves pending payment"""
        self.cursor.execute('''
            SELECT move_id, driver_name, pickup_location, delivery_location, 
                   old_trailer, new_trailer, created_date
            FROM moves 
            WHERE payment_status = 'pending' OR payment_status IS NULL
            ORDER BY created_date
        ''')
        return self.cursor.fetchall()
    
    def calculate_payment_breakdown(self, moves: List, total_client_payment: float, service_fee: float):
        """
        Calculate how to distribute payment among drivers
        
        Args:
            moves: List of move records
            total_client_payment: Total amount client paid
            service_fee: Service fee from factoring company
        
        Returns:
            Detailed payment breakdown
        """
        # Calculate factoring fee
        factoring_fee = total_client_payment * self.FACTORING_RATE
        
        # Group moves by driver and calculate base amounts
        driver_moves = {}
        total_base_amount = 0
        
        for move in moves:
            move_id, driver, pickup, delivery, old_trailer, new_trailer, date = move
            
            # Get route rate
            route_key = (pickup, delivery)
            route_rate = self.ROUTE_RATES.get(route_key, 0)
            
            if route_rate == 0:
                # Try reverse route
                route_key = (delivery, pickup)
                route_rate = self.ROUTE_RATES.get(route_key, 0)
            
            if driver not in driver_moves:
                driver_moves[driver] = {
                    'moves': [],
                    'base_amount': 0,
                    'routes': []
                }
            
            driver_moves[driver]['moves'].append(move_id)
            driver_moves[driver]['base_amount'] += route_rate
            driver_moves[driver]['routes'].append(f"{pickup} → {delivery} (${route_rate:.2f})")
            total_base_amount += route_rate
        
        # Verify total matches (or close)
        if abs(total_base_amount - total_client_payment) > 100:
            st.warning(f"⚠️ Expected total: ${total_base_amount:.2f}, Client paid: ${total_client_payment:.2f}")
        
        # Calculate proportional distribution if amounts don't match exactly
        adjustment_factor = total_client_payment / total_base_amount if total_base_amount > 0 else 1
        
        # Calculate final payments
        num_drivers = len(driver_moves)
        service_fee_per_driver = service_fee / num_drivers if num_drivers > 0 else 0
        
        results = {
            'total_client_payment': total_client_payment,
            'factoring_fee': factoring_fee,
            'service_fee': service_fee,
            'num_drivers': num_drivers,
            'service_fee_per_driver': service_fee_per_driver,
            'driver_payments': {}
        }
        
        for driver, data in driver_moves.items():
            # Adjust base amount proportionally
            adjusted_gross = data['base_amount'] * adjustment_factor
            
            # Calculate driver's share of factoring fee
            driver_factoring = adjusted_gross * self.FACTORING_RATE
            
            # Calculate net payment
            net_payment = adjusted_gross - driver_factoring - service_fee_per_driver
            
            results['driver_payments'][driver] = {
                'moves': data['moves'],
                'routes': data['routes'],
                'base_amount': data['base_amount'],
                'adjusted_gross': adjusted_gross,
                'factoring_fee': driver_factoring,
                'service_fee_share': service_fee_per_driver,
                'net_payment': net_payment
            }
        
        return results
    
    def save_payment_batch(self, breakdown: Dict, payment_date: str = None):
        """Save payment batch to database"""
        if not payment_date:
            payment_date = datetime.now().strftime('%Y-%m-%d')
        
        # Generate batch ID
        batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Save submission record
        self.cursor.execute('''
            INSERT INTO submissions (submission_id, client_payment, factoring_fee, 
                                   service_fee, num_drivers, submission_date, payment_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (batch_id, breakdown['total_client_payment'], breakdown['factoring_fee'],
              breakdown['service_fee'], breakdown['num_drivers'], 
              datetime.now().strftime('%Y-%m-%d'), payment_date, 'processed'))
        
        # Update moves and create payment records
        for driver, data in breakdown['driver_payments'].items():
            # Update each move
            for move_id in data['moves']:
                self.cursor.execute('''
                    UPDATE moves 
                    SET payment_status = 'paid',
                        payment_date = ?,
                        actual_client_payment = ?,
                        driver_pay = ?,
                        factoring_fee = ?,
                        service_fee = ?
                    WHERE move_id = ?
                ''', (payment_date, data['adjusted_gross'], data['net_payment'],
                      data['factoring_fee'], data['service_fee_share'], move_id))
            
            # Create payment record
            self.cursor.execute('''
                INSERT INTO payments (driver_name, payment_date, amount, service_fee, status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (driver, payment_date, data['net_payment'], data['service_fee_share'],
                  'processed', f"Batch {batch_id}: {len(data['moves'])} moves"))
        
        self.conn.commit()
        return batch_id
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def show_management_payment_interface():
    """Streamlit interface for management payment entry"""
    st.header("💰 Management Payment Entry")
    st.info("Enter the total amount received from client and service fee to calculate driver payments")
    
    payment_system = ManagementPaymentEntry()
    
    # Get pending moves
    pending_moves = payment_system.get_pending_moves()
    
    if not pending_moves:
        st.warning("No pending moves to process")
        payment_system.close()
        return
    
    # Display pending moves
    st.subheader("📋 Pending Moves")
    
    # Create checkboxes for move selection
    selected_moves = []
    move_display = []
    
    for move in pending_moves:
        move_id, driver, pickup, delivery, old_trailer, new_trailer, date = move
        display_text = f"{move_id}: {driver} - {pickup} → {delivery} ({old_trailer} → {new_trailer}) - {date}"
        
        if st.checkbox(display_text, key=move_id):
            selected_moves.append(move)
            move_display.append(display_text)
    
    if selected_moves:
        st.divider()
        st.subheader("💵 Payment Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate expected total based on routes
            expected_total = 0
            for move in selected_moves:
                pickup, delivery = move[2], move[3]
                route_key = (pickup, delivery)
                rate = payment_system.ROUTE_RATES.get(route_key, 0)
                if rate == 0:
                    rate = payment_system.ROUTE_RATES.get((delivery, pickup), 0)
                expected_total += rate
            
            st.info(f"Expected Total (based on routes): ${expected_total:,.2f}")
            
            total_payment = st.number_input(
                "Total Client Payment",
                min_value=0.0,
                value=expected_total,
                step=100.0,
                help="Enter the total amount the client paid for these moves"
            )
        
        with col2:
            service_fee = st.number_input(
                "Service Fee (from factoring company)",
                min_value=0.0,
                value=6.00,
                step=1.0,
                help="Enter the service fee charged by the factoring company"
            )
            
            payment_date = st.date_input(
                "Payment Date",
                value=datetime.now()
            )
        
        if st.button("Calculate Payment Breakdown", type="primary"):
            # Calculate breakdown
            breakdown = payment_system.calculate_payment_breakdown(
                selected_moves, total_payment, service_fee
            )
            
            # Display breakdown
            st.divider()
            st.subheader("📊 Payment Breakdown")
            
            # Summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Client Payment", f"${breakdown['total_client_payment']:,.2f}")
            with col2:
                st.metric("Factoring Fee (3%)", f"-${breakdown['factoring_fee']:,.2f}")
            with col3:
                st.metric("Service Fee", f"-${breakdown['service_fee']:.2f}")
            with col4:
                net_total = breakdown['total_client_payment'] - breakdown['factoring_fee'] - breakdown['service_fee']
                st.metric("Net to Drivers", f"${net_total:,.2f}")
            
            # Individual driver breakdowns
            st.divider()
            st.subheader("👥 Driver Payments")
            
            for driver, data in breakdown['driver_payments'].items():
                with st.expander(f"{driver} - Net: ${data['net_payment']:,.2f}"):
                    st.markdown("**Routes:**")
                    for route in data['routes']:
                        st.markdown(f"  • {route}")
                    
                    st.markdown("**Calculation:**")
                    st.markdown(f"  • Base Amount: ${data['base_amount']:,.2f}")
                    if abs(data['adjusted_gross'] - data['base_amount']) > 0.01:
                        st.markdown(f"  • Adjusted Gross: ${data['adjusted_gross']:,.2f}")
                    st.markdown(f"  • Factoring Fee: -${data['factoring_fee']:,.2f}")
                    st.markdown(f"  • Service Fee Share: -${data['service_fee_share']:.2f}")
                    st.markdown(f"  • **NET PAYMENT: ${data['net_payment']:,.2f}**")
            
            # Save button
            st.divider()
            if st.button("💾 Save and Process Payments", type="primary"):
                batch_id = payment_system.save_payment_batch(
                    breakdown, 
                    payment_date.strftime('%Y-%m-%d')
                )
                st.success(f"✅ Payment batch {batch_id} processed successfully!")
                st.balloons()
                
                # Generate receipts button
                if st.button("📄 Generate Driver Receipts"):
                    st.info("Receipt generation would happen here")
                
                # Rerun to refresh the page
                st.rerun()
    
    payment_system.close()


if __name__ == "__main__":
    import streamlit as st
    show_management_payment_interface()