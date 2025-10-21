from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from studybuddy.models import UserProfile, Note, Room, Message
from django.utils import timezone
from datetime import timedelta

def create_user(username='testuser', password='password123', email='test@example.com'):
    """
    Creates and returns a User instance. The UserProfile will be automatically
    created via the post_save signal, so we DON'T create it manually here.
    """
    # Check if user already exists to avoid conflicts in repeated test runs
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': email}
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
        response = self.client.post(reverse('studybuddy:login'), {'username': 'testuser', 'password': 'password123'})
        self.assertEqual(response.status_code, 302)  # Redirect on successful login

        # Logout
        response = self.client.get(reverse('studybuddy:logout'))
        self.assertEqual(response.status_code, 302)  # Redirect on logout

class RegisterTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_user(self):
        response = self.client.post(reverse('studybuddy:register'), {
            'username': 'newuser',
            'password': 'password123',
            'password2': 'password123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(UserProfile.objects.filter(user__username='newuser').exists())
        self.assertIn(response.status_code, [200, 302])  # Accept page render or redirect


class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()

    def test_password_reset_request(self):
        response = self.client.post(reverse('studybuddy:password_reset_request'), {'email': self.user.email})
        self.assertEqual(response.status_code, 302)  # Redirect after request

    def test_password_reset_confirm_invalid(self):
        response = self.client.get(reverse('studybuddy:password_reset_confirm', kwargs={'uidb64': 'fake', 'token': 'fake'}))
        self.assertEqual(response.status_code, 200)  # Shows invalid reset page

# ------------------------
# Notes tests
# ------------------------
class NoteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username='testuser', password='password123')

    def test_note_crud(self):
        # Create
        response = self.client.post(reverse('studybuddy:note_add'), {'title': 'Note 1', 'content': 'Content 1'})
        self.assertEqual(response.status_code, 302)
        note = Note.objects.get(title='Note 1')

        # Update
        response = self.client.post(reverse('studybuddy:note_edit', kwargs={'pk': note.pk}),
                                    {'title': 'Updated Note', 'content': 'Updated Content'})
        self.assertEqual(response.status_code, 302)
        note.refresh_from_db()
        self.assertEqual(note.title, 'Updated Note')

        # Delete
        response = self.client.post(reverse('studybuddy:note_delete', kwargs={'pk': note.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Note.objects.filter(pk=note.pk).exists())

# ------------------------
# Room and message tests
# ------------------------
class RoomTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username='testuser', password='password123')
        self.room = Room.objects.create(name='Room1', created_by=self.user)

    def test_room_detail_and_delete(self):
        response = self.client.get(reverse('studybuddy:room_detail', kwargs={'room_id': self.room.id}))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('studybuddy:room_delete', kwargs={'room_id': self.room.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Room.objects.filter(id=self.room.id).exists())

    def test_message_delete(self):
        msg = Message.objects.create(room=self.room, user=self.user, content='Hello')
        response = self.client.post(reverse('studybuddy:message_delete', kwargs={'message_id': msg.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Message.objects.filter(id=msg.id).exists())

# ------------------------
# Pomodoro timer tests
# ------------------------
class TimerTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_user()
        self.client.login(username='testuser', password='password123')
        self.room = Room.objects.create(name='RoomTimer', created_by=self.user)

    def test_timer_start_pause_reset_state(self):
        # Start
        response = self.client.post(reverse('studybuddy:timer_start', kwargs={'room_id': self.room.id}))
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertTrue(state['is_running'])

        # Pause
        response = self.client.post(reverse('studybuddy:timer_pause', kwargs={'room_id': self.room.id}))
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertFalse(state['is_running'])

        # Reset
        response = self.client.post(reverse('studybuddy:timer_reset', kwargs={'room_id': self.room.id}))
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertFalse(state['is_running'])
        self.assertEqual(state['time_left'], 1500)
