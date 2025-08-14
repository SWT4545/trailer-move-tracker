"""
Comprehensive fix for ALL database column issues
"""

import sqlite3
import os
import glob

def get_actual_columns():
    """Get actual column names from database"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    tables_columns = {}
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        tables_columns[table_name] = [col[1] for col in columns]
    
    conn.close()
    return tables_columns

def fix_python_files():
    """Fix column references in all Python files"""
    
    # Get actual columns
    tables = get_actual_columns()
    
    # Define replacements based on actual columns
    replacements = []
    
    # Activity log fixes
    if 'activity_log' in tables:
        cols = tables['activity_log']
        if 'user' in cols and 'username' not in cols:
            replacements.append(('SELECT timestamp, username, action', 'SELECT timestamp, user, action'))
            replacements.append(('activity_log.username', 'activity_log.user'))
            replacements.append(("'username'", "'user'"))
            replacements.append(('"username"', '"user"'))
            replacements.append(('WHERE username', 'WHERE user'))
            replacements.append(('ORDER BY username', 'ORDER BY user'))
    
    # Users table fixes
    if 'users' in tables:
        cols = tables['users']
        print(f"Users table columns: {cols}")
    
    # Drivers table fixes
    if 'drivers' in tables:
        cols = tables['drivers']
        print(f"Drivers table columns: {cols}")
    
    # Apply fixes to all Python files
    python_files = glob.glob('*.py')
    
    for filepath in python_files:
        if filepath == 'fix_all_db_columns.py':
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            
            # Apply replacements
            for old, new in replacements:
                if old in content:
                    content = content.replace(old, new)
                    print(f"Fixed '{old}' -> '{new}' in {filepath}")
            
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[UPDATED] {filepath}")
                
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

def fix_specific_files():
    """Fix specific known issues"""
    
    # Fix system_admin_fixed.py
    fixes = [
        ('system_admin_fixed.py', 
         'SELECT timestamp, username, action, details', 
         'SELECT timestamp, user, action, details'),
        ('system_admin_fixed.py',
         'SELECT timestamp, username, action FROM activity_log',
         'SELECT timestamp, user, action FROM activity_log'),
        ('app.py',
         'SELECT timestamp, username, action, details\n        FROM activity_log',
         'SELECT timestamp, user, action, details\n        FROM activity_log'),
        ('app.py',
         'DELETE FROM activity_log \n        WHERE action',
         'DELETE FROM activity_log \n        WHERE action'),
        ('ui_fixes.py',
         'SELECT timestamp, username, action',
         'SELECT timestamp, user, action'),
    ]
    
    for filename, old, new in fixes:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if old in content:
                    content = content.replace(old, new)
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"[FIXED] {filename}: activity_log.username -> activity_log.user")
            except Exception as e:
                print(f"Error fixing {filename}: {e}")

def add_missing_columns():
    """Add any missing columns that are expected"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    # Check if activity_log needs username column (for compatibility)
    cursor.execute("PRAGMA table_info(activity_log)")
    cols = [col[1] for col in cursor.fetchall()]
    
    if 'username' not in cols and 'user' in cols:
        # Add username as alias for user
        try:
            cursor.execute("ALTER TABLE activity_log ADD COLUMN username TEXT")
            cursor.execute("UPDATE activity_log SET username = user")
            print("[ADDED] username column to activity_log for compatibility")
        except:
            pass
    
    conn.commit()
    conn.close()

def verify_queries():
    """Verify all queries work"""
    conn = sqlite3.connect('trailer_tracker_streamlined.db')
    cursor = conn.cursor()
    
    tests = [
        ("Activity log", "SELECT timestamp, user, action, details FROM activity_log ORDER BY timestamp DESC LIMIT 10"),
        ("Users", "SELECT id, username, role, active FROM users"),
        ("Drivers", "SELECT driver_name, company_name, active FROM drivers"),
        ("Trailers", "SELECT trailer_number, trailer_type, is_new FROM trailers LIMIT 5"),
        ("Moves", "SELECT id, move_id, delivery_status FROM moves LIMIT 5"),
    ]
    
    print("\nVerifying queries:")
    print("-" * 50)
    
    for name, query in tests:
        try:
            cursor.execute(query)
            count = len(cursor.fetchall())
            print(f"[OK] {name}: {count} records")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
    
    conn.close()

def main():
    print("=" * 60)
    print("COMPREHENSIVE DATABASE COLUMN FIX")
    print("=" * 60)
    
    # Step 1: Get actual columns
    print("\n1. Analyzing database structure...")
    tables = get_actual_columns()
    print(f"   Found {len(tables)} tables")
    
    # Step 2: Fix Python files
    print("\n2. Fixing Python files...")
    fix_python_files()
    
    # Step 3: Fix specific known issues
    print("\n3. Fixing specific files...")
    fix_specific_files()
    
    # Step 4: Add compatibility columns
    print("\n4. Adding compatibility columns...")
    add_missing_columns()
    
    # Step 5: Verify
    print("\n5. Verifying queries...")
    verify_queries()
    
    print("\n" + "=" * 60)
    print("FIXES COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()