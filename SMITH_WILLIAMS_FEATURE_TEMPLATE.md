# Smith & Williams Trucking - Reusable Feature Template
## For Future Application Development

### 🎨 THEME & BRANDING MODULE
```python
# Dark Professional Theme with Red Accents
- Primary Background: #0E0E0E (Near black)
- Secondary Background: #1A1A1A (Dark gray)
- Accent Color: #DC143C (Crimson red)
- Border Accent: #8B0000 (Dark red)
- Text: #FFFFFF (White)
- Success: Green indicators
- Warning: Yellow indicators
- Error: Red indicators

# Logo Placement
- Login page: Centered above login form
- Main app: Top of sidebar with company name
- Reports: Header of PDF documents
- File: swt_logo_white.png (white version for dark background)

# CSS Implementation:
st.markdown("""
<style>
    .stApp { background-color: #0E0E0E; }
    h1 { 
        color: #FFFFFF; 
        border-bottom: 2px solid #DC143C; 
        padding-bottom: 10px; 
    }
    div[data-testid="metric-container"] {
        background-color: #1A1A1A;
        border: 1px solid #DC143C;
        border-radius: 5px;
        padding: 10px;
    }
    section[data-testid="stSidebar"] {
        background-color: #1A1A1A;
        border-right: 2px solid #8B0000;
    }
</style>
""", unsafe_allow_html=True)
```

### 🔐 AUTHENTICATION MODULE
```python
# Premium Login Page Features:
- Branded header with logo
- Professional login form
- Demo credentials dropdown
- Role-based access control
- Session management
- Remember me option (optional)

# User Roles Structure:
ROLES = {
    'business_administrator': {
        'access': ['all_features'],
        'can_edit': True,
        'can_delete': True,
        'view_financial': True
    },
    'operations_coordinator': {
        'access': ['operations', 'drivers', 'moves'],
        'can_edit': True,
        'can_delete': False,
        'view_financial': False
    },
    'driver': {
        'access': ['my_routes', 'upload_pod'],
        'can_edit': False,
        'can_delete': False,
        'view_financial': False
    }
}
```

### 📊 DASHBOARD MODULE
```python
# Executive/Admin Dashboard:
- Total moves (today/week/month)
- Revenue metrics with trends
- Pending payments from factoring
- Driver payment status
- Critical alerts

# Operations Dashboard:
- Active moves status
- Available trailers
- Driver availability
- Pending assignments
- Today's schedule

# Driver Dashboard:
- My assigned moves
- Earnings (today/week/total)
- POD upload status
- Route information
- Payment history
```

### 🚛 TRAILER MANAGEMENT MODULE
```python
# Features:
- Add trailer pairs (new from base, old at location)
- Automatic location capture
- Status tracking (available/assigned/completed)
- Trailer history log
- Quick search and filters
- Bulk import option

# Database Schema:
trailers_table = {
    'id': 'INTEGER PRIMARY KEY',
    'trailer_number': 'TEXT UNIQUE',
    'trailer_type': 'TEXT (new/old)',
    'current_location': 'TEXT',
    'status': 'TEXT',
    'paired_trailer_id': 'INTEGER',
    'added_date': 'TIMESTAMP'
}
```

### 📍 LOCATION MANAGEMENT MODULE
```python
# Features:
- Auto-populate from trailer entries
- Manual location addition
- Address validation
- Mileage matrix caching
- Frequent locations list
- Google Maps integration

# Location Structure:
{
    'location_title': 'Customer Name/ID',
    'street_address': '123 Main St',
    'city': 'Memphis',
    'state': 'TN',
    'zip_code': '38103',
    'coordinates': {'lat': 35.1495, 'lng': -90.0490}
}
```

### 🗺️ MILEAGE CALCULATOR MODULE
```python
# Google Maps Integration:
- API-based distance calculation
- Route visualization
- Caching for repeated routes
- Round-trip calculations
- Proof screenshots for reports

# Payment Calculation:
base_rate = 2.10  # per mile
factoring_fee = 0.03  # 3%
driver_pay = miles * base_rate * (1 - factoring_fee)
```

### 📋 MOVE ASSIGNMENT MODULE
```python
# Workflow:
1. Select trailer pair
2. Assign driver
3. Set pickup/delivery times
4. Calculate mileage and pay
5. Generate driver message
6. Create tracking link

# Driver Message Template:
"Move #{move_id}
📍 Pick up NEW trailer at Fleet Memphis
📍 Deliver to {location}
📍 Return with OLD trailer
💰 Pay: ${amount}
📱 Details: {tracking_link}"
```

### 👤 DRIVER PORTAL MODULE
```python
# Mobile-Optimized Features:
- My moves list with status
- Route details with map
- Earnings dashboard
- POD upload interface
- Picture upload (pickup/delivery)
- Digital signature capture
- Payment history

# Responsive Design:
- Touch-friendly buttons
- Large text for mobile
- Swipe navigation
- Offline capability
- Auto-save drafts
```

### 📸 POD UPLOAD MODULE
```python
# Features:
- Direct camera access
- Multiple file upload
- Image compression
- Automatic categorization
- Manual coordinator upload backup
- Verification system

# Upload Requirements:
- POD document (required)
- Pickup photo (required)
- Delivery photo (required)
- Damage photos (optional)
- Notes field
```

### 💰 PAYMENT TRACKING MODULE
```python
# Factoring Company Integration:
- Rate confirmation generation
- POD package assembly
- Submission tracking
- Payment confirmation
- Driver payment distribution
- Payment history reports

# Workflow:
1. Compile move documentation
2. Send to factoring company
3. Track submission status
4. Confirm payment received
5. Calculate driver payments
6. Mark as paid
```

### 📧 COMMUNICATION MODULE
```python
# Email Features:
- Template system
- Bulk sending
- Signature management
- Attachment handling
- Delivery tracking

# SMS Features (when available):
- Driver notifications
- Move updates
- Payment confirmations
- Emergency alerts
```

### 📊 REPORTING MODULE
```python
# Client Reports:
- Move summary with dates
- Trailer locations
- Mileage proof
- Cost breakdown
- PDF generation with branding

# Internal Reports:
- Driver performance
- Revenue analysis
- Route efficiency
- Payment reconciliation
```

### 🎓 TRAINING/WALKTHROUGH MODULE
```python
# Interactive Walkthrough:
- Role-based tutorials
- Step-by-step guides
- Tooltip hints
- Video tutorials (optional)
- Progress tracking

# Topics:
1. System overview
2. Adding trailers
3. Creating moves
4. Driver communication
5. POD processing
6. Payment tracking
```

### 📱 MOBILE OPTIMIZATION
```python
# Responsive Design Rules:
- Minimum button size: 44x44px
- Font size: 16px minimum
- Touch targets: 8px spacing
- Collapsible sidebars
- Swipe gestures
- Portrait/landscape support

# Platform Support:
- iOS Safari
- Android Chrome
- Tablet optimization
- Desktop browsers
```

### 🔧 UTILITY FUNCTIONS
```python
# Common Utilities:
- Date/time formatting
- Currency formatting
- Distance calculations
- Status indicators
- Progress bars
- Loading states
- Error handling
- Data validation
```

### 📂 DATABASE STRUCTURE
```python
# Core Tables:
- users (authentication)
- trailers (inventory)
- locations (addresses)
- moves (assignments)
- drivers (personnel)
- payments (financial)
- documents (uploads)
- activity_log (audit)
```

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Core Setup
- [ ] Authentication system
- [ ] Database initialization
- [ ] Theme implementation
- [ ] Basic navigation

### Phase 2: Operations
- [ ] Trailer management
- [ ] Location management
- [ ] Move creation
- [ ] Driver assignment

### Phase 3: Driver Features
- [ ] Driver portal
- [ ] POD uploads
- [ ] Route viewing
- [ ] Payment tracking

### Phase 4: Administration
- [ ] Payment processing
- [ ] Report generation
- [ ] Email communications
- [ ] System monitoring

### Phase 5: Polish
- [ ] Mobile optimization
- [ ] Training system
- [ ] Performance tuning
- [ ] Production deployment

## 🎯 USAGE INSTRUCTIONS

To implement any feature module:

1. **Choose modules needed** for your specific application
2. **Copy the relevant code blocks** from this template
3. **Customize the configuration** for your use case
4. **Maintain the theme consistency** across all modules
5. **Test on all target platforms** (mobile, tablet, desktop)

## 🔑 KEY SUCCESS FACTORS

1. **Simplicity**: Keep interfaces clean and intuitive
2. **Mobile-First**: Design for phone/tablet primary use
3. **Automation**: Minimize manual data entry
4. **Reliability**: Ensure offline capability and data persistence
5. **Branding**: Consistent Smith & Williams identity throughout