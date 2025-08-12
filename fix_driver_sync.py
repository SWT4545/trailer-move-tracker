"""
Fix Driver Synchronization
Ensures drivers in user accounts are also in database
"""

import sqlite3
import json
import os
from datetime import datetime

def sync_drivers_to_database():
    """Sync all driver users to the database"""
    
    if not os.path.exists('user_accounts.json'):
        print("No user accounts file found")
        return
    
    # Load user accounts
    with open('user_accounts.json', 'r') as f:
        users = json.load(f)
    
    # Connect to database
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    synced = 0
    errors = 0
    
    print("SYNCING DRIVERS TO DATABASE")
    print("=" * 50)
    
    for username, info in users.get('users', {}).items():
        if 'driver' in info.get('roles', []):
            driver_name = info.get('name', username)
            
            # Check if driver exists in database
            cursor.execute('SELECT id FROM drivers WHERE driver_name = ?', (driver_name,))
            if not cursor.fetchone():
                # Add to drivers table
                try:
                    cursor.execute('''
                        INSERT INTO drivers (driver_name, phone, email, username, status, active, created_at)
                        VALUES (?, ?, ?, ?, 'available', 1, CURRENT_TIMESTAMP)
                    ''', (
                        driver_name,
                        info.get('phone', ''),
                        info.get('email', ''),
                        username
                    ))
                    
                    # Also add to drivers_extended
                    cursor.execute('''
                        INSERT OR IGNORE INTO drivers_extended (driver_name, driver_type, phone, email, status, active)
                        VALUES (?, 'company', ?, ?, 'available', 1)
                    ''', (
                        driver_name,
                        info.get('phone', ''),
                        info.get('email', '')
                    ))
                    
                    conn.commit()
                    synced += 1
                    print(f"✓ Synced: {driver_name} ({username})")
                    
                except sqlite3.IntegrityError as e:
                    errors += 1
                    print(f"✗ Error syncing {driver_name}: {e}")
                    conn.rollback()
            else:
                print(f"• Already exists: {driver_name}")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print(f"Sync complete: {synced} added, {errors} errors")
    
    return synced, errors

if __name__ == "__main__":
    sync_drivers_to_database()