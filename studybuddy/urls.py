from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views  # import from accounts app

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),  # signup/login
    path("accounts/", include("django.contrib.auth.urls")),
    path("", account_views.home_view, name="home"),  # root URL uses accounts.views.home_view
]
