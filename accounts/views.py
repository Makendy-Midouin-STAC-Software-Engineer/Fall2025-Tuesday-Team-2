from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def home_view(request):
    return render(request, "home.html")

def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save() # create the user
            return redirect('registration_complete')  # redirect to confirmation page
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})

# accounts/views.py
def registration_complete(request):
    return render(request, 'accounts/registration_complete.html')

