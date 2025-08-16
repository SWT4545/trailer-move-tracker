"""
Fix return trailer (old_trailer) data for all moves
Based on actual move data from production
"""

import sqlite3
from datetime import datetime

# Database path
DB_PATH = 'swt_fleet.db'

def fix_return_trailers():
    """Fix return trailer assignments based on correct data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if we have new_trailer and old_trailer columns
    cursor.execute("PRAGMA table_info(moves)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'new_trailer' not in columns or 'old_trailer' not in columns:
        print("Database doesn't have new_trailer/old_trailer columns. Skipping fixes.")
        conn.close()
        return
    
    # Correct return trailer mappings based on production data
    # Format: (system_id, correct_old_trailer)
    trailer_fixes = [
        # Brandon's moves
        ('SWT-2025-008', '6981'),  # 7162 swapped with 6981
        ('SWT-2025-009', '7162'),  # 6981 swapped with 7162
        ('SWT-2025-010', '7131'),  # 5906 swapped with 7131
        ('SWT-2025-011', '5906'),  # 7131 swapped with 5906
        ('SWT-2025-012', '7144'),  # 6014 swapped with 7144
        ('SWT-2025-013', '6014'),  # 7144 swapped with 6014
        ('SWT-2025-014', '4427'),  # 5876 swapped with 4427
        ('SWT-2025-015', '5876'),  # 4427 swapped with 5876
        ('SWT-2025-016', '5950'),  # 6837 swapped with 5950
        ('SWT-2025-017', '6837'),  # 5950 swapped with 6837
        ('SWT-2025-018', '6094'),  # Return trailer: 6094
        
        # Carl's moves - verify these are correct
        ('SWT-2025-003', '6231'),  # 190011 swapped with 6231
        ('SWT-2025-004', '3083'),  # 190030 swapped with 3083
        ('SWT-2025-005', '6783'),  # 18V00298 swapped with 6783
        ('SWT-2025-006', '7160'),  # 190033 swapped with 7160
        ('SWT-2025-007', '7153'),  # 7728 swapped with 7153
        
        # Terrance's moves
        ('SWT-2025-001', '3170'),  # 190046 swapped with 3170
        ('SWT-2025-002', '6061'),  # 18V00407 swapped with 6061
        
        # Jermichael's moves
        ('SWT-2025-019', '6024'),  # 6017 swapped with 6024
        ('SWT-2025-020', '5955'),  # 7124 swapped with 5955
        ('SWT-2025-021', '7146'),  # 7145 swapped with 7146
        ('SWT-2025-022', '7155'),  # 6023 swapped with 7155
        ('SWT-2025-023', '6015'),  # 7126 swapped with 6015
    ]
    
    # Apply fixes
    for system_id, correct_old_trailer in trailer_fixes:
        try:
            cursor.execute('''
                UPDATE moves 
                SET old_trailer = ?
                WHERE system_id = ?
            ''', (correct_old_trailer, system_id))
            print(f"Fixed {system_id}: old_trailer = {correct_old_trailer}")
        except Exception as e:
            print(f"Error fixing {system_id}: {e}")
    
    # Also update any moves where old_trailer is still NULL or 'TBD'
    cursor.execute('''
        SELECT system_id, new_trailer, driver_name, move_date
        FROM moves
        WHERE (old_trailer IS NULL OR old_trailer = 'TBD' OR old_trailer = '')
        AND status = 'completed'
    ''')
    
    incomplete_moves = cursor.fetchall()
    if incomplete_moves:
        print(f"\nFound {len(incomplete_moves)} moves with missing return trailers:")
        for move in incomplete_moves:
            print(f"  {move[0]} - Driver: {move[2]}, Date: {move[3]}, New Trailer: {move[1]}")
    
    conn.commit()
    conn.close()
    print("\nReturn trailer fixes completed!")

if __name__ == "__main__":
    fix_return_trailers()