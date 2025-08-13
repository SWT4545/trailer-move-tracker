"""
Database Migration for Driver Self-Assignment System
Adds new tables and columns to support driver self-assignment features
"""

import sqlite3
import os
from datetime import datetime
import json

DB_FILE = 'trailer_tracker_streamlined.db'
BACKUP_FILE = f'trailer_tracker_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

def backup_database():
    """Create a backup of the database before migration"""
    import shutil
    if os.path.exists(DB_FILE):
        shutil.copy2(DB_FILE, BACKUP_FILE)
        print(f"Database backed up to {BACKUP_FILE}")
        return True
    return False

def run_migration():
    """Run the database migration for self-assignment features"""
    
    # Create backup first
    if not backup_database():
        print("Could not create backup. Migration cancelled.")
        return False
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Add new columns to trailers table for location tracking
        print("Adding location tracking columns to trailers table...")
        
        # Check if columns exist before adding
        cursor.execute("PRAGMA table_info(trailers)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        new_trailer_columns = [
            ("last_known_location", "TEXT"),
            ("location_confirmed_by", "TEXT"),
            ("location_confirmed_at", "TIMESTAMP"),
            ("is_reserved", "BOOLEAN DEFAULT 0"),
            ("reserved_by_driver", "TEXT"),
            ("reserved_until", "TIMESTAMP")
        ]
        
        for col_name, col_type in new_trailer_columns:
            if col_name not in existing_columns:
                cursor.execute(f"ALTER TABLE trailers ADD COLUMN {col_name} {col_type}")
                print(f"  - Added column: {col_name}")
        
        # 2. Add new columns to moves table for self-assignment tracking
        print("\nAdding self-assignment columns to moves table...")
        
        cursor.execute("PRAGMA table_info(moves)")
        existing_move_columns = [col[1] for col in cursor.fetchall()]
        
        new_move_columns = [
            ("self_assigned", "BOOLEAN DEFAULT 0"),
            ("assigned_at", "TIMESTAMP"),
            ("assignment_type", "TEXT DEFAULT 'coordinator'"),
            ("unassigned_at", "TIMESTAMP"),
            ("unassigned_reason", "TEXT")
        ]
        
        for col_name, col_type in new_move_columns:
            if col_name not in existing_move_columns:
                cursor.execute(f"ALTER TABLE moves ADD COLUMN {col_name} {col_type}")
                print(f"  - Added column: {col_name}")
        
        # 3. Create notifications table
        print("\nCreating notifications table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            driver_id INTEGER,
            move_id TEXT,
            message TEXT NOT NULL,
            type TEXT CHECK(type IN ('info', 'warning', 'success', 'error', 'assignment', 'completion')),
            priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'urgent')) DEFAULT 'medium',
            read BOOLEAN DEFAULT 0,
            read_at TIMESTAMP,
            action_required BOOLEAN DEFAULT 0,
            action_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        )
        ''')
        print("  - Notifications table created")
        
        # Create index for faster queries
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_notifications_user 
        ON notifications(user_id, read, created_at DESC)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_notifications_driver 
        ON notifications(driver_id, read, created_at DESC)
        ''')
        
        # 4. Create driver availability table
        print("\nCreating driver availability table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS driver_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            status TEXT CHECK(status IN ('available', 'assigned', 'in_transit', 'break', 'offline')) DEFAULT 'available',
            current_move_id TEXT,
            last_known_location TEXT,
            last_completed_move_id TEXT,
            next_available_time TIMESTAMP,
            max_daily_moves INTEGER DEFAULT 1,
            completed_moves_today INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (driver_id) REFERENCES drivers(id)
        )
        ''')
        print("  - Driver availability table created")
        
        # Create index for availability queries
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_driver_availability_status 
        ON driver_availability(status, updated_at DESC)
        ''')
        
        # 5. Create trailer location reports table
        print("\nCreating trailer location reports table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trailer_location_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trailer_number TEXT NOT NULL,
            reported_location TEXT NOT NULL,
            reported_by_driver TEXT NOT NULL,
            photo_url TEXT,
            notes TEXT,
            verified BOOLEAN DEFAULT 0,
            verified_by TEXT,
            verified_at TIMESTAMP,
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("  - Trailer location reports table created")
        
        # 6. Create assignment history table for tracking all assignment changes
        print("\nCreating assignment history table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id TEXT NOT NULL,
            driver_id INTEGER,
            driver_name TEXT,
            action TEXT CHECK(action IN ('assigned', 'unassigned', 'reassigned', 'completed', 'cancelled')),
            action_by TEXT,
            action_type TEXT CHECK(action_type IN ('self', 'coordinator', 'system', 'management')),
            reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("  - Assignment history table created")
        
        # 7. Create available moves view for drivers
        print("\nCreating available moves view...")
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS available_moves_view AS
        SELECT 
            t1.trailer_number as new_trailer,
            t2.trailer_number as old_trailer,
            t1.swap_location as location,
            l.location_address as full_address,
            t1.id as new_trailer_id,
            t2.id as old_trailer_id,
            CASE 
                WHEN t1.is_reserved = 1 THEN 'reserved'
                WHEN EXISTS (
                    SELECT 1 FROM moves m 
                    WHERE (m.new_trailer = t1.trailer_number OR m.old_trailer = t2.trailer_number)
                    AND m.status IN ('assigned', 'in_progress')
                ) THEN 'assigned'
                ELSE 'available'
            END as availability_status,
            t1.reserved_by_driver,
            t1.reserved_until
        FROM trailers t1
        LEFT JOIN trailers t2 ON t1.paired_trailer_id = t2.id
        LEFT JOIN locations l ON t1.swap_location = l.location_title
        WHERE t1.trailer_type = 'new' 
        AND t1.status = 'available'
        ''')
        print("  - Available moves view created")
        
        # 8. Add driver columns if not exists
        print("\nUpdating drivers table...")
        cursor.execute("PRAGMA table_info(drivers)")
        existing_driver_columns = [col[1] for col in cursor.fetchall()]
        
        new_driver_columns = [
            ("password_hash", "TEXT"),
            ("driver_type", "TEXT DEFAULT 'contractor'"),
            ("active", "BOOLEAN DEFAULT 1"),
            ("can_self_assign", "BOOLEAN DEFAULT 1"),
            ("max_concurrent_moves", "INTEGER DEFAULT 1"),
            ("preferred_locations", "TEXT"),
            ("last_login", "TIMESTAMP"),
            ("notification_preferences", "TEXT")
        ]
        
        for col_name, col_type in new_driver_columns:
            if col_name not in existing_driver_columns:
                cursor.execute(f"ALTER TABLE drivers ADD COLUMN {col_name} {col_type}")
                print(f"  - Added column to drivers: {col_name}")
        
        # 9. Initialize driver availability records for existing drivers
        print("\nInitializing driver availability records...")
        cursor.execute("SELECT id, driver_name FROM drivers WHERE active = 1 OR active IS NULL")
        drivers = cursor.fetchall()
        
        for driver_id, driver_name in drivers:
            cursor.execute("""
                INSERT OR IGNORE INTO driver_availability (driver_id, status)
                VALUES (?, 'available')
            """, (driver_id,))
        print(f"  - Initialized availability for {len(drivers)} drivers")
        
        # 10. Create settings table for system configuration
        print("\nCreating system settings table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        )
        ''')
        
        # Insert default settings
        default_settings = [
            ('self_assignment_enabled', 'true', 'boolean', 'Enable driver self-assignment feature'),
            ('assignment_lead_time_hours', '2', 'integer', 'Minimum hours before pickup for self-assignment'),
            ('reservation_timeout_minutes', '30', 'integer', 'Minutes before reserved trailer becomes available again'),
            ('max_daily_moves_per_driver', '1', 'integer', 'Maximum moves a driver can self-assign per day'),
            ('require_photo_confirmation', 'true', 'boolean', 'Require photo when confirming trailer location'),
            ('auto_notify_coordinators', 'true', 'boolean', 'Automatically notify coordinators of self-assignments')
        ]
        
        for key, value, type_, desc in default_settings:
            cursor.execute("""
                INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, description)
                VALUES (?, ?, ?, ?)
            """, (key, value, type_, desc))
        print("  - System settings table created with defaults")
        
        # Commit transaction
        cursor.execute("COMMIT")
        conn.commit()
        print("\nMigration completed successfully!")
        
        # Log migration
        cursor.execute("""
            INSERT INTO activity_log (action, entity_type, user, details)
            VALUES ('database_migration', 'system', 'migration_script', ?)
        """, (json.dumps({
            'migration': 'driver_self_assignment',
            'timestamp': datetime.now().isoformat(),
            'backup_file': BACKUP_FILE
        }),))
        conn.commit()
        
        return True
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"\nMigration failed: {e}")
        print(f"Database has been rolled back. Backup available at {BACKUP_FILE}")
        return False
    
    finally:
        conn.close()

def verify_migration():
    """Verify that all migration changes were applied successfully"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("\nVerifying migration...")
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    required_tables = [
        'notifications',
        'driver_availability', 
        'trailer_location_reports',
        'assignment_history',
        'system_settings'
    ]
    
    for table in required_tables:
        if table in tables:
            print(f"  - Table '{table}' exists")
        else:
            print(f"  X Table '{table}' missing")
    
    # Check view
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = [v[0] for v in cursor.fetchall()]
    if 'available_moves_view' in views:
        print(f"  - View 'available_moves_view' exists")
    
    conn.close()
    print("\nVerification complete")

if __name__ == "__main__":
    print("Starting Driver Self-Assignment Database Migration")
    print("=" * 50)
    
    if run_migration():
        verify_migration()
    else:
        print("\nMigration failed. Please check the error messages above.")