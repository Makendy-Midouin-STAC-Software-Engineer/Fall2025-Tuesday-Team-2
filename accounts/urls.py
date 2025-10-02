from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home, name="home"),  # home view
    path("signup/", views.signup_view, name="signup"),
    path("registration-complete/", views.registration_complete, name="registration_complete"),
]
