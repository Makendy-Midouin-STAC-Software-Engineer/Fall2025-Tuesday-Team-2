from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudyRoomBooking
from .notifications import send_booking_notification

@receiver(post_save, sender=StudyRoomBooking)
def notify_on_booking(sender, instance, created, **kwargs):
    if created:
        send_booking_notification(
            user_email=instance.user.email,
            room_name=instance.room_name,
            booking_time=instance.booking_time
        )