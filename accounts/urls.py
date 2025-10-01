from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('registration-complete/', views.registration_complete, name='registration_complete'),
]
