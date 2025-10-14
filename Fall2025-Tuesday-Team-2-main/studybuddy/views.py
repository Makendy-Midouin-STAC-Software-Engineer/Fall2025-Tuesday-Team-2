# File: studybuddy/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Room, Message

# ---- Authentication Views ----
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('studybuddy:rooms')
    else:
        form = UserCreationForm()
    return render(request, 'studybuddy/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('studybuddy:rooms')
    else:
        form = AuthenticationForm()
    return render(request, 'studybuddy/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('studybuddy:login')

# ---- Main App Views ----
@login_required
def rooms(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            Room.objects.create(name=name, description=description, created_by=request.user)
        return redirect('studybuddy:rooms')

    all_rooms = Room.objects.all().order_by('-created_at')
    return render(request, 'studybuddy/rooms.html', {'rooms': all_rooms})

@login_required
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    messages = room.messages.order_by('timestamp')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(room=room, user=request.user, content=content)
        return redirect('studybuddy:room_detail', room_id=room.id)

    context = {'room': room, 'messages': messages}
    return render(request, 'studybuddy/room_detail.html', context)
