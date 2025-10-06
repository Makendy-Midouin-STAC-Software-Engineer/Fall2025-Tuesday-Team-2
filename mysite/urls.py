from django.http import HttpResponse
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", lambda request: HttpResponse("Welcome to my Django app! 🎉")),  # optional homepage
    path("polls/", include("polls.urls")),  # include your app routes (includes logout)
    path("admin/", admin.site.urls),
]

