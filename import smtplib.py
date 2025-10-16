from django.db import models
from django.contrib.auth.models import User

class StudyRoomBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room_name = models.CharField(max_length=100)
    booking_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)