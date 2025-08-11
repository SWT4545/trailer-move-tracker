"""
Database schema update script to add full address fields
"""

import sqlite3
from contextlib import contextmanager

DB_NAME = 'smith_williams_trucking.db'

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def update_schema():
    """Update database schema to include full address fields"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(locations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = [
            ('street_address', 'TEXT'),
            ('city', 'TEXT'),
            ('state', 'TEXT'),
            ('zip_code', 'TEXT'),
            ('country', 'TEXT DEFAULT "USA"'),
            ('full_address', 'TEXT')  # Computed full address for maps
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE locations ADD COLUMN {col_name} {col_type}')
                    print(f"Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    print(f"Column {col_name} might already exist: {e}")
        
        conn.commit()
        print("Schema update completed!")
        
        # Show updated schema
        cursor.execute("PRAGMA table_info(locations)")
        print("\nUpdated locations table schema:")
        for col in cursor.fetchall():
            print(f"  - {col[1]}: {col[2]}")

if __name__ == "__main__":
    update_schema()