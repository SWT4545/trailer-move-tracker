"""
Vernon Enhanced - Intelligent IT Bot with Configurable Validation
Fixed: False positives/negatives, added custom check configuration
"""

import streamlit as st
import sqlite3
import os
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import logging
from pathlib import Path
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Vernon Enhanced - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vernon_enhanced.log'),
        logging.StreamHandler()
    ]
)

class VernonEnhanced:
    """Enhanced IT Bot with configurable validation and real system checks"""
    
    def __init__(self):
        self.name = "Vernon"
        self.role = "IT Support Specialist"
        self.status = "Active"
        self.db_path = 'trailer_tracker_streamlined.db'
        self.config_file = 'vernon_config.json'
        self.load_configuration()
        self.init_session_state()
        
    def init_session_state(self):
        """Initialize Vernon's session state"""
        if 'vernon_state' not in st.session_state:
            st.session_state.vernon_state = {
                'last_check': None,
                'issues_found': [],
                'issues_fixed': [],
                'system_health': 100,
                'custom_checks': [],
                'check_history': []
            }
    
    def load_configuration(self):
        """Load Vernon's configuration"""
        default_config = {
            'enabled_checks': {
                'database': True,
                'files': True,
                'users': True,
                'drivers': True,
                'trailers': True,
                'moves': True,
                'session': True,
                'performance': True
            },
            'auto_fix': True,
            'check_frequency': 'on_demand',
            'custom_checks': [],
            'thresholds': {
                'orphaned_records': 5,
                'stuck_moves': 3,
                'inactive_days': 30,
                'performance_ms': 5000
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_configuration()
    
    def save_configuration(self):
        """Save Vernon's configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except:
            return False
    
    def add_custom_check(self, check_type, query, description, auto_fix_query=None):
        """Add a custom validation check"""
        custom_check = {
            'id': f"custom_{int(time.time())}",
            'type': check_type,
            'query': query,
            'description': description,
            'auto_fix': auto_fix_query,
            'enabled': True,
            'created': datetime.now().isoformat()
        }
        
        self.config['custom_checks'].append(custom_check)
        self.save_configuration()
        return custom_check['id']
    
    def run_system_check(self, verbose=True):
        """Run comprehensive system validation"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'checks_performed': [],
            'issues_found': [],
            'issues_fixed': [],
            'warnings': [],
            'system_health': 100
        }
        
        if verbose:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        checks_to_run = []
        
        # Add enabled standard checks
        if self.config['enabled_checks'].get('database'):
            checks_to_run.append(('database', self.check_database))
        if self.config['enabled_checks'].get('files'):
            checks_to_run.append(('files', self.check_files))
        if self.config['enabled_checks'].get('users'):
            checks_to_run.append(('users', self.check_users))
        if self.config['enabled_checks'].get('drivers'):
            checks_to_run.append(('drivers', self.check_drivers))
        if self.config['enabled_checks'].get('trailers'):
            checks_to_run.append(('trailers', self.check_trailers))
        if self.config['enabled_checks'].get('moves'):
            checks_to_run.append(('moves', self.check_moves))
        if self.config['enabled_checks'].get('performance'):
            checks_to_run.append(('performance', self.check_performance))
        
        # Run checks
        total_checks = len(checks_to_run) + len(self.config['custom_checks'])
        current_check = 0
        
        for check_name, check_func in checks_to_run:
            current_check += 1
            if verbose:
                progress_bar.progress(current_check / total_checks)
                status_text.text(f"Checking {check_name}...")
            
            try:
                result = check_func()
                report['checks_performed'].append(check_name)
                
                if result.get('issues'):
                    report['issues_found'].extend(result['issues'])
                if result.get('fixed'):
                    report['issues_fixed'].extend(result['fixed'])
                if result.get('warnings'):
                    report['warnings'].extend(result['warnings'])
                    
            except Exception as e:
                report['issues_found'].append(f"Check {check_name} failed: {str(e)}")
                logging.error(f"Check {check_name} failed: {traceback.format_exc()}")
        
        # Run custom checks
        for custom_check in self.config['custom_checks']:
            if custom_check.get('enabled'):
                current_check += 1
                if verbose:
                    progress_bar.progress(current_check / total_checks)
                    status_text.text(f"Running custom check: {custom_check['description']}")
                
                result = self.run_custom_check(custom_check)
                report['checks_performed'].append(f"custom: {custom_check['description']}")
                
                if result.get('issues'):
                    report['issues_found'].extend(result['issues'])
                if result.get('fixed'):
                    report['issues_fixed'].extend(result['fixed'])
        
        # Calculate health score
        health = 100
        health -= len(report['issues_found']) * 5
        health -= len(report['warnings']) * 2
        health += len(report['issues_fixed']) * 3
        report['system_health'] = max(0, min(100, health))
        
        # Update session state
        st.session_state.vernon_state['last_check'] = datetime.now()
        st.session_state.vernon_state['issues_found'] = report['issues_found']
        st.session_state.vernon_state['issues_fixed'] = report['issues_fixed']
        st.session_state.vernon_state['system_health'] = report['system_health']
        
        # Add to history
        st.session_state.vernon_state['check_history'].append({
            'timestamp': report['timestamp'],
            'health': report['system_health'],
            'issues': len(report['issues_found']),
            'fixed': len(report['issues_fixed'])
        })
        
        if verbose:
            progress_bar.progress(1.0)
            status_text.text("Check complete!")
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
        
        return report
    
    def check_database(self):
        """Check database integrity"""
        result = {'issues': [], 'fixed': [], 'warnings': []}
        
        try:
            if not os.path.exists(self.db_path):
                result['issues'].append("Database file missing")
                if self.config['auto_fix']:
                    # Recreate database
                    import database as db
                    db.init_database()
                    result['fixed'].append("Database recreated")
                return result
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check table structure
            required_tables = [
                'trailers', 'locations', 'drivers', 'moves',
                'mileage_cache', 'activity_log', 'drivers_extended'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table not in existing_tables:
                    result['issues'].append(f"Table '{table}' missing")
                    if self.config['auto_fix']:
                        self.create_table(conn, table)
                        result['fixed'].append(f"Created table '{table}'")
            
            # Check for orphaned records
            cursor.execute("""
                SELECT COUNT(*) FROM moves 
                WHERE driver_name NOT IN (SELECT driver_name FROM drivers)
                AND driver_name != 'Unknown Driver'
            """)
            orphaned = cursor.fetchone()[0]
            
            if orphaned > self.config['thresholds']['orphaned_records']:
                result['issues'].append(f"{orphaned} orphaned move records")
                if self.config['auto_fix']:
                    cursor.execute("""
                        UPDATE moves SET driver_name = 'Unknown Driver'
                        WHERE driver_name NOT IN (SELECT driver_name FROM drivers)
                        AND driver_name != 'Unknown Driver'
                    """)
                    conn.commit()
                    result['fixed'].append(f"Fixed {orphaned} orphaned moves")
            
            # Check for stuck moves
            cursor.execute("""
                SELECT COUNT(*) FROM moves 
                WHERE status = 'in_progress'
                AND julianday('now') - julianday(created_at) > ?
            """, (self.config['thresholds']['stuck_moves'],))
            stuck = cursor.fetchone()[0]
            
            if stuck > 0:
                result['warnings'].append(f"{stuck} moves stuck in progress")
            
            conn.close()
            
        except Exception as e:
            result['issues'].append(f"Database check error: {str(e)}")
            
        return result
    
    def check_files(self):
        """Check required files"""
        result = {'issues': [], 'fixed': [], 'warnings': []}
        
        required_files = {
            'app.py': 'Main application',
            'database.py': 'Database module',
            'user_accounts.json': 'User accounts',
            '.streamlit/config.toml': 'Streamlit configuration'
        }
        
        for file_path, description in required_files.items():
            if not os.path.exists(file_path):
                result['issues'].append(f"{description} file missing ({file_path})")
                
                if self.config['auto_fix']:
                    if file_path == 'user_accounts.json':
                        # Create default user file
                        default_users = {
                            'users': {
                                'admin': {
                                    'password': 'admin123',
                                    'roles': ['business_administrator'],
                                    'name': 'Administrator',
                                    'is_owner': True
                                }
                            }
                        }
                        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
                        with open(file_path, 'w') as f:
                            json.dump(default_users, f, indent=2)
                        result['fixed'].append(f"Created {description}")
                    
                    elif file_path == '.streamlit/config.toml':
                        os.makedirs('.streamlit', exist_ok=True)
                        with open(file_path, 'w') as f:
                            f.write('[theme]\n')
                            f.write('primaryColor = "#DC143C"\n')
                            f.write('backgroundColor = "#0E0E0E"\n')
                            f.write('secondaryBackgroundColor = "#1A1A1A"\n')
                            f.write('textColor = "#FFFFFF"\n')
                        result['fixed'].append(f"Created {description}")
        
        return result
    
    def check_users(self):
        """Check user system integrity"""
        result = {'issues': [], 'fixed': [], 'warnings': []}
        
        try:
            # Load user data
            if os.path.exists('user_accounts.json'):
                with open('user_accounts.json', 'r') as f:
                    user_data = json.load(f)
                
                users = user_data.get('users', {})
                
                # Check for admin user
                has_admin = any('business_administrator' in u.get('roles', []) for u in users.values())
                if not has_admin:
                    result['warnings'].append("No administrator account found")
                
                # Check for invalid users
                for username, info in users.items():
                    if not info.get('password'):
                        result['issues'].append(f"User '{username}' has no password")
                    if not info.get('roles'):
                        result['issues'].append(f"User '{username}' has no roles")
                
                # Check for duplicate driver accounts
                driver_names = {}
                for username, info in users.items():
                    if 'driver' in info.get('roles', []):
                        name = info.get('name', '')
                        if name in driver_names:
                            result['warnings'].append(f"Duplicate driver account: {name}")
                        driver_names[name] = username
                        
        except Exception as e:
            result['issues'].append(f"User check error: {str(e)}")
            
        return result
    
    def check_drivers(self):
        """Check driver data integrity"""
        result = {'issues': [], 'fixed': [], 'warnings': []}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for drivers without extended info
            cursor.execute("""
                SELECT d.driver_name FROM drivers d
                LEFT JOIN drivers_extended de ON d.driver_name = de.driver_name
                WHERE de.driver_name IS NULL
            """)
            missing_extended = cursor.fetchall()
            
            if missing_extended:
                for (driver_name,) in missing_extended:
                    result['issues'].append(f"Driver '{driver_name}' missing extended info")
                    
                    if self.config['auto_fix']:
                        cursor.execute("""
                            INSERT INTO drivers_extended (driver_name, driver_type)
                            VALUES (?, 'company')
                        """, (driver_name,))
                        result['fixed'].append(f"Added extended info for '{driver_name}'")
            
            # Check for expired CDLs
            cursor.execute("""
                SELECT driver_name, cdl_expiry FROM drivers_extended
                WHERE cdl_expiry IS NOT NULL 
                AND date(cdl_expiry) < date('now')
            """)
            expired_cdls = cursor.fetchall()
            
            for driver_name, expiry in expired_cdls:
                result['warnings'].append(f"Driver '{driver_name}' has expired CDL ({expiry})")
            
            # Check for expired insurance (contractors)
            cursor.execute("""
                SELECT driver_name, insurance_expiry FROM drivers_extended
                WHERE driver_type = 'contractor'
                AND insurance_expiry IS NOT NULL
                AND date(insurance_expiry) < date('now')
            """)
            expired_insurance = cursor.fetchall()
            
            for driver_name, expiry in expired_insurance:
                result['issues'].append(f"Contractor '{driver_name}' has expired insurance ({expiry})")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            result['issues'].append(f"Driver check error: {str(e)}")
            
        return result
    
    def check_trailers(self):
        """Check trailer data integrity"""
        result = {'issues': [], 'fixed': [], 'warnings': []}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for duplicate trailers
            cursor.execute("""
                SELECT trailer_number, COUNT(*) as count
                FROM trailers
                GROUP BY trailer_number
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            
            for trailer, count in duplicates:
                result['issues'].append(f"Duplicate trailer '{trailer}' ({count} entries)")
            
            # Check for trailers with invalid status
            cursor.execute("""
                SELECT trailer_number FROM trailers
                WHERE status NOT IN ('available', 'in_transit', 'maintenance', 'retired')
            """)
            invalid_status = cursor.fetchall()
            
            for (trailer,) in invalid_status:
                result['issues'].append(f"Trailer '{trailer}' has invalid status")
                
                if self.config['auto_fix']:
                    cursor.execute("""
                        UPDATE trailers SET status = 'available'
                        WHERE trailer_number = ?
                    """, (trailer,))
                    result['fixed'].append(f"Reset status for trailer '{trailer}'")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            result['issues'].append(f"Trailer check error: {str(e)}")
            
        return result
    
    def check_moves(self):
        """Check move data integrity"""
        result = {'issues': [], 'fixed': [], 'warnings': []}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for moves without trailers
            cursor.execute("""
                SELECT move_id FROM moves
                WHERE (new_trailer IS NULL OR new_trailer = '')
                AND (old_trailer IS NULL OR old_trailer = '')
            """)
            no_trailers = cursor.fetchall()
            
            for (move_id,) in no_trailers:
                result['issues'].append(f"Move '{move_id}' has no trailers assigned")
            
            # Check for stuck moves
            cursor.execute("""
                SELECT move_id, driver_name, 
                       julianday('now') - julianday(created_at) as days_old
                FROM moves
                WHERE status = 'assigned'
                AND julianday('now') - julianday(created_at) > ?
            """, (self.config['thresholds']['stuck_moves'],))
            stuck_moves = cursor.fetchall()
            
            for move_id, driver, days in stuck_moves:
                result['warnings'].append(f"Move '{move_id}' stuck for {int(days)} days (Driver: {driver})")
            
            conn.close()
            
        except Exception as e:
            result['issues'].append(f"Move check error: {str(e)}")
            
        return result
    
    def check_performance(self):
        """Check system performance"""
        result = {'issues': [], 'fixed': [], 'warnings': []}
        
        try:
            # Check database size
            if os.path.exists(self.db_path):
                db_size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
                if db_size > 100:
                    result['warnings'].append(f"Database size is {db_size:.1f} MB")
                    
                    if self.config['auto_fix']:
                        conn = sqlite3.connect(self.db_path)
                        conn.execute("VACUUM")
                        conn.close()
                        result['fixed'].append("Database optimized")
            
            # Check log file sizes
            log_files = ['vernon_enhanced.log', 'vernon_it_log.txt']
            for log_file in log_files:
                if os.path.exists(log_file):
                    log_size = os.path.getsize(log_file) / (1024 * 1024)  # MB
                    if log_size > 10:
                        result['warnings'].append(f"Log file '{log_file}' is {log_size:.1f} MB")
                        
                        if self.config['auto_fix']:
                            # Rotate log
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            os.rename(log_file, f"{log_file}.{timestamp}")
                            result['fixed'].append(f"Rotated log file '{log_file}'")
            
        except Exception as e:
            result['issues'].append(f"Performance check error: {str(e)}")
            
        return result
    
    def run_custom_check(self, custom_check):
        """Run a custom validation check"""
        result = {'issues': [], 'fixed': []}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Run check query
            cursor.execute(custom_check['query'])
            results = cursor.fetchall()
            
            if results:
                for row in results:
                    result['issues'].append(f"{custom_check['description']}: {row}")
                
                # Run auto-fix if available
                if self.config['auto_fix'] and custom_check.get('auto_fix'):
                    cursor.execute(custom_check['auto_fix'])
                    conn.commit()
                    result['fixed'].append(f"Applied fix for: {custom_check['description']}")
            
            conn.close()
            
        except Exception as e:
            result['issues'].append(f"Custom check '{custom_check['description']}' failed: {str(e)}")
            
        return result
    
    def create_table(self, conn, table_name):
        """Create missing table"""
        cursor = conn.cursor()
        
        table_definitions = {
            'drivers_extended': '''
                CREATE TABLE drivers_extended (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT UNIQUE NOT NULL,
                    driver_type TEXT DEFAULT 'company',
                    phone TEXT,
                    email TEXT,
                    cdl_number TEXT,
                    cdl_expiry DATE,
                    company_name TEXT,
                    mc_number TEXT,
                    dot_number TEXT,
                    insurance_company TEXT,
                    insurance_policy TEXT,
                    insurance_expiry DATE,
                    status TEXT DEFAULT 'available',
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        if table_name in table_definitions:
            cursor.execute(table_definitions[table_name])
            conn.commit()
    
    def show_configuration_ui(self):
        """Show Vernon's configuration interface"""
        st.markdown("### ⚙️ Vernon Configuration")
        
        with st.expander("Validation Checks", expanded=True):
            st.markdown("**Enable/Disable Checks:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                self.config['enabled_checks']['database'] = st.checkbox(
                    "Database Integrity",
                    value=self.config['enabled_checks'].get('database', True)
                )
                self.config['enabled_checks']['files'] = st.checkbox(
                    "Required Files",
                    value=self.config['enabled_checks'].get('files', True)
                )
                self.config['enabled_checks']['users'] = st.checkbox(
                    "User Accounts",
                    value=self.config['enabled_checks'].get('users', True)
                )
                self.config['enabled_checks']['drivers'] = st.checkbox(
                    "Driver Data",
                    value=self.config['enabled_checks'].get('drivers', True)
                )
            
            with col2:
                self.config['enabled_checks']['trailers'] = st.checkbox(
                    "Trailer Data",
                    value=self.config['enabled_checks'].get('trailers', True)
                )
                self.config['enabled_checks']['moves'] = st.checkbox(
                    "Move Records",
                    value=self.config['enabled_checks'].get('moves', True)
                )
                self.config['enabled_checks']['performance'] = st.checkbox(
                    "System Performance",
                    value=self.config['enabled_checks'].get('performance', True)
                )
            
            st.divider()
            
            self.config['auto_fix'] = st.checkbox(
                "🔧 Auto-fix issues when possible",
                value=self.config.get('auto_fix', True)
            )
        
        with st.expander("Thresholds", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                self.config['thresholds']['orphaned_records'] = st.number_input(
                    "Orphaned Records Warning",
                    min_value=1,
                    value=self.config['thresholds'].get('orphaned_records', 5)
                )
                self.config['thresholds']['stuck_moves'] = st.number_input(
                    "Stuck Moves Days",
                    min_value=1,
                    value=self.config['thresholds'].get('stuck_moves', 3)
                )
            
            with col2:
                self.config['thresholds']['inactive_days'] = st.number_input(
                    "Inactive User Days",
                    min_value=1,
                    value=self.config['thresholds'].get('inactive_days', 30)
                )
                self.config['thresholds']['performance_ms'] = st.number_input(
                    "Performance Threshold (ms)",
                    min_value=100,
                    value=self.config['thresholds'].get('performance_ms', 5000)
                )
        
        with st.expander("Custom Checks", expanded=False):
            st.markdown("**Add Custom Validation Check:**")
            
            with st.form("add_custom_check"):
                check_type = st.selectbox(
                    "Check Type",
                    ["Database Query", "File Check", "Data Validation"]
                )
                
                description = st.text_input(
                    "Description",
                    placeholder="Brief description of what this checks"
                )
                
                query = st.text_area(
                    "SQL Query (for issues)",
                    placeholder="SELECT ... FROM ... WHERE ...",
                    help="Query should return rows that represent issues"
                )
                
                fix_query = st.text_area(
                    "Auto-fix Query (optional)",
                    placeholder="UPDATE/DELETE/INSERT query to fix issues"
                )
                
                if st.form_submit_button("Add Custom Check"):
                    if description and query:
                        check_id = self.add_custom_check(
                            check_type, query, description, fix_query
                        )
                        st.success(f"✅ Custom check added: {check_id}")
                        time.sleep(1)
                        st.rerun()
            
            # Show existing custom checks
            if self.config['custom_checks']:
                st.markdown("**Existing Custom Checks:**")
                for check in self.config['custom_checks']:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"📋 {check['description']}")
                        with col2:
                            if st.button("Remove", key=f"remove_{check['id']}"):
                                self.config['custom_checks'] = [
                                    c for c in self.config['custom_checks'] 
                                    if c['id'] != check['id']
                                ]
                                self.save_configuration()
                                st.rerun()
                        with col3:
                            enabled = st.checkbox(
                                "Enabled",
                                value=check.get('enabled', True),
                                key=f"enable_{check['id']}"
                            )
                            check['enabled'] = enabled
        
        if st.button("💾 Save Configuration", type="primary"):
            if self.save_configuration():
                st.success("✅ Configuration saved!")
            else:
                st.error("Failed to save configuration")
    
    def show_validation_results(self, report):
        """Display validation results"""
        # Health indicator
        health = report['system_health']
        if health >= 80:
            st.success(f"🟢 System Health: {health}%")
        elif health >= 60:
            st.warning(f"🟡 System Health: {health}%")
        else:
            st.error(f"🔴 System Health: {health}%")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Checks Performed", len(report['checks_performed']))
        
        with col2:
            st.metric("Issues Found", len(report['issues_found']))
        
        with col3:
            st.metric("Issues Fixed", len(report['issues_fixed']))
        
        with col4:
            st.metric("Warnings", len(report['warnings']))
        
        # Details
        if report['issues_found']:
            with st.expander(f"❌ Issues Found ({len(report['issues_found'])})", expanded=True):
                for issue in report['issues_found']:
                    st.write(f"• {issue}")
        
        if report['issues_fixed']:
            with st.expander(f"✅ Issues Fixed ({len(report['issues_fixed'])})", expanded=True):
                for fix in report['issues_fixed']:
                    st.write(f"• {fix}")
        
        if report['warnings']:
            with st.expander(f"⚠️ Warnings ({len(report['warnings'])})", expanded=False):
                for warning in report['warnings']:
                    st.write(f"• {warning}")

def show_vernon_enhanced():
    """Main Vernon Enhanced interface"""
    vernon = VernonEnhanced()
    
    st.title(f"🤖 {vernon.name} - IT Support")
    st.info(f"👋 Hi! I'm {vernon.name}, your IT specialist. I can validate and fix system issues.")
    
    # Add master refresh button at the top
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning("⚠️ **Master System Controls**")
        if st.button("🔄 MASTER REFRESH - Fix All Connection Issues", type="primary", use_container_width=True):
            with st.spinner("Refreshing entire system..."):
                try:
                    # Import the connection manager
                    from database_connection_manager import refresh_all_connections
                    
                    # Clear all caches
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    
                    # Refresh database connections
                    refresh_all_connections()
                    
                    # Clear session state issues
                    if 'vernon_state' in st.session_state:
                        st.session_state.vernon_state['issues_found'] = []
                    
                    st.success("✅ System refresh complete! All connections reset.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Refresh failed: {e}")
    
    st.divider()
    
    tabs = st.tabs(["🔍 System Check", "⚙️ Configuration", "📊 History", "🛠️ Advanced Tools"])
    
    with tabs[0]:
        st.markdown("### System Validation")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 Run System Check", type="secondary", use_container_width=True):
                with st.spinner("Running validation..."):
                    report = vernon.run_system_check(verbose=True)
                    vernon.show_validation_results(report)
        
        # Show last check info
        if st.session_state.vernon_state['last_check']:
            st.divider()
            last_check = st.session_state.vernon_state['last_check']
            time_since = datetime.now() - last_check
            
            st.info(f"Last check: {time_since.total_seconds() / 60:.1f} minutes ago")
            
            if st.session_state.vernon_state['issues_found']:
                st.warning(f"Unresolved issues: {len(st.session_state.vernon_state['issues_found'])}")
    
    with tabs[1]:
        vernon.show_configuration_ui()
    
    with tabs[2]:
        st.markdown("### Check History")
        
        if st.session_state.vernon_state['check_history']:
            # Convert to DataFrame
            df = pd.DataFrame(st.session_state.vernon_state['check_history'])
            
            # Chart
            st.line_chart(df.set_index('timestamp')['health'])
            
            # Table
            st.dataframe(
                df[['timestamp', 'health', 'issues', 'fixed']].tail(10),
                use_container_width=True
            )
        else:
            st.info("No check history yet. Run a system check to start tracking.")
    
    with tabs[3]:  # Advanced Tools
        st.markdown("### 🛠️ Advanced Recovery Tools")
        st.warning("Use these tools when experiencing persistent issues")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Database Tools")
            if st.button("🔧 Repair Database Connections"):
                with st.spinner("Repairing..."):
                    try:
                        from database_connection_manager import db_manager
                        db_manager.ensure_tables()
                        st.success("Database connections repaired")
                    except Exception as e:
                        st.error(f"Repair failed: {e}")
            
            if st.button("🔄 Sync All Drivers"):
                with st.spinner("Syncing drivers..."):
                    try:
                        from database_connection_manager import sync_drivers_from_users
                        count = sync_drivers_from_users()
                        st.success(f"Synced {count} drivers")
                    except Exception as e:
                        st.error(f"Sync failed: {e}")
        
        with col2:
            st.markdown("#### Cache Tools")
            if st.button("🗑️ Clear All Caches"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("All caches cleared")
            
            if st.button("🔄 Reset Session State"):
                for key in list(st.session_state.keys()):
                    if key not in ['authenticated', 'user_name', 'user_role']:
                        del st.session_state[key]
                st.success("Session state reset")
                st.rerun()

# Export for use in main app
__all__ = ['VernonEnhanced', 'show_vernon_enhanced']