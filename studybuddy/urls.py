from django.urls import path
from . import views

# Required for namespacing
app_name = "studybuddy"

urlpatterns = [
    path("", views.home_view, name="home"),  # Home page
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("register/", views.custom_register, name="register"),
    path("login/", views.custom_login, name="login"),
    path("logout/", views.custom_logout, name="logout"),
    path(
        "forgot-password/", views.password_reset_request, name="password_reset_request"
    ),
    path(
        "reset-password/<uidb64>/<token>/",
        views.password_reset_confirm,
        name="password_reset_confirm",
    ),
    # Profile URL
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    # Notes URLs
    path("notes/", views.NoteListView.as_view(), name="note_list"),
    path("notes/add/", views.NoteCreateView.as_view(), name="note_add"),
    path("notes/<int:pk>/edit/", views.NoteUpdateView.as_view(), name="note_edit"),
    path("notes/<int:pk>/delete/", views.NoteDeleteView.as_view(), name="note_delete"),
    # Rooms URLs
    path("rooms/", views.rooms, name="rooms"),
    path("rooms/api/", views.get_rooms, name="get_rooms"),
    path("rooms/join/", views.join_private_room, name="join_private_room"),
    path("room/<int:room_id>/", views.room_detail, name="room_detail"),
    path(
        "room/<int:room_id>/set_privacy/",
        views.set_privacy,
        name="set_privacy",
    ),
    path("room/<int:room_id>/delete/", views.room_delete, name="room_delete"),
    path("room/<int:room_id>/messages/", views.get_messages, name="get_messages"),
    path("room/<int:room_id>/send-message/", views.send_message, name="send_message"),
    path(
        "message/<int:message_id>/delete/", views.message_delete, name="message_delete"
    ),
    # Pomodoro Timer URLs
    path("room/<int:room_id>/timer/start/", views.timer_start, name="timer_start"),
    path("room/<int:room_id>/timer/pause/", views.timer_pause, name="timer_pause"),
    path("room/<int:room_id>/timer/reset/", views.timer_reset, name="timer_reset"),
    path("room/<int:room_id>/timer/state/", views.timer_state, name="timer_state"),
    # Real-time chat API
    path("room/<int:room_id>/messages/", views.get_messages, name="get_messages"),
    path("room/<int:room_id>/send-message/", views.send_message, name="send_message"),
]
