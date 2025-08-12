# Role Management Guide

## IMPORTANT: Single Login System for Drivers

**Drivers have ONE account** - No separate driver login needed!
- Create driver as user in User Management with 'driver' role
- Driver logs in through main system (same as everyone)
- Add driver details (CDL, insurance, etc.) in Driver Management

## Current User Accounts

### Owner
- **Brandon** (owner123) - Business Administrator with owner privileges

### Single Role Users
- **admin** (admin123) - Business Administrator
- **coordinator** (coord123) - Operations Coordinator  
- **driver1** (driver123) - John Smith - Driver
- **driver2** (driver456) - Mike Johnson - Driver
- **viewer** (view123) - Viewer Account (read-only)
- **client1** (client123) - Client Viewer (read-only)
- **newdriver** (new123) - New Driver
- **trainee** (trainee123) - Trainee (viewer role)
- **demo** (demo) - Demo User - Business Administrator

### Dual-Role Users
- **sarah** (sarah123) - Sarah Williams - Driver + Coordinator
- **tom** (tom123) - Tom Davis - Driver + Coordinator

## In-App User Management (NEW!)

### No Code Editing Required!
Users can now be managed directly through the application interface by administrators:

1. **Login** as Brandon (owner) or admin
2. **Navigate** to ⚙️ System Admin → User Management tab
3. **Choose** your action:
   - **Add Users** - Create new accounts with single or dual roles
   - **Edit Roles** - Upgrade/downgrade user permissions
   - **Reset Passwords** - Change any user's password
   - **Remove Users** - Delete accounts (except owner)

### How to Add a New User (Through App)

1. Go to **⚙️ System Admin** → **User Management** tab
2. Click **➕ Add User** tab
3. Fill in:
   - Username (for login)
   - Password (initial password)
   - Full Name (display name)
   - Email (optional)
   - Phone (optional)
   - Select one or more roles (for dual-role users, check multiple boxes)
   - For client viewers: Enter client company name
4. Click **➕ Create User**

### How to Create a Driver Account

1. **First:** Create user account
   - Go to **⚙️ System Admin** → **User Management**
   - Add user with 'Driver' role
   - Set username/password for their login

2. **Then:** Add driver details
   - Go to **👤 Drivers** → **📝 Driver Details**
   - Select the driver user you created
   - Choose driver type:
     - **Company Driver:** Internal employee drivers
     - **Contractor/Owner-Operator:** Independent contractors
   - Add basic info:
     - Phone & Email
     - CDL Number & Expiry Date
   - For Contractors ONLY add:
     - Company Name
     - MC Number
     - DOT Number  
     - Insurance Company & Policy
     - Insurance Expiry Date
     - Upload Insurance Certificate (optional)

3. **Driver logs in** with the username/password from step 1

**Note:** Driver information can be updated at any time - not just during creation

### How to Upgrade a User to Dual Role (Through App)

Example: Upgrade "newdriver" to also have coordinator access:

1. Go to **⚙️ System Admin** → **User Management** tab
2. Click **✏️ Edit Roles** tab
3. Select "newdriver" from dropdown
4. Check both:
   - ✅ Driver
   - ✅ Operations Coordinator
5. Click **💾 Update Roles**

The user can now switch between roles using the sidebar dropdown!

## Available Roles

- `'business_administrator'` - Full system control
- `'operations_coordinator'` - Manage moves and assignments
- `'driver'` - Upload PODs, view assignments
- `'viewer'` - Read-only access to dashboards

## Role Progression Path

Typical progression:
1. Start as `viewer` (trainee learning the system)
2. Upgrade to `driver` (can now handle deliveries)
3. Add `operations_coordinator` (dual role - can self-assign and help manage)
4. Potentially promote to `business_administrator` (full control)

## Notes

- Users with driver role automatically appear in driver assignment list
- Dual-role users see a role switcher dropdown in sidebar
- Viewer role is perfect for clients or trainees who need read-only access
- Changes require editing the code and redeploying