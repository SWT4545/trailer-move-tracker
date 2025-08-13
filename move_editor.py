"""
Move Editor Module - Change/Edit Trailers in Active Moves
Allows changing trailers when they're not ready or need replacement
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import database as db
import json
import os
from database_connection_manager import db_manager

class MoveEditor:
    def __init__(self):
        # Use correct database path
        self.db_path = 'trailer_tracker_streamlined.db' if os.path.exists('trailer_tracker_streamlined.db') else 'trailer_data.db'
        self.ensure_change_log_table()
    
    def ensure_change_log_table(self):
        """Create table to track trailer changes"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
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
                
                conn.commit()
        except Exception as e:
            st.warning(f"Could not create change log table: {e}")
    
    def get_active_moves(self):
        """Get all active moves that can be edited"""
        try:
            with db_manager.get_connection() as conn:
                query = """
                    SELECT * FROM trailer_moves 
                    WHERE status IN ('assigned', 'in_progress', 'pending')
                    ORDER BY move_date DESC
                """
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            st.error(f"Database error: {e}")
            return pd.DataFrame()
    
    def get_available_trailers(self, trailer_type, exclude_id=None):
        """Get available trailers of specified type"""
        try:
            with db_manager.get_connection() as conn:
                query = """
                    SELECT * FROM trailers 
                    WHERE trailer_type = ? AND status = 'available'
                """
                
                if exclude_id:
                    query += " AND trailer_number != ?"
                    df = pd.read_sql_query(query, conn, params=(trailer_type, exclude_id))
                else:
                    df = pd.read_sql_query(query, conn, params=(trailer_type,))
                
                return df
        except Exception as e:
            st.error(f"Database error: {e}")
            return pd.DataFrame()
    
    def log_change(self, move_id, change_type, old_value, new_value, reason, changed_by):
        """Log a trailer change"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO move_changes (move_id, change_type, old_value, new_value, reason, changed_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (move_id, change_type, old_value, new_value, reason, changed_by))
                
                conn.commit()
        except Exception as e:
            st.error(f"Could not log change: {e}")
    
    def update_move_trailers(self, move_id, new_trailer=None, old_trailer=None, reason="", user=""):
        """Update trailers in a move"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current move details
                cursor.execute("SELECT * FROM trailer_moves WHERE id = ?", (move_id,))
                current_move = cursor.fetchone()
                
                if not current_move:
                    return False, "Move not found"
                
                updates = []
                params = []
                
                # Update NEW trailer if provided
                if new_trailer and new_trailer != current_move[2]:  # Index 2 is new_trailer
                    # Log the change
                    self.log_change(move_id, "NEW_TRAILER", current_move[2], new_trailer, reason, user)
                    
                    # Free up the old NEW trailer
                    cursor.execute("UPDATE trailers SET status = 'available' WHERE trailer_number = ?", (current_move[2],))
                    
                    # Mark new trailer as in_use
                    cursor.execute("UPDATE trailers SET status = 'in_use' WHERE trailer_number = ?", (new_trailer,))
                    
                    updates.append("new_trailer = ?")
                    params.append(new_trailer)
                
                # Update OLD trailer if provided
                if old_trailer and old_trailer != current_move[3]:  # Index 3 is old_trailer
                    # Log the change
                    self.log_change(move_id, "OLD_TRAILER", current_move[3], old_trailer, reason, user)
                    
                    # Free up the old OLD trailer
                    cursor.execute("UPDATE trailers SET status = 'available' WHERE trailer_number = ?", (current_move[3],))
                    
                    # Mark new trailer as in_use
                    cursor.execute("UPDATE trailers SET status = 'in_use' WHERE trailer_number = ?", (old_trailer,))
                    
                    updates.append("old_trailer = ?")
                    params.append(old_trailer)
                
                if updates:
                    # Update the move
                    query = f"UPDATE trailer_moves SET {', '.join(updates)}, updated_date = CURRENT_TIMESTAMP WHERE id = ?"
                    params.append(move_id)
                    cursor.execute(query, params)
                    
                    conn.commit()
                    return True, "Move updated successfully"
                else:
                    return False, "No changes made"
        except Exception as e:
            return False, f"Database error: {e}"
    
    def get_change_history(self, move_id=None):
        """Get change history for a move or all moves"""
        try:
            with db_manager.get_connection() as conn:
                if move_id:
                    query = """
                        SELECT mc.*, tm.driver_name 
                        FROM move_changes mc
                        LEFT JOIN trailer_moves tm ON mc.move_id = tm.id
                        WHERE mc.move_id = ?
                        ORDER BY mc.changed_at DESC
                    """
                    df = pd.read_sql_query(query, conn, params=(move_id,))
                else:
                    query = """
                        SELECT mc.*, tm.driver_name 
                        FROM move_changes mc
                        LEFT JOIN trailer_moves tm ON mc.move_id = tm.id
                        ORDER BY mc.changed_at DESC
                        LIMIT 50
                    """
                    df = pd.read_sql_query(query, conn)
                
                return df
        except Exception as e:
            st.error(f"Database error: {e}")
            return pd.DataFrame()

def show_move_editor():
    """Main UI for editing moves"""
    st.title("🔄 Edit Move - Change Trailers")
    st.info("Change trailers when they're not ready or need replacement")
    
    # Add refresh button for connection issues
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Refresh Page", type="secondary", use_container_width=True):
            from database_connection_manager import refresh_all_connections
            refresh_all_connections()
            st.rerun()
    
    try:
        editor = MoveEditor()
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        st.info("Click the refresh button above to retry")
        return
    
    # Get user info
    user_name = st.session_state.get('user_name', 'Unknown')
    user_role = st.session_state.get('user_role', '')
    
    # Check permissions
    if user_role not in ['business_administrator', 'operations_coordinator']:
        st.error("You don't have permission to edit moves")
        return
    
    # Get active moves
    active_moves = editor.get_active_moves()
    
    if active_moves.empty:
        st.warning("No active moves to edit")
        st.info("This could mean no moves are active or there's a database connection issue.")
        return
    
    # Select move to edit
    col1, col2 = st.columns([2, 1])
    
    with col1:
        move_options = {}
        for _, move in active_moves.iterrows():
            label = f"Move #{move['id']} - {move['driver_name']} - {move['new_trailer']} ↔️ {move['old_trailer']} - {move['delivery_location']}"
            move_options[label] = move['id']
        
        selected_move_label = st.selectbox("Select Move to Edit", list(move_options.keys()))
        selected_move_id = move_options[selected_move_label]
    
    with col2:
        # Show current status
        current_move = active_moves[active_moves['id'] == selected_move_id].iloc[0]
        st.markdown("**Current Status**")
        st.write(f"Status: {current_move['status']}")
        st.write(f"Date: {current_move['move_date']}")
    
    # Display current move details
    st.divider()
    st.markdown("### Current Move Details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📦 NEW Trailer**")
        st.info(f"{current_move['new_trailer']}")
        st.caption(f"From: {current_move.get('pickup_location', 'Base')}")
    
    with col2:
        st.markdown("**🚛 OLD Trailer**")
        st.info(f"{current_move['old_trailer']}")
        st.caption(f"At: {current_move['delivery_location']}")
    
    with col3:
        st.markdown("**👤 Driver**")
        st.info(f"{current_move['driver_name']}")
        st.caption(f"Miles: {current_move.get('total_miles', 0)}")
    
    # Edit form
    st.divider()
    st.markdown("### 🔧 Change Trailers")
    
    with st.form("edit_move_form"):
        st.warning("⚠️ Only change trailers if they're not ready or need replacement")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Change NEW Trailer")
            change_new = st.checkbox("Replace NEW trailer")
            
            if change_new:
                # Get available NEW trailers
                available_new = editor.get_available_trailers('new', current_move['new_trailer'])
                
                if not available_new.empty:
                    new_trailer_options = ['Keep Current'] + [
                        f"{t['trailer_number']} (at {t['current_location']})" 
                        for _, t in available_new.iterrows()
                    ]
                    selected_new = st.selectbox("Select Replacement NEW Trailer", new_trailer_options)
                    
                    if selected_new != 'Keep Current':
                        new_trailer_number = selected_new.split(' (')[0]
                    else:
                        new_trailer_number = None
                else:
                    st.error("No available NEW trailers")
                    new_trailer_number = None
            else:
                new_trailer_number = None
        
        with col2:
            st.markdown("#### Change OLD Trailer")
            change_old = st.checkbox("Replace OLD trailer")
            
            if change_old:
                # Get available OLD trailers
                available_old = editor.get_available_trailers('old', current_move['old_trailer'])
                
                if not available_old.empty:
                    old_trailer_options = ['Keep Current'] + [
                        f"{t['trailer_number']} (at {t['current_location']})" 
                        for _, t in available_old.iterrows()
                    ]
                    selected_old = st.selectbox("Select Replacement OLD Trailer", old_trailer_options)
                    
                    if selected_old != 'Keep Current':
                        old_trailer_number = selected_old.split(' (')[0]
                    else:
                        old_trailer_number = None
                else:
                    st.error("No available OLD trailers")
                    old_trailer_number = None
            else:
                old_trailer_number = None
        
        # Reason for change
        reason = st.text_area("Reason for Change*", 
                             placeholder="Explain why the trailer(s) need to be changed",
                             help="This will be logged for audit purposes")
        
        # Notification option
        notify_driver = st.checkbox("Notify driver of change", value=True)
        
        submitted = st.form_submit_button("✅ Confirm Changes", type="primary", use_container_width=True)
        
        if submitted:
            if not reason:
                st.error("Please provide a reason for the change")
            elif not change_new and not change_old:
                st.warning("No changes selected")
            else:
                # Apply changes
                success, message = editor.update_move_trailers(
                    selected_move_id,
                    new_trailer=new_trailer_number,
                    old_trailer=old_trailer_number,
                    reason=reason,
                    user=user_name
                )
                
                if success:
                    st.success(message)
                    
                    # Show notification
                    if notify_driver:
                        st.info(f"📱 Driver {current_move['driver_name']} will be notified of the change")
                    
                    # Log the change
                    st.markdown("### Change Summary")
                    if new_trailer_number:
                        st.write(f"✅ NEW trailer changed from {current_move['new_trailer']} to {new_trailer_number}")
                    if old_trailer_number:
                        st.write(f"✅ OLD trailer changed from {current_move['old_trailer']} to {old_trailer_number}")
                    
                    st.rerun()
                else:
                    st.error(message)
    
    # Show change history
    st.divider()
    st.markdown("### 📜 Change History")
    
    history = editor.get_change_history(selected_move_id)
    
    if not history.empty:
        for _, change in history.iterrows():
            with st.expander(f"{change['change_type']} - {change['changed_at']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Changed by:** {change['changed_by']}")
                    st.write(f"**From:** {change['old_value']}")
                    st.write(f"**To:** {change['new_value']}")
                with col2:
                    st.write(f"**Reason:** {change['reason']}")
    else:
        st.info("No changes recorded for this move")

def show_change_audit_log():
    """Show audit log of all trailer changes"""
    st.title("📋 Trailer Change Audit Log")
    
    editor = MoveEditor()
    
    # Get all changes
    all_changes = editor.get_change_history()
    
    if not all_changes.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Changes", len(all_changes))
        with col2:
            st.metric("Moves Affected", all_changes['move_id'].nunique())
        with col3:
            st.metric("NEW Trailer Changes", len(all_changes[all_changes['change_type'] == 'NEW_TRAILER']))
        with col4:
            st.metric("OLD Trailer Changes", len(all_changes[all_changes['change_type'] == 'OLD_TRAILER']))
        
        st.divider()
        
        # Display changes
        st.dataframe(
            all_changes[['move_id', 'driver_name', 'change_type', 'old_value', 'new_value', 'reason', 'changed_by', 'changed_at']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No trailer changes recorded yet")

# Export functions
__all__ = ['MoveEditor', 'show_move_editor', 'show_change_audit_log']