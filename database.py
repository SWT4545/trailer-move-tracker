import sqlite3
import pandas as pd
from datetime import datetime
from contextlib import contextmanager
import os

DATABASE_PATH = 'data/trailer_moves.db'

@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database with all required tables"""
    os.makedirs('data', exist_ok=True)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Create trailer_moves table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trailer_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                new_trailer TEXT,
                pickup_location TEXT,
                destination TEXT,
                old_trailer TEXT,
                old_pickup TEXT,
                old_destination TEXT,
                assigned_driver TEXT,
                date_assigned DATE,
                completion_date DATE,
                received_ppw BOOLEAN DEFAULT 0,
                processed BOOLEAN DEFAULT 0,
                paid BOOLEAN DEFAULT 0,
                miles REAL,
                rate REAL DEFAULT 2.10,
                factor_fee REAL DEFAULT 0.03,
                load_pay REAL,
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create locations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_title TEXT UNIQUE NOT NULL,
                location_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create drivers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT UNIQUE NOT NULL,
                truck_number TEXT,
                company_name TEXT,
                company_address TEXT,
                dot TEXT,
                mc TEXT,
                insurance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create mileage_cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mileage_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_location TEXT NOT NULL,
                to_location TEXT NOT NULL,
                miles REAL NOT NULL,
                round_trip_miles REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_location, to_location)
            )
        ''')
        
        # Create changes_history table for undo functionality
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS changes_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                operation TEXT NOT NULL,
                old_data TEXT,
                new_data TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()

# Trailer Moves Operations
def add_trailer_move(data):
    """Add a new trailer move"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Calculate load_pay if miles and rate are provided
        if 'miles' in data and 'rate' in data:
            factor_fee = data.get('factor_fee', 0.03)
            data['load_pay'] = data['miles'] * data['rate'] * (1 - factor_fee)
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f'INSERT INTO trailer_moves ({columns}) VALUES ({placeholders})'
        
        cursor.execute(query, list(data.values()))
        conn.commit()
        return cursor.lastrowid

def get_all_trailer_moves(include_deleted=False):
    """Get all trailer moves as a DataFrame"""
    with get_connection() as conn:
        query = 'SELECT * FROM trailer_moves'
        if not include_deleted:
            query += ' WHERE deleted = 0'
        query += ' ORDER BY date_assigned DESC'
        return pd.read_sql_query(query, conn)

def update_trailer_move(move_id, data):
    """Update a trailer move"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Calculate load_pay if miles and rate are updated
        if 'miles' in data and 'rate' in data:
            factor_fee = data.get('factor_fee', 0.03)
            data['load_pay'] = data['miles'] * data['rate'] * (1 - factor_fee)
        
        data['updated_at'] = datetime.now()
        
        set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
        query = f'UPDATE trailer_moves SET {set_clause} WHERE id = ?'
        
        cursor.execute(query, list(data.values()) + [move_id])
        conn.commit()

def delete_trailer_move(move_id, soft_delete=True):
    """Delete a trailer move (soft delete by default)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if soft_delete:
            cursor.execute('UPDATE trailer_moves SET deleted = 1 WHERE id = ?', (move_id,))
        else:
            cursor.execute('DELETE FROM trailer_moves WHERE id = ?', (move_id,))
        
        conn.commit()

def get_trailer_move_by_id(move_id):
    """Get a single trailer move by ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trailer_moves WHERE id = ? AND deleted = 0', (move_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

# Location Operations
def add_location(location_title, location_address=None):
    """Add a new location"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO locations (location_title, location_address) VALUES (?, ?)',
            (location_title, location_address)
        )
        conn.commit()
        return cursor.lastrowid

def get_all_locations(include_deleted=False):
    """Get all locations"""
    with get_connection() as conn:
        query = 'SELECT * FROM locations'
        if not include_deleted:
            query += ' WHERE deleted = 0'
        query += ' ORDER BY location_title'
        return pd.read_sql_query(query, conn)

def update_location(location_id, data):
    """Update a location"""
    with get_connection() as conn:
        cursor = conn.cursor()
        set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
        query = f'UPDATE locations SET {set_clause} WHERE id = ?'
        cursor.execute(query, list(data.values()) + [location_id])
        conn.commit()

def delete_location(location_id, soft_delete=True):
    """Delete a location"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if soft_delete:
            cursor.execute('UPDATE locations SET deleted = 1 WHERE id = ?', (location_id,))
        else:
            cursor.execute('DELETE FROM locations WHERE id = ?', (location_id,))
        conn.commit()

# Driver Operations
def add_driver(driver_data):
    """Add a new driver"""
    with get_connection() as conn:
        cursor = conn.cursor()
        columns = ', '.join(driver_data.keys())
        placeholders = ', '.join(['?' for _ in driver_data])
        query = f'INSERT INTO drivers ({columns}) VALUES ({placeholders})'
        cursor.execute(query, list(driver_data.values()))
        conn.commit()
        return cursor.lastrowid

def get_all_drivers(include_deleted=False):
    """Get all drivers"""
    with get_connection() as conn:
        query = 'SELECT * FROM drivers'
        if not include_deleted:
            query += ' WHERE deleted = 0'
        query += ' ORDER BY driver_name'
        return pd.read_sql_query(query, conn)

def update_driver(driver_id, data):
    """Update a driver"""
    with get_connection() as conn:
        cursor = conn.cursor()
        set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
        query = f'UPDATE drivers SET {set_clause} WHERE id = ?'
        cursor.execute(query, list(data.values()) + [driver_id])
        conn.commit()

def delete_driver(driver_id, soft_delete=True):
    """Delete a driver"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if soft_delete:
            cursor.execute('UPDATE drivers SET deleted = 1 WHERE id = ?', (driver_id,))
        else:
            cursor.execute('DELETE FROM drivers WHERE id = ?', (driver_id,))
        conn.commit()

# Mileage Cache Operations
def add_mileage_cache(from_location, to_location, miles):
    """Add or update mileage cache"""
    with get_connection() as conn:
        cursor = conn.cursor()
        round_trip_miles = miles * 2
        cursor.execute('''
            INSERT OR REPLACE INTO mileage_cache 
            (from_location, to_location, miles, round_trip_miles) 
            VALUES (?, ?, ?, ?)
        ''', (from_location, to_location, miles, round_trip_miles))
        conn.commit()

def get_cached_mileage(from_location, to_location):
    """Get cached mileage between two locations"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Check both directions
        cursor.execute('''
            SELECT miles, round_trip_miles FROM mileage_cache 
            WHERE (from_location = ? AND to_location = ?) 
            OR (from_location = ? AND to_location = ?)
        ''', (from_location, to_location, to_location, from_location))
        result = cursor.fetchone()
        if result:
            return dict(result)
        return None

def get_all_mileage_cache():
    """Get all cached mileages"""
    with get_connection() as conn:
        return pd.read_sql_query(
            'SELECT * FROM mileage_cache ORDER BY from_location, to_location', 
            conn
        )

def delete_mileage_cache(cache_id):
    """Delete a mileage cache entry"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM mileage_cache WHERE id = ?', (cache_id,))
        conn.commit()

# Summary Statistics
def get_summary_stats():
    """Get summary statistics for the dashboard"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        stats = {}
        
        # Total moves
        cursor.execute('SELECT COUNT(*) as total FROM trailer_moves WHERE deleted = 0')
        stats['total_moves'] = cursor.fetchone()['total']
        
        # Unpaid moves
        cursor.execute('SELECT COUNT(*) as unpaid FROM trailer_moves WHERE paid = 0 AND deleted = 0')
        stats['unpaid_moves'] = cursor.fetchone()['unpaid']
        
        # Total unpaid amount
        cursor.execute('''
            SELECT SUM(load_pay) as total_unpaid 
            FROM trailer_moves 
            WHERE paid = 0 AND deleted = 0
        ''')
        result = cursor.fetchone()
        stats['total_unpaid'] = result['total_unpaid'] if result['total_unpaid'] else 0
        
        # In progress moves (assigned but not completed)
        cursor.execute('''
            SELECT COUNT(*) as in_progress 
            FROM trailer_moves 
            WHERE completion_date IS NULL AND deleted = 0
        ''')
        stats['in_progress'] = cursor.fetchone()['in_progress']
        
        # Total miles
        cursor.execute('SELECT SUM(miles) as total_miles FROM trailer_moves WHERE deleted = 0')
        result = cursor.fetchone()
        stats['total_miles'] = result['total_miles'] if result['total_miles'] else 0
        
        return stats

# Undo functionality
def save_change_history(table_name, record_id, operation, old_data=None, new_data=None):
    """Save change history for undo functionality"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO changes_history (table_name, record_id, operation, old_data, new_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (table_name, record_id, operation, str(old_data), str(new_data)))
        conn.commit()

def get_recent_changes(limit=10):
    """Get recent changes for undo functionality"""
    with get_connection() as conn:
        return pd.read_sql_query(
            'SELECT * FROM changes_history ORDER BY changed_at DESC LIMIT ?',
            conn,
            params=(limit,)
        )