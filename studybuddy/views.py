from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import uuid

from .models import Note, Room, Message, UserProfile


# -----------------------------
# AUTHENTICATION VIEWS
# -----------------------------

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('studybuddy:note_list')  # redirect to notes list after login
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'studybuddy/login.html')


def custom_logout(request):
    logout(request)
    return render(request, 'studybuddy/logout.html')


def custom_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Validation
        if password != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
        else:
            # Create user and log them in immediately
            user = User.objects.create_user(username=username, email=email or '', password=password)
            user.save()
            
            # Create user profile for future use (email verification can be added later)
            UserProfile.objects.create(user=user, email_verified=True)
            
            # Log them in automatically
            login(request, user)
            messages.success(request, f"Welcome {username}! Your account has been created.")
            return redirect('studybuddy:note_list')
            
    return render(request, 'studybuddy/register.html')


def send_verification_email(request, user, profile):
    """Send email verification link to user"""
    verification_link = request.build_absolute_uri(
        f'/studybuddy/verify-email/{profile.verification_token}/'
    )
    
    subject = 'Verify your StudyBuddy account'
    message = f"""
Hi {user.username},

Thank you for registering with StudyBuddy!

Please click the link below to verify your email address:
{verification_link}

This link will expire in 24 hours.

If you didn't create this account, please ignore this email.

Best regards,
The StudyBuddy Team
    """
    
    send_mail(
        subject,
        message,
        'noreply@studybuddy.com',
        [user.email],
        fail_silently=False,
    )


def verify_email(request, token):
    """Verify user's email with token"""
    try:
        profile = UserProfile.objects.get(verification_token=token)
        
        if profile.email_verified:
            messages.info(request, "Your email is already verified. You can login now.")
        elif profile.is_token_valid():
            profile.email_verified = True
            profile.save()
            messages.success(request, "Email verified successfully! You can now login.")
        else:
            messages.error(request, "This verification link has expired. Please contact support.")
            
    except UserProfile.DoesNotExist:
        messages.error(request, "Invalid verification link.")
    
    return redirect('studybuddy:login')


def password_reset_request(request):
    """Handle password reset request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset link
            reset_link = request.build_absolute_uri(
                f'/studybuddy/reset-password/{uid}/{token}/'
            )
            
            # Send email
            subject = 'Password Reset Request - StudyBuddy'
            message = f"""
Hi {user.username},

You requested to reset your password for your StudyBuddy account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
The StudyBuddy Team
            """
            
            send_mail(
                subject,
                message,
                'noreply@studybuddy.com',
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 
                f"Password reset instructions have been sent to {email}. "
                "For development, check the terminal for the email.")
        except User.DoesNotExist:
            # Don't reveal that the email doesn't exist (security)
            messages.success(request, 
                "If an account exists with that email, password reset instructions have been sent.")
        
        return redirect('studybuddy:login')
    
    return render(request, 'studybuddy/password_reset.html')


def password_reset_confirm(request, uidb64, token):
    """Handle password reset confirmation"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            
            if password != password2:
                messages.error(request, "Passwords do not match.")
            elif len(password) < 8:
                messages.error(request, "Password must be at least 8 characters.")
            else:
                user.set_password(password)
                user.save()
                messages.success(request, "Password has been reset successfully. You can now login.")
                return redirect('studybuddy:login')
        
        return render(request, 'studybuddy/password_reset_confirm.html', {'validlink': True})
    else:
        messages.error(request, "This password reset link is invalid or has expired.")
        return redirect('studybuddy:password_reset_request')


def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'studybuddy/home_logged_in.html', {'username': request.user.username})
    else:
        return render(request, 'studybuddy/home.html')


# -----------------------------
# NOTES FEATURE
# -----------------------------

@login_required
def notes_home(request):
    """Simple notes homepage (placeholder)"""
    return render(request, 'notes/home.html')


class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = 'studybuddy/note_list.html'
    context_object_name = 'notes'

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user).order_by('-updated_at')


class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    fields = ['title', 'content']
    template_name = 'studybuddy/note_form.html'
    success_url = reverse_lazy('studybuddy:note_list')
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    fields = ['title', 'content']
    template_name = 'studybuddy/note_form.html'
    success_url = reverse_lazy('studybuddy:note_list')

class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    template_name = 'studybuddy/note_confirm_delete.html'
    success_url = reverse_lazy('studybuddy:note_list')


# -----------------------------
# ROOMS & MESSAGES FEATURE
# -----------------------------

@login_required
def rooms(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            Room.objects.create(name=name, description=description, created_by=request.user)
        return redirect('studybuddy:rooms')

    all_rooms = Room.objects.all().order_by('-created_at')
    return render(request, 'studybuddy/rooms.html', {'rooms': all_rooms})


@login_required
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room_messages = room.messages.order_by('timestamp')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(room=room, user=request.user, content=content)
        return redirect('studybuddy:room_detail', room_id=room.id)

    context = {'room': room, 'messages': room_messages}
    return render(request, 'studybuddy/room_detail.html', context)


@login_required
def room_delete(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    # Only the creator can delete the room
    if room.created_by != request.user:
        messages.error(request, "You don't have permission to delete this room.")
        return redirect('studybuddy:room_detail', room_id=room.id)
    
    if request.method == 'POST':
        room.delete()
        messages.success(request, f"Room '{room.name}' has been deleted.")
        return redirect('studybuddy:rooms')
    
    return render(request, 'studybuddy/room_confirm_delete.html', {'room': room})


@login_required
def message_delete(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    room_id = message.room.id
    
    # Only the message author can delete it
    if message.user != request.user:
        messages.error(request, "You don't have permission to delete this message.")
        return redirect('studybuddy:room_detail', room_id=room_id)
    
    message.delete()
    messages.success(request, "Message deleted successfully.")
    return redirect('studybuddy:room_detail', room_id=room_id)


# -----------------------------
# POMODORO TIMER CONTROLS
# -----------------------------

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

@login_required
@require_POST
def timer_start(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    # Only room creator can control timer
    if room.created_by != request.user:
        return JsonResponse({'error': 'Only the room creator can control the timer'}, status=403)
    
    if not room.timer_is_running:
        room.timer_is_running = True
        room.timer_started_at = timezone.now()
        room.save()
    
    return JsonResponse(room.get_timer_state())


@login_required
@require_POST
def timer_pause(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    # Only room creator can control timer
    if room.created_by != request.user:
        return JsonResponse({'error': 'Only the room creator can control the timer'}, status=403)
    
    if room.timer_is_running:
        # Calculate remaining time and save it
        elapsed = int((timezone.now() - room.timer_started_at).total_seconds())
        room.timer_duration = max(0, room.timer_duration - elapsed)
        room.timer_is_running = False
        room.timer_started_at = None
        room.save()
    
    return JsonResponse(room.get_timer_state())


@login_required
@require_POST
def timer_reset(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    # Only room creator can control timer
    if room.created_by != request.user:
        return JsonResponse({'error': 'Only the room creator can control the timer'}, status=403)
    
    room.timer_is_running = False
    room.timer_started_at = None
    room.timer_mode = 'work'
    room.timer_duration = 1500  # 25 minutes
    room.save()
    
    return JsonResponse(room.get_timer_state())


@login_required
def timer_state(request, room_id):
    """Get current timer state - all users can view"""
    room = get_object_or_404(Room, id=room_id)
    return JsonResponse(room.get_timer_state())
