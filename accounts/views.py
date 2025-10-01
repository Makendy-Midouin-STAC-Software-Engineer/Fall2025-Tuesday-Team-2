from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")  # after signup, redirect to login
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})
