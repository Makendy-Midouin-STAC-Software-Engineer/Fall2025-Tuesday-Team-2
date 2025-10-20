from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
from datetime import timedelta


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    token_created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    def is_token_valid(self):
        """Check if verification token is still valid (24 hours)"""
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
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Pomodoro Timer Fields (server-side, synced across all users)
    timer_started_at = models.DateTimeField(null=True, blank=True)
    timer_duration = models.IntegerField(default=1500)  # 25 minutes in seconds
    timer_is_running = models.BooleanField(default=False)
    timer_mode = models.CharField(max_length=10, default='work', choices=[('work', 'Work'), ('break', 'Break')])

    def __str__(self):
        return self.name
    
    def get_timer_state(self):
        """Get current timer state for all users in the room"""
        if not self.timer_is_running:
            return {
                'is_running': False,
                'time_left': self.timer_duration,
                'mode': self.timer_mode,
                'duration': self.timer_duration
            }
        
        # Calculate time elapsed since timer started
        elapsed = int((timezone.now() - self.timer_started_at).total_seconds())
        time_left = max(0, self.timer_duration - elapsed)
        
        # Check if timer has finished
        if time_left == 0:
            # Auto-switch modes and reset
            self.timer_is_running = False
            self.timer_mode = 'break' if self.timer_mode == 'work' else 'work'
            self.timer_duration = 300 if self.timer_mode == 'break' else 1500  # 5 or 25 minutes
            self.save()
            time_left = self.timer_duration
        
        return {
            'is_running': self.timer_is_running,
            'time_left': time_left,
            'mode': self.timer_mode,
            'duration': self.timer_duration
        }


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"
