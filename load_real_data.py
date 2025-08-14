"""
Load REAL data into the system
"""

import sqlite3
from datetime import datetime

def load_real_data():
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    print('LOADING REAL DATA INTO SYSTEM...')
    print('=' * 60)
    
    # First, clear out all fake test data
    cursor.execute('DELETE FROM moves')
    print('Cleared all test moves')
    
    # Add real locations
    locations = [
        ('Fleet Memphis', '2505 Farrisview Boulevard', 'Memphis', 'TN', '38114', '7082853823'),
        ('FedEx Memphis', '2903 Sprankle Ave', 'Memphis', 'TN', '38118', '7082853823'),
        ('FedEx Indy', '6648 South Perimeter Road', 'Indianapolis', 'IN', '46241', '7082853823'),
        ('Chicago', '632 West Cargo Road', 'Chicago', 'IL', '60666', '7082853823'),
    ]
    
    # Check if locations table exists, if not create it
    cursor.execute('''CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        address TEXT,
        city TEXT,
        state TEXT,
        zip TEXT,
        phone TEXT
    )''')
    
    for loc in locations:
        name, address, city, state, zip_code, phone = loc
        cursor.execute('''INSERT OR REPLACE INTO locations (name, address, city, state, zip, phone)
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (name, address, city, state, zip_code, phone))
    print(f'Added {len(locations)} real locations')
    
    # Real moves from your data
    real_moves = [
        # Justin Duckett completed moves - WITH PAYMENT DATA
        ('SWT-2025-001', 'Justin Duckett', 'Fleet Memphis', 'FedEx Memphis', '2025-01-06', 'completed', 97, 203.70, '7155', '7146', 'paid'),
        ('SWT-2025-002', 'Justin Duckett', 'Fleet Memphis', 'FedEx Memphis', '2025-01-07', 'completed', 97, 203.70, '5955', '6024', 'paid'),
        ('SWT-2025-003', 'Justin Duckett', 'Fleet Memphis', 'Chicago', '2025-01-08', 'completed', 537, 1127.70, '6061', '6094', 'pending'),
        ('SWT-2025-004', 'Justin Duckett', 'Fleet Memphis', 'FedEx Indy', '2025-01-09', 'completed', 380, 798.00, '3170', '7153', 'pending'),
        ('SWT-2025-006', 'Justin Duckett', 'Fleet Memphis', 'FedEx Indy', '2025-01-11', 'completed', 380, 798.00, '6015', '7160', 'pending'),
        
        # Carl Strickland completed moves  
        ('SWT-2025-005', 'Carl Strickland', 'Fleet Memphis', 'FedEx Indy', '2025-01-10', 'completed', 380, 798.00, '6783', '3083', 'pending'),
    ]
    
    for move in real_moves:
        move_id, driver, pickup, delivery, move_date, status, miles, pay, new_trailer, old_trailer, payment_status = move
        
        # Calculate net pay (after 3% service fee)
        service_fee = pay * 0.03
        net_pay = pay - service_fee
        
        # Set payment date if paid
        payment_date = move_date if payment_status == 'paid' else None
        
        cursor.execute('''INSERT INTO moves (move_id, driver_name, pickup_location, delivery_location,
                                             move_date, status, total_miles, driver_pay, customer_name,
                                             payment_status, new_trailer, old_trailer, service_fee, net_pay,
                                             payment_date)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (move_id, driver, pickup, delivery, move_date, status, miles, pay, 
                        'Metro Logistics, Inc.', payment_status, new_trailer, old_trailer, 
                        service_fee, net_pay, payment_date))
    
    print(f'Added {len(real_moves)} completed moves')
    
    # Update driver totals in driver table
    cursor.execute('''UPDATE drivers SET total_miles = 
                      (SELECT SUM(total_miles) FROM moves WHERE driver_name = drivers.driver_name AND status = 'completed'),
                      total_earnings = 
                      (SELECT SUM(net_pay) FROM moves WHERE driver_name = drivers.driver_name AND payment_status = 'paid')''')
    
    conn.commit()
    
    # Show summary
    print()
    print('REAL DATA SUMMARY:')
    print('=' * 60)
    
    # Justin's totals
    cursor.execute('''SELECT COUNT(*), SUM(driver_pay), SUM(net_pay) 
                      FROM moves WHERE driver_name = 'Justin Duckett' ''')
    j_count, j_gross, j_net = cursor.fetchone()
    
    cursor.execute('''SELECT SUM(net_pay) FROM moves 
                      WHERE driver_name = 'Justin Duckett' AND payment_status = 'paid' ''')
    j_paid = cursor.fetchone()[0] or 0
    
    print(f'Justin Duckett:')
    print(f'  Moves: {j_count}')
    print(f'  Gross Earnings: ${j_gross:,.2f}')
    print(f'  Net Earnings: ${j_net:,.2f}')
    print(f'  Already Paid: ${j_paid:,.2f}')
    print(f'  Pending Payment: ${j_net - j_paid:,.2f}')
    
    # Carl's totals
    cursor.execute('''SELECT COUNT(*), SUM(driver_pay), SUM(net_pay) 
                      FROM moves WHERE driver_name = 'Carl Strickland' ''')
    c_count, c_gross, c_net = cursor.fetchone()
    
    cursor.execute('''SELECT SUM(net_pay) FROM moves 
                      WHERE driver_name = 'Carl Strickland' AND payment_status = 'paid' ''')
    c_paid = cursor.fetchone()[0] or 0
    
    print()
    print(f'Carl Strickland:')
    print(f'  Moves: {c_count}')
    print(f'  Gross Earnings: ${c_gross:,.2f}')
    print(f'  Net Earnings: ${c_net:,.2f}')
    print(f'  Already Paid: ${c_paid:,.2f}')
    print(f'  Pending Payment: ${c_net - c_paid:,.2f}')
    
    print()
    print(f'TOTAL PENDING PAYMENTS: ${(j_net - j_paid) + (c_net - c_paid):,.2f}')
    
    conn.close()
    print()
    print('✅ REAL DATA LOADED SUCCESSFULLY!')

if __name__ == '__main__':
    load_real_data()