"""
Interactive Help System for Trailer Fleet Management System
Provides contextual help, tooltips, and walkthroughs
"""

import streamlit as st
from typing import Dict, Optional

class HelpSystem:
    def __init__(self):
        self.help_content = self._load_help_content()
        self.walkthroughs = self._load_walkthroughs()
    
    def _load_help_content(self) -> Dict:
        """Load all help content"""
        return {
            'dashboard': {
                'title': 'Dashboard Overview',
                'content': """
                The dashboard shows your fleet status at a glance:
                - **Active Moves**: Trailers currently in transit
                - **OLD Trailers**: Available for pickup at FedEx locations
                - **NEW Trailers**: Ready for delivery from Fleet Memphis
                - **Recent Activity**: Latest completed moves and earnings
                """,
                'tips': [
                    "Green badges mean trailers are available",
                    "Click on any move to see full details",
                    "Earnings shown are AFTER 3% factoring fee"
                ]
            },
            'create_move': {
                'title': 'Creating a New Move',
                'content': """
                **Step-by-step process:**
                1. **Select NEW Trailer** - Choose from available trailers at Fleet Memphis
                2. **Select Destination** - Pick FedEx location (shows OLD trailer count)
                3. **Choose OLD Trailer** - Select which trailer to bring back
                4. **Assign Driver** - Pick who will handle this move
                5. **Set Date & Client** - Schedule and assign to customer
                """,
                'tips': [
                    "Routes with [AVAILABLE] have OLD trailers ready for pickup",
                    "System auto-calculates mileage based on destination",
                    "Earnings = Miles × $2.10 - 3% factoring"
                ]
            },
            'active_moves': {
                'title': 'Managing Active Moves',
                'content': """
                Track all moves in progress:
                - **Update Status** - Mark as picked up, in transit, or delivered
                - **Add MLBL** - Enter Master Load Bill number when received
                - **Quick Actions** - Complete or cancel moves
                - **Real-time Tracking** - See where each trailer is
                """,
                'tips': [
                    "Yellow status = In Transit",
                    "Green status = Delivered",
                    "Add MLBL numbers for payment processing"
                ]
            },
            'completed_moves': {
                'title': 'Completed Moves & Payments',
                'content': """
                Review finished moves and track payments:
                - **Payment Status** - Pending, Processing, or Paid
                - **Earnings Breakdown** - Gross, factoring fee, and net
                - **Export Options** - Generate PDFs for records
                - **Date Filtering** - Search by date range
                """,
                'tips': [
                    "Green = Paid, Yellow = Pending",
                    "Click 'Mark as Paid' when payment received",
                    "Generate monthly reports for accounting"
                ]
            }
        }
    
    def _load_walkthroughs(self) -> Dict:
        """Load walkthrough sequences"""
        return {
            'first_move': [
                {
                    'step': 1,
                    'title': 'Creating Your First Move',
                    'content': 'Click on "Create Move" tab to start',
                    'highlight': 'create_move_tab'
                },
                {
                    'step': 2,
                    'title': 'Select NEW Trailer',
                    'content': 'Choose an available NEW trailer from Fleet Memphis',
                    'highlight': 'trailer_select'
                },
                {
                    'step': 3,
                    'title': 'Pick Destination',
                    'content': 'Select FedEx location - ones with OLD trailers show counts',
                    'highlight': 'destination_select'
                },
                {
                    'step': 4,
                    'title': 'Assign Driver',
                    'content': 'Choose which driver will handle this move',
                    'highlight': 'driver_select'
                },
                {
                    'step': 5,
                    'title': 'Create Move',
                    'content': 'Click CREATE MOVE ORDER to finalize',
                    'highlight': 'create_button'
                }
            ]
        }
    
    def show_help_button(self, key: str, size: str = "small"):
        """Show a help button for a specific topic"""
        help_icon = "❓"
        if size == "small":
            if st.button(help_icon, key=f"help_{key}", help="Click for help"):
                self.show_help_modal(key)
        else:
            if st.button(f"{help_icon} Help", key=f"help_{key}", help="Click for help"):
                self.show_help_modal(key)
    
    def show_help_modal(self, topic: str):
        """Display help content in a modal-like container"""
        if topic in self.help_content:
            help_data = self.help_content[topic]
            with st.expander(f"ℹ️ {help_data['title']}", expanded=True):
                st.markdown(help_data['content'])
                
                if help_data.get('tips'):
                    st.markdown("**💡 Quick Tips:**")
                    for tip in help_data['tips']:
                        st.markdown(f"• {tip}")
    
    def show_inline_help(self, topic: str, style: str = "info"):
        """Show inline help text"""
        if topic in self.help_content:
            help_data = self.help_content[topic]
            if style == "info":
                st.info(f"ℹ️ **Tip**: {help_data['tips'][0] if help_data.get('tips') else help_data['content'][:100]}")
    
    def show_sidebar_help(self):
        """Add help section to sidebar"""
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 📚 Help & Support")
            
            # Quick help topics
            with st.expander("❓ Quick Help"):
                st.markdown("""
                **Common Tasks:**
                
                🚚 **Create Move**
                - Select NEW trailer from Fleet
                - Pick FedEx destination
                - Choose OLD trailer to return
                - Assign driver & date
                
                📍 **Track Move**
                - View in Active Moves
                - Update status as needed
                - Add MLBL when received
                
                💰 **Process Payment**
                - Mark move as completed
                - Wait for payment
                - Mark as paid when received
                
                📊 **View Reports**
                - Check dashboard metrics
                - Generate PDFs
                - Export data
                """)

# Singleton instance
_help_system = None

def get_help_system():
    """Get or create help system instance"""
    global _help_system
    if _help_system is None:
        _help_system = HelpSystem()
    return _help_system

def show_contextual_help(context: str, position: str = "top"):
    """Show help relevant to current context"""
    help_sys = get_help_system()
    
    if position == "top":
        col1, col2 = st.columns([10, 1])
        with col2:
            help_sys.show_help_button(context, "small")
    elif position == "inline":
        help_sys.show_inline_help(context, "info")
    
    return help_sys