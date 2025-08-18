"""
Interactive Training System for Trailer Move Tracker
Complete user guide with role-based tutorials
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from PIL import Image
import auth_config
import branding

# Page configuration
page_icon = "📚"
if os.path.exists("swt_logo.png"):
    try:
        page_icon = Image.open("swt_logo.png")
    except:
        pass

st.set_page_config(
    page_title="Training Center - Smith and Williams Trucking",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Training modules for each role
TRAINING_MODULES = {
    'executive': {
        'title': 'Executive Complete Training',
        'modules': [
            'login_basics',
            'executive_responsibilities',
            'dashboard_overview',
            'financial_management',
            'user_management',
            'reports_exports',
            'security_best_practices'
        ]
    },
    'admin': {
        'title': 'Administrator Complete Training',
        'modules': [
            'login_basics',
            'admin_responsibilities',
            'dashboard_overview',
            'trailer_management',
            'add_moves',
            'financial_management',
            'user_management',
            'password_management',
            'reports_exports',
            'security_best_practices'
        ]
    },
    'operations_coordinator': {
        'title': 'Operations Coordinator Training Guide',
        'modules': [
            'login_basics',
            'coordinator_responsibilities',
            'coordinator_how_to',
            'dashboard_overview',
            'trailer_management',
            'add_moves',
            'driver_management',
            'location_management',
            'photo_documentation',
            'reports_exports',
            'password_management'
        ]
    },
    'operations_specialist': {
        'title': 'Operations Specialist Training Guide',
        'modules': [
            'login_basics',
            'specialist_responsibilities',
            'specialist_how_to',
            'dashboard_overview',
            'trailer_management',
            'add_moves',
            'data_verification',
            'location_counts',
            'password_management'
        ]
    },
    'viewer': {
        'title': 'Viewer Training Guide',
        'modules': [
            'login_basics',
            'viewer_responsibilities',
            'dashboard_overview',
            'progress_monitoring',
            'password_management'
        ]
    },
    'client': {
        'title': 'Client Access Guide',
        'modules': [
            'access_instructions',
            'client_responsibilities',
            'progress_dashboard',
            'understanding_metrics'
        ]
    }
}

# Detailed content for each module
MODULE_CONTENT = {
    'executive_responsibilities': {
        'title': '👔 Executive Role & Responsibilities',
        'duration': '10 minutes',
        'content': """
        ### Your Role as Executive/CEO
        
        As the Executive, you have **COMPLETE CONTROL** over the entire system.
        
        #### 🎯 Primary Responsibilities:
        
        **1. Strategic Oversight**
        - Monitor overall business performance
        - Review financial metrics and profitability
        - Make high-level decisions on operations
        - Set company policies and procedures
        
        **2. System Administration**
        - Override any user action or setting
        - Access all areas of the system
        - View sensitive financial data
        - Manage user permissions and access
        
        **3. Financial Management**
        - Approve large expenditures
        - Review profit margins and costs
        - Monitor accounts receivable
        - Oversee factor fee negotiations
        
        **4. Quality Control**
        - Ensure data accuracy and integrity
        - Review operational efficiency
        - Monitor customer satisfaction
        - Oversee compliance and safety
        
        #### 🔑 Special Executive Powers:
        
        ✅ **Full Override Authority**
        - Change any data entry
        - Override system restrictions
        - Access locked accounts
        - Bypass approval workflows
        
        ✅ **Complete Visibility**
        - View all passwords (only Executive can do this)
        - See deleted records
        - Access audit logs
        - Monitor all user activity
        
        ✅ **System Control**
        - Lock/unlock the entire system
        - Perform emergency shutdowns
        - Reset all user sessions
        - Modify core configurations
        
        #### 📊 Key Metrics You Should Monitor:
        
        **Daily:**
        - Total moves in progress
        - Revenue generated
        - Outstanding payments
        - System issues or errors
        
        **Weekly:**
        - Driver performance
        - Location efficiency
        - Customer satisfaction
        - Cash flow status
        
        **Monthly:**
        - Profitability analysis
        - Growth trends
        - Operational costs
        - System usage statistics
        """
    },
    'admin_responsibilities': {
        'title': '👨‍💼 Administrator Role & Responsibilities',
        'duration': '15 minutes',
        'content': """
        ### Your Role as Administrator
        
        As an Administrator, you manage the day-to-day system operations and user access.
        
        #### 🎯 Primary Responsibilities:
        
        **1. User Management**
        - Create and manage user accounts
        - Assign appropriate roles
        - Reset passwords when needed
        - Monitor user activity
        - Deactivate terminated employees
        
        **2. System Maintenance**
        - Perform daily backups
        - Monitor system performance
        - Troubleshoot user issues
        - Maintain data integrity
        - Update system configurations
        
        **3. Financial Operations**
        - Generate invoices
        - Process payments
        - Manage factor fees
        - Export financial reports
        - Monitor accounts receivable
        
        **4. Data Management**
        - Import/export data
        - Maintain database
        - Archive old records
        - Ensure data accuracy
        - Generate reports
        
        #### 📋 Daily Checklist:
        
        **Morning Tasks:**
        - [ ] Check system status
        - [ ] Review overnight errors
        - [ ] Verify backup completed
        - [ ] Check user access requests
        - [ ] Review unpaid invoices
        
        **Throughout the Day:**
        - [ ] Monitor active moves
        - [ ] Assist users with issues
        - [ ] Process new user requests
        - [ ] Update trailer statuses
        - [ ] Generate required reports
        
        **End of Day:**
        - [ ] Review day's activities
        - [ ] Ensure all data saved
        - [ ] Check tomorrow's schedule
        - [ ] Lock sensitive records
        - [ ] Verify system backup
        
        #### ⚠️ Important Restrictions:
        
        Unlike the Executive, you CANNOT:
        - View other users' passwords
        - Override executive decisions
        - Delete financial records without approval
        - Modify system core settings
        - Access executive-only reports
        """
    },
    'coordinator_responsibilities': {
        'title': '📋 Operations Coordinator Role & Responsibilities',
        'duration': '20 minutes',
        'content': """
        ### Your Role as Operations Coordinator
        
        You are the backbone of daily operations, managing trailer movements and coordinating with drivers.
        
        #### 🎯 Primary Responsibilities:
        
        **1. Route Planning & Coordination**
        - Plan efficient routes for drivers
        - Prioritize pickups based on location counts
        - Coordinate trailer swaps and deliveries
        - Monitor route progress in real-time
        - Adjust plans for delays or issues
        
        **2. Driver Management**
        - Assign drivers to routes
        - Communicate pickup/delivery instructions
        - Monitor driver performance
        - Handle driver questions and issues
        - Ensure proper documentation
        
        **3. Location Management**
        - Track trailer counts at each location
        - Identify high-priority locations (5+ trailers)
        - Coordinate with customers on pickups
        - Update location information
        - Monitor location capacity
        
        **4. Documentation & Compliance**
        - Ensure drivers submit 12 photos per route
        - Verify paperwork completion
        - Track rate confirmations
        - Monitor compliance with procedures
        - Generate operational reports
        
        #### 📊 Priority Management System:
        
        **🔴 URGENT (Immediate Action)**
        - Locations with 5+ old trailers
        - Delayed deliveries
        - Driver emergencies
        - Customer complaints
        
        **🟡 HIGH (Within 24 Hours)**
        - Locations with 3-4 old trailers
        - Upcoming deliveries
        - Driver scheduling conflicts
        - Documentation issues
        
        **🟢 NORMAL (Within 48 Hours)**
        - Locations with 1-2 old trailers
        - Routine pickups
        - Standard documentation
        - Regular reports
        
        #### 🚚 Daily Workflow:
        
        **6:00 AM - Morning Setup**
        1. Review overnight trailer arrivals
        2. Check location trailer counts
        3. Identify priority pickups
        4. Plan day's routes
        
        **7:00 AM - Driver Dispatch**
        1. Assign drivers to routes
        2. Send route instructions
        3. Provide special instructions
        4. Confirm driver availability
        
        **8:00 AM - 5:00 PM - Active Monitoring**
        1. Track driver progress
        2. Handle customer calls
        3. Adjust routes as needed
        4. Verify photo submissions
        5. Update trailer statuses
        
        **5:00 PM - End of Day**
        1. Review completed routes
        2. Check missing documentation
        3. Plan next day's priorities
        4. Generate daily report
        
        #### 📱 Communication Guidelines:
        
        **With Drivers:**
        - Clear, concise instructions
        - Include all addresses and contacts
        - Specify photo requirements
        - Provide backup contacts
        
        **With Customers:**
        - Professional and courteous
        - Confirm pickup/delivery times
        - Address concerns promptly
        - Document all interactions
        
        **With Management:**
        - Daily status updates
        - Flag urgent issues immediately
        - Provide performance metrics
        - Suggest improvements
        """
    },
    'specialist_responsibilities': {
        'title': '📝 Operations Specialist Role & Responsibilities',
        'duration': '15 minutes',
        'content': """
        ### Your Role as Operations Specialist
        
        You ensure data accuracy and support the Operations Coordinator with administrative tasks.
        
        #### 🎯 Primary Responsibilities:
        
        **1. Data Entry & Management**
        - Enter new trailer information accurately
        - Update trailer locations and statuses
        - Add driver assignments
        - Input mileage and route data
        - Maintain customer information
        
        **2. Quality Assurance**
        - Verify data accuracy before saving
        - Check for duplicate entries
        - Validate trailer numbers (8 characters)
        - Ensure all required fields completed
        - Cross-reference with paperwork
        
        **3. Documentation Support**
        - Organize submitted photos
        - File rate confirmations
        - Track paperwork status
        - Scan and upload documents
        - Maintain digital records
        
        **4. Location Tracking**
        - Monitor trailer counts at locations
        - Update location statuses
        - Flag high-priority locations
        - Track old trailer accumulation
        - Report capacity issues
        
        #### ✅ Data Entry Standards:
        
        **Trailer Numbers:**
        - Always 8 characters (e.g., 18V12345)
        - Check for duplicates before adding
        - Verify against paperwork
        - Use correct prefix codes
        
        **Location Information:**
        - Full address required
        - Include contact details
        - Note special instructions
        - Update trailer counts
        - Flag access restrictions
        
        **Driver Assignments:**
        - Verify driver availability
        - Check license status
        - Confirm contact information
        - Note any restrictions
        - Track assignment history
        
        #### 🔍 Common Errors to Avoid:
        
        **❌ DON'T:**
        - Enter partial trailer numbers
        - Skip location details
        - Forget to update counts
        - Create duplicate entries
        - Leave required fields blank
        
        **✅ DO:**
        - Double-check all entries
        - Verify with source documents
        - Update in real-time
        - Communicate discrepancies
        - Maintain accurate records
        
        #### 📋 Daily Tasks:
        
        **Morning (8:00-10:00 AM)**
        - [ ] Process overnight paperwork
        - [ ] Enter new trailer arrivals
        - [ ] Update location counts
        - [ ] Verify yesterday's entries
        
        **Midday (10:00 AM-2:00 PM)**
        - [ ] Enter active route data
        - [ ] Process driver submissions
        - [ ] Update trailer statuses
        - [ ] File documentation
        
        **Afternoon (2:00-5:00 PM)**
        - [ ] Complete day's data entry
        - [ ] Run accuracy checks
        - [ ] Prepare next day's forms
        - [ ] Generate entry reports
        
        #### 💡 Pro Tips:
        
        1. **Use Templates:** Create standard entries for common routes
        2. **Batch Process:** Group similar entries together
        3. **Verify Twice:** Check before and after saving
        4. **Ask Questions:** When in doubt, ask the Coordinator
        5. **Document Issues:** Keep notes on problems encountered
        """
    },
    'viewer_responsibilities': {
        'title': '👁️ Viewer Role & Responsibilities',
        'duration': '10 minutes',
        'content': """
        ### Your Role as Viewer
        
        You have read-only access to monitor operations and track progress.
        
        #### 🎯 Primary Responsibilities:
        
        **1. Monitoring Operations**
        - View active trailer moves
        - Track completion status
        - Monitor driver assignments
        - Review location statuses
        
        **2. Reporting Observations**
        - Identify potential issues
        - Note unusual patterns
        - Report concerns to management
        - Suggest improvements
        
        **3. Supporting Decision Making**
        - Provide status updates
        - Share dashboard views
        - Export allowed reports
        - Assist with data analysis
        
        #### 🚫 Access Limitations:
        
        You CANNOT:
        - Edit any data
        - Add new entries
        - Delete records
        - Access financial information
        - Modify user settings
        - Generate invoices
        
        You CAN:
        - View all dashboards
        - Export basic reports
        - Monitor progress
        - Track performance metrics
        - View historical data
        
        #### 📊 Key Areas to Monitor:
        
        - Active moves dashboard
        - Completion rates
        - Location trailer counts
        - Driver availability
        - Route progress
        - Performance trends
        """
    },
    'client_responsibilities': {
        'title': '🤝 Client Access & Expectations',
        'duration': '5 minutes',
        'content': """
        ### Your Role as Client
        
        You have limited access to view progress on your shipments.
        
        #### 🎯 What You Can Access:
        
        **Progress Dashboard**
        - View your active shipments
        - Track completion status
        - See estimated timelines
        - Monitor delivery progress
        
        **Performance Metrics**
        - On-time delivery rate
        - Route completion times
        - Service reliability
        - Historical performance
        
        #### 🚫 Privacy & Security:
        
        You CANNOT see:
        - Other clients' data
        - Financial information
        - Driver personal details
        - Internal notes
        - Pricing information
        - System settings
        
        #### 📞 Getting Help:
        
        For assistance:
        1. Contact your account manager
        2. Use provided support email
        3. Reference your client ID
        4. Include shipment numbers
        
        #### 📊 Understanding Your Dashboard:
        
        - Green = On schedule
        - Yellow = Minor delay
        - Red = Attention needed
        - Blue = Completed
        """
    },
    'coordinator_how_to': {
        'title': '🛠️ How-To Guide for Operations Coordinators',
        'duration': '25 minutes',
        'content': """
        ### Complete How-To Guide for Daily Operations
        
        #### 📍 How to Prioritize Location Pickups
        
        **Step 1: Check Location Dashboard**
        ```
        Navigate to: Dashboard → Location Summary
        Sort by: Old Trailer Count (Descending)
        ```
        
        **Step 2: Apply Priority Rules**
        - 🔴 5+ trailers = Schedule TODAY
        - 🟡 3-4 trailers = Schedule within 24 hours
        - 🟢 1-2 trailers = Normal scheduling
        - ⚪ 0 trailers = No action needed
        
        **Step 3: Create Pickup Route**
        1. Group nearby high-priority locations
        2. Calculate optimal route sequence
        3. Estimate time for each stop
        4. Add buffer time for delays
        
        **Example Route Planning:**
        ```
        Morning Route (8 AM start):
        1. Chicago (8 trailers) - 45 min
        2. Joliet (5 trailers) - 30 min
        3. Aurora (3 trailers) - 30 min
        Return to Fleet - 60 min
        Total: 2 hrs 45 min
        ```
        
        #### 🚚 How to Assign Drivers Effectively
        
        **Step 1: Check Driver Availability**
        - View Driver Dashboard
        - Check current assignments
        - Verify hours of service
        - Review equipment status
        
        **Step 2: Match Driver to Route**
        Consider:
        - [ ] Driver location
        - [ ] Experience level
        - [ ] Equipment type needed
        - [ ] Customer preferences
        - [ ] Previous performance
        
        **Step 3: Send Assignment**
        1. Click "Assign Driver"
        2. Select driver from list
        3. Add route details:
           - Pickup locations
           - Delivery destinations
           - Special instructions
           - Photo requirements (12 total)
        4. Send via system notification
        
        #### 📸 How to Manage Photo Documentation
        
        **Required Photos (12 per route):**
        1. **New Trailer Pickup (5 photos)**
           - Front view
           - Left side
           - Right side
           - Rear view
           - VIN/ID plate
        
        2. **New Trailer Delivery (5 photos)**
           - Delivery location
           - Trailer positioned
           - Customer signature
           - Paperwork
           - Final placement
        
        3. **Old Trailer Pickup (1 photo)**
           - Loaded trailer at pickup
        
        4. **Old Trailer Return (1 photo)**
           - Trailer at Fleet yard
        
        **Verification Process:**
        1. Driver uploads photos
        2. System timestamps each photo
        3. You verify completeness
        4. Flag any missing/unclear photos
        5. Request retakes if needed
        
        #### 📞 How to Handle Common Situations
        
        **Situation: Driver Can't Find Trailer**
        1. Verify trailer number with driver
        2. Check last known location
        3. Contact location manager
        4. Update system if moved
        5. Provide new directions
        
        **Situation: Location Has More Trailers Than Expected**
        1. Get exact count from driver
        2. Update location count immediately
        3. Photo document all trailers
        4. Arrange additional pickups if needed
        5. Notify management of discrepancy
        
        **Situation: Customer Refuses Delivery**
        1. Get reason from driver
        2. Contact customer directly
        3. Document refusal reason
        4. Arrange alternative:
           - Return to Fleet
           - Deliver to alternate location
           - Hold for next day
        5. Update all parties
        
        **Situation: Equipment Breakdown**
        1. Ensure driver safety
        2. Get exact location
        3. Arrange roadside assistance
        4. Dispatch replacement driver
        5. Update delivery schedules
        6. Notify affected customers
        
        #### 📊 How to Generate Reports
        
        **Daily Operations Report:**
        1. Go to Reports → Daily Summary
        2. Select date range (usually today)
        3. Include:
           - [ ] Completed moves
           - [ ] In-progress routes
           - [ ] Location counts
           - [ ] Driver performance
        4. Export as PDF
        5. Email to management
        
        **Weekly Performance Report:**
        1. Reports → Weekly Analysis
        2. Review metrics:
           - Completion rate
           - Average delivery time
           - Photo compliance
           - Customer feedback
        3. Identify trends
        4. Note improvements needed
        5. Submit recommendations
        """
    },
    'specialist_how_to': {
        'title': '🛠️ How-To Guide for Operations Specialists',
        'duration': '20 minutes',
        'content': """
        ### Complete How-To Guide for Data Management
        
        #### 📝 How to Add a New Trailer Move
        
        **Step 1: Gather Information**
        Before starting, ensure you have:
        - [ ] Trailer number(s)
        - [ ] Pickup location and address
        - [ ] Delivery destination
        - [ ] Driver assignment
        - [ ] Rate confirmation
        
        **Step 2: Navigate to Add Move**
        ```
        Main Menu → Add New Move
        ```
        
        **Step 3: Enter Trailer Details**
        
        **New Trailer Section:**
        1. Enter trailer number (8 characters)
        2. Select/add pickup location
        3. Select/add destination
        4. Verify addresses are complete
        
        **Old Trailer Section (if applicable):**
        1. Enter old trailer number
        2. Select pickup location
        3. Note current trailer count
        4. Add to location count
        
        **Step 4: Assign Driver**
        1. Select from dropdown
        2. Or add new driver:
           - Full name
           - Phone number
           - Email address
           - License number
        3. Set assignment date
        
        **Step 5: Calculate Mileage**
        1. System auto-calculates if cached
        2. Otherwise enter manually:
           - One-way miles
           - Round trip (usually 2x one-way)
        3. Verify with Google Maps if needed
        
        **Step 6: Review and Save**
        1. Check all fields for accuracy
        2. Verify trailer numbers
        3. Confirm addresses
        4. Save the move
        5. Note the generated Move ID
        
        #### 🔍 How to Verify Data Accuracy
        
        **Daily Verification Checklist:**
        
        **1. Trailer Number Validation**
        ```
        Correct: 18V12345 (8 characters)
        Wrong: 18V1234 (too short)
        Wrong: 18V123456 (too long)
        ```
        
        **2. Check for Duplicates**
        1. Search for trailer number
        2. Review recent entries
        3. Compare with paperwork
        4. Flag any duplicates found
        
        **3. Location Verification**
        - Full address present?
        - ZIP code correct?
        - Contact info included?
        - Special instructions noted?
        
        **4. Cross-Reference Documents**
        1. Compare with rate confirmation
        2. Verify against BOL
        3. Check driver paperwork
        4. Match photo submissions
        
        #### 📍 How to Update Location Counts
        
        **When Adding Old Trailer:**
        1. Select location from dropdown
        2. System shows current count
        3. Add trailer increases count by 1
        4. Verify new count is correct
        5. Flag if 5+ trailers (high priority)
        
        **When Removing Trailer:**
        1. Find the trailer move
        2. Mark as "Picked Up"
        3. System decreases count by 1
        4. Verify count accuracy
        5. Update priority status
        
        **Manual Count Correction:**
        1. Go to Location Management
        2. Select location
        3. Click "Adjust Count"
        4. Enter correct number
        5. Add note explaining discrepancy
        6. Save and notify Coordinator
        
        #### 📊 How to Handle Data Issues
        
        **Missing Information:**
        1. Flag incomplete entry
        2. Contact source (driver/coordinator)
        3. Get missing details
        4. Update record
        5. Document resolution
        
        **Incorrect Entry:**
        1. Locate the wrong entry
        2. Click Edit
        3. Correct the information
        4. Add note about correction
        5. Save changes
        6. Verify accuracy
        
        **System Errors:**
        1. Screenshot error message
        2. Note what you were doing
        3. Try again in 5 minutes
        4. If persists, contact admin
        5. Document in error log
        
        #### 💡 Data Entry Best Practices
        
        **Speed + Accuracy Tips:**
        
        1. **Use Tab Key**
           - Tab between fields
           - Faster than clicking
           - Maintains flow
        
        2. **Copy/Paste Carefully**
           - Verify after pasting
           - Check for extra spaces
           - Ensure complete copy
        
        3. **Batch Similar Entries**
           - Group by location
           - Process same driver together
           - Use previous as template
        
        4. **Regular Saves**
           - Save every 5 entries
           - Prevent data loss
           - Allow for verification
        
        5. **End-of-Day Review**
           - Check day's entries
           - Run duplicate check
           - Verify counts match
           - Generate summary report
        """
    },
    'photo_documentation': {
        'title': '📸 Photo Documentation Requirements',
        'duration': '15 minutes',
        'content': """
        ### Complete Photo Documentation Guide
        
        #### 📋 Why Photos Are Required
        
        Photos provide:
        - Proof of delivery
        - Condition documentation
        - Location verification
        - Damage protection
        - Customer disputes resolution
        - Insurance requirements
        
        #### 📸 Required Photos: 12 Per Route
        
        ### 1️⃣ New Trailer Pickup (5 Photos)
        
        **Photo 1: Front View**
        - Entire front of trailer visible
        - Trailer number clearly shown
        - Include tractor if attached
        - Check for damage
        
        **Photo 2: Driver Side**
        - Full length of left side
        - Include wheels and undercarriage
        - Note any damage or markings
        - Capture DOT numbers
        
        **Photo 3: Passenger Side**
        - Full length of right side
        - Check for damage
        - Include any placards
        - Verify door seals
        
        **Photo 4: Rear View**
        - Doors closed and sealed
        - License plate visible
        - Note seal numbers
        - Check door condition
        
        **Photo 5: VIN/ID Plate**
        - Close-up of VIN plate
        - Manufacturer's plate
        - Model and year visible
        - Serial number clear
        
        ### 2️⃣ New Trailer Delivery (5 Photos)
        
        **Photo 6: Delivery Location**
        - Wide shot of delivery site
        - Include building/landmarks
        - Show access roads
        - Capture address if visible
        
        **Photo 7: Trailer Positioned**
        - Trailer in final position
        - Show proper placement
        - Include dock if applicable
        - Verify correct location
        
        **Photo 8: Customer Signature**
        - Signed paperwork
        - Time stamp visible
        - Name printed clearly
        - Company representative
        
        **Photo 9: Completed Paperwork**
        - BOL or delivery receipt
        - All fields completed
        - Stamps/seals visible
        - Special instructions noted
        
        **Photo 10: Final Placement**
        - Trailer unhitched
        - Landing gear down
        - Properly positioned
        - Ready for customer use
        
        ### 3️⃣ Old Trailer Pickup (1 Photo)
        
        **Photo 11: Loaded Old Trailer**
        - Shows loaded condition
        - Trailer number visible
        - Pickup location clear
        - Sealed and secured
        
        ### 4️⃣ Old Trailer Return (1 Photo)
        
        **Photo 12: Fleet Yard Return**
        - Trailer at Fleet location
        - Final position
        - Available for next use
        - Inspection complete
        
        #### 📱 Photo Upload Process
        
        **For Drivers:**
        1. Take all required photos
        2. Check clarity before moving
        3. Upload through driver app
        4. Verify upload successful
        5. Keep copies for 24 hours
        
        **For Coordinators:**
        1. Receive photo notification
        2. Review all 12 photos
        3. Verify requirements met
        4. Request retakes if needed
        5. Approve and file
        
        #### ⚠️ Common Photo Issues
        
        **Problem: Blurry Photos**
        - Solution: Clean camera lens
        - Steady hand or rest phone
        - Good lighting
        - Retake immediately
        
        **Problem: Missing Information**
        - Solution: Include all required elements
        - Step back for wider shots
        - Get closer for details
        - Verify before leaving
        
        **Problem: Wrong Angle**
        - Solution: Follow photo guide
        - Straight-on shots
        - Avoid extreme angles
        - Include reference points
        
        #### ✅ Photo Quality Checklist
        
        Before submitting:
        - [ ] All 12 photos taken
        - [ ] Trailer numbers visible
        - [ ] No blurry images
        - [ ] Proper lighting
        - [ ] Timestamps included
        - [ ] Locations identifiable
        - [ ] Paperwork legible
        - [ ] Damage documented
        """
    },
    'data_verification': {
        'title': '🔍 Data Verification Process',
        'duration': '15 minutes',
        'content': """
        ### Data Verification & Quality Control
        
        #### 🎯 Why Verification Matters
        
        **Impact of Errors:**
        - Wrong location = Wasted fuel and time
        - Wrong trailer = Driver can't find equipment
        - Missing data = Delayed payments
        - Duplicates = Confusion and double billing
        
        #### ✅ Verification Checklist
        
        **1. Trailer Number Format**
        ```
        Standard Format: XXY##### 
        Example: 18V12345
        
        Where:
        - XX = Year (18, 19, 20, etc.)
        - Y = Type code (V, T, R, etc.)
        - ##### = 5-digit sequence
        
        Total: ALWAYS 8 characters
        ```
        
        **2. Required Fields Check**
        - [ ] Trailer number (8 chars)
        - [ ] Pickup location
        - [ ] Destination
        - [ ] Driver assigned
        - [ ] Date assigned
        - [ ] Mileage entered
        
        **3. Logical Validation**
        - Dates make sense (not future/past)
        - Miles reasonable for route
        - Location exists in system
        - Driver available for assignment
        
        #### 🔍 How to Find Errors
        
        **Step 1: Visual Scan**
        - Look for obvious typos
        - Check number patterns
        - Verify complete entries
        - Note missing data
        
        **Step 2: System Search**
        ```sql
        Search for duplicates:
        - Enter trailer number
        - Check last 7 days
        - Review results
        - Flag any matches
        ```
        
        **Step 3: Cross-Reference**
        - Compare with paperwork
        - Check against photos
        - Verify with dispatch notes
        - Match driver reports
        
        #### 🛠️ Fixing Common Errors
        
        **Error: Duplicate Entry**
        1. Find both entries
        2. Determine which is correct
        3. Delete duplicate
        4. Merge any unique data
        5. Note in comments
        
        **Error: Wrong Location**
        1. Verify correct location
        2. Edit the entry
        3. Update address
        4. Adjust trailer count
        5. Notify coordinator
        
        **Error: Missing Information**
        1. Identify what's missing
        2. Check source documents
        3. Contact driver if needed
        4. Fill in missing data
        5. Mark as verified
        
        #### 📊 Daily Verification Report
        
        **What to Include:**
        - Total entries reviewed
        - Errors found and fixed
        - Duplicate entries removed
        - Missing data completed
        - Issues requiring follow-up
        
        **Format Example:**
        ```
        Date: [Today]
        Reviewed: 45 entries
        Errors Fixed: 3
        - 2 duplicate trailers
        - 1 wrong location
        Pending: 1 (awaiting driver info)
        Accuracy Rate: 93.3%
        ```
        """
    },
    'location_counts': {
        'title': '📍 Managing Location Trailer Counts',
        'duration': '10 minutes',
        'content': """
        ### Understanding Location Trailer Counts
        
        #### 🎯 Why Counts Matter
        
        Location counts help:
        - Prioritize pickups
        - Plan efficient routes
        - Prevent overflow
        - Reduce storage costs
        - Improve customer service
        
        #### 📊 Priority System
        
        **🔴 CRITICAL (5+ trailers)**
        - Schedule pickup TODAY
        - May need multiple trucks
        - Customer getting frustrated
        - Storage fees accumulating
        - Top priority assignment
        
        **🟡 HIGH (3-4 trailers)**
        - Schedule within 24 hours
        - Single truck sufficient
        - Monitor closely
        - Prevent escalation
        - Plan route efficiently
        
        **🟢 NORMAL (1-2 trailers)**
        - Regular scheduling
        - Combine with other stops
        - No immediate pressure
        - Standard processing
        - Routine pickup
        
        **⚪ CLEAR (0 trailers)**
        - No action needed
        - Location available
        - Ready for deliveries
        - Good standing
        
        #### 📈 Tracking Best Practices
        
        **Real-Time Updates:**
        1. Update immediately when:
           - Trailer delivered (count +1)
           - Trailer picked up (count -1)
           - Count corrected
        
        2. Verify counts daily:
           - Morning check
           - Afternoon review
           - End-of-day reconciliation
        
        **Visual Monitoring:**
        ```
        Location Dashboard View:
        
        Chicago      [████████] 8 🔴
        Detroit      [██████  ] 6 🔴
        Indianapolis [████    ] 4 🟡
        Memphis      [██      ] 2 🟢
        St. Louis    [        ] 0 ⚪
        ```
        
        #### 🚨 Alert Thresholds
        
        **Automatic Alerts Trigger When:**
        - Location reaches 5 trailers
        - No pickup in 48 hours at 3+
        - Customer complaint logged
        - Capacity exceeded
        
        **Response Protocol:**
        1. Acknowledge alert
        2. Assign priority status
        3. Schedule immediate pickup
        4. Notify coordinator
        5. Update customer
        
        #### 📋 Monthly Analysis
        
        Track patterns:
        - Which locations accumulate fastest?
        - Seasonal variations?
        - Customer delivery patterns?
        - Optimization opportunities?
        
        Use insights to:
        - Adjust pickup schedules
        - Negotiate storage terms
        - Plan resource allocation
        - Improve efficiency
        """
    },
    'login_basics': {
        'title': '🔐 Login & Access',
        'duration': '5 minutes',
        'content': """
        ### Getting Started with the System
        
        #### Step 1: Access the Application
        1. Open your web browser (Chrome, Firefox, Edge recommended)
        2. Navigate to: **http://localhost:8501** (or your company URL)
        3. You'll see the login screen
        
        #### Step 2: Enter Your Credentials
        
        **Your Login Information:**
        - **Username:** `{username}`
        - **Password:** `{password}`
        
        > ⚠️ **IMPORTANT:** You must change your password on first login!
        
        #### Step 3: Login Process
        1. Enter your username in the first field
        2. Enter your password in the second field
        3. Click the **🔓 Login** button
        4. Wait for the system to verify your credentials
        
        #### Common Issues:
        - **"Invalid username or password"**: Check for typos, caps lock
        - **Page not loading**: Check your internet connection
        - **Forgot password**: Contact your administrator
        
        #### Security Tips:
        - Never share your login credentials
        - Always logout when finished
        - Use a strong password (we'll show you how next)
        """
    },
    'password_management': {
        'title': '🔑 Password Management',
        'duration': '10 minutes',
        'content': """
        ### How to Change Your Password
        
        #### Why Change Your Password?
        - Default passwords are not secure
        - Regular changes prevent unauthorized access
        - Protects company and client data
        
        #### Step-by-Step Password Change:
        
        1. **Access Password Settings**
           - Login with your current credentials
           - Navigate to **⚙️ Settings** in the sidebar
           - Click on **🔐 Access Control** tab
        
        2. **Current Default Passwords** (MUST BE CHANGED):
           ```
           Admin:    admin / admin123
           Manager:  manager / manager123
           Viewer:   viewer / view123
           Client:   client / client123
           ```
        
        3. **Creating a Strong Password:**
           
           ✅ **Good Password Example:** `Truck#2024$Secure!`
           - At least 12 characters
           - Mix of uppercase and lowercase
           - Include numbers
           - Include special characters
           - Not related to personal info
           
           ❌ **Bad Password Examples:**
           - `password123` (too common)
           - `john2024` (personal info)
           - `12345678` (too simple)
        
        4. **Changing Your Password:**
           ```python
           # For Administrators: Edit auth_config.py
           
           USERS = {
               'admin': {
                   'password': 'YourNewSecurePassword#2024!',  # Change this line
                   'role': 'admin',
                   'name': 'Administrator'
               }
           }
           ```
        
        5. **After Changing:**
           - Save the file
           - Restart the application
           - Test login with new password
           - Store password securely (use password manager)
        
        #### Password Security Checklist:
        - [ ] Changed default password
        - [ ] Password is at least 12 characters
        - [ ] Includes uppercase and lowercase
        - [ ] Includes numbers and symbols
        - [ ] Not used elsewhere
        - [ ] Stored securely
        - [ ] Not written on sticky notes!
        """
    },
    'dashboard_overview': {
        'title': '📊 Dashboard Overview',
        'duration': '15 minutes',
        'content': """
        ### Understanding the Main Dashboard
        
        #### Key Metrics Section
        At the top of your dashboard, you'll see 5 key metrics:
        
        1. **Total Moves** - All trailer moves in the system
        2. **Unpaid Moves** - Moves pending payment
        3. **Total Unpaid** - Dollar amount outstanding
        4. **In Progress** - Currently active moves
        5. **Total Miles** - Cumulative distance
        
        #### Using Filters
        
        **Step 1: Status Filter**
        - Click the dropdown under "Status Filter"
        - Options: All, Unpaid, Paid, In Progress, Completed
        - Select to filter the data table
        
        **Step 2: Driver Filter**
        - Select specific driver or "All"
        - Updates table immediately
        
        **Step 3: Date Range**
        - Click calendar icons
        - Select From and To dates
        - Data updates automatically
        
        #### Working with the Data Table
        
        **Viewing Moves:**
        - Scroll horizontally to see all columns
        - Click column headers to sort
        - Use search box to find specific entries
        
        **Editing Moves:**
        1. Find the move ID you want to edit
        2. Enter the ID in "Enter Move ID" field
        3. Click **📝 Edit Details**
        4. Update information in the form
        5. Click **💾 Save Changes**
        
        **Deleting Moves** (Admin only):
        1. Enter the Move ID
        2. Click **🗑️ Delete**
        3. Confirm the deletion
        
        #### Pro Tips:
        - Export data regularly for backups
        - Use filters to find information quickly
        - Check "Unpaid Moves" daily
        """
    },
    'trailer_management': {
        'title': '🚛 Trailer Management',
        'duration': '20 minutes',
        'content': """
        ### Complete Trailer Management Guide
        
        #### Understanding Trailer Types
        
        **New Trailers:** Empty trailers going to destination
        **Old Trailers:** Loaded trailers being picked up
        
        #### Adding a New Trailer
        
        1. **Navigate to Trailer Management**
           - Click **🚛 Trailer Management** in sidebar
        
        2. **Click "Add New Trailer" Tab**
        
        3. **Fill in Required Information:**
           - **Trailer Number:** Enter unique identifier (e.g., "TR2024-001")
           - **Trailer Type:** Select "New" or "Old"
           - **Current Location:** Choose from dropdown or add new
           - **Status:** Select current status
           - **VIN (optional):** Vehicle identification number
           - **Year/Make/Model:** Equipment details
        
        4. **Click "➕ Add Trailer"**
        
        #### Managing Existing Trailers
        
        **View All Trailers:**
        - Default view shows all trailers
        - Color coding:
          - 🟢 Green border = Available
          - 🟡 Yellow = Assigned/In Transit
          - ⚫ Gray = Completed/Archived
        
        **Update Trailer Status:**
        1. Find trailer in list
        2. Click **Update Status** button
        3. Select new status:
           - Available
           - Assigned
           - In Transit
           - Maintenance
           - Completed
        4. Add notes if needed
        5. Save changes
        
        **Archive Old Trailers:**
        - Completed moves older than 7 days
        - Click **Archive Completed** button
        - Trailers move to archive tab
        
        #### Best Practices:
        - Update status immediately when assigned
        - Add notes for maintenance issues
        - Review available trailers daily
        - Archive completed moves weekly
        """
    },
    'add_moves': {
        'title': '➕ Adding New Moves',
        'duration': '15 minutes',
        'content': """
        ### How to Add a New Trailer Move
        
        #### Step-by-Step Process
        
        **1. Navigate to Add New Move**
        - Click **➕ Add New Move** in sidebar
        
        **2. Trailer Information Section**
        
        📦 **New Trailer Details:**
        - Check "Select from Available Trailers" if using existing
        - Or enter new trailer number manually
        - Select pickup location from dropdown
        - Select destination
        
        🔄 **Old Trailer (Optional):**
        - Enter if swapping trailers
        - Include old pickup and destination
        
        **3. Driver Assignment**
        
        👤 **Assign Driver:**
        - Select from dropdown list
        - Or click "➕ Add New Driver" if not listed
        - Enter assignment date (defaults to today)
        
        **4. Mileage & Payment**
        
        📏 **Calculate Miles:**
        - System auto-calculates if locations are cached
        - Or enter manually
        - Check "💾 Save mileage" for future use
        
        💰 **Payment Calculation:**
        - **Rate per Mile:** Default $2.10 (editable)
        - **Factor Fee:** Default 3% (0.03)
        - **Load Pay:** Auto-calculated
        
        **Example Calculation:**
        ```
        Miles: 250
        Rate: $2.10
        Gross: 250 × $2.10 = $525.00
        Factor Fee: $525.00 × 0.03 = $15.75
        Net Pay: $525.00 - $15.75 = $509.25
        ```
        
        **5. Status & Notes**
        
        ☑️ **Check applicable boxes:**
        - [ ] Received PPW (Proof of Pickup/Weight)
        - [ ] Processed
        - [ ] Paid
        
        📝 **Add Comments:**
        - Special instructions
        - Delivery requirements
        - Contact information
        
        **6. Save the Move**
        - Click **💾 Save Trailer Move**
        - System assigns unique ID
        - Confirmation message appears
        
        #### Common Scenarios
        
        **Scenario 1: Simple Delivery**
        - New trailer from Dallas to Houston
        - No old trailer
        - Single driver assigned
        
        **Scenario 2: Trailer Swap**
        - Pick up old trailer in Austin
        - Deliver to San Antonio
        - Pick up new trailer in San Antonio
        - Deliver to Dallas
        
        **Scenario 3: Multi-Stop Route**
        - Use comments to note all stops
        - Calculate total miles
        - Assign primary driver
        
        #### Troubleshooting:
        - **"Location not found"**: Add location first in Manage Locations
        - **"Driver not available"**: Check driver isn't already assigned
        - **"Invalid miles"**: Must be greater than 0
        """
    },
    'progress_monitoring': {
        'title': '📈 Progress Dashboard',
        'duration': '10 minutes',
        'content': """
        ### Understanding the Progress Dashboard
        
        #### Key Sections
        
        **1. Active Routes (Top Metrics)**
        - Routes in Progress: Currently moving
        - Completed Today: Finished today
        - Completed This Week: 7-day total
        - Avg Completion: Average days per route
        
        **2. Driver Performance Charts**
        
        **Active Drivers (Left Chart):**
        - Shows drivers with active routes
        - Bar length = number of active routes
        - Sorted by most active
        
        **Completion Rates (Right Chart):**
        - Percentage of completed assignments
        - Color coding:
          - 🟢 Green = 90%+ (Excellent)
          - 🟡 Yellow = 70-89% (Good)
          - 🔴 Red = Below 70% (Needs Improvement)
        
        **3. Interactive Charts Toggle**
        - Check "📊 Interactive Charts" for hover details
        - Uncheck for static view (better for printing)
        
        **4. Trend Analysis**
        
        **Daily Completions:**
        - Line graph showing 30-day trend
        - Dotted line = 7-day average
        - Look for patterns (busy days, slow periods)
        
        **Top Routes:**
        - Most frequently used routes
        - Helps identify main corridors
        - Plan resources accordingly
        
        **5. Trailer Status**
        - Pie chart showing fleet distribution
        - Available vs In Transit
        - Quick visual of utilization rate
        
        #### Using Filters
        - Date range selection
        - Driver specific views
        - Status filters
        
        #### Interpreting Metrics
        
        **Good Performance Indicators:**
        - Completion rate above 85%
        - Avg completion under 3 days
        - Utilization above 60%
        
        **Warning Signs:**
        - Completion rate below 70%
        - Increasing in-progress count
        - Low utilization (under 40%)
        """
    },
    'financial_management': {
        'title': '💰 Financial Management',
        'duration': '25 minutes',
        'content': """
        ### Managing Invoices & Payments (Admin Only)
        
        #### Invoice Generation
        
        **Step 1: Navigate to Updates & Invoices**
        - Click **💰 Updates & Invoices** in sidebar
        
        **Step 2: Select Moves for Invoice**
        1. Filter by date range
        2. Filter by driver/contractor
        3. Check unpaid moves only
        4. Select moves to include
        
        **Step 3: Generate Invoice**
        ```
        Invoice Details:
        - Invoice Number: Auto-generated
        - Date: Current date
        - Due Date: Net 30 default
        - Company Details: Pre-filled
        - Line Items: Selected moves
        - Subtotal: Calculated
        - Factor Fee: Deducted
        - Total Due: Final amount
        ```
        
        **Step 4: Review & Send**
        - Preview invoice
        - Add notes if needed
        - Click **Send Invoice**
        - Email to contractor
        
        #### Payment Processing
        
        **Recording Payments:**
        1. Find invoice in system
        2. Click **Record Payment**
        3. Enter payment details:
           - Payment date
           - Amount received
           - Payment method
           - Reference number
        4. Save payment record
        
        **Payment Reports:**
        - Accounts receivable aging
        - Payment history by contractor
        - Outstanding balances
        - Monthly revenue reports
        
        #### Factor Fee Management
        
        **Understanding Factor Fees:**
        - Default: 3% (0.03)
        - Deducted from gross pay
        - Covers financing costs
        
        **Adjusting Rates:**
        - Per contractor basis
        - Volume discounts
        - Special agreements
        
        #### Best Practices:
        - Generate invoices weekly
        - Follow up on overdue payments
        - Maintain payment records
        - Regular financial reconciliation
        """
    },
    'access_instructions': {
        'title': '🔗 Client Access Instructions',
        'duration': '5 minutes',
        'content': """
        ### Accessing Your Progress Dashboard
        
        #### Option 1: Direct Link Access
        
        If you received a link like:
        `http://tracker.smithwilliams.com:8502?token=abc123xyz`
        
        1. **Click the link** or copy/paste into browser
        2. **Dashboard loads automatically**
        3. **No login required** - link contains your access
        
        #### Option 2: Access Code Method
        
        If you received:
        - **URL:** `http://tracker.smithwilliams.com:8502`
        - **Access Code:** `client123`
        
        1. **Go to the URL**
        2. **Enter access code** when prompted
        3. **Click "Access Dashboard"**
        
        #### What You Can See:
        - ✅ Active routes and progress
        - ✅ Completion metrics
        - ✅ Driver performance (no names)
        - ✅ Route statistics
        - ✅ Fleet utilization
        
        #### What You Cannot See:
        - ❌ Financial information
        - ❌ Driver personal details
        - ❌ Internal notes
        - ❌ Edit capabilities
        
        #### Troubleshooting:
        - **"Invalid token"**: Link may have expired, request new one
        - **"Access denied"**: Check access code spelling
        - **Dashboard not loading**: Clear browser cache
        - **Need help?**: Contact your account manager
        """
    },
    'security_best_practices': {
        'title': '🛡️ Security Best Practices',
        'duration': '15 minutes',
        'content': """
        ### System Security Guidelines
        
        #### Password Security
        
        **DO:**
        - ✅ Change default passwords immediately
        - ✅ Use unique passwords for this system
        - ✅ Enable two-factor authentication if available
        - ✅ Use a password manager
        - ✅ Change passwords every 90 days
        
        **DON'T:**
        - ❌ Share passwords with anyone
        - ❌ Write passwords on sticky notes
        - ❌ Use personal information in passwords
        - ❌ Reuse passwords from other sites
        - ❌ Send passwords via email
        
        #### Access Management
        
        **User Account Reviews:**
        - Monthly review of active users
        - Remove terminated employees immediately
        - Audit user roles quarterly
        - Document access changes
        
        **Sharing Dashboard Access:**
        1. Use time-limited tokens
        2. Set appropriate expiration dates
        3. Track who has access
        4. Revoke expired tokens
        
        #### Data Protection
        
        **Backups:**
        - Daily automatic backups
        - Weekly off-site backup
        - Test restore process monthly
        - Encrypt backup files
        
        **Sensitive Data:**
        - Never export financial data to personal devices
        - Use encrypted connections (HTTPS)
        - Lock computer when away
        - Clear browser cache after sensitive work
        
        #### Incident Response
        
        **If you suspect unauthorized access:**
        1. Change your password immediately
        2. Notify administrator
        3. Check recent activity logs
        4. Document the incident
        
        **If you accidentally share credentials:**
        1. Change password immediately
        2. Notify administrator
        3. Review recent system activity
        4. Update security training
        
        #### Compliance Checklist
        - [ ] Passwords changed from defaults
        - [ ] Access reviews conducted
        - [ ] Backups verified
        - [ ] Security training completed
        - [ ] Incident plan reviewed
        """
    }
}

def check_training_access():
    """Check if user has access to training"""
    # Check for training token in URL
    query_params = st.query_params
    if 'token' in query_params:
        return query_params['token'], 'token'
    
    # Check for role parameter
    if 'role' in query_params:
        return query_params['role'], 'role'
    
    # Show role selection
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>📚 Training Center</h1>
        <h3>Smith and Williams Trucking - Trailer Move Tracker</h3>
        <p>Select your role to access the appropriate training materials</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        role = st.selectbox(
            "Select Your Role",
            options=['', 'executive', 'admin', 'operations_coordinator', 'operations_specialist', 'viewer', 'client'],
            format_func=lambda x: {
                '': '-- Select Role --',
                'executive': '👔 Executive/CEO',
                'admin': '👨‍💼 Administrator',
                'operations_coordinator': '📋 Operations Coordinator',
                'operations_specialist': '📝 Operations Specialist',
                'viewer': '👁️ Viewer',
                'client': '🤝 Client'
            }.get(x, x)
        )
        
        if st.button("🎓 Start Training", disabled=not role, use_container_width=True):
            st.query_params['role'] = role
            st.rerun()
    
    return None, None

def show_module(module_key, role):
    """Display a training module"""
    module = MODULE_CONTENT.get(module_key, {})
    
    # Get user-specific information
    user_info = {
        'admin': {'user': 'admin', 'password': 'admin123'},
        'manager': {'user': 'manager', 'password': 'manager123'},
        'viewer': {'user': 'viewer', 'password': 'view123'},
        'client': {'user': 'client', 'password': 'client123'}
    }.get(role, {'user': 'user', 'password': 'password'})
    
    # Format content with user-specific data
    content = module.get('content', '').format(**user_info)
    
    # Display module
    st.markdown(f"## {module.get('title', 'Training Module')}")
    st.markdown(f"**Estimated Duration:** {module.get('duration', 'N/A')}")
    st.markdown("---")
    st.markdown(content)
    
    # Add interactive elements based on module
    if module_key == 'password_management':
        with st.expander("🔐 Practice: Create Your Password"):
            st.text_input("Enter a new password:", type="password", key="practice_pwd")
            if st.button("Check Password Strength"):
                pwd = st.session_state.get('practice_pwd', '')
                score = 0
                feedback = []
                
                if len(pwd) >= 12:
                    score += 25
                    feedback.append("✅ Good length")
                else:
                    feedback.append("❌ Too short (need 12+ characters)")
                
                if any(c.isupper() for c in pwd) and any(c.islower() for c in pwd):
                    score += 25
                    feedback.append("✅ Mixed case")
                else:
                    feedback.append("❌ Add uppercase and lowercase")
                
                if any(c.isdigit() for c in pwd):
                    score += 25
                    feedback.append("✅ Contains numbers")
                else:
                    feedback.append("❌ Add numbers")
                
                if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pwd):
                    score += 25
                    feedback.append("✅ Contains special characters")
                else:
                    feedback.append("❌ Add special characters")
                
                # Show score
                if score >= 75:
                    st.success(f"Strong Password! Score: {score}/100")
                elif score >= 50:
                    st.warning(f"Moderate Password. Score: {score}/100")
                else:
                    st.error(f"Weak Password! Score: {score}/100")
                
                for f in feedback:
                    st.write(f)

def main():
    # Apply branding
    st.markdown(branding.CUSTOM_CSS, unsafe_allow_html=True)
    
    # Check access
    access_value, access_type = check_training_access()
    if not access_value:
        return
    
    # Determine role
    if access_type == 'role':
        role = access_value
    else:
        # Token-based access - decode role from token
        role = 'viewer'  # Default for token access
    
    # Get training plan for role
    training_plan = TRAINING_MODULES.get(role, {})
    modules = training_plan.get('modules', [])
    
    # Sidebar navigation
    st.sidebar.markdown(f"# 📚 {training_plan.get('title', 'Training Guide')}")
    st.sidebar.markdown(f"**Role:** {role.title()}")
    st.sidebar.markdown("---")
    
    # Progress tracking
    if 'completed_modules' not in st.session_state:
        st.session_state.completed_modules = set()
    
    # Module selection
    st.sidebar.markdown("### 📖 Training Modules")
    
    selected_module = None
    for i, module_key in enumerate(modules, 1):
        module_info = MODULE_CONTENT.get(module_key, {})
        is_completed = module_key in st.session_state.completed_modules
        
        # Create button with completion indicator
        icon = "✅" if is_completed else f"{i}."
        if st.sidebar.button(
            f"{icon} {module_info.get('title', module_key)}",
            key=f"module_{module_key}",
            use_container_width=True
        ):
            selected_module = module_key
    
    # Progress bar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Training Progress")
    progress = len(st.session_state.completed_modules) / len(modules) if modules else 0
    st.sidebar.progress(progress)
    st.sidebar.markdown(f"**{len(st.session_state.completed_modules)}/{len(modules)}** modules completed")
    
    # Quick links
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔗 Quick Links")
    st.sidebar.markdown("""
    - [Download PDF Guide](#)
    - [Watch Video Tutorials](#)
    - [Contact Support](#)
    - [Report an Issue](#)
    """)
    
    # Main content area
    if selected_module:
        # Show selected module
        show_module(selected_module, role)
        
        # Module completion
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if selected_module not in st.session_state.completed_modules:
                if st.button("✅ Mark as Completed", use_container_width=True):
                    st.session_state.completed_modules.add(selected_module)
                    st.success("Module completed! Great job! 🎉")
                    st.balloons()
                    st.rerun()
            else:
                st.success("✅ You've completed this module!")
                if st.button("📖 Review Again", use_container_width=True):
                    pass  # Just stays on the same module
    else:
        # Welcome screen
        st.markdown(f"""
        # Welcome to the Training Center!
        
        ## 👋 Hello, {role.title()}!
        
        This interactive training guide will walk you through everything you need to know about using the Trailer Move Tracker system.
        
        ### 📚 Your Training Plan
        
        You have **{len(modules)} modules** to complete:
        """)
        
        # List modules with descriptions
        for i, module_key in enumerate(modules, 1):
            module_info = MODULE_CONTENT.get(module_key, {})
            is_completed = module_key in st.session_state.completed_modules
            status = "✅" if is_completed else "⏳"
            
            st.markdown(f"""
            **{i}. {module_info.get('title', module_key)}** {status}
            - Duration: {module_info.get('duration', 'N/A')}
            """)
        
        st.markdown("""
        ### 🎯 How to Use This Training
        
        1. **Start with Module 1** - Login & Access basics
        2. **Complete in Order** - Each module builds on the previous
        3. **Practice Along** - Have the main system open in another tab
        4. **Mark Complete** - Track your progress as you go
        5. **Ask Questions** - Contact support if you need help
        
        ### 🏆 Completion Certificate
        
        Complete all modules to receive your training certificate!
        
        ---
        
        **Ready to start?** Select the first module from the sidebar to begin your training.
        """)
        
        # Show completion certificate if all done
        if len(st.session_state.completed_modules) == len(modules):
            st.markdown("---")
            st.success("🎉 **Congratulations!** You've completed all training modules!")
            
            # Generate certificate
            st.markdown(f"""
            <div style="border: 3px solid #DC143C; padding: 2rem; text-align: center; border-radius: 10px;">
                <h2>🏆 Certificate of Completion</h2>
                <p>This certifies that</p>
                <h3>{role.title()} User</h3>
                <p>has successfully completed the</p>
                <h3>Trailer Move Tracker Training Program</h3>
                <p>Date: {datetime.now().strftime('%B %d, %Y')}</p>
                <br>
                <p><small>Smith and Williams Trucking</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🎓 Download Certificate"):
                st.info("Certificate download feature coming soon!")

if __name__ == "__main__":
    main()