#!/usr/bin/env python
"""Script to create the Group2Admin superuser"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.db import transaction  # noqa: E402

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

# Set password and attributes (will update if user already exists)
try:
    with transaction.atomic():
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.email = email
        user.save()

        # Verify the save
        user.refresh_from_db()

        if user.is_superuser and user.is_staff:
            if created:
                print(f"[SUCCESS] Superuser '{username}' created successfully!")
                print(f"   Email: {email}")
                print(f"   Password: {password}")
            else:
                print(
                    f"[SUCCESS] Superuser '{username}' already exists "
                    f"- password updated!"
                )
                print(f"   Email: {email}")
                print(f"   Password: {password}")
            print("[VERIFIED] User successfully saved with superuser privileges")
        else:
            print("[ERROR] User was not saved with superuser privileges")
except Exception as e:
    print(f"[ERROR] Error creating superuser: {str(e)}")
    raise
