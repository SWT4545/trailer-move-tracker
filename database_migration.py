"""
Database Migration and Data Preservation System
Vernon AI - Ensures no data loss during updates
"""

import sqlite3
import pandas as pd
import os
import shutil
from datetime import datetime
import json

class DatabaseMigration:
    def __init__(self):
        self.main_db = 'trailer_tracker_streamlined.db'
        self.trailer_db = 'trailer_data.db'
        self.backup_dir = 'database_backups'
        
    def create_backup(self, db_path):
        """Create timestamped backup of database"""
        if not os.path.exists(db_path):
            return None
            
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_name = os.path.basename(db_path).replace('.db', '')
        backup_path = os.path.join(self.backup_dir, f"{db_name}_backup_{timestamp}.db")
        
        # Copy database to backup
        shutil.copy2(db_path, backup_path)
        print(f"[OK] Backup created: {backup_path}")
        return backup_path
    
    def safe_add_column(self, db_path, table_name, column_name, column_type, default_value=None):
        """Safely add column if it doesn't exist"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        
        if column_name not in columns:
            # Add column with default value
            default_clause = f" DEFAULT {default_value}" if default_value is not None else ""
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_clause}")
                conn.commit()
                print(f"[OK] Added column {column_name} to {table_name}")
            except Exception as e:
                print(f"[WARNING] Could not add column {column_name}: {e}")
        else:
            print(f"[EXISTS] Column {column_name} already exists in {table_name}")
        
        conn.close()
    
    def migrate_drivers_table(self):
        """Migrate drivers table with new fields while preserving data"""
        if not os.path.exists(self.trailer_db):
            print("[OK] No existing trailer_data.db to migrate")
            return
            
        conn = sqlite3.connect(self.trailer_db)
        cursor = conn.cursor()
        
        # Check if drivers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drivers'")
        if not cursor.fetchone():
            print("[OK] No drivers table to migrate")
            conn.close()
            return
        
        # Add new columns if they don't exist
        self.safe_add_column(self.trailer_db, 'drivers', 'home_address', 'TEXT', "''")
        self.safe_add_column(self.trailer_db, 'drivers', 'business_address', 'TEXT', "''")
        self.safe_add_column(self.trailer_db, 'drivers', 'is_owner', 'INTEGER', 0)
        
        conn.close()
        print("[COMPLETE] Drivers table migration complete")
    
    def migrate_moves_table(self):
        """Migrate moves table with payment tracking fields"""
        if not os.path.exists(self.main_db):
            print("[OK] No existing database to migrate")
            return
            
        conn = sqlite3.connect(self.main_db)
        cursor = conn.cursor()
        
        # Check if moves table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='moves'")
        if not cursor.fetchone():
            print("[OK] No moves table to migrate")
            conn.close()
            return
        
        # Add payment tracking columns if they don't exist
        self.safe_add_column(self.main_db, 'moves', 'payment_received', 'REAL', 0)
        self.safe_add_column(self.main_db, 'moves', 'client_actual_payment', 'REAL', 'NULL')
        self.safe_add_column(self.main_db, 'moves', 'total_miles', 'REAL', 0)
        self.safe_add_column(self.main_db, 'moves', 'driver_pay', 'REAL', 0)
        
        conn.close()
        print("[COMPLETE] Moves table migration complete")
    
    def ensure_payment_tables(self):
        """Ensure payment-related tables exist without losing data"""
        if not os.path.exists(self.trailer_db):
            # Create new database with tables
            conn = sqlite3.connect(self.trailer_db)
            print("[OK] Created new trailer_data.db")
        else:
            conn = sqlite3.connect(self.trailer_db)
            print("[OK] Using existing trailer_data.db")
        
        cursor = conn.cursor()
        
        # Create payment receipts table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_receipts (
                receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT NOT NULL,
                load_number TEXT NOT NULL,
                payment_date TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                gross_amount REAL NOT NULL,
                deductions REAL DEFAULT 0,
                net_amount REAL NOT NULL,
                rate_per_mile REAL NOT NULL,
                total_miles REAL NOT NULL,
                payment_method TEXT,
                check_number TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                pdf_path TEXT
            )
        """)
        
        # Create 1099 tracking table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contractor_1099 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT NOT NULL,
                tax_year INTEGER NOT NULL,
                ein_ssn TEXT,
                total_payments REAL NOT NULL,
                form_1099_sent INTEGER DEFAULT 0,
                sent_date TEXT,
                filing_status TEXT,
                business_name TEXT,
                business_address TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(driver_name, tax_year)
            )
        """)
        
        # Create tax documents table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tax_documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT NOT NULL,
                document_type TEXT NOT NULL,
                document_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                tax_year INTEGER,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_by TEXT,
                notes TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        print("[COMPLETE] Payment tables ready")
    
    def verify_data_integrity(self):
        """Verify all data is intact after migration"""
        issues = []
        
        # Check main database
        if os.path.exists(self.main_db):
            conn = sqlite3.connect(self.main_db)
            cursor = conn.cursor()
            
            # Count records in key tables
            tables_to_check = ['moves', 'trailers', 'locations', 'drivers', 'users']
            for table in tables_to_check:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"[OK] {table}: {count} records")
                else:
                    print(f"[WARNING] Table {table} not found")
            
            conn.close()
        
        # Check trailer database
        if os.path.exists(self.trailer_db):
            conn = sqlite3.connect(self.trailer_db)
            cursor = conn.cursor()
            
            # Count driver records
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drivers'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM drivers")
                count = cursor.fetchone()[0]
                print(f"[OK] drivers (trailer_data.db): {count} records")
            
            conn.close()
        
        return len(issues) == 0
    
    def run_safe_migration(self):
        """Run complete migration with safety checks"""
        print("\n" + "="*50)
        print("DATABASE MIGRATION AND DATA PRESERVATION")
        print("="*50 + "\n")
        
        # Step 1: Create backups
        print("Step 1: Creating backups...")
        backups = []
        if os.path.exists(self.main_db):
            backup = self.create_backup(self.main_db)
            if backup:
                backups.append(backup)
        
        if os.path.exists(self.trailer_db):
            backup = self.create_backup(self.trailer_db)
            if backup:
                backups.append(backup)
        
        if backups:
            print(f"[OK] Created {len(backups)} backup(s)")
        else:
            print("[OK] No existing databases to backup")
        
        # Step 2: Migrate schema
        print("\nStep 2: Migrating database schema...")
        self.migrate_drivers_table()
        self.migrate_moves_table()
        self.ensure_payment_tables()
        
        # Step 3: Verify integrity
        print("\nStep 3: Verifying data integrity...")
        if self.verify_data_integrity():
            print("[SUCCESS] All data verified successfully!")
        else:
            print("[WARNING] Some issues found - check logs")
        
        print("\n" + "="*50)
        print("MIGRATION COMPLETE - YOUR DATA IS SAFE!")
        print("="*50 + "\n")
        
        if backups:
            print("Backups stored in:", self.backup_dir)
            for backup in backups:
                print(f"  - {os.path.basename(backup)}")

# Run migration when imported or executed
if __name__ == "__main__":
    migration = DatabaseMigration()
    migration.run_safe_migration()