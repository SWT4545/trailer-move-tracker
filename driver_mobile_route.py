"""
Mobile-Optimized Driver Route Interface
Smith and Williams Trucking
Designed for smartphone use during deliveries
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import database as db
import hashlib
import base64
import io
from PIL import Image
import time

def show_driver_route(route_id):
    """Mobile-optimized route interface for drivers"""
    
    # Mobile-specific page config
    st.set_page_config(
        page_title=f"Route #{route_id}",
        page_icon="🚛",
        layout="centered",  # Better for mobile
        initial_sidebar_state="collapsed"
    )
    
    # Apply mobile CSS
    st.markdown("""
    <style>
    /* Mobile-specific styling */
    .stApp {
        max-width: 100%;
        padding: 0;
        margin: 0;
    }
    
    /* Large touch-friendly buttons */
    .stButton > button {
        width: 100%;
        min-height: 60px;
        font-size: 18px !important;
        font-weight: bold;
        margin: 10px 0;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Success button (green) */
    .success-button > button {
        background-color: #28a745 !important;
        color: white !important;
    }
    
    /* Warning button (yellow) */
    .warning-button > button {
        background-color: #ffc107 !important;
        color: black !important;
    }
    
    /* Danger button (red) */
    .danger-button > button {
        background-color: #dc3545 !important;
        color: white !important;
    }
    
    /* Info panels */
    .route-info {
        background: #f8f9fa;
        border: 2px solid #DC143C;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Progress indicator */
    .progress-step {
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
        font-size: 16px;
    }
    
    .step-active {
        background: #e7f3ff;
        border: 2px solid #17a2b8;
    }
    
    .step-completed {
        background: #d4edda;
        border: 2px solid #28a745;
    }
    
    .step-pending {
        background: #f8f9fa;
        border: 2px solid #6c757d;
    }
    
    /* Photo upload area */
    .photo-upload {
        border: 3px dashed #DC143C;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background: #fff;
        margin: 10px 0;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ensure inputs don't zoom on iOS */
    input, select, textarea {
        font-size: 16px !important;
    }
    
    /* Large text for readability */
    h1 { font-size: 24px !important; }
    h2 { font-size: 20px !important; }
    h3 { font-size: 18px !important; }
    p { font-size: 16px !important; }
    </style>
    """, unsafe_allow_html=True)
    
    # Get route details
    route = db.get_move_by_id(route_id)
    if not route:
        st.error("❌ Route not found!")
        return
    
    # Initialize session state for route progress
    if f'route_{route_id}_progress' not in st.session_state:
        st.session_state[f'route_{route_id}_progress'] = {
            'current_step': 'pickup_arrival',
            'pickup_arrival': False,
            'pickup_photos': [],
            'pickup_depart': False,
            'delivery_arrival': False,
            'delivery_photos': [],
            'delivery_complete': False,
            'old_pickup': False,
            'old_photo': None,
            'fleet_return': False,
            'fleet_photo': None,
            'route_complete': False
        }
    
    progress = st.session_state[f'route_{route_id}_progress']
    
    # Header with route info
    st.markdown(f"""
    <div class="route-info">
        <h2 style="margin: 0; color: #DC143C;">Route #{route_id}</h2>
        <p style="margin: 5px 0;"><strong>Driver:</strong> {route['assigned_driver']}</p>
        <p style="margin: 5px 0;"><strong>Miles:</strong> {route['miles']:,.0f}</p>
        <p style="margin: 5px 0;"><strong>Pay:</strong> ${route['load_pay']:.2f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress indicator
    steps = [
        ('pickup_arrival', '📍 Pickup', progress['pickup_arrival']),
        ('delivery_arrival', '📦 Delivery', progress['delivery_complete']),
        ('fleet_return', '🏢 Return', progress['route_complete'])
    ]
    
    cols = st.columns(3)
    for idx, (step_key, step_name, is_complete) in enumerate(steps):
        with cols[idx]:
            if is_complete:
                st.success(f"✅ {step_name}")
            elif progress['current_step'] == step_key:
                st.info(f"▶️ {step_name}")
            else:
                st.text(f"⏳ {step_name}")
    
    st.divider()
    
    # Current step interface
    current_step = progress['current_step']
    
    if current_step == 'pickup_arrival':
        show_pickup_arrival(route, progress, route_id)
    elif current_step == 'pickup_photos':
        show_pickup_photos(route, progress, route_id)
    elif current_step == 'pickup_depart':
        show_pickup_depart(route, progress, route_id)
    elif current_step == 'delivery_arrival':
        show_delivery_arrival(route, progress, route_id)
    elif current_step == 'delivery_photos':
        show_delivery_photos(route, progress, route_id)
    elif current_step == 'delivery_complete':
        show_delivery_complete(route, progress, route_id)
    elif current_step == 'old_pickup':
        show_old_pickup(route, progress, route_id)
    elif current_step == 'fleet_return':
        show_fleet_return(route, progress, route_id)
    elif current_step == 'complete':
        show_route_complete(route, progress, route_id)

def show_pickup_arrival(route, progress, route_id):
    """Pickup arrival step"""
    st.markdown("## 📍 PICKUP - Arrival")
    
    st.markdown(f"""
    <div class="route-info">
        <h3>Pickup Location</h3>
        <p style="font-size: 18px; font-weight: bold;">{route['pickup_location']}</p>
        <p>New Trailer: <strong>{route['new_trailer']}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.warning("⚠️ Confirm you have arrived at the pickup location")
    
    if st.button("✅ ARRIVED AT PICKUP", use_container_width=True):
        progress['pickup_arrival'] = True
        progress['current_step'] = 'pickup_photos'
        db.add_route_progress(route_id, 'pickup_arrival', route['pickup_location'])
        st.success("✅ Arrival confirmed!")
        time.sleep(1)
        st.rerun()
    
    # Emergency options
    with st.expander("⚠️ Issues?"):
        if st.button("Wrong Location", use_container_width=True):
            st.error("Contact dispatch immediately: (555) 123-4567")
        if st.button("Trailer Not Here", use_container_width=True):
            st.error("Contact dispatch immediately: (555) 123-4567")

def show_pickup_photos(route, progress, route_id):
    """Pickup photo documentation"""
    st.markdown("## 📸 PICKUP - Photos Required")
    
    st.info(f"📷 Take 5 photos of trailer {route['new_trailer']}")
    
    photo_types = [
        ('Front of trailer', 'new_trailer_front'),
        ('Back of trailer', 'new_trailer_back'),
        ('Left side', 'new_trailer_left'),
        ('Right side', 'new_trailer_right'),
        ('Inside trailer', 'new_trailer_inside')
    ]
    
    # Photo counter
    photos_taken = len(progress['pickup_photos'])
    st.progress(photos_taken / 5)
    st.markdown(f"**Photos: {photos_taken}/5**")
    
    # Camera input for current photo
    if photos_taken < 5:
        current_photo_name, current_photo_type = photo_types[photos_taken]
        st.markdown(f"### 📷 Take Photo: {current_photo_name}")
        
        # Use camera input
        photo = st.camera_input(f"Photo {photos_taken + 1}: {current_photo_name}")
        
        if photo:
            # Save photo
            progress['pickup_photos'].append({
                'type': current_photo_type,
                'data': photo.getvalue(),
                'timestamp': datetime.now()
            })
            
            # Save to database
            db.save_route_photo(route_id, current_photo_type, photo.getvalue(), route['pickup_location'])
            
            st.success(f"✅ Photo {photos_taken + 1} saved!")
            time.sleep(1)
            st.rerun()
    
    # Continue button when all photos taken
    if photos_taken == 5:
        st.success("✅ All pickup photos complete!")
        
        # Show thumbnails
        cols = st.columns(5)
        for idx, photo in enumerate(progress['pickup_photos']):
            with cols[idx]:
                st.image(photo['data'], width=60)
        
        if st.button("➡️ CONTINUE TO DEPARTURE", use_container_width=True):
            progress['current_step'] = 'pickup_depart'
            st.rerun()

def show_pickup_depart(route, progress, route_id):
    """Pickup departure"""
    st.markdown("## 🚛 PICKUP - Departure")
    
    st.success("✅ Trailer hooked and ready!")
    
    # Checklist
    st.markdown("### Pre-Departure Checklist")
    checks = [
        st.checkbox("Trailer properly connected", key="check1"),
        st.checkbox("Lights tested", key="check2"),
        st.checkbox("Paperwork collected (if any)", key="check3"),
        st.checkbox("No damage to trailer", key="check4")
    ]
    
    all_checked = all(checks)
    
    if all_checked:
        if st.button("🚛 DEPART PICKUP", use_container_width=True):
            progress['pickup_depart'] = True
            progress['current_step'] = 'delivery_arrival'
            db.add_route_progress(route_id, 'pickup_depart', route['pickup_location'])
            st.success("✅ Departed from pickup!")
            time.sleep(1)
            st.rerun()
    else:
        st.warning("⚠️ Complete all checks before departing")

def show_delivery_arrival(route, progress, route_id):
    """Delivery arrival"""
    st.markdown("## 📦 DELIVERY - Arrival")
    
    st.markdown(f"""
    <div class="route-info">
        <h3>Delivery Location</h3>
        <p style="font-size: 18px; font-weight: bold;">{route['destination']}</p>
        <p>Delivering: <strong>{route['new_trailer']}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.warning("⚠️ Confirm arrival at delivery location")
    
    if st.button("✅ ARRIVED AT DELIVERY", use_container_width=True):
        progress['delivery_arrival'] = True
        progress['current_step'] = 'delivery_photos'
        db.add_route_progress(route_id, 'delivery_arrival', route['destination'])
        st.success("✅ Arrival confirmed!")
        time.sleep(1)
        st.rerun()

def show_delivery_photos(route, progress, route_id):
    """Delivery photo documentation"""
    st.markdown("## 📸 DELIVERY - Photos Required")
    
    st.info(f"📷 Take 5 photos at delivery location")
    
    photo_types = [
        ('Front at delivery', 'new_delivery_front'),
        ('Back at delivery', 'new_delivery_back'),
        ('Left at delivery', 'new_delivery_left'),
        ('Right at delivery', 'new_delivery_right'),
        ('Inside (empty/left)', 'new_delivery_inside')
    ]
    
    photos_taken = len(progress['delivery_photos'])
    st.progress(photos_taken / 5)
    st.markdown(f"**Photos: {photos_taken}/5**")
    
    if photos_taken < 5:
        current_photo_name, current_photo_type = photo_types[photos_taken]
        st.markdown(f"### 📷 Take Photo: {current_photo_name}")
        
        photo = st.camera_input(f"Photo {photos_taken + 1}: {current_photo_name}")
        
        if photo:
            progress['delivery_photos'].append({
                'type': current_photo_type,
                'data': photo.getvalue(),
                'timestamp': datetime.now()
            })
            
            db.save_route_photo(route_id, current_photo_type, photo.getvalue(), route['destination'])
            
            st.success(f"✅ Photo {photos_taken + 1} saved!")
            time.sleep(1)
            st.rerun()
    
    if photos_taken == 5:
        st.success("✅ All delivery photos complete!")
        
        if st.button("➡️ CONTINUE", use_container_width=True):
            progress['current_step'] = 'delivery_complete'
            st.rerun()

def show_delivery_complete(route, progress, route_id):
    """Complete delivery and pick up old trailer"""
    st.markdown("## 🔄 Pick Up Old Trailer")
    
    if route['old_trailer']:
        st.markdown(f"""
        <div class="route-info">
            <h3>Old Trailer to Pick Up</h3>
            <p style="font-size: 18px; font-weight: bold;">{route['old_trailer']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📸 PHOTOGRAPH OLD TRAILER", use_container_width=True):
            progress['current_step'] = 'old_pickup'
            st.rerun()
    else:
        st.info("No old trailer to pick up at this location")
        if st.button("➡️ RETURN TO FLEET", use_container_width=True):
            progress['current_step'] = 'fleet_return'
            st.rerun()

def show_old_pickup(route, progress, route_id):
    """Old trailer pickup documentation"""
    st.markdown("## 📸 Old Trailer Pickup")
    
    st.info(f"Take 1 photo of old trailer {route['old_trailer']}")
    
    photo = st.camera_input("Old trailer photo")
    
    if photo:
        progress['old_photo'] = photo.getvalue()
        db.save_route_photo(route_id, 'old_trailer_pickup', photo.getvalue(), route['destination'])
        st.success("✅ Old trailer documented!")
        
        if st.button("🚛 RETURN TO FLEET", use_container_width=True):
            progress['old_pickup'] = True
            progress['current_step'] = 'fleet_return'
            db.add_route_progress(route_id, 'old_pickup', route['destination'])
            st.rerun()

def show_fleet_return(route, progress, route_id):
    """Fleet return confirmation"""
    st.markdown("## 🏢 RETURN TO FLEET")
    
    st.markdown(f"""
    <div class="route-info">
        <h3>Return Location</h3>
        <p style="font-size: 18px; font-weight: bold;">Fleet Memphis</p>
        <p>Returning: <strong>{route['old_trailer'] if route['old_trailer'] else 'No trailer'}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.warning("⚠️ Confirm arrival at Fleet Memphis")
    
    if st.button("✅ ARRIVED AT FLEET", use_container_width=True):
        st.success("✅ Take final photo for POD")
        
        photo = st.camera_input("Fleet return photo (serves as POD)")
        
        if photo:
            progress['fleet_photo'] = photo.getvalue()
            db.save_route_photo(route_id, 'pod_fleet', photo.getvalue(), 'Fleet Memphis')
            
            if st.button("✅ COMPLETE ROUTE", use_container_width=True):
                progress['fleet_return'] = True
                progress['route_complete'] = True
                progress['current_step'] = 'complete'
                
                # Update route in database
                db.update_move(route_id, {
                    'completion_date': datetime.now(),
                    'photos_captured': 12
                })
                db.add_route_progress(route_id, 'completed', 'Fleet Memphis')
                
                st.rerun()

def show_route_complete(route, progress, route_id):
    """Route completion screen"""
    st.balloons()
    
    st.markdown("""
    <div style="background: #d4edda; border: 3px solid #28a745; border-radius: 15px; padding: 20px; text-align: center;">
        <h1 style="color: #28a745; margin: 0;">✅ ROUTE COMPLETE!</h1>
        <p style="font-size: 20px; margin: 10px 0;">Great job!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Earnings summary
    st.markdown(f"""
    <div class="route-info" style="text-align: center;">
        <h2 style="margin: 10px 0;">You Earned</h2>
        <p style="font-size: 36px; font-weight: bold; color: #28a745; margin: 10px 0;">
            ${route['load_pay']:.2f}
        </p>
        <p style="font-size: 18px;">For {route['miles']:,.0f} miles</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary of work
    st.markdown("### 📋 Route Summary")
    st.success(f"✅ Delivered: {route['new_trailer']}")
    if route['old_trailer']:
        st.success(f"✅ Returned: {route['old_trailer']}")
    st.success(f"✅ Total Photos: 12")
    st.success(f"✅ Completed: {datetime.now().strftime('%I:%M %p')}")
    
    # Close button
    if st.button("🏠 RETURN TO DASHBOARD", use_container_width=True):
        st.info("Thank you for your hard work! Drive safely!")

# Direct link handler
def handle_driver_link(route_id):
    """Handle direct driver link access"""
    show_driver_route(route_id)

if __name__ == "__main__":
    # Check if route_id in query params
    import sys
    if len(sys.argv) > 1:
        route_id = int(sys.argv[1])
        handle_driver_link(route_id)
    else:
        st.error("No route specified. Please use the link provided in your SMS.")