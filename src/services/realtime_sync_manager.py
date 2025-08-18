"""
Real-time Synchronization Manager
Ensures all pages update when data changes occur
Implements observer pattern for cross-module communication
"""

import streamlit as st
import sqlite3
import json
from datetime import datetime, timedelta
import database as db
from typing import Dict, List, Any, Callable
import threading
import time

class RealtimeSyncManager:
    """Manages real-time synchronization across all modules"""
    
    def __init__(self):
        self.initialize_sync_tables()
        self.event_handlers = {}
        self.last_check = datetime.now()
        
    def initialize_sync_tables(self):
        """Create tables for tracking changes and notifications"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create change tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    changed_by TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT 0,
                    UNIQUE(entity_type, entity_id, action, changed_at)
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_data_changes_unprocessed 
                ON data_changes(processed, changed_at DESC)
            """)
            
            # Create real-time notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS realtime_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_role TEXT,
                    target_user TEXT,
                    notification_type TEXT,
                    priority INTEGER DEFAULT 0,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT 0
                )
            """)
            
            conn.commit()
        except Exception as e:
            print(f"Sync table initialization error: {e}")
        finally:
            conn.close()
    
    def track_change(self, entity_type: str, entity_id: str, action: str, 
                    old_value: Any = None, new_value: Any = None, user: str = None):
        """Track a data change for synchronization"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO data_changes 
                (entity_type, entity_id, action, old_value, new_value, changed_by, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_type,
                str(entity_id),
                action,
                json.dumps(old_value) if old_value else None,
                json.dumps(new_value) if new_value else None,
                user or st.session_state.get('user', 'system'),
                datetime.now()
            ))
            
            conn.commit()
            
            # Trigger immediate notification for critical changes
            if action in ['assignment', 'cancellation', 'completion']:
                self.send_realtime_notification(entity_type, entity_id, action, new_value)
                
        except Exception as e:
            print(f"Error tracking change: {e}")
        finally:
            conn.close()
    
    def send_realtime_notification(self, entity_type: str, entity_id: str, 
                                  action: str, data: Any):
        """Send real-time notification to relevant users"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Determine target roles based on action
            target_roles = []
            if action == 'assignment':
                target_roles = ['Coordinator', 'Admin']
            elif action == 'cancellation':
                target_roles = ['Coordinator', 'Admin', 'Driver']
            elif action == 'completion':
                target_roles = ['Coordinator', 'Admin', 'Accounting']
            
            for role in target_roles:
                cursor.execute("""
                    INSERT INTO realtime_notifications 
                    (target_role, notification_type, priority, data, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    role,
                    f"{entity_type}_{action}",
                    2 if action == 'cancellation' else 1,
                    json.dumps({
                        'entity_type': entity_type,
                        'entity_id': entity_id,
                        'action': action,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }),
                    datetime.now() + timedelta(hours=24)
                ))
            
            conn.commit()
        except Exception as e:
            print(f"Error sending notification: {e}")
        finally:
            conn.close()
    
    def check_for_updates(self, last_check: datetime = None) -> Dict[str, List[Dict]]:
        """Check for any data updates since last check"""
        if not last_check:
            last_check = self.last_check
        
        conn = db.get_connection()
        cursor = conn.cursor()
        updates = {}
        
        try:
            # Get unprocessed changes
            cursor.execute("""
                SELECT entity_type, entity_id, action, new_value, changed_by, changed_at
                FROM data_changes
                WHERE changed_at > ? AND processed = 0
                ORDER BY changed_at DESC
                LIMIT 100
            """, (last_check,))
            
            changes = cursor.fetchall()
            
            for change in changes:
                entity_type = change[0]
                if entity_type not in updates:
                    updates[entity_type] = []
                
                updates[entity_type].append({
                    'entity_id': change[1],
                    'action': change[2],
                    'new_value': json.loads(change[3]) if change[3] else None,
                    'changed_by': change[4],
                    'changed_at': change[5]
                })
            
            # Mark as processed
            if changes:
                cursor.execute("""
                    UPDATE data_changes
                    SET processed = 1
                    WHERE changed_at > ? AND processed = 0
                """, (last_check,))
                conn.commit()
            
            self.last_check = datetime.now()
            
        except Exception as e:
            print(f"Error checking updates: {e}")
        finally:
            conn.close()
        
        return updates
    
    def get_pending_notifications(self, role: str = None, user: str = None) -> List[Dict]:
        """Get pending notifications for a role or user"""
        conn = db.get_connection()
        cursor = conn.cursor()
        notifications = []
        
        try:
            query = """
                SELECT id, notification_type, priority, data, created_at
                FROM realtime_notifications
                WHERE acknowledged = 0 
                AND expires_at > ?
            """
            params = [datetime.now()]
            
            if role:
                query += " AND target_role = ?"
                params.append(role)
            
            if user:
                query += " AND (target_user = ? OR target_user IS NULL)"
                params.append(user)
            
            query += " ORDER BY priority DESC, created_at DESC LIMIT 10"
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                notifications.append({
                    'id': row[0],
                    'type': row[1],
                    'priority': row[2],
                    'data': json.loads(row[3]) if row[3] else {},
                    'created_at': row[4]
                })
                
        except Exception as e:
            print(f"Error getting notifications: {e}")
        finally:
            conn.close()
        
        return notifications
    
    def acknowledge_notification(self, notification_id: int):
        """Mark a notification as acknowledged"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE realtime_notifications
                SET acknowledged = 1
                WHERE id = ?
            """, (notification_id,))
            conn.commit()
        except Exception as e:
            print(f"Error acknowledging notification: {e}")
        finally:
            conn.close()


class DataChangeTracker:
    """Decorator and context manager for tracking data changes"""
    
    def __init__(self, sync_manager: RealtimeSyncManager):
        self.sync_manager = sync_manager
    
    def track_trailer_change(self, trailer_id: str, action: str):
        """Track trailer-related changes"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Get old value before change
                old_value = self.get_trailer_state(trailer_id)
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Get new value after change
                new_value = self.get_trailer_state(trailer_id)
                
                # Track the change
                self.sync_manager.track_change(
                    'trailer', trailer_id, action,
                    old_value, new_value,
                    st.session_state.get('user')
                )
                
                return result
            return wrapper
        return decorator
    
    def track_move_change(self, move_id: str, action: str):
        """Track move-related changes"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Get old value before change
                old_value = self.get_move_state(move_id)
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Get new value after change
                new_value = self.get_move_state(move_id)
                
                # Track the change
                self.sync_manager.track_change(
                    'move', move_id, action,
                    old_value, new_value,
                    st.session_state.get('user')
                )
                
                # Update driver availability if assignment changed
                if action in ['assignment', 'unassignment', 'completion']:
                    self.update_driver_availability(new_value.get('driver_name'))
                
                return result
            return wrapper
        return decorator
    
    def get_trailer_state(self, trailer_id: str) -> Dict:
        """Get current state of a trailer"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT trailer_number, status, current_location, 
                       is_reserved, reserved_by_driver
                FROM trailers
                WHERE id = ? OR trailer_number = ?
            """, (trailer_id, trailer_id))
            
            result = cursor.fetchone()
            if result:
                return {
                    'trailer_number': result[0],
                    'status': result[1],
                    'location': result[2],
                    'is_reserved': result[3],
                    'reserved_by': result[4]
                }
        except Exception as e:
            print(f"Error getting trailer state: {e}")
        finally:
            conn.close()
        
        return {}
    
    def get_move_state(self, move_id: str) -> Dict:
        """Get current state of a move"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT move_id, status, driver_name, new_trailer, 
                       old_trailer, self_assigned
                FROM moves
                WHERE move_id = ?
            """, (move_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'move_id': result[0],
                    'status': result[1],
                    'driver_name': result[2],
                    'new_trailer': result[3],
                    'old_trailer': result[4],
                    'self_assigned': result[5]
                }
        except Exception as e:
            print(f"Error getting move state: {e}")
        finally:
            conn.close()
        
        return {}
    
    def update_driver_availability(self, driver_name: str):
        """Update driver availability status"""
        if not driver_name:
            return
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if driver has active moves
            cursor.execute("""
                SELECT COUNT(*) FROM moves
                WHERE driver_name = ?
                AND status IN ('assigned', 'in_progress', 'pickup_complete')
            """, (driver_name,))
            
            active_moves = cursor.fetchone()[0]
            
            # Update availability
            new_status = 'assigned' if active_moves > 0 else 'available'
            
            cursor.execute("""
                UPDATE driver_availability
                SET status = ?, updated_at = ?
                WHERE driver_id = (
                    SELECT id FROM drivers WHERE driver_name = ?
                )
            """, (new_status, datetime.now(), driver_name))
            
            conn.commit()
        except Exception as e:
            print(f"Error updating driver availability: {e}")
        finally:
            conn.close()


def show_realtime_notifications():
    """Display real-time notifications in the UI"""
    sync_manager = RealtimeSyncManager()
    
    # Get notifications for current user
    role = st.session_state.get('user_role')
    username = st.session_state.get('user')
    
    notifications = sync_manager.get_pending_notifications(role, username)
    
    if notifications:
        with st.container():
            st.markdown("### 🔔 Real-time Updates")
            
            for notif in notifications[:5]:  # Show max 5 notifications
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Format notification based on type
                    notif_data = notif['data']
                    
                    if notif['type'] == 'move_assignment':
                        st.info(f"🚚 New self-assignment: {notif_data.get('entity_id')} by {notif_data.get('data', {}).get('driver_name', 'Unknown')}")
                    elif notif['type'] == 'move_cancellation':
                        st.warning(f"❌ Move cancelled: {notif_data.get('entity_id')}")
                    elif notif['type'] == 'move_completion':
                        st.success(f"✅ Move completed: {notif_data.get('entity_id')}")
                    else:
                        st.info(f"ℹ️ {notif['type']}: {notif_data.get('entity_id')}")
                
                with col2:
                    if st.button("Dismiss", key=f"dismiss_{notif['id']}"):
                        sync_manager.acknowledge_notification(notif['id'])
                        st.rerun()


def auto_refresh_check():
    """Check for updates and refresh if needed"""
    if 'last_update_check' not in st.session_state:
        st.session_state.last_update_check = datetime.now()
    
    # Check every 10 seconds
    if datetime.now() - st.session_state.last_update_check > timedelta(seconds=10):
        sync_manager = RealtimeSyncManager()
        updates = sync_manager.check_for_updates(st.session_state.last_update_check)
        
        if updates:
            # Store updates in session state
            st.session_state.pending_updates = updates
            st.session_state.last_update_check = datetime.now()
            
            # Show update notification
            st.info(f"📊 {len(updates)} data updates available. Refreshing...")
            time.sleep(1)
            st.rerun()


def apply_updates_to_page():
    """Apply pending updates to the current page"""
    if 'pending_updates' in st.session_state:
        updates = st.session_state.pending_updates
        
        # Apply updates based on current page context
        current_page = st.session_state.get('current_page', 'dashboard')
        
        if 'trailer' in updates and current_page in ['trailers', 'dashboard']:
            st.info("🚛 Trailer data updated")
        
        if 'move' in updates and current_page in ['moves', 'dashboard', 'driver_portal']:
            st.info("📦 Move assignments updated")
        
        if 'driver' in updates and current_page in ['drivers', 'coordinator']:
            st.info("👥 Driver status updated")
        
        # Clear pending updates
        del st.session_state.pending_updates


# Initialize sync manager globally
sync_manager = RealtimeSyncManager()
change_tracker = DataChangeTracker(sync_manager)