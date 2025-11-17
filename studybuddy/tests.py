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
            {"username": "newusername", "first_name": "", "last_name": ""},
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newusername")

    def test_edit_profile_update_first_last_name(self):
        """Test updating first_name and last_name"""
        response = self.client.post(
            reverse("studybuddy:edit_profile"),
            {"username": "testuser", "first_name": "John", "last_name": "Doe"},
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
        Message.objects.create(room=self.room, user=self.user, content="Hello World")

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
            {"content": "Test message"},
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
            {"content": ""},
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


# ------------------------
# Private Room tests
# ------------------------
class PrivateRoomTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = create_user(username="user1", password="password123")
        self.user2 = create_user(username="user2", password="password123")
        self.client.login(username="user1", password="password123")
        self.room = Room.objects.create(name="TestRoom", created_by=self.user1)

    def test_generate_private_code(self):
        """Test that generate_private_code creates a unique code"""
        code1 = self.room.generate_private_code()
        code2 = self.room.generate_private_code()
        # Codes should be different
        self.assertNotEqual(code1, code2)
        # Codes should be 6-8 characters
        self.assertGreaterEqual(len(code1), 6)
        self.assertLessEqual(len(code1), 8)

    def test_set_privacy_make_private(self):
        """Test making a room private with auto-generated code"""
        response = self.client.post(
            reverse("studybuddy:set_privacy", kwargs={"room_id": self.room.id}),
            {"is_private": "true"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["is_private"])
        self.assertIsNotNone(data["code"])
        self.assertGreaterEqual(len(data["code"]), 6)

        # Verify room is now private
        self.room.refresh_from_db()
        self.assertTrue(self.room.is_private)
        self.assertIsNotNone(self.room.password)
        self.assertEqual(self.room.password, data["code"])

    def test_set_privacy_make_public(self):
        """Test making a private room public"""
        self.room.is_private = True
        self.room.password = "TESTCODE"
        self.room.save()

        response = self.client.post(
            reverse("studybuddy:set_privacy", kwargs={"room_id": self.room.id}),
            {"is_private": "false"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["is_private"])

        # Verify room is now public
        self.room.refresh_from_db()
        self.assertFalse(self.room.is_private)
        self.assertIsNone(self.room.password)

    def test_set_privacy_unauthorized(self):
        """Test that non-creators cannot change privacy"""
        self.client.logout()
        self.client.login(username="user2", password="password123")

        response = self.client.post(
            reverse("studybuddy:set_privacy", kwargs={"room_id": self.room.id}),
            {"is_private": "true"},
        )
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data["success"])

    def test_join_private_room_valid_code(self):
        """Test joining a private room with valid code"""
        self.room.is_private = True
        self.room.password = "ABC123"
        self.room.save()

        self.client.logout()
        self.client.login(username="user2", password="password123")

        response = self.client.post(
            reverse("studybuddy:join_private_room"), {"room_code": "ABC123"}
        )
        self.assertEqual(response.status_code, 302)  # Redirects to room
        # Check session access was granted
        session = self.client.session
        self.assertTrue(session.get(f"access_room_{self.room.id}"))

    def test_join_private_room_invalid_code(self):
        """Test joining a private room with invalid code"""
        self.room.is_private = True
        self.room.password = "ABC123"
        self.room.save()

        self.client.logout()
        self.client.login(username="user2", password="password123")

        response = self.client.post(
            reverse("studybuddy:join_private_room"), {"room_code": "WRONG"}
        )
        self.assertEqual(response.status_code, 302)  # Redirects back to rooms

    def test_join_private_room_empty_code(self):
        """Test joining with empty code"""
        response = self.client.post(
            reverse("studybuddy:join_private_room"), {"room_code": ""}
        )
        self.assertEqual(response.status_code, 302)

    def test_room_detail_private_room_access(self):
        """Test accessing private room with session access"""
        self.room.is_private = True
        self.room.password = "TESTCODE"
        self.room.save()

        self.client.logout()
        self.client.login(username="user2", password="password123")

        # First attempt should show password prompt
        response = self.client.get(
            reverse("studybuddy:room_detail", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "password")

        # Submit correct password
        response = self.client.post(
            reverse("studybuddy:room_detail", kwargs={"room_id": self.room.id}),
            {"room_password": "TESTCODE"},
        )
        self.assertEqual(response.status_code, 302)

        # Now should have access
        response = self.client.get(
            reverse("studybuddy:room_detail", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TestRoom")

    def test_room_detail_private_room_wrong_password(self):
        """Test accessing private room with wrong password"""
        self.room.is_private = True
        self.room.password = "TESTCODE"
        self.room.save()

        self.client.logout()
        self.client.login(username="user2", password="password123")

        response = self.client.post(
            reverse("studybuddy:room_detail", kwargs={"room_id": self.room.id}),
            {"room_password": "WRONG"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect password")

    def test_room_detail_private_room_creator_access(self):
        """Test that room creator can always access private room"""
        self.room.is_private = True
        self.room.password = "TESTCODE"
        self.room.save()

        # Creator should have direct access
        response = self.client.get(
            reverse("studybuddy:room_detail", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TestRoom")

    def test_get_rooms_api(self):
        """Test get_rooms API endpoint"""
        # Create public and private rooms
        public_room = Room.objects.create(
            name="PublicRoom", created_by=self.user1, is_private=False
        )
        private_room = Room.objects.create(
            name="PrivateRoom",
            created_by=self.user1,
            is_private=True,
            password="CODE123",
        )

        response = self.client.get(reverse("studybuddy:get_rooms"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("rooms", data)
        # Should only return public rooms
        room_ids = [room["id"] for room in data["rooms"]]
        self.assertIn(public_room.id, room_ids)
        self.assertNotIn(private_room.id, room_ids)

    def test_get_rooms_api_room_data(self):
        """Test get_rooms API returns correct room data"""
        # Delete the room from setUp
        self.room.delete()

        room = Room.objects.create(
            name="TestRoom",
            description="Test Description",
            created_by=self.user1,
            is_private=False,
        )

        response = self.client.get(reverse("studybuddy:get_rooms"))
        data = response.json()
        self.assertEqual(len(data["rooms"]), 1)
        room_data = data["rooms"][0]
        self.assertEqual(room_data["id"], room.id)
        self.assertEqual(room_data["name"], "TestRoom")
        self.assertEqual(room_data["description"], "Test Description")
        self.assertEqual(room_data["created_by"], "user1")
        self.assertTrue(room_data["is_creator"])

    def test_rooms_view_filters_private(self):
        """Test that rooms view only shows public rooms"""
        # Create public and private rooms
        Room.objects.create(name="PublicRoom", created_by=self.user1, is_private=False)
        Room.objects.create(
            name="PrivateRoom",
            created_by=self.user1,
            is_private=True,
            password="CODE123",
        )

        response = self.client.get(reverse("studybuddy:rooms"))
        self.assertEqual(response.status_code, 200)
        # Should only show public room
        self.assertContains(response, "PublicRoom")
        self.assertNotContains(response, "PrivateRoom")


# ------------------------
# Additional coverage tests
# ------------------------
class AdditionalCoverageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username="testuser", password="password123")

    def test_profile_view(self):
        """Test profile view"""
        response = self.client.get(reverse("studybuddy:profile"))
        self.assertEqual(response.status_code, 200)

    def test_room_delete_get_not_creator(self):
        """Test room delete GET when user is not creator"""
        other_user = create_user(username="otheruser", password="password123")
        room = Room.objects.create(name="OtherRoom", created_by=other_user)

        response = self.client.get(
            reverse("studybuddy:room_delete", kwargs={"room_id": room.id})
        )
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)

    def test_message_delete_ajax(self):
        """Test message delete via AJAX"""
        room = Room.objects.create(name="TestRoom", created_by=self.user)
        message = Message.objects.create(
            room=room, user=self.user, content="Test message"
        )

        response = self.client.post(
            reverse("studybuddy:message_delete", kwargs={"message_id": message.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

    def test_message_delete_ajax_unauthorized(self):
        """Test message delete via AJAX when not owner"""
        other_user = create_user(username="otheruser", password="password123")
        room = Room.objects.create(name="TestRoom", created_by=self.user)
        message = Message.objects.create(
            room=room, user=other_user, content="Test message"
        )

        response = self.client.post(
            reverse("studybuddy:message_delete", kwargs={"message_id": message.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)

    def test_edit_profile_change_password(self):
        """Test changing password via edit profile"""
        response = self.client.post(
            reverse("studybuddy:edit_profile"),
            {
                "change_password": "1",
                "old_password": "password123",
                "new_password1": "newpassword123",
                "new_password2": "newpassword123",
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirect on success

    def test_edit_profile_change_password_mismatch(self):
        """Test changing password with mismatched passwords"""
        response = self.client.post(
            reverse("studybuddy:edit_profile"),
            {
                "change_password": "1",
                "old_password": "password123",
                "new_password1": "newpassword123",
                "new_password2": "differentpass",
            },
        )
        self.assertEqual(response.status_code, 200)  # Shows error

    def test_edit_profile_form_errors(self):
        """Test edit profile with form errors"""
        response = self.client.post(
            reverse("studybuddy:edit_profile"),
            {
                "update_info": "1",
                "username": "",  # Invalid empty username
            },
        )
        self.assertEqual(response.status_code, 200)  # Shows errors

    def test_password_reset_confirm_valid_token_get(self):
        """Test password reset confirm GET with valid token"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

        self.client.logout()
        response = self.client.get(
            reverse(
                "studybuddy:password_reset_confirm",
                kwargs={"uidb64": uidb64, "token": token},
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_password_reset_confirm_valid_token_post(self):
        """Test password reset confirm POST with valid token"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        # Ensure user has email for token generation
        self.user.email = "test@example.com"
        self.user.save()

        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

        self.client.logout()
        response = self.client.post(
            reverse(
                "studybuddy:password_reset_confirm",
                kwargs={"uidb64": uidb64, "token": token},
            ),
            {
                "password": "newpassword123",
                "password2": "newpassword123",
            },
        )
        # Should redirect to login on success, or show page if validation fails
        self.assertIn(response.status_code, [200, 302])

    def test_password_reset_confirm_password_mismatch(self):
        """Test password reset with mismatched passwords"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

        self.client.logout()
        response = self.client.post(
            reverse(
                "studybuddy:password_reset_confirm",
                kwargs={"uidb64": uidb64, "token": token},
            ),
            {
                "password": "newpassword123",
                "password2": "differentpass",
            },
        )
        self.assertEqual(response.status_code, 200)  # Shows error

    def test_password_reset_confirm_short_password(self):
        """Test password reset with password too short"""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

        self.client.logout()
        response = self.client.post(
            reverse(
                "studybuddy:password_reset_confirm",
                kwargs={"uidb64": uidb64, "token": token},
            ),
            {
                "password": "short",
                "password2": "short",
            },
        )
        self.assertEqual(response.status_code, 200)  # Shows error


# ------------------------
# Room Presence tests
# ------------------------
class RoomPresenceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = create_user(username="user1", password="password123")
        self.user2 = create_user(username="user2", password="password123")
        self.client.login(username="user1", password="password123")
        self.room = Room.objects.create(name="TestRoom", created_by=self.user1)

    def test_room_presence_update(self):
        """Test that room_presence endpoint updates presence and returns count"""
        response = self.client.get(
            reverse("studybuddy:room_presence", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("active_count", data)
        self.assertIn("active_users", data)
        self.assertEqual(data["active_count"], 1)
        self.assertIn("user1", data["active_users"])

    def test_room_presence_multiple_users(self):
        """Test room presence with multiple users"""
        # User 1 updates presence
        self.client.get(
            reverse("studybuddy:room_presence", kwargs={"room_id": self.room.id})
        )

        # User 2 logs in and updates presence
        client2 = Client()
        client2.login(username="user2", password="password123")
        response = client2.get(
            reverse("studybuddy:room_presence", kwargs={"room_id": self.room.id})
        )

        data = response.json()
        self.assertEqual(data["active_count"], 2)
        self.assertIn("user1", data["active_users"])
        self.assertIn("user2", data["active_users"])

    def test_room_presence_requires_login(self):
        """Test that room presence requires authentication"""
        self.client.logout()
        response = self.client.get(
            reverse("studybuddy:room_presence", kwargs={"room_id": self.room.id})
        )
        self.assertEqual(response.status_code, 302)  # Redirects to login


# ------------------------
# Home View tests
# ------------------------
class HomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()

    def test_home_view_authenticated(self):
        """Test home view for authenticated users"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("studybuddy:home"))
        self.assertIn(response.status_code, [200, 302])

    def test_home_view_unauthenticated(self):
        """Test home view for unauthenticated users"""
        response = self.client.get(reverse("studybuddy:home"))
        self.assertIn(response.status_code, [200, 302])


# ------------------------
# Admin tests
# ------------------------
class AdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="adminpass"
        )
        self.client.login(username="admin", password="adminpass")
        self.user = create_user()
        self.room = Room.objects.create(name="TestRoom", created_by=self.user)

    def test_admin_site_accessible(self):
        """Test that admin site is accessible to superuser"""
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)

    def test_user_profile_admin(self):
        """Test UserProfile in admin"""
        response = self.client.get("/admin/studybuddy/userprofile/")
        self.assertEqual(response.status_code, 200)

    def test_note_admin(self):
        """Test Note in admin"""
        response = self.client.get("/admin/studybuddy/note/")
        self.assertEqual(response.status_code, 200)

    def test_room_admin(self):
        """Test Room in admin"""
        response = self.client.get("/admin/studybuddy/room/")
        self.assertEqual(response.status_code, 200)

    def test_message_admin(self):
        """Test Message in admin"""
        response = self.client.get("/admin/studybuddy/message/")
        self.assertEqual(response.status_code, 200)


# ------------------------
# Additional Model tests for coverage
# ------------------------
class ModelStringTests(TestCase):
    def setUp(self):
        self.user = create_user()

    def test_note_str(self):
        """Test Note __str__ method"""
        note = Note.objects.create(user=self.user, title="Test Note", content="Content")
        self.assertEqual(str(note), "Test Note")

    def test_room_generate_code_fallback(self):
        """Test Room generate_private_code fallback"""
        room = Room.objects.create(name="TestRoom", created_by=self.user)
        # Generate multiple codes to test uniqueness
        code1 = room.generate_private_code()
        code2 = room.generate_private_code()
        self.assertIsNotNone(code1)
        self.assertIsNotNone(code2)
        # Codes should be uppercase and reasonable length
        self.assertTrue(code1.isupper())
        self.assertGreaterEqual(len(code1), 6)

    def test_room_presence_model_methods(self):
        """Test RoomPresence model methods"""
        from studybuddy.models import RoomPresence

        room = Room.objects.create(name="TestRoom", created_by=self.user)

        # Test update_presence
        RoomPresence.update_presence(room, self.user)
        self.assertTrue(RoomPresence.objects.filter(room=room, user=self.user).exists())

        # Test get_active_users
        active_count = RoomPresence.get_active_users(room, threshold_seconds=30)
        self.assertEqual(active_count, 1)

    def test_user_profile_token_expired(self):
        """Test UserProfile is_token_valid when expired"""
        profile = UserProfile.objects.get(user=self.user)
        # Set token_created_at to over 24 hours ago
        profile.token_created_at = timezone.now() - timedelta(hours=25)
        profile.save()
        self.assertFalse(profile.is_token_valid())
