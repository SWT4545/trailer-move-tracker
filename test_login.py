"""
Test login credentials
"""

import auth_config

print("=" * 60)
print("TESTING LOGIN CREDENTIALS")
print("=" * 60)

# Test each user
test_credentials = [
    ("brandon_smith", "executive123"),
    ("admin", "admin123"),
    ("manager", "manager123"),
    ("viewer", "view123"),
    ("client", "client123"),
]

print("\nAvailable users in system:")
for username, user_data in auth_config.USERS.items():
    print(f"  - {username}: role={user_data['role']}, password={user_data['password']}")

print("\n" + "-" * 60)
print("Testing login combinations:")
print("-" * 60)

for username, password in test_credentials:
    result = auth_config.validate_user(username, password)
    status = "✓ SUCCESS" if result else "✗ FAILED"
    print(f"{status}: {username} / {password}")

print("\n" + "=" * 60)
print("If all show SUCCESS, the credentials are correct.")
print("Try clearing your browser cache or using incognito mode.")
print("=" * 60)