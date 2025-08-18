"""
Driver Self-Assignment Module
Allows drivers to self-assign available moves with real-time tracking
Includes progress monitoring, pay calculation, and load management
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import mileage_calculator as mileage_calc
import json
import sqlite3
from database_connection_manager import db_manager

class DriverSelfAssignment:
    """Manages the driver self-assignment workflow"""
    
    def __init__(self, driver_id, driver_name):
        self.driver_id = driver_id
        self.driver_name = driver_name
        self.conn = db.get_connection()
        self.load_driver_info()
        
    def load_driver_info(self):
        """Load driver information and availability status"""
        cursor = self.conn.cursor()
        
        # Get driver availability
        cursor.execute("""
            SELECT status, current_move_id, completed_moves_today, max_daily_moves
            FROM driver_availability
            WHERE driver_id = ?
        """, (self.driver_id,))
        
        result = cursor.fetchone()
        if result:
            self.status, self.current_move_id, self.completed_today, self.max_daily = result
        else:
            # Initialize if not exists
            cursor.execute("""
                INSERT INTO driver_availability (driver_id, status)
                VALUES (?, 'available')
            """, (self.driver_id,))
            self.conn.commit()
            self.status = 'available'
            self.current_move_id = None
            self.completed_today = 0
            self.max_daily = 1
    
    def get_available_moves(self):
        """Get all available moves for self-assignment"""
        cursor = self.conn.cursor()
        
        # Get available trailer pairs with location info
        query = """
            SELECT 
                t1.id as new_trailer_id,
                t1.trailer_number as new_trailer,
                t2.id as old_trailer_id,
                t2.trailer_number as old_trailer,
                t1.swap_location as location,
                l.address as full_address,
                l.city,
                l.state,
                t1.notes as new_trailer_notes,
                t2.notes as old_trailer_notes,
                t1.is_reserved,
                t1.reserved_by_driver,
                t1.reserved_until
            FROM trailers t1
            LEFT JOIN trailers t2 ON t1.paired_trailer_id = t2.id
            LEFT JOIN locations l ON t1.swap_location = l.location_title
            WHERE t1.trailer_type = 'new' 
            AND t1.status = 'available'
            AND t2.trailer_number IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM moves m 
                WHERE (m.new_trailer = t1.trailer_number OR m.old_trailer = t2.trailer_number)
                AND m.status IN ('assigned', 'in_progress', 'pickup_complete')
            )
            ORDER BY t1.swap_location, t1.trailer_number
        """
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        
        available_moves = []
        for row in results:
            move = dict(zip(columns, row))
            
            # Check reservation status
            if move['is_reserved']:
                if move['reserved_by_driver'] == self.driver_name:
                    move['availability'] = 'reserved_by_you'
                elif move['reserved_until'] and datetime.now() > datetime.fromisoformat(move['reserved_until']):
                    # Reservation expired, clear it
                    self.clear_reservation(move['new_trailer_id'])
                    move['availability'] = 'available'
                else:
                    move['availability'] = 'reserved'
            else:
                move['availability'] = 'available'
            
            # Calculate mileage and pay
            base_location = self.get_base_location()
            if base_location and move['location']:
                from_address = mileage_calc.get_location_full_address(base_location)
                to_address = move['full_address']
                
                if from_address and to_address:
                    one_way_miles, _ = mileage_calc.calculate_mileage_with_cache(
                        base_location, move['location'], from_address, to_address
                    )
                    if one_way_miles:
                        move['one_way_miles'] = one_way_miles
                        move['round_trip_miles'] = one_way_miles * 2
                        move['estimated_pay'] = self.calculate_driver_pay(move['round_trip_miles'])
                    else:
                        move['one_way_miles'] = 0
                        move['round_trip_miles'] = 0
                        move['estimated_pay'] = 0
            
            available_moves.append(move)
        
        return available_moves
    
    def get_base_location(self):
        """Get the default base location"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT location_title FROM locations WHERE is_base_location = 1 LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else "Fleet Memphis"
    
    def calculate_driver_pay(self, miles):
        """Calculate driver pay based on mileage"""
        rate_per_mile = 2.10
        factoring_fee = 0.03
        return miles * rate_per_mile * (1 - factoring_fee)
    
    def reserve_trailer(self, new_trailer_id, duration_minutes=30):
        """Reserve a trailer for the driver"""
        cursor = self.conn.cursor()
        
        try:
            # Check if already reserved
            cursor.execute("""
                SELECT is_reserved, reserved_by_driver 
                FROM trailers 
                WHERE id = ?
            """, (new_trailer_id,))
            
            is_reserved, reserved_by = cursor.fetchone()
            
            if is_reserved and reserved_by != self.driver_name:
                return False, "Trailer already reserved by another driver"
            
            # Reserve the trailer
            reservation_until = datetime.now() + timedelta(minutes=duration_minutes)
            cursor.execute("""
                UPDATE trailers
                SET is_reserved = 1,
                    reserved_by_driver = ?,
                    reserved_until = ?
                WHERE id = ?
            """, (self.driver_name, reservation_until.isoformat(), new_trailer_id))
            
            self.conn.commit()
            return True, f"Trailer reserved until {reservation_until.strftime('%I:%M %p')}"
            
        except Exception as e:
            self.conn.rollback()
            return False, str(e)
    
    def clear_reservation(self, trailer_id):
        """Clear a trailer reservation"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE trailers
            SET is_reserved = 0,
                reserved_by_driver = NULL,
                reserved_until = NULL
            WHERE id = ?
        """, (trailer_id,))
        self.conn.commit()
    
    def self_assign_move(self, new_trailer, old_trailer, location):
        """Self-assign a move to the driver"""
        cursor = self.conn.cursor()
        
        try:
            # Begin transaction for atomicity
            cursor.execute("BEGIN TRANSACTION")
            
            # Check if driver can take more moves
            if self.status != 'available':
                raise Exception("You already have an active move")
            
            if self.completed_today >= self.max_daily:
                raise Exception(f"Daily limit of {self.max_daily} moves reached")
            
            # Check if move already exists
            cursor.execute("""
                SELECT id FROM moves
                WHERE (new_trailer = ? OR old_trailer = ?)
                AND status IN ('assigned', 'in_progress', 'pickup_complete')
            """, (new_trailer, old_trailer))
            
            if cursor.fetchone():
                raise Exception("This move is already assigned")
            
            # Generate move ID
            move_id = f"SELF-{datetime.now().strftime('%Y%m%d')}-{self.driver_id}-{datetime.now().strftime('%H%M%S')}"
            
            # Get location details
            base_location = self.get_base_location()
            
            # Create the move
            cursor.execute("""
                INSERT INTO moves (
                    move_id, new_trailer, old_trailer, 
                    pickup_location, delivery_location,
                    driver_name, move_date, status,
                    self_assigned, assigned_at, assignment_type,
                    created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                move_id, new_trailer, old_trailer,
                base_location, location,
                self.driver_name, datetime.now().date(),
                'assigned', 1, datetime.now(), 'self',
                f"Driver: {self.driver_name}", datetime.now()
            ))
            
            # Update driver availability
            cursor.execute("""
                UPDATE driver_availability
                SET status = 'assigned',
                    current_move_id = ?,
                    updated_at = ?
                WHERE driver_id = ?
            """, (move_id, datetime.now(), self.driver_id))
            
            # Update trailer status
            cursor.execute("""
                UPDATE trailers
                SET status = 'assigned',
                    is_reserved = 0,
                    reserved_by_driver = NULL,
                    reserved_until = NULL
                WHERE trailer_number IN (?, ?)
            """, (new_trailer, old_trailer))
            
            # Log assignment in history
            cursor.execute("""
                INSERT INTO assignment_history (
                    move_id, driver_id, driver_name,
                    action, action_by, action_type, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                move_id, self.driver_id, self.driver_name,
                'assigned', self.driver_name, 'self', datetime.now()
            ))
            
            # Create notification for coordinators
            self.create_assignment_notification(move_id, new_trailer, old_trailer, location)
            
            # Commit transaction
            cursor.execute("COMMIT")
            self.conn.commit()
            
            return True, move_id
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            return False, str(e)
    
    def create_assignment_notification(self, move_id, new_trailer, old_trailer, location):
        """Create notification for self-assignment"""
        cursor = self.conn.cursor()
        
        message = f"Driver {self.driver_name} self-assigned: {new_trailer} <-> {old_trailer} at {location}"
        
        # Notify all coordinators
        cursor.execute("""
            INSERT INTO notifications (
                driver_id, move_id, message, type, priority, action_required
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (self.driver_id, move_id, message, 'assignment', 'medium', 0))
        
        self.conn.commit()
    
    def unassign_move(self, move_id, reason="Driver cancelled"):
        """Unassign a self-assigned move"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            # Get move details
            cursor.execute("""
                SELECT new_trailer, old_trailer, status
                FROM moves WHERE move_id = ?
            """, (move_id,))
            
            result = cursor.fetchone()
            if not result:
                raise Exception("Move not found")
            
            new_trailer, old_trailer, status = result
            
            if status not in ['assigned']:
                raise Exception("Can only unassign moves that haven't started")
            
            # Update move status
            cursor.execute("""
                UPDATE moves
                SET status = 'cancelled',
                    unassigned_at = ?,
                    unassigned_reason = ?
                WHERE move_id = ?
            """, (datetime.now(), reason, move_id))
            
            # Update driver availability
            cursor.execute("""
                UPDATE driver_availability
                SET status = 'available',
                    current_move_id = NULL,
                    updated_at = ?
                WHERE driver_id = ?
            """, (datetime.now(), self.driver_id))
            
            # Update trailer status
            cursor.execute("""
                UPDATE trailers
                SET status = 'available'
                WHERE trailer_number IN (?, ?)
            """, (new_trailer, old_trailer))
            
            # Log unassignment
            cursor.execute("""
                INSERT INTO assignment_history (
                    move_id, driver_id, driver_name,
                    action, action_by, action_type, reason, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                move_id, self.driver_id, self.driver_name,
                'unassigned', self.driver_name, 'self', reason, datetime.now()
            ))
            
            cursor.execute("COMMIT")
            self.conn.commit()
            
            return True, "Move unassigned successfully"
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            return False, str(e)
    
    def get_my_current_move(self):
        """Get driver's current active move with progress tracking"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                m.move_id,
                m.new_trailer,
                m.old_trailer,
                m.pickup_location,
                m.delivery_location,
                m.status,
                m.total_miles,
                m.driver_pay,
                m.pickup_time,
                m.delivery_time,
                m.pod_uploaded,
                m.created_at,
                m.self_assigned
            FROM moves m
            WHERE m.driver_name = ?
            AND m.status IN ('assigned', 'in_progress', 'pickup_complete')
            ORDER BY m.created_at DESC
            LIMIT 1
        """
        
        cursor.execute(query, (self.driver_name,))
        columns = [desc[0] for desc in cursor.description]
        result = cursor.fetchone()
        
        if result:
            move = dict(zip(columns, result))
            
            # Calculate progress percentage
            progress_steps = {
                'assigned': 0,
                'in_progress': 33,
                'pickup_complete': 66,
                'completed': 100
            }
            move['progress_percentage'] = progress_steps.get(move['status'], 0)
            
            # Calculate estimated pay if not set
            if not move['driver_pay'] and move['total_miles']:
                move['driver_pay'] = self.calculate_driver_pay(move['total_miles'])
            
            return move
        
        return None
    
    def get_my_completed_moves(self, days=30):
        """Get driver's completed moves with earnings"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                m.move_id,
                m.move_date,
                m.new_trailer,
                m.old_trailer,
                m.delivery_location,
                m.total_miles,
                m.driver_pay,
                m.payment_status,
                m.driver_paid
            FROM moves m
            WHERE m.driver_name = ?
            AND m.status = 'completed'
            AND m.move_date >= date('now', '-' || ? || ' days')
            ORDER BY m.move_date DESC
        """
        
        cursor.execute(query, (self.driver_name, days))
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        
        moves = []
        total_earnings = 0
        paid_earnings = 0
        pending_earnings = 0
        
        for row in results:
            move = dict(zip(columns, row))
            moves.append(move)
            
            if move['driver_pay']:
                total_earnings += move['driver_pay']
                if move['driver_paid']:
                    paid_earnings += move['driver_pay']
                else:
                    pending_earnings += move['driver_pay']
        
        return {
            'moves': moves,
            'total_earnings': total_earnings,
            'paid_earnings': paid_earnings,
            'pending_earnings': pending_earnings,
            'move_count': len(moves)
        }


def show_self_assignment_interface(driver_id, driver_name):
    """Main interface for driver self-assignment"""
    
    assignment = DriverSelfAssignment(driver_id, driver_name)
    
    # Header with driver stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Status", assignment.status.title())
    
    with col2:
        st.metric("Today's Moves", f"{assignment.completed_today}/{assignment.max_daily}")
    
    # Get earnings summary
    completed = assignment.get_my_completed_moves(30)
    
    with col3:
        st.metric("Pending Pay", f"${completed['pending_earnings']:,.2f}")
    
    with col4:
        st.metric("30-Day Earnings", f"${completed['total_earnings']:,.2f}")
    
    st.markdown("---")
    
    # Check if driver has current move
    current_move = assignment.get_my_current_move()
    
    if current_move:
        # Show current move progress
        st.markdown("### 🚚 Current Move Progress")
        
        # Progress bar
        progress = current_move['progress_percentage']
        st.progress(progress / 100)
        st.caption(f"Status: **{current_move['status'].replace('_', ' ').title()}** ({progress}% complete)")
        
        # Move details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Move Details**")
            st.write(f"Move ID: {current_move['move_id']}")
            st.write(f"NEW: {current_move['new_trailer']}")
            st.write(f"OLD: {current_move['old_trailer']}")
        
        with col2:
            st.markdown("**Route**")
            st.write(f"From: {current_move['pickup_location']}")
            st.write(f"To: {current_move['delivery_location']}")
            if current_move['total_miles']:
                st.write(f"Miles: {current_move['total_miles']}")
        
        with col3:
            st.markdown("**Earnings**")
            if current_move['driver_pay']:
                st.write(f"Pay: ${current_move['driver_pay']:,.2f}")
            st.write(f"Self-Assigned: {'Yes' if current_move['self_assigned'] else 'No'}")
        
        # Action buttons based on status
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        if current_move['status'] == 'assigned':
            with col1:
                if st.button("🚀 Start Move", type="primary", use_container_width=True):
                    # Update status to in_progress
                    st.success("Move started! Drive safely.")
                    st.rerun()
            
            with col3:
                if st.button("❌ Cancel Assignment", use_container_width=True):
                    success, message = assignment.unassign_move(current_move['move_id'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    else:
        # Show available moves for self-assignment
        st.markdown("### 📋 Available Moves")
        
        available_moves = assignment.get_available_moves()
        
        if not available_moves:
            st.info("No moves available for self-assignment at this time.")
        else:
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                location_filter = st.selectbox(
                    "Filter by Location",
                    ["All"] + list(set(m['location'] for m in available_moves if m['location']))
                )
            
            with col2:
                min_pay = st.number_input("Minimum Pay", value=0, step=50)
            
            with col3:
                sort_by = st.selectbox(
                    "Sort By",
                    ["Location", "Pay (High to Low)", "Miles (Low to High)"]
                )
            
            # Apply filters
            filtered_moves = available_moves
            
            if location_filter != "All":
                filtered_moves = [m for m in filtered_moves if m['location'] == location_filter]
            
            if min_pay > 0:
                filtered_moves = [m for m in filtered_moves if m.get('estimated_pay', 0) >= min_pay]
            
            # Apply sorting
            if sort_by == "Pay (High to Low)":
                filtered_moves.sort(key=lambda x: x.get('estimated_pay', 0), reverse=True)
            elif sort_by == "Miles (Low to High)":
                filtered_moves.sort(key=lambda x: x.get('round_trip_miles', 0))
            else:
                filtered_moves.sort(key=lambda x: x.get('location', ''))
            
            # Display moves as cards
            for move in filtered_moves:
                if move['availability'] not in ['available', 'reserved_by_you']:
                    continue
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    
                    with col1:
                        st.markdown(f"**{move['location']}**")
                        st.caption(f"NEW: {move['new_trailer']} | OLD: {move['old_trailer']}")
                        if move['city'] and move['state']:
                            st.caption(f"📍 {move['city']}, {move['state']}")
                    
                    with col2:
                        if move.get('round_trip_miles'):
                            st.metric("Miles", f"{move['round_trip_miles']:.1f}")
                        else:
                            st.metric("Miles", "N/A")
                    
                    with col3:
                        if move.get('estimated_pay'):
                            st.metric("Est. Pay", f"${move['estimated_pay']:,.2f}")
                        else:
                            st.metric("Est. Pay", "N/A")
                    
                    with col4:
                        if move['availability'] == 'reserved_by_you':
                            if st.button("✅ Confirm Assignment", key=f"assign_{move['new_trailer_id']}", type="primary"):
                                success, move_id = assignment.self_assign_move(
                                    move['new_trailer'],
                                    move['old_trailer'],
                                    move['location']
                                )
                                if success:
                                    st.success(f"Move {move_id} assigned to you!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(move_id)
                        else:
                            if st.button("📌 Reserve & Review", key=f"reserve_{move['new_trailer_id']}"):
                                success, message = assignment.reserve_trailer(move['new_trailer_id'])
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                    
                    # Show notes if available
                    if move.get('new_trailer_notes') or move.get('old_trailer_notes'):
                        with st.expander("📝 Notes"):
                            if move.get('new_trailer_notes'):
                                st.write(f"**New Trailer:** {move['new_trailer_notes']}")
                            if move.get('old_trailer_notes'):
                                st.write(f"**Old Trailer:** {move['old_trailer_notes']}")
                    
                    st.markdown("---")
    
    # Show completed moves in expander
    with st.expander("📊 My Completed Moves (Last 30 Days)"):
        completed_data = assignment.get_my_completed_moves(30)
        
        if completed_data['moves']:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Moves", completed_data['move_count'])
            with col2:
                st.metric("Paid", f"${completed_data['paid_earnings']:,.2f}")
            with col3:
                st.metric("Pending", f"${completed_data['pending_earnings']:,.2f}")
            
            # Moves table
            df = pd.DataFrame(completed_data['moves'])
            df['move_date'] = pd.to_datetime(df['move_date']).dt.strftime('%m/%d/%Y')
            df['driver_pay'] = df['driver_pay'].apply(lambda x: f"${x:,.2f}" if x else "TBD")
            df['payment_status'] = df['payment_status'].str.title()
            
            display_columns = ['move_date', 'new_trailer', 'old_trailer', 'delivery_location', 'total_miles', 'driver_pay', 'payment_status']
            st.dataframe(df[display_columns], use_container_width=True, hide_index=True)
        else:
            st.info("No completed moves in the last 30 days")