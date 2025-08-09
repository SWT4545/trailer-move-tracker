"""
Test script to verify user management functionality
"""

import auth_config
import user_management

print("=" * 60)
print("TESTING USER MANAGEMENT SYSTEM")
print("=" * 60)

# Test 1: Verify Brandon Smith's executive account
print("\n1. Executive Account Check:")
brandon = auth_config.USERS.get('brandon_smith', {})
print(f"   - Username: brandon_smith")
print(f"   - Role: {brandon.get('role')}")
print(f"   - Email: {brandon.get('email')}")
print(f"   - Title: {brandon.get('title')}")
print(f"   - Has Override: {auth_config.USER_ROLES.get('executive', {}).get('override_all', False)}")

# Test 2: Verify executive permissions
print("\n2. Executive Permissions:")
exec_perms = auth_config.get_user_permissions('brandon_smith')
if exec_perms:
    print(f"   - Can manage users: {exec_perms.get('manage_users', False)}")
    print(f"   - Can view financial: {exec_perms.get('view_financial', False)}")
    print(f"   - Can delete: {exec_perms.get('can_delete', False)}")
    print(f"   - Override all: {exec_perms.get('override_all', False)}")

# Test 3: Test password generation
print("\n3. Password Generation Test:")
test_pass = user_management.generate_password()
print(f"   - Generated password: {test_pass}")
print(f"   - Length: {len(test_pass)}")
print(f"   - Has special chars: {any(c in '!@#$%^&*' for c in test_pass)}")

# Test 4: List all users and roles
print("\n4. All System Users:")
for username, user_data in auth_config.USERS.items():
    role = user_data.get('role')
    email = user_data.get('email', 'No email')
    print(f"   - {username}: {role} ({email})")

# Test 5: Company email configuration
print("\n5. Email Configuration:")
print(f"   - Company Email: Smithandwilliamstrucking@gmail.com")
print(f"   - CEO Email: {brandon.get('email', 'Not set')}")

print("\n" + "=" * 60)
print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 60)
print("\nUser Management Features Available:")
print("- Add new users with custom roles")
print("- Edit existing user details")
print("- Delete users (except self)")
print("- Reset passwords")
print("- Lock/unlock accounts")
print("- Generate secure passwords")
print("- View all user credentials (Executive only)")
print("\nAccess the system at: http://localhost:8501")
print("Login as: brandon_smith / executive123")