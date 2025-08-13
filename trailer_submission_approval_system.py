"""
Trailer Submission and Approval System
Allows drivers to submit trailer pairs they find
Coordinators verify with clients before approval
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import json
import sqlite3
from realtime_sync_manager import RealtimeSyncManager

class TrailerSubmissionSystem:
    """Manages driver trailer submissions and coordinator approvals"""
    
    def __init__(self):
        self.ensure_submission_tables()
        self.sync_manager = RealtimeSyncManager()
    
    def ensure_submission_tables(self):
        """Create tables for trailer submission workflow"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create pending trailer submissions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trailer_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id TEXT UNIQUE,
                    new_trailer_number TEXT NOT NULL,
                    old_trailer_number TEXT NOT NULL,
                    location TEXT NOT NULL,
                    location_address TEXT,
                    city TEXT,
                    state TEXT,
                    submitted_by_driver TEXT NOT NULL,
                    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    submission_notes TEXT,
                    photo_url TEXT,
                    
                    -- Approval workflow
                    status TEXT DEFAULT 'pending',
                    reviewed_by TEXT,
                    review_date TIMESTAMP,
                    review_notes TEXT,
                    client_verified BOOLEAN DEFAULT 0,
                    client_name TEXT,
                    client_contact TEXT,
                    
                    -- After approval
                    approved BOOLEAN DEFAULT 0,
                    approval_date TIMESTAMP,
                    rejection_reason TEXT,
                    trailer_ids_created TEXT,
                    
                    CHECK(status IN ('pending', 'reviewing', 'approved', 'rejected', 'client_verification'))
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trailer_submissions_status 
                ON trailer_submissions(status, submission_date DESC)
            """)
            
            # Create notifications for submissions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submission_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    submission_id TEXT,
                    notification_type TEXT,
                    message TEXT,
                    target_role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read BOOLEAN DEFAULT 0,
                    FOREIGN KEY (submission_id) REFERENCES trailer_submissions(submission_id)
                )
            """)
            
            conn.commit()
        except Exception as e:
            print(f"Error creating submission tables: {e}")
        finally:
            conn.close()
    
    def submit_trailer_pair(self, driver_name, new_trailer, old_trailer, location, 
                           city=None, state=None, notes=None, photo=None):
        """Driver submits a trailer pair for approval"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Generate submission ID
            submission_id = f"SUB-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{driver_name[:3].upper()}"
            
            # Check if trailer already exists or pending
            cursor.execute("""
                SELECT COUNT(*) FROM trailers 
                WHERE trailer_number IN (?, ?)
            """, (new_trailer, old_trailer))
            
            if cursor.fetchone()[0] > 0:
                return False, "One or both trailers already exist in system"
            
            cursor.execute("""
                SELECT COUNT(*) FROM trailer_submissions 
                WHERE (new_trailer_number = ? OR old_trailer_number = ?)
                AND status IN ('pending', 'reviewing', 'client_verification')
            """, (new_trailer, old_trailer))
            
            if cursor.fetchone()[0] > 0:
                return False, "Trailer already submitted and pending approval"
            
            # Insert submission
            cursor.execute("""
                INSERT INTO trailer_submissions (
                    submission_id, new_trailer_number, old_trailer_number,
                    location, city, state, submitted_by_driver,
                    submission_notes, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                submission_id, new_trailer, old_trailer,
                location, city, state, driver_name,
                notes, 'pending'
            ))
            
            # Create notification for coordinators
            cursor.execute("""
                INSERT INTO submission_notifications (
                    submission_id, notification_type, message, target_role
                ) VALUES (?, ?, ?, ?)
            """, (
                submission_id,
                'new_submission',
                f"Driver {driver_name} submitted trailers: {new_trailer} ↔ {old_trailer} at {location}",
                'Coordinator'
            ))
            
            # Track change for real-time sync
            self.sync_manager.track_change(
                'trailer_submission', submission_id, 'submitted',
                None, {'driver': driver_name, 'location': location}
            )
            
            conn.commit()
            return True, submission_id
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def get_pending_submissions(self, status_filter='pending'):
        """Get all pending trailer submissions for review"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                submission_id,
                new_trailer_number,
                old_trailer_number,
                location,
                city,
                state,
                submitted_by_driver,
                submission_date,
                submission_notes,
                status,
                client_verified
            FROM trailer_submissions
            WHERE status = ? OR status = 'all'
            ORDER BY submission_date DESC
        """
        
        if status_filter == 'all':
            query = query.replace("WHERE status = ? OR status = 'all'", "")
            cursor.execute(query)
        else:
            cursor.execute(query, (status_filter,))
        
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        conn.close()
        
        submissions = []
        for row in results:
            submissions.append(dict(zip(columns, row)))
        
        return submissions
    
    def review_submission(self, submission_id, reviewer, action, notes=None, 
                         client_name=None, client_verified=False):
        """Coordinator reviews a submission"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            if action == 'verify_client':
                # Move to client verification status
                cursor.execute("""
                    UPDATE trailer_submissions
                    SET status = 'client_verification',
                        reviewed_by = ?,
                        review_date = ?,
                        review_notes = ?,
                        client_name = ?
                    WHERE submission_id = ?
                """, (reviewer, datetime.now(), notes, client_name, submission_id))
                
            elif action == 'approve':
                # Get submission details
                cursor.execute("""
                    SELECT new_trailer_number, old_trailer_number, location, city, state
                    FROM trailer_submissions
                    WHERE submission_id = ?
                """, (submission_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False, "Submission not found"
                
                new_trailer, old_trailer, location, city, state = result
                
                # Create actual trailer records
                # First, ensure location exists
                if city and state:
                    full_location = f"{location}, {city}, {state}"
                    cursor.execute("""
                        INSERT OR IGNORE INTO locations (
                            location_title, city, state
                        ) VALUES (?, ?, ?)
                    """, (location, city, state))
                else:
                    full_location = location
                
                # Insert new trailer
                cursor.execute("""
                    INSERT INTO trailers (
                        trailer_number, trailer_type, current_location,
                        status, swap_location, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    new_trailer, 'new', 'Fleet Memphis',
                    'available', location, f"Submitted by {reviewer}"
                ))
                new_id = cursor.lastrowid
                
                # Insert old trailer
                cursor.execute("""
                    INSERT INTO trailers (
                        trailer_number, trailer_type, current_location,
                        status, swap_location, paired_trailer_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    old_trailer, 'old', location,
                    'available', location, new_id, f"Pair with {new_trailer}"
                ))
                old_id = cursor.lastrowid
                
                # Update new trailer with pair
                cursor.execute("""
                    UPDATE trailers SET paired_trailer_id = ? WHERE id = ?
                """, (old_id, new_id))
                
                # Update submission record
                cursor.execute("""
                    UPDATE trailer_submissions
                    SET status = 'approved',
                        approved = 1,
                        approval_date = ?,
                        reviewed_by = ?,
                        review_notes = ?,
                        client_verified = ?,
                        trailer_ids_created = ?
                    WHERE submission_id = ?
                """, (
                    datetime.now(), reviewer, notes, 
                    1 if client_verified else 0,
                    json.dumps({'new_id': new_id, 'old_id': old_id}),
                    submission_id
                ))
                
                # Notify driver of approval
                cursor.execute("""
                    SELECT submitted_by_driver FROM trailer_submissions
                    WHERE submission_id = ?
                """, (submission_id,))
                driver = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO notifications (
                        driver_id, message, type, priority
                    ) VALUES (
                        (SELECT id FROM drivers WHERE driver_name = ?),
                        ?, 'success', 'medium'
                    )
                """, (
                    driver,
                    f"Your trailer submission {new_trailer} ↔ {old_trailer} has been approved!"
                ))
                
            elif action == 'reject':
                cursor.execute("""
                    UPDATE trailer_submissions
                    SET status = 'rejected',
                        approved = 0,
                        reviewed_by = ?,
                        review_date = ?,
                        rejection_reason = ?
                    WHERE submission_id = ?
                """, (reviewer, datetime.now(), notes, submission_id))
                
                # Notify driver of rejection
                cursor.execute("""
                    SELECT submitted_by_driver FROM trailer_submissions
                    WHERE submission_id = ?
                """, (submission_id,))
                driver = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO notifications (
                        driver_id, message, type, priority
                    ) VALUES (
                        (SELECT id FROM drivers WHERE driver_name = ?),
                        ?, 'warning', 'medium'
                    )
                """, (
                    driver,
                    f"Your trailer submission was not approved. Reason: {notes}"
                ))
            
            conn.commit()
            return True, f"Submission {action}ed successfully"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def get_driver_submissions(self, driver_name):
        """Get all submissions by a specific driver"""
        conn = db.get_connection()
        
        query = """
            SELECT 
                submission_id,
                new_trailer_number || ' ↔ ' || old_trailer_number as trailers,
                location,
                submission_date,
                status,
                approved,
                rejection_reason,
                review_notes
            FROM trailer_submissions
            WHERE submitted_by_driver = ?
            ORDER BY submission_date DESC
            LIMIT 20
        """
        
        df = pd.read_sql_query(query, conn, params=(driver_name,))
        conn.close()
        
        return df


def show_driver_trailer_submission(driver_name):
    """Driver interface to submit trailers found in the field"""
    
    st.markdown("### 🚛 Report Trailers Found")
    st.info("Found OLD trailers in the field that need pickup? Report them here for client verification!")
    
    submission_system = TrailerSubmissionSystem()
    
    # Submission form
    with st.form("trailer_submission_form", clear_on_submit=True):
        st.markdown("#### Trailer Information")
        
        # Trailer type selector (default to OLD)
        trailer_type = st.radio(
            "What type of trailer did you find?",
            ["OLD trailer (needs pickup)", "NEW trailer (from Fleet)"],
            index=0,  # Default to OLD
            help="Most field discoveries are OLD trailers that need to be picked up"
        )
        
        is_old_trailer = "OLD" in trailer_type
        
        col1, col2 = st.columns(2)
        
        with col1:
            if is_old_trailer:
                # Found an OLD trailer
                old_trailer = st.text_input(
                    "🔴 OLD Trailer Number *",
                    placeholder="e.g., TRL-OLD-456",
                    help="The trailer you found that needs to be picked up"
                )
                
                # Optional - if they know the NEW trailer to pair
                new_trailer = st.text_input(
                    "🟢 NEW Trailer Number (if known)",
                    placeholder="e.g., TRL-NEW-123 (optional)",
                    help="Leave blank if you don't know the NEW trailer assignment"
                )
            else:
                # Found a NEW trailer
                new_trailer = st.text_input(
                    "🟢 NEW Trailer Number *",
                    placeholder="e.g., TRL-NEW-123",
                    help="The NEW trailer from Fleet Memphis"
                )
                
                old_trailer = st.text_input(
                    "🔴 OLD Trailer Number (if known)",
                    placeholder="e.g., TRL-OLD-456 (optional)",
                    help="Leave blank if you don't know the OLD trailer to pair"
                )
            
            location = st.text_input(
                "📍 Current Location *",
                placeholder="e.g., Nashville Terminal",
                help="Where you found this trailer"
            )
            
            city = st.text_input(
                "City *",
                placeholder="e.g., Nashville"
            )
        
        with col2:
            state = st.selectbox(
                "State *",
                ["TN", "MS", "AR", "AL", "LA", "MO", "KY", "GA", "TX"]
            )
            
            # Client info if known
            client_name = st.text_input(
                "Client Name (if known)",
                placeholder="e.g., FedEx, UPS, etc.",
                help="Which client owns this trailer?"
            )
            
            notes = st.text_area(
                "Additional Details",
                placeholder="Condition, accessibility, dock number, etc.",
                height=100
            )
        
        # Photo upload (optional)
        photo = st.file_uploader(
            "Photo (optional)",
            type=['jpg', 'jpeg', 'png'],
            help="Photo of trailers or location for verification"
        )
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.warning("⚠️ Submissions require coordinator approval")
        
        with col2:
            submit = st.form_submit_button(
                "📤 Submit for Approval",
                type="primary",
                use_container_width=True
            )
        
        with col3:
            cancel = st.form_submit_button(
                "❌ Cancel",
                use_container_width=True
            )
        
        if submit:
            # Validate based on what was found
            if is_old_trailer:
                # OLD trailer found - must have at least OLD trailer number
                if old_trailer and location and city and state:
                    # If no NEW trailer provided, use placeholder
                    if not new_trailer:
                        new_trailer = "TBD-PENDING-ASSIGNMENT"
                    
                    success, result = submission_system.submit_trailer_pair(
                        driver_name, new_trailer, old_trailer,
                        location, city, state, 
                        notes=f"Type: OLD trailer found. Client: {client_name or 'Unknown'}. {notes}"
                    )
                else:
                    st.error("Please provide OLD trailer number and location details")
                    return
            else:
                # NEW trailer found - must have at least NEW trailer number
                if new_trailer and location and city and state:
                    # If no OLD trailer provided, use placeholder
                    if not old_trailer:
                        old_trailer = "TBD-PENDING-ASSIGNMENT"
                    
                    success, result = submission_system.submit_trailer_pair(
                        driver_name, new_trailer, old_trailer,
                        location, city, state,
                        notes=f"Type: NEW trailer found. Client: {client_name or 'Unknown'}. {notes}"
                    )
                else:
                    st.error("Please provide NEW trailer number and location details")
                    return
                
                if success:
                    trailer_type_text = "OLD trailer" if is_old_trailer else "NEW trailer"
                    st.success(f"""
                    ✅ {trailer_type_text} reported successfully!
                    
                    Submission ID: {result}
                    
                    The coordinator will:
                    1. Verify with client {client_name or '(to be determined)'}
                    2. Assign pairing if needed
                    3. Make available for pickup
                    
                    You'll be notified once approved.
                    """)
                    st.balloons()
                else:
                    st.error(f"Submission failed: {result}")
    
    # Show driver's submission history
    with st.expander("📋 My Submission History", expanded=False):
        submissions_df = submission_system.get_driver_submissions(driver_name)
        
        if not submissions_df.empty:
            # Format status column
            def format_status(row):
                if row['status'] == 'pending':
                    return '⏳ Pending'
                elif row['status'] == 'reviewing':
                    return '🔍 Under Review'
                elif row['status'] == 'client_verification':
                    return '📞 Verifying with Client'
                elif row['status'] == 'approved':
                    return '✅ Approved'
                elif row['status'] == 'rejected':
                    return '❌ Rejected'
                return row['status']
            
            submissions_df['Status'] = submissions_df.apply(format_status, axis=1)
            
            # Display columns
            display_cols = ['submission_date', 'trailers', 'location', 'Status']
            if 'rejection_reason' in submissions_df.columns:
                display_cols.append('rejection_reason')
            
            st.dataframe(
                submissions_df[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'submission_date': st.column_config.DateColumn('Date', format='MM/DD/YYYY'),
                    'trailers': 'Trailers',
                    'location': 'Location',
                    'Status': 'Status',
                    'rejection_reason': 'Notes'
                }
            )
        else:
            st.info("No submissions yet")


def show_coordinator_approval_queue():
    """Coordinator interface to review and approve trailer submissions"""
    
    st.markdown("### 📋 Trailer Submission Approval Queue")
    
    submission_system = TrailerSubmissionSystem()
    
    # Filter tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "⏳ Pending", "📞 Client Verification", "✅ Approved", "❌ Rejected"
    ])
    
    with tab1:
        show_submissions_by_status('pending', submission_system)
    
    with tab2:
        show_submissions_by_status('client_verification', submission_system)
    
    with tab3:
        show_submissions_by_status('approved', submission_system)
    
    with tab4:
        show_submissions_by_status('rejected', submission_system)


def show_submissions_by_status(status, submission_system):
    """Display submissions filtered by status"""
    
    submissions = submission_system.get_pending_submissions(status)
    
    if not submissions:
        st.info(f"No {status} submissions")
        return
    
    for submission in submissions:
        with st.container():
            # Submission card
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                # Show trailer info with clear OLD/NEW indicators
                new_trailer_display = submission['new_trailer_number']
                old_trailer_display = submission['old_trailer_number']
                
                # Add visual indicators
                if "TBD" in new_trailer_display:
                    trailer_display = f"🔴 OLD: {old_trailer_display} (NEW to be assigned)"
                elif "TBD" in old_trailer_display:
                    trailer_display = f"🟢 NEW: {new_trailer_display} (OLD to be assigned)"
                else:
                    trailer_display = f"🟢 NEW: {new_trailer_display} ↔ 🔴 OLD: {old_trailer_display}"
                
                st.markdown(f"**{trailer_display}**")
                st.caption(f"📍 {submission['location']}, {submission['city']}, {submission['state']}")
                st.caption(f"Submitted by: {submission['submitted_by_driver']} on {submission['submission_date']}")
                
                if submission['submission_notes']:
                    st.caption(f"Notes: {submission['submission_notes']}")
            
            with col2:
                if status == 'pending':
                    # Client verification step
                    client_name = st.text_input(
                        "Client Name",
                        key=f"client_{submission['submission_id']}",
                        placeholder="Enter client name"
                    )
                    
                    if st.button("📞 Verify with Client", key=f"verify_{submission['submission_id']}"):
                        if client_name:
                            success, msg = submission_system.review_submission(
                                submission['submission_id'],
                                st.session_state.get('username', 'Coordinator'),
                                'verify_client',
                                notes=f"Contacting {client_name} for verification",
                                client_name=client_name
                            )
                            if success:
                                st.success("Moved to client verification")
                                st.rerun()
                        else:
                            st.error("Enter client name first")
            
            with col3:
                if status in ['pending', 'client_verification']:
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        if st.button("✅ Approve", key=f"approve_{submission['submission_id']}", type="primary"):
                            notes = st.session_state.get(f"notes_{submission['submission_id']}", "")
                            success, msg = submission_system.review_submission(
                                submission['submission_id'],
                                st.session_state.get('username', 'Coordinator'),
                                'approve',
                                notes=notes or "Client verified",
                                client_verified=True
                            )
                            if success:
                                st.success("Trailers approved and added!")
                                st.balloons()
                                st.rerun()
                    
                    with col_b:
                        if st.button("❌ Reject", key=f"reject_{submission['submission_id']]}"):
                            reason = st.text_input(
                                "Rejection reason",
                                key=f"reason_{submission['submission_id']}"
                            )
                            if reason:
                                success, msg = submission_system.review_submission(
                                    submission['submission_id'],
                                    st.session_state.get('username', 'Coordinator'),
                                    'reject',
                                    notes=reason
                                )
                                if success:
                                    st.warning("Submission rejected")
                                    st.rerun()
                            else:
                                st.error("Please provide rejection reason")
                
                elif status == 'approved':
                    st.success(f"✅ Approved by {submission.get('reviewed_by', 'Unknown')}")
                
                elif status == 'rejected':
                    st.error(f"❌ Rejected: {submission.get('rejection_reason', 'No reason provided')}")
            
            st.markdown("---")


# Export functions
__all__ = [
    'TrailerSubmissionSystem',
    'show_driver_trailer_submission',
    'show_coordinator_approval_queue'
]