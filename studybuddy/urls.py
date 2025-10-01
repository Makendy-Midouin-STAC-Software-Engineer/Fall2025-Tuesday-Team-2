from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

# Simple homepage view
def home(request):
    return HttpResponse("Welcome to StudyBuddy!")  # replace with render if using a template

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),  # your signup page
    path("accounts/", include("django.contrib.auth.urls")),  # login/logout
    path("", home, name="home"),  # root URL
]
