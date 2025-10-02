from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def dummy_login(request):
    # This is just a placeholder for testing
    return render(request, 'accounts/dummy_login.html')

def dummy_logout(request):
    return render(request, 'accounts/dummy_logout.html')

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # saves the user
            return redirect('accounts:registration_complete')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

def registration_complete(request):
    return render(request, 'accounts/registration_complete.html')

def home_view(request):
    return render(request, 'accounts/home.html')
