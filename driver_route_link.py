"""
Driver Route Link Generator
Creates shareable links for drivers with route information
Works without Twilio - copy/paste to SMS manually
"""

import streamlit as st
import hashlib
import json
import base64
from datetime import datetime, timedelta
import database as db
import pandas as pd
from urllib.parse import urlencode

def generate_route_token(move_id, driver_name, expiry_hours=24):
    """Generate a secure token for driver route access"""
    # Create token data
    token_data = {
        'move_id': move_id,
        'driver': driver_name,
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(hours=expiry_hours)).isoformat(),
        'type': 'driver_route'
    }
    
    # Encode token
    token_json = json.dumps(token_data)
    token_bytes = token_json.encode('utf-8')
    token_b64 = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
    
    # Create hash for verification
    hash_input = f"{move_id}{driver_name}{token_data['created']}"
    token_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
    
    return f"{token_b64}.{token_hash}"

def decode_route_token(token):
    """Decode and validate route token"""
    try:
        # Split token and hash
        token_b64, token_hash = token.rsplit('.', 1)
        
        # Decode token
        token_bytes = base64.urlsafe_b64decode(token_b64)
        token_json = token_bytes.decode('utf-8')
        token_data = json.loads(token_json)
        
        # Check expiry
        expires = datetime.fromisoformat(token_data['expires'])
        if datetime.now() > expires:
            return None, "Token expired"
        
        # Verify hash
        hash_input = f"{token_data['move_id']}{token_data['driver']}{token_data['created']}"
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        
        if token_hash != expected_hash:
            return None, "Invalid token"
        
        return token_data, None
    except Exception as e:
        return None, str(e)

def generate_driver_message(move_data, token, base_url="http://localhost:8501"):
    """Generate a copyable message for drivers with route information"""
    
    message = f"""
🚛 ROUTE ASSIGNMENT - {move_data['driver_name']}

📅 Date: {move_data['date_assigned']}
📍 Move ID: #{move_data['id']}

NEW TRAILER PICKUP:
📦 Trailer: {move_data['new_trailer_number']}
📍 Location: {move_data['new_pickup_location']}
📮 Address: {move_data.get('new_pickup_address', 'See route link')}

DELIVERY:
📍 Destination: {move_data['new_destination']}
📮 Address: {move_data.get('new_destination_address', 'See route link')}
"""

    if move_data.get('old_trailer_number'):
        message += f"""
OLD TRAILER PICKUP:
📦 Trailer: {move_data['old_trailer_number']}
📍 Location: {move_data['old_pickup_location']}
📮 Address: {move_data.get('old_pickup_address', 'See route link')}
"""

    message += f"""
📏 Miles: {move_data.get('miles', 'TBD')} (Round trip: {move_data.get('round_trip_miles', 'TBD')})
💰 Rate: ${move_data.get('rate', 2.10)}/mile

📸 REQUIRED: 12 photos total
- 5 new trailer pickup
- 5 new trailer delivery  
- 1 old trailer pickup
- 1 old trailer return

🔗 ROUTE DETAILS & PHOTO UPLOAD:
{base_url}/driver?token={token}

⚠️ This link expires in 24 hours
Reply 'ACCEPTED' to confirm
Call dispatch with any issues
"""
    
    return message

def show_route_generator():
    """Show the route link generator interface"""
    st.markdown("### 📱 Generate Driver Route Links")
    
    st.info("""
    **How it works:**
    1. Select a move to send to driver
    2. System generates a unique secure link
    3. Copy the message and paste into SMS/WhatsApp
    4. Driver clicks link to view route and upload photos
    """)
    
    # Get active moves
    conn = db.get_connection()
    
    # Get moves that need driver assignment or are in progress
    query = """
        SELECT * FROM trailer_moves 
        WHERE paid = 0 
        ORDER BY date_assigned DESC
    """
    
    moves_df = pd.read_sql_query(query, conn)
    
    if moves_df.empty:
        st.warning("No active moves to assign")
        return
    
    # Select move
    col1, col2 = st.columns(2)
    
    with col1:
        # Create display options for moves
        move_options = []
        for _, move in moves_df.iterrows():
            option = f"#{move['id']} - {move['new_trailer_number']} - {move['driver_name']} - {move['new_pickup_location']} to {move['new_destination']}"
            move_options.append(option)
        
        selected_option = st.selectbox(
            "Select Move to Send",
            options=move_options,
            help="Choose the move to generate a link for"
        )
        
        if selected_option:
            move_id = int(selected_option.split('#')[1].split(' ')[0])
            move_data = moves_df[moves_df['id'] == move_id].iloc[0].to_dict()
    
    with col2:
        st.markdown("**Move Details:**")
        if selected_option:
            st.write(f"Driver: {move_data['driver_name']}")
            st.write(f"New Trailer: {move_data['new_trailer_number']}")
            st.write(f"Route: {move_data['new_pickup_location']} → {move_data['new_destination']}")
            if move_data.get('old_trailer_number'):
                st.write(f"Old Trailer: {move_data['old_trailer_number']}")
    
    st.divider()
    
    # Link generation options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        link_type = st.radio(
            "Link Type",
            ["Standard (24 hours)", "Extended (48 hours)", "Weekly (7 days)"],
            help="How long the link should remain active"
        )
        
        expiry_hours = {
            "Standard (24 hours)": 24,
            "Extended (48 hours)": 48,
            "Weekly (7 days)": 168
        }[link_type]
    
    with col2:
        include_maps = st.checkbox("Include Google Maps links", value=True)
        include_instructions = st.checkbox("Include special instructions", value=True)
    
    with col3:
        base_url = st.text_input(
            "Base URL",
            value="http://localhost:8501",
            help="Change this to your server URL when deployed"
        )
    
    # Generate button
    if st.button("🔗 Generate Driver Link", type="primary", use_container_width=True):
        if selected_option:
            # Generate token
            token = generate_route_token(
                move_id=move_data['id'],
                driver_name=move_data['driver_name'],
                expiry_hours=expiry_hours
            )
            
            # Store token in database for validation
            store_driver_token(move_data['id'], move_data['driver_name'], token, expiry_hours)
            
            # Generate message
            message = generate_driver_message(move_data, token, base_url)
            
            # Display copyable message
            st.success("✅ Route link generated successfully!")
            
            st.markdown("### 📋 Copy this message and send to driver:")
            
            # Create a text area with the message
            st.text_area(
                "Message to copy:",
                value=message,
                height=400,
                help="Click to select all, then copy and paste into SMS or messaging app"
            )
            
            # Also show just the link separately
            st.markdown("### 🔗 Or just send the link:")
            link = f"{base_url}/driver?token={token}"
            st.code(link, language=None)
            
            # Show QR code option
            with st.expander("📱 Generate QR Code (Optional)"):
                st.info("Driver can scan this QR code instead of clicking the link")
                # Would need qrcode library for this
                st.write("QR Code generation available with qrcode library")
            
            # Log generation
            st.info(f"""
            **Link Details:**
            - Move ID: #{move_data['id']}
            - Driver: {move_data['driver_name']}
            - Expires: {(datetime.now() + timedelta(hours=expiry_hours)).strftime('%Y-%m-%d %I:%M %p')}
            - Token: {token[:20]}...
            """)

def store_driver_token(move_id, driver_name, token, expiry_hours):
    """Store driver token in database for validation"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Create tokens table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS driver_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id INTEGER,
            driver_name TEXT,
            token TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            used BOOLEAN DEFAULT 0,
            FOREIGN KEY (move_id) REFERENCES trailer_moves (id)
        )
    """)
    
    # Store token
    expires_at = datetime.now() + timedelta(hours=expiry_hours)
    cursor.execute("""
        INSERT INTO driver_tokens (move_id, driver_name, token, expires_at)
        VALUES (?, ?, ?, ?)
    """, (move_id, driver_name, token, expires_at))
    
    conn.commit()
    conn.close()

def validate_driver_token(token):
    """Validate driver token from database"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Check if token exists and is valid
    cursor.execute("""
        SELECT * FROM driver_tokens 
        WHERE token = ? 
        AND expires_at > datetime('now')
        AND used = 0
    """, (token,))
    
    token_data = cursor.fetchone()
    conn.close()
    
    return token_data

def show_bulk_message_generator():
    """Generate messages for multiple drivers at once"""
    st.markdown("### 📤 Bulk Message Generator")
    
    conn = db.get_connection()
    
    # Get today's moves
    query = """
        SELECT * FROM trailer_moves 
        WHERE date_assigned = date('now')
        AND paid = 0
        ORDER BY driver_name
    """
    
    today_moves = pd.read_sql_query(query, conn)
    
    if today_moves.empty:
        st.info("No moves scheduled for today")
        return
    
    st.write(f"Found {len(today_moves)} moves for today")
    
    # Display moves
    st.dataframe(
        today_moves[['id', 'driver_name', 'new_trailer_number', 'new_pickup_location', 'new_destination']],
        use_container_width=True
    )
    
    # Bulk generate
    if st.button("📱 Generate All Messages", type="primary"):
        base_url = st.text_input("Base URL", value="http://localhost:8501")
        
        messages = []
        for _, move in today_moves.iterrows():
            token = generate_route_token(
                move_id=move['id'],
                driver_name=move['driver_name'],
                expiry_hours=24
            )
            store_driver_token(move['id'], move['driver_name'], token, 24)
            
            message = f"""
============================================
TO: {move['driver_name']}
MOVE ID: #{move['id']}
============================================

{generate_driver_message(move.to_dict(), token, base_url)}

============================================
"""
            messages.append(message)
        
        # Display all messages
        st.success(f"Generated {len(messages)} messages")
        
        all_messages = "\n".join(messages)
        st.text_area(
            "All Messages (copy and send individually):",
            value=all_messages,
            height=600
        )

if __name__ == "__main__":
    st.set_page_config(
        page_title="Driver Route Links - Smith and Williams Trucking",
        page_icon="📱",
        layout="wide"
    )
    
    st.title("📱 Driver Communication System")
    
    tab1, tab2 = st.tabs(["Single Route", "Bulk Messages"])
    
    with tab1:
        show_route_generator()
    
    with tab2:
        show_bulk_message_generator()