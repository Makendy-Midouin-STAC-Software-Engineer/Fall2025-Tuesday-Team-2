from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Note, Room, Message


# -----------------------------
# AUTHENTICATION VIEWS
# -----------------------------

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('studybuddy:note_list')  # redirect to notes list after login
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'studybuddy/login.html')


def custom_logout(request):
    logout(request)
    return render(request, 'studybuddy/logout.html')


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
            login(request, user)
            return redirect('studybuddy:note_list')  # redirect to notes list after registration
    return render(request, 'studybuddy/register.html')


def home_view(request):
    if request.user.is_authenticated:
        return render(request, 'studybuddy/home_logged_in.html', {'username': request.user.username})
    else:
        return render(request, 'studybuddy/home.html')


# -----------------------------
# NOTES FEATURE
# -----------------------------

@login_required
def notes_home(request):
    """Simple notes homepage (placeholder)"""
    return render(request, 'notes/home.html')


class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = 'studybuddy/note_list.html'
    context_object_name = 'notes'

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user).order_by('-updated_at')


class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    fields = ['title', 'content']
    template_name = 'studybuddy/note_form.html'
    success_url = reverse_lazy('studybuddy:note_list')
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    fields = ['title', 'content']
    template_name = 'studybuddy/note_form.html'
    success_url = reverse_lazy('studybuddy:note_list')

class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    template_name = 'studybuddy/note_confirm_delete.html'
    success_url = reverse_lazy('studybuddy:note_list')


# -----------------------------
# ROOMS & MESSAGES FEATURE
# -----------------------------

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
    room_messages = room.messages.order_by('timestamp')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(room=room, user=request.user, content=content)
        return redirect('studybuddy:room_detail', room_id=room.id)

    context = {'room': room, 'messages': room_messages}
    return render(request, 'studybuddy/room_detail.html', context)
