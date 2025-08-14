# -*- coding: utf-8 -*-
"""
Implement logo animation on login
"""

import os
import base64

def create_login_animation_code():
    """Create the login animation implementation"""
    
    code = '''# Add this to the login page section of app.py

def show_login_animation():
    """Display company logo animation on login"""
    import time
    import base64
    
    # Check for animation file
    animation_file = "company_logo_animation.mp4.MOV"
    
    if os.path.exists(animation_file):
        # Show animation
        with open(animation_file, 'rb') as f:
            video_bytes = f.read()
            video_b64 = base64.b64encode(video_bytes).decode()
            
        st.markdown(
            f"""
            <div style="text-align: center; margin: 2rem auto;">
                <video autoplay muted style="max-width: 400px; border-radius: 10px;">
                    <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                </video>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Wait for animation
        time.sleep(2)
        
        # Show white logo after
        if os.path.exists("swt_logo_white.png"):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image("swt_logo_white.png", use_container_width=True)
    else:
        # Fallback to static white logo
        if os.path.exists("swt_logo_white.png"):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image("swt_logo_white.png", use_container_width=True)
        else:
            st.markdown(
                """
                <div style="text-align: center; padding: 2rem;">
                    <h1>S&W Trucking</h1>
                </div>
                """,
                unsafe_allow_html=True
            )

# Update the login function to include animation
def login_page_with_animation():
    """Enhanced login page with animation"""
    
    # Show animation first
    show_login_animation()
    
    # Then show login form
    st.markdown("### Welcome to Smith & Williams Trucking")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_btn = st.form_submit_button("Login", type="primary")
        with col2:
            # Show Vernon IT support
            st.markdown("[Vernon IT] Need help? Contact support")
        
        if login_btn:
            # Your existing login logic here
            pass
'''
    
    return code

def update_app_with_animation():
    """Update the main app to include animation"""
    
    # Read current app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if animation code is already there
    if 'show_login_animation' in content:
        print("[INFO] Animation code already in app.py")
        return
    
    # Find the login section and prepare update
    animation_import = """
# Import animation handler
try:
    from logo_animation import show_login_animation, show_white_logo
    ANIMATION_AVAILABLE = True
except:
    ANIMATION_AVAILABLE = False
"""
    
    # Create a patch file instead of modifying directly
    with open('app_animation_patch.py', 'w', encoding='utf-8') as f:
        f.write(animation_import)
        f.write("\n\n")
        f.write(create_login_animation_code())
    
    print("[OK] Animation patch created in app_animation_patch.py")
    print("To apply: Add the code from app_animation_patch.py to your login section")

def check_animation_file():
    """Check if animation file exists"""
    animation_file = "company_logo_animation.mp4.MOV"
    
    if os.path.exists(animation_file):
        size = os.path.getsize(animation_file) / (1024 * 1024)  # MB
        print(f"[OK] Animation file found: {animation_file} ({size:.2f} MB)")
        return True
    else:
        print(f"[INFO] Animation file not found: {animation_file}")
        print("      The system will use static logo as fallback")
        return False

def create_enhanced_logo_handler():
    """Create enhanced logo handler with animation support"""
    
    content = '''# -*- coding: utf-8 -*-
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
'''
    
    with open('enhanced_logo_handler.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Enhanced logo handler created")

def main():
    print("\n" + "="*50)
    print("LOGO ANIMATION IMPLEMENTATION")
    print("="*50 + "\n")
    
    # Check for animation file
    check_animation_file()
    
    # Create enhanced handler
    create_enhanced_logo_handler()
    
    # Create patch for app.py
    update_app_with_animation()
    
    print("\n" + "="*50)
    print("ANIMATION SETUP COMPLETE")
    print("="*50)
    
    print("\nTo activate animation:")
    print("1. Ensure company_logo_animation.mp4.MOV is in the root directory")
    print("2. Add code from app_animation_patch.py to your login section")
    print("3. Import: from enhanced_logo_handler import show_login_page_with_logo")
    print("4. Call show_login_page_with_logo() at the start of login")
    
    return True

if __name__ == "__main__":
    main()