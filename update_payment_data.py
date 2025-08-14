"""
Update existing data with correct payment calculations
Based on the new payment workflow understanding
"""

import sqlite3
from enhanced_payment_system import EnhancedPaymentSystem

def update_payment_data():
    conn = sqlite3.connect('trailers.db')
    cursor = conn.cursor()
    payment_system = EnhancedPaymentSystem()
    
    print("UPDATING PAYMENT DATA WITH CORRECT CALCULATIONS")
    print("=" * 60)
    
    # Clear and recreate moves with proper data
    cursor.execute("DELETE FROM moves")
    cursor.execute("DELETE FROM payments")
    
    # Based on the original data provided, these were the FINAL amounts after fees
    # So we need to work backwards to get the client payment amounts
    
    moves_data = [
        # Justin's moves on 8/09 - Local Memphis moves (10 miles each)
        {
            'move_id': 'MOV-001',
            'pickup': 'FedEx Memphis',
            'delivery': 'Fleet Memphis', 
            'driver': 'Justin Duckett',
            'date': '2025-08-09',
            'miles': 10,
            'status': 'completed',
            'paid_date': '2025-08-13'
        },
        {
            'move_id': 'MOV-002',
            'pickup': 'FedEx Memphis',
            'delivery': 'Fleet Memphis',
            'driver': 'Justin Duckett', 
            'date': '2025-08-09',
            'miles': 10,
            'status': 'completed',
            'paid_date': '2025-08-13'
        },
        # Brandon's Chicago run - 530 miles
        {
            'move_id': 'MOV-003',
            'pickup': 'Memphis',
            'delivery': 'Chicago',
            'driver': 'Brandon Smith',
            'date': '2025-08-11',
            'miles': 530,
            'status': 'completed', 
            'paid_date': '2025-08-13'
        },
        # Justin's Indy run - 280 miles
        {
            'move_id': 'MOV-004',
            'pickup': 'Memphis',
            'delivery': 'FedEx Indy',
            'driver': 'Justin Duckett',
            'date': '2025-08-11',
            'miles': 280,
            'status': 'completed',
            'paid_date': '2025-08-13'
        },
        # Carl's Indy run - 280 miles
        {
            'move_id': 'MOV-005',
            'pickup': 'Memphis',
            'delivery': 'FedEx Indy',
            'driver': 'Carl Strikland',
            'date': '2025-08-11',
            'miles': 280,
            'status': 'completed',
            'paid_date': '2025-08-13'
        },
        # Brandon's current in-progress move
        {
            'move_id': 'MOV-006',
            'pickup': 'Memphis',
            'delivery': 'FedEx Indy',
            'driver': 'Brandon Smith',
            'date': '2025-08-13',
            'miles': 280,
            'status': 'in_progress',
            'paid_date': None
        }
    ]
    
    for move in moves_data:
        # Calculate payments
        if move['status'] == 'completed':
            # For completed moves, calculate actual payment
            gross_earnings = move['miles'] * 2.10
            payment = payment_system.calculate_actual_payment(gross_earnings, 6.00, 1)
            
            cursor.execute('''
                INSERT INTO moves (move_id, pickup_location, delivery_location, driver_name,
                                 status, created_date, total_miles, estimated_miles,
                                 actual_client_payment, driver_pay, factoring_fee, 
                                 service_fee, payment_status, payment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (move['move_id'], move['pickup'], move['delivery'], move['driver'],
                  move['status'], move['date'], move['miles'], move['miles'],
                  gross_earnings, payment['net_per_driver'], payment['factoring_fee'],
                  payment['service_fee'], 'finalized', move['paid_date']))
            
            # Add payment record
            cursor.execute('''
                INSERT INTO payments (driver_name, payment_date, amount, service_fee, 
                                    miles, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (move['driver'], move['paid_date'], payment['net_per_driver'], 
                  payment['service_fee'], move['miles'], 'paid',
                  f"{move['pickup']} to {move['delivery']}"))
            
            print(f"Updated {move['move_id']}: {move['driver']} - ${payment['net_per_driver']:,.2f}")
            
        else:
            # For in-progress moves, calculate estimated payment
            payment = payment_system.calculate_estimated_payment(move['miles'], 1)
            
            cursor.execute('''
                INSERT INTO moves (move_id, pickup_location, delivery_location, driver_name,
                                 status, created_date, total_miles, estimated_miles,
                                 driver_pay, factoring_fee, service_fee, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (move['move_id'], move['pickup'], move['delivery'], move['driver'],
                  move['status'], move['date'], move['miles'], move['miles'],
                  payment['net_per_driver'], payment['factoring_fee'], 
                  payment['service_fee'], 'estimated'))
            
            print(f"Estimated {move['move_id']}: {move['driver']} - ${payment['net_per_driver']:,.2f}")
    
    # Calculate and show driver totals
    print("\n" + "=" * 60)
    print("DRIVER PAYMENT SUMMARY")
    print("=" * 60)
    
    cursor.execute('''
        SELECT driver_name, COUNT(*) as move_count, SUM(driver_pay) as total_pay
        FROM moves
        WHERE status = 'completed'
        GROUP BY driver_name
    ''')
    
    for driver, count, total in cursor.fetchall():
        print(f"{driver}: {count} moves - Total: ${total:,.2f}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("PAYMENT DATA UPDATE COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    update_payment_data()