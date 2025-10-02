from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # you can add custom fields later if needed (e.g., student_id, major, etc.)
    email = models.EmailField(unique=True) #unique email usage
    pass
