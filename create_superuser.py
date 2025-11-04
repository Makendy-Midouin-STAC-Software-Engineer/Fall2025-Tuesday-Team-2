#!/usr/bin/env python
"""Script to create the Group2Admin superuser"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth.models import User  # noqa: E402

username = "Group2Admin"
email = "studybuddy@gmail.com"
password = "Team2Fall2025!"

# Check if user already exists
user, created = User.objects.get_or_create(
    username=username,
    defaults={
        "email": email,
        "is_superuser": True,
        "is_staff": True,
        "is_active": True,
    },
)

# Set password (will update if user already exists)
user.set_password(password)
user.is_superuser = True
user.is_staff = True
user.is_active = True
user.email = email
user.save()

if created:
    print(f"✅ Superuser '{username}' created successfully!")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
else:
    print(f"✅ Superuser '{username}' already exists - password updated!")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
