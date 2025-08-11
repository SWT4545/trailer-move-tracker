"""
Comprehensive Onboarding and Training System
Smith and Williams Trucking
Mobile-Optimized Design
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import branding
import time

# Job Descriptions Database
JOB_DESCRIPTIONS = {
    'executive': {
        'title': 'CEO/Executive',
        'department': 'Executive Leadership',
        'reports_to': 'Board of Directors',
        'salary_range': '$150,000 - $250,000',
        'employment_type': 'Full-Time',
        'summary': """
        The CEO/Executive provides strategic leadership and oversees all operations of Smith and Williams Trucking. 
        This role requires making high-level decisions about policy and strategy while ensuring the company's 
        financial success and operational excellence.
        """,
        'responsibilities': [
            'Set company vision, strategy, and long-term goals',
            'Oversee all departments and ensure alignment with company objectives',
            'Make final decisions on major contracts and partnerships',
            'Review and approve budgets and financial reports',
            'Represent the company to stakeholders and clients',
            'Ensure regulatory compliance and safety standards',
            'Drive innovation and continuous improvement',
            'Build and maintain relationships with key customers'
        ],
        'requirements': [
            'Bachelor\'s degree in Business, Logistics, or related field (MBA preferred)',
            '10+ years of executive experience in transportation/logistics',
            'Proven track record of business growth and profitability',
            'Strong leadership and decision-making skills',
            'Excellent communication and negotiation abilities',
            'Deep understanding of DOT regulations and compliance',
            'Experience with fleet management and operations',
            'Strategic thinking and problem-solving capabilities'
        ],
        'benefits': [
            'Competitive executive compensation package',
            'Performance-based bonuses',
            'Company vehicle',
            'Comprehensive health insurance',
            '401(k) with company match',
            'Paid time off and holidays',
            'Professional development opportunities'
        ]
    },
    'admin': {
        'title': 'System Administrator',
        'department': 'Information Technology',
        'reports_to': 'CEO/Executive',
        'salary_range': '$70,000 - $95,000',
        'employment_type': 'Full-Time',
        'summary': """
        The System Administrator manages and maintains all technology systems for Smith and Williams Trucking, 
        ensuring smooth operations of the Trailer Move Tracker and supporting all users with technical needs.
        """,
        'responsibilities': [
            'Manage and maintain the Trailer Move Tracker system',
            'Create and manage user accounts and permissions',
            'Ensure data security and system backups',
            'Troubleshoot technical issues for all users',
            'Generate system reports and analytics',
            'Implement system updates and improvements',
            'Train users on system features',
            'Monitor system performance and uptime'
        ],
        'requirements': [
            'Bachelor\'s degree in Computer Science or related field',
            '3+ years of system administration experience',
            'Experience with database management (SQL)',
            'Knowledge of web applications and cloud services',
            'Strong problem-solving and analytical skills',
            'Excellent communication skills',
            'Ability to work independently',
            'On-call availability for system emergencies'
        ],
        'benefits': [
            'Competitive salary',
            'Health, dental, and vision insurance',
            '401(k) retirement plan',
            'Paid training and certifications',
            'Flexible work arrangements',
            'Company laptop and equipment',
            'Professional development budget'
        ]
    },
    'operations_coordinator': {
        'title': 'Operations Coordinator',
        'department': 'Operations',
        'reports_to': 'Operations Manager',
        'salary_range': '$50,000 - $70,000',
        'employment_type': 'Full-Time',
        'summary': """
        The Operations Coordinator is responsible for the day-to-day coordination of trailer movements, 
        driver assignments, and route optimization. This role is critical to ensuring efficient operations 
        and excellent customer service.
        """,
        'responsibilities': [
            'Coordinate and assign drivers to routes daily',
            'Monitor route progress and handle issues',
            'Communicate with customers about deliveries',
            'Optimize routes for efficiency and cost-effectiveness',
            'Process and submit documents to contractors',
            'Generate operational reports for management',
            'Manage trailer inventory and availability',
            'Train and supervise Operations Specialists',
            'Ensure compliance with delivery schedules',
            'Handle driver communications and support'
        ],
        'requirements': [
            'High school diploma or equivalent (Associate\'s degree preferred)',
            '2+ years of logistics or dispatch experience',
            'Strong organizational and multitasking abilities',
            'Excellent communication skills',
            'Proficiency with computer systems and software',
            'Ability to work under pressure',
            'Problem-solving and decision-making skills',
            'Knowledge of DOT regulations helpful'
        ],
        'benefits': [
            'Competitive hourly wage or salary',
            'Health insurance options',
            '401(k) plan',
            'Paid time off',
            'Performance bonuses',
            'Career advancement opportunities',
            'On-the-job training'
        ]
    },
    'operations_specialist': {
        'title': 'Operations Specialist',
        'department': 'Operations',
        'reports_to': 'Operations Coordinator',
        'salary_range': '$35,000 - $45,000',
        'employment_type': 'Full-Time',
        'summary': """
        The Operations Specialist supports the Operations Coordinator by maintaining accurate data in the 
        Trailer Move Tracker system. This entry-level position is perfect for someone looking to start 
        a career in logistics and transportation.
        """,
        'responsibilities': [
            'Enter new and old trailer information accurately',
            'Maintain location database with current information',
            'Update trailer status and availability',
            'Verify data accuracy and fix errors',
            'Support Operations Coordinator with daily tasks',
            'Monitor location trailer counts',
            'Generate basic operational reports',
            'Assist with customer inquiries as needed'
        ],
        'requirements': [
            'High school diploma or equivalent',
            'Strong attention to detail',
            'Basic computer skills',
            'Good typing speed and accuracy',
            'Ability to follow procedures',
            'Team player attitude',
            'Willingness to learn',
            'Reliable and punctual'
        ],
        'benefits': [
            'Competitive starting wage',
            'Health insurance after 90 days',
            '401(k) eligibility after 1 year',
            'Paid training program',
            'Career growth opportunities',
            'Supportive team environment',
            'Performance reviews and raises'
        ]
    },
    'driver': {
        'title': 'Professional Truck Driver',
        'department': 'Transportation',
        'reports_to': 'Operations Coordinator',
        'salary_range': '$60,000 - $85,000 (based on miles)',
        'employment_type': 'Full-Time / Contract',
        'summary': """
        Professional Truck Drivers are the backbone of Smith and Williams Trucking, responsible for 
        safely transporting trailers between locations while maintaining excellent customer service 
        and compliance with all regulations.
        """,
        'responsibilities': [
            'Safely operate commercial vehicles',
            'Transport trailers between designated locations',
            'Perform pre-trip and post-trip inspections',
            'Document deliveries with photos and paperwork',
            'Maintain accurate logs and records',
            'Communicate with dispatch about route status',
            'Ensure cargo security and safety',
            'Provide professional customer service',
            'Comply with DOT regulations and hours of service',
            'Report vehicle maintenance needs'
        ],
        'requirements': [
            'Valid CDL Class A license',
            'Clean driving record',
            'DOT medical certificate',
            'Minimum 2 years OTR experience preferred',
            'Ability to lift 50+ pounds',
            'Pass drug screening and background check',
            'Good communication skills',
            'Smartphone for route documentation'
        ],
        'benefits_company': [
            'Competitive pay per mile ($2.10/mile)',
            'Health insurance available',
            'Direct deposit weekly pay',
            'Performance bonuses',
            'Newer equipment',
            'Home time options',
            'Referral bonuses',
            'Safety bonuses'
        ],
        'benefits_contractor': [
            'High pay per mile rate',
            'Weekly settlements',
            'Fuel card program',
            'Quick pay options',
            'Consistent freight',
            'Dedicated routes available',
            'Owner-operator support'
        ]
    }
}

# Onboarding Checklists by Role
ONBOARDING_CHECKLISTS = {
    'operations_coordinator': {
        'day_1': [
            'Complete HR paperwork and I-9 verification',
            'Receive login credentials and system access',
            'Tour of office and introduction to team',
            'Review company policies and procedures',
            'Set up workstation and equipment',
            'Complete initial system training module',
            'Shadow current coordinator for overview'
        ],
        'week_1': [
            'Complete all training modules',
            'Learn route assignment process',
            'Practice driver communication protocols',
            'Understand customer requirements',
            'Review trailer management system',
            'Learn document processing procedures',
            'Practice report generation'
        ],
        'month_1': [
            'Independently handle morning assignments',
            'Manage driver issues and concerns',
            'Build relationships with regular drivers',
            'Master route optimization techniques',
            'Handle customer communications',
            'Generate weekly reports',
            'Train on emergency procedures'
        ]
    },
    'operations_specialist': {
        'day_1': [
            'Complete new hire paperwork',
            'Receive system login credentials',
            'Complete Operations Specialist training',
            'Learn trailer number formats',
            'Practice data entry with supervisor',
            'Review accuracy standards',
            'Understand role responsibilities'
        ],
        'week_1': [
            'Complete all 6 training modules',
            'Pass certification test (80%+)',
            'Shadow experienced specialist',
            'Practice adding trailers independently',
            'Learn location management',
            'Understand priority system',
            'Review common errors to avoid'
        ],
        'month_1': [
            'Maintain 98%+ accuracy rate',
            'Handle morning data entry independently',
            'Identify and report data issues',
            'Support coordinator effectively',
            'Suggest process improvements',
            'Cross-train on related tasks',
            'Build speed while maintaining accuracy'
        ]
    },
    'driver': {
        'day_1': [
            'Complete driver application and paperwork',
            'Provide CDL and medical certificate',
            'Complete drug screen and background check',
            'Review safety policies and procedures',
            'Receive driver portal login',
            'Download mobile app for routes',
            'Complete equipment orientation'
        ],
        'week_1': [
            'Complete safety training videos',
            'Learn photo documentation requirements',
            'Practice with route tracking system',
            'Understand pay structure',
            'Review delivery procedures',
            'Complete first supervised route',
            'Learn paperwork requirements'
        ],
        'month_1': [
            'Complete routes independently',
            'Maintain on-time delivery rate',
            'Master photo documentation',
            'Build customer relationships',
            'Optimize route efficiency',
            'Participate in safety meetings',
            'Achieve performance targets'
        ]
    }
}

def show_mobile_header():
    """Mobile-optimized header"""
    st.markdown("""
    <style>
    /* Mobile-responsive styles */
    @media (max-width: 768px) {
        .stButton > button {
            width: 100%;
            margin: 0.25rem 0;
            padding: 0.75rem;
            font-size: 1rem;
        }
        
        .stSelectbox > div > div {
            font-size: 1rem;
        }
        
        .stTextInput > div > div > input {
            font-size: 16px !important; /* Prevents zoom on iOS */
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.3rem !important;
        }
        
        h3 {
            font-size: 1.1rem !important;
        }
        
        .main-header {
            padding: 1rem !important;
        }
        
        .job-card {
            margin: 0.5rem 0;
            padding: 1rem;
        }
        
        [data-testid="column"] {
            padding: 0.25rem !important;
        }
        
        .stMetric {
            padding: 0.5rem;
        }
        
        [data-testid="metric-container"] {
            padding: 0.5rem;
        }
        
        /* Fix for mobile sidebar */
        [data-testid="stSidebar"] {
            min-width: 250px;
            max-width: 250px;
        }
        
        /* Larger touch targets */
        .stCheckbox {
            min-height: 44px;
        }
        
        /* Better spacing for mobile */
        .element-container {
            margin: 0.5rem 0;
        }
    }
    
    /* Additional mobile fixes */
    @media (max-width: 480px) {
        .stColumns {
            gap: 0.5rem !important;
        }
        
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        
        [data-testid="column"] {
            width: 100% !important;
            flex: none !important;
        }
    }
    
    /* Ensure readable font sizes on all devices */
    body {
        -webkit-text-size-adjust: 100%;
        text-size-adjust: 100%;
    }
    
    /* Fix input zoom on iOS */
    input, select, textarea {
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Mobile-friendly header
    st.markdown(f"""
    <div class="main-header" style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #DC143C 0%, #8B0000 100%); color: white; border-radius: 10px;">
        <h2 style="margin: 0; font-size: 1.3rem;">Smith and Williams Trucking</h2>
        <p style="margin: 0.5rem 0; font-size: 1rem;">Onboarding & Training Portal</p>
    </div>
    """, unsafe_allow_html=True)

def show_job_descriptions():
    """Display job descriptions page"""
    show_mobile_header()
    
    st.title("💼 Job Descriptions")
    
    # Mobile-friendly selection
    if st.checkbox("📱 Use mobile view", value=True):
        # Mobile dropdown
        role_options = {
            'CEO/Executive': 'executive',
            'System Administrator': 'admin',
            'Operations Coordinator': 'operations_coordinator',
            'Operations Specialist': 'operations_specialist',
            'Professional Driver': 'driver'
        }
        
        selected_role_name = st.selectbox(
            "Select Position to View",
            list(role_options.keys())
        )
        selected_role = role_options[selected_role_name]
        
        # Display selected job description
        job = JOB_DESCRIPTIONS[selected_role]
        
        # Mobile-optimized card
        st.markdown(f"""
        <div class="job-card" style="background: white; border: 2px solid #DC143C; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
            <h3 style="color: #DC143C; margin-bottom: 0.5rem;">{job['title']}</h3>
            <p style="margin: 0.25rem 0;"><strong>Department:</strong> {job['department']}</p>
            <p style="margin: 0.25rem 0;"><strong>Reports to:</strong> {job['reports_to']}</p>
            <p style="margin: 0.25rem 0;"><strong>Salary:</strong> {job['salary_range']}</p>
            <p style="margin: 0.25rem 0;"><strong>Type:</strong> {job['employment_type']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Expandable sections for mobile
        with st.expander("📋 Position Summary"):
            st.write(job['summary'])
        
        with st.expander("✅ Key Responsibilities"):
            for resp in job['responsibilities']:
                st.write(f"• {resp}")
        
        with st.expander("📚 Requirements"):
            for req in job['requirements']:
                st.write(f"• {req}")
        
        with st.expander("🎁 Benefits"):
            if selected_role == 'driver':
                st.write("**Company Drivers:**")
                for benefit in job['benefits_company']:
                    st.write(f"• {benefit}")
                st.write("\n**Contract Drivers:**")
                for benefit in job['benefits_contractor']:
                    st.write(f"• {benefit}")
            else:
                for benefit in job['benefits']:
                    st.write(f"• {benefit}")
    
    else:
        # Desktop tabs view
        tabs = st.tabs(list(role_options.keys()))
        
        for idx, (tab, (role_name, role_key)) in enumerate(zip(tabs, role_options.items())):
            with tab:
                display_job_description(role_key)

def display_job_description(role_key):
    """Display a single job description"""
    job = JOB_DESCRIPTIONS[role_key]
    
    # Header information
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {job['title']}")
        st.markdown(f"**Department:** {job['department']}")
        st.markdown(f"**Reports to:** {job['reports_to']}")
    with col2:
        st.markdown(f"**Salary Range:** {job['salary_range']}")
        st.markdown(f"**Employment Type:** {job['employment_type']}")
    
    st.divider()
    
    # Position summary
    st.markdown("#### Position Summary")
    st.write(job['summary'])
    
    # Responsibilities
    st.markdown("#### Key Responsibilities")
    for resp in job['responsibilities']:
        st.write(f"• {resp}")
    
    # Requirements
    st.markdown("#### Requirements")
    for req in job['requirements']:
        st.write(f"• {req}")
    
    # Benefits
    st.markdown("#### Benefits & Compensation")
    if role_key == 'driver':
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Company Drivers:**")
            for benefit in job['benefits_company']:
                st.write(f"• {benefit}")
        with col2:
            st.markdown("**Contract Drivers:**")
            for benefit in job['benefits_contractor']:
                st.write(f"• {benefit}")
    else:
        for benefit in job['benefits']:
            st.write(f"• {benefit}")

def show_onboarding_checklist(role):
    """Display onboarding checklist for a specific role"""
    show_mobile_header()
    
    st.title("📋 Onboarding Checklist")
    
    role_titles = {
        'operations_coordinator': 'Operations Coordinator',
        'operations_specialist': 'Operations Specialist',
        'driver': 'Professional Driver'
    }
    
    if role not in ONBOARDING_CHECKLISTS:
        st.info("Onboarding checklist not available for this role yet.")
        return
    
    st.markdown(f"### {role_titles.get(role, role.title())} Onboarding")
    
    checklist = ONBOARDING_CHECKLISTS[role]
    
    # Progress tracking
    if f'onboarding_progress_{role}' not in st.session_state:
        st.session_state[f'onboarding_progress_{role}'] = {
            'day_1': [],
            'week_1': [],
            'month_1': []
        }
    
    progress = st.session_state[f'onboarding_progress_{role}']
    
    # Calculate overall progress
    total_tasks = sum(len(tasks) for tasks in checklist.values())
    completed_tasks = sum(len(completed) for completed in progress.values())
    progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Progress bar
    st.progress(progress_percentage / 100)
    st.markdown(f"**Overall Progress: {progress_percentage:.0f}%** ({completed_tasks}/{total_tasks} tasks)")
    
    # Mobile-friendly tabs
    tab1, tab2, tab3 = st.tabs(["📅 Day 1", "📅 Week 1", "📅 Month 1"])
    
    with tab1:
        st.markdown("### First Day Tasks")
        display_checklist_section('day_1', checklist['day_1'], progress, role)
    
    with tab2:
        st.markdown("### First Week Goals")
        display_checklist_section('week_1', checklist['week_1'], progress, role)
    
    with tab3:
        st.markdown("### First Month Objectives")
        display_checklist_section('month_1', checklist['month_1'], progress, role)
    
    # Action buttons
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📧 Email Checklist", use_container_width=True):
            st.info("Checklist will be emailed to your registered address")
    
    with col2:
        if st.button("📥 Download PDF", use_container_width=True):
            st.info("PDF download will be available soon")
    
    # Completion certificate
    if progress_percentage == 100:
        st.balloons()
        st.success("🎉 Congratulations! You've completed all onboarding tasks!")
        generate_onboarding_certificate(role)

def display_checklist_section(period, tasks, progress, role):
    """Display a checklist section with mobile-friendly checkboxes"""
    for idx, task in enumerate(tasks):
        task_key = f"{role}_{period}_{idx}"
        
        # Check if task is completed
        is_completed = task in progress[period]
        
        # Create checkbox with larger touch target for mobile
        if st.checkbox(
            task,
            value=is_completed,
            key=task_key,
            help="Tap to mark as complete"
        ):
            if task not in progress[period]:
                progress[period].append(task)
                st.success(f"✅ Task completed: {task[:30]}...")
        else:
            if task in progress[period]:
                progress[period].remove(task)

def generate_onboarding_certificate(role):
    """Generate onboarding completion certificate"""
    role_titles = {
        'operations_coordinator': 'Operations Coordinator',
        'operations_specialist': 'Operations Specialist',
        'driver': 'Professional Driver'
    }
    
    st.markdown(f"""
    <div style="border: 3px solid #DC143C; padding: 2rem; border-radius: 10px; text-align: center; background: white; margin: 1rem 0;">
        <h2 style="color: #DC143C; margin-bottom: 1rem;">Onboarding Complete!</h2>
        <h3 style="color: #000; margin-bottom: 1rem;">{role_titles.get(role, role.title())}</h3>
        
        <p style="font-size: 1.1rem; margin: 1rem;">
        This certifies successful completion of all onboarding requirements
        </p>
        
        <p style="margin: 2rem 0;">
        <strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}<br>
        <strong>Department:</strong> Operations<br>
        <strong>Status:</strong> Ready for Work
        </p>
        
        <div style="margin-top: 2rem; padding-top: 1rem; border-top: 2px solid #DC143C;">
            <p style="font-style: italic;">Smith and Williams Trucking<br>Human Resources Department</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_role_training(role):
    """Show role-specific training modules"""
    show_mobile_header()
    
    st.title("🎓 Role-Based Training")
    
    # Training modules by role
    training_modules = {
        'executive': [
            {'name': 'Strategic Planning & Vision', 'duration': '2 hours', 'type': 'Video'},
            {'name': 'Financial Management & Analysis', 'duration': '3 hours', 'type': 'Interactive'},
            {'name': 'Regulatory Compliance Overview', 'duration': '1.5 hours', 'type': 'Document'},
            {'name': 'Leadership & Team Building', 'duration': '2 hours', 'type': 'Workshop'},
            {'name': 'Customer Relationship Management', 'duration': '1 hour', 'type': 'Video'}
        ],
        'admin': [
            {'name': 'System Architecture Overview', 'duration': '2 hours', 'type': 'Technical'},
            {'name': 'Database Management & Backups', 'duration': '3 hours', 'type': 'Hands-on'},
            {'name': 'User Management & Security', 'duration': '2 hours', 'type': 'Interactive'},
            {'name': 'Troubleshooting Common Issues', 'duration': '2 hours', 'type': 'Workshop'},
            {'name': 'Report Generation & Analytics', 'duration': '1.5 hours', 'type': 'Practical'}
        ],
        'operations_coordinator': [
            {'name': 'Route Planning & Optimization', 'duration': '3 hours', 'type': 'Interactive'},
            {'name': 'Driver Management & Communication', 'duration': '2 hours', 'type': 'Video'},
            {'name': 'Customer Service Excellence', 'duration': '1.5 hours', 'type': 'Workshop'},
            {'name': 'Document Processing & Compliance', 'duration': '2 hours', 'type': 'Hands-on'},
            {'name': 'Crisis Management & Problem Solving', 'duration': '2 hours', 'type': 'Scenario'},
            {'name': 'Team Leadership & Training', 'duration': '1.5 hours', 'type': 'Video'}
        ],
        'operations_specialist': [
            {'name': 'Data Entry Best Practices', 'duration': '1 hour', 'type': 'Interactive'},
            {'name': 'Trailer Management System', 'duration': '2 hours', 'type': 'Hands-on'},
            {'name': 'Location Tracking & Priorities', 'duration': '1.5 hours', 'type': 'Practical'},
            {'name': 'Error Detection & Correction', 'duration': '1 hour', 'type': 'Workshop'},
            {'name': 'Daily Workflow Optimization', 'duration': '1.5 hours', 'type': 'Scenario'},
            {'name': 'Communication & Teamwork', 'duration': '1 hour', 'type': 'Video'}
        ],
        'driver': [
            {'name': 'Safety Procedures & Compliance', 'duration': '3 hours', 'type': 'Video'},
            {'name': 'Mobile App & Route Tracking', 'duration': '1 hour', 'type': 'Hands-on'},
            {'name': 'Photo Documentation Requirements', 'duration': '30 mins', 'type': 'Practical'},
            {'name': 'Customer Service at Delivery', 'duration': '1 hour', 'type': 'Video'},
            {'name': 'Hours of Service & Logs', 'duration': '2 hours', 'type': 'Interactive'},
            {'name': 'Vehicle Inspection & Maintenance', 'duration': '1.5 hours', 'type': 'Practical'}
        ]
    }
    
    if role not in training_modules:
        st.info("Training modules are being developed for this role.")
        return
    
    modules = training_modules[role]
    
    # Progress tracking
    if f'training_progress_{role}' not in st.session_state:
        st.session_state[f'training_progress_{role}'] = []
    
    completed = st.session_state[f'training_progress_{role}']
    progress = len(completed) / len(modules) if modules else 0
    
    # Display progress
    st.progress(progress)
    st.markdown(f"**Training Progress: {progress*100:.0f}%** ({len(completed)}/{len(modules)} modules)")
    
    # Display modules in mobile-friendly cards
    for idx, module in enumerate(modules):
        is_completed = idx in completed
        
        # Mobile-optimized module card
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="padding: 0.5rem; background: {'#d4edda' if is_completed else '#f8f9fa'}; 
                            border-left: 4px solid {'#28a745' if is_completed else '#DC143C'}; 
                            border-radius: 4px; margin: 0.5rem 0;">
                    <strong>{module['name']}</strong><br>
                    <small>Duration: {module['duration']} | Type: {module['type']}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if not is_completed:
                    if st.button(f"Start", key=f"start_{role}_{idx}", use_container_width=True):
                        st.info(f"Starting: {module['name']}")
                        # In production, this would launch the actual training
                        
                        # Simulate completion for demo
                        if st.button(f"Complete", key=f"complete_{role}_{idx}"):
                            completed.append(idx)
                            st.success("Module completed!")
                            st.rerun()
                else:
                    st.success("✅ Done")
    
    # Completion actions
    if progress == 1.0:
        st.balloons()
        st.success("🎓 All training modules completed! You're ready to begin work!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📜 Get Certificate", use_container_width=True):
                generate_training_certificate(role)
        with col2:
            if st.button("📊 View Score", use_container_width=True):
                st.info("Average Score: 95%")

def generate_training_certificate(role):
    """Generate training completion certificate"""
    st.markdown(f"""
    <div style="border: 3px solid #DC143C; padding: 1.5rem; border-radius: 10px; text-align: center; background: white;">
        <h2 style="color: #DC143C;">Training Certificate</h2>
        <p style="font-size: 1.1rem; margin: 1rem;">
        This certifies completion of all required training modules for<br>
        <strong style="font-size: 1.3rem;">{role.replace('_', ' ').title()}</strong>
        </p>
        <p>Date: {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    """, unsafe_allow_html=True)

def show_onboarding_portal():
    """Main onboarding portal interface"""
    show_mobile_header()
    
    st.title("👋 Welcome to Smith and Williams Trucking!")
    
    # Get user role from session
    user_role = st.session_state.get('user_role', 'operations_specialist')
    user_name = st.session_state.get('user_name', 'New Team Member')
    
    st.markdown(f"""
    ### Hello, {user_name}!
    Welcome to your personalized onboarding portal. We're excited to have you join our team!
    """)
    
    # Mobile-friendly navigation
    st.markdown("### 📱 Quick Access")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💼 Job Description", use_container_width=True):
            st.session_state['onboarding_page'] = 'job_description'
            st.rerun()
        
        if st.button("📋 Onboarding Checklist", use_container_width=True):
            st.session_state['onboarding_page'] = 'checklist'
            st.rerun()
    
    with col2:
        if st.button("🎓 Training Modules", use_container_width=True):
            st.session_state['onboarding_page'] = 'training'
            st.rerun()
        
        if st.button("📚 Resources", use_container_width=True):
            st.session_state['onboarding_page'] = 'resources'
            st.rerun()
    
    st.divider()
    
    # Display selected page
    page = st.session_state.get('onboarding_page', 'overview')
    
    if page == 'job_description':
        show_job_descriptions()
    elif page == 'checklist':
        show_onboarding_checklist(user_role)
    elif page == 'training':
        show_role_training(user_role)
    elif page == 'resources':
        show_resources()
    else:
        show_onboarding_overview(user_role)

def show_onboarding_overview(role):
    """Show onboarding overview and timeline"""
    st.markdown("### 🗓️ Your First 30 Days")
    
    # Timeline
    timeline_data = {
        'Day 1': '🏢 Orientation & Setup',
        'Week 1': '📚 Core Training',
        'Week 2': '👥 Shadowing & Practice',
        'Week 3': '✅ Independent Work',
        'Week 4': '📊 Performance Review'
    }
    
    # Mobile-friendly timeline display
    for time, task in timeline_data.items():
        st.markdown(f"""
        <div style="padding: 0.75rem; margin: 0.5rem 0; background: white; border-left: 4px solid #DC143C; border-radius: 4px;">
            <strong>{time}</strong>: {task}
        </div>
        """, unsafe_allow_html=True)
    
    # Important contacts
    st.markdown("### 📞 Important Contacts")
    
    contacts = {
        'HR Department': '(555) 123-4567',
        'IT Support': '(555) 123-4568',
        'Operations Manager': '(555) 123-4569',
        'Emergency': '911'
    }
    
    for name, number in contacts.items():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{name}**")
        with col2:
            st.markdown(f"📞 {number}")

def show_resources():
    """Show onboarding resources and documents"""
    st.markdown("### 📚 Onboarding Resources")
    
    resources = {
        'Employee Handbook': '📘 Company policies and procedures',
        'Benefits Guide': '🏥 Health insurance and retirement plans',
        'Safety Manual': '⚠️ Safety procedures and protocols',
        'System Guide': '💻 Trailer Move Tracker user guide',
        'Directory': '📞 Company directory and contacts'
    }
    
    for title, description in resources.items():
        with st.expander(f"{title}"):
            st.write(description)
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📥 Download", key=f"dl_{title}", use_container_width=True):
                    st.info(f"Downloading {title}...")
            with col2:
                if st.button(f"👁️ View", key=f"view_{title}", use_container_width=True):
                    st.info(f"Opening {title}...")

# Main app function
def show_onboarding_system():
    """Main entry point for onboarding system"""
    # Ensure mobile responsiveness
    st.set_page_config(
        page_title="Onboarding - Smith and Williams Trucking",
        page_icon="👋",
        layout="wide",
        initial_sidebar_state="collapsed"  # Better for mobile
    )
    
    # Navigation
    menu = st.selectbox(
        "Select Section",
        ["🏠 Onboarding Portal", "💼 Job Descriptions", "📋 Checklists", "🎓 Training"],
        label_visibility="collapsed"
    )
    
    if menu == "🏠 Onboarding Portal":
        show_onboarding_portal()
    elif menu == "💼 Job Descriptions":
        show_job_descriptions()
    elif menu == "📋 Checklists":
        role = st.session_state.get('user_role', 'operations_specialist')
        show_onboarding_checklist(role)
    elif menu == "🎓 Training":
        role = st.session_state.get('user_role', 'operations_specialist')
        show_role_training(role)

if __name__ == "__main__":
    show_onboarding_system()