"""
Update database with final correct payment data
"""

import sqlite3
from final_payment_system import FinalPaymentSystem
from datetime import datetime

def update_database_with_final_data():
    conn = sqlite3.connect('trailers.db')
    cursor = conn.cursor()
    
    print("UPDATING DATABASE WITH FINAL PAYMENT DATA")
    print("=" * 70)
    
    # Clear existing data
    cursor.execute("DELETE FROM moves")
    cursor.execute("DELETE FROM payments")
    
    # Initialize payment system
    payment_system = FinalPaymentSystem()
    
    # Create the submission
    submission_data = {
        'client_payment': 6693.00,
        'moves': [
            {'driver': 'Justin Duckett', 'gross': 200, 'move_id': 'MOV-001', 
             'old_trailer': '6014', 'new_trailer': '18V00327', 'location': 'FedEx Memphis', 'date': '2025-08-09'},
            {'driver': 'Justin Duckett', 'gross': 200, 'move_id': 'MOV-002',
             'old_trailer': '7144', 'new_trailer': '190030', 'location': 'FedEx Memphis', 'date': '2025-08-09'},
            {'driver': 'Justin Duckett', 'gross': 1960, 'move_id': 'MOV-003',
             'old_trailer': '7131', 'new_trailer': '190011', 'location': 'FedEx Indy', 'date': '2025-08-11'},
            {'driver': 'Carl Strikland', 'gross': 1960, 'move_id': 'MOV-004',
             'old_trailer': '7162', 'new_trailer': '190033', 'location': 'FedEx Indy', 'date': '2025-08-11'},
            {'driver': 'Brandon Smith', 'gross': 2373, 'move_id': 'MOV-005',
             'old_trailer': '5906', 'new_trailer': '7728', 'location': 'Chicago', 'date': '2025-08-11'}
        ],
        'service_fee': 6.00
    }
    
    # Calculate payment breakdown
    breakdown = payment_system.calculate_submission_payment(submission_data)
    
    # Save submission
    submission_id = payment_system.save_submission(submission_data, breakdown)
    print(f"Created submission: {submission_id}")
    
    # Insert moves into moves table
    for move in submission_data['moves']:
        driver_data = breakdown['driver_payments'][move['driver']]
        # Calculate this move's portion of the net payment
        move_net = driver_data['net_payment'] * (move['gross'] / driver_data['gross'])
        
        cursor.execute('''
            INSERT INTO moves (move_id, old_trailer, new_trailer, delivery_location,
                             driver_name, status, created_date, actual_client_payment,
                             driver_pay, factoring_fee, service_fee, payment_status, payment_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (move['move_id'], move['old_trailer'], move['new_trailer'], move['location'],
              move['driver'], 'completed', move['date'], move['gross'],
              move_net, driver_data['factoring_share'] * (move['gross'] / driver_data['gross']),
              driver_data['service_fee_share'] * (move['gross'] / driver_data['gross']),
              'paid', '2025-08-13'))
        
        print(f"Added {move['move_id']}: {move['driver']} - Gross: ${move['gross']:.2f}, Net: ${move_net:.2f}")
    
    # Add Brandon's in-progress move
    cursor.execute('''
        INSERT INTO moves (move_id, old_trailer, new_trailer, delivery_location,
                         driver_name, status, created_date, estimated_miles,
                         payment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('MOV-006', '6981', '18V00298', 'FedEx Indy', 'Brandon Smith',
          'completed', '2025-08-13', 280, 'pending'))
    print("Added MOV-006: Brandon Smith - Status: Completed but unpaid (estimated $1960 gross)")
    
    # Add payment records
    for driver_name, driver_data in breakdown['driver_payments'].items():
        cursor.execute('''
            INSERT INTO payments (driver_name, payment_date, amount, service_fee,
                                status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (driver_name, '2025-08-13', driver_data['net_payment'],
              driver_data['service_fee_share'], 'paid',
              f"{len(driver_data['moves'])} moves - {', '.join(driver_data['moves'])}"))
        print(f"Payment record: {driver_name} - ${driver_data['net_payment']:.2f}")
    
    conn.commit()
    
    # Verify data
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    cursor.execute("SELECT COUNT(*) FROM moves")
    print(f"Total moves in database: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT driver_name, SUM(driver_pay) FROM moves WHERE payment_status = 'paid' GROUP BY driver_name")
    for driver, total in cursor.fetchall():
        print(f"{driver}: ${total:.2f}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("DATABASE UPDATED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    update_database_with_final_data()