"""
Update trailer inventory to match exact list provided
38 trailers total: 23 OLD, 15 NEW
"""

import sqlite3
from datetime import datetime

def update_trailer_inventory():
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    print("UPDATING TRAILER INVENTORY TO MATCH EXACT LIST")
    print("=" * 60)
    
    # Get location IDs
    cursor.execute('SELECT id, location_title FROM locations')
    loc_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Clear existing trailers (we'll rebuild from your exact list)
    cursor.execute('DELETE FROM trailers')
    print("Cleared existing trailer data")
    
    # ========== OLD TRAILERS (23 total) ==========
    
    # OLD AVAILABLE (12 trailers) - at various FedEx locations
    old_available = [
        ('7155', 'FedEx Houston'),
        ('7146', 'FedEx Oakland'),
        ('5955', 'FedEx Indy'),
        ('6024', 'FedEx Chicago'),
        ('6061', 'FedEx Dallas'),
        ('3170', 'FedEx Chicago'),
        ('7153', 'FedEx Dulles VA'),
        ('6015', 'FedEx Hebron KY'),
        ('7160', 'FedEx Dallas'),
        ('6783', 'FedEx Newark NJ'),
        ('3083', 'FedEx Indy'),
        ('6231', 'FedEx Indy'),
    ]
    
    # OLD NOT AVAILABLE (11 trailers) - matched with moves, now at Fleet Memphis
    old_not_available = [
        ('6094', 'Fleet Memphis'),  # In active move with Brandon
        ('6837', 'Fleet Memphis'),  # In active move with Carl
        ('5950', 'Fleet Memphis'),  # Completed move
        ('5876', 'Fleet Memphis'),  # Completed move
        ('4427', 'Fleet Memphis'),  # Completed move
        ('6014', 'Fleet Memphis'),  # Completed move
        ('7144', 'Fleet Memphis'),  # Completed move
        ('5906', 'Fleet Memphis'),  # Completed move
        ('7131', 'Fleet Memphis'),  # Completed move
        ('7162', 'Fleet Memphis'),  # Completed move
        ('6981', 'Fleet Memphis'),  # Completed move
    ]
    
    # ========== NEW TRAILERS (15 total) ==========
    
    # NEW AVAILABLE (3 trailers) - at Fleet Memphis ready for delivery
    new_available = [
        ('18V00600', 'Fleet Memphis'),
        ('18V00598', 'Fleet Memphis'),
        ('18V00599', 'Fleet Memphis'),
    ]
    
    # NEW RESERVED (1 trailer) - reserved by owner, at Fleet Memphis
    new_reserved = [
        ('18V00408', 'Fleet Memphis'),  # Reserved but not yet in a move
    ]
    
    # NEW NOT AVAILABLE (11 trailers) - matched with moves
    # These are either delivered to FedEx or in transit
    new_not_available_completed = [
        ('18V00406', 'FedEx Memphis'),   # Completed move
        ('18V00409', 'FedEx Memphis'),   # Completed move
        ('18V00414', 'FedEx Memphis'),   # Completed move
        ('190030', 'FedEx Memphis'),     # Completed move
        ('190033', 'FedEx Indy'),        # Completed move
        ('18V00298', 'FedEx Indy'),      # Completed move
        ('190011', 'FedEx Indy'),        # Completed move
        ('7728', 'FedEx Chicago'),       # Completed move
        ('18V00327', 'FedEx Memphis'),   # Completed move
    ]
    
    new_not_available_active = [
        ('18V00407', 'Fleet Memphis'),   # Active move (in transit)
        ('190046', 'Fleet Memphis'),     # Active move (in transit)
    ]
    
    # Insert all OLD trailers
    print("\nInserting OLD trailers...")
    for trailer, location in old_available:
        cursor.execute('''
            INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
            VALUES (?, 'Roller Bed', ?, 'available', 0)
        ''', (trailer, loc_map.get(location, loc_map['Fleet Memphis'])))
    print(f"  - Added {len(old_available)} available OLD trailers")
    
    for trailer, location in old_not_available:
        # These are at Fleet Memphis after being swapped
        cursor.execute('''
            INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
            VALUES (?, 'Roller Bed', ?, 'available', 0)
        ''', (trailer, loc_map['Fleet Memphis']))
    print(f"  - Added {len(old_not_available)} not available OLD trailers (at Fleet after swap)")
    
    # Insert all NEW trailers
    print("\nInserting NEW trailers...")
    for trailer, location in new_available:
        cursor.execute('''
            INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
            VALUES (?, 'Roller Bed', ?, 'available', 1)
        ''', (trailer, loc_map['Fleet Memphis']))
    print(f"  - Added {len(new_available)} available NEW trailers")
    
    for trailer, location in new_reserved:
        cursor.execute('''
            INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
            VALUES (?, 'Roller Bed', ?, 'reserved', 1)
        ''', (trailer, loc_map['Fleet Memphis']))
    print(f"  - Added {len(new_reserved)} reserved NEW trailers")
    
    for trailer, location in new_not_available_completed:
        cursor.execute('''
            INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
            VALUES (?, 'Roller Bed', ?, 'delivered', 1)
        ''', (trailer, loc_map.get(location, loc_map['Fleet Memphis'])))
    print(f"  - Added {len(new_not_available_completed)} delivered NEW trailers")
    
    for trailer, location in new_not_available_active:
        cursor.execute('''
            INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
            VALUES (?, 'Roller Bed', ?, 'in_transit', 1)
        ''', (trailer, loc_map['Fleet Memphis']))
    print(f"  - Added {len(new_not_available_active)} in-transit NEW trailers")
    
    conn.commit()
    
    # Verify final counts
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    
    cursor.execute('SELECT COUNT(*) FROM trailers')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 0')
    old_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 1')
    new_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 0 AND status = "available"')
    old_available_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 1 AND status = "available"')
    new_available_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trailers WHERE is_new = 1 AND status = "reserved"')
    new_reserved_count = cursor.fetchone()[0]
    
    print(f"Total trailers: {total} (should be 38)")
    print(f"OLD trailers: {old_count} (should be 23)")
    print(f"  - Available: {old_available_count}")
    print(f"NEW trailers: {new_count} (should be 15)")
    print(f"  - Available: {new_available_count} (should be 3)")
    print(f"  - Reserved: {new_reserved_count} (should be 1)")
    
    # Check that all move trailers exist
    print("\nChecking moves have matching trailers...")
    cursor.execute('SELECT DISTINCT new_trailer FROM moves WHERE new_trailer IS NOT NULL')
    new_in_moves = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT DISTINCT old_trailer FROM moves WHERE old_trailer IS NOT NULL')
    old_in_moves = [row[0] for row in cursor.fetchall()]
    
    missing_new = []
    missing_old = []
    
    for trailer in new_in_moves:
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE trailer_number = ?', (trailer,))
        if cursor.fetchone()[0] == 0:
            missing_new.append(trailer)
    
    for trailer in old_in_moves:
        cursor.execute('SELECT COUNT(*) FROM trailers WHERE trailer_number = ?', (trailer,))
        if cursor.fetchone()[0] == 0:
            missing_old.append(trailer)
    
    if missing_new:
        print(f"WARNING: NEW trailers in moves but not in inventory: {missing_new}")
    else:
        print("✓ All NEW trailers in moves are in inventory")
    
    if missing_old:
        print(f"WARNING: OLD trailers in moves but not in inventory: {missing_old}")
    else:
        print("✓ All OLD trailers in moves are in inventory")
    
    conn.close()
    print("\nUPDATE COMPLETE!")

if __name__ == "__main__":
    update_trailer_inventory()