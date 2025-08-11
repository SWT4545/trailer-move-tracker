"""
Database update to support Fleet Memphis as base location
and proper trailer swap workflow
"""

import sqlite3
from contextlib import contextmanager
import database as db

def update_database_for_fleet():
    """Update database to support Fleet Memphis workflow"""
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Add Fleet Memphis as a permanent location if not exists
        full_address = "3691 Pilot Dr, Memphis, TN 38118, USA"
        cursor.execute("""
            INSERT OR IGNORE INTO locations 
            (location_title, location_address, street_address, city, state, zip_code) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Fleet Memphis",
            full_address,
            "3691 Pilot Dr",
            "Memphis",
            "TN",
            "38118"
        ))
        
        # Update trailer_moves table to include round trip fields
        try:
            cursor.execute("ALTER TABLE trailer_moves ADD COLUMN is_round_trip BOOLEAN DEFAULT 1")
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE trailer_moves ADD COLUMN base_location TEXT DEFAULT 'Fleet Memphis'")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE trailer_moves ADD COLUMN round_trip_miles REAL")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE trailer_moves ADD COLUMN one_way_miles REAL")
        except:
            pass
        
        # Update trailers table to track swap status
        try:
            cursor.execute("ALTER TABLE trailers ADD COLUMN swap_location TEXT")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE trailers ADD COLUMN swap_date DATE")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE trailers ADD COLUMN paired_trailer_id INTEGER")
        except:
            pass
        
        conn.commit()
        print("Database updated for Fleet Memphis workflow")
        
        # Show current structure
        cursor.execute("PRAGMA table_info(trailer_moves)")
        print("\nTrailer moves columns:")
        for col in cursor.fetchall():
            print(f"  - {col[1]}: {col[2]}")

if __name__ == "__main__":
    db.init_database()
    update_database_for_fleet()