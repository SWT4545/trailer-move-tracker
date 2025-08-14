"""
Fix move statuses to properly show in-process work for drivers
Ensures Brandon's current move shows as awaiting payment
"""

import sqlite3
from datetime import datetime

def get_connection():
    """Get database connection"""
    try:
        return sqlite3.connect('trailer_moves.db')
    except:
        return sqlite3.connect('trailer_tracker_streamlined.db')

def fix_move_statuses():
    """Fix the current move status for Brandon"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("FIXING MOVE STATUSES")
    print("="*60)
    
    # Fix Brandon's current move - should be completed but not paid
    cursor.execute("""
        UPDATE moves 
        SET status = 'completed', 
            completed_date = '2025-08-13',
            payment_date = NULL,
            notes = 'Completed - Awaiting payment processing'
        WHERE old_trailer = '6981' AND new_trailer = '18V00298'
    """)
    
    print("Fixed Brandon's move 6981/18V00298 - Status: Completed, awaiting payment")
    
    # Ensure all paid moves are marked correctly
    cursor.execute("""
        UPDATE moves 
        SET status = 'paid'
        WHERE payment_date IS NOT NULL AND payment_date != ''
    """)
    
    paid_count = cursor.rowcount
    print(f"Updated {paid_count} moves to 'paid' status")
    
    # Show current move statuses
    print("\nCURRENT MOVE STATUS SUMMARY:")
    print("-"*40)
    
    cursor.execute("""
        SELECT driver_name, old_trailer, new_trailer, status, 
               completed_date, payment_date
        FROM moves
        ORDER BY completed_date DESC
    """)
    
    for move in cursor.fetchall():
        driver = move[0] or "Unassigned"
        status_text = "PAID" if move[3] == 'paid' else "AWAITING PAYMENT" if move[3] == 'completed' else move[3].upper()
        print(f"{driver}: {move[1]} -> {move[2]}")
        print(f"  Status: {status_text}")
        print(f"  Completed: {move[4]}, Paid: {move[5] or 'PENDING'}")
        print()
    
    conn.commit()
    conn.close()
    print("Move statuses fixed successfully!")

def create_pending_assignments():
    """Create some pending assignments for drivers to pick up"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\nCREATING PENDING ASSIGNMENTS")
    print("="*60)
    
    # Create assignments for available trailers
    assignments = [
        {
            'old_trailer': '3083',
            'new_trailer': '190010',
            'location': 'FedEx Indy',
            'suggested_driver': 'Justin Duckett',
            'notes': 'Ready for pickup - FedEx Indy'
        },
        {
            'old_trailer': '6837',
            'new_trailer': '190046',
            'location': 'FedEx Indy',
            'suggested_driver': 'Carl Strickland',
            'notes': 'Ready for pickup - FedEx Indy'
        }
    ]
    
    for i, assign in enumerate(assignments, 7):
        order_num = f"SWT-2025-08-{str(i).zfill(3)}"
        
        # Check if move already exists
        cursor.execute("""
            SELECT id FROM moves 
            WHERE old_trailer = ? AND new_trailer = ?
        """, (assign['old_trailer'], assign['new_trailer']))
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO moves 
                (order_number, customer_name, old_trailer, new_trailer,
                 pickup_location, delivery_location, pickup_date,
                 driver_name, status, notes, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_num, 'FedEx', assign['old_trailer'], assign['new_trailer'],
                  'Fleet Memphis', assign['location'], '2025-08-14',
                  None, 'pending_assignment', assign['notes'], 950.00))
            
            print(f"Created pending assignment: {assign['old_trailer']} -> {assign['new_trailer']}")
            print(f"  Suggested for: {assign['suggested_driver']}")
            
            # Update trailer statuses
            cursor.execute("""
                UPDATE trailers 
                SET status = 'pending_assignment',
                    notes = ?
                WHERE trailer_number IN (?, ?)
            """, (f"Pending assignment - suggested for {assign['suggested_driver']}", 
                  assign['old_trailer'], assign['new_trailer']))
    
    conn.commit()
    conn.close()
    print("\nPending assignments created!")

def show_driver_workload():
    """Show what each driver should see"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\nDRIVER WORKLOAD VIEW")
    print("="*60)
    
    drivers = ['Justin Duckett', 'Carl Strickland', 'Brandon Smith']
    
    for driver in drivers:
        print(f"\n{driver.upper()}'S VIEW:")
        print("-"*40)
        
        # Completed moves
        cursor.execute("""
            SELECT COUNT(*), SUM(amount)
            FROM moves 
            WHERE driver_name = ? AND status = 'paid'
        """, (driver,))
        
        completed = cursor.fetchone()
        print(f"Completed & Paid: {completed[0]} moves, ${completed[1] or 0:,.2f}")
        
        # Pending payment
        cursor.execute("""
            SELECT old_trailer, new_trailer, amount
            FROM moves 
            WHERE driver_name = ? AND status = 'completed'
        """, (driver,))
        
        pending = cursor.fetchall()
        if pending:
            for p in pending:
                print(f"Awaiting Payment: {p[0]} -> {p[1]} (${p[2]:,.2f})")
        
        # Available to assign
        cursor.execute("""
            SELECT old_trailer, new_trailer, pickup_location
            FROM moves 
            WHERE status = 'pending_assignment'
            AND (driver_name IS NULL OR driver_name = '')
        """)
        
        available = cursor.fetchall()
        if available and driver != 'Brandon Smith':  # Brandon has a pending payment
            print(f"Available to Self-Assign: {len(available)} moves")
            for a in available[:2]:  # Show first 2
                print(f"  - {a[0]} -> {a[1]} at {a[2]}")
    
    conn.close()

def main():
    """Main execution"""
    print("SMITH & WILLIAMS TRUCKING - STATUS FIX")
    print("="*60)
    
    # Fix current statuses
    fix_move_statuses()
    
    # Create pending assignments
    create_pending_assignments()
    
    # Show driver workload
    show_driver_workload()
    
    print("\n" + "="*60)
    print("NEXT STEPS FOR EACH ROLE:")
    print("-"*40)
    print("BRANDON (Owner):")
    print("  1. Process payment for your move (6981/18V00298)")
    print("  2. Review pending assignments for other drivers")
    print("\nJUSTIN:")
    print("  1. Check self-assign for trailer 3083/190010 at FedEx Indy")
    print("\nCARL:")
    print("  1. Check self-assign for trailer 6837/190046 at FedEx Indy")
    print("\nDATA ENTRY:")
    print("  1. Update locations for 11 trailers marked 'Location TBD'")
    print("="*60)

if __name__ == "__main__":
    main()