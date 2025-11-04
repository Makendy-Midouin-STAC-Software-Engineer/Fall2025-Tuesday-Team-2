from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm


class EditProfileForm(UserChangeForm):
    """Custom form for editing user profile - excludes email field"""

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove password field from UserChangeForm
        if "password" in self.fields:
            del self.fields["password"]

        # Remove email and other unwanted fields
        fields_to_remove = [
            "email",
            "last_login",
            "date_joined",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        ]
        for field in fields_to_remove:
            if field in self.fields:
                del self.fields[field]
