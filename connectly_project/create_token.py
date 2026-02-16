#!/usr/bin/env python
"""Script to create a user and authentication token for Postman testing"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connectly_project.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from posts.models import User as CustomUser

print("\n" + "="*60)
print("CREATING USER AND AUTHENTICATION TOKEN")
print("="*60 + "\n")

# Create or get Django user (for authentication)
django_user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)

if created:
    django_user.set_password('secure_pass123')
    django_user.save()
    print(f"✅ Created Django user: {django_user.username}")
else:
    print(f"ℹ️  Django user already exists: {django_user.username}")

# Create or get custom user (for posts/comments)
custom_user, created = CustomUser.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)

if created:
    print(f"✅ Created Custom user: {custom_user.username} (ID: {custom_user.id})")
else:
    print(f"ℹ️  Custom user already exists: {custom_user.username} (ID: {custom_user.id})")

# Create or get authentication token
token, created = Token.objects.get_or_create(user=django_user)

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
print(f"🆔 Custom User ID: {custom_user.id}")
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
