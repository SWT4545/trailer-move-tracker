"""
Fix OLD trailer assignments in moves
Ensure OLD trailers are actually at the destination FedEx location
"""

import sqlite3

def fix_old_trailer_assignments():
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    # Get all moves that need fixing
    cursor.execute('''
        SELECT m.id, m.system_id, m.destination_location_id, l.location_title
        FROM moves m
        JOIN locations l ON m.destination_location_id = l.id
        WHERE m.old_trailer IS NOT NULL
        ORDER BY m.system_id
    ''')
    
    moves = cursor.fetchall()
    
    for move_id, system_id, dest_id, dest_name in moves:
        # Get available OLD trailers at this destination
        cursor.execute('''
            SELECT trailer_number 
            FROM trailers 
            WHERE current_location_id = ?
            AND is_new = 0
            AND status = 'available'
            ORDER BY trailer_number
            LIMIT 1
        ''', (dest_id,))
        
        available_trailer = cursor.fetchone()
        
        if available_trailer:
            # Update the move with correct OLD trailer
            cursor.execute('''
                UPDATE moves 
                SET old_trailer = ?
                WHERE id = ?
            ''', (available_trailer[0], move_id))
            print(f"Fixed {system_id}: Now picking up OLD {available_trailer[0]} from {dest_name}")
        else:
            print(f"WARNING: No OLD trailers available at {dest_name} for move {system_id}")
    
    conn.commit()
    print("\nAll OLD trailer assignments have been fixed!")
    
    # Verify the fix
    print("\nVerification - Active moves with correct OLD trailers:")
    cursor.execute('''
        SELECT m.system_id, m.new_trailer, m.old_trailer, l.location_title
        FROM moves m
        JOIN locations l ON m.destination_location_id = l.id
        WHERE m.status IN ('active', 'assigned', 'in_transit')
    ''')
    
    for row in cursor.fetchall():
        print(f"  {row[0]}: NEW {row[1]} to {row[3]}, picking up OLD {row[2]}")
    
    conn.close()

if __name__ == "__main__":
    fix_old_trailer_assignments()