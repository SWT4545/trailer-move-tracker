"""
Error Message Handler - Graceful Error Display
Makes error messages less alarming for non-critical issues
"""

import streamlit as st
import logging

class ErrorHandler:
    """Handles different types of errors with appropriate display styles"""
    
    @staticmethod
    def show_message(message, level="info", icon=None):
        """
        Display message with appropriate styling based on severity
        
        Levels:
        - critical: Red error box (real errors)
        - warning: Yellow warning (attention needed)
        - info: Blue info box (neutral information)
        - success: Green success (positive feedback)
        - placeholder: Gray subtle text (empty states)
        """
        
        if level == "critical":
            # Real errors that need attention
            if icon:
                st.error(f"{icon} {message}")
            else:
                st.error(f"❌ {message}")
                
        elif level == "warning":
            # Issues that might need attention
            if icon:
                st.warning(f"{icon} {message}")
            else:
                st.warning(f"⚠️ {message}")
                
        elif level == "info":
            # Neutral information
            if icon:
                st.info(f"{icon} {message}")
            else:
                st.info(message)
                
        elif level == "success":
            # Positive feedback
            if icon:
                st.success(f"{icon} {message}")
            else:
                st.success(f"✅ {message}")
                
        elif level == "placeholder":
            # Subtle placeholder for empty states
            st.markdown(f"""
                <div style='
                    padding: 1rem;
                    background-color: rgba(128, 128, 128, 0.1);
                    border-radius: 0.5rem;
                    color: #888;
                    font-style: italic;
                    text-align: center;
                '>
                    {icon if icon else '📋'} {message}
                </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def handle_database_error(error, context=""):
        """Handle database errors gracefully"""
        error_str = str(error).lower()
        
        # Check if it's just a missing column or table
        if "no such column" in error_str:
            # Not critical - probably just needs sync
            ErrorHandler.show_message(
                "Database needs to be synced. Click refresh or sync drivers.",
                level="info",
                icon="🔄"
            )
            
        elif "no such table" in error_str:
            # Table doesn't exist - needs initialization
            ErrorHandler.show_message(
                "Database tables need to be created. Click the refresh button.",
                level="warning",
                icon="🗂️"
            )
            
        elif "database is locked" in error_str:
            # Temporary issue
            ErrorHandler.show_message(
                "Database is busy. Please try again in a moment.",
                level="info",
                icon="⏳"
            )
            
        elif "not found" in error_str or "empty" in error_str:
            # No data - not an error
            ErrorHandler.show_message(
                f"No {context} found yet. Add some to get started!",
                level="placeholder",
                icon="➕"
            )
            
        else:
            # Real error that needs attention
            ErrorHandler.show_message(
                f"Database error: {error}",
                level="critical"
            )
            logging.error(f"Database error in {context}: {error}")
    
    @staticmethod
    def handle_empty_data(data_type):
        """Display friendly message for empty data"""
        messages = {
            "drivers": "No drivers found. Add drivers in the Drivers section.",
            "trailers": "No trailers available. Add trailers to get started.",
            "moves": "No active moves. Create a new move to begin.",
            "locations": "No locations yet. They'll be added automatically when you create moves.",
            "rate_cons": "No rate confirmations uploaded yet.",
            "payments": "No payments to display.",
            "users": "No users found. Contact your administrator."
        }
        
        message = messages.get(data_type, f"No {data_type} found.")
        ErrorHandler.show_message(message, level="placeholder")
    
    @staticmethod
    def handle_permission_error(required_role=None):
        """Display permission error gracefully"""
        if required_role:
            ErrorHandler.show_message(
                f"This feature requires {required_role} permissions.",
                level="info",
                icon="🔒"
            )
        else:
            ErrorHandler.show_message(
                "You don't have permission to access this feature.",
                level="info",
                icon="🔒"
            )
    
    @staticmethod
    def handle_loading_state(item_type):
        """Show loading state"""
        with st.spinner(f"Loading {item_type}..."):
            return True
    
    @staticmethod
    def handle_sync_needed(item_type):
        """Show sync needed message"""
        ErrorHandler.show_message(
            f"{item_type} need to be synced. Click the Sync button to update.",
            level="info",
            icon="🔄"
        )

# Convenience functions for common cases
def show_empty_state(data_type):
    """Quick function to show empty state"""
    ErrorHandler.handle_empty_data(data_type)

def show_error_safe(error, context=""):
    """Safe error display that won't alarm users unnecessarily"""
    ErrorHandler.handle_database_error(error, context)

def show_info(message, icon="ℹ️"):
    """Show informational message"""
    ErrorHandler.show_message(message, level="info", icon=icon)

def show_placeholder(message, icon="📋"):
    """Show placeholder for empty data"""
    ErrorHandler.show_message(message, level="placeholder", icon=icon)