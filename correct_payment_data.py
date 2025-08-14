"""
Correct Payment Data Calculation
Working backwards from net driver pay to find client payments
"""

import sqlite3
from enhanced_payment_system import EnhancedPaymentSystem

def recalculate_payments():
    """
    The original data provided was the NET amount drivers received AFTER fees.
    We need to work backwards to find what the client actually paid.
    
    Formula: 
    Net Pay = Client Payment - (Client Payment * 0.03) - Service Fee
    Net Pay = Client Payment * 0.97 - Service Fee
    Client Payment = (Net Pay + Service Fee) / 0.97
    """
    
    print("RECALCULATING PAYMENT DATA")
    print("=" * 60)
    print("Working backwards from NET driver payments to find client payments\n")
    
    # Original data - these are NET amounts AFTER all fees
    driver_payments = [
        {
            'driver': 'Justin Duckett',
            'date': '2025-08-13',
            'net_received': 609.00,  # This is what Justin actually received
            'moves': 2,  # 2 local Memphis moves
            'description': '2 Memphis local moves (6014→18V00327, 7144→190030)'
        },
        {
            'driver': 'Brandon Smith', 
            'date': '2025-08-13',
            'net_received': 1113.00,  # Brandon's net pay
            'moves': 1,  # Chicago run
            'description': 'Memphis to Chicago (5906→7728)'
        },
        {
            'driver': 'Justin Duckett',
            'date': '2025-08-13', 
            'net_received': 588.00,  # Justin's Indy run net
            'moves': 1,
            'description': 'Memphis to FedEx Indy (7131→190011)'
        },
        {
            'driver': 'Carl Strikland',
            'date': '2025-08-13',
            'net_received': 588.00,  # Carl's net pay
            'moves': 1,
            'description': 'Memphis to FedEx Indy (7162→190033)'
        }
    ]
    
    total_client_payment = 0
    total_factoring_fees = 0
    total_service_fees = 0
    
    for payment in driver_payments:
        # Work backwards to find client payment
        # Net = ClientPayment * 0.97 - ServiceFee
        # ClientPayment = (Net + ServiceFee) / 0.97
        
        service_fee = 6.00 * payment['moves']  # $6 per move
        client_payment = (payment['net_received'] + service_fee) / 0.97
        factoring_fee = client_payment * 0.03
        
        # Verify our calculation
        calculated_net = client_payment - factoring_fee - service_fee
        
        print(f"Driver: {payment['driver']}")
        print(f"Description: {payment['description']}")
        print(f"Net Received (given): ${payment['net_received']:,.2f}")
        print(f"Service Fee: ${service_fee:.2f} ({payment['moves']} moves × $6)")
        print(f"Client Payment (calculated): ${client_payment:,.2f}")
        print(f"Factoring Fee (3%): ${factoring_fee:.2f}")
        print(f"Verification: ${client_payment:,.2f} - ${factoring_fee:.2f} - ${service_fee:.2f} = ${calculated_net:,.2f}")
        print(f"Match: {'✓' if abs(calculated_net - payment['net_received']) < 0.01 else '✗'}")
        
        # Calculate implied mileage
        implied_miles = client_payment / 2.10
        print(f"Implied Miles: {implied_miles:.1f} miles (at $2.10/mile)")
        print("-" * 60)
        
        total_client_payment += client_payment
        total_factoring_fees += factoring_fee
        total_service_fees += service_fee
    
    print("\nSUMMARY TOTALS")
    print("=" * 60)
    print(f"Total Client Payments: ${total_client_payment:,.2f}")
    print(f"Total Factoring Fees (3%): ${total_factoring_fees:,.2f}")
    print(f"Total Service Fees: ${total_service_fees:,.2f}")
    print(f"Total Net to Drivers: ${total_client_payment - total_factoring_fees - total_service_fees:,.2f}")
    
    # Now let's combine Justin's payments
    print("\nCOMBINED DRIVER TOTALS")
    print("=" * 60)
    
    # Justin had two separate payments
    justin_total_net = 609.00 + 588.00
    justin_service_fee = 18.00  # 3 moves total × $6
    justin_client_payment = (justin_total_net + justin_service_fee) / 0.97
    justin_factoring = justin_client_payment * 0.03
    
    print(f"Justin Duckett (3 moves total):")
    print(f"  Total Net Received: ${justin_total_net:,.2f}")
    print(f"  Total Client Payment: ${justin_client_payment:,.2f}")
    print(f"  Factoring Fee: ${justin_factoring:.2f}")
    print(f"  Service Fee: ${justin_service_fee:.2f}")
    
    brandon_net = 1113.00
    brandon_service = 6.00
    brandon_client = (brandon_net + brandon_service) / 0.97
    brandon_factoring = brandon_client * 0.03
    
    print(f"\nBrandon Smith (1 move):")
    print(f"  Net Received: ${brandon_net:,.2f}")
    print(f"  Client Payment: ${brandon_client:,.2f}")
    print(f"  Factoring Fee: ${brandon_factoring:.2f}")
    print(f"  Service Fee: ${brandon_service:.2f}")
    
    carl_net = 588.00
    carl_service = 6.00
    carl_client = (carl_net + carl_service) / 0.97
    carl_factoring = carl_client * 0.03
    
    print(f"\nCarl Strikland (1 move):")
    print(f"  Net Received: ${carl_net:,.2f}")
    print(f"  Client Payment: ${carl_client:,.2f}")
    print(f"  Factoring Fee: ${carl_factoring:.2f}")
    print(f"  Service Fee: ${carl_service:.2f}")
    
    return {
        'justin': {'net': justin_total_net, 'client_payment': justin_client_payment},
        'brandon': {'net': brandon_net, 'client_payment': brandon_client},
        'carl': {'net': carl_net, 'client_payment': carl_client}
    }

def update_database_with_correct_payments():
    """Update the database with correctly calculated payments"""
    
    conn = sqlite3.connect('trailers.db')
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("UPDATING DATABASE WITH CORRECT PAYMENTS")
    print("=" * 60)
    
    # Clear existing moves and payments
    cursor.execute("DELETE FROM moves")
    cursor.execute("DELETE FROM payments")
    
    # Moves with correct calculations
    moves = [
        # Justin's Memphis local moves (combined payment of $609)
        {
            'id': 'MOV-001',
            'old_trailer': '6014',
            'new_trailer': '18V00327',
            'location': 'FedEx Memphis',
            'driver': 'Justin Duckett',
            'date': '2025-08-09',
            'net_pay': 304.50,  # Half of $609
            'service_fee': 6.00
        },
        {
            'id': 'MOV-002', 
            'old_trailer': '7144',
            'new_trailer': '190030',
            'location': 'FedEx Memphis',
            'driver': 'Justin Duckett',
            'date': '2025-08-09',
            'net_pay': 304.50,  # Half of $609
            'service_fee': 6.00
        },
        # Brandon's Chicago run
        {
            'id': 'MOV-003',
            'old_trailer': '5906',
            'new_trailer': '7728',
            'location': 'Chicago',
            'driver': 'Brandon Smith',
            'date': '2025-08-11',
            'net_pay': 1113.00,
            'service_fee': 6.00
        },
        # Justin's Indy run
        {
            'id': 'MOV-004',
            'old_trailer': '7131',
            'new_trailer': '190011',
            'location': 'FedEx Indy',
            'driver': 'Justin Duckett',
            'date': '2025-08-11',
            'net_pay': 588.00,
            'service_fee': 6.00
        },
        # Carl's Indy run
        {
            'id': 'MOV-005',
            'old_trailer': '7162',
            'new_trailer': '190033',
            'location': 'FedEx Indy',
            'driver': 'Carl Strikland',
            'date': '2025-08-11',
            'net_pay': 588.00,
            'service_fee': 6.00
        },
        # Brandon's current in-progress move
        {
            'id': 'MOV-006',
            'old_trailer': '6981',
            'new_trailer': '18V00298',
            'location': 'FedEx Indy',
            'driver': 'Brandon Smith',
            'date': '2025-08-13',
            'net_pay': None,  # Not paid yet
            'service_fee': None,
            'status': 'completed',  # Completed but not paid
            'payment_status': 'pending'
        }
    ]
    
    for move in moves:
        if move.get('net_pay'):
            # Calculate client payment from net pay
            client_payment = (move['net_pay'] + move['service_fee']) / 0.97
            factoring_fee = client_payment * 0.03
            miles = client_payment / 2.10  # Implied miles
            
            cursor.execute('''
                INSERT INTO moves (move_id, old_trailer, new_trailer, delivery_location,
                                 driver_name, status, created_date, total_miles,
                                 actual_client_payment, driver_pay, factoring_fee,
                                 service_fee, payment_status, payment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (move['id'], move['old_trailer'], move['new_trailer'], move['location'],
                  move['driver'], 'completed', move['date'], round(miles, 1),
                  client_payment, move['net_pay'], factoring_fee,
                  move['service_fee'], 'paid', '2025-08-13'))
            
            print(f"Added {move['id']}: {move['driver']} - Net: ${move['net_pay']:.2f}, Client: ${client_payment:.2f}")
        else:
            # In-progress move - estimate payment
            estimated_miles = 280  # Memphis to Indy
            client_payment = estimated_miles * 2.10
            factoring_fee = client_payment * 0.03
            service_fee = 6.00
            net_pay = client_payment - factoring_fee - service_fee
            
            cursor.execute('''
                INSERT INTO moves (move_id, old_trailer, new_trailer, delivery_location,
                                 driver_name, status, created_date, estimated_miles,
                                 driver_pay, factoring_fee, service_fee, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (move['id'], move['old_trailer'], move['new_trailer'], move['location'],
                  move['driver'], 'completed', move['date'], estimated_miles,
                  net_pay, factoring_fee, service_fee, 'pending'))
            
            print(f"Added {move['id']}: {move['driver']} - Status: Completed/Unpaid, Estimated: ${net_pay:.2f}")
    
    # Add payment records for paid moves
    payments = [
        ('Justin Duckett', '2025-08-13', 1197.00, 18.00, 'Paid for 3 moves'),
        ('Brandon Smith', '2025-08-13', 1113.00, 6.00, 'Chicago run payment'),
        ('Carl Strikland', '2025-08-13', 588.00, 6.00, 'Indianapolis delivery')
    ]
    
    for driver, date, amount, fees, notes in payments:
        cursor.execute('''
            INSERT INTO payments (driver_name, payment_date, amount, service_fee, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (driver, date, amount, fees, 'paid', notes))
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("DATABASE UPDATED WITH CORRECT PAYMENT DATA!")
    print("=" * 60)

if __name__ == "__main__":
    # First show the calculations
    results = recalculate_payments()
    
    # Then update the database
    update_database_with_correct_payments()