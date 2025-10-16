from django.core.mail import send_mail

def send_booking_notification(user_email, room_name, booking_time):
    subject = "Study Buddy Room Booking Confirmation"
    message = f"Your booking for room '{room_name}' at {booking_time} is confirmed."
    send_mail(subject, message, 'noreply@yourdomain.com', [user_email])