"""
Robust Database Connection Manager
Handles all database connections with retry logic and connection pooling
"""

import sqlite3
import os
import time
import streamlit as st
from contextlib import contextmanager
import threading

class DatabaseConnectionManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if not self.initialized:
            self.db_path = self._get_db_path()
            self.max_retries = 3
            self.retry_delay = 0.5
            self.initialized = True
    
    def _get_db_path(self):
        """Get the correct database path"""
        if os.path.exists('trailer_tracker_streamlined.db'):
            return 'trailer_tracker_streamlined.db'
        elif os.path.exists('trailer_data.db'):
            return 'trailer_data.db'
        else:
            # Create new database if none exists
            return 'trailer_tracker_streamlined.db'
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with retry logic"""
        conn = None
        for attempt in range(self.max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                conn.row_factory = sqlite3.Row
                yield conn
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise
            except Exception as e:
                if conn:
                    conn.rollback()
                raise
            finally:
                if conn:
                    conn.close()
    
    def execute_query(self, query, params=None, fetch_one=False):
        """Execute a query with automatic retry and connection management"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                return cursor.fetchone()
            else:
                return cursor.fetchall()
    
    def execute_many(self, query, params_list):
        """Execute many queries with automatic retry"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def table_exists(self, table_name):
        """Check if a table exists"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_query(query, (table_name,), fetch_one=True)
        return result is not None
    
    def ensure_tables(self):
        """Ensure all required tables exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure drivers table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    driver_name TEXT,
                    phone TEXT,
                    email TEXT,
                    status TEXT DEFAULT 'available',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Update driver_name column if needed
            cursor.execute("PRAGMA table_info(drivers)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'driver_name' not in columns:
                cursor.execute("ALTER TABLE drivers ADD COLUMN driver_name TEXT")
                cursor.execute("UPDATE drivers SET driver_name = name WHERE driver_name IS NULL")
            
            # Ensure trailer_moves table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trailer_moves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT,
                    new_trailer TEXT,
                    old_trailer TEXT,
                    pickup_location TEXT,
                    delivery_location TEXT,
                    move_date DATE,
                    pickup_time TIME,
                    total_miles REAL,
                    driver_pay REAL,
                    status TEXT DEFAULT 'assigned',
                    special_instructions TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    pod_uploaded BOOLEAN DEFAULT 0,
                    pod_upload_date TIMESTAMP,
                    payment_status TEXT DEFAULT 'pending',
                    paid_date TIMESTAMP,
                    notes TEXT
                )
            """)
            
            # Ensure trailers table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trailers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trailer_number TEXT UNIQUE NOT NULL,
                    trailer_type TEXT CHECK(trailer_type IN ('new', 'old')),
                    current_location TEXT,
                    status TEXT DEFAULT 'available',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Ensure locations table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_title TEXT UNIQUE NOT NULL,
                    street_address TEXT,
                    city TEXT,
                    state TEXT,
                    zip_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Ensure driver_extended table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS driver_extended (
                    driver_id INTEGER PRIMARY KEY,
                    driver_type TEXT DEFAULT 'company',
                    cdl_number TEXT,
                    cdl_expiry DATE,
                    company_name TEXT,
                    mc_number TEXT,
                    dot_number TEXT,
                    insurance_company TEXT,
                    insurance_policy TEXT,
                    insurance_expiry DATE,
                    truck_number TEXT,
                    trailer_number TEXT,
                    license_state TEXT,
                    hazmat_endorsed BOOLEAN DEFAULT 0,
                    tanker_endorsed BOOLEAN DEFAULT 0,
                    doubles_endorsed BOOLEAN DEFAULT 0,
                    emergency_contact TEXT,
                    emergency_phone TEXT,
                    notes TEXT,
                    address_street TEXT,
                    address_city TEXT,
                    address_state TEXT,
                    address_zip TEXT,
                    FOREIGN KEY (driver_id) REFERENCES drivers(id)
                )
            """)
            
            # Ensure move_changes table exists (for move editor)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS move_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    move_id INTEGER,
                    change_type TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    reason TEXT,
                    changed_by TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Ensure W9 documents table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS w9_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT NOT NULL,
                    driver_id INTEGER,
                    file_name TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tax_year INTEGER,
                    ein_or_ssn TEXT,
                    business_name TEXT,
                    status TEXT DEFAULT 'active',
                    verified_by TEXT,
                    verified_date TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (driver_id) REFERENCES drivers(id)
                )
            """)
            
            conn.commit()

# Global instance
db_manager = DatabaseConnectionManager()

def get_all_drivers_safe():
    """Safely get all drivers with retry logic"""
    try:
        db_manager.ensure_tables()
        
        query = """
            SELECT d.*, 
                   de.driver_type, de.cdl_number, de.company_name,
                   de.address_street, de.address_city, de.address_state, de.address_zip
            FROM drivers d
            LEFT JOIN driver_extended de ON d.id = de.driver_id
            ORDER BY d.name
        """
        
        results = db_manager.execute_query(query)
        
        drivers = []
        for row in results:
            driver = dict(row)
            drivers.append(driver)
        
        return drivers
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def sync_drivers_from_users():
    """Sync drivers from user accounts to drivers table"""
    try:
        # Load user accounts
        import json
        if os.path.exists('user_accounts.json'):
            with open('user_accounts.json', 'r') as f:
                user_data = json.load(f)
            
            drivers_added = 0
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                for username, user_info in user_data['users'].items():
                    if 'driver' in user_info.get('roles', []):
                        driver_name = user_info.get('name', username)
                        
                        # Check if driver exists
                        cursor.execute("SELECT id FROM drivers WHERE name = ?", (driver_name,))
                        if not cursor.fetchone():
                            # Add driver
                            cursor.execute("""
                                INSERT INTO drivers (name, phone, email, status)
                                VALUES (?, ?, ?, 'available')
                            """, (driver_name, user_info.get('phone', ''), user_info.get('email', '')))
                            drivers_added += 1
                
                conn.commit()
            
            return drivers_added
    except Exception as e:
        st.error(f"Sync error: {e}")
        return 0

def refresh_all_connections():
    """Force refresh all database connections"""
    global db_manager
    db_manager = DatabaseConnectionManager()
    db_manager.ensure_tables()
    
    # Clear Streamlit cache
    st.cache_data.clear()
    st.cache_resource.clear()
    
    # Sync drivers
    sync_drivers_from_users()
    
    return True