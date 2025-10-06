from django.urls import path
from . import views

app_name = 'studybuddy'

urlpatterns = [
    path('register/', views.custom_register, name='register'),
    path('', views.home, name='home'),            # Home page after login
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
]
