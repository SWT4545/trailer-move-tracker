"""
Load Real Production Data for Smith & Williams Trucking
This script loads all the actual data from the specifications
"""

import sqlite3
from datetime import datetime, date, timedelta

def load_real_production_data():
    """Load all real production data into the system"""
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    print("Loading Real Production Data...")
    print("=" * 60)
    
    # Clear existing data first
    tables_to_clear = ['moves', 'trailers', 'locations', 'drivers', 'documents', 'financials']
    for table in tables_to_clear:
        try:
            cursor.execute(f'DELETE FROM {table}')
        except:
            pass
    
    # 1. LOAD LOCATIONS
    print("\n1. Loading Locations...")
    locations = [
        # Main base
        ('Fleet Memphis', '2505 Farrisview Boulevard', 'Memphis', 'TN', '38114', 35.1964, -89.9397, 'base', 1, '7082853823'),
        
        # FedEx locations with addresses
        ('FedEx Memphis', '2903 Sprankle Ave', 'Memphis', 'TN', '38118', 35.0537, -89.9693, 'customer', 0, '7082853823'),
        ('FedEx Indy', '6648 South Perimeter Road', 'Indianapolis', 'IN', '46241', 39.7200, -86.2906, 'customer', 0, '7082853823'),
        ('FedEx Chicago', '632 West Cargo Road', 'Chicago', 'IL', '60666', 41.9742, -87.8901, 'customer', 0, '7082853823'),
        
        # Additional FedEx locations (placeholders for now)
        ('FedEx Houston', '1000 Airport Blvd', 'Houston', 'TX', '77061', 29.6454, -95.2788, 'customer', 0, None),
        ('FedEx Oakland', '8500 Pardee Dr', 'Oakland', 'CA', '94621', 37.7413, -122.2009, 'customer', 0, None),
        ('FedEx Dallas', '2400 Aviation Dr', 'Dallas', 'TX', '75261', 32.8968, -97.0382, 'customer', 0, None),
        ('FedEx Dulles VA', '45005 Aviation Dr', 'Dulles', 'VA', '20166', 38.9544, -77.4506, 'customer', 0, None),
        ('FedEx Hebron KY', '1113 Worldwide Blvd', 'Hebron', 'KY', '41048', 39.0668, -84.7038, 'customer', 0, None),
        ('FedEx Newark NJ', '100 Haynes Ave', 'Newark', 'NJ', '07114', 40.6895, -74.1745, 'customer', 0, None)
    ]
    
    for loc in locations:
        cursor.execute('''
            INSERT OR REPLACE INTO locations (
                location_title, address, city, state, zip_code,
                latitude, longitude, location_type, is_base_location, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', loc)
    print(f"[OK] Loaded {len(locations)} locations")
    
    # 2. LOAD DRIVERS
    print("\n2. Loading Driver Profiles...")
    
    # Brandon Smith (Owner/Driver)
    cursor.execute('''
        INSERT OR REPLACE INTO drivers (
            driver_name, company_name, phone, email, driver_type,
            cdl_number, insurance_policy, insurance_expiry, w9_on_file,
            status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        'Brandon Smith', 'Smith & Williams Trucking', '951-437-5474',
        'dispatch@smithwilliamstrucking.com', 'owner',
        'CDL-OWNER-001', 'COMMERCIAL', '2026-12-31', 1, 'active'
    ))
    
    # Justin Duckett
    cursor.execute('''
        INSERT OR REPLACE INTO drivers (
            driver_name, company_name, phone, email, driver_type,
            cdl_number, insurance_policy, insurance_expiry, w9_on_file,
            status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        'Justin Duckett', 'L&P Solutions', '9012184083',
        'Lpsolutions1623@gmail.com', 'contractor',
        'DOT-3978189', 'KSCW4403105-00', '2025-11-26', 1, 'active'
    ))
    
    # Carl Strickland
    cursor.execute('''
        INSERT OR REPLACE INTO drivers (
            driver_name, company_name, phone, email, driver_type,
            cdl_number, insurance_policy, insurance_expiry, w9_on_file,
            status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        'Carl Strickland', 'Cross State Logistics Inc.', '9014974055',
        'Strick750@gmail.com', 'contractor',
        'DOT-3737098', '02TRM061775-01', '2025-12-04', 1, 'active'
    ))
    
    print("[OK] Loaded 3 driver profiles")
    
    # 3. LOAD TRAILERS
    print("\n3. Loading Trailers...")
    
    # Get location IDs
    cursor.execute('SELECT id, location_title FROM locations')
    loc_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Old trailers at various locations (Ready for pickup)
    old_trailers = [
        ('7155', 'Roller Bed', loc_map['FedEx Houston'], 'available', 0),
        ('7146', 'Roller Bed', loc_map['FedEx Oakland'], 'available', 0),
        ('5955', 'Roller Bed', loc_map['FedEx Indy'], 'available', 0),
        ('6024', 'Roller Bed', loc_map['FedEx Chicago'], 'available', 0),
        ('6061', 'Roller Bed', loc_map['FedEx Dallas'], 'available', 0),
        ('3170', 'Roller Bed', loc_map['FedEx Chicago'], 'available', 0),
        ('7153', 'Roller Bed', loc_map['FedEx Dulles VA'], 'available', 0),
        ('6015', 'Roller Bed', loc_map['FedEx Hebron KY'], 'available', 0),
        ('7160', 'Roller Bed', loc_map['FedEx Dallas'], 'available', 0),
        ('6783', 'Roller Bed', loc_map['FedEx Newark NJ'], 'available', 0),
        ('3083', 'Roller Bed', loc_map['FedEx Indy'], 'available', 0),
        ('6231', 'Roller Bed', loc_map['FedEx Indy'], 'available', 0),
    ]
    
    # New trailers (delivered or active/in transit)
    new_trailers = [
        ('190033', 'Roller Bed', loc_map['FedEx Indy'], 'delivered', 1),
        ('190046', 'Roller Bed', loc_map['Fleet Memphis'], 'in_transit', 1),  # Active move to FedEx Indy
        ('18V00298', 'Roller Bed', loc_map['FedEx Indy'], 'delivered', 1),
        ('7728', 'Roller Bed', loc_map['FedEx Chicago'], 'delivered', 1),
        ('190011', 'Roller Bed', loc_map['FedEx Indy'], 'delivered', 1),
        ('190030', 'Roller Bed', loc_map['FedEx Memphis'], 'delivered', 1),
        ('18V00327', 'Roller Bed', loc_map['FedEx Memphis'], 'delivered', 1),
        ('18V00406', 'Roller Bed', loc_map['FedEx Memphis'], 'delivered', 1),
        ('18V00409', 'Roller Bed', loc_map['FedEx Memphis'], 'delivered', 1),
        ('18V00414', 'Roller Bed', loc_map['FedEx Memphis'], 'delivered', 1),
        ('18V00407', 'Roller Bed', loc_map['Fleet Memphis'], 'in_transit', 1),  # Active move to FedEx Indy
    ]
    
    # Old trailers that were swapped (now at Fleet Memphis)
    returned_trailers = [
        ('7162', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # Returned from FedEx Indy
        ('7131', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # Returned from FedEx Indy
        ('5906', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # Returned from FedEx Chicago
        ('7144', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # Returned from FedEx Memphis
        ('6014', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # Returned from FedEx Indy
        ('6981', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # Returned from FedEx Indy
        ('5950', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # Returned from FedEx Memphis
        ('5876', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # Returned from FedEx Memphis
        ('4427', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # Returned from FedEx Memphis
    ]
    
    all_trailers = old_trailers + new_trailers + returned_trailers
    
    for trailer in all_trailers:
        cursor.execute('''
            INSERT OR REPLACE INTO trailers (
                trailer_number, trailer_type, current_location_id, status, is_new
            ) VALUES (?, ?, ?, ?, ?)
        ''', trailer)
    
    print(f"[OK] Loaded {len(all_trailers)} trailers")
    
    # 4. LOAD MOVES
    print("\n4. Loading Moves...")
    
    # Get driver IDs
    cursor.execute('SELECT id, driver_name FROM drivers')
    driver_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Get trailer IDs
    cursor.execute('SELECT id, trailer_number FROM trailers')
    trailer_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    move_counter = 1
    
    # Function to generate system ID
    def get_system_id():
        nonlocal move_counter
        system_id = f"SWT-2025-08-{move_counter:04d}"
        move_counter += 1
        return system_id
    
    # Calculate mileage between locations (simplified - would use Google Maps API in production)
    mileage = {
        ('Fleet Memphis', 'FedEx Memphis'): 15,  # Local Memphis
        ('FedEx Memphis', 'Fleet Memphis'): 15,
        ('Fleet Memphis', 'FedEx Indy'): 385,
        ('FedEx Indy', 'Fleet Memphis'): 385,
        ('Fleet Memphis', 'FedEx Chicago'): 540,
        ('FedEx Chicago', 'Fleet Memphis'): 540,
    }
    
    # COMPLETED AND PAID MOVES (with trailer swap details)
    completed_paid_moves = [
        # Justin Duckett moves - each move swaps trailers
        {
            'system_id': get_system_id(),
            'new_trailer': '18V00327', 'old_trailer': '6014',  # Delivered 18V00327, picked up 6014
            'origin': 'Fleet Memphis', 'destination': 'FedEx Indy',
            'driver': 'Justin Duckett', 'date': date(2025, 8, 12),
            'delivered': date(2025, 8, 13), 'status': 'completed',
            'payment_status': 'paid', 'miles': 933.33  # Actual round trip from Metro Logistics  # Round trip
        },
        {
            'system_id': get_system_id(),
            'new_trailer': '190030', 'old_trailer': '7144',
            'origin': 'Fleet Memphis', 'destination': 'FedEx Memphis',
            'driver': 'Justin Duckett', 'date': date(2025, 8, 12),
            'delivered': date(2025, 8, 13), 'status': 'completed',
            'payment_status': 'paid', 'miles': 15 * 2
        },
        {
            'system_id': get_system_id(),
            'new_trailer': '190011', 'old_trailer': '7131',
            'origin': 'Fleet Memphis', 'destination': 'FedEx Indy',
            'driver': 'Justin Duckett', 'date': date(2025, 8, 12),
            'delivered': date(2025, 8, 13), 'status': 'completed',
            'payment_status': 'paid', 'miles': 933.33  # Actual round trip from Metro Logistics
        },
        
        # Brandon Smith move
        {
            'system_id': get_system_id(),
            'new_trailer': '7728', 'old_trailer': '5906',
            'origin': 'Fleet Memphis', 'destination': 'FedEx Chicago',
            'driver': 'Brandon Smith', 'date': date(2025, 8, 12),
            'delivered': date(2025, 8, 13), 'status': 'completed',
            'payment_status': 'paid', 'miles': 540 * 2
        },
        
        # Carl Strickland move
        {
            'system_id': get_system_id(),
            'new_trailer': '190033', 'old_trailer': '7162',
            'origin': 'Fleet Memphis', 'destination': 'FedEx Indy',
            'driver': 'Carl Strickland', 'date': date(2025, 8, 12),
            'delivered': date(2025, 8, 13), 'status': 'completed',
            'payment_status': 'paid', 'miles': 933.33  # Actual round trip from Metro Logistics
        },
    ]
    
    # COMPLETED BUT NOT PAID MOVES (Brandon Smith)
    completed_unpaid_moves = [
        {
            'system_id': get_system_id(),
            'new_trailer': '18V00414', 'old_trailer': '5950',
            'origin': 'Fleet Memphis', 'destination': 'FedEx Memphis',
            'driver': 'Brandon Smith', 'date': date(2025, 8, 14),
            'delivered': date(2025, 8, 14), 'status': 'completed',
            'payment_status': 'pending', 'miles': 15 * 2
        },
        {
            'system_id': get_system_id(),
            'new_trailer': '18V00409', 'old_trailer': '5876',
            'origin': 'Fleet Memphis', 'destination': 'FedEx Memphis',
            'driver': 'Brandon Smith', 'date': date(2025, 8, 14),
            'delivered': date(2025, 8, 14), 'status': 'completed',
            'payment_status': 'pending', 'miles': 15 * 2
        },
        {
            'system_id': get_system_id(),
            'new_trailer': '18V00406', 'old_trailer': '4427',
            'origin': 'Fleet Memphis', 'destination': 'FedEx Memphis',
            'driver': 'Brandon Smith', 'date': date(2025, 8, 14),
            'delivered': date(2025, 8, 14), 'status': 'completed',
            'payment_status': 'pending', 'miles': 15 * 2
        },
        {
            'system_id': get_system_id(),
            'new_trailer': '18V00298', 'old_trailer': '6981',
            'origin': 'Fleet Memphis', 'destination': 'FedEx Indy',
            'driver': 'Brandon Smith', 'date': date(2025, 8, 12),
            'delivered': date(2025, 8, 13), 'status': 'completed',
            'payment_status': 'pending', 'miles': 385 * 2
        },
    ]
    
    # IN PROCESS MOVES (ACTIVE)
    in_process_moves = [
        {
            'system_id': get_system_id(),
            'new_trailer': '190046', 'old_trailer': '6837',
            'origin': 'Fleet Memphis', 'destination': 'FedEx Indy',
            'driver': 'Carl Strickland', 'date': date(2025, 8, 14),
            'delivered': None, 'status': 'active',  # Changed to active
            'payment_status': 'pending', 'miles': 385 * 2
        },
        {
            'system_id': get_system_id(),
            'new_trailer': '18V00407', 'old_trailer': '6094',
            'origin': 'Fleet Memphis', 'destination': 'FedEx Indy',
            'driver': 'Brandon Smith', 'date': date(2025, 8, 14),
            'delivered': None, 'status': 'active',  # Changed to active
            'payment_status': 'pending', 'miles': 385 * 2
        },
    ]
    
    # Insert all moves
    all_moves = completed_paid_moves + completed_unpaid_moves + in_process_moves
    
    for move in all_moves:
        # Calculate financial details
        # For Indy routes: $1960.00 payment for 933.33 miles
        # After 3% factoring: $1960 * 0.97 = $1901.20
        estimated_earnings = move['miles'] * 2.10
        
        if move['payment_status'] == 'paid':
            # For paid moves, calculate with fees
            factoring_fee = estimated_earnings * 0.03  # 3% factoring fee
            after_factoring = estimated_earnings - factoring_fee  # Should be $1901.20 for Indy routes
            # Service fee TBD - will be subtracted from after_factoring amount
            service_fee = 6.00  # Placeholder - actual TBD
            driver_net_pay = after_factoring - service_fee
            actual_payment = estimated_earnings  # Client pays full amount
        else:
            factoring_fee = None
            service_fee = None
            driver_net_pay = None
            actual_payment = None
        
        cursor.execute('''
            INSERT INTO moves (
                system_id, mlbl_number, move_date, trailer_id,
                origin_location_id, destination_location_id, client,
                driver_id, driver_name, estimated_miles, base_rate,
                estimated_earnings, actual_client_payment, factoring_fee,
                service_fee, driver_net_pay, status, delivery_status,
                delivery_date, payment_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            move['system_id'],
            None,  # MLBL to be added later by management
            move['date'],
            trailer_map.get(move['new_trailer']),
            loc_map[move['origin']],
            loc_map[move['destination']],
            'FedEx',  # Client
            driver_map[move['driver']],
            move['driver'],
            move['miles'],
            2.10,
            estimated_earnings,
            actual_payment,
            factoring_fee,
            service_fee,
            driver_net_pay,
            move['status'],
            'Delivered' if move['delivered'] else 'In Transit',
            move['delivered'],
            move['payment_status']
        ))
    
    print(f"[OK] Loaded {len(all_moves)} moves")
    print(f"  - {len(completed_paid_moves)} completed and paid")
    print(f"  - {len(completed_unpaid_moves)} completed awaiting payment")
    print(f"  - {len(in_process_moves)} active (in process)")
    
    # 5. FINANCIAL SUMMARY
    print("\n5. Financial Summary:")
    
    # Calculate totals for paid moves
    total_paid = sum(m['miles'] * 2.10 for m in completed_paid_moves)
    
    # Justin Duckett: 3 moves
    justin_moves = [m for m in completed_paid_moves if m['driver'] == 'Justin Duckett']
    justin_gross = sum(m['miles'] * 2.10 for m in justin_moves)
    justin_net = justin_gross - (justin_gross * 0.03) - 6.00  # 3% factoring + $2 service fee
    
    # Brandon Smith: 1 paid move
    brandon_paid = [m for m in completed_paid_moves if m['driver'] == 'Brandon Smith']
    brandon_gross = sum(m['miles'] * 2.10 for m in brandon_paid)
    brandon_net = brandon_gross - (brandon_gross * 0.03) - 2.00
    
    # Carl Strickland: 1 move
    carl_moves = [m for m in completed_paid_moves if m['driver'] == 'Carl Strickland']
    carl_gross = sum(m['miles'] * 2.10 for m in carl_moves)
    carl_net = carl_gross - (carl_gross * 0.03) - 2.00
    
    print(f"\nTotal Client Payment (5 paid moves): ${total_paid:,.2f}")
    print(f"\nDriver Net Earnings After Fees:")
    print(f"  Justin Duckett (3 moves): ${justin_net:,.2f}")
    print(f"  Brandon Smith (1 paid move): ${brandon_net:,.2f}")
    print(f"  Carl Strickland (1 move): ${carl_net:,.2f}")
    
    # Brandon's pending moves
    brandon_pending = [m for m in completed_unpaid_moves if m['driver'] == 'Brandon Smith']
    brandon_pending_gross = sum(m['miles'] * 2.10 for m in brandon_pending)
    print(f"\n  Brandon Smith pending payment (4 moves): ${brandon_pending_gross:,.2f}")
    
    # Brandon's in-process move
    brandon_in_process = [m for m in in_process_moves if m['driver'] == 'Brandon Smith']
    brandon_future = sum(m['miles'] * 2.10 for m in brandon_in_process)
    print(f"  Brandon Smith in process (1 move): ${brandon_future:,.2f}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Real production data loaded successfully!")
    print("\nSystem is ready with:")
    print(f"  - {len(locations)} locations")
    print(f"  - {len(all_trailers)} trailers")
    print(f"  - 3 driver profiles")
    print(f"  - {len(all_moves)} moves")
    print(f"  - Financial tracking with 3% factoring fee")
    print(f"  - Service fee splitting among drivers")

if __name__ == "__main__":
    load_real_production_data()