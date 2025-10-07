from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('studybuddy:home')  # change 'home' to whatever page you want after login
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'studybuddy/login.html')


def custom_logout(request):
    logout(request)
    return render(request, 'studybuddy/logout.html')


def home(request):
    return render(request, 'studybuddy/home.html')  # simple homepage after login

def custom_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            login(request, user)  # auto login after registration
            return redirect('studybuddy:home')
    return render(request, 'studybuddy/register.html')