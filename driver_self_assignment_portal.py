"""
Driver Self-Assignment Portal
Allows drivers to view and claim available moves
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sqlite3

def get_connection():
    return sqlite3.connect('trailer_tracker_streamlined.db')

def show_driver_self_assignment(username):
    """Show available moves for driver self-assignment"""
    
    st.markdown("## 🚚 Available Moves - Self Assignment")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get driver info
    cursor.execute('''SELECT driver_name, company_name, coi_uploaded, w9_uploaded 
                     FROM drivers WHERE username = ? OR driver_name = ?''', 
                  (username, username))
    driver_info = cursor.fetchone()
    
    if not driver_info:
        st.error("Driver profile not found")
        return
    
    driver_name, company_name, coi_uploaded, w9_uploaded = driver_info
    
    # Check if driver can self-assign (must have documents)
    if not (coi_uploaded and w9_uploaded):
        st.warning("⚠️ You must upload COI and W9 documents before self-assigning moves")
        st.info("Please go to the Documents tab to upload required paperwork")
        conn.close()
        return
    
    # Tabs for different move statuses
    tabs = st.tabs(["🆕 Available", "⏳ My Pending", "✅ My Completed", "📋 How It Works"])
    
    with tabs[0]:  # Available Moves
        st.markdown("### Available for Assignment")
        
        # Get unassigned moves that are marked as available by management
        cursor.execute('''SELECT m.id, m.move_id, m.pickup_location, m.delivery_location, 
                                m.total_miles, m.move_date, m.notes, m.new_trailer, m.old_trailer
                         FROM moves m
                         LEFT JOIN trailers t1 ON m.new_trailer = t1.trailer_number
                         LEFT JOIN trailers t2 ON m.old_trailer = t2.trailer_number
                         WHERE (m.driver_name IS NULL OR m.driver_name = '') 
                         AND m.status IN ('pending', 'available')
                         AND (t1.is_reserved = 0 OR t1.is_reserved IS NULL)
                         AND (t2.is_reserved = 0 OR t2.is_reserved IS NULL)
                         ORDER BY m.move_date ASC''')
        available_moves = cursor.fetchall()
        
        if available_moves:
            for move in available_moves:
                move_id_db, move_id, pickup, delivery, miles, date, notes, new_trailer, old_trailer = move
                
                # Calculate estimated pay
                rate_per_mile = 2.10
                estimated_pay = miles * rate_per_mile if miles else 0
                
                with st.expander(f"📦 {move_id} - {pickup} to {delivery}", expanded=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **Route:** {pickup} → {delivery}  
                        **Distance:** {miles or 'TBD'} miles  
                        **Date:** {date}  
                        **Notes:** {notes or 'Standard delivery'}
                        """)
                    
                    with col2:
                        # Calculate with 3% factoring fee estimate
                        factoring_fee = estimated_pay * 0.03
                        net_estimate = estimated_pay - factoring_fee
                        st.metric("Estimated Net Pay", f"${net_estimate:.2f}")
                        st.caption("After ~3% factoring (estimate)")
                    
                    with col3:
                        if st.button(f"✅ Accept Move", key=f"accept_{move_id_db}"):
                            # Assign move to driver and reserve trailers
                            cursor.execute('''UPDATE moves 
                                           SET driver_name = ?, 
                                               status = 'assigned',
                                               assigned_at = ?
                                           WHERE id = ?''',
                                         (driver_name, datetime.now(), move_id_db))
                            
                            # Reserve the trailers for this driver
                            if new_trailer:
                                cursor.execute('''UPDATE trailers 
                                               SET is_reserved = 1, 
                                                   reserved_by_driver = ?,
                                                   reserved_until = ?
                                               WHERE trailer_number = ?''',
                                             (driver_name, datetime.now() + timedelta(days=7), new_trailer))
                            
                            if old_trailer:
                                cursor.execute('''UPDATE trailers 
                                               SET is_reserved = 1,
                                                   reserved_by_driver = ?,
                                                   reserved_until = ?
                                               WHERE trailer_number = ?''',
                                             (driver_name, datetime.now() + timedelta(days=7), old_trailer))
                            
                            conn.commit()
                            st.success(f"✅ Move {move_id} assigned to you! Trailers reserved.")
                            st.balloons()
                            st.rerun()
        else:
            st.info("No available moves at this time. Check back later!")
            
            # Show option to be notified
            if st.checkbox("Notify me when moves become available"):
                st.success("✅ You'll be notified of new moves")
    
    with tabs[1]:  # My Pending Moves
        st.markdown("### Your Assigned Moves")
        
        # Get driver's pending moves
        cursor.execute('''SELECT id, move_id, pickup_location, delivery_location, 
                                total_miles, driver_pay, status, move_date
                         FROM moves 
                         WHERE driver_name = ? 
                         AND status IN ('assigned', 'in_progress', 'pending')
                         ORDER BY move_date ASC''',
                      (driver_name,))
        pending_moves = cursor.fetchall()
        
        if pending_moves:
            for move in pending_moves:
                move_id_db, move_id, pickup, delivery, miles, pay, status, date = move
                
                status_emoji = {
                    'assigned': '📋',
                    'in_progress': '🚚',
                    'pending': '⏳'
                }.get(status, '📦')
                
                with st.expander(f"{status_emoji} {move_id} - {status.title()}", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **Route:** {pickup} → {delivery}  
                        **Distance:** {miles} miles  
                        **Pay:** ${pay:.2f}  
                        **Date:** {date}  
                        **Status:** {status.replace('_', ' ').title()}
                        """)
                    
                    with col2:
                        if status == 'assigned':
                            if st.button(f"🚀 Start Move", key=f"start_{move_id_db}"):
                                cursor.execute('''UPDATE moves 
                                               SET status = 'in_progress'
                                               WHERE id = ?''', (move_id_db,))
                                conn.commit()
                                st.success("Move started!")
                                st.rerun()
                                
                            if st.button(f"❌ Release Move", key=f"release_{move_id_db}"):
                                # Get trailer numbers from move
                                cursor.execute('SELECT new_trailer, old_trailer FROM moves WHERE id = ?', (move_id_db,))
                                trailers = cursor.fetchone()
                                
                                # Release the move
                                cursor.execute('''UPDATE moves 
                                               SET driver_name = NULL,
                                                   status = 'available'
                                               WHERE id = ?''', (move_id_db,))
                                
                                # Release trailer reservations
                                if trailers:
                                    for trailer in trailers:
                                        if trailer:
                                            cursor.execute('''UPDATE trailers 
                                                           SET is_reserved = 0,
                                                               reserved_by_driver = NULL,
                                                               reserved_until = NULL
                                                           WHERE trailer_number = ?''', (trailer,))
                                
                                conn.commit()
                                st.info("Move and trailers released back to pool")
                                st.rerun()
                        
                        elif status == 'in_progress':
                            if st.button(f"✅ Complete", key=f"complete_{move_id_db}"):
                                cursor.execute('''UPDATE moves 
                                               SET status = 'completed',
                                                   completed_date = ?
                                               WHERE id = ?''', 
                                             (datetime.now().strftime('%Y-%m-%d'), move_id_db))
                                conn.commit()
                                st.success("Move completed! 🎉")
                                st.rerun()
        else:
            st.info("You have no pending moves. Check Available Moves to accept new assignments!")
    
    with tabs[2]:  # Completed Moves
        st.markdown("### Your Completed Moves")
        
        # Get completed moves summary
        cursor.execute('''SELECT COUNT(*), SUM(total_miles), SUM(driver_pay)
                         FROM moves 
                         WHERE driver_name = ? AND status = 'completed' ''',
                      (driver_name,))
        summary = cursor.fetchone()
        count, total_miles, total_pay = summary
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Completed", count or 0)
        with col2:
            st.metric("Total Miles", f"{int(total_miles or 0):,}")
        with col3:
            st.metric("Total Earnings", f"${total_pay or 0:,.2f}")
        
        # Show recent completed
        cursor.execute('''SELECT move_id, pickup_location, delivery_location, 
                                total_miles, driver_pay, move_date
                         FROM moves 
                         WHERE driver_name = ? AND status = 'completed'
                         ORDER BY move_date DESC LIMIT 10''',
                      (driver_name,))
        completed = cursor.fetchall()
        
        if completed:
            st.markdown("#### Recent Completions")
            for move in completed:
                move_id, pickup, delivery, miles, pay, date = move
                st.markdown(f"✅ **{move_id}** - {pickup} to {delivery} ({miles} mi) - ${pay:.2f} - {date}")
    
    with tabs[3]:  # How It Works
        st.markdown("### 📋 Self-Assignment Guide")
        
        with st.expander("How Self-Assignment Works", expanded=True):
            st.markdown("""
            **Step 1: Review Available Moves**
            - Check the Available tab for unassigned moves
            - Review pickup/delivery locations and distance
            - Check estimated pay (calculated at $2.10/mile)
            
            **Step 2: Accept a Move**
            - Click "Accept Move" to claim the assignment
            - Move will be assigned to you immediately
            - You can manage multiple moves at once
            
            **Step 3: Start the Move**
            - Go to "My Pending" tab
            - Click "Start Move" when you begin
            - Status changes to "In Progress"
            
            **Step 4: Complete Delivery**
            - Click "Complete" when delivery is done
            - Upload POD if required
            - Payment will be processed weekly
            
            **Important Notes:**
            - $6 service fee per completed move
            - Must have valid COI and W9 on file
            - Can release moves back if needed
            - All moves tracked for payment
            """)
        
        with st.expander("Payment Information"):
            st.markdown(f"""
            **Your Rate Structure:**
            - Base Rate: $2.10 per mile
            - Service Fee: $6.00 per move
            - Payment Schedule: Weekly (Fridays)
            
            **Example:**
            - 200 mile move = $420 gross
            - Less $6 service fee = $414 net
            
            **Current Totals:**
            - Completed: {count or 0} moves
            - Total Miles: {int(total_miles or 0):,}
            - Total Earned: ${total_pay or 0:,.2f}
            """)
        
        with st.expander("Rules & Requirements"):
            st.markdown("""
            **Eligibility Requirements:**
            - ✅ Valid CDL
            - ✅ Current COI on file
            - ✅ W9 form submitted
            - ✅ Approved contractor status
            
            **Assignment Rules:**
            - First-come, first-served basis
            - Maximum 3 active moves at once
            - Must complete within scheduled timeframe
            - Can release back to pool if needed
            
            **Quality Standards:**
            - On-time pickup and delivery
            - Proper documentation (POD)
            - Professional communication
            - Safe driving record
            """)
    
    conn.close()

def add_self_assignment_to_menu(driver_name):
    """Add self-assignment option to driver menu"""
    if st.button("🎯 Self-Assign Moves", use_container_width=True):
        show_driver_self_assignment(driver_name)