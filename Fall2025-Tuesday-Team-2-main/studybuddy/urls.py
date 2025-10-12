from django.urls import path
from . import views

app_name = 'studybuddy'

urlpatterns = [
    path('', views.rooms, name='rooms'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

