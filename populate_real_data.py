"""
Populate the system with real trailer and move data
This script sets up the actual operational data for Smith & Williams Trucking
"""

import sqlite3
from datetime import datetime, date, timedelta
import json

def get_connection():
    """Get database connection"""
    # Try multiple database names
    try:
        conn = sqlite3.connect('trailer_moves.db')
        return conn
    except:
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            return conn
        except:
            # Create new if none exist
            conn = sqlite3.connect('trailer_moves.db')
            return conn

def init_tables():
    """Initialize all required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Trailers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trailers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trailer_number TEXT UNIQUE NOT NULL,
        current_location TEXT,
        destination TEXT,
        customer_name TEXT,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        assigned_driver TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Moves table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE,
        customer_name TEXT,
        old_trailer TEXT,
        new_trailer TEXT,
        pickup_location TEXT,
        delivery_location TEXT,
        pickup_date DATE,
        delivery_date DATE,
        completed_date DATE,
        payment_date DATE,
        amount DECIMAL(10,2),
        driver_name TEXT,
        status TEXT,
        notes TEXT,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Locations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        address TEXT,
        city TEXT,
        state TEXT,
        zip TEXT,
        type TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    return conn

def populate_locations(conn):
    """Add the three main locations"""
    cursor = conn.cursor()
    
    locations = [
        {
            'driver_name': 'FedEx Memphis',
            'address': '2874 Business Park Drive',
            'city': 'Memphis',
            'state': 'TN',
            'zip': '38118',
            'type': 'Customer',
            'notes': 'Main FedEx hub - Memphis'
        },
        {
            'driver_name': 'FedEx Indy',
            'address': '6920 Network Place',
            'city': 'Indianapolis',
            'state': 'IN',
            'zip': '46278',
            'type': 'Customer',
            'notes': 'FedEx Indianapolis hub'
        },
        {
            'driver_name': 'Fleet Memphis',
            'address': '3195 Airways Blvd',
            'city': 'Memphis',
            'state': 'TN',
            'zip': '38116',
            'type': 'Fleet',
            'notes': 'Fleet Services Memphis - All new trailers originate here'
        },
        {
            'driver_name': 'Chicago',
            'address': 'TBD',
            'city': 'Chicago',
            'state': 'IL',
            'zip': '60666',
            'type': 'Customer',
            'notes': 'Chicago location - address to be confirmed'
        }
    ]
    
    for loc in locations:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO locations (name, address, city, state, zip, type, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (loc['name'], loc['address'], loc['city'], loc['state'], 
                  loc['zip'], loc['type'], loc['notes']))
            print(f"Added location: {loc['name']}")
        except Exception as e:
            print(f"Location {loc['name']} may already exist: {e}")
    
    conn.commit()

def populate_old_trailers(conn):
    """Add old trailers that need to be moved"""
    cursor = conn.cursor()
    
    # Old trailers at unspecified locations (to be matched later)
    old_trailers_unknown = [
        '7155', '7146', '5955', '6024', '6061', '6094', 
        '3170', '7153', '6015', '7160', '6783'
    ]
    
    # Old trailers at FedEx Indy
    old_trailers_indy = ['3083', '6837', '6231']
    
    # Add trailers with unknown locations
    for trailer in old_trailers_unknown:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO trailers 
                (trailer_number, current_location, status, notes, customer_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (trailer, 'Location TBD', 'pending_pickup', 
                  'Old trailer - location to be confirmed', 'FedEx'))
            print(f"Added old trailer {trailer} - location TBD")
        except Exception as e:
            print(f"Error adding trailer {trailer}: {e}")
    
    # Add trailers at FedEx Indy
    for trailer in old_trailers_indy:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO trailers 
                (trailer_number, current_location, status, notes, customer_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (trailer, 'FedEx Indy', 'pending_pickup', 
                  'Old trailer at Indianapolis', 'FedEx'))
            print(f"Added old trailer {trailer} at FedEx Indy")
        except Exception as e:
            print(f"Error adding trailer {trailer}: {e}")
    
    conn.commit()

def populate_new_trailers(conn):
    """Add new trailers at Fleet Memphis ready to move"""
    cursor = conn.cursor()
    
    new_trailers = ['190010', '190033', '190046', '18V00298', '7728']
    
    for trailer in new_trailers:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO trailers 
                (trailer_number, current_location, status, notes, customer_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (trailer, 'Fleet Memphis', 'ready_to_move', 
                  'New trailer ready for delivery', 'FedEx'))
            print(f"Added new trailer {trailer} at Fleet Memphis")
        except Exception as e:
            print(f"Error adding trailer {trailer}: {e}")
    
    conn.commit()

def populate_completed_moves(conn):
    """Add completed moves with payment status"""
    cursor = conn.cursor()
    
    completed_moves = [
        {
            'old_trailer': '6014',
            'new_trailer': '18V00327',
            'location': 'FedEx Memphis',
            'driver': 'Justin Duckett',
            'completed': '2025-08-09',
            'paid': '2025-08-13',
            'amount': 850.00
        },
        {
            'old_trailer': '7144',
            'new_trailer': '190030',
            'location': 'FedEx Memphis',
            'driver': 'Justin Duckett',
            'completed': '2025-08-09',
            'paid': '2025-08-13',
            'amount': 850.00
        },
        {
            'old_trailer': '5906',
            'new_trailer': '7728',
            'location': 'Chicago',
            'driver': 'Brandon Smith',
            'completed': '2025-08-11',
            'paid': '2025-08-13',
            'amount': 1200.00
        },
        {
            'old_trailer': '7131',
            'new_trailer': '190011',
            'location': 'FedEx Indy',
            'driver': 'Justin Duckett',
            'completed': '2025-08-11',
            'paid': '2025-08-13',
            'amount': 950.00
        },
        {
            'old_trailer': '7162',
            'new_trailer': '190033',
            'location': 'FedEx Indy',
            'driver': 'Carl Strickland',
            'completed': '2025-08-11',
            'paid': '2025-08-13',
            'amount': 950.00
        }
    ]
    
    for i, move in enumerate(completed_moves, 1):
        order_num = f"SWT-2025-08-{str(i).zfill(3)}"
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO moves 
                (order_number, customer_name, old_trailer, new_trailer,
                 pickup_location, delivery_location, pickup_date, delivery_date,
                 completed_date, payment_date, amount, driver_name, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_num, 'FedEx', move['old_trailer'], move['new_trailer'],
                  'Fleet Memphis', move['location'], 
                  move['completed'], move['completed'],
                  move['completed'], move['paid'],
                  move['amount'], move['driver'], 'paid',
                  f"Completed swap at {move['location']}"))
            print(f"Added completed move: {move['old_trailer']} -> {move['new_trailer']} by {move['driver']}")
            
            # Update trailer statuses
            cursor.execute('''
                UPDATE trailers SET status = 'delivered', 
                current_location = ?, notes = ?
                WHERE trailer_number = ?
            ''', (move['location'], f"Delivered by {move['driver']} on {move['completed']}", 
                  move['new_trailer']))
            
            cursor.execute('''
                UPDATE trailers SET status = 'picked_up',
                current_location = 'Fleet Memphis', notes = ?
                WHERE trailer_number = ?
            ''', (f"Picked up from {move['location']} on {move['completed']}", 
                  move['old_trailer']))
            
        except Exception as e:
            print(f"Error adding move: {e}")
    
    conn.commit()

def populate_current_move(conn):
    """Add current in-process move"""
    cursor = conn.cursor()
    
    # Current move: 6981 swap with 18V00298 at FedEx Indy by Brandon
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO moves 
            (order_number, customer_name, old_trailer, new_trailer,
             pickup_location, delivery_location, pickup_date, delivery_date,
             completed_date, amount, driver_name, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('SWT-2025-08-006', 'FedEx', '6981', '18V00298',
              'Fleet Memphis', 'FedEx Indy', 
              '2025-08-13', '2025-08-13',
              '2025-08-13', 950.00, 'Brandon Smith', 'completed_pending_payment',
              'Completed today - awaiting payment'))
        print("Added current move: 6981 -> 18V00298 by Brandon (completed, not paid)")
        
        # Update trailer statuses
        cursor.execute('''
            UPDATE trailers SET status = 'in_transit', 
            current_location = 'FedEx Indy', assigned_driver = 'Brandon Smith'
            WHERE trailer_number IN ('6981', '18V00298')
        ''')
        
    except Exception as e:
        print(f"Error adding current move: {e}")
    
    conn.commit()

def create_summary_report(conn):
    """Create a summary of the data"""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("DATA POPULATION SUMMARY")
    print("="*60)
    
    # Count trailers
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE status = 'pending_pickup'")
    old_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE status = 'ready_to_move'")
    new_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'paid'")
    paid_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed_pending_payment'")
    pending_count = cursor.fetchone()[0]
    
    print(f"\nTRAILER INVENTORY:")
    print(f"  - Old trailers to pick up: {old_count}")
    print(f"  - New trailers ready to move: {new_count}")
    
    print(f"\nMOVES STATUS:")
    print(f"  - Completed and paid: {paid_count}")
    print(f"  - Completed pending payment: {pending_count}")
    
    print(f"\nDRIVER ACTIVITY:")
    cursor.execute("""
        SELECT driver_name, COUNT(*) as moves, SUM(amount) as earnings
        FROM moves 
        GROUP BY driver_name
    """)
    
    for driver in cursor.fetchall():
        print(f"  - {driver[0]}: {driver[1]} moves, ${driver[2]:,.2f} total")
    
    print("\nQUESTIONS FOR CLARIFICATION:")
    print("  1. What are the addresses for the old trailers without locations?")
    print("  2. Should we auto-match old trailers to nearest location?")
    print("  3. What is the standard rate per move for each location?")
    print("  4. Do you want automatic driver assignment based on location?")
    print("  5. Should completed moves auto-generate invoices?")

def main():
    """Main execution"""
    print("SMITH & WILLIAMS TRUCKING - DATA POPULATION")
    print("="*60)
    
    # Initialize database
    conn = init_tables()
    print("Database initialized")
    
    # Populate all data
    print("\nAdding locations...")
    populate_locations(conn)
    
    print("\nAdding old trailers...")
    populate_old_trailers(conn)
    
    print("\nAdding new trailers...")
    populate_new_trailers(conn)
    
    print("\nAdding completed moves...")
    populate_completed_moves(conn)
    
    print("\nAdding current move...")
    populate_current_move(conn)
    
    # Generate summary
    create_summary_report(conn)
    
    conn.close()
    print("\nData population complete!")
    print("You can now login to test each role with this real data.")

if __name__ == "__main__":
    main()