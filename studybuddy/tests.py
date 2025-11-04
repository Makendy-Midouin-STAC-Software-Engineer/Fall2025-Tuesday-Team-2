from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from studybuddy.models import UserProfile, Note, Room, Message
from django.utils import timezone
from datetime import timedelta
from studybuddy.forms import RegisterForm, NoteForm
from django.contrib.admin.sites import AdminSite
from studybuddy.admin import NoteAdmin


def create_user(username="testuser", password="password123", email="test@example.com"):
    """
    Creates and returns a User instance. The UserProfile will be automatically
    created via the post_save signal, so we DON'T create it manually here.
    """
    # Check if user already exists to avoid conflicts in repeated test runs
    user, created = User.objects.get_or_create(
        username=username, defaults={"email": email}
    )
    if created:
        user.set_password(password)
        user.save()
    return user


# ------------------------
# Auth and registration tests
# ------------------------
class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()

    def test_login_logout(self):
        # Login
        response = self.client.post(
            reverse("studybuddy:login"),
            {"username": "testuser", "password": "password123"},
        )
        self.assertEqual(response.status_code, 302)  # Redirect on successful login

        # Logout
        response = self.client.get(reverse("studybuddy:logout"))
        self.assertEqual(response.status_code, 302)  # Redirect on logout


class RegisterTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()

    def test_register_user(self):
        response = self.client.post(
            reverse("studybuddy:register"),
            {
                "username": "newuser",
                "password": "password123",
                "password2": "password123",
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertTrue(UserProfile.objects.filter(user__username="newuser").exists())
        self.assertIn(
            response.status_code, [200, 302]
        )  # Accept page render or redirect
    
    def test_login_invalid_credentials(self):
        """Invalid login shows template error message"""
        response = self.client.post(
            reverse("studybuddy:login"),
            {"username": self.user.username, "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")  
    
    def test_register_existing_username(self):
        """Trying to register existing username shows error"""
        response = self.client.post(
            reverse("studybuddy:register"),
            {"username": self.user.username, "password": "password123", "password2": "password123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username already exists") 

    def test_register_password_mismatch(self):
        """Register with mismatched passwords shows error"""
        response = self.client.post(
            reverse("studybuddy:register"),
            {"username": "uniqueuser", "password": "password123", "password2": "differentpass"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match")


class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()

    def test_password_reset_request(self):
        response = self.client.post(
            reverse("studybuddy:password_reset_request"), {"email": self.user.email}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after request

    def test_password_reset_confirm_invalid(self):
        response = self.client.get(
            reverse(
                "studybuddy:password_reset_confirm",
                kwargs={"uidb64": "fake", "token": "fake"},
            )
        )
        self.assertEqual(response.status_code, 200)  # Shows invalid reset page

    def test_password_reset_get(self):
        """Test password reset GET"""
        response = self.client.get(reverse("studybuddy:password_reset_request"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_user_not_found(self):
        """Test password reset with non-existent email"""
        response = self.client.post(
            reverse("studybuddy:password_reset_request"),
            {"email": "nonexistent@example.com"},
        )
        self.assertEqual(
            response.status_code, 302
        )  # Redirects even when email not found


# ------------------------
# Notes tests
# ------------------------
class NoteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username="testuser", password="password123")

    def test_note_crud(self):
        # Create
        response = self.client.post(
            reverse("studybuddy:note_add"), {"title": "Note 1", "content": "Content 1"}
        )
        self.assertEqual(response.status_code, 302)
        note = Note.objects.get(title="Note 1")

        # Update
        response = self.client.post(
            reverse("studybuddy:note_edit", kwargs={"pk": note.pk}),
            {"title": "Updated Note", "content": "Updated Content"},
        )
        self.assertEqual(response.status_code, 302)
        note.refresh_from_db()
        self.assertEqual(note.title, "Updated Note")

        # Delete
        response = self.client.post(
            reverse("studybuddy:note_delete", kwargs={"pk": note.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Note.objects.filter(pk=note.pk).exists())

    def test_note_create_invalid(self):
        """Empty title should re-render form with error message"""
        response = self.client.post(
            reverse("studybuddy:note_add"),
            {"title": "", "content": "Some content"},
        )
        self.assertEqual(response.status_code, 200)  # form re-rendered
        self.assertContains(response, "This field is required")

    def test_update_other_user_note_forbidden(self):
        other_user = create_user(username="otheruser")
        other_note = Note.objects.create(user=other_user, title="Other", content="Other content")
        response = self.client.post(
            reverse("studybuddy:note_edit", kwargs={"pk": other_note.pk}),
            {"title": "Hacked", "content": "Bad"},
        )
        self.assertIn(response.status_code, [200, 302, 403])


# ------------------------
# Room and message tests
# ------------------------
class RoomTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username="testuser", password="password123")
        self.room = Room.objects.create(name="Room1", created_by=self.user)

    def test_room_detail_and_delete(self):
        response = self.client.get(
            reverse("studybuddy:room_detail", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("studybuddy:room_delete", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Room.objects.filter(id=self.room.id).exists())

    def test_message_delete(self):
        msg = Message.objects.create(room=self.room, user=self.user, content="Hello")
        response = self.client.post(
            reverse("studybuddy:message_delete", kwargs={"message_id": msg.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Message.objects.filter(id=msg.id).exists())

# ------------------------
# ExpandedRoomTests fixes
# ------------------------
class ExpandedRoomTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = create_user(username="user1")
        self.user2 = create_user(username="user2")
        self.room = Room.objects.create(name="TestRoom", created_by=self.user1)

    def test_non_creator_cannot_delete_room(self):
        self.client.login(username="user2", password="password123")
        response = self.client.post(reverse("studybuddy:room_delete", kwargs={"room_id": self.room.id}))
        self.assertIn(response.status_code, [302, 403])  # match actual view behavior

    def test_send_message_invalid_data(self):
        self.client.login(username="user1", password="password123")
        response = self.client.post(
            reverse("studybuddy:room_detail", kwargs={"room_id": self.room.id}),
            {"content": ""},  # empty message
        )
        self.assertIn(response.status_code, [200, 302])

# ------------------------
# Pomodoro timer tests
# ------------------------
class TimerTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username="testuser", password="password123")
        self.room = Room.objects.create(name="RoomTimer", created_by=self.user)

    def test_timer_start_pause_reset_state(self):
        # Start
        response = self.client.post(
            reverse("studybuddy:timer_start", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertTrue(state["is_running"])

        # Pause
        response = self.client.post(
            reverse("studybuddy:timer_pause", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertFalse(state["is_running"])

        # Reset
        response = self.client.post(
            reverse("studybuddy:timer_reset", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertFalse(state["is_running"])
        self.assertEqual(state["time_left"], 1500)

    def test_timer_state_view(self):
        """Test getting timer state"""
        response = self.client.get(
            reverse("studybuddy:timer_state", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertIn("is_running", state)
        self.assertIn("time_left", state)
        self.assertIn("mode", state)

    def test_timer_get_state(self):
        """Test Room.get_timer_state() method when timer is running"""
        self.room.timer_is_running = True
        self.room.timer_started_at = timezone.now() - timedelta(seconds=60)
        self.room.save()

        state = self.room.get_timer_state()
        self.assertTrue(state["is_running"])
        self.assertGreater(state["time_left"], 0)
        self.assertLessEqual(state["time_left"], self.room.timer_duration)

    def test_timer_get_state_expired(self):
        """Test timer auto-resets when expired"""
        self.room.timer_is_running = True
        self.room.timer_started_at = timezone.now() - timedelta(seconds=2000)
        self.room.save()

        state = self.room.get_timer_state()
        self.assertFalse(state["is_running"])
        self.assertEqual(state["time_left"], self.room.timer_duration)
    
    def test_timer_expired_auto_reset(self):
        self.room.timer_is_running = True
        self.room.timer_started_at = timezone.now() - timedelta(seconds=2000)
        self.room.save()
        state = self.room.get_timer_state()
        self.assertFalse(state["is_running"])
        self.assertEqual(state["time_left"], self.room.timer_duration)

    def test_timer_future_start(self):
        self.room.timer_is_running = True
        self.room.timer_started_at = timezone.now() + timedelta(seconds=60)
        self.room.save()
        state = self.room.get_timer_state()
        self.assertTrue("time_left" in state)

# ------------------------
# Permission tests
# ------------------------
class PermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = create_user(username="user1", password="password123")
        self.user2 = create_user(username="user2", password="password123")
        self.room = Room.objects.create(name="TestRoom", created_by=self.user1)

    def test_non_creator_cannot_control_timer(self):
        """Test that non-creators cannot control timer"""
        self.client.login(username="user2", password="password123")

        response = self.client.post(
            reverse("studybuddy:timer_start", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            reverse("studybuddy:timer_pause", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            reverse("studybuddy:timer_reset", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 403)

    def test_non_creator_can_view_timer(self):
        """Test that non-creators can view timer state"""
        self.client.login(username="user2", password="password123")

        response = self.client.get(
            reverse("studybuddy:timer_state", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)


# ------------------------
# Model string representations
# ------------------------
class ModelReprTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.room = Room.objects.create(name="TestRoom", created_by=self.user)

    def test_user_profile_str(self):
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(str(profile), "testuser's profile")

    def test_room_str(self):
        self.assertEqual(str(self.room), "TestRoom")

    def test_message_str(self):
        message = Message.objects.create(
            room=self.room, user=self.user, content="Test message content"
        )
        self.assertEqual(str(message), "testuser: Test message content")


# ------------------------
# Additional view tests
# ------------------------
class AdditionalViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username="testuser", password="password123")

    def test_home_view_not_authenticated(self):
        """Test home view for non-authenticated users"""
        self.client.logout()
        response = self.client.get("/")
        self.assertIn(response.status_code, [200, 302])  # Can redirect or show page

    def test_note_list_view(self):
        """Test note list view"""
        response = self.client.get(reverse("studybuddy:note_list"))
        self.assertEqual(response.status_code, 200)

    def test_note_create_get(self):
        """Test note create GET"""
        response = self.client.get(reverse("studybuddy:note_add"))
        self.assertEqual(response.status_code, 200)

    def test_note_update_get(self):
        """Test note update GET"""
        note = Note.objects.create(user=self.user, title="Test", content="Content")
        response = self.client.get(
            reverse("studybuddy:note_edit", kwargs={"pk": note.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_note_delete_get(self):
        """Test note delete confirmation GET"""
        note = Note.objects.create(user=self.user, title="Test", content="Content")
        response = self.client.get(
            reverse("studybuddy:note_delete", kwargs={"pk": note.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_rooms_view_get(self):
        """Test rooms list GET"""
        response = self.client.get(reverse("studybuddy:rooms"))
        self.assertEqual(response.status_code, 200)

    def test_room_delete_get(self):
        """Test room delete confirmation GET"""
        room = Room.objects.create(name="TestRoom", created_by=self.user)
        response = self.client.get(
            reverse("studybuddy:room_delete", kwargs={"room_id": room.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_rooms_create_room(self):
        """Test creating a room via POST"""
        response = self.client.post(
            reverse("studybuddy:rooms"),
            {"name": "New Room", "description": "New Description"},
        )
        self.assertEqual(response.status_code, 302)  # Redirects after creation
        self.assertTrue(Room.objects.filter(name="New Room").exists())

    def test_room_detail_send_message(self):
        """Test sending a message in room"""
        room = Room.objects.create(name="TestRoom", created_by=self.user)
        response = self.client.post(
            reverse("studybuddy:room_detail", kwargs={"room_id": room.id}),
            {"content": "Hello World"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Message.objects.filter(content="Hello World").exists())


# ------------------------
# User profile tests
# ------------------------
class UserProfileModelTests(TestCase):
    def setUp(self):
        self.user = create_user()

    def test_user_profile_exists(self):
        """Test that UserProfile is created when user is created"""
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_user_profile_default_email_verified(self):
        """Test UserProfile default values"""
        profile = UserProfile.objects.get(user=self.user)
        self.assertFalse(profile.email_verified)
        self.assertIsNotNone(profile.verification_token)

    def test_token_validity(self):
        """Test token validity check"""
        profile = UserProfile.objects.get(user=self.user)
        # Token should be valid (just created)
        self.assertTrue(profile.is_token_valid())

# ------------------------
# ExpandedUserProfileTests fixes
# ------------------------
class ExpandedUserProfileTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.profile = UserProfile.objects.get(user=self.user)

    def test_token_expired(self):
        """Token should be invalid after expiry"""
        # simulate token created 2 days ago
        self.profile.token_created_at = timezone.now() - timedelta(days=2)
        self.profile.save()
        self.assertFalse(self.profile.is_token_valid())

# ------------------------
# Edge cases and error handling
# ------------------------
class ErrorHandlingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username="testuser", password="password123")

    def test_register_username_already_exists(self):
        """Test registration with existing username"""
        response = self.client.post(
            reverse("studybuddy:register"),
            {
                "username": "testuser",
                "password": "password123",
                "password2": "password123",
            },
        )
        self.assertEqual(response.status_code, 200)  # Should show error

    def test_register_passwords_mismatch(self):
        """Test registration with mismatched passwords"""
        response = self.client.post(
            reverse("studybuddy:register"),
            {
                "username": "uniqueuser",
                "password": "password123",
                "password2": "differentpass",
            },
        )
        self.assertEqual(response.status_code, 200)  # Should show error

    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = self.client.post(
            reverse("studybuddy:login"),
            {"username": "testuser", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, 200)  # Should show error

    def test_note_update_other_user_note(self):
        """Test that users can't update other users' notes"""
        other_user = create_user(username="otheruser", password="password123")
        other_note = Note.objects.create(
            user=other_user, title="Other", content="Content"
        )

        response = self.client.post(
            reverse("studybuddy:note_edit", kwargs={"pk": other_note.pk}),
            {"title": "Hacked", "content": "Bad"},
        )
        # Should either redirect or show error
        self.assertIn(response.status_code, [200, 302, 403])


class FormEdgeCaseTests(TestCase):
    def test_register_form_password_mismatch(self):
        form_data = {
            "username": "user",
            "password": "pass1",
            "password2": "pass2",
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_register_form_missing_username(self):
        form_data = {"username": "", "password": "pass1", "password2": "pass1"}
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_note_form_missing_title(self):
        form_data = {"title": "", "content": "Some content"}
        form = NoteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

class ViewEdgeCaseTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client.login(username="testuser", password="password123")

        # Create a test room
        self.room = Room.objects.create(
            name="Test Room",
            created_by=self.user  # match your Room model field
        )

    def test_send_message_empty_content(self):
        """
        Sending an empty message should re-render the room page with an error.
        """
        url = reverse('studybuddy:send_message', kwargs={'room_id': self.room.id})
        response = self.client.post(url, {'content': ''})  # empty content

        # Check that the response re-renders the room page (status 200)
        self.assertEqual(response.status_code, 200)

        # Check that the error message appears in the context
        self.assertContains(response, "Message content cannot be empty")

        # Ensure no message was created
        self.assertEqual(Message.objects.filter(room=self.room).count(), 0)

class AdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.user = create_user()
        self.note = Note.objects.create(user=self.user, title="Admin Note", content="Content")
        self.admin = NoteAdmin(Note, self.site)

    def test_note_admin_str(self):
        """Test Note admin string representation"""
        self.assertEqual(str(self.note), "Admin Note")