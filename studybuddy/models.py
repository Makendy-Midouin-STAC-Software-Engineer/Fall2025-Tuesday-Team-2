from django.db import models
from django.contrib.auth.models import User
import uuid
import secrets
import string
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )
    token_created_at = models.DateTimeField(auto_now_add=True)

    # Editable fields (no profile image)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def is_token_valid(self):
        return timezone.now() < self.token_created_at + timedelta(hours=24)


class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Room(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rooms")
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)
    password = models.CharField(max_length=128, blank=True, null=True)

    # Pomodoro Timer Fields
    timer_started_at = models.DateTimeField(null=True, blank=True)
    timer_duration = models.IntegerField(default=1500)  # 25 minutes in seconds
    timer_is_running = models.BooleanField(default=False)
    timer_mode = models.CharField(
        max_length=10, default="work", choices=[("work", "Work"), ("break", "Break")]
    )

    def __str__(self):
        return self.name

    def get_timer_state(self):
        """Get current timer state for all users in the room"""
        if not self.timer_is_running:
            return {
                "is_running": False,
                "time_left": self.timer_duration,
                "mode": self.timer_mode,
                "duration": self.timer_duration,
            }

        elapsed = int((timezone.now() - self.timer_started_at).total_seconds())
        time_left = max(0, self.timer_duration - elapsed)

        if time_left == 0:
            # Switch modes and reset
            self.timer_is_running = False
            self.timer_mode = "break" if self.timer_mode == "work" else "work"
            self.timer_duration = 300 if self.timer_mode == "break" else 1500
            self.save()
            time_left = self.timer_duration

        return {
            "is_running": self.timer_is_running,
            "time_left": time_left,
            "mode": self.timer_mode,
            "duration": self.timer_duration,
        }

    def generate_private_code(self):
        """Generate a unique, easy-to-share code for private room access"""
        # Generate a 6-character code using uppercase letters and numbers
        code_length = 6
        characters = string.ascii_uppercase + string.digits
        # Exclude confusing characters (0, O, I, 1)
        characters = (
            characters.replace("0", "")
            .replace("O", "")
            .replace("I", "")
            .replace("1", "")
        )

        max_attempts = 100
        for _ in range(max_attempts):
            code = "".join(secrets.choice(characters) for _ in range(code_length))
            # Check if code is unique (not used by another private room)
            if (
                not Room.objects.filter(is_private=True, password=code)
                .exclude(pk=self.pk)
                .exists()
            ):
                return code

        # Fallback: if we can't find a unique code, use a longer UUID-based code
        return secrets.token_urlsafe(6).upper()[:8]


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"


class RoomPresence(models.Model):
    """Track active users in rooms"""

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="presence")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("room", "user")
        indexes = [
            models.Index(fields=["room", "last_seen"]),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.room.name}"

    @classmethod
    def get_active_users(cls, room, threshold_seconds=30):
        """Get count of users active in the last threshold_seconds"""
        cutoff_time = timezone.now() - timedelta(seconds=threshold_seconds)
        return cls.objects.filter(room=room, last_seen__gte=cutoff_time).count()

    @classmethod
    def update_presence(cls, room, user):
        """Update or create presence record for a user in a room"""
        obj, created = cls.objects.update_or_create(
            room=room, user=user, defaults={"last_seen": timezone.now()}
        )
        return obj

    @classmethod
    def cleanup_old_records(cls, days=1):
        """Clean up presence records older than specified days"""
        cutoff_time = timezone.now() - timedelta(days=days)
        cls.objects.filter(last_seen__lt=cutoff_time).delete()


# SIGNALS


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a UserProfile whenever a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Automatically save the UserProfile whenever the User is saved"""
    if hasattr(instance, "profile"):
        instance.profile.save()
