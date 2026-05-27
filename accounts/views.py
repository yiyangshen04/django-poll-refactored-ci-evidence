from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages

from pollme.messages import SUCCESS_TAGS, WARNING_TAGS
from .forms import UserRegistrationForm


def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            redirect_url = request.GET.get('next', 'home')
            return redirect(redirect_url)
        else:
            messages.error(request, "Username Or Password is incorrect!",
                           extra_tags=WARNING_TAGS)

    return render(request, 'accounts/login.html')


def logout_user(request):
    logout(request)
    return redirect('home')


def create_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Thanks for registering {user.username}.',
                extra_tags=SUCCESS_TAGS,
            )
            return redirect('accounts:login')
        messages.error(request, 'Registration Failed!', extra_tags=WARNING_TAGS)
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})
