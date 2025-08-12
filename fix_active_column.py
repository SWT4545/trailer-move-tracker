"""
Fix missing 'active' column in drivers table
"""

import sqlite3
import os

def fix_database_columns():
    """Add missing columns to drivers table"""
    db_path = 'trailer_tracker_streamlined.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(drivers)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Current columns in drivers table: {columns}")
        
        # Add missing columns
        missing_columns = {
            'active': 'INTEGER DEFAULT 1',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        for col_name, col_def in missing_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE drivers ADD COLUMN {col_name} {col_def}")
                    print(f"Added column: {col_name}")
                    conn.commit()
                except sqlite3.OperationalError as e:
                    if "duplicate column" not in str(e).lower():
                        print(f"Error adding {col_name}: {e}")
        
        # Verify columns were added
        cursor.execute("PRAGMA table_info(drivers)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Updated columns in drivers table: {columns}")
        
        # Set all existing drivers to active
        cursor.execute("UPDATE drivers SET active = 1 WHERE active IS NULL")
        conn.commit()
        
        conn.close()
        print("Database fix completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error fixing database: {e}")
        return False

if __name__ == "__main__":
    fix_database_columns()