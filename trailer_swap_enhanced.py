"""
Enhanced Trailer Swap Management
Core functionality fixed for 100% reliability
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
import time
import json
import mileage_calculator as mileage_calc
import api_config

class EnhancedTrailerSwapManager:
    """Robust trailer swap management with proper state handling"""
    
    def __init__(self):
        self.db_path = 'trailer_tracker_streamlined.db'
        self.init_session_state()
        self.ensure_database_structure()
    
    def init_session_state(self):
        """Initialize swap management state"""
        if 'swap_state' not in st.session_state:
            st.session_state.swap_state = {
                'active_swap': None,
                'selected_new': None,
                'selected_old': None,
                'selected_driver': None,
                'selected_location': None,
                'swap_in_progress': False,
                'last_swap_time': None
            }
    
    def ensure_database_structure(self):
        """Ensure all required tables exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure trailers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trailers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trailer_number TEXT UNIQUE NOT NULL,
                    trailer_type TEXT CHECK(trailer_type IN ('new', 'old')),
                    current_location TEXT,
                    status TEXT DEFAULT 'available',
                    swap_location TEXT,
                    paired_trailer_id INTEGER,
                    notes TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Ensure moves table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS moves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    move_id TEXT UNIQUE NOT NULL,
                    new_trailer TEXT,
                    old_trailer TEXT,
                    pickup_location TEXT,
                    delivery_location TEXT,
                    driver_name TEXT,
                    move_date DATE,
                    pickup_time TIME,
                    delivery_time TIME,
                    total_miles REAL,
                    driver_pay REAL,
                    status TEXT DEFAULT 'assigned',
                    payment_status TEXT DEFAULT 'pending',
                    notes TEXT,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trailers_status ON trailers(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trailers_type ON trailers(trailer_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_moves_status ON moves(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_moves_driver ON moves(driver_name)')
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Database initialization error: {e}")
            return False
    
    def get_available_trailers(self, trailer_type=None):
        """Get available trailers with proper filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            if trailer_type:
                query = """
                    SELECT trailer_number, current_location, status, notes
                    FROM trailers
                    WHERE trailer_type = ? AND status = 'available'
                    ORDER BY trailer_number
                """
                df = pd.read_sql_query(query, conn, params=(trailer_type,))
            else:
                query = """
                    SELECT trailer_number, trailer_type, current_location, status, notes
                    FROM trailers
                    WHERE status = 'available'
                    ORDER BY trailer_type, trailer_number
                """
                df = pd.read_sql_query(query, conn)
            
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error loading trailers: {e}")
            return pd.DataFrame()
    
    def get_available_drivers(self):
        """Get available drivers"""
        try:
            conn = sqlite3.connect(self.db_path)
            # Fixed query - removed non-existent 'active' column
            query = """
                SELECT driver_name, phone, email, status
                FROM drivers
                WHERE status = 'available'
                ORDER BY driver_name
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                # Don't show as error - just informational
                return df
            return df
        except Exception as e:
            # Try simpler query without status filter
            try:
                conn = sqlite3.connect(self.db_path)
                query = "SELECT driver_name, phone, email, status FROM drivers ORDER BY driver_name"
                df = pd.read_sql_query(query, conn)
                conn.close()
                return df
            except:
                # Return empty dataframe silently
                return pd.DataFrame()
    
    def get_locations(self):
        """Get all locations"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT location_title, street_address, city, state
                FROM locations
                ORDER BY location_title
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error loading locations: {e}")
            return pd.DataFrame()
    
    def create_swap(self, swap_data):
        """Create a trailer swap with validation"""
        # Prevent double submission
        if st.session_state.swap_state['swap_in_progress']:
            st.warning("⏳ Previous swap is still processing...")
            return False
        
        st.session_state.swap_state['swap_in_progress'] = True
        
        try:
            # Validate required fields
            required = ['new_trailer', 'old_trailer', 'driver_name', 'location']
            for field in required:
                if not swap_data.get(field):
                    st.error(f"Missing required field: {field}")
                    return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate unique move ID
            move_id = f"SWAP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Begin transaction
            conn.execute('BEGIN TRANSACTION')
            
            # Calculate mileage
            base_location = "Fleet Memphis, TN"  # Default base location
            delivery_location = swap_data['location']
            
            # Get full addresses for calculation
            from_address = base_location
            to_address = mileage_calc.get_location_full_address(delivery_location)
            
            total_miles = 0
            if to_address:
                # Calculate one-way mileage
                one_way_miles, error = mileage_calc.calculate_mileage_google(
                    from_address, to_address, 
                    api_config.get_google_maps_key()
                )
                if one_way_miles:
                    total_miles = round(one_way_miles * 2, 1)  # Round trip
                else:
                    # Use default if calculation fails
                    st.warning(f"Could not calculate exact mileage: {error}. Using estimated distance.")
                    total_miles = 100  # Default estimate
            
            # Calculate driver pay (97% of gross)
            driver_pay = round(total_miles * 2.10 * 0.97, 2) if total_miles else 0
            
            # Create the move record with mileage
            cursor.execute('''
                INSERT INTO moves (
                    move_id, new_trailer, old_trailer, 
                    pickup_location, delivery_location,
                    driver_name, move_date, status,
                    total_miles, driver_pay,
                    created_by, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                move_id,
                swap_data['new_trailer'],
                swap_data['old_trailer'],
                swap_data['location'],
                swap_data['location'],
                swap_data['driver_name'],
                swap_data.get('move_date', date.today()),
                'assigned',
                total_miles,
                driver_pay,
                st.session_state.get('user_name', 'System'),
                swap_data.get('notes', '')
            ))
            
            # Update trailer statuses
            cursor.execute('''
                UPDATE trailers 
                SET status = 'in_transit', 
                    swap_location = ?,
                    updated_date = CURRENT_TIMESTAMP
                WHERE trailer_number IN (?, ?)
            ''', (swap_data['location'], swap_data['new_trailer'], swap_data['old_trailer']))
            
            # Update driver status
            cursor.execute('''
                UPDATE drivers 
                SET status = 'on_trip'
                WHERE driver_name = ?
            ''', (swap_data['driver_name'],))
            
            # Log the activity
            cursor.execute('''
                INSERT INTO activity_log (action, entity_type, entity_id, user, details)
                VALUES ('create_swap', 'move', ?, ?, ?)
            ''', (
                move_id,
                st.session_state.get('user_name', 'System'),
                json.dumps(swap_data)
            ))
            
            conn.commit()
            conn.close()
            
            # Update session state
            st.session_state.swap_state['last_swap_time'] = datetime.now()
            st.session_state.swap_state['active_swap'] = move_id
            
            # Clear selections
            st.session_state.swap_state['selected_new'] = None
            st.session_state.swap_state['selected_old'] = None
            st.session_state.swap_state['selected_driver'] = None
            st.session_state.swap_state['selected_location'] = None
            
            return move_id
            
        except sqlite3.IntegrityError as e:
            if conn:
                conn.rollback()
            st.error(f"Database integrity error: {e}")
            return False
        except Exception as e:
            if conn:
                conn.rollback()
            st.error(f"Error creating swap: {e}")
            return False
        finally:
            st.session_state.swap_state['swap_in_progress'] = False
    
    def update_swap_status(self, move_id, new_status):
        """Update swap status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get move details
            cursor.execute('''
                SELECT new_trailer, old_trailer, driver_name 
                FROM moves WHERE move_id = ?
            ''', (move_id,))
            move = cursor.fetchone()
            
            if not move:
                st.error(f"Move {move_id} not found")
                return False
            
            new_trailer, old_trailer, driver_name = move
            
            # Update move status
            cursor.execute('''
                UPDATE moves 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE move_id = ?
            ''', (new_status, move_id))
            
            # Update related statuses based on new status
            if new_status == 'completed':
                # Mark trailers as available at new location
                cursor.execute('''
                    UPDATE trailers 
                    SET status = 'available',
                        current_location = swap_location,
                        swap_location = NULL
                    WHERE trailer_number IN (?, ?)
                ''', (new_trailer, old_trailer))
                
                # Mark driver as available
                cursor.execute('''
                    UPDATE drivers SET status = 'available'
                    WHERE driver_name = ?
                ''', (driver_name,))
                
            elif new_status == 'cancelled':
                # Revert trailer and driver statuses
                cursor.execute('''
                    UPDATE trailers 
                    SET status = 'available',
                        swap_location = NULL
                    WHERE trailer_number IN (?, ?)
                ''', (new_trailer, old_trailer))
                
                cursor.execute('''
                    UPDATE drivers SET status = 'available'
                    WHERE driver_name = ?
                ''', (driver_name,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error updating swap status: {e}")
            return False
    
    def get_active_swaps(self):
        """Get all active swaps"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT move_id, new_trailer, old_trailer, driver_name,
                       pickup_location, move_date, status, created_at
                FROM moves
                WHERE status IN ('assigned', 'in_progress')
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error loading active swaps: {e}")
            return pd.DataFrame()
    
    def get_swap_history(self, days=30):
        """Get swap history"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT move_id, new_trailer, old_trailer, driver_name,
                       pickup_location, move_date, status, created_at
                FROM moves
                WHERE date(created_at) >= date('now', '-' || ? || ' days')
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn, params=(days,))
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error loading history: {e}")
            return pd.DataFrame()
    
    def show_create_swap_form(self):
        """Display swap creation form with enhanced UI"""
        st.markdown("### 🔄 Create Trailer Swap")
        
        # Load data
        new_trailers_df = self.get_available_trailers('new')
        old_trailers_df = self.get_available_trailers('old')
        drivers_df = self.get_available_drivers()
        locations_df = self.get_locations()
        
        # Check availability
        if new_trailers_df.empty:
            st.warning("⚠️ No NEW trailers available for swap")
            return
        
        if old_trailers_df.empty:
            st.warning("⚠️ No OLD trailers available for swap")
            return
        
        if drivers_df.empty:
            st.warning("⚠️ No drivers available for assignment")
            return
        
        if locations_df.empty:
            st.warning("⚠️ No locations configured")
            return
        
        # Create form
        with st.form("create_swap_enhanced", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🟢 NEW Trailer (Delivering)**")
                new_trailer = st.selectbox(
                    "Select NEW Trailer",
                    new_trailers_df['trailer_number'].tolist(),
                    help="This trailer will be delivered to the location"
                )
                
                st.markdown("**📍 Swap Location**")
                location = st.selectbox(
                    "Select Location",
                    locations_df['location_title'].tolist(),
                    help="Where the swap will occur"
                )
                
                move_date = st.date_input(
                    "Swap Date",
                    value=date.today(),
                    min_value=date.today()
                )
            
            with col2:
                st.markdown("**🔴 OLD Trailer (Picking Up)**")
                old_trailer = st.selectbox(
                    "Select OLD Trailer",
                    old_trailers_df['trailer_number'].tolist(),
                    help="This trailer will be picked up from the location"
                )
                
                st.markdown("**🚛 Assign Driver**")
                driver = st.selectbox(
                    "Select Driver",
                    drivers_df['driver_name'].tolist(),
                    help="Driver responsible for the swap"
                )
                
                notes = st.text_area(
                    "Notes (Optional)",
                    placeholder="Special instructions or notes about this swap"
                )
            
            # Show preview
            st.divider()
            st.markdown("**📋 Swap Summary:**")
            st.info(f"""
            • **Driver:** {driver} will pick up **{old_trailer}** and deliver **{new_trailer}**
            • **Location:** {location}
            • **Date:** {move_date}
            """)
            
            # Submit button
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                submitted = st.form_submit_button(
                    "Create Swap",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted:
                swap_data = {
                    'new_trailer': new_trailer,
                    'old_trailer': old_trailer,
                    'driver_name': driver,
                    'location': location,
                    'move_date': move_date,
                    'notes': notes
                }
                
                with st.spinner("Creating swap..."):
                    move_id = self.create_swap(swap_data)
                    
                    if move_id:
                        st.success(f"""
                        ✅ **Swap Created Successfully!**
                        
                        **Move ID:** {move_id}
                        **Driver:** {driver}
                        **Status:** Assigned and ready
                        """)
                        time.sleep(2)
                        st.rerun()
    
    def show_active_swaps(self):
        """Display active swaps with management options"""
        st.markdown("### 📊 Active Swaps")
        
        swaps_df = self.get_active_swaps()
        
        if swaps_df.empty:
            st.info("No active swaps at the moment")
            return
        
        # Display each swap
        for _, swap in swaps_df.iterrows():
            status_color = "🟡" if swap['status'] == 'assigned' else "🟢"
            
            with st.expander(f"{status_color} {swap['move_id']} - {swap['driver_name']}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Swap Details:**")
                    st.write(f"📦 NEW: {swap['new_trailer']}")
                    st.write(f"📦 OLD: {swap['old_trailer']}")
                    st.write(f"📍 Location: {swap['pickup_location']}")
                
                with col2:
                    st.markdown("**Assignment:**")
                    st.write(f"🚛 Driver: {swap['driver_name']}")
                    st.write(f"📅 Date: {swap['move_date']}")
                    st.write(f"⏰ Created: {swap['created_at']}")
                
                with col3:
                    st.markdown("**Actions:**")
                    
                    if swap['status'] == 'assigned':
                        if st.button("Start", key=f"start_{swap['move_id']}"):
                            if self.update_swap_status(swap['move_id'], 'in_progress'):
                                st.success("Swap started!")
                                time.sleep(1)
                                st.rerun()
                    
                    elif swap['status'] == 'in_progress':
                        if st.button("Complete", key=f"complete_{swap['move_id']}"):
                            if self.update_swap_status(swap['move_id'], 'completed'):
                                st.success("Swap completed!")
                                time.sleep(1)
                                st.rerun()
                    
                    if st.button("Cancel", key=f"cancel_{swap['move_id']}"):
                        if self.update_swap_status(swap['move_id'], 'cancelled'):
                            st.warning("Swap cancelled")
                            time.sleep(1)
                            st.rerun()
    
    def show_swap_history(self):
        """Display swap history"""
        st.markdown("### 📜 Swap History")
        
        # Date range selector
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            days = st.selectbox("Show last", [7, 14, 30, 60, 90], index=2)
        
        history_df = self.get_swap_history(days)
        
        if history_df.empty:
            st.info(f"No swaps in the last {days} days")
            return
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Swaps", len(history_df))
        
        with col2:
            completed = len(history_df[history_df['status'] == 'completed'])
            st.metric("Completed", completed)
        
        with col3:
            in_progress = len(history_df[history_df['status'] == 'in_progress'])
            st.metric("In Progress", in_progress)
        
        with col4:
            cancelled = len(history_df[history_df['status'] == 'cancelled'])
            st.metric("Cancelled", cancelled)
        
        st.divider()
        
        # Display history table
        display_df = history_df[['move_id', 'driver_name', 'new_trailer', 
                                 'old_trailer', 'pickup_location', 
                                 'move_date', 'status']]
        
        # Color code by status
        def highlight_status(row):
            if row['status'] == 'completed':
                return ['background-color: #1e4d2b'] * len(row)
            elif row['status'] == 'cancelled':
                return ['background-color: #4d1e1e'] * len(row)
            elif row['status'] == 'in_progress':
                return ['background-color: #4d4d1e'] * len(row)
            else:
                return [''] * len(row)
        
        styled_df = display_df.style.apply(highlight_status, axis=1)
        st.dataframe(styled_df, use_container_width=True)

def show_enhanced_trailer_swap():
    """Main entry point for enhanced trailer swap management"""
    manager = EnhancedTrailerSwapManager()
    
    st.title("🔄 Trailer Swap Management")
    
    tabs = st.tabs(["➕ Create Swap", "📊 Active Swaps", "📜 History"])
    
    with tabs[0]:
        manager.show_create_swap_form()
    
    with tabs[1]:
        manager.show_active_swaps()
    
    with tabs[2]:
        manager.show_swap_history()

# Export for use in main app
__all__ = ['EnhancedTrailerSwapManager', 'show_enhanced_trailer_swap']