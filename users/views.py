from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
# from .forms import RegisterForm
from django.contrib import messages
from .forms import CustomUserCreationForm
from library.models import UserProfile

# def register_view(request):
#     if request.method == 'POST':
#         form = RegisterForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             return redirect('dashboard')
#     else:
#         form = RegisterForm()
#     return render(request, 'users/register.html', {'form': form})
def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')  # or your homepage
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, 'Недійсні дані для входу')
    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')
