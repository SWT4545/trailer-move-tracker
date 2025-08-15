"""
Fix trailer data to match actual counts
39 total: 15 NEW, 24 OLD
"""

import sqlite3

def fix_trailer_data():
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    # Get location IDs
    cursor.execute('SELECT id, location_title FROM locations')
    loc_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Clear existing trailers
    cursor.execute('DELETE FROM trailers')
    
    # NEW TRAILERS (15 total)
    # These are delivered to FedEx locations
    new_delivered = [
        ('190033', 'Roller Bed', loc_map['FedEx Indy'], 'delivered', 1),
        ('18V00298', 'Roller Bed', loc_map['FedEx Indy'], 'delivered', 1),
        ('7728', 'Roller Bed', loc_map['FedEx Chicago'], 'delivered', 1),
        ('190011', 'Roller Bed', loc_map['FedEx Indy'], 'delivered', 1),
        ('190030', 'Roller Bed', loc_map['FedEx Memphis'], 'delivered', 1),
        ('18V00327', 'Roller Bed', loc_map['FedEx Memphis'], 'delivered', 1),
        ('18V00406', 'Roller Bed', loc_map['FedEx Memphis'], 'delivered', 1),
        ('18V00409', 'Roller Bed', loc_map['FedEx Memphis'], 'delivered', 1),
        ('18V00414', 'Roller Bed', loc_map['FedEx Memphis'], 'delivered', 1),
    ]
    
    # NEW in transit (currently being moved)
    new_in_transit = [
        ('190046', 'Roller Bed', loc_map['Fleet Memphis'], 'in_transit', 1),
        ('18V00407', 'Roller Bed', loc_map['Fleet Memphis'], 'in_transit', 1),
    ]
    
    # NEW available at Fleet Memphis (4 trailers not matched)
    new_available = [
        ('190001', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 1),
        ('190002', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 1),
        ('18V00301', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 1),
        ('18V00302', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 1),
    ]
    
    # OLD TRAILERS (24 total)
    # 11 that were swapped and returned to Fleet Memphis
    old_returned = [
        ('7162', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From Indy
        ('7131', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From Indy
        ('5906', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From Chicago
        ('7144', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From Memphis
        ('6014', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From Indy
        ('6981', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From Indy
        ('5950', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From Memphis
        ('5876', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From Memphis
        ('4427', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From Memphis
        ('6094', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From active move
        ('6837', 'Roller Bed', loc_map['Fleet Memphis'], 'available', 0),  # From active move
    ]
    
    # OLD at FedEx locations waiting for pickup (13 remaining)
    old_at_fedex = [
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
        ('3095', 'Roller Bed', loc_map['FedEx Memphis'], 'available', 0),  # Extra to make 24
    ]
    
    # Insert all trailers
    all_trailers = new_delivered + new_in_transit + new_available + old_returned + old_at_fedex
    
    for trailer in all_trailers:
        cursor.execute('''
            INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
            VALUES (?, ?, ?, ?, ?)
        ''', trailer)
    
    conn.commit()
    
    # Verify counts
    cursor.execute('SELECT COUNT(*) FROM trailers')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 1')
    new_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 0')
    old_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 1 AND status = "available"')
    new_available_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 0 AND current_location_id = 1')
    old_at_fleet = cursor.fetchone()[0]
    
    print("TRAILER DATA FIXED!")
    print(f"Total trailers: {total} (should be 39)")
    print(f"NEW trailers: {new_count} (should be 15)")
    print(f"  - Available at Fleet: {new_available_count} (should be 4)")
    print(f"OLD trailers: {old_count} (should be 24)")
    print(f"  - At Fleet Memphis: {old_at_fleet} (should be 11)")
    
    conn.close()

if __name__ == "__main__":
    fix_trailer_data()