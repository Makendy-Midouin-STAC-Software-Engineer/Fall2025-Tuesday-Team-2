from django.http import HttpResponse
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", lambda request: HttpResponse("Welcome to my Django app! 🎉")),
    path("polls/", include("polls.urls")),
    path("admin/", admin.site.urls),
]
