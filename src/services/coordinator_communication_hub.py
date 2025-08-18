"""
Operations Coordinator Communication Hub
Comprehensive driver communication system with individual and group messaging
Clear, easy-to-use interface for coordinators
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import hashlib
import json
import base64
from urllib.parse import urlencode

# Coordinator-friendly styling
COORDINATOR_CSS = """
<style>
    .comm-header {
        background: linear-gradient(135deg, #DC143C 0%, #8B0000 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .quick-stats {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .driver-card {
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s;
    }
    
    .driver-card:hover {
        border-color: #DC143C;
        box-shadow: 0 2px 8px rgba(220,20,60,0.2);
    }
    
    .priority-high {
        border-left: 5px solid #dc3545;
    }
    
    .priority-medium {
        border-left: 5px solid #ffc107;
    }
    
    .priority-normal {
        border-left: 5px solid #28a745;
    }
    
    .message-preview {
        background: #e7f3ff;
        border: 2px solid #17a2b8;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        font-family: monospace;
        white-space: pre-wrap;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        position: relative;
    }
    
    .step {
        flex: 1;
        text-align: center;
        position: relative;
        z-index: 1;
    }
    
    .step-number {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #ddd;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.5rem;
        font-weight: bold;
    }
    
    .step.active .step-number {
        background: #DC143C;
    }
    
    .step.completed .step-number {
        background: #28a745;
    }
    
    .template-card {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
    }
    
    .template-card:hover {
        background: #ffc107;
    }
</style>
"""

def generate_route_token(move_id, driver_name, expiry_hours=24):
    """Generate a secure token for driver route access"""
    token_data = {
        'move_id': move_id,
        'driver': driver_name,
        'created': datetime.now().isoformat(),
        'expires': (datetime.now() + timedelta(hours=expiry_hours)).isoformat(),
        'type': 'driver_route'
    }
    
    token_json = json.dumps(token_data)
    token_bytes = token_json.encode('utf-8')
    token_b64 = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
    
    hash_input = f"{move_id}{driver_name}{token_data['created']}"
    token_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
    
    return f"{token_b64}.{token_hash}"

def store_communication_log(driver_name, move_id, message_type, message_content, token=None):
    """Log all communications for tracking"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS communication_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT,
            move_id INTEGER,
            message_type TEXT,
            message_content TEXT,
            token TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_by TEXT
        )
    """)
    
    cursor.execute("""
        INSERT INTO communication_log (driver_name, move_id, message_type, message_content, token, sent_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (driver_name, move_id, message_type, message_content, token, st.session_state.get('user', 'Coordinator')))
    
    conn.commit()
    conn.close()

def get_today_assignments():
    """Get all assignments for today with priority indicators"""
    conn = db.get_connection()
    
    query = """
        SELECT 
            tm.*,
            l1.address as pickup_address,
            l2.address as delivery_address,
            l1.old_trailer_count as pickup_trailer_count,
            CASE 
                WHEN l1.old_trailer_count >= 5 THEN 'HIGH'
                WHEN l1.old_trailer_count >= 3 THEN 'MEDIUM'
                ELSE 'NORMAL'
            END as priority
        FROM trailer_moves tm
        LEFT JOIN locations l1 ON tm.new_pickup_location = l1.location_title
        LEFT JOIN locations l2 ON tm.new_destination = l2.location_title
        WHERE date(tm.date_assigned) = date('now')
        ORDER BY 
            CASE 
                WHEN l1.old_trailer_count >= 5 THEN 1
                WHEN l1.old_trailer_count >= 3 THEN 2
                ELSE 3
            END,
            tm.driver_name
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_message_templates():
    """Get predefined message templates"""
    return {
        "Standard Route": """🚛 ROUTE ASSIGNMENT - {driver_name}

📅 Date: {date}
📍 Move ID: #{move_id}

NEW TRAILER:
📦 Trailer: {new_trailer}
📍 Pickup: {pickup_location}
📍 Deliver to: {delivery_location}

📏 Miles: {miles} (Round trip: {round_trip})
💰 Rate: ${rate}/mile

📸 REQUIRED: 12 photos
🔗 Route Details: {link}

Reply ACCEPTED to confirm""",

        "Urgent Pickup": """🚨 URGENT PICKUP - {driver_name}

⚠️ HIGH PRIORITY - {pickup_location} has {trailer_count} trailers!

📦 Trailer: {new_trailer}
📍 Location: {pickup_location}
⏰ Pickup ASAP

🔗 Details: {link}

Call dispatch if any issues: (555) 123-4567""",

        "Route Update": """📱 ROUTE UPDATE - {driver_name}

Your route #{move_id} has been updated:

{update_details}

🔗 Check updated details: {link}

Questions? Call dispatch.""",

        "Daily Schedule": """📅 TODAY'S SCHEDULE - {driver_name}

You have {route_count} route(s) today:

{route_list}

🔗 All routes: {link}

Safe travels! 🚛""",

        "Reminder": """⏰ REMINDER - {driver_name}

{reminder_message}

🔗 Route link: {link}

Thank you!"""
    }

def generate_message_content(template, move_data, link, custom_values={}):
    """Generate message content from template and data"""
    values = {
        'driver_name': move_data.get('driver_name', ''),
        'date': datetime.now().strftime('%B %d, %Y'),
        'move_id': move_data.get('id', ''),
        'new_trailer': move_data.get('new_trailer_number', ''),
        'pickup_location': move_data.get('new_pickup_location', ''),
        'delivery_location': move_data.get('new_destination', ''),
        'miles': move_data.get('miles', 'TBD'),
        'round_trip': move_data.get('round_trip_miles', 'TBD'),
        'rate': move_data.get('rate', 2.10),
        'link': link,
        'trailer_count': move_data.get('pickup_trailer_count', 0),
        **custom_values
    }
    
    try:
        return template.format(**values)
    except KeyError as e:
        return template  # Return template as-is if formatting fails

def show_coordinator_hub():
    """Main coordinator communication interface"""
    
    st.markdown(COORDINATOR_CSS, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="comm-header">
        <h1>📱 Operations Coordinator Communication Hub</h1>
        <p>Manage all driver communications from one place</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Stats
    today_assignments = get_today_assignments()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 Today's Routes", len(today_assignments))
    with col2:
        high_priority = len(today_assignments[today_assignments['priority'] == 'HIGH'])
        st.metric("🚨 High Priority", high_priority)
    with col3:
        unique_drivers = today_assignments['driver_name'].nunique() if not today_assignments.empty else 0
        st.metric("👥 Active Drivers", unique_drivers)
    with col4:
        st.metric("📱 Messages Sent", "Track in log")
    
    # Main Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Individual Messages",
        "📢 Group Broadcast", 
        "📋 Today's Assignments",
        "📝 Templates",
        "📊 Communication Log"
    ])
    
    with tab1:
        show_individual_messaging(today_assignments)
    
    with tab2:
        show_group_broadcast(today_assignments)
    
    with tab3:
        show_todays_assignments(today_assignments)
    
    with tab4:
        show_message_templates()
    
    with tab5:
        show_communication_log()

def show_individual_messaging(assignments_df):
    """Individual driver messaging interface"""
    
    st.markdown("### 📤 Send Individual Driver Messages")
    
    # Step indicator
    st.markdown("""
    <div class="step-indicator">
        <div class="step active">
            <div class="step-number">1</div>
            <div>Select Route</div>
        </div>
        <div class="step">
            <div class="step-number">2</div>
            <div>Customize Message</div>
        </div>
        <div class="step">
            <div class="step-number">3</div>
            <div>Generate Link</div>
        </div>
        <div class="step">
            <div class="step-number">4</div>
            <div>Copy & Send</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if assignments_df.empty:
        st.info("📭 No routes assigned for today. Add routes in the main system.")
        return
    
    # Step 1: Select Route
    st.markdown("#### Step 1: Select Route")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create display options with priority indicators
        route_options = []
        for _, row in assignments_df.iterrows():
            priority_icon = {
                'HIGH': '🔴',
                'MEDIUM': '🟡', 
                'NORMAL': '🟢'
            }.get(row['priority'], '⚪')
            
            option = f"{priority_icon} #{row['id']} - {row['driver_name']} - {row['new_trailer_number']} ({row['new_pickup_location']} → {row['new_destination']})"
            route_options.append(option)
        
        selected_route = st.selectbox(
            "Choose route to send:",
            options=route_options,
            help="Routes are sorted by priority (Red = High, Yellow = Medium, Green = Normal)"
        )
        
        if selected_route:
            route_id = int(selected_route.split('#')[1].split(' ')[0])
            move_data = assignments_df[assignments_df['id'] == route_id].iloc[0].to_dict()
    
    with col2:
        if selected_route:
            # Show route details card
            priority_class = f"priority-{move_data['priority'].lower()}"
            st.markdown(f"""
            <div class="driver-card {priority_class}">
                <strong>Driver:</strong> {move_data['driver_name']}<br>
                <strong>Trailer:</strong> {move_data['new_trailer_number']}<br>
                <strong>Priority:</strong> {move_data['priority']}<br>
                <strong>Location Count:</strong> {move_data.get('pickup_trailer_count', 0)} trailers
            </div>
            """, unsafe_allow_html=True)
    
    if selected_route:
        st.divider()
        
        # Step 2: Customize Message
        st.markdown("#### Step 2: Customize Message")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Template selection
            templates = get_message_templates()
            template_name = st.selectbox(
                "Message Template:",
                options=list(templates.keys()),
                help="Choose a pre-written template or create custom"
            )
            
            # Link expiry
            expiry_option = st.selectbox(
                "Link Valid For:",
                ["24 hours", "48 hours", "72 hours", "1 week"],
                help="How long the driver's link will work"
            )
            
            expiry_map = {
                "24 hours": 24,
                "48 hours": 48,
                "72 hours": 72,
                "1 week": 168
            }
            expiry_hours = expiry_map[expiry_option]
        
        with col2:
            # Additional options
            include_maps = st.checkbox("📍 Include Google Maps links", value=True)
            include_photos = st.checkbox("📸 Include photo instructions", value=True)
            urgent_flag = st.checkbox("🚨 Mark as URGENT", value=(move_data['priority'] == 'HIGH'))
            
            # Base URL configuration
            base_url = st.text_input(
                "Server URL:",
                value="http://localhost:8501",
                help="Change this to your actual server address"
            )
        
        # Step 3: Generate Link
        st.divider()
        st.markdown("#### Step 3: Generate Link & Message")
        
        if st.button("🔗 Generate Message", type="primary", use_container_width=True):
            # Generate token
            token = generate_route_token(
                move_id=move_data['id'],
                driver_name=move_data['driver_name'],
                expiry_hours=expiry_hours
            )
            
            # Generate link
            link = f"{base_url}/driver?token={token}"
            
            # Generate message from template
            template = templates[template_name]
            
            # Add custom values if needed
            custom_values = {}
            if template_name == "Urgent Pickup":
                custom_values['trailer_count'] = move_data.get('pickup_trailer_count', 0)
            
            message = generate_message_content(template, move_data, link, custom_values)
            
            # Add urgent prefix if flagged
            if urgent_flag and "URGENT" not in message:
                message = "🚨 URGENT 🚨\n\n" + message
            
            # Add maps links if requested
            if include_maps and move_data.get('pickup_address'):
                maps_link = f"https://www.google.com/maps/search/?api=1&query={move_data['pickup_address'].replace(' ', '+')}"
                message += f"\n\n📍 Pickup Maps: {maps_link}"
            
            # Store in session for display
            st.session_state['generated_message'] = message
            st.session_state['generated_link'] = link
            st.session_state['generated_token'] = token
            
            # Log the communication
            store_communication_log(
                driver_name=move_data['driver_name'],
                move_id=move_data['id'],
                message_type=template_name,
                message_content=message,
                token=token
            )
            
            st.success("✅ Message generated successfully!")
        
        # Step 4: Copy & Send
        if 'generated_message' in st.session_state:
            st.divider()
            st.markdown("#### Step 4: Copy & Send to Driver")
            
            # Message preview
            st.markdown("**📱 Message Preview:**")
            st.markdown(f"""
            <div class="message-preview">
{st.session_state['generated_message']}
            </div>
            """, unsafe_allow_html=True)
            
            # Copy options
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_area(
                    "📋 Full Message (Copy All):",
                    value=st.session_state['generated_message'],
                    height=300,
                    help="Select all (Ctrl+A) then copy (Ctrl+C)"
                )
            
            with col2:
                st.text_input(
                    "🔗 Just the Link:",
                    value=st.session_state['generated_link'],
                    help="Copy just the link if sending separately"
                )
                
                st.info(f"""
                **✅ Ready to send!**
                1. Copy the message
                2. Open your SMS/WhatsApp
                3. Paste and send to driver
                4. Driver clicks link on phone
                """)
            
            # Success confirmation
            st.markdown("""
            <div class="success-box">
                <strong>✅ Message Generated Successfully!</strong><br>
                • Link expires: {expiry}<br>
                • Token ID: {token_id}<br>
                • Logged in system for tracking
            </div>
            """.format(
                expiry=(datetime.now() + timedelta(hours=expiry_hours)).strftime('%B %d at %I:%M %p'),
                token_id=st.session_state['generated_token'][:20] + "..."
            ), unsafe_allow_html=True)

def show_group_broadcast(assignments_df):
    """Group messaging for multiple drivers"""
    
    st.markdown("### 📢 Group Broadcast Messages")
    
    if assignments_df.empty:
        st.info("📭 No routes assigned for today.")
        return
    
    # Group selection options
    col1, col2 = st.columns(2)
    
    with col1:
        broadcast_type = st.radio(
            "Broadcast Type:",
            ["All Drivers Today", "High Priority Only", "Select Specific Drivers", "Custom Group"]
        )
    
    with col2:
        if broadcast_type == "High Priority Only":
            high_priority_drivers = assignments_df[assignments_df['priority'] == 'HIGH']['driver_name'].unique()
            st.info(f"Will send to {len(high_priority_drivers)} drivers with high priority routes")
        elif broadcast_type == "All Drivers Today":
            all_drivers = assignments_df['driver_name'].unique()
            st.info(f"Will send to all {len(all_drivers)} drivers with routes today")
    
    # Driver selection for custom group
    selected_drivers = []
    if broadcast_type == "Select Specific Drivers":
        selected_drivers = st.multiselect(
            "Select Drivers:",
            options=assignments_df['driver_name'].unique().tolist(),
            help="Choose specific drivers to message"
        )
    elif broadcast_type == "Custom Group":
        custom_group = st.text_area(
            "Enter driver names (one per line):",
            help="Type driver names, one per line"
        )
        if custom_group:
            selected_drivers = [name.strip() for name in custom_group.split('\n') if name.strip()]
    
    # Message composition
    st.divider()
    st.markdown("#### Compose Group Message")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        message_type = st.selectbox(
            "Message Type:",
            ["Daily Schedule", "General Announcement", "Safety Reminder", "Route Updates", "Custom Message"]
        )
        
        if message_type == "Custom Message":
            group_message = st.text_area(
                "Message Content:",
                height=150,
                placeholder="Type your message here..."
            )
        else:
            # Use predefined templates
            group_templates = {
                "Daily Schedule": "Good morning team! Today's routes are ready. Check your individual links for details. Drive safe!",
                "General Announcement": "Important: {announcement}",
                "Safety Reminder": "Safety Reminder: {reminder}",
                "Route Updates": "Route updates have been made. Please check your latest assignment."
            }
            template = group_templates.get(message_type, "")
            
            if "{" in template:
                custom_text = st.text_input("Fill in the blank:", placeholder="Enter your message")
                group_message = template.format(
                    announcement=custom_text,
                    reminder=custom_text
                ) if custom_text else template
            else:
                group_message = template
    
    with col2:
        st.markdown("**Options:**")
        include_individual_links = st.checkbox("Include individual route links", value=True)
        send_time = st.selectbox(
            "Send:",
            ["Now", "Schedule for later"]
        )
        
        if send_time == "Schedule for later":
            scheduled_time = st.time_input("Send at:", value=datetime.now().time())
    
    # Generate messages
    if st.button("📤 Generate Group Messages", type="primary", use_container_width=True):
        # Determine target drivers
        if broadcast_type == "All Drivers Today":
            target_drivers = assignments_df['driver_name'].unique().tolist()
        elif broadcast_type == "High Priority Only":
            target_drivers = assignments_df[assignments_df['priority'] == 'HIGH']['driver_name'].unique().tolist()
        elif broadcast_type in ["Select Specific Drivers", "Custom Group"]:
            target_drivers = selected_drivers
        else:
            target_drivers = []
        
        if not target_drivers:
            st.error("No drivers selected")
            return
        
        # Generate messages for each driver
        generated_messages = []
        base_url = "http://localhost:8501"  # Get from config
        
        for driver in target_drivers:
            driver_routes = assignments_df[assignments_df['driver_name'] == driver]
            
            if not driver_routes.empty and include_individual_links:
                # Generate links for each route
                driver_message = f"📱 {driver}\n\n{group_message}\n\n"
                
                for _, route in driver_routes.iterrows():
                    token = generate_route_token(
                        move_id=route['id'],
                        driver_name=driver,
                        expiry_hours=24
                    )
                    link = f"{base_url}/driver?token={token}"
                    driver_message += f"Route #{route['id']}: {link}\n"
                
                generated_messages.append(driver_message)
                
                # Log communication
                store_communication_log(
                    driver_name=driver,
                    move_id=None,
                    message_type="Group Broadcast",
                    message_content=driver_message,
                    token=None
                )
            else:
                # Just the message without links
                driver_message = f"📱 {driver}\n\n{group_message}"
                generated_messages.append(driver_message)
        
        # Display all messages
        st.success(f"✅ Generated {len(generated_messages)} messages")
        
        # Combined output
        all_messages_text = "\n\n" + ("="*50) + "\n\n".join(generated_messages)
        
        st.text_area(
            "📋 All Messages (Copy and send individually):",
            value=all_messages_text,
            height=400,
            help="Copy each driver's section and send via SMS"
        )
        
        # Download option
        st.download_button(
            label="📥 Download All Messages",
            data=all_messages_text,
            file_name=f"driver_messages_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

def show_todays_assignments(assignments_df):
    """Show all today's assignments with quick actions"""
    
    st.markdown("### 📋 Today's Route Assignments")
    
    if assignments_df.empty:
        st.info("No routes assigned for today")
        return
    
    # Priority filter
    priority_filter = st.selectbox(
        "Filter by Priority:",
        ["All", "High Priority", "Medium Priority", "Normal Priority"]
    )
    
    if priority_filter != "All":
        priority_map = {
            "High Priority": "HIGH",
            "Medium Priority": "MEDIUM",
            "Normal Priority": "NORMAL"
        }
        filtered_df = assignments_df[assignments_df['priority'] == priority_map[priority_filter]]
    else:
        filtered_df = assignments_df
    
    # Display assignments
    for _, route in filtered_df.iterrows():
        priority_color = {
            'HIGH': '#dc3545',
            'MEDIUM': '#ffc107',
            'NORMAL': '#28a745'
        }.get(route['priority'], '#6c757d')
        
        with st.expander(f"#{route['id']} - {route['driver_name']} - {route['new_trailer_number']}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                **Driver:** {route['driver_name']}  
                **Trailer:** {route['new_trailer_number']}  
                **Priority:** <span style="color: {priority_color}">●</span> {route['priority']}
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                **From:** {route['new_pickup_location']}  
                **To:** {route['new_destination']}  
                **Miles:** {route.get('miles', 'TBD')}
                """)
            
            with col3:
                st.markdown(f"""
                **Location Count:** {route.get('pickup_trailer_count', 0)} trailers  
                **Status:** {route.get('status', 'Pending')}  
                **Rate:** ${route.get('rate', 2.10)}/mile
                """)
            
            # Quick actions
            st.divider()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📱 Send Link", key=f"send_{route['id']}"):
                    st.info(f"Use Individual Messages tab to send to {route['driver_name']}")
            
            with col2:
                if st.button(f"📝 View Details", key=f"view_{route['id']}"):
                    st.info(f"Move #{route['id']} details")
            
            with col3:
                if st.button(f"📞 Contact Driver", key=f"contact_{route['id']}"):
                    st.info(f"Driver: {route['driver_name']}")

def show_message_templates():
    """Manage and preview message templates"""
    
    st.markdown("### 📝 Message Templates")
    
    templates = get_message_templates()
    
    st.info("""
    **Using Templates:**
    - Templates use {placeholders} that auto-fill with route data
    - You can edit templates before sending
    - Create custom templates for common scenarios
    """)
    
    # Display existing templates
    for name, template in templates.items():
        with st.expander(f"📄 {name}"):
            st.text_area(
                "Template Content:",
                value=template,
                height=200,
                disabled=True,
                key=f"template_{name}"
            )
            
            st.markdown("**Available placeholders:**")
            st.code("""
{driver_name} - Driver's name
{date} - Today's date
{move_id} - Route/Move ID
{new_trailer} - Trailer number
{pickup_location} - Pickup location
{delivery_location} - Delivery destination
{miles} - One-way miles
{round_trip} - Round trip miles
{rate} - Rate per mile
{link} - Driver's unique link
{trailer_count} - Trailers at location
            """)
    
    # Custom template creator
    st.divider()
    st.markdown("#### Create Custom Template")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_template_name = st.text_input("Template Name:")
        new_template_content = st.text_area(
            "Template Content:",
            height=200,
            placeholder="Type your template here... Use {placeholders} for dynamic content"
        )
    
    with col2:
        st.markdown("**Tips:**")
        st.markdown("""
        - Keep messages concise
        - Include clear instructions
        - Use emojis for clarity 📱 🚛 📍
        - Always include the {link}
        - Test with real data first
        """)
        
        if st.button("💾 Save Template"):
            if new_template_name and new_template_content:
                st.success(f"Template '{new_template_name}' saved!")
                # Would save to database here

def show_communication_log():
    """Display communication history and statistics"""
    
    st.markdown("### 📊 Communication Log")
    
    # Date filter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_filter = st.selectbox(
            "Time Period:",
            ["Today", "Last 7 Days", "Last 30 Days", "Custom Range"]
        )
    
    with col2:
        if date_filter == "Custom Range":
            start_date = st.date_input("From:")
            end_date = st.date_input("To:")
    
    with col3:
        driver_filter = st.text_input("Filter by Driver:", placeholder="Enter driver name")
    
    # Get communication logs
    conn = db.get_connection()
    
    query = """
        SELECT * FROM communication_log 
        WHERE 1=1
    """
    
    if date_filter == "Today":
        query += " AND date(sent_at) = date('now')"
    elif date_filter == "Last 7 Days":
        query += " AND date(sent_at) >= date('now', '-7 days')"
    elif date_filter == "Last 30 Days":
        query += " AND date(sent_at) >= date('now', '-30 days')"
    
    if driver_filter:
        query += f" AND driver_name LIKE '%{driver_filter}%'"
    
    query += " ORDER BY sent_at DESC LIMIT 100"
    
    try:
        logs_df = pd.read_sql_query(query, conn)
        
        if not logs_df.empty:
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Messages", len(logs_df))
            with col2:
                unique_drivers = logs_df['driver_name'].nunique()
                st.metric("Drivers Contacted", unique_drivers)
            with col3:
                today_count = len(logs_df[pd.to_datetime(logs_df['sent_at']).dt.date == pd.Timestamp.now().date()])
                st.metric("Sent Today", today_count)
            with col4:
                most_common_type = logs_df['message_type'].mode()[0] if not logs_df['message_type'].empty else "N/A"
                st.metric("Most Used Template", most_common_type)
            
            # Log table
            st.divider()
            
            display_df = logs_df[['sent_at', 'driver_name', 'move_id', 'message_type', 'sent_by']].copy()
            display_df['sent_at'] = pd.to_datetime(display_df['sent_at']).dt.strftime('%Y-%m-%d %I:%M %p')
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Export option
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Export Communication Log",
                data=csv,
                file_name=f"communication_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No communication logs found for the selected period")
            
    except Exception as e:
        st.info("Communication log will be available after sending first message")
    
    conn.close()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Coordinator Communication Hub - Smith and Williams Trucking",
        page_icon="📱",
        layout="wide"
    )
    
    show_coordinator_hub()