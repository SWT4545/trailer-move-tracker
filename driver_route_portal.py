"""
Driver Route Portal
Mobile-friendly interface for drivers to view routes and upload photos
Accessible via generated links
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import database as db
import json
import base64
import hashlib
from PIL import Image
import io

# Mobile-friendly CSS
MOBILE_CSS = """
<style>
    /* Mobile optimized styles */
    .stApp {
        max-width: 100%;
        padding: 0.5rem;
    }
    
    .main-header {
        background: linear-gradient(135deg, #DC143C 0%, #8B0000 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .route-card {
        background: white;
        border: 2px solid #DC143C;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .photo-section {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.875rem;
    }
    
    .status-pending {
        background: #ffc107;
        color: #000;
    }
    
    .status-complete {
        background: #28a745;
        color: white;
    }
    
    .photo-counter {
        background: #DC143C;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    
    /* Mobile-friendly buttons */
    .stButton > button {
        width: 100%;
        padding: 1rem;
        font-size: 1.1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    /* Make file uploader more prominent */
    .uploadedFile {
        border: 2px dashed #DC143C;
        border-radius: 10px;
        padding: 1rem;
    }
    
    @media (max-width: 768px) {
        .stApp {
            padding: 0.25rem;
        }
        
        h1 {
            font-size: 1.5rem;
        }
        
        h2 {
            font-size: 1.25rem;
        }
        
        h3 {
            font-size: 1.1rem;
        }
    }
</style>
"""

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
            return None, "This link has expired. Please request a new one from dispatch."
        
        # Verify hash
        hash_input = f"{token_data['move_id']}{token_data['driver']}{token_data['created']}"
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        
        if token_hash != expected_hash:
            return None, "Invalid link. Please check with dispatch."
        
        return token_data, None
    except Exception as e:
        return None, "Invalid link format. Please check with dispatch."

def get_move_details(move_id):
    """Get move details from database"""
    conn = db.get_connection()
    query = """
        SELECT tm.*, 
               l1.address as new_pickup_address,
               l2.address as new_destination_address,
               l3.address as old_pickup_address,
               l4.address as old_destination_address
        FROM trailer_moves tm
        LEFT JOIN locations l1 ON tm.new_pickup_location = l1.location_title
        LEFT JOIN locations l2 ON tm.new_destination = l2.location_title
        LEFT JOIN locations l3 ON tm.old_pickup_location = l3.location_title
        LEFT JOIN locations l4 ON tm.old_destination = l4.location_title
        WHERE tm.id = ?
    """
    
    move_df = pd.read_sql_query(query, conn, params=(move_id,))
    conn.close()
    
    if move_df.empty:
        return None
    
    return move_df.iloc[0].to_dict()

def save_driver_photos(move_id, photo_type, photos):
    """Save uploaded photos to database"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Create photos table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS driver_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            move_id INTEGER,
            photo_type TEXT,
            photo_data BLOB,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            driver_name TEXT,
            FOREIGN KEY (move_id) REFERENCES trailer_moves (id)
        )
    """)
    
    saved_count = 0
    for photo in photos:
        # Convert photo to bytes
        img = Image.open(photo)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr = img_byte_arr.getvalue()
        
        cursor.execute("""
            INSERT INTO driver_photos (move_id, photo_type, photo_data, driver_name)
            VALUES (?, ?, ?, ?)
        """, (move_id, photo_type, img_byte_arr, st.session_state.get('driver_name', '')))
        saved_count += 1
    
    conn.commit()
    conn.close()
    
    return saved_count

def get_photo_count(move_id):
    """Get count of photos uploaded for this move"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN photo_type = 'new_pickup' THEN 1 END) as new_pickup_count,
            COUNT(CASE WHEN photo_type = 'new_delivery' THEN 1 END) as new_delivery_count,
            COUNT(CASE WHEN photo_type = 'old_pickup' THEN 1 END) as old_pickup_count,
            COUNT(CASE WHEN photo_type = 'old_return' THEN 1 END) as old_return_count
        FROM driver_photos
        WHERE move_id = ?
    """, (move_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return {
        'new_pickup': result[0] if result else 0,
        'new_delivery': result[1] if result else 0,
        'old_pickup': result[2] if result else 0,
        'old_return': result[3] if result else 0
    }

def update_move_status(move_id, status_type):
    """Update move status in database"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    if status_type == 'accepted':
        cursor.execute("""
            UPDATE trailer_moves 
            SET status = 'In Progress',
                last_updated = datetime('now')
            WHERE id = ?
        """, (move_id,))
    elif status_type == 'completed':
        cursor.execute("""
            UPDATE trailer_moves 
            SET status = 'Completed',
                completion_date = date('now'),
                last_updated = datetime('now')
            WHERE id = ?
        """, (move_id,))
    
    conn.commit()
    conn.close()

def show_driver_portal():
    """Main driver portal interface"""
    
    # Apply mobile CSS
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
    
    # Check for token in URL
    query_params = st.query_params
    
    if 'token' not in query_params:
        st.markdown("""
        <div class="main-header">
            <h1>🚛 Smith and Williams Trucking</h1>
            <p>Driver Route Portal</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.error("❌ No route link provided. Please use the link sent by dispatch.")
        st.info("📱 If you need a new link, contact dispatch.")
        return
    
    # Decode token
    token = query_params['token']
    token_data, error = decode_route_token(token)
    
    if error:
        st.markdown("""
        <div class="main-header">
            <h1>🚛 Smith and Williams Trucking</h1>
            <p>Driver Route Portal</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.error(f"❌ {error}")
        return
    
    # Get move details
    move_id = token_data['move_id']
    driver_name = token_data['driver']
    move_details = get_move_details(move_id)
    
    if not move_details:
        st.error("❌ Route not found. Please contact dispatch.")
        return
    
    # Store driver name in session
    st.session_state['driver_name'] = driver_name
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>🚛 Route #{move_id}</h1>
        <p>Driver: {driver_name}</p>
        <p>{datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Route Details
    st.markdown("""
    <div class="route-card">
        <h2>📋 Route Information</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # New Trailer Section
    with st.expander("🚛 NEW TRAILER - PICKUP & DELIVERY", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📦 Pickup:**")
            st.write(f"Trailer: **{move_details['new_trailer_number']}**")
            st.write(f"Location: {move_details['new_pickup_location']}")
            if move_details.get('new_pickup_address'):
                st.write(f"Address: {move_details['new_pickup_address']}")
                if st.button("📍 Open in Maps (Pickup)", key="maps_pickup"):
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={move_details['new_pickup_address'].replace(' ', '+')}"
                    st.markdown(f'<a href="{maps_url}" target="_blank">Open Google Maps</a>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("**📍 Delivery:**")
            st.write(f"Destination: {move_details['new_destination']}")
            if move_details.get('new_destination_address'):
                st.write(f"Address: {move_details['new_destination_address']}")
                if st.button("📍 Open in Maps (Delivery)", key="maps_delivery"):
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={move_details['new_destination_address'].replace(' ', '+')}"
                    st.markdown(f'<a href="{maps_url}" target="_blank">Open Google Maps</a>', unsafe_allow_html=True)
    
    # Old Trailer Section (if applicable)
    if move_details.get('old_trailer_number'):
        with st.expander("🔄 OLD TRAILER - PICKUP", expanded=True):
            st.write(f"Trailer: **{move_details['old_trailer_number']}**")
            st.write(f"Location: {move_details['old_pickup_location']}")
            if move_details.get('old_pickup_address'):
                st.write(f"Address: {move_details['old_pickup_address']}")
                if st.button("📍 Open in Maps (Old Pickup)", key="maps_old"):
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={move_details['old_pickup_address'].replace(' ', '+')}"
                    st.markdown(f'<a href="{maps_url}" target="_blank">Open Google Maps</a>', unsafe_allow_html=True)
    
    # Trip Information
    with st.expander("📏 Trip Details", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("One Way", f"{move_details.get('miles', 'TBD')} miles")
        with col2:
            st.metric("Round Trip", f"{move_details.get('round_trip_miles', 'TBD')} miles")
        
        if move_details.get('special_instructions'):
            st.info(f"📝 Special Instructions: {move_details['special_instructions']}")
    
    st.divider()
    
    # Photo Upload Section
    st.markdown("""
    <div class="photo-section">
        <h2>📸 Photo Documentation</h2>
        <p><strong>Required: 12 photos total</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get current photo counts
    photo_counts = get_photo_count(move_id)
    total_photos = sum(photo_counts.values())
    
    # Photo counter
    st.markdown(f"""
    <div class="photo-counter">
        📸 {total_photos} / 12 Photos Uploaded
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    progress = min(total_photos / 12, 1.0)
    st.progress(progress)
    
    # Photo upload sections
    tab1, tab2, tab3, tab4 = st.tabs([
        f"New Pickup ({photo_counts['new_pickup']}/5)",
        f"New Delivery ({photo_counts['new_delivery']}/5)",
        f"Old Pickup ({photo_counts['old_pickup']}/1)",
        f"Old Return ({photo_counts['old_return']}/1)"
    ])
    
    with tab1:
        st.markdown("### 📦 New Trailer Pickup Photos")
        st.info("""
        Required (5 photos):
        1. Front view
        2. Driver side
        3. Passenger side
        4. Rear view
        5. VIN/ID plate
        """)
        
        new_pickup_photos = st.file_uploader(
            "Upload New Pickup Photos",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            key="new_pickup",
            help="Select all 5 photos at once"
        )
        
        if new_pickup_photos:
            if st.button("💾 Save New Pickup Photos", key="save_new_pickup"):
                count = save_driver_photos(move_id, 'new_pickup', new_pickup_photos)
                st.success(f"✅ Saved {count} photos")
                st.rerun()
    
    with tab2:
        st.markdown("### 📍 New Trailer Delivery Photos")
        st.info("""
        Required (5 photos):
        1. Delivery location
        2. Trailer positioned
        3. Customer signature
        4. Completed paperwork
        5. Final placement
        """)
        
        new_delivery_photos = st.file_uploader(
            "Upload New Delivery Photos",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            key="new_delivery",
            help="Select all 5 photos at once"
        )
        
        if new_delivery_photos:
            if st.button("💾 Save New Delivery Photos", key="save_new_delivery"):
                count = save_driver_photos(move_id, 'new_delivery', new_delivery_photos)
                st.success(f"✅ Saved {count} photos")
                st.rerun()
    
    with tab3:
        if move_details.get('old_trailer_number'):
            st.markdown("### 🔄 Old Trailer Pickup Photo")
            st.info("Required: 1 photo showing loaded trailer at pickup")
            
            old_pickup_photos = st.file_uploader(
                "Upload Old Pickup Photo",
                type=['jpg', 'jpeg', 'png'],
                accept_multiple_files=True,
                key="old_pickup",
                help="Select 1 photo"
            )
            
            if old_pickup_photos:
                if st.button("💾 Save Old Pickup Photo", key="save_old_pickup"):
                    count = save_driver_photos(move_id, 'old_pickup', old_pickup_photos)
                    st.success(f"✅ Saved {count} photo")
                    st.rerun()
        else:
            st.info("No old trailer for this route")
    
    with tab4:
        if move_details.get('old_trailer_number'):
            st.markdown("### 🏭 Old Trailer Return Photo")
            st.info("Required: 1 photo showing trailer returned to Fleet")
            
            old_return_photos = st.file_uploader(
                "Upload Old Return Photo",
                type=['jpg', 'jpeg', 'png'],
                accept_multiple_files=True,
                key="old_return",
                help="Select 1 photo"
            )
            
            if old_return_photos:
                if st.button("💾 Save Old Return Photo", key="save_old_return"):
                    count = save_driver_photos(move_id, 'old_return', old_return_photos)
                    st.success(f"✅ Saved {count} photo")
                    st.rerun()
        else:
            st.info("No old trailer for this route")
    
    st.divider()
    
    # Status Updates
    st.markdown("### 📊 Route Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ ACCEPT ROUTE", type="primary", use_container_width=True):
            update_move_status(move_id, 'accepted')
            st.success("Route accepted! Safe travels!")
            # Send notification to dispatch
    
    with col2:
        if total_photos >= 12:
            if st.button("🏁 COMPLETE ROUTE", type="primary", use_container_width=True):
                update_move_status(move_id, 'completed')
                st.success("Route completed! Thank you!")
                st.balloons()
        else:
            st.button(f"📸 Need {12 - total_photos} more photos", disabled=True, use_container_width=True)
    
    # Help section
    with st.expander("❓ Need Help?"):
        st.markdown("""
        **Dispatch Contact:**
        - 📞 Phone: (555) 123-4567
        - 📱 Text: (555) 123-4567
        - 📧 Email: dispatch@smithwilliamstrucking.com
        
        **Common Issues:**
        - Can't find trailer: Call dispatch immediately
        - Photo won't upload: Check file size (max 10MB)
        - Wrong information: Contact dispatch to update
        - App issues: Try refreshing the page
        """)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Driver Portal - Smith and Williams Trucking",
        page_icon="🚛",
        layout="wide",
        initial_sidebar_state="collapsed"  # Hide sidebar for mobile
    )
    
    show_driver_portal()