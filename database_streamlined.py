"""
Streamlined database operations for Smith & Williams Trucking
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json

DB_FILE = 'trailer_tracker_streamlined.db'

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_database():
    """Initialize database with all required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Trailers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trailers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trailer_number TEXT UNIQUE NOT NULL,
        trailer_type TEXT CHECK(trailer_type IN ('new', 'old')),
        current_location TEXT,
        status TEXT DEFAULT 'available',
        swap_location TEXT,
        paired_trailer_id INTEGER,
        notes TEXT,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Locations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_title TEXT UNIQUE NOT NULL,
        street_address TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        location_address TEXT GENERATED ALWAYS AS 
            (street_address || ', ' || city || ', ' || state || ' ' || COALESCE(zip_code, '')) STORED,
        coordinates TEXT,
        is_base_location BOOLEAN DEFAULT 0,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Drivers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_name TEXT UNIQUE NOT NULL,
        phone TEXT,
        email TEXT,
        username TEXT UNIQUE,
        status TEXT DEFAULT 'available',
        total_miles REAL DEFAULT 0,
        total_earnings REAL DEFAULT 0,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Moves table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        move_id TEXT UNIQUE,
        new_trailer TEXT,
        old_trailer TEXT,
        pickup_location TEXT,
        delivery_location TEXT,
        driver_name TEXT,
        move_date DATE,
        pickup_time TIME,
        delivery_time TIME,
        total_miles REAL,
        driver_pay REAL,
        status TEXT DEFAULT 'assigned',
        payment_status TEXT DEFAULT 'pending',
        pod_uploaded BOOLEAN DEFAULT 0,
        pod_upload_time TIMESTAMP,
        notes TEXT,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Payment tracking
        rate_confirmation_sent BOOLEAN DEFAULT 0,
        submitted_to_factoring TIMESTAMP,
        factoring_confirmed TIMESTAMP,
        payment_received TIMESTAMP,
        driver_paid TIMESTAMP,
        
        -- Document references
        pod_url TEXT,
        pickup_photo_url TEXT,
        delivery_photo_url TEXT,
        damage_photos_urls TEXT
    )
    ''')
    
    # Mileage cache table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mileage_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_location TEXT,
        to_location TEXT,
        miles REAL,
        source TEXT,
        cached_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(from_location, to_location)
    )
    ''')
    
    # Activity log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        entity_type TEXT,
        entity_id INTEGER,
        user TEXT,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Archive table for old moves
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS archived_moves (
        id INTEGER PRIMARY KEY,
        move_data TEXT,
        archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        archived_by TEXT
    )
    ''')
    
    # Payment batch tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT UNIQUE,
        move_ids TEXT,
        total_amount REAL,
        factoring_fee REAL,
        net_amount REAL,
        submitted_date TIMESTAMP,
        confirmed_date TIMESTAMP,
        status TEXT DEFAULT 'pending'
    )
    ''')
    
    # Insert default base location if not exists
    cursor.execute('''
    INSERT OR IGNORE INTO locations (location_title, street_address, city, state, zip_code, is_base_location)
    VALUES ('Fleet Memphis', '3716 Hwy 78', 'Memphis', 'TN', '38109', 1)
    ''')
    
    conn.commit()
    conn.close()

# Trailer operations
def add_trailer(trailer_data):
    """Add new trailer"""
    conn = get_connection()
    cursor = conn.cursor()
    
    columns = ', '.join(trailer_data.keys())
    placeholders = ', '.join(['?' for _ in trailer_data])
    
    cursor.execute(f'''
    INSERT INTO trailers ({columns})
    VALUES ({placeholders})
    ''', list(trailer_data.values()))
    
    trailer_id = cursor.lastrowid
    
    # Log activity
    log_activity('add_trailer', 'trailer', trailer_id, trailer_data.get('created_by', 'system'))
    
    conn.commit()
    conn.close()
    return trailer_id

def update_trailer(trailer_id, updates):
    """Update trailer"""
    conn = get_connection()
    cursor = conn.cursor()
    
    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [trailer_id]
    
    cursor.execute(f'''
    UPDATE trailers 
    SET {set_clause}, updated_date = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', values)
    
    conn.commit()
    conn.close()

def get_all_trailers():
    """Get all trailers"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM trailers ORDER BY added_date DESC", conn)
    conn.close()
    return df

def get_available_trailers(trailer_type=None):
    """Get available trailers"""
    conn = get_connection()
    query = "SELECT * FROM trailers WHERE status = 'available'"
    if trailer_type:
        query += f" AND trailer_type = '{trailer_type}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Location operations
def add_location(location_title, street_address, city, state, zip_code=None):
    """Add new location"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO locations (location_title, street_address, city, state, zip_code)
        VALUES (?, ?, ?, ?, ?)
        ''', (location_title, street_address, city, state, zip_code))
        
        location_id = cursor.lastrowid
        conn.commit()
        return location_id
    except sqlite3.IntegrityError:
        # Location already exists
        cursor.execute('''
        SELECT id FROM locations WHERE location_title = ?
        ''', (location_title,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def get_all_locations():
    """Get all locations"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM locations ORDER BY location_title", conn)
    conn.close()
    return df

# Driver operations
def add_driver(driver_data):
    """Add new driver"""
    conn = get_connection()
    cursor = conn.cursor()
    
    columns = ', '.join(driver_data.keys())
    placeholders = ', '.join(['?' for _ in driver_data])
    
    cursor.execute(f'''
    INSERT INTO drivers ({columns})
    VALUES ({placeholders})
    ''', list(driver_data.values()))
    
    driver_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return driver_id

def get_all_drivers():
    """Get all drivers"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM drivers ORDER BY driver_name", conn)
    conn.close()
    return df

def update_driver_status(driver_name, status):
    """Update driver availability status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE drivers SET status = ? WHERE driver_name = ?
    ''', (status, driver_name))
    
    conn.commit()
    conn.close()

# Move operations
def add_trailer_move(move_data):
    """Add new trailer move"""
    conn = get_connection()
    cursor = conn.cursor()
    
    columns = ', '.join(move_data.keys())
    placeholders = ', '.join(['?' for _ in move_data])
    
    cursor.execute(f'''
    INSERT INTO moves ({columns})
    VALUES ({placeholders})
    ''', list(move_data.values()))
    
    move_id = cursor.lastrowid
    
    # Log activity
    log_activity('create_move', 'move', move_id, move_data.get('created_by', 'system'))
    
    conn.commit()
    conn.close()
    return move_id

def get_all_trailer_moves():
    """Get all trailer moves"""
    conn = get_connection()
    df = pd.read_sql_query("""
    SELECT * FROM moves 
    WHERE id NOT IN (SELECT id FROM archived_moves)
    ORDER BY created_at DESC
    """, conn)
    conn.close()
    return df

def update_move_status(move_id, status):
    """Update move status"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE moves 
    SET status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (status, move_id))
    
    conn.commit()
    conn.close()

def update_move_payment_status(move_id, payment_status, additional_data=None):
    """Update payment status of a move"""
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = {'payment_status': payment_status}
    
    if additional_data:
        if 'submitted_date' in additional_data:
            updates['submitted_to_factoring'] = additional_data['submitted_date']
        if 'paid_date' in additional_data:
            updates['payment_received'] = additional_data['paid_date']
    
    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [move_id]
    
    cursor.execute(f'''
    UPDATE moves 
    SET {set_clause}, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', values)
    
    conn.commit()
    conn.close()

# Archive operations
def archive_old_moves(days_old=90):
    """Archive moves older than specified days"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(f'''
    INSERT INTO archived_moves (id, move_data)
    SELECT id, json_object(
        'move_id', move_id,
        'new_trailer', new_trailer,
        'old_trailer', old_trailer,
        'driver_name', driver_name,
        'move_date', move_date,
        'total_miles', total_miles,
        'driver_pay', driver_pay,
        'status', status
    )
    FROM moves
    WHERE julianday('now') - julianday(created_at) > ?
    ''', (days_old,))
    
    # Delete from main table
    cursor.execute(f'''
    DELETE FROM moves
    WHERE julianday('now') - julianday(created_at) > ?
    ''', (days_old,))
    
    conn.commit()
    conn.close()

# Activity logging
def log_activity(action, entity_type, entity_id, user, details=None):
    """Log system activity"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO activity_log (action, entity_type, entity_id, user, details)
    VALUES (?, ?, ?, ?, ?)
    ''', (action, entity_type, entity_id, user, json.dumps(details) if details else None))
    
    conn.commit()
    conn.close()

# Summary statistics
def get_summary_stats():
    """Get summary statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total moves
    cursor.execute("SELECT COUNT(*) FROM moves")
    stats['total_moves'] = cursor.fetchone()[0]
    
    # Active moves
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status IN ('assigned', 'in_progress')")
    stats['active_moves'] = cursor.fetchone()[0]
    
    # Completed moves
    cursor.execute("SELECT COUNT(*) FROM moves WHERE status = 'completed'")
    stats['completed_moves'] = cursor.fetchone()[0]
    
    # Total miles
    cursor.execute("SELECT SUM(total_miles) FROM moves WHERE status = 'completed'")
    result = cursor.fetchone()[0]
    stats['total_miles'] = result if result else 0
    
    # Total revenue
    stats['total_revenue'] = stats['total_miles'] * 2.10
    
    # Available drivers
    cursor.execute("SELECT COUNT(*) FROM drivers WHERE status = 'available'")
    stats['available_drivers'] = cursor.fetchone()[0]
    
    # Available trailers
    cursor.execute("SELECT COUNT(*) FROM trailers WHERE status = 'available'")
    stats['available_trailers'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

# Email history (placeholder for tracking)
def get_email_history(limit=10):
    """Get email history (placeholder)"""
    return pd.DataFrame()  # Empty for now