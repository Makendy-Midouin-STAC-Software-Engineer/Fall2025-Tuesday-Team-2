from django.urls import path
from . import views

# Required for namespacing
app_name = "studybuddy"

urlpatterns = [
    path("", views.home_view, name="home"),  # Home page
    path("register/", views.custom_register, name="register"),
    path("login/", views.custom_login, name="login"),
    path("logout/", views.custom_logout, name="logout"),
    path("verify-email/<uuid:token>/", views.verify_email, name="verify_email"),
    path(
        "forgot-password/", views.password_reset_request, name="password_reset_request"
    ),
    path(
        "reset-password/<uidb64>/<token>/",
        views.password_reset_confirm,
        name="password_reset_confirm",
    ),
    # Notes URLs
    path("notes/", views.NoteListView.as_view(), name="note_list"),
    path("notes/add/", views.NoteCreateView.as_view(), name="note_add"),
    path("notes/<int:pk>/edit/", views.NoteUpdateView.as_view(), name="note_edit"),
    path("notes/<int:pk>/delete/", views.NoteDeleteView.as_view(), name="note_delete"),
    # Rooms URLs
    path("rooms/", views.rooms, name="rooms"),
    path("room/<int:room_id>/", views.room_detail, name="room_detail"),
    path("room/<int:room_id>/delete/", views.room_delete, name="room_delete"),
    path(
        "message/<int:message_id>/delete/", views.message_delete, name="message_delete"
    ),
    path("join-room/", views.join_room_by_code, name="join_room_by_code"),
    # Pomodoro Timer URLs
    path("room/<int:room_id>/timer/start/", views.timer_start, name="timer_start"),
    path("room/<int:room_id>/timer/pause/", views.timer_pause, name="timer_pause"),
    path("room/<int:room_id>/timer/reset/", views.timer_reset, name="timer_reset"),
    path("room/<int:room_id>/timer/state/", views.timer_state, name="timer_state"),
]
