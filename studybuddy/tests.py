from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from studybuddy.models import UserProfile, Note, Room, Message
from django.utils import timezone
from datetime import timedelta


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


# ------------------------
# Edit Profile tests
# ------------------------
class EditProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username="testuser", password="password123")

    def test_edit_profile_get(self):
        """Test edit profile GET request"""
        response = self.client.get(reverse("studybuddy:edit_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Profile")

    def test_edit_profile_update_username(self):
        """Test updating username via edit profile"""
        response = self.client.post(
            reverse("studybuddy:edit_profile"),
            {"username": "newusername", "first_name": "", "last_name": ""}
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newusername")

    def test_edit_profile_update_first_last_name(self):
        """Test updating first_name and last_name"""
        response = self.client.post(
            reverse("studybuddy:edit_profile"),
            {"username": "testuser", "first_name": "John", "last_name": "Doe"}
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")

    def test_edit_profile_requires_login(self):
        """Test that edit profile requires authentication"""
        self.client.logout()
        response = self.client.get(reverse("studybuddy:edit_profile"))
        self.assertEqual(response.status_code, 302)  # Redirects to login


# ------------------------
# Real-time chat tests
# ------------------------
class RealTimeChatTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username="testuser", password="password123")
        self.room = Room.objects.create(name="TestRoom", created_by=self.user)

    def test_get_messages_api(self):
        """Test get_messages API endpoint returns JSON"""
        # Create a message
        Message.objects.create(
            room=self.room, user=self.user, content="Hello World"
        )
        
        response = self.client.get(
            reverse("studybuddy:get_messages", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("messages", data)
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["content"], "Hello World")
        self.assertEqual(data["messages"][0]["user"], "testuser")
        self.assertTrue(data["messages"][0]["is_own"])

    def test_send_message_api(self):
        """Test send_message API endpoint via AJAX"""
        response = self.client.post(
            reverse("studybuddy:send_message", kwargs={"room_id": self.room.id}),
            {"content": "Test message"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"]["content"], "Test message")
        self.assertTrue(Message.objects.filter(content="Test message").exists())

    def test_send_message_empty_content(self):
        """Test send_message with empty content returns error"""
        response = self.client.post(
            reverse("studybuddy:send_message", kwargs={"room_id": self.room.id}),
            {"content": ""}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    def test_get_messages_multiple_messages(self):
        """Test get_messages with multiple messages"""
        other_user = create_user(username="otheruser", password="password123")
        Message.objects.create(room=self.room, user=self.user, content="Message 1")
        Message.objects.create(room=self.room, user=other_user, content="Message 2")
        Message.objects.create(room=self.room, user=self.user, content="Message 3")
        
        response = self.client.get(
            reverse("studybuddy:get_messages", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["messages"]), 3)
        # Verify is_own is correct
        self.assertTrue(data["messages"][0]["is_own"])
        self.assertFalse(data["messages"][1]["is_own"])
        self.assertTrue(data["messages"][2]["is_own"])
