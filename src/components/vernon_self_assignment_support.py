"""
Vernon IT Support - Enhanced for Self-Assignment System
Provides intelligent IT support for the new driver self-assignment features
"""

import streamlit as st
import json
from datetime import datetime
import database as db
import sqlite3

class VernonSelfAssignmentSupport:
    """Vernon's enhanced support for self-assignment system"""
    
    def __init__(self):
        self.knowledge_base = self.load_self_assignment_knowledge()
        self.common_issues = self.load_common_issues()
        
    def load_self_assignment_knowledge(self):
        """Load knowledge base for self-assignment support"""
        return {
            'self_assignment': {
                'how_to_self_assign': """
                **How to Self-Assign a Move:**
                1. Go to the 'Self-Assign Move' tab
                2. Browse available moves (shown with location and pay)
                3. Click 'Reserve & Review' to hold a move for 30 minutes
                4. Click 'Confirm Assignment' to accept the move
                5. The move will appear in your 'Current Move' tab
                """,
                'reservation_system': """
                **Reservation System:**
                - You can reserve a move for 30 minutes to review details
                - Only one reservation at a time
                - Reservations auto-expire after 30 minutes
                - Other drivers cannot take reserved moves
                """,
                'daily_limits': """
                **Daily Move Limits:**
                - Default: 1 move per day
                - Can be adjusted in Settings
                - Resets at midnight
                - Management can override limits
                """,
                'cannot_see_moves': """
                **Why You Can't See Available Moves:**
                1. You already have an active move
                2. You've reached your daily limit
                3. No moves currently available
                4. Your account may not have self-assignment permission
                """,
                'payment_tracking': """
                **Payment & Earnings:**
                - Estimated pay shown before assignment
                - Actual pay calculated after completion
                - View earnings in 'My Earnings' tab
                - Payments processed weekly
                - Pending vs Paid status tracked
                """
            },
            'troubleshooting': {
                'login_issues': """
                **Login Problems:**
                1. Verify username (provided by dispatch)
                2. Check password (case-sensitive)
                3. Clear browser cache
                4. Try incognito/private mode
                5. Contact dispatch for password reset
                """,
                'assignment_failed': """
                **Assignment Failed:**
                - Move may have been taken by another driver
                - Check your daily limit hasn't been reached
                - Verify you don't have an active move
                - Try refreshing the page
                - Contact support if issue persists
                """,
                'progress_not_updating': """
                **Progress Not Updating:**
                1. Click the Refresh button
                2. Check your internet connection
                3. Try logging out and back in
                4. Clear browser cache
                5. Report to IT if continues
                """,
                'photo_upload_issues': """
                **Photo Upload Problems:**
                - Max file size: 10MB
                - Accepted formats: JPG, PNG
                - Check internet connection
                - Try reducing photo size
                - Use mobile browser if app issues
                """,
                'reservation_expired': """
                **Reservation Expired:**
                - Reservations last 30 minutes
                - Move becomes available to others
                - You can reserve again if still available
                - Complete assignment quickly after reserving
                """
            },
            'features': {
                'trailer_reporting': """
                **Report Trailer Locations:**
                - Help team track trailer locations
                - Report any trailer you spot
                - Optional photo for verification
                - Earns recognition points
                - Improves system accuracy
                """,
                'earnings_dashboard': """
                **Earnings Dashboard:**
                - View last 7, 14, 30, 60, or 90 days
                - See pending vs paid amounts
                - Track total miles driven
                - Export for tax purposes
                - Real-time updates
                """,
                'notification_settings': """
                **Notification Preferences:**
                - Email alerts for new moves
                - SMS for urgent updates
                - In-app notifications
                - Customize in Settings tab
                - Quiet hours available
                """,
                'move_progress': """
                **Tracking Move Progress:**
                1. **Assigned** (25%) - Move assigned, not started
                2. **In Progress** (50%) - Pickup started
                3. **Pickup Complete** (75%) - Heading to delivery
                4. **Completed** (100%) - Delivery done
                """
            },
            'policies': {
                'cancellation': """
                **Cancellation Policy:**
                - Can cancel before starting pickup
                - Must provide reason
                - Excessive cancellations reviewed
                - Emergency cancellations understood
                - Contact dispatch for help
                """,
                'priority_moves': """
                **Priority Move System:**
                - Some moves marked as urgent
                - Higher pay for priority moves
                - First-come, first-served basis
                - No seniority advantage
                - Fair opportunity for all
                """,
                'documentation': """
                **Required Documentation:**
                - Pickup photo required
                - Delivery photo required
                - POD (Proof of Delivery) required
                - Fleet receipt for fuel
                - Damage photos if applicable
                """
            }
        }
    
    def load_common_issues(self):
        """Load common issues and solutions"""
        return {
            'database_error': {
                'symptoms': ['Database locked', 'Connection error', 'Table not found'],
                'solutions': [
                    'Refresh the page',
                    'Clear browser cache',
                    'Wait 30 seconds and retry',
                    'Contact IT if persists'
                ]
            },
            'assignment_conflict': {
                'symptoms': ['Move already assigned', 'Conflict error', 'Cannot assign'],
                'solutions': [
                    'Move was taken by another driver',
                    'Refresh to see updated list',
                    'Try a different move',
                    'Check your active moves'
                ]
            },
            'payment_questions': {
                'symptoms': ['Payment not showing', 'Wrong amount', 'Status unclear'],
                'solutions': [
                    'Payments process weekly',
                    'Check payment status column',
                    'Verify POD was uploaded',
                    'Contact accounting for details'
                ]
            }
        }
    
    def diagnose_issue(self, issue_description):
        """Diagnose issue based on description"""
        issue_lower = issue_description.lower()
        
        # Check for keyword matches
        if 'login' in issue_lower or 'password' in issue_lower:
            return self.knowledge_base['troubleshooting']['login_issues']
        elif 'assign' in issue_lower and ('fail' in issue_lower or 'can\'t' in issue_lower):
            return self.knowledge_base['troubleshooting']['assignment_failed']
        elif 'move' in issue_lower and 'see' in issue_lower:
            return self.knowledge_base['self_assignment']['cannot_see_moves']
        elif 'pay' in issue_lower or 'earning' in issue_lower:
            return self.knowledge_base['self_assignment']['payment_tracking']
        elif 'reserve' in issue_lower or 'reservation' in issue_lower:
            return self.knowledge_base['self_assignment']['reservation_system']
        elif 'photo' in issue_lower or 'upload' in issue_lower:
            return self.knowledge_base['troubleshooting']['photo_upload_issues']
        elif 'progress' in issue_lower:
            return self.knowledge_base['features']['move_progress']
        elif 'cancel' in issue_lower:
            return self.knowledge_base['policies']['cancellation']
        else:
            return """
            I couldn't find a specific solution. Please try:
            1. Refresh the page
            2. Check the walkthrough guide
            3. Contact dispatch for assistance
            
            You can also browse topics in the help menu.
            """
    
    def log_support_interaction(self, user, issue, solution_provided):
        """Log support interactions for improvement"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO activity_log (action, entity_type, user, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                'vernon_support',
                'self_assignment',
                user,
                json.dumps({
                    'issue': issue,
                    'solution': solution_provided[:500]  # Truncate long solutions
                }),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
        except:
            pass  # Silent fail for logging


def show_vernon_support_widget(context="general"):
    """Show Vernon support widget in any interface"""
    
    with st.expander("🤖 Vernon IT Support - Click for Help", expanded=False):
        vernon = VernonSelfAssignmentSupport()
        
        tab1, tab2, tab3, tab4 = st.tabs(["❓ Ask Vernon", "📚 Topics", "🚨 Common Issues", "📞 Contact"])
        
        with tab1:
            st.markdown("**Hi! I'm Vernon, your IT assistant. How can I help?**")
            
            issue = st.text_area(
                "Describe your issue:",
                placeholder="e.g., I can't see any available moves",
                key=f"vernon_issue_{context}"
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🔍 Get Help", key=f"vernon_help_{context}"):
                    if issue:
                        solution = vernon.diagnose_issue(issue)
                        st.markdown("### 💡 Solution:")
                        st.markdown(solution)
                        
                        # Log interaction
                        user = st.session_state.get('driver_name', 'Unknown')
                        vernon.log_support_interaction(user, issue, solution)
                    else:
                        st.warning("Please describe your issue")
        
        with tab2:
            st.markdown("**Browse Help Topics:**")
            
            topic_category = st.selectbox(
                "Category:",
                ["Self-Assignment", "Troubleshooting", "Features", "Policies"],
                key=f"vernon_category_{context}"
            )
            
            if topic_category == "Self-Assignment":
                topics = vernon.knowledge_base['self_assignment']
            elif topic_category == "Troubleshooting":
                topics = vernon.knowledge_base['troubleshooting']
            elif topic_category == "Features":
                topics = vernon.knowledge_base['features']
            else:
                topics = vernon.knowledge_base['policies']
            
            topic_name = st.selectbox(
                "Topic:",
                list(topics.keys()),
                format_func=lambda x: x.replace('_', ' ').title(),
                key=f"vernon_topic_{context}"
            )
            
            if topic_name:
                st.markdown(topics[topic_name])
        
        with tab3:
            st.markdown("**Common Issues & Quick Fixes:**")
            
            for issue_type, issue_data in vernon.common_issues.items():
                with st.expander(issue_type.replace('_', ' ').title()):
                    st.markdown("**Symptoms:**")
                    for symptom in issue_data['symptoms']:
                        st.write(f"• {symptom}")
                    
                    st.markdown("**Solutions:**")
                    for i, solution in enumerate(issue_data['solutions'], 1):
                        st.write(f"{i}. {solution}")
        
        with tab4:
            st.markdown("**Contact Support:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **📞 Dispatch**
                - Phone: (555) 123-4567
                - Hours: 24/7
                - For: Urgent issues
                """)
                
                st.markdown("""
                **📧 IT Support**
                - Email: it@smithwilliams.com
                - Response: Within 2 hours
                - For: Technical issues
                """)
            
            with col2:
                st.markdown("""
                **💬 Live Chat**
                - Available: 6 AM - 10 PM
                - Click chat icon
                - For: Quick questions
                """)
                
                st.markdown("""
                **📱 Text Support**
                - Text: (555) 987-6543
                - Keyword: HELP
                - For: Mobile issues
                """)
            
            st.info("**Emergency**: For safety issues, call 911 immediately")


def integrate_vernon_everywhere():
    """Function to add Vernon to any page"""
    # This would be called in each module where Vernon is needed
    show_vernon_support_widget(context=st.session_state.get('current_page', 'general'))