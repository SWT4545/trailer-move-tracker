# Smith & Williams Trucking Branding Configuration

# Company Information
COMPANY_NAME = "Smith & Williams Trucking Solutions, LLC"
COMPANY_NAME_SHORT = "Smith & Williams Trucking"
APP_NAME = "Trailer Move Tracker"
COMPANY_MC = "MC#: 1276006"
COMPANY_DOT = "DOT#: 3675217"
COMPANY_CEO = "Brandon Smith"
COMPANY_CEO_PHONE = "951.437.5474"
COMPANY_CEO_EMAIL = "Brandon@smithwilliamstrucking.com"

# Company Taglines
PRIMARY_TAGLINE = "Your cargo. Our mission. Moving forward."
SECONDARY_TAGLINE = "Your freight, our commitment"
SHORT_TAGLINE = "Moving forward."  # For space-limited uses

# Email Disclaimer
EMAIL_DISCLAIMER = """
CONFIDENTIALITY NOTICE: This email and any attachments contain confidential and proprietary information intended solely for the use of the intended recipient(s). If you are not the intended recipient, you are hereby notified that any reading, use, disclosure, copying, or distribution of this email or its attachments is strictly prohibited. If you have received this email in error, please notify the sender immediately by reply email and delete this email and all copies from your system. Thank you.
"""

# Short disclaimer for signatures
SHORT_DISCLAIMER = "This email contains confidential information intended only for the addressee."

# Brand Colors
COLORS = {
    'primary_red': '#DC143C',  # Crimson Red
    'black': '#000000',
    'white': '#FFFFFF',
    'gray': '#808080',
    'light_gray': '#F5F5F5',
    'success_green': '#28a745',
    'warning_yellow': '#ffc107',
    'info_blue': '#17a2b8',
    'danger_red': '#dc3545',
    
    # Status Colors for Trailers
    'available': '#FFFFFF',
    'assigned': '#ffc107',  # Yellow for pending
    'completed': '#808080',  # Gray for completed
    'new_trailer': '#28a745',  # Green for newly added (< 24 hours)
}

# CSS Styles for Streamlit
CUSTOM_CSS = """
<style>
    /* Mobile-First Responsive Design */
    @media (max-width: 768px) {
        /* Mobile optimizations */
        .stApp {
            font-size: 16px !important;
        }
        
        /* Prevent iOS zoom on inputs */
        input, select, textarea {
            font-size: 16px !important;
            -webkit-appearance: none;
            appearance: none;
        }
        
        /* Larger touch targets */
        .stButton > button {
            min-height: 44px;
            width: 100%;
            margin: 0.5rem 0;
            font-size: 16px !important;
        }
        
        .stCheckbox {
            min-height: 44px;
        }
        
        .stSelectbox > div > div {
            min-height: 44px;
            font-size: 16px !important;
        }
        
        /* Responsive columns */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            padding: 0.25rem !important;
        }
        
        /* Stack columns on mobile */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0.5rem !important;
        }
        
        /* Responsive metrics */
        [data-testid="metric-container"] {
            padding: 0.5rem !important;
            min-width: auto !important;
        }
        
        /* Responsive header */
        .main-header {
            padding: 1rem !important;
        }
        
        .main-header h1 {
            font-size: 1.5rem !important;
        }
        
        /* Responsive sidebar */
        [data-testid="stSidebar"] {
            width: 250px !important;
            min-width: 250px !important;
        }
        
        /* Responsive tables */
        .stDataFrame {
            overflow-x: auto !important;
        }
        
        /* Responsive text */
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.3rem !important;
        }
        
        h3 {
            font-size: 1.1rem !important;
        }
        
        /* Hide less important elements on mobile */
        .css-1d391kg p {
            font-size: 14px !important;
        }
    }
    
    /* Tablet optimizations */
    @media (min-width: 768px) and (max-width: 1024px) {
        [data-testid="column"] {
            flex: 1 1 50% !important;
        }
        
        .stButton > button {
            min-width: 150px;
        }
    }
    
    /* Prevent text size adjustment */
    body {
        -webkit-text-size-adjust: 100%;
        text-size-adjust: 100%;
    }
    
    /* Main theme */
    .stApp {
        background-color: #FFFFFF;
        font-size: 14px;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #DC143C 0%, #8B0000 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        border: 2px solid #000000;
    }
    
    .company-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    
    .logo-icon {
        font-size: 3rem;
    }
    
    /* Card styling with depth */
    .trailer-card {
        background: white;
        border: 2px solid #000000;
        border-left: 5px solid #DC143C;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .trailer-card:hover {
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    .trailer-card.available {
        border-left-color: #28a745;
        border: 2px solid #000000;
        border-left: 5px solid #28a745;
    }
    
    .trailer-card.assigned {
        background-color: #fff3cd;
        border: 2px solid #000000;
        border-left: 5px solid #ffc107;
    }
    
    .trailer-card.completed {
        background-color: #f8f9fa;
        border: 2px solid #000000;
        border-left: 5px solid #6c757d;
        opacity: 0.8;
    }
    
    .trailer-card.completed .trailer-number {
        text-decoration: line-through;
    }
    
    /* Button styling with depth */
    .stButton > button {
        background: linear-gradient(135deg, #DC143C 0%, #B91C3C 100%);
        color: white;
        border: 2px solid #000000;
        padding: 0.5rem 1.5rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
        box-shadow: 0 4px 6px rgba(220, 20, 60, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #B91C3C 0%, #8B0000 100%);
        box-shadow: 0 6px 12px rgba(220, 20, 60, 0.4);
        transform: translateY(-2px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(220, 20, 60, 0.3);
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background: white;
        border: 2px solid #000000;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        min-width: 150px;
    }
    
    [data-testid="metric-container"] [data-testid="metric-label"] {
        color: #666;
        font-size: 0.85rem;
        font-weight: 600;
        white-space: nowrap;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #DC143C;
        font-size: 1.3rem;
        font-weight: bold;
        white-space: nowrap;
        overflow: visible;
    }
    
    /* Ensure metric containers don't overflow */
    [data-testid="stMetricValue"] div {
        white-space: nowrap !important;
        overflow: visible !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Data editor styling */
    .stDataFrame {
        border: 2px solid #000000;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Select box styling */
    .stSelectbox > div > div {
        border: 1px solid #000000;
    }
    
    /* Input field focus */
    .stTextInput > div > div > input {
        border: 1px solid #000000;
    }
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within,
    .stTextArea > div > div > textarea:focus {
        border: 2px solid #DC143C !important;
        box-shadow: 0 0 0 0.2rem rgba(220, 20, 60, 0.25) !important;
    }
    .stTextArea > div > div > textarea {
        border: 1px solid #000000;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #000000;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        color: #666;
        font-weight: 600;
        font-size: 14px;
        border: 1px solid #000000;
        border-bottom: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #DC143C;
        color: white;
    }
    
    /* Success/Error/Warning messages */
    .stAlert {
        border-radius: 8px;
        border: 2px solid #000000;
        border-left: 5px solid;
    }
    
    /* Count badges */
    .count-badge {
        background-color: #DC143C;
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        border: 1px solid #000000;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #DC143C;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border: 2px solid #000000;
        border-radius: 6px;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #DC143C;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #B91C3C;
    }
    
    /* Additional borders for forms and containers */
    .stForm {
        border: 2px solid #000000;
        border-radius: 8px;
        padding: 1.5rem;
        background: white;
        margin-bottom: 1rem;
    }
    
    /* Checkbox and radio button containers */
    .stCheckbox, .stRadio {
        padding: 0.5rem;
        border-left: 3px solid #DC143C;
    }
    
    /* Number input styling */
    .stNumberInput > div > div > input {
        border: 1px solid #000000;
    }
    
    /* Date input styling */
    .stDateInput > div > div > input {
        border: 1px solid #000000;
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        border: 2px dashed #000000;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Column containers */
    .css-1d391kg, .css-12w0qpk {
        padding: 0.5rem;
    }
    
    /* Force metrics to have adequate space */
    div[data-testid="column"] > div[data-testid="metric-container"] {
        min-width: 120px;
        width: 100%;
    }
    
    /* Adjust metric value container specifically */
    div[data-testid="metric-container"] > div {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    
    /* Sidebar styling with border */
    section[data-testid="stSidebar"] > div {
        border-right: 3px solid #000000;
    }
    
    /* Sidebar text sizing */
    .css-1d391kg p, .css-1d391kg label {
        font-size: 14px;
    }
    
    /* Download button special styling */
    .stDownloadButton > button {
        border: 2px solid #000000;
        background: linear-gradient(135deg, #28a745 0%, #218838 100%);
    }
    
    /* Info boxes */
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 0.5rem;
    }
    
    /* Header text styling */
    h1 {
        font-size: 1.75rem;
        border-bottom: 2px solid #000000;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    h2 {
        font-size: 1.5rem;
        border-bottom: 2px solid #000000;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    h3 {
        font-size: 1.25rem;
        border-bottom: 1px solid #000000;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Divider styling */
    hr {
        border: none;
        border-top: 2px solid #000000;
        margin: 1.5rem 0;
    }
</style>
"""

# Logo image path
import base64
import os

def get_logo_base64():
    """Get base64 encoded logo for embedding in HTML"""
    logo_path = "swt_logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def get_logo_html(width=60):
    """Get logo HTML image tag"""
    logo_base64 = get_logo_base64()
    if logo_base64:
        return f'<img src="data:image/png;base64,{logo_base64}" width="{width}" alt="SWT Logo" />'
    # Fallback to SVG if image not found
    return """
<svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
    <!-- Vinyl Record Base -->
    <circle cx="30" cy="30" r="28" fill="#000000" stroke="#DC143C" stroke-width="2"/>
    <circle cx="30" cy="30" r="20" fill="#1a1a1a"/>
    <circle cx="30" cy="30" r="12" fill="#000000"/>
    <circle cx="30" cy="30" r="5" fill="#DC143C"/>
    
    <!-- Crown -->
    <path d="M20 15 L25 10 L30 13 L35 10 L40 15 L38 25 L22 25 Z" 
          fill="#DC143C" stroke="#FFFFFF" stroke-width="1"/>
    
    <!-- Wings -->
    <path d="M10 30 Q5 25 8 20 Q12 22 15 25 L20 30 Z" 
          fill="#DC143C" stroke="#FFFFFF" stroke-width="1" opacity="0.8"/>
    <path d="M50 30 Q55 25 52 20 Q48 22 45 25 L40 30 Z" 
          fill="#DC143C" stroke="#FFFFFF" stroke-width="1" opacity="0.8"/>
</svg>
"""

# Email Templates
EMAIL_TEMPLATES = {
    'contractor_update': {
        'subject': 'Move Update - {company_name}',
        'body': '''Dear {contractor_name},

Please find attached the move update for {date_range}.

Summary:
- Completed Moves: {total_moves}
- Total Miles: {total_miles}
- Total Amount: {total_amount}

Please provide rate confirmation for the amount shown.

Thank you,
Smith and Williams Trucking
'''
    },
    'document_submission': {
        'subject': 'Required Documents Submission - Smith and Williams Trucking',
        'body': '''Dear {recipient_name},

Please find attached the required documents for your review.

Documents Included:
{document_list}

If you have any questions or need additional information, please don't hesitate to contact us.

Best regards,
Smith and Williams Trucking

This is an automated message from the Trailer Move Tracker system.
'''
    },
    'progress_report': {
        'subject': 'Daily Progress Report - Smith and Williams Trucking',
        'body': '''Daily Operations Summary for {date}

Performance Metrics:
- Routes Completed Today: {routes_today}
- Routes In Progress: {routes_progress}
- On-Time Delivery Rate: {on_time_rate}%
- Active Drivers: {active_drivers}

Trailer Status:
- Available New Trailers: {new_trailers}
- Available Old Trailers: {old_trailers}
- Trailers in Transit: {transit_trailers}

For detailed information, please access the Progress Dashboard.

Smith and Williams Trucking
Operations Department
'''
    }
}

def get_header_html():
    """Generate the branded header HTML"""
    return f"""
    <div class="main-header">
        <div class="company-logo">
            {get_logo_html(width=60)}
            <div>
                <h1 style="margin: 0; font-size: 1.8rem;">{COMPANY_NAME}</h1>
                <p style="margin: 0; font-size: 1rem; opacity: 0.9;">{APP_NAME}</p>
            </div>
        </div>
    </div>
    """

def get_trailer_card_html(trailer_number, location, status, days_available=None):
    """Generate HTML for a trailer card"""
    status_class = status.lower().replace(' ', '-')
    days_badge = f'<span class="count-badge">{days_available} days</span>' if days_available else ''
    
    return f"""
    <div class="trailer-card {status_class}">
        <h3 class="trailer-number" style="margin: 0; color: #000;">{trailer_number}</h3>
        <p style="margin: 0.5rem 0; color: #666;">{location}</p>
        {days_badge}
    </div>
    """

def apply_branding(st):
    """Apply branding to Streamlit app"""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(get_header_html(), unsafe_allow_html=True)