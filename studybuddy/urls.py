from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home page
    path('', accounts_views.home_view, name='home'),

    # Accounts app
    path('accounts/', include('accounts.urls')),  # all accounts URLs are here
]
