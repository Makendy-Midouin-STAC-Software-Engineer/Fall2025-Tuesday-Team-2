from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),  # signup page
    path("accounts/", include("django.contrib.auth.urls")),  # login/logout
]
