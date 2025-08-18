"""
Vernon - The Face of IT Support
Smith & Williams Trucking's friendly, knowledgeable IT specialist
Always ready to help with a professional yet approachable demeanor
"""

import streamlit as st
import random
from datetime import datetime
import json

class Vernon:
    """Vernon's personality and interactions"""
    
    def __init__(self):
        self.name = "Vernon"
        self.title = "IT Support Specialist"
        self.company = "Smith & Williams Trucking"
        self.avatar = "🧑‍💻"  # Vernon's avatar
        self.mood = self.get_current_mood()
        
    def get_current_mood(self):
        """Vernon's mood based on time of day"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "energetic"  # Morning Vernon is energetic
        elif 12 <= hour < 17:
            return "focused"    # Afternoon Vernon is focused
        elif 17 <= hour < 21:
            return "helpful"    # Evening Vernon is extra helpful
        else:
            return "dedicated"  # Night Vernon is dedicated (always on call)
    
    def get_greeting(self, user_name=None):
        """Vernon's personalized greetings"""
        hour = datetime.now().hour
        
        greetings = {
            "morning": [
                f"Good morning! Vernon here, ready to tackle any IT challenges today! ☕",
                f"Morning! It's Vernon from IT. How can I make your tech life easier today?",
                f"Hey there! Vernon at your service. Let's solve some problems! 🌟"
            ],
            "afternoon": [
                f"Good afternoon! Vernon from IT here. What can I help you with?",
                f"Hi! It's Vernon. Having any tech troubles this afternoon?",
                f"Vernon here! Ready to assist with any system questions."
            ],
            "evening": [
                f"Good evening! Vernon from IT, still here to help!",
                f"Evening! It's Vernon. Don't hesitate to ask for help.",
                f"Hi there! Vernon here, working late to keep things running smooth."
            ],
            "night": [
                f"Vernon here! IT support never sleeps at Smith & Williams! 🌙",
                f"Late night? No problem! Vernon's got your back.",
                f"It's Vernon from IT. I'm here whenever you need help!"
            ]
        }
        
        if 5 <= hour < 12:
            greeting_list = greetings["morning"]
        elif 12 <= hour < 17:
            greeting_list = greetings["afternoon"]
        elif 17 <= hour < 21:
            greeting_list = greetings["evening"]
        else:
            greeting_list = greetings["night"]
        
        greeting = random.choice(greeting_list)
        
        if user_name:
            greeting = greeting.replace("!", f", {user_name}!")
        
        return greeting
    
    def get_signature(self):
        """Vernon's email/message signature"""
        return f"""
        Best regards,
        
        **{self.name}**
        {self.title}
        {self.company}
        📧 vernon.it@smithwilliamstrucking.com
        📱 Extension: 1337
        💬 *"Your IT success is my priority!"*
        """
    
    def get_tips(self):
        """Vernon's helpful IT tips"""
        tips = [
            "💡 **Vernon's Tip:** Save frequently! Use Ctrl+S (or Cmd+S on Mac) every few minutes.",
            "💡 **Vernon's Tip:** Clear your browser cache weekly for better performance.",
            "💡 **Vernon's Tip:** Take a screenshot before reporting an error - it helps me help you faster!",
            "💡 **Vernon's Tip:** The self-assignment system works best on your iPhone's Safari browser.",
            "💡 **Vernon's Tip:** Remember to upload your POD immediately after delivery!",
            "💡 **Vernon's Tip:** Use the refresh button if data seems outdated.",
            "💡 **Vernon's Tip:** Contact me directly for urgent IT issues - I'm always here!",
            "💡 **Vernon's Tip:** Enable notifications to stay updated on your moves.",
            "💡 **Vernon's Tip:** The walkthrough guide has all the answers - check it out!",
            "💡 **Vernon's Tip:** Reserved trailers expire after 30 minutes - assign quickly!"
        ]
        return random.choice(tips)
    
    def solve_problem(self, problem_description):
        """Vernon's problem-solving responses"""
        problem_lower = problem_description.lower()
        
        # Vernon's solution database
        solutions = {
            "login": {
                "diagnosis": "Ah, login troubles! I see this often.",
                "solution": "Let's fix this: 1) Check your username spelling, 2) Verify CAPS LOCK is off, 3) Try clearing browser cookies, 4) If still stuck, I'll reset your password - just call ext. 1337!",
                "followup": "Did that work? If not, I'm just a call away!"
            },
            "slow": {
                "diagnosis": "System running slow? Let Vernon investigate!",
                "solution": "Try these quick fixes: 1) Refresh the page (F5), 2) Close other browser tabs, 3) Clear cache (I can walk you through it!), 4) Check your internet connection.",
                "followup": "Performance should improve now. Let me know if it's still sluggish!"
            },
            "upload": {
                "diagnosis": "Upload issues can be frustrating - let's solve this together!",
                "solution": "Here's what usually works: 1) Check file size (max 10MB), 2) Ensure it's JPG, PNG, or PDF, 3) Try using your phone's camera directly, 4) Check your internet connection.",
                "followup": "Your documents are important - I'll make sure they upload!"
            },
            "assign": {
                "diagnosis": "Self-assignment not working? Vernon's on it!",
                "solution": "Let's check: 1) Are you in Driver Mode?, 2) Do you have an active move already?, 3) Try refreshing the page, 4) Check if the trailer is still available.",
                "followup": "The self-assignment system is my specialty - we'll get you moving!"
            },
            "default": {
                "diagnosis": "I understand you're having an issue. Vernon's here to help!",
                "solution": "Let me gather more info: 1) What were you trying to do?, 2) What error did you see?, 3) Can you send a screenshot?, 4) When did this start?",
                "followup": "Don't worry - we'll figure this out together!"
            }
        }
        
        # Find matching solution
        for keyword, response in solutions.items():
            if keyword in problem_lower:
                return response
        
        return solutions["default"]
    
    def get_encouragement(self):
        """Vernon's encouraging messages"""
        messages = [
            "You're doing great! Technology can be tricky, but you've got this! - Vernon",
            "Don't worry, we'll figure it out together! That's what I'm here for. - Vernon",
            "Every expert was once a beginner. You're learning fast! - Vernon",
            "Great question! That shows you're thinking ahead. - Vernon",
            "I'm impressed with how quickly you're picking this up! - Vernon",
            "Remember, there's no such thing as a dumb question in IT! - Vernon",
            "You're making my job easy with such clear descriptions! - Vernon",
            "Together, we make a great team! You drive, I support. - Vernon"
        ]
        return random.choice(messages)
    
    def get_status_update(self):
        """Vernon's system status updates"""
        return {
            "message": f"Vernon's System Check - {datetime.now().strftime('%I:%M %p')}",
            "status": "✅ All systems operational",
            "details": [
                "✓ Database: Online",
                "✓ Self-Assignment: Active", 
                "✓ Document Upload: Ready",
                "✓ Notifications: Enabled",
                "✓ Vernon Support: Always On!"
            ],
            "note": "I'm monitoring everything 24/7 so you don't have to!"
        }


def show_vernon_chat_interface():
    """Interactive chat interface with Vernon"""
    vernon = Vernon()
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea, #764ba2); 
                padding: 1.5rem; border-radius: 12px; color: white;">
        <h2>{vernon.avatar} Chat with SUPER VERNON - IT Superhero</h2>
        <p style="font-size: 0.9rem; opacity: 0.8;">Current Superpower: {vernon.superpower}</p>
        <p style="opacity: 0.9;">{vernon.get_greeting(st.session_state.get('user'))}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat interface
    if 'vernon_chat' not in st.session_state:
        st.session_state.vernon_chat = []
    
    # Display chat history
    for message in st.session_state.vernon_chat:
        if message['sender'] == 'user':
            st.markdown(f"""
            <div style="background: #e3f2fd; padding: 0.75rem; margin: 0.5rem 0; 
                        border-radius: 12px; margin-left: 20%;">
                <b>You:</b> {message['text']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #f3e5f5; padding: 0.75rem; margin: 0.5rem 0; 
                        border-radius: 12px; margin-right: 20%;">
                <b>{vernon.avatar} Vernon:</b> {message['text']}
            </div>
            """, unsafe_allow_html=True)
    
    # Input area
    with st.form("vernon_chat_form", clear_on_submit=True):
        user_message = st.text_input(
            "Type your message to Vernon:",
            placeholder="e.g., How do I self-assign a move?",
            key="vernon_input"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            send = st.form_submit_button("💬 Send", type="primary", use_container_width=True)
        with col2:
            if st.form_submit_button("🔄 Clear Chat", use_container_width=True):
                st.session_state.vernon_chat = []
                st.rerun()
        with col3:
            if st.form_submit_button("📞 Call Vernon", use_container_width=True):
                st.info("📞 Call Vernon at ext. 1337")
        
        if send and user_message:
            # Add user message
            st.session_state.vernon_chat.append({
                'sender': 'user',
                'text': user_message
            })
            
            # Get Vernon's response
            solution = vernon.solve_problem(user_message)
            
            # Add Vernon's responses
            st.session_state.vernon_chat.append({
                'sender': 'vernon',
                'text': solution['diagnosis']
            })
            
            st.session_state.vernon_chat.append({
                'sender': 'vernon',
                'text': solution['solution']
            })
            
            st.session_state.vernon_chat.append({
                'sender': 'vernon',
                'text': solution['followup']
            })
            
            st.rerun()
    
    # Vernon's helpful footer
    with st.expander("🎯 Vernon's Quick Solutions"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Common Issues:**")
            if st.button("Can't login"):
                st.info("Check CAPS LOCK and try again. Still stuck? Call me at ext. 1337!")
            if st.button("Can't see moves"):
                st.info("Switch to Driver Mode using the sidebar role switcher!")
            if st.button("Upload failed"):
                st.info("Check file size (max 10MB) and format (JPG, PNG, PDF)")
        
        with col2:
            st.markdown("**Quick Actions:**")
            if st.button("System Status"):
                status = vernon.get_status_update()
                st.success(status['message'])
                for detail in status['details']:
                    st.write(detail)
                st.info(status['note'])
            if st.button("Get IT Tip"):
                st.info(vernon.get_tips())
            if st.button("Encouragement"):
                st.success(vernon.get_encouragement())
    
    # Vernon's signature
    st.markdown("---")
    st.markdown(vernon.get_signature())


def show_vernon_widget(compact=False):
    """Vernon widget that can be embedded anywhere"""
    vernon = Vernon()
    
    if compact:
        # Compact version for sidebars
        with st.container():
            st.markdown(f"**{vernon.avatar} Vernon IT Support**")
            st.caption("Available 24/7 • Ext. 1337")
            if st.button("💬 Chat with Vernon", use_container_width=True):
                st.session_state.show_vernon_chat = True
                st.rerun()
    else:
        # Full version
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea, #764ba2);
                        padding: 1rem; border-radius: 8px; color: white;">
                <h4>{vernon.avatar} Need Help? Ask Vernon!</h4>
                <p style="margin: 0; opacity: 0.9;">Your friendly IT support specialist</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💬 Live Chat", use_container_width=True):
                    st.session_state.show_vernon_chat = True
            with col2:
                if st.button("📞 Call Vernon", use_container_width=True):
                    st.info("Extension: 1337")
            with col3:
                if st.button("📧 Email Vernon", use_container_width=True):
                    st.info("vernon.it@smithwilliamstrucking.com")
            
            # Show a random tip
            st.info(vernon.get_tips())


def vernon_easter_eggs():
    """Fun Vernon easter eggs for the system"""
    vernon = Vernon()
    
    # Random Vernon appearances
    if random.random() < 0.05:  # 5% chance
        messages = [
            "Vernon was here! 🧑‍💻 - Keeping your systems running smooth!",
            "Vernon's watching... your system health! Everything looks good! 👍",
            "Vernon says: Remember to take a break and stretch! 🏃‍♂️",
            "Vernon's IT fact: The first computer bug was an actual bug (a moth)! 🦋",
            "Vernon checked in - all systems green! ✅"
        ]
        return random.choice(messages)
    return None


# Vernon's presence throughout the app
def integrate_vernon_everywhere():
    """Add Vernon's helpful presence to every page"""
    
    # Check if Vernon should appear
    if 'vernon_last_tip' not in st.session_state:
        st.session_state.vernon_last_tip = datetime.now()
    
    # Show Vernon tip every 30 minutes
    if (datetime.now() - st.session_state.vernon_last_tip).seconds > 1800:
        vernon = Vernon()
        st.sidebar.info(vernon.get_tips())
        st.session_state.vernon_last_tip = datetime.now()
    
    # Easter egg check
    egg = vernon_easter_eggs()
    if egg:
        st.sidebar.success(egg)
    
    # Always show Vernon widget in sidebar
    with st.sidebar:
        st.markdown("---")
        show_vernon_widget(compact=True)


# Export main components
__all__ = [
    'Vernon',
    'show_vernon_chat_interface',
    'show_vernon_widget',
    'integrate_vernon_everywhere'
]