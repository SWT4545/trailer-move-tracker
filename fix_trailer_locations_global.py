"""
Fix all trailer locations globally based on actual current state
"""

import sqlite3

def fix_all_trailer_locations():
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    # Get location IDs
    cursor.execute("SELECT id, location_title FROM locations")
    locations = {title: id for id, title in cursor.fetchall()}
    
    # Based on user feedback and active moves:
    # FedEx Indy has 6094 and 6837 (being picked up by active moves)
    # Plus the original 5955, 3083, 6231
    
    trailer_locations = {
        # OLD trailers at FedEx locations
        'FedEx Indy': ['5955', '3083', '6231', '6094', '6837'],  # 5 at Indy
        'FedEx Houston': ['7155'],
        'FedEx Oakland': ['7146'],
        'FedEx Chicago': ['6024', '3170'],
        'FedEx Dallas': ['6061', '7160'],
        'FedEx Dulles VA': ['7153'],
        'FedEx Hebron KY': ['6015'],
        'FedEx Newark NJ': ['6783'],
        # OLD trailers at Fleet Memphis (remaining)
        'Fleet Memphis': ['5950', '5876', '4427', '6014', '7144', '5906', '7131', '7162', '6981']
    }
    
    # Update each trailer to correct location
    for location, trailers in trailer_locations.items():
        if location in locations:
            loc_id = locations[location]
            for trailer in trailers:
                cursor.execute('''
                    UPDATE trailers 
                    SET current_location_id = ?
                    WHERE trailer_number = ?
                ''', (loc_id, trailer))
                print(f"  {trailer} -> {location}")
    
    conn.commit()
    
    # Verify the fix
    print("\n" + "="*60)
    print("VERIFIED OLD TRAILER LOCATIONS:")
    print("="*60)
    
    cursor.execute('''
        SELECT l.location_title, COUNT(t.id) as count, GROUP_CONCAT(t.trailer_number, ', ') as trailers
        FROM trailers t
        JOIN locations l ON t.current_location_id = l.id
        WHERE t.is_new = 0
        GROUP BY l.location_title
        ORDER BY l.location_title
    ''')
    
    total = 0
    for location, count, trailers in cursor.fetchall():
        print(f'\n{location}: {count} OLD trailers')
        print(f'  {trailers}')
        total += count
    
    print(f'\nTotal OLD trailers: {total}')
    
    # Check active moves are correct
    print("\n" + "="*60)
    print("ACTIVE MOVES:")
    print("="*60)
    
    cursor.execute('''
        SELECT m.system_id, m.new_trailer, m.old_trailer, l.location_title
        FROM moves m
        JOIN locations l ON m.destination_location_id = l.id
        WHERE m.status IN ('active', 'assigned', 'in_transit')
        ORDER BY m.system_id
    ''')
    
    for move in cursor.fetchall():
        print(f"{move[0]}: Deliver NEW {move[1]} to {move[3]}, pickup OLD {move[2]}")
        
        # Verify OLD trailer is at destination
        cursor.execute('''
            SELECT l.location_title 
            FROM trailers t
            JOIN locations l ON t.current_location_id = l.id
            WHERE t.trailer_number = ?
        ''', (move[2],))
        
        result = cursor.fetchone()
        if result and result[0] == move[3]:
            print(f"  ✓ OLD {move[2]} is correctly at {move[3]}")
        else:
            print(f"  ✗ WARNING: OLD {move[2]} is at {result[0] if result else 'UNKNOWN'}")
    
    conn.close()

if __name__ == "__main__":
    fix_all_trailer_locations()