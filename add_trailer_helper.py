"""
Helper script to add new trailers to the fleet
This will work even after the fix_trailer_inventory has run
"""

import sqlite3
from datetime import datetime

def add_new_trailer(trailer_number, is_new=True, location="Fleet Memphis"):
    """Add a new trailer to the inventory"""
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    # Check if trailer already exists
    cursor.execute("SELECT id FROM trailers WHERE trailer_number = ?", (trailer_number,))
    if cursor.fetchone():
        print(f"Trailer {trailer_number} already exists!")
        conn.close()
        return False
    
    # Get location ID
    cursor.execute("SELECT id FROM locations WHERE location_title = ?", (location,))
    loc_result = cursor.fetchone()
    location_id = loc_result[0] if loc_result else 1
    
    # Add the trailer
    cursor.execute('''
        INSERT INTO trailers (trailer_number, trailer_type, current_location_id, status, is_new)
        VALUES (?, 'Roller Bed', ?, 'available', ?)
    ''', (trailer_number, location_id, 1 if is_new else 0))
    
    conn.commit()
    
    # Get new count
    cursor.execute("SELECT COUNT(*) FROM trailers")
    total = cursor.fetchone()[0]
    
    print(f"Added trailer {trailer_number} ({'NEW' if is_new else 'OLD'})")
    print(f"Total trailers now: {total}")
    
    conn.close()
    return True

def remove_trailer(trailer_number):
    """Remove a trailer from inventory"""
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    # Check if trailer is in use
    cursor.execute('''
        SELECT COUNT(*) FROM moves 
        WHERE (new_trailer = ? OR old_trailer = ?) 
        AND status IN ('active', 'in_transit')
    ''', (trailer_number, trailer_number))
    
    if cursor.fetchone()[0] > 0:
        print(f"Cannot remove {trailer_number} - currently in use!")
        conn.close()
        return False
    
    # Remove the trailer
    cursor.execute("DELETE FROM trailers WHERE trailer_number = ?", (trailer_number,))
    
    if cursor.rowcount > 0:
        conn.commit()
        
        # Get new count
        cursor.execute("SELECT COUNT(*) FROM trailers")
        total = cursor.fetchone()[0]
        
        print(f"Removed trailer {trailer_number}")
        print(f"Total trailers now: {total}")
        result = True
    else:
        print(f"Trailer {trailer_number} not found")
        result = False
    
    conn.close()
    return result

def list_all_trailers():
    """List all trailers in the system"""
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.trailer_number, 
               CASE WHEN t.is_new = 1 THEN 'NEW' ELSE 'OLD' END as type,
               l.location_title, t.status
        FROM trailers t
        LEFT JOIN locations l ON t.current_location_id = l.id
        ORDER BY t.is_new DESC, t.trailer_number
    ''')
    
    trailers = cursor.fetchall()
    
    print("\n=== CURRENT TRAILER INVENTORY ===")
    print(f"Total: {len(trailers)} trailers\n")
    
    new_trailers = [t for t in trailers if t[1] == 'NEW']
    old_trailers = [t for t in trailers if t[1] == 'OLD']
    
    print(f"NEW Trailers ({len(new_trailers)}):")
    for trailer in new_trailers:
        print(f"  {trailer[0]:10} at {trailer[2]:20} [{trailer[3]}]")
    
    print(f"\nOLD Trailers ({len(old_trailers)}):")
    for trailer in old_trailers:
        print(f"  {trailer[0]:10} at {trailer[2]:20} [{trailer[3]}]")
    
    conn.close()

def reset_fix_flag():
    """Reset the fix flag to allow the fix to run again if needed"""
    conn = sqlite3.connect('smith_williams_trucking.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM system_flags WHERE flag_name = 'trailer_fix_38_complete'")
    conn.commit()
    conn.close()
    print("Fix flag reset - the 38-trailer fix will run on next app load if count is 32")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python add_trailer_helper.py list")
        print("  python add_trailer_helper.py add <trailer_number> [NEW|OLD] [location]")
        print("  python add_trailer_helper.py remove <trailer_number>")
        print("  python add_trailer_helper.py reset_fix")
        print("\nExamples:")
        print("  python add_trailer_helper.py add 18V00700 NEW")
        print("  python add_trailer_helper.py add 7200 OLD 'FedEx Memphis'")
        print("  python add_trailer_helper.py remove 7200")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_all_trailers()
    
    elif command == "add":
        if len(sys.argv) < 3:
            print("Error: Trailer number required")
            sys.exit(1)
        
        trailer_num = sys.argv[2]
        is_new = True if len(sys.argv) < 4 or sys.argv[3].upper() == "NEW" else False
        location = sys.argv[4] if len(sys.argv) > 4 else "Fleet Memphis"
        
        add_new_trailer(trailer_num, is_new, location)
    
    elif command == "remove":
        if len(sys.argv) < 3:
            print("Error: Trailer number required")
            sys.exit(1)
        
        remove_trailer(sys.argv[2])
    
    elif command == "reset_fix":
        reset_fix_flag()
    
    else:
        print(f"Unknown command: {command}")