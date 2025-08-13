"""
Trailer Table Sync Manager
Ensures trailer data updates are synchronized across all user profiles
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json
import streamlit as st

class TrailerSyncManager:
    def __init__(self):
        self.conn = sqlite3.connect('trailer_tracker_streamlined.db')
        self.ensure_sync_tables()
    
    def ensure_sync_tables(self):
        """Ensure sync tracking tables exist"""
        cursor = self.conn.cursor()
        
        # Create sync log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trailer_sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                operation TEXT,
                record_id TEXT,
                changes TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_by TEXT
            )
        ''')
        
        # Create profile sync status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profile_sync_status (
                profile_id TEXT PRIMARY KEY,
                last_sync TIMESTAMP,
                pending_updates INTEGER DEFAULT 0,
                sync_status TEXT DEFAULT 'active'
            )
        ''')
        
        self.conn.commit()
    
    def sync_trailer_update(self, trailer_number, changes, updated_by):
        """Sync trailer updates across all profiles"""
        cursor = self.conn.cursor()
        
        # Log the sync operation
        cursor.execute('''
            INSERT INTO trailer_sync_log (table_name, operation, record_id, changes, synced_by)
            VALUES (?, ?, ?, ?, ?)
        ''', ('trailer_inventory', 'update', trailer_number, json.dumps(changes), updated_by))
        
        # Update all profile sync status
        cursor.execute('''
            UPDATE profile_sync_status
            SET pending_updates = pending_updates + 1
            WHERE sync_status = 'active'
        ''')
        
        self.conn.commit()
        
        # Trigger real-time update notification
        self.notify_profiles(trailer_number, changes)
    
    def notify_profiles(self, trailer_number, changes):
        """Send notifications to all active profiles"""
        # In production, this would use WebSockets or Server-Sent Events
        # For now, we'll use session state flags
        if 'sync_notifications' not in st.session_state:
            st.session_state.sync_notifications = []
        
        notification = {
            'timestamp': datetime.now().isoformat(),
            'trailer': trailer_number,
            'changes': changes,
            'type': 'trailer_update'
        }
        
        st.session_state.sync_notifications.append(notification)
    
    def get_pending_updates(self, profile_id):
        """Get pending updates for a specific profile"""
        cursor = self.conn.cursor()
        
        # Get profile's last sync time
        cursor.execute('''
            SELECT last_sync FROM profile_sync_status WHERE profile_id = ?
        ''', (profile_id,))
        
        result = cursor.fetchone()
        last_sync = result[0] if result else '2000-01-01'
        
        # Get all updates since last sync
        cursor.execute('''
            SELECT * FROM trailer_sync_log
            WHERE synced_at > ?
            ORDER BY synced_at DESC
        ''', (last_sync,))
        
        updates = cursor.fetchall()
        return updates
    
    def mark_synced(self, profile_id):
        """Mark profile as synced"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO profile_sync_status (profile_id, last_sync, pending_updates)
            VALUES (?, ?, 0)
        ''', (profile_id, datetime.now()))
        
        self.conn.commit()
    
    def auto_sync_check(self, username):
        """Check for updates and auto-sync if needed"""
        updates = self.get_pending_updates(username)
        
        if updates:
            # Apply updates
            for update in updates:
                table_name, operation, record_id, changes = update[1:5]
                self.apply_update(table_name, operation, record_id, json.loads(changes))
            
            # Mark as synced
            self.mark_synced(username)
            
            return len(updates)
        return 0
    
    def apply_update(self, table_name, operation, record_id, changes):
        """Apply a sync update to local view"""
        cursor = self.conn.cursor()
        
        if operation == 'update' and table_name == 'trailer_inventory':
            # Build UPDATE query dynamically
            set_clause = ', '.join([f"{k} = ?" for k in changes.keys()])
            values = list(changes.values())
            values.append(record_id)
            
            cursor.execute(f'''
                UPDATE {table_name}
                SET {set_clause}
                WHERE trailer_number = ?
            ''', values)
        
        elif operation == 'insert':
            # Build INSERT query
            columns = ', '.join(changes.keys())
            placeholders = ', '.join(['?' for _ in changes])
            values = list(changes.values())
            
            cursor.execute(f'''
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders})
            ''', values)
        
        self.conn.commit()
    
    def show_sync_status(self):
        """Display sync status in UI"""
        st.sidebar.markdown("### 🔄 Sync Status")
        
        # Check for pending updates
        username = st.session_state.get('username', 'unknown')
        updates_count = len(self.get_pending_updates(username))
        
        if updates_count > 0:
            st.sidebar.warning(f"📥 {updates_count} pending updates")
            if st.sidebar.button("Sync Now", use_container_width=True):
                synced = self.auto_sync_check(username)
                st.sidebar.success(f"✅ Synced {synced} updates")
                st.rerun()
        else:
            st.sidebar.success("✅ All synced")
        
        # Show recent notifications
        if st.session_state.get('sync_notifications'):
            with st.sidebar.expander("Recent Updates"):
                for notif in st.session_state.sync_notifications[-5:]:
                    st.write(f"🚛 {notif['trailer']}: {notif['type']}")

# Global sync manager instance
sync_manager = None

def get_sync_manager():
    """Get or create sync manager instance"""
    global sync_manager
    if sync_manager is None:
        sync_manager = TrailerSyncManager()
    return sync_manager

def sync_trailer_change(trailer_number, changes, username):
    """Helper function to sync trailer changes"""
    manager = get_sync_manager()
    manager.sync_trailer_update(trailer_number, changes, username)

def check_for_updates(username):
    """Helper function to check for updates"""
    manager = get_sync_manager()
    return manager.auto_sync_check(username)

def show_sync_widget():
    """Helper function to show sync widget"""
    manager = get_sync_manager()
    manager.show_sync_status()

# Auto-sync decorator
def with_sync(func):
    """Decorator to automatically sync after database operations"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Trigger sync check
        if 'username' in st.session_state:
            check_for_updates(st.session_state.username)
        
        return result
    return wrapper