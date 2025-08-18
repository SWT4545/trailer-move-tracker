# -*- coding: utf-8 -*-
"""
Enhanced Logo Handler with Animation Support
"""

import streamlit as st
import os
import base64
import time

def show_login_page_with_logo():
    """Show login page with logo animation"""
    
    # Check for video animation
    animation_file = "company_logo_animation.mp4.MOV"
    white_logo = "swt_logo_white.png"
    
    # CSS for centering
    st.markdown("""
        <style>
        .logo-container {
            text-align: center;
            padding: 2rem;
        }
        video {
            max-width: 400px;
            margin: 0 auto;
            display: block;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Display animation or logo
    if os.path.exists(animation_file):
        # Show video animation
        video_file = open(animation_file, 'rb')
        video_bytes = video_file.read()
        st.video(video_bytes)
        video_file.close()
        
        # Brief pause
        time.sleep(1)
    
    # Show static logo
    if os.path.exists(white_logo):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(white_logo, use_container_width=True)
    else:
        st.markdown("""
            <div class="logo-container">
                <h1>Smith & Williams Trucking</h1>
                <p>Fleet Management System</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Vernon IT Support indicator
    with st.sidebar:
        st.markdown("---")
        st.markdown("**[Vernon IT]** Support Available")
        st.markdown("*Your IT Assistant*")

def initialize_with_animation():
    """Initialize app with animation"""
    
    if 'animation_shown' not in st.session_state:
        st.session_state.animation_shown = False
    
    if not st.session_state.animation_shown:
        # Show animation on first load
        show_login_page_with_logo()
        st.session_state.animation_shown = True
        return False
    
    return True
