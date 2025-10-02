from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # saves the user
            return redirect('registration_complete')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

def registration_complete(request):
    return render(request, 'accounts/registration_complete.html')

def home(request):
    return render(request, 'accounts/home.html')
