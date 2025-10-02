from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

# Home view
def home_view(request):
    logged_in = request.session.get('logged_in', False)
    username = request.session.get('username', '')
    return render(request, 'accounts/home.html', {'logged_in': logged_in, 'username': username})

# Dummy login
def dummy_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', 'guest')
        request.session['logged_in'] = True
        request.session['username'] = username
        return redirect('accounts:home')
    return render(request, 'accounts/dummy_login.html')

# Dummy logout
def dummy_logout(request):
    request.session['logged_in'] = False
    request.session['username'] = ''
    return redirect('accounts:home')

# Signup view
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts:registration_complete')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

# Registration complete
def registration_complete(request):
    return render(request, 'accounts/registration_complete.html')
