# -----------------------------
# IMPORTS
# -----------------------------

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

import uuid

from .models import Note, Room, Message, UserProfile
from .forms import EditProfileForm

# -----------------------------
# AUTHENTICATION VIEWS
# -----------------------------


def custom_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("studybuddy:note_list")
        messages.error(request, "Invalid username or password")
    return render(request, "studybuddy/login.html")


def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("studybuddy:login")


def custom_register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        # Validation
        if password != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(username=username, password=password)
            user_profile = user.profile
            user_profile.email_verified = True
            user_profile.save()

            login(request, user)
            messages.success(
                request,
                f"Welcome {username}! Your account has been created.",
            )
            return redirect("studybuddy:note_list")

    return render(request, "studybuddy/register.html")


def password_reset_request(request):
    """Handle password reset request"""
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(
                f"/studybuddy/reset-password/{uid}/{token}/"
            )

            subject = "Password Reset Request - StudyBuddy"
            message = (
                f"Hi {user.username},\n\n"
                "You requested to reset your password for your StudyBuddy account.\n\n"
                f"Click the link below to reset your password:\n{reset_link}\n\n"
                "This link will expire in 1 hour.\n\n"
                "If you didn't request this, please ignore this email.\n\n"
                "Best regards,\nThe StudyBuddy Team"
            )

            send_mail(
                subject,
                message,
                "noreply@studybuddy.com",
                [user.email],
                fail_silently=False,
            )

            messages.success(
                request,
                f"Password reset instructions have been sent to {email}. "
                "For development, check the terminal for the email.",
            )
        except User.DoesNotExist:
            messages.success(
                request,
                "If an account exists with that email, password reset instructions "
                "have been sent.",
            )

        return redirect("studybuddy:login")

    return render(request, "studybuddy/password_reset.html")


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get("password")
            password2 = request.POST.get("password2")
            if password != password2:
                messages.error(request, "Passwords do not match.")
            elif len(password) < 8:
                messages.error(request, "Password must be at least 8 characters.")
            else:
                user.set_password(password)
                user.save()
                messages.success(
                    request,
                    "Password has been reset successfully. You can now login.",
                )
                return redirect("studybuddy:login")
        return render(
            request, "studybuddy/password_reset_confirm.html", {"validlink": True}
        )
    return render(
        request, "studybuddy/password_reset_confirm.html", {"validlink": False}
    )


def home_view(request):
    if request.user.is_authenticated:
        return render(
            request,
            "studybuddy/home_logged_in.html",
            {"username": request.user.username},
        )
    return render(request, "studybuddy/home.html")


@login_required
def edit_profile(request):
    """Edit profile view - allows user to update username, first_name, last_name"""
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("studybuddy:home")
    else:
        form = EditProfileForm(instance=request.user)
    
    return render(request, "studybuddy/edit_profile.html", {"form": form})


# -----------------------------
# NOTES FEATURE
# -----------------------------


@login_required
def notes_home(request):
    """Simple notes homepage (placeholder)"""
    return render(request, "notes/home.html")


class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = "studybuddy/note_list.html"
    context_object_name = "notes"

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user).order_by("-updated_at")


class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    fields = ["title", "content"]
    template_name = "studybuddy/note_form.html"
    success_url = reverse_lazy("studybuddy:note_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    fields = ["title", "content"]
    template_name = "studybuddy/note_form.html"
    success_url = reverse_lazy("studybuddy:note_list")


class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    template_name = "studybuddy/note_confirm_delete.html"
    success_url = reverse_lazy("studybuddy:note_list")


# -----------------------------
# ROOMS & MESSAGES FEATURE
# -----------------------------


@login_required
def rooms(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        if name:
            Room.objects.create(
                name=name,
                description=description,
                created_by=request.user,
            )
        return redirect("studybuddy:rooms")

    all_rooms = Room.objects.all().order_by("-created_at")
    return render(request, "studybuddy/rooms.html", {"rooms": all_rooms})


@login_required
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room_messages = room.messages.order_by("timestamp")

    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Message.objects.create(room=room, user=request.user, content=content)
        return redirect("studybuddy:room_detail", room_id=room.id)

    context = {"room": room, "messages": room_messages}
    return render(request, "studybuddy/room_detail.html", context)


@login_required
def room_delete(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if room.created_by != request.user:
        messages.error(request, "You don't have permission to delete this room.")
        return redirect("studybuddy:room_detail", room_id=room.id)

    if request.method == "POST":
        room.delete()
        messages.success(request, f"Room '{room.name}' has been deleted.")
        return redirect("studybuddy:rooms")

    return render(request, "studybuddy/room_confirm_delete.html", {"room": room})


@login_required
def message_delete(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    room_id = message.room.id

    if message.user != request.user:
        messages.error(request, "You don't have permission to delete this message.")
        return redirect("studybuddy:room_detail", room_id=room_id)

    message.delete()
    messages.success(request, "Message deleted successfully.")
    return redirect("studybuddy:room_detail", room_id=room_id)


# -----------------------------
# POMODORO TIMER CONTROLS
# -----------------------------


@login_required
@require_POST
def timer_start(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if room.created_by != request.user:
        return JsonResponse(
            {"error": "Only the room creator can control the timer"}, status=403
        )

    if not room.timer_is_running:
        room.timer_is_running = True
        room.timer_started_at = timezone.now()
        room.save()

    return JsonResponse(room.get_timer_state())


@login_required
@require_POST
def timer_pause(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if room.created_by != request.user:
        return JsonResponse(
            {"error": "Only the room creator can control the timer"}, status=403
        )

    if room.timer_is_running:
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

    if room.created_by != request.user:
        return JsonResponse(
            {"error": "Only the room creator can control the timer"}, status=403
        )

    room.timer_is_running = False
    room.timer_started_at = None
    room.timer_mode = "work"
    room.timer_duration = 1500
    room.save()

    return JsonResponse(room.get_timer_state())


@login_required
def timer_state(request, room_id):
    """Get current timer state - all users can view"""
    room = get_object_or_404(Room, id=room_id)
    return JsonResponse(room.get_timer_state())


@login_required
def get_messages(request, room_id):
    """Get messages for a room in JSON format for real-time chat updates"""
    room = get_object_or_404(Room, id=room_id)
    room_messages = room.messages.order_by("timestamp")
    
    messages_data = []
    for msg in room_messages:
        # Send ISO 8601 timestamp for frontend timezone conversion
        timestamp_iso = msg.timestamp.isoformat()
        messages_data.append({
            "id": msg.id,
            "user": msg.user.username,
            "content": msg.content,
            "timestamp": timestamp_iso,
            "is_own": msg.user.id == request.user.id,
        })
    
    return JsonResponse({"messages": messages_data})


@login_required
@require_POST
def send_message(request, room_id):
    """Send a message via AJAX - returns JSON response"""
    room = get_object_or_404(Room, id=room_id)
    content = request.POST.get("content", "").strip()
    
    if not content:
        return JsonResponse({"error": "Message content is required"}, status=400)
    
    message = Message.objects.create(room=room, user=request.user, content=content)
    
    # Send ISO 8601 timestamp for frontend timezone conversion
    timestamp_iso = message.timestamp.isoformat()
    
    return JsonResponse({
        "success": True,
        "message": {
            "id": message.id,
            "user": message.user.username,
            "content": message.content,
            "timestamp": timestamp_iso,
            "is_own": True,
        }
    })
