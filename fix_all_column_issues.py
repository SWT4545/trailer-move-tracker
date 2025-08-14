"""
Fix all database column name issues across ALL files
"""

import os
import re

def fix_file(filepath, replacements):
    """Fix column names in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for old, new in replacements:
            content = re.sub(old, new, content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

# Define all the column name fixes
column_fixes = [
    # Drivers table fixes
    (r'\bd\.name\b', 'd.driver_name'),
    (r'\bdrivers\.name\b', 'drivers.driver_name'),
    (r'SELECT name FROM drivers', 'SELECT driver_name FROM drivers'),
    (r'SELECT DISTINCT name FROM drivers', 'SELECT DISTINCT driver_name FROM drivers'),
    (r'\bd\.company\b', 'd.company_name'),
    (r'\bdrivers\.company\b', 'drivers.company_name'),
    (r'ORDER BY d\.name', 'ORDER BY d.driver_name'),
    (r'ORDER BY name', 'ORDER BY driver_name'),
    (r'ON d\.name = m\.driver_name', 'ON d.driver_name = m.driver_name'),
    (r'ON drivers\.name = moves\.driver_name', 'ON drivers.driver_name = moves.driver_name'),
    
    # Make sure we're using the right column names
    (r"INSERT INTO drivers \(name,", "INSERT INTO drivers (driver_name,"),
    (r"'name':", "'driver_name':"),
    (r'"name":', '"driver_name":'),
]

# List of Python files to check and fix
python_files = [
    'app.py',
    'app_complete_fixes.py',
    'driver_management_enhanced.py',
    'driver_portal.py',
    'driver_portal_enhanced.py',
    'driver_pages.py',
    'driver_self_assignment.py',
    'driver_self_assignment_portal.py',
    'management_dashboard_enhanced.py',
    'user_management.py',
    'user_management_old.py',
    'user_manager.py',
    'enhanced_user_manager.py',
    'system_admin_fixed.py',
    'report_generator_fixed.py',
    'ui_fixes.py',
    'populate_real_data.py',
    'setup_drivers.py',
    'create_driver_profile.py',
    'create_test_driver.py',
    'update_b_smith_dual_role.py',
    'add_driver_role_to_brandon.py'
]

# Additional files that might have driver queries
additional_files = [
    f for f in os.listdir('.')
    if f.endswith('.py') and 'driver' in f.lower()
]

all_files = list(set(python_files + additional_files))

print("Fixing column name issues in all files...")
print("=" * 50)

fixed_count = 0
for filename in all_files:
    if os.path.exists(filename):
        if fix_file(filename, column_fixes):
            print(f"[FIXED] {filename}")
            fixed_count += 1
        else:
            print(f"  No changes needed: {filename}")
    else:
        print(f"  File not found: {filename}")

print("=" * 50)
print(f"Fixed {fixed_count} files")

# Now let's also update the database to ensure consistency
import sqlite3

print("\nUpdating database for consistency...")
conn = sqlite3.connect('trailer_tracker_streamlined.db')
cursor = conn.cursor()

# Ensure all drivers have company_name if they don't
cursor.execute("""
    UPDATE drivers 
    SET company_name = COALESCE(company_name, 'Independent')
    WHERE company_name IS NULL OR company_name = ''
""")

# Ensure all drivers have active status
cursor.execute("""
    UPDATE drivers 
    SET active = 1
    WHERE active IS NULL
""")

conn.commit()
conn.close()

print("[OK] Database updated")
print("\nAll column issues fixed!")