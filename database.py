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
        
        # Create trailers table for trailer management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trailers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trailer_number TEXT UNIQUE NOT NULL,
                trailer_type TEXT NOT NULL CHECK(trailer_type IN ('new', 'old')),
                current_location TEXT,
                status TEXT DEFAULT 'available' CHECK(status IN ('available', 'assigned', 'completed')),
                loaded_status BOOLEAN DEFAULT 0,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_date TIMESTAMP,
                completed_date TIMESTAMP,
                assigned_to_move_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT 0,
                FOREIGN KEY (assigned_to_move_id) REFERENCES trailer_moves(id)
            )
        ''')
        
        # Create trailer_history table for tracking trailer movements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trailer_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trailer_id INTEGER NOT NULL,
                move_id INTEGER,
                status_change TEXT NOT NULL,
                change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                changed_by TEXT,
                notes TEXT,
                FOREIGN KEY (trailer_id) REFERENCES trailers(id),
                FOREIGN KEY (move_id) REFERENCES trailer_moves(id)
            )
        ''')
        
        # Create email_templates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT UNIQUE NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                template_type TEXT DEFAULT 'custom',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create email_recipients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT,
                email_address TEXT UNIQUE NOT NULL,
                company_name TEXT,
                is_default BOOLEAN DEFAULT 0,
                is_favorite BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create email_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipients TEXT NOT NULL,
                cc TEXT,
                bcc TEXT,
                subject TEXT NOT NULL,
                body TEXT,
                attachments TEXT,
                delivery_status TEXT DEFAULT 'sent',
                sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        # Create contractor_update_preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contractor_update_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contractor_name TEXT UNIQUE NOT NULL,
                update_frequency TEXT DEFAULT 'Weekly Summary',
                rate_confirmation_deadline TEXT DEFAULT '48 hours',
                auto_send BOOLEAN DEFAULT 0,
                last_update_sent TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add new columns to trailer_moves table for trailer management
        cursor.execute('''
            PRAGMA table_info(trailer_moves)
        ''')
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'new_trailer_id' not in columns:
            cursor.execute('ALTER TABLE trailer_moves ADD COLUMN new_trailer_id INTEGER')
        if 'old_trailer_id' not in columns:
            cursor.execute('ALTER TABLE trailer_moves ADD COLUMN old_trailer_id INTEGER')
        
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

# Trailer Management Operations
def add_trailer(data):
    """Add a new trailer to the system"""
    with get_connection() as conn:
        cursor = conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f'INSERT INTO trailers ({columns}) VALUES ({placeholders})'
        cursor.execute(query, list(data.values()))
        conn.commit()
        
        # Add to history
        trailer_id = cursor.lastrowid
        add_trailer_history(trailer_id, None, 'added', data.get('notes', ''))
        return trailer_id

def get_all_trailers(trailer_type=None, status=None, include_deleted=False):
    """Get all trailers with optional filters"""
    with get_connection() as conn:
        query = 'SELECT * FROM trailers WHERE 1=1'
        params = []
        
        if not include_deleted:
            query += ' AND deleted = 0'
        
        if trailer_type:
            query += ' AND trailer_type = ?'
            params.append(trailer_type)
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY added_date DESC'
        return pd.read_sql_query(query, conn, params=params)

def get_available_trailers(trailer_type=None):
    """Get available trailers for selection"""
    return get_all_trailers(trailer_type=trailer_type, status='available')

def get_trailer_by_id(trailer_id):
    """Get a single trailer by ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trailers WHERE id = ? AND deleted = 0', (trailer_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def get_trailer_by_number(trailer_number):
    """Get a trailer by its number"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trailers WHERE trailer_number = ? AND deleted = 0', (trailer_number,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def update_trailer(trailer_id, data):
    """Update a trailer"""
    with get_connection() as conn:
        cursor = conn.cursor()
        data['updated_at'] = datetime.now()
        set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
        query = f'UPDATE trailers SET {set_clause} WHERE id = ?'
        cursor.execute(query, list(data.values()) + [trailer_id])
        conn.commit()

def assign_trailer_to_move(trailer_id, move_id):
    """Assign a trailer to a move"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE trailers 
            SET status = 'assigned', 
                assigned_to_move_id = ?, 
                assigned_date = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (move_id, trailer_id))
        conn.commit()
        
        # Add to history
        add_trailer_history(trailer_id, move_id, 'assigned')

def complete_trailer_assignment(trailer_id):
    """Mark a trailer assignment as completed"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get the move_id before updating
        cursor.execute('SELECT assigned_to_move_id FROM trailers WHERE id = ?', (trailer_id,))
        result = cursor.fetchone()
        move_id = result['assigned_to_move_id'] if result else None
        
        cursor.execute('''
            UPDATE trailers 
            SET status = 'completed', 
                completed_date = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (trailer_id,))
        conn.commit()
        
        # Add to history
        add_trailer_history(trailer_id, move_id, 'completed')

def delete_trailer(trailer_id, soft_delete=True):
    """Delete a trailer"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if soft_delete:
            cursor.execute('UPDATE trailers SET deleted = 1 WHERE id = ?', (trailer_id,))
        else:
            cursor.execute('DELETE FROM trailers WHERE id = ?', (trailer_id,))
        conn.commit()

def add_trailer_history(trailer_id, move_id, status_change, notes='', changed_by='system'):
    """Add a history entry for trailer status change"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trailer_history (trailer_id, move_id, status_change, changed_by, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (trailer_id, move_id, status_change, changed_by, notes))
        conn.commit()

def get_trailer_history(trailer_id=None, move_id=None):
    """Get trailer history"""
    with get_connection() as conn:
        query = 'SELECT * FROM trailer_history WHERE 1=1'
        params = []
        
        if trailer_id:
            query += ' AND trailer_id = ?'
            params.append(trailer_id)
        
        if move_id:
            query += ' AND move_id = ?'
            params.append(move_id)
        
        query += ' ORDER BY change_date DESC'
        return pd.read_sql_query(query, conn, params=params)

def get_trailer_statistics():
    """Get statistics for trailer management dashboard"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        stats = {}
        
        # Available new trailers
        cursor.execute("SELECT COUNT(*) as count FROM trailers WHERE trailer_type = 'new' AND status = 'available' AND deleted = 0")
        stats['available_new'] = cursor.fetchone()['count']
        
        # Available old trailers
        cursor.execute("SELECT COUNT(*) as count FROM trailers WHERE trailer_type = 'old' AND status = 'available' AND deleted = 0")
        stats['available_old'] = cursor.fetchone()['count']
        
        # Assigned trailers
        cursor.execute("SELECT COUNT(*) as count FROM trailers WHERE status = 'assigned' AND deleted = 0")
        stats['assigned'] = cursor.fetchone()['count']
        
        # Completed today
        cursor.execute("""
            SELECT COUNT(*) as count FROM trailers 
            WHERE status = 'completed' 
            AND DATE(completed_date) = DATE('now')
            AND deleted = 0
        """)
        stats['completed_today'] = cursor.fetchone()['count']
        
        return stats

# Email Management Operations
def add_email_template(name, subject, body, template_type='custom'):
    """Add or update an email template"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO email_templates (template_name, subject, body, template_type)
            VALUES (?, ?, ?, ?)
        ''', (name, subject, body, template_type))
        conn.commit()
        return cursor.lastrowid

def get_email_template(name):
    """Get an email template by name"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM email_templates WHERE template_name = ?', (name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def get_all_email_templates():
    """Get all email templates"""
    with get_connection() as conn:
        return pd.read_sql_query('SELECT * FROM email_templates ORDER BY template_name', conn)

def add_email_recipient(email, nickname=None, company=None, is_default=False, is_favorite=False):
    """Add or update an email recipient"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO email_recipients 
            (email_address, nickname, company_name, is_default, is_favorite)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, nickname, company, is_default, is_favorite))
        conn.commit()
        return cursor.lastrowid

def get_email_recipients(favorites_only=False):
    """Get email recipients"""
    with get_connection() as conn:
        query = 'SELECT * FROM email_recipients WHERE deleted = 0'
        if favorites_only:
            query += ' AND is_favorite = 1'
        query += ' ORDER BY is_favorite DESC, nickname'
        return pd.read_sql_query(query, conn)

def add_email_history(recipients, subject, body, cc=None, bcc=None, attachments=None, status='sent'):
    """Add email to history"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO email_history 
            (recipients, cc, bcc, subject, body, attachments, delivery_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (recipients, cc, bcc, subject, body, attachments, status))
        conn.commit()
        return cursor.lastrowid

def get_email_history(limit=50):
    """Get email history"""
    with get_connection() as conn:
        return pd.read_sql_query(
            'SELECT * FROM email_history ORDER BY sent_date DESC LIMIT ?',
            conn,
            params=(limit,)
        )

# Contractor Update Preferences
def save_contractor_update_preference(contractor_name, frequency, deadline, auto_send=False):
    """Save or update contractor update preferences"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO contractor_update_preferences 
            (contractor_name, update_frequency, rate_confirmation_deadline, auto_send, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (contractor_name, frequency, deadline, auto_send))
        conn.commit()
        return cursor.lastrowid

def get_contractor_update_preference(contractor_name):
    """Get update preferences for a specific contractor"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM contractor_update_preferences 
            WHERE contractor_name = ?
        ''', (contractor_name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        # Return defaults if no preference saved
        return {
            'update_frequency': 'Weekly Summary',
            'rate_confirmation_deadline': '48 hours',
            'auto_send': False
        }

def get_all_contractor_preferences():
    """Get all contractor update preferences"""
    with get_connection() as conn:
        return pd.read_sql_query(
            'SELECT * FROM contractor_update_preferences ORDER BY contractor_name',
            conn
        )

def mark_update_sent(contractor_name):
    """Mark that an update was sent to a contractor"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE contractor_update_preferences 
            SET last_update_sent = CURRENT_TIMESTAMP
            WHERE contractor_name = ?
        ''', (contractor_name,))
        conn.commit()

# Enhanced Driver Management Functions
def get_driver_by_phone(phone_number):
    """Get driver by phone number"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM drivers WHERE phone_number = ? AND deleted = 0', (phone_number,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def update_driver_profile(driver_id, data):
    """Update driver profile with enhanced fields"""
    with get_connection() as conn:
        cursor = conn.cursor()
        set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
        query = f'UPDATE drivers SET {set_clause} WHERE id = ?'
        cursor.execute(query, list(data.values()) + [driver_id])
        conn.commit()

def create_driver_login(driver_id, username, password_hash):
    """Create login credentials for driver"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE drivers 
            SET username = ?, password_hash = ?, is_active = 1
            WHERE id = ?
        ''', (username, password_hash, driver_id))
        conn.commit()

def authenticate_driver(username, password_hash):
    """Authenticate driver login"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM drivers 
            WHERE username = ? AND password_hash = ? AND is_active = 1 AND deleted = 0
        ''', (username, password_hash))
        row = cursor.fetchone()
        if row:
            # Update last login
            cursor.execute('UPDATE drivers SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (row['id'],))
            conn.commit()
            return dict(row)
        return None

def get_driver_performance(driver_id, week_start=None):
    """Get driver performance metrics"""
    with get_connection() as conn:
        if week_start:
            return pd.read_sql_query('''
                SELECT * FROM driver_performance 
                WHERE driver_id = ? AND week_start = ?
            ''', conn, params=(driver_id, week_start))
        else:
            return pd.read_sql_query('''
                SELECT * FROM driver_performance 
                WHERE driver_id = ? 
                ORDER BY week_start DESC
            ''', conn, params=(driver_id,))

def update_driver_performance(driver_id, week_start, metrics):
    """Update driver performance metrics"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO driver_performance 
            (driver_id, week_start, miles_driven, routes_completed, on_time_count, late_count, earnings, performance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (driver_id, week_start, metrics.get('miles_driven', 0), 
              metrics.get('routes_completed', 0), metrics.get('on_time_count', 0),
              metrics.get('late_count', 0), metrics.get('earnings', 0),
              metrics.get('performance_score', 0)))
        conn.commit()

# Location Trailer Count Management
def get_location_trailer_counts():
    """Get old trailer counts at all locations"""
    with get_connection() as conn:
        return pd.read_sql_query('''
            SELECT 
                l.id,
                l.location_title,
                COALESCE(ltc.old_trailer_count, 0) as old_trailer_count,
                ltc.alert_status,
                ltc.days_since_last_pickup
            FROM locations l
            LEFT JOIN location_trailer_counts ltc ON l.id = ltc.location_id
            WHERE l.deleted = 0
            ORDER BY COALESCE(ltc.old_trailer_count, 0) DESC
        ''', conn)

def update_location_trailer_count(location_name, adjustment):
    """Update trailer count at a location"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get location ID
        cursor.execute('SELECT id FROM locations WHERE location_title = ?', (location_name,))
        location = cursor.fetchone()
        if not location:
            return
        
        location_id = location['id']
        
        # Update or insert count
        cursor.execute('''
            INSERT INTO location_trailer_counts (location_id, location_name, old_trailer_count, last_updated)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(location_id) DO UPDATE SET
                old_trailer_count = old_trailer_count + ?,
                last_updated = CURRENT_TIMESTAMP
        ''', (location_id, location_name, max(0, adjustment), adjustment))
        
        # Update alert status based on count
        cursor.execute('SELECT old_trailer_count FROM location_trailer_counts WHERE location_id = ?', (location_id,))
        result = cursor.fetchone()
        if result:
            count = result['old_trailer_count']
            if count >= 5:
                alert_status = 'red'
            elif count >= 3:
                alert_status = 'yellow'
            else:
                alert_status = 'green'
            
            cursor.execute('''
                UPDATE location_trailer_counts 
                SET alert_status = ? 
                WHERE location_id = ?
            ''', (alert_status, location_id))
        
        conn.commit()

# Route Progress Tracking
def add_route_progress(route_id, milestone, location=None, notes=None):
    """Add route progress milestone"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO route_progress (route_id, milestone, confirmed_location, notes)
            VALUES (?, ?, ?, ?)
        ''', (route_id, milestone, location, notes))
        conn.commit()

def get_route_progress(route_id):
    """Get all progress milestones for a route"""
    with get_connection() as conn:
        return pd.read_sql_query('''
            SELECT * FROM route_progress 
            WHERE route_id = ? 
            ORDER BY timestamp
        ''', conn, params=(route_id,))

# Photo Management
def save_route_photo(route_id, photo_type, photo_data, location=None):
    """Save a photo for a route"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO route_photos (route_id, photo_type, photo_data, location)
            VALUES (?, ?, ?, ?)
        ''', (route_id, photo_type, photo_data, location))
        conn.commit()
        
        # Update photo count on route
        cursor.execute('''
            UPDATE trailer_moves 
            SET photos_captured = (
                SELECT COUNT(*) FROM route_photos WHERE route_id = ?
            )
            WHERE id = ?
        ''', (route_id, route_id))
        conn.commit()

def get_route_photos(route_id):
    """Get all photos for a route"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, photo_type, timestamp, location 
            FROM route_photos 
            WHERE route_id = ?
            ORDER BY timestamp
        ''', (route_id,))
        return [dict(row) for row in cursor.fetchall()]

# Generic Document Management
def save_generic_document(doc_type, name, file_data, is_generic=True):
    """Save a generic document like rate confirmation"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO generic_documents (document_type, document_name, file_data, is_generic)
            VALUES (?, ?, ?, ?)
        ''', (doc_type, name, file_data, is_generic))
        conn.commit()
        return cursor.lastrowid

def get_generic_document(doc_type='rate_confirmation'):
    """Get the generic document"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM generic_documents 
            WHERE document_type = ? AND is_generic = 1
            ORDER BY uploaded_date DESC
            LIMIT 1
        ''', (doc_type,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

# Training System Functions
def get_training_modules(role=None):
    """Get training modules for a specific role"""
    with get_connection() as conn:
        if role:
            return pd.read_sql_query('''
                SELECT * FROM training_modules 
                WHERE role = ? AND is_active = 1
                ORDER BY order_index
            ''', conn, params=(role,))
        else:
            return pd.read_sql_query('''
                SELECT * FROM training_modules 
                WHERE is_active = 1
                ORDER BY role, order_index
            ''', conn)

def save_training_progress(user_id, module_id, score=None, completed=False):
    """Save training progress"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if completed:
            cursor.execute('''
                UPDATE training_progress 
                SET completed_at = CURRENT_TIMESTAMP, score = ?, is_certified = ?
                WHERE user_id = ? AND module_id = ?
            ''', (score, score >= 80 if score else False, user_id, module_id))
        else:
            cursor.execute('''
                INSERT INTO training_progress (user_id, module_id, score)
                VALUES (?, ?, ?)
                ON CONFLICT DO UPDATE SET attempts = attempts + 1
            ''', (user_id, module_id, score))
        conn.commit()

def get_training_progress(user_id):
    """Get training progress for a user"""
    with get_connection() as conn:
        return pd.read_sql_query('''
            SELECT 
                tm.*,
                tp.started_at,
                tp.completed_at,
                tp.score,
                tp.is_certified
            FROM training_modules tm
            LEFT JOIN training_progress tp ON tm.id = tp.module_id AND tp.user_id = ?
            WHERE tm.is_active = 1
            ORDER BY tm.order_index
        ''', conn, params=(user_id,))

# Company Performance Metrics
def get_company_performance(date_from=None, date_to=None):
    """Get company performance metrics"""
    with get_connection() as conn:
        query = 'SELECT * FROM company_performance WHERE 1=1'
        params = []
        
        if date_from:
            query += ' AND metric_date >= ?'
            params.append(date_from)
        if date_to:
            query += ' AND metric_date <= ?'
            params.append(date_to)
        
        query += ' ORDER BY metric_date DESC'
        
        return pd.read_sql_query(query, conn, params=params)

def update_company_performance(date, metrics):
    """Update company performance metrics"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO company_performance 
            (metric_date, routes_completed, routes_in_progress, on_time_percentage, 
             average_completion_hours, fleet_utilization, customer_satisfaction, safety_incidents)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, metrics.get('routes_completed', 0), metrics.get('routes_in_progress', 0),
              metrics.get('on_time_percentage', 0), metrics.get('average_completion_hours', 0),
              metrics.get('fleet_utilization', 0), metrics.get('customer_satisfaction', 0),
              metrics.get('safety_incidents', 0)))
        conn.commit()

# Status Report Generation
def save_status_report(report_date, report_type, report_data, pdf_data=None, generated_by=None):
    """Save a generated status report"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO status_reports 
            (report_date, report_type, report_data, pdf_data, generated_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (report_date, report_type, report_data, pdf_data, generated_by))
        conn.commit()
        return cursor.lastrowid

def get_status_reports(limit=10):
    """Get recent status reports"""
    with get_connection() as conn:
        return pd.read_sql_query('''
            SELECT * FROM status_reports 
            ORDER BY generated_at DESC
            LIMIT ?
        ''', conn, params=(limit,))