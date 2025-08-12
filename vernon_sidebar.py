"""
Vernon Sidebar Component - Available on Every Page
Vernon can analyze and fix issues on any page
"""

import streamlit as st
import sqlite3
import json
import os
from datetime import datetime
import traceback

class VernonSidebar:
    """Vernon as an always-available sidebar assistant with cross-page awareness"""
    
    def __init__(self):
        self.name = "Vernon"
        self.current_page = st.session_state.get('current_page', 'Unknown')
        self.init_cross_page_tracking()
    
    def init_cross_page_tracking(self):
        """Initialize cross-page issue tracking"""
        if 'vernon_all_page_issues' not in st.session_state:
            st.session_state['vernon_all_page_issues'] = {}
        if 'vernon_cross_page_fixes' not in st.session_state:
            st.session_state['vernon_cross_page_fixes'] = []
        if 'vernon_fix_history' not in st.session_state:
            st.session_state['vernon_fix_history'] = []
    
    def show_sidebar(self):
        """Show Vernon in the sidebar"""
        with st.sidebar:
            st.divider()
            
            # Vernon header
            with st.expander("🤖 Vernon IT Assistant", expanded=False):
                st.caption("I'm here to help fix any issues!")
                
                # Quick actions
                if st.button("🔍 Check This Page", use_container_width=True):
                    self.analyze_current_page()
                
                if st.button("🔧 Auto-Fix Issues", use_container_width=True):
                    self.fix_page_issues()
                
                if st.button("💬 Report Problem", use_container_width=True):
                    self.show_problem_reporter()
                
                # Show current status
                if 'vernon_last_check' in st.session_state:
                    last_check = st.session_state['vernon_last_check']
                    st.caption(f"Last check: {last_check}")
                
                # Show issues if any
                if 'vernon_current_issues' in st.session_state:
                    issues = st.session_state['vernon_current_issues']
                    if issues:
                        st.warning(f"Found {len(issues)} issues")
                        for issue in issues[:3]:  # Show first 3
                            st.caption(f"• {issue}")
                
                # Show cross-page fixes available
                if 'vernon_cross_page_fixes' in st.session_state:
                    fixes = st.session_state['vernon_cross_page_fixes']
                    if fixes:
                        st.info(f"📋 {len(fixes)} fixes from other pages")
                        if st.button("Apply Cross-Page Fixes"):
                            self.apply_cross_page_fixes()
    
    def analyze_current_page(self):
        """Analyze the current page for issues"""
        issues = []
        
        # Detect current page context
        page = st.session_state.get('current_page', 'Unknown')
        
        try:
            if 'driver' in page.lower():
                issues.extend(self.check_driver_page())
            elif 'trailer' in page.lower():
                issues.extend(self.check_trailer_page())
            elif 'move' in page.lower() or 'swap' in page.lower():
                issues.extend(self.check_moves_page())
            elif 'payment' in page.lower():
                issues.extend(self.check_payment_page())
            
            # Always check database
            issues.extend(self.check_database_integrity())
            
            # Store results
            st.session_state['vernon_current_issues'] = issues
            st.session_state['vernon_last_check'] = datetime.now().strftime('%H:%M:%S')
            
            # Track issues for this page
            st.session_state['vernon_all_page_issues'][page] = {
                'issues': issues,
                'timestamp': datetime.now().isoformat()
            }
            
            # Check for related issues on other pages
            self.identify_cross_page_fixes(issues)
            
            if issues:
                st.warning(f"Vernon found {len(issues)} issues on this page")
            else:
                st.success("Vernon: Everything looks good on this page!")
                
        except Exception as e:
            st.error(f"Vernon encountered an error: {e}")
    
    def check_driver_page(self):
        """Check for driver-related issues"""
        issues = []
        
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Check for driver sync issues
            if os.path.exists('user_accounts.json'):
                with open('user_accounts.json', 'r') as f:
                    users = json.load(f)
                
                # Count driver users
                driver_users = sum(1 for u, i in users.get('users', {}).items() 
                                 if 'driver' in i.get('roles', []))
                
                # Count database drivers
                cursor.execute('SELECT COUNT(*) FROM drivers')
                db_drivers = cursor.fetchone()[0]
                
                if driver_users != db_drivers:
                    issues.append(f"Driver sync issue: {driver_users} users vs {db_drivers} in database")
            
            # Check for missing columns
            cursor.execute('PRAGMA table_info(drivers)')
            cols = [col[1] for col in cursor.fetchall()]
            required = ['driver_name', 'active', 'created_at']
            
            for col in required:
                if col not in cols:
                    issues.append(f"Missing column: drivers.{col}")
            
            # Check for orphaned extended records
            cursor.execute("""
                SELECT COUNT(*) FROM drivers_extended de
                WHERE NOT EXISTS (
                    SELECT 1 FROM drivers d WHERE d.driver_name = de.driver_name
                )
            """)
            orphaned = cursor.fetchone()[0]
            if orphaned > 0:
                issues.append(f"{orphaned} orphaned extended driver records")
            
            conn.close()
            
        except Exception as e:
            issues.append(f"Database check error: {str(e)}")
        
        return issues
    
    def check_trailer_page(self):
        """Check for trailer-related issues"""
        issues = []
        
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Check for trailers without type
            cursor.execute("SELECT COUNT(*) FROM trailers WHERE trailer_type IS NULL")
            no_type = cursor.fetchone()[0]
            if no_type > 0:
                issues.append(f"{no_type} trailers without type specified")
            
            # Check for duplicate trailers
            cursor.execute("""
                SELECT trailer_number, COUNT(*) as cnt 
                FROM trailers 
                GROUP BY trailer_number 
                HAVING cnt > 1
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                issues.append(f"{len(duplicates)} duplicate trailer numbers")
            
            conn.close()
            
        except Exception as e:
            issues.append(f"Trailer check error: {str(e)}")
        
        return issues
    
    def check_moves_page(self):
        """Check for move/swap related issues"""
        issues = []
        
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Check for moves without drivers
            cursor.execute("""
                SELECT COUNT(*) FROM moves 
                WHERE driver_name IS NULL OR driver_name = ''
            """)
            no_driver = cursor.fetchone()[0]
            if no_driver > 0:
                issues.append(f"{no_driver} moves without assigned driver")
            
            # Check for stuck moves
            cursor.execute("""
                SELECT COUNT(*) FROM moves 
                WHERE status = 'in_progress' 
                AND julianday('now') - julianday(created_at) > 7
            """)
            stuck = cursor.fetchone()[0]
            if stuck > 0:
                issues.append(f"{stuck} moves stuck in progress > 7 days")
            
            conn.close()
            
        except Exception as e:
            issues.append(f"Move check error: {str(e)}")
        
        return issues
    
    def check_payment_page(self):
        """Check for payment-related issues"""
        issues = []
        
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Check for unpaid completed moves
            cursor.execute("""
                SELECT COUNT(*) FROM moves 
                WHERE status = 'completed' 
                AND payment_status = 'pending'
                AND julianday('now') - julianday(updated_at) > 30
            """)
            unpaid = cursor.fetchone()[0]
            if unpaid > 0:
                issues.append(f"{unpaid} completed moves unpaid > 30 days")
            
            conn.close()
            
        except Exception as e:
            issues.append(f"Payment check error: {str(e)}")
        
        return issues
    
    def check_database_integrity(self):
        """General database integrity checks"""
        issues = []
        
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Check for required tables
            required_tables = ['drivers', 'trailers', 'moves', 'locations']
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table not in existing:
                    issues.append(f"Missing table: {table}")
            
            conn.close()
            
        except Exception as e:
            issues.append(f"Database integrity check failed: {str(e)}")
        
        return issues
    
    def fix_page_issues(self):
        """Attempt to fix detected issues"""
        if 'vernon_current_issues' not in st.session_state:
            st.info("Vernon: Run 'Check This Page' first to detect issues")
            return
        
        issues = st.session_state['vernon_current_issues']
        if not issues:
            st.success("Vernon: No issues to fix!")
            return
        
        fixed = []
        failed = []
        
        for issue in issues:
            try:
                if "Driver sync issue" in issue:
                    if self.fix_driver_sync():
                        fixed.append("Driver sync")
                    else:
                        failed.append("Driver sync")
                        
                elif "Missing column" in issue:
                    if self.fix_missing_columns(issue):
                        fixed.append(issue)
                    else:
                        failed.append(issue)
                        
                elif "orphaned" in issue.lower():
                    if self.fix_orphaned_records(issue):
                        fixed.append("Orphaned records")
                    else:
                        failed.append("Orphaned records")
                        
                elif "stuck" in issue.lower():
                    if self.fix_stuck_moves():
                        fixed.append("Stuck moves")
                    else:
                        failed.append("Stuck moves")
                        
            except Exception as e:
                failed.append(f"{issue}: {str(e)}")
        
        if fixed:
            st.success(f"Vernon fixed {len(fixed)} issues!")
        if failed:
            st.warning(f"Vernon couldn't fix {len(failed)} issues")
        
        # Re-analyze after fixes
        self.analyze_current_page()
    
    def fix_driver_sync(self):
        """Fix driver synchronization issues"""
        try:
            # Import and run the sync function
            exec(open('fix_driver_sync.py').read())
            return True
        except:
            # Fallback sync
            try:
                with open('user_accounts.json', 'r') as f:
                    users = json.load(f)
                
                conn = sqlite3.connect('trailer_tracker_streamlined.db')
                cursor = conn.cursor()
                
                for username, info in users.get('users', {}).items():
                    if 'driver' in info.get('roles', []):
                        driver_name = info.get('name', username)
                        
                        cursor.execute('SELECT id FROM drivers WHERE driver_name = ?', (driver_name,))
                        if not cursor.fetchone():
                            cursor.execute('''
                                INSERT INTO drivers (driver_name, phone, email, username, status, active)
                                VALUES (?, ?, ?, ?, 'available', 1)
                            ''', (driver_name, info.get('phone', ''), info.get('email', ''), username))
                
                conn.commit()
                conn.close()
                return True
            except:
                return False
    
    def fix_missing_columns(self, issue):
        """Fix missing database columns"""
        try:
            # Parse table and column from issue
            if "drivers." in issue:
                table = "drivers"
                col = issue.split("drivers.")[1]
                
                conn = sqlite3.connect('trailer_tracker_streamlined.db')
                cursor = conn.cursor()
                
                # Add missing column
                col_defs = {
                    'active': 'BOOLEAN DEFAULT 1',
                    'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                }
                
                if col in col_defs:
                    cursor.execute(f'ALTER TABLE {table} ADD COLUMN {col} {col_defs[col]}')
                    conn.commit()
                    conn.close()
                    return True
        except:
            pass
        return False
    
    def fix_orphaned_records(self, issue):
        """Fix orphaned records"""
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Delete orphaned extended driver records
            cursor.execute("""
                DELETE FROM drivers_extended 
                WHERE driver_name NOT IN (SELECT driver_name FROM drivers)
            """)
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def fix_stuck_moves(self):
        """Fix stuck moves"""
        try:
            conn = sqlite3.connect('trailer_tracker_streamlined.db')
            cursor = conn.cursor()
            
            # Mark old in-progress moves as abandoned
            cursor.execute("""
                UPDATE moves 
                SET status = 'abandoned'
                WHERE status = 'in_progress'
                AND julianday('now') - julianday(created_at) > 7
            """)
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def show_problem_reporter(self):
        """Show problem reporting interface"""
        with st.form("vernon_report_problem"):
            st.markdown("### Report an Issue to Vernon")
            
            problem_type = st.selectbox(
                "What kind of issue?",
                ["Data not saving", "Button not working", "Page freezing", 
                 "Error message", "Missing data", "Other"]
            )
            
            description = st.text_area(
                "Describe the issue:",
                placeholder="Tell Vernon what's wrong..."
            )
            
            if st.form_submit_button("Send to Vernon"):
                # Log the issue
                self.log_user_issue(problem_type, description)
                st.success("Vernon received your report and will investigate!")
    
    def log_user_issue(self, problem_type, description):
        """Log user-reported issue"""
        try:
            issue_log = {
                'timestamp': datetime.now().isoformat(),
                'page': self.current_page,
                'type': problem_type,
                'description': description,
                'user': st.session_state.get('user_name', 'Unknown')
            }
            
            # Save to Vernon's log
            log_file = 'vernon_user_issues.json'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(issue_log)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            st.error(f"Vernon couldn't log the issue: {e}")

def init_vernon_sidebar():
    """Initialize Vernon in the sidebar"""
    vernon = VernonSidebar()
    vernon.show_sidebar()
    return vernon

# Export for use in main app
__all__ = ['VernonSidebar', 'init_vernon_sidebar']