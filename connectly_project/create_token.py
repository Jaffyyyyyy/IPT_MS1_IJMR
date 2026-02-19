#!/usr/bin/env python
"""Script to create a user and authentication token for Postman testing"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connectly_project.settings')
django.setup()

from rest_framework.authtoken.models import Token
from posts.models import User

print("\n" + "="*60)
print("CREATING USER AND AUTHENTICATION TOKEN")
print("="*60 + "\n")

# Create or get user (now uses single custom User model)
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)

if created:
    user.set_password('secure_pass123')
    user.save()
    print(f"✅ Created user: {user.username} (ID: {user.id})")
else:
    print(f"ℹ️  User already exists: {user.username} (ID: {user.id})")

# Create or get authentication token
token, created = Token.objects.get_or_create(user=user)

if created:
    print(f"✅ Generated new token")
else:
    print(f"ℹ️  Using existing token")

print("\n" + "="*60)
print("YOUR AUTHENTICATION DETAILS")
print("="*60)
print(f"\n🔑 TOKEN: {token.key}")
print(f"\n👤 Username: testuser")
print(f"🔒 Password: secure_pass123")
print(f"🆔 User ID: {user.id}")
print("\n" + "="*60)
print("POSTMAN SETUP INSTRUCTIONS")
print("="*60)
print("\n1. Open your Postman collection")
print("2. Click on the collection name (top)")
print("3. Go to 'Variables' tab")
print("4. Find 'auth_token' variable")
print(f"5. Set its value to: {token.key}")
print("6. Click 'Save'")
print("\n✅ You're all set! Run your tests now.\n")
