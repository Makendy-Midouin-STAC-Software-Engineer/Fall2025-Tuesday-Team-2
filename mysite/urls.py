from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Root URL redirects to login page
    path("", RedirectView.as_view(url="/studybuddy/login/")),
    # Include the studybuddy app URLs with namespace
    path(
        "studybuddy/",
        include(("studybuddy.urls", "studybuddy"), namespace="studybuddy"),
    ),
    # Include built-in auth views for password change, reset, login, logout, etc.
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
]
