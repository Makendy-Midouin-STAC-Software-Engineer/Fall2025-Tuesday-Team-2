from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home_view, name="home"),  # home view
    path("signup/", views.signup_view, name="signup"),
    path("registration-complete/", views.registration_complete, name="registration_complete"),
    path('login/', views.dummy_login, name='login'),  # temporary
    path('logout/', views.dummy_logout, name='logout'),  #temporary
]
