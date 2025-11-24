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
from django.db import transaction
from datetime import timedelta
from django.db.models import Q
import markdown
from django.utils.safestring import mark_safe

from .forms import UserUpdateForm, ProfileUpdateForm

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash


from .models import Note, Room, Message, RoomPresence

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

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("studybuddy:note_detail", kwargs={"pk": self.object.pk})


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    fields = ["title", "content"]
    template_name = "studybuddy/note_form.html"

    def get_success_url(self):
        return reverse_lazy("studybuddy:note_detail", kwargs={"pk": self.object.pk})


class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    template_name = "studybuddy/note_confirm_delete.html"
    success_url = reverse_lazy("studybuddy:note_list")


def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk)
    html = markdown.markdown(note.content, extensions=["fenced_code", "codehilite"])
    return render(
        request,
        "studybuddy/note_detail.html",
        {
            "note": note,
            "html": mark_safe(html),
        },
    )


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

    # Only show public rooms in the list
    all_rooms = (
        Room.objects.filter(
            Q(is_private=False)  # show public rooms
            | Q(created_by=request.user)  # show rooms YOU created
        )
        .distinct()
        .order_by("-created_at")
    )

    # Add session-access rooms for private rooms
    session_rooms = []
    private_rooms = Room.objects.filter(is_private=True)

    for room in private_rooms:
        if request.session.get(f"access_room_{room.id}", False):
            session_rooms.append(room)

    # Merge + dedupe
    all_rooms = list(
        {room.id: room for room in list(all_rooms) + session_rooms}.values()
    )

    return render(request, "studybuddy/rooms.html", {"rooms": all_rooms})


@login_required
def get_rooms(request):
    """Get rooms visible to the user (public, created, or session-access private rooms)"""

    # Base: public OR created by user
    base_rooms = (
        Room.objects.filter(Q(is_private=False) | Q(created_by=request.user))
        .distinct()
        .order_by("-created_at")
    )

    # Add private rooms user has access to
    session_rooms = []
    private_rooms = Room.objects.filter(is_private=True)

    for room in private_rooms:
        if request.session.get(f"access_room_{room.id}", False):
            session_rooms.append(room)

    all_rooms = list(
        {room.id: room for room in list(base_rooms) + session_rooms}.values()
    )

    # Convert to JSON
    rooms_data = []
    for room in all_rooms:
        rooms_data.append(
            {
                "id": room.id,
                "name": room.name,
                "description": room.description or "",
                "created_by": room.created_by.username,
                "created_at": room.created_at.isoformat(),
                "is_creator": room.created_by_id == request.user.id,
                "is_private": room.is_private,
            }
        )

    return JsonResponse({"rooms": rooms_data})


@login_required
def search_rooms(request):
    query = request.GET.get("q", "").strip()

    # Build base queryset (same visibility rules as rooms list)
    base_rooms = Room.objects.filter(
        Q(is_private=False) | Q(created_by=request.user)
    ).distinct()

    # Add session-access private rooms
    session_rooms = []
    private_rooms = Room.objects.filter(is_private=True)

    for room in private_rooms:
        if request.session.get(f"access_room_{room.id}", False):
            session_rooms.append(room)

    visible_rooms = list(
        {room.id: room for room in list(base_rooms) + session_rooms}.values()
    )

    # Apply search filter: name OR creator username
    if query:
        visible_rooms = [
            r
            for r in visible_rooms
            if query.lower() in r.name.lower()
            or query.lower() in r.created_by.username.lower()
        ]

    # Serialize
    rooms_data = [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description or "",
            "created_by": r.created_by.username,
            "created_at": r.created_at.isoformat(),
            "is_creator": r.created_by_id == request.user.id,
            "is_private": r.is_private,
        }
        for r in visible_rooms
    ]

    return JsonResponse({"rooms": rooms_data})


@login_required
def join_private_room(request):
    """Handle joining a private room by code"""
    if request.method == "POST":
        code = request.POST.get("room_code", "").strip().upper()

        if not code:
            messages.error(request, "Please enter a room code.")
            return redirect("studybuddy:rooms")

        # Find the private room with this code
        try:
            room = Room.objects.get(is_private=True, password=code)
            # Grant session access to this room
            session_key = f"access_room_{room.id}"
            request.session[session_key] = True
            request.session.modified = True
            messages.success(request, f"Successfully joined '{room.name}'!")
            return redirect("studybuddy:room_detail", room_id=room.id)
        except Room.DoesNotExist:
            messages.error(request, "Invalid room code. Please check and try again.")
            return redirect("studybuddy:rooms")

    return redirect("studybuddy:rooms")


@login_required
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    user_is_creator = room.created_by_id == request.user.id
    session_key = f"access_room_{room.id}"
    has_session_access = request.session.get(session_key)

    # --- Private room check ---
    if room.is_private and not user_is_creator and not has_session_access:
        error_message = None
        if request.method == "POST" and "room_password" in request.POST:
            submitted_password = request.POST.get("room_password", "")
            if submitted_password and submitted_password == (room.password or ""):
                request.session[session_key] = True
                request.session.modified = True
                return redirect("studybuddy:room_detail", room_id=room.id)
            error_message = "Incorrect password."
        return render(
            request,
            "studybuddy/room_password_prompt.html",
            {"room": room, "error_message": error_message},
        )

    # --- Normal room logic ---
    room_messages = room.messages.order_by("timestamp")

    if request.method == "POST" and "content" in request.POST:
        content = request.POST.get("content")
        if content:
            Message.objects.create(room=room, user=request.user, content=content)
        return redirect("studybuddy:room_detail", room_id=room.id)

    context = {"room": room, "messages": room_messages}
    return render(request, "studybuddy/room_detail.html", context)


@login_required
@require_POST
def set_privacy(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if room.created_by != request.user:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    make_private = request.POST.get("is_private", "").lower() in {"1", "true", "yes"}

    try:
        with transaction.atomic():
            if make_private:
                # Auto-generate code instead of requiring user input
                code = room.generate_private_code()
                room.is_private = True
                room.password = code
            else:
                room.is_private = False
                room.password = None

            room.save()
            room.refresh_from_db()  # Ensure we have latest state

        return JsonResponse(
            {
                "success": True,
                "is_private": room.is_private,
                "code": room.password if room.is_private else None,
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


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
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"error": "You don't have permission to delete this message."},
                status=403,
            )
        messages.error(request, "You don't have permission to delete this message.")
        return redirect("studybuddy:room_detail", room_id=room_id)

    message.delete()

    # Return JSON response for AJAX requests
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True})

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
        messages_data.append(
            {
                "id": msg.id,
                "user": msg.user.username,
                "content": msg.content,
                "timestamp": timestamp_iso,
                "is_own": msg.user.id == request.user.id,
            }
        )

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

    return JsonResponse(
        {
            "success": True,
            "message": {
                "id": message.id,
                "user": message.user.username,
                "content": message.content,
                "timestamp": timestamp_iso,
                "is_own": True,
            },
        }
    )


@login_required
def room_presence(request, room_id):
    """Update user presence and return active user count"""
    room = get_object_or_404(Room, id=room_id)

    # Update current user's presence
    RoomPresence.update_presence(room, request.user)

    # Get active users count (active in last 30 seconds)
    active_count = RoomPresence.get_active_users(room, threshold_seconds=30)

    # Get list of active usernames (optional, for displaying who's online)
    cutoff_time = timezone.now() - timedelta(seconds=30)
    active_users = (
        RoomPresence.objects.filter(room=room, last_seen__gte=cutoff_time)
        .select_related("user")
        .values_list("user__username", flat=True)
    )

    return JsonResponse(
        {"active_count": active_count, "active_users": list(active_users)}
    )


# -----------------------------
# Profile
# -----------------------------


@login_required
def edit_profile(request):
    # Initialize forms (will be overwritten if POST)
    u_form = UserUpdateForm(instance=request.user)
    p_form = ProfileUpdateForm(instance=request.user.profile)
    pw_form = PasswordChangeForm(user=request.user)

    if request.method == "POST":
        # Check if this is a profile update (has profile fields or update_info button)
        profile_fields = {
            "username",
            "first_name",
            "last_name",
            "email",
            "bio",
            "phone_number",
            "location",
        }
        has_profile_data = any(field in request.POST for field in profile_fields)

        if "update_info" in request.POST or (
            has_profile_data and "change_password" not in request.POST
        ):
            # Updating account & profile info
            # Ensure email is included if not in POST (use existing email)
            post_data = request.POST.copy()
            if "email" not in post_data and request.user.email:
                post_data["email"] = request.user.email

            u_form = UserUpdateForm(post_data, instance=request.user)
            p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)

            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, "Your profile has been updated!")
                return redirect("studybuddy:edit_profile")
            else:
                messages.error(request, "Please fix the errors below.")

            pw_form = PasswordChangeForm(user=request.user)  # fresh password form

        elif "change_password" in request.POST:
            # Changing password
            pw_form = PasswordChangeForm(user=request.user, data=request.POST)
            u_form = UserUpdateForm(instance=request.user)
            p_form = ProfileUpdateForm(instance=request.user.profile)

            if pw_form.is_valid():
                user = pw_form.save()
                update_session_auth_hash(request, user)  # keeps user logged in
                messages.success(request, "Your password has been updated!")
                return redirect("studybuddy:edit_profile")
            else:
                messages.error(request, "Please fix the errors below.")

    context = {"u_form": u_form, "p_form": p_form, "pw_form": pw_form}
    return render(request, "studybuddy/edit_profile.html", context)


@login_required
def profile(request):
    return render(request, "studybuddy/profile.html", {"user": request.user})
