"""
UI Responsiveness Fix Module
Fixes: Double-click issues, page freezing, button response delays
"""

import streamlit as st
import time
import hashlib
from datetime import datetime
import json

class UIResponsivenessFix:
    """Centralized UI responsiveness management"""
    
    def __init__(self):
        self.init_ui_state()
        self.apply_performance_css()
    
    def init_ui_state(self):
        """Initialize UI state management"""
        if 'ui_state' not in st.session_state:
            st.session_state.ui_state = {
                'form_locks': {},
                'button_locks': {},
                'last_action': None,
                'action_timestamps': {},
                'pending_operations': [],
                'debounce_timers': {}
            }
    
    def apply_performance_css(self):
        """Apply CSS for better UI performance"""
        st.markdown("""
        <style>
            /* Prevent double-click on all buttons */
            .stButton > button {
                transition: all 0.1s ease;
                pointer-events: auto;
            }
            
            .stButton > button:active {
                transform: scale(0.98);
            }
            
            .stButton > button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                pointer-events: none;
            }
            
            /* Faster form transitions */
            .stForm {
                transition: opacity 0.1s ease;
            }
            
            /* Prevent text selection during operations */
            .processing {
                user-select: none;
                pointer-events: none;
                opacity: 0.7;
            }
            
            /* Smooth select box interactions */
            div[data-baseweb="select"] {
                transition: all 0.1s ease;
            }
            
            /* Radio button responsiveness */
            .stRadio > div {
                transition: all 0.05s ease;
            }
            
            .stRadio > div > label {
                cursor: pointer;
                transition: background-color 0.1s ease;
            }
            
            .stRadio > div > label:hover {
                background-color: rgba(220, 20, 60, 0.1);
            }
            
            /* Prevent layout shift */
            .main .block-container {
                padding-top: 2rem;
                animation: fadeIn 0.2s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0.8; }
                to { opacity: 1; }
            }
            
            /* Loading states */
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.3);
                z-index: 9999;
                display: none;
            }
            
            .loading-overlay.active {
                display: block;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def prevent_double_submit(self, form_key, timeout=2.0):
        """Prevent double form submission"""
        current_time = time.time()
        
        if form_key in st.session_state.ui_state['form_locks']:
            last_submit = st.session_state.ui_state['form_locks'][form_key]
            if current_time - last_submit < timeout:
                return False
        
        st.session_state.ui_state['form_locks'][form_key] = current_time
        return True
    
    def debounce_action(self, action_key, callback, delay=0.5):
        """Debounce rapid actions"""
        current_time = time.time()
        
        if action_key in st.session_state.ui_state['debounce_timers']:
            last_time = st.session_state.ui_state['debounce_timers'][action_key]
            if current_time - last_time < delay:
                return None
        
        st.session_state.ui_state['debounce_timers'][action_key] = current_time
        return callback()
    
    def lock_button(self, button_key, duration=1.0):
        """Temporarily lock a button after click"""
        st.session_state.ui_state['button_locks'][button_key] = {
            'locked': True,
            'until': time.time() + duration
        }
    
    def is_button_locked(self, button_key):
        """Check if button is locked"""
        if button_key in st.session_state.ui_state['button_locks']:
            lock_info = st.session_state.ui_state['button_locks'][button_key]
            if lock_info['locked'] and time.time() < lock_info['until']:
                return True
            else:
                # Unlock if time has passed
                st.session_state.ui_state['button_locks'][button_key]['locked'] = False
        return False
    
    def create_responsive_button(self, label, key=None, type="secondary", 
                                use_container_width=False, disabled=False):
        """Create a responsive button with lock mechanism"""
        if key is None:
            key = hashlib.md5(label.encode()).hexdigest()[:8]
        
        # Check if button is locked
        is_locked = self.is_button_locked(key)
        
        # Create button with lock state
        clicked = st.button(
            label,
            key=key,
            type=type,
            use_container_width=use_container_width,
            disabled=disabled or is_locked
        )
        
        if clicked and not is_locked:
            self.lock_button(key)
            return True
        
        return False
    
    def create_responsive_form(self, key, clear_on_submit=False):
        """Create a responsive form with submission control"""
        form_hash = hashlib.md5(key.encode()).hexdigest()
        
        # Check if form is processing
        is_processing = form_hash in st.session_state.ui_state.get('pending_operations', [])
        
        if is_processing:
            st.warning("⏳ Processing previous submission...")
            return None
        
        return st.form(key, clear_on_submit=clear_on_submit)
    
    def start_operation(self, operation_id):
        """Mark operation as started"""
        if 'pending_operations' not in st.session_state.ui_state:
            st.session_state.ui_state['pending_operations'] = []
        
        st.session_state.ui_state['pending_operations'].append(operation_id)
        st.session_state.ui_state['action_timestamps'][operation_id] = time.time()
    
    def end_operation(self, operation_id):
        """Mark operation as completed"""
        if operation_id in st.session_state.ui_state.get('pending_operations', []):
            st.session_state.ui_state['pending_operations'].remove(operation_id)
    
    def show_processing_overlay(self, message="Processing..."):
        """Show processing overlay"""
        st.markdown(f"""
        <div class="loading-overlay active">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                        background: #1a1a1a; padding: 20px; border-radius: 10px; 
                        border: 2px solid #DC143C;">
                <h3 style="color: white; margin: 0;">{message}</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def create_responsive_selectbox(self, label, options, key=None, index=0, 
                                   format_func=None, on_change=None):
        """Create responsive selectbox with better state management"""
        if key is None:
            key = hashlib.md5(label.encode()).hexdigest()[:8]
        
        # Store previous value
        prev_key = f"{key}_prev"
        if prev_key not in st.session_state:
            st.session_state[prev_key] = None
        
        # Create selectbox
        value = st.selectbox(
            label,
            options,
            key=key,
            index=index,
            format_func=format_func
        )
        
        # Check if value changed
        if value != st.session_state[prev_key]:
            st.session_state[prev_key] = value
            if on_change:
                on_change(value)
        
        return value
    
    def create_responsive_radio(self, label, options, key=None, index=0, 
                               horizontal=False, on_change=None):
        """Create responsive radio buttons"""
        if key is None:
            key = hashlib.md5(label.encode()).hexdigest()[:8]
        
        # Initialize state if needed
        state_key = f"{key}_state"
        if state_key not in st.session_state:
            st.session_state[state_key] = options[index] if options else None
        
        # Create container for better control
        container = st.container()
        
        with container:
            # Create radio
            value = st.radio(
                label,
                options,
                key=key,
                index=index,
                horizontal=horizontal
            )
            
            # Handle change
            if value != st.session_state[state_key]:
                st.session_state[state_key] = value
                if on_change:
                    # Delay to ensure UI updates
                    time.sleep(0.1)
                    on_change(value)
        
        return value
    
    def create_responsive_tabs(self, tabs):
        """Create responsive tabs with state management"""
        # Generate unique key for tabs
        tabs_key = hashlib.md5(str(tabs).encode()).hexdigest()[:8]
        
        # Track active tab
        if f"active_tab_{tabs_key}" not in st.session_state:
            st.session_state[f"active_tab_{tabs_key}"] = 0
        
        # Create tabs
        tab_objects = st.tabs(tabs)
        
        return tab_objects
    
    def batch_update_state(self, updates):
        """Batch update session state to prevent multiple reruns"""
        for key, value in updates.items():
            st.session_state[key] = value
    
    def create_responsive_columns(self, spec):
        """Create responsive columns with proper spacing"""
        cols = st.columns(spec)
        
        # Add small delay to prevent layout issues
        time.sleep(0.01)
        
        return cols
    
    def safe_rerun(self, delay=0.5):
        """Safe rerun with delay to prevent rapid reruns"""
        time.sleep(delay)
        st.rerun()

# Global instance
ui_fix = UIResponsivenessFix()

def responsive_button(label, **kwargs):
    """Wrapper for responsive button"""
    return ui_fix.create_responsive_button(label, **kwargs)

def responsive_form(key, **kwargs):
    """Wrapper for responsive form"""
    return ui_fix.create_responsive_form(key, **kwargs)

def responsive_selectbox(label, options, **kwargs):
    """Wrapper for responsive selectbox"""
    return ui_fix.create_responsive_selectbox(label, options, **kwargs)

def responsive_radio(label, options, **kwargs):
    """Wrapper for responsive radio"""
    return ui_fix.create_responsive_radio(label, options, **kwargs)

def prevent_double_submit(form_key):
    """Wrapper for double submit prevention"""
    return ui_fix.prevent_double_submit(form_key)

def start_operation(operation_id):
    """Wrapper for operation start"""
    return ui_fix.start_operation(operation_id)

def end_operation(operation_id):
    """Wrapper for operation end"""
    return ui_fix.end_operation(operation_id)

def safe_rerun(delay=0.5):
    """Wrapper for safe rerun"""
    return ui_fix.safe_rerun(delay)

# Export all functions
__all__ = [
    'UIResponsivenessFix',
    'ui_fix',
    'responsive_button',
    'responsive_form',
    'responsive_selectbox',
    'responsive_radio',
    'prevent_double_submit',
    'start_operation',
    'end_operation',
    'safe_rerun'
]