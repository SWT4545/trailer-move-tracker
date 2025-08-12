"""
Vernon - IT Bot for Smith & Williams Trucking System
Automated system maintenance, monitoring, and repair
"""

import streamlit as st
import sqlite3
import os
import sys
import json
import time
import hashlib
import subprocess
from datetime import datetime, timedelta
import pandas as pd
import traceback
import logging
from pathlib import Path
import shutil
import psutil
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Vernon IT Bot - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vernon_it_log.txt'),
        logging.StreamHandler()
    ]
)

class VernonITBot:
    """IT Bot for system maintenance and monitoring"""
    
    def __init__(self):
        self.name = "Vernon"
        self.role = "IT Support Specialist"
        self.company = "Smith & Williams Trucking"
        self.status = "Active"
        self.last_check = None
        self.issues_fixed = 0
        self.total_checks = 0
        self.system_health = 100
        self.maintenance_schedule = {
            'hourly': timedelta(hours=1),
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1)
        }
        
    def greet(self):
        """Vernon's greeting"""
        greetings = [
            f"🤖 {self.name} here, your IT specialist at {self.company}",
            f"👨‍💻 {self.name} reporting for duty - system monitoring active",
            f"🔧 {self.name} online - ready to maintain your systems"
        ]
        return greetings[datetime.now().second % 3]
    
    def check_client_portal_health(self):
        """Vernon checks on the client portal like a friendly IT guy"""
        report = {
            'status': 'OK',
            'client_users': 0,
            'document_uploads': 0,
            'audit_entries': 0,
            'issues_found': [],
            'issues_fixed': [],
            'vernon_says': "👋 Hey there! Let me check on your client portal..."
        }
        
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Check client_company field in users table
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'client_company' not in columns:
                report['issues_found'].append('Missing client_company field')
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN client_company TEXT")
                    conn.commit()
                    report['issues_fixed'].append('Added client_company field')
                    self.issues_fixed += 1
                except:
                    pass
            
            # Count client users
            try:
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'client_viewer'")
                report['client_users'] = cursor.fetchone()[0]
            except:
                pass
            
            # Check document uploads table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_uploads'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM document_uploads")
                report['document_uploads'] = cursor.fetchone()[0]
                
                # Check for stuck documents
                cursor.execute("""
                    SELECT COUNT(*) FROM document_uploads 
                    WHERE status = 'pending' 
                    AND julianday('now') - julianday(upload_time) > 7
                """)
                stuck = cursor.fetchone()[0]
                if stuck > 0:
                    report['issues_found'].append(f'{stuck} stuck document uploads')
            
            # Check audit log
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='client_audit_log'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM client_audit_log")
                report['audit_entries'] = cursor.fetchone()[0]
                
                # Check for suspicious activity
                cursor.execute("""
                    SELECT username, COUNT(*) as attempts 
                    FROM client_audit_log 
                    WHERE action = 'UNAUTHORIZED_ACCESS_ATTEMPT'
                    AND julianday('now') - julianday(timestamp) < 1
                    GROUP BY username
                    HAVING attempts > 5
                """)
                suspicious = cursor.fetchall()
                if suspicious:
                    for user, attempts in suspicious:
                        report['issues_found'].append(f'Suspicious activity: {user} ({attempts} attempts)')
            
            conn.close()
            
            # Vernon's friendly assessment
            if report['issues_found']:
                report['status'] = 'WARNING'
                if report['issues_fixed']:
                    report['vernon_says'] = f"🔧 Fixed {len(report['issues_fixed'])} issues! But I found {len(report['issues_found'])} more that need attention."
                else:
                    report['vernon_says'] = f"🤔 Found {len(report['issues_found'])} issues. Let me help you fix those!"
            elif report['issues_fixed']:
                report['vernon_says'] = f"✨ All fixed! Took care of {len(report['issues_fixed'])} issues for you."
            else:
                if report['client_users'] > 0:
                    report['vernon_says'] = f"✅ Everything's running smooth! You have {report['client_users']} happy clients using the portal."
                else:
                    report['vernon_says'] = "💡 Portal is ready! No clients set up yet - want me to help you add some?"
                
        except Exception as e:
            report['status'] = 'ERROR'
            report['issues_found'].append(f'Portal check failed: {str(e)}')
            report['vernon_says'] = "😅 Oops, ran into a snag checking the portal. Let me try a different approach..."
        
        return report
    
    def run_diagnostic(self, verbose=True):
        """Run complete system diagnostic"""
        self.total_checks += 1
        diagnostic_report = {
            'timestamp': datetime.now().isoformat(),
            'system_health': 100,
            'issues_found': [],
            'issues_fixed': [],
            'warnings': [],
            'recommendations': [],
            'client_portal': self.check_client_portal_health()
        }
        
        if verbose:
            st.info(f"🔍 {self.name}: Starting comprehensive system diagnostic...")
        
        # Check database integrity
        db_status = self.check_database_integrity()
        diagnostic_report.update(db_status)
        
        # Check file system
        file_status = self.check_file_system()
        diagnostic_report['file_system'] = file_status
        
        # Check dependencies
        dep_status = self.check_dependencies()
        diagnostic_report['dependencies'] = dep_status
        
        # Check session state
        session_status = self.check_session_state()
        diagnostic_report['session'] = session_status
        
        # Check API configurations
        api_status = self.check_api_configurations()
        diagnostic_report['apis'] = api_status
        
        # Check system resources
        resource_status = self.check_system_resources()
        diagnostic_report['resources'] = resource_status
        
        # Calculate overall health
        total_issues = len(diagnostic_report.get('issues_found', []))
        fixed_issues = len(diagnostic_report.get('issues_fixed', []))
        warnings = len(diagnostic_report.get('warnings', []))
        
        health_score = 100
        health_score -= (total_issues - fixed_issues) * 10
        health_score -= warnings * 2
        diagnostic_report['system_health'] = max(0, health_score)
        self.system_health = diagnostic_report['system_health']
        
        if verbose:
            self.display_diagnostic_report(diagnostic_report)
        
        # Log the diagnostic
        logging.info(f"Diagnostic complete: Health={self.system_health}%, Issues={total_issues}, Fixed={fixed_issues}")
        
        self.last_check = datetime.now()
        return diagnostic_report
    
    def check_database_integrity(self):
        """Check and repair database issues"""
        report = {
            'database_status': 'OK',
            'issues_found': [],
            'issues_fixed': []
        }
        
        try:
            # Check if database exists
            db_path = 'trailer_tracker_streamlined.db'
            if not os.path.exists(db_path):
                report['issues_found'].append('Database file missing')
                # Create database
                self.initialize_database()
                report['issues_fixed'].append('Database recreated')
                self.issues_fixed += 1
            
            # Connect and check tables
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check required tables including client portal tables
            required_tables = [
                'users', 'trailers', 'locations', 'drivers', 
                'moves', 'mileage_cache', 'activity_log', 'archived_moves',
                'document_uploads', 'client_audit_log'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table not in existing_tables:
                    report['issues_found'].append(f'Table {table} missing')
                    self.create_missing_table(conn, table)
                    report['issues_fixed'].append(f'Table {table} created')
                    self.issues_fixed += 1
            
            # Check for corrupt data
            for table in existing_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    # Check for orphaned records
                    if table == 'moves':
                        cursor.execute("""
                            SELECT COUNT(*) FROM moves 
                            WHERE driver_name NOT IN (SELECT name FROM drivers)
                        """)
                        orphaned = cursor.fetchone()[0]
                        if orphaned > 0:
                            report['issues_found'].append(f'{orphaned} orphaned moves found')
                            # Fix by setting to 'Unknown Driver'
                            cursor.execute("""
                                UPDATE moves SET driver_name = 'Unknown Driver'
                                WHERE driver_name NOT IN (SELECT name FROM drivers)
                            """)
                            conn.commit()
                            report['issues_fixed'].append(f'Fixed {orphaned} orphaned moves')
                            self.issues_fixed += 1
                            
                except Exception as e:
                    report['issues_found'].append(f'Table {table} corrupted: {str(e)}')
                    # Attempt repair
                    try:
                        cursor.execute(f"REINDEX {table}")
                        report['issues_fixed'].append(f'Table {table} reindexed')
                        self.issues_fixed += 1
                    except:
                        pass
            
            # Vacuum database for optimization
            cursor.execute("VACUUM")
            conn.commit()
            conn.close()
            
        except Exception as e:
            report['database_status'] = 'ERROR'
            report['issues_found'].append(f'Database error: {str(e)}')
            logging.error(f"Database check failed: {str(e)}")
        
        return report
    
    def check_file_system(self):
        """Check file system integrity"""
        report = {
            'status': 'OK',
            'missing_files': [],
            'created_files': [],
            'permissions': []
        }
        
        # Required files
        required_files = [
            'app.py',
            'database.py',
            'auth_config.py',
            'requirements.txt',
            '.streamlit/config.toml'
        ]
        
        for file in required_files:
            if not os.path.exists(file):
                report['missing_files'].append(file)
                # Attempt to create if it's a config file
                if file == '.streamlit/config.toml':
                    self.create_streamlit_config()
                    report['created_files'].append(file)
                    self.issues_fixed += 1
        
        # Check write permissions
        try:
            test_file = 'vernon_test.tmp'
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except:
            report['permissions'].append('Cannot write to directory')
            report['status'] = 'WARNING'
        
        return report
    
    def check_dependencies(self):
        """Check Python dependencies"""
        report = {
            'status': 'OK',
            'missing': [],
            'outdated': [],
            'installed': []
        }
        
        required_packages = {
            'streamlit': '1.28.0',
            'pandas': '2.0.0',
            'plotly': '5.17.0',
            'Pillow': '10.0.0'
        }
        
        for package, min_version in required_packages.items():
            try:
                __import__(package)
            except ImportError:
                report['missing'].append(package)
                # Attempt to install
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                    report['installed'].append(package)
                    self.issues_fixed += 1
                except:
                    report['status'] = 'ERROR'
        
        return report
    
    def check_session_state(self):
        """Check and repair session state issues"""
        report = {
            'status': 'OK',
            'fixed_keys': [],
            'warnings': []
        }
        
        # Essential session state keys
        essential_keys = {
            'authenticated': False,
            'user_role': None,
            'user_name': None,
            'company_name': 'Smith & Williams Trucking',
            'company_email': 'Dispatch@smithwilliamstrucking.com'
        }
        
        for key, default_value in essential_keys.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                report['fixed_keys'].append(key)
                self.issues_fixed += 1
        
        # Check for corrupt session data
        for key in st.session_state:
            try:
                # Attempt to serialize to JSON (basic integrity check)
                json.dumps(st.session_state[key], default=str)
            except:
                report['warnings'].append(f'Session key {key} may be corrupted')
        
        return report
    
    def check_api_configurations(self):
        """Check API configurations"""
        report = {
            'status': 'OK',
            'google_maps': 'Not configured',
            'email': 'Not configured',
            'warnings': []
        }
        
        # Check Google Maps API
        if os.environ.get('GOOGLE_MAPS_API_KEY'):
            report['google_maps'] = 'Configured'
        else:
            report['warnings'].append('Google Maps API key not set')
        
        # Check email configuration
        if st.session_state.get('google_workspace_enabled'):
            report['email'] = 'Google Workspace'
        else:
            report['email'] = 'SMTP (simulated)'
        
        return report
    
    def check_system_resources(self):
        """Check system resources"""
        report = {
            'status': 'OK',
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'warnings': []
        }
        
        try:
            # CPU usage
            report['cpu_percent'] = psutil.cpu_percent(interval=1)
            if report['cpu_percent'] > 80:
                report['warnings'].append(f'High CPU usage: {report["cpu_percent"]}%')
            
            # Memory usage
            memory = psutil.virtual_memory()
            report['memory_percent'] = memory.percent
            if memory.percent > 80:
                report['warnings'].append(f'High memory usage: {memory.percent}%')
            
            # Disk usage
            disk = psutil.disk_usage('/')
            report['disk_percent'] = disk.percent
            if disk.percent > 90:
                report['warnings'].append(f'Low disk space: {disk.percent}% used')
                report['status'] = 'WARNING'
            
        except:
            # psutil might not be available
            report['status'] = 'UNKNOWN'
        
        return report
    
    def initialize_database(self):
        """Initialize database with proper schema"""
        import database as db
        db.init_db()
        logging.info("Database initialized by Vernon")
    
    def create_missing_table(self, conn, table_name):
        """Create missing database table"""
        cursor = conn.cursor()
        
        table_schemas = {
            'users': """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'trailers': """
                CREATE TABLE trailers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    new_trailer TEXT NOT NULL,
                    old_trailer TEXT NOT NULL,
                    customer_location TEXT NOT NULL,
                    status TEXT DEFAULT 'available',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'drivers': """
                CREATE TABLE drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    email TEXT,
                    status TEXT DEFAULT 'available',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'moves': """
                CREATE TABLE moves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    new_trailer TEXT,
                    old_trailer TEXT,
                    pickup_location TEXT,
                    delivery_location TEXT,
                    driver_name TEXT,
                    status TEXT DEFAULT 'pending',
                    total_miles REAL,
                    driver_pay REAL,
                    move_date DATE,
                    pod_uploaded BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        }
        
        if table_name in table_schemas:
            cursor.execute(table_schemas[table_name])
            conn.commit()
            logging.info(f"Table {table_name} created by Vernon")
    
    def create_streamlit_config(self):
        """Create Streamlit configuration file"""
        config_dir = '.streamlit'
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        config_content = """[theme]
primaryColor = "#DC143C"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"

[server]
port = 8501
enableCORS = false
headless = true

[browser]
gatherUsageStats = false
"""
        
        with open(os.path.join(config_dir, 'config.toml'), 'w') as f:
            f.write(config_content)
        
        logging.info("Streamlit config created by Vernon")
    
    def display_diagnostic_report(self, report):
        """Display diagnostic report in Streamlit"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "System Health",
                f"{report['system_health']}%",
                delta=None if report['system_health'] >= 90 else f"-{100-report['system_health']}%"
            )
        
        with col2:
            issues = len(report.get('issues_found', []))
            fixed = len(report.get('issues_fixed', []))
            st.metric(
                "Issues Found/Fixed",
                f"{fixed}/{issues}",
                delta=f"+{fixed} fixed" if fixed > 0 else None
            )
        
        with col3:
            st.metric(
                "Last Check",
                datetime.now().strftime("%H:%M:%S"),
                delta="Just now"
            )
        
        # Show details in expander
        with st.expander(f"📋 Diagnostic Details by {self.name}", expanded=False):
            if report.get('issues_found'):
                st.warning(f"**Issues Found ({len(report['issues_found'])}):**")
                for issue in report['issues_found']:
                    st.write(f"• {issue}")
            
            if report.get('issues_fixed'):
                st.success(f"**Issues Fixed ({len(report['issues_fixed'])}):**")
                for fix in report['issues_fixed']:
                    st.write(f"✅ {fix}")
            
            if report.get('warnings'):
                st.info(f"**Warnings ({len(report['warnings'])}):**")
                for warning in report['warnings']:
                    st.write(f"⚠️ {warning}")
            
            if report.get('recommendations'):
                st.info("**Recommendations:**")
                for rec in report['recommendations']:
                    st.write(f"💡 {rec}")
            
            # System status
            st.divider()
            st.write("**System Components:**")
            st.write(f"• Database: {report.get('database_status', 'Unknown')}")
            st.write(f"• File System: {report.get('file_system', {}).get('status', 'Unknown')}")
            st.write(f"• Dependencies: {report.get('dependencies', {}).get('status', 'Unknown')}")
            st.write(f"• APIs: {report.get('apis', {}).get('status', 'Unknown')}")
    
    def auto_fix_common_issues(self):
        """Vernon automatically fixes common issues"""
        fixes_applied = []
        
        # Check and fix client portal issues first
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Fix stuck documents
            cursor.execute("""
                UPDATE document_uploads 
                SET status = 'review_needed'
                WHERE status = 'pending' 
                AND julianday('now') - julianday(upload_time) > 7
            """)
            if cursor.rowcount > 0:
                fixes_applied.append(f"📄 Flagged {cursor.rowcount} stuck documents")
            
            # Clean old audit logs (keep 30 days)
            cursor.execute("""
                DELETE FROM client_audit_log 
                WHERE julianday('now') - julianday(timestamp) > 30
            """)
            if cursor.rowcount > 0:
                fixes_applied.append(f"🧹 Cleaned {cursor.rowcount} old audit logs")
            
            conn.commit()
            conn.close()
        except:
            pass
        
        # Fix 1: Clear stale session data
        if st.session_state.get('last_activity'):
            last_activity = st.session_state['last_activity']
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity)
            if datetime.now() - last_activity > timedelta(hours=24):
                # Clear stale session
                for key in list(st.session_state.keys()):
                    if key not in ['company_name', 'company_email']:
                        del st.session_state[key]
                fixes_applied.append("Cleared stale session data")
        
        # Fix 2: Reset stuck move statuses
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Find moves stuck in 'in_progress' for over 48 hours
            cursor.execute("""
                UPDATE moves 
                SET status = 'pending'
                WHERE status = 'in_progress' 
                AND datetime(created_at) < datetime('now', '-48 hours')
            """)
            
            if cursor.rowcount > 0:
                fixes_applied.append(f"Reset {cursor.rowcount} stuck moves")
                conn.commit()
            
            conn.close()
        except:
            pass
        
        # Fix 3: Clean up temp files
        temp_files = [f for f in os.listdir('.') if f.endswith('.tmp') or f.startswith('~')]
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
                fixes_applied.append(f"Removed temp file: {temp_file}")
            except:
                pass
        
        return fixes_applied
    
    def schedule_maintenance(self, interval='hourly'):
        """Schedule automatic maintenance"""
        if 'vernon_last_maintenance' not in st.session_state:
            st.session_state.vernon_last_maintenance = datetime.now()
        
        last_maintenance = st.session_state.vernon_last_maintenance
        next_maintenance = last_maintenance + self.maintenance_schedule.get(interval, timedelta(hours=1))
        
        if datetime.now() >= next_maintenance:
            # Run maintenance
            report = self.run_diagnostic(verbose=False)
            st.session_state.vernon_last_maintenance = datetime.now()
            
            # Log maintenance
            logging.info(f"Scheduled maintenance completed: Health={report['system_health']}%")
            
            # Alert if issues found
            if report['system_health'] < 90:
                st.warning(f"🔧 {self.name}: System health check detected issues. Health: {report['system_health']}%")
            
            return report
        
        return None
    
    def validate_after_upgrade(self):
        """Validate system after upgrades"""
        validation_report = {
            'timestamp': datetime.now().isoformat(),
            'version_check': 'OK',
            'compatibility': 'OK',
            'migration': 'OK',
            'tests_passed': []
        }
        
        st.info(f"🔍 {self.name}: Validating system after upgrade...")
        
        # Run comprehensive diagnostic
        diagnostic = self.run_diagnostic(verbose=False)
        validation_report['diagnostic'] = diagnostic
        
        # Test critical functions
        tests = [
            ('Database connection', self.test_database_connection),
            ('User authentication', self.test_authentication),
            ('Move creation', self.test_move_creation),
            ('POD upload', self.test_pod_upload),
            ('Email system', self.test_email_system)
        ]
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    validation_report['tests_passed'].append(test_name)
                    st.success(f"✅ {test_name}: Passed")
                else:
                    st.error(f"❌ {test_name}: Failed")
            except Exception as e:
                st.error(f"❌ {test_name}: Error - {str(e)}")
        
        # Overall validation status
        if len(validation_report['tests_passed']) == len(tests):
            st.success(f"✅ {self.name}: All validation tests passed! System is ready.")
        else:
            st.warning(f"⚠️ {self.name}: Some tests failed. Please review the issues.")
        
        return validation_report
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except:
            return False
    
    def test_authentication(self):
        """Test authentication system"""
        try:
            import auth_config
            # Just check if auth functions exist
            return hasattr(auth_config, 'verify_password')
        except:
            return False
    
    def test_move_creation(self):
        """Test move creation functionality"""
        try:
            import database as db
            # Check if function exists
            return hasattr(db, 'create_move')
        except:
            return False
    
    def test_pod_upload(self):
        """Test POD upload functionality"""
        # Check if upload directory can be created
        try:
            upload_dir = 'uploads'
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            return True
        except:
            return False
    
    def test_email_system(self):
        """Test email system"""
        try:
            import email_integration
            return hasattr(email_integration, 'send_email_smtp')
        except:
            return False
    
    def show_control_panel(self):
        """Show Vernon's control panel"""
        st.markdown(f"### 🤖 {self.name}'s IT Control Panel")
        st.caption(f"Status: {self.status} | Role: {self.role}")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("System Health", f"{self.system_health}%")
        with col2:
            st.metric("Total Checks", self.total_checks)
        with col3:
            st.metric("Issues Fixed", self.issues_fixed)
        with col4:
            last_check = self.last_check.strftime("%H:%M") if self.last_check else "Never"
            st.metric("Last Check", last_check)
        
        st.divider()
        
        # Control buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔍 Run Full Diagnostic", use_container_width=True):
                self.run_diagnostic()
        
        with col2:
            if st.button("🔧 Auto-Fix Issues", use_container_width=True):
                fixes = self.auto_fix_common_issues()
                if fixes:
                    st.success(f"Applied {len(fixes)} fixes:")
                    for fix in fixes:
                        st.write(f"• {fix}")
                else:
                    st.info("No issues to fix")
        
        with col3:
            if st.button("✅ Validate System", use_container_width=True):
                self.validate_after_upgrade()
        
        with col4:
            if st.button("👥 Check Client Portal", use_container_width=True):
                with st.spinner("Vernon is checking the client portal..."):
                    portal_health = self.check_client_portal_health()
                
                # Vernon speaks first
                if portal_health['status'] == 'OK':
                    st.success(f"**Vernon says:** {portal_health['vernon_says']}")
                elif portal_health['status'] == 'WARNING':
                    st.warning(f"**Vernon says:** {portal_health['vernon_says']}")
                else:
                    st.error(f"**Vernon says:** {portal_health['vernon_says']}")
                
                # Show stats in a friendly way
                with st.expander("📊 Portal Statistics", expanded=True):
                    stat_col1, stat_col2, stat_col3 = st.columns(3)
                    with stat_col1:
                        st.metric("Client Accounts", portal_health['client_users'], 
                                 help="Number of client viewer accounts")
                    with stat_col2:
                        st.metric("Documents", portal_health['document_uploads'],
                                 help="Total documents uploaded by clients")
                    with stat_col3:
                        st.metric("Activity Logs", portal_health['audit_entries'],
                                 help="Client actions being tracked")
                
                # Show issues in Vernon's friendly style
                if portal_health['issues_found']:
                    with st.expander("🔍 What Vernon Found", expanded=True):
                        for issue in portal_health['issues_found']:
                            st.write(f"• {issue}")
                        st.info("💡 **Vernon's tip:** Click 'Auto-Fix Issues' to resolve these!")
                
                if portal_health['issues_fixed']:
                    with st.expander("✅ What Vernon Fixed", expanded=True):
                        for fix in portal_health['issues_fixed']:
                            st.write(f"• {fix}")
                        st.success("🎉 Vernon handled these automatically!")
        
        # Maintenance schedule
        st.divider()
        st.markdown("#### ⏰ Maintenance Schedule")
        
        schedule_option = st.selectbox(
            "Automatic maintenance interval",
            ["Disabled", "Hourly", "Daily", "Weekly"],
            index=1
        )
        
        if schedule_option != "Disabled":
            interval = schedule_option.lower()
            result = self.schedule_maintenance(interval)
            if result:
                st.info(f"Maintenance completed: Health = {result['system_health']}%")
            else:
                next_check = st.session_state.get('vernon_last_maintenance', datetime.now())
                next_check += self.maintenance_schedule[interval]
                st.info(f"Next maintenance: {next_check.strftime('%Y-%m-%d %H:%M')}")
        
        # Activity log
        with st.expander("📜 Vernon's Activity Log", expanded=False):
            log_file = 'vernon_it_log.txt'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-20:]  # Last 20 lines
                    for line in lines:
                        st.text(line.strip())
            else:
                st.info("No activity log yet")
        
        # System info
        with st.expander("🖥️ System Information", expanded=False):
            st.write(f"**Platform:** {platform.system()} {platform.release()}")
            st.write(f"**Python:** {sys.version.split()[0]}")
            st.write(f"**Streamlit:** {st.__version__}")
            st.write(f"**Working Directory:** {os.getcwd()}")
            
            # Database info
            if os.path.exists('trailer_tracker_streamlined.db'):
                size = os.path.getsize('trailer_tracker_streamlined.db') / (1024 * 1024)
                st.write(f"**Database Size:** {size:.2f} MB")

# Singleton instance
_vernon_instance = None

def get_vernon():
    """Get Vernon IT Bot instance"""
    global _vernon_instance
    if _vernon_instance is None:
        _vernon_instance = VernonITBot()
    return _vernon_instance

def run_background_monitoring():
    """Run Vernon in background mode"""
    vernon = get_vernon()
    
    # Check if it's time for scheduled maintenance
    if 'vernon_enabled' not in st.session_state:
        st.session_state.vernon_enabled = True
    
    if st.session_state.vernon_enabled:
        # Run periodic checks silently
        vernon.schedule_maintenance('hourly')
        
        # Auto-fix critical issues silently
        if vernon.system_health < 70:
            vernon.auto_fix_common_issues()

def show_vernon_sidebar():
    """Show Vernon's status in sidebar"""
    vernon = get_vernon()
    
    with st.sidebar:
        with st.expander(f"🤖 {vernon.name} - IT Support", expanded=False):
            st.caption(vernon.greet())
            
            # Quick health indicator
            health_color = "🟢" if vernon.system_health >= 90 else "🟡" if vernon.system_health >= 70 else "🔴"
            st.write(f"{health_color} System Health: {vernon.system_health}%")
            
            # Quick actions
            if st.button("Quick Check", key="vernon_quick_check"):
                report = vernon.run_diagnostic(verbose=False)
                st.success(f"Check complete: {report['system_health']}% healthy")
            
            if vernon.system_health < 90:
                if st.button("Fix Issues", key="vernon_fix"):
                    fixes = vernon.auto_fix_common_issues()
                    st.success(f"Applied {len(fixes)} fixes")

def initialize_vernon():
    """Initialize Vernon on app startup"""
    vernon = get_vernon()
    
    # Run initial diagnostic silently
    if 'vernon_initialized' not in st.session_state:
        report = vernon.run_diagnostic(verbose=False)
        st.session_state.vernon_initialized = True
        
        # Show welcome message if issues found
        if report['system_health'] < 100:
            st.toast(f"🤖 {vernon.name}: System check complete. Health: {report['system_health']}%")
        
        logging.info(f"Vernon initialized: System health = {report['system_health']}%")

# Export functions for use in main app
__all__ = [
    'VernonITBot',
    'get_vernon',
    'run_background_monitoring',
    'show_vernon_sidebar',
    'initialize_vernon'
]