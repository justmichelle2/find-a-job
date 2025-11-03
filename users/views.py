from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import RegistrationForm, LoginForm


def register(request):
    """
    Function-based view for user registration.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Account created successfully! You are now registered as a {"company" if user.is_company else "student"}.'
            )
            login(request, user)
            return redirect('jobs:job_list')
    else:
        form = RegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """
    Function-based view for user login.
    """
    if request.user.is_authenticated:
        return redirect('jobs:job_list')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                # Redirect based on user type
                if user.is_company:
                    return redirect('jobs:my_jobs')
                else:
                    return redirect('jobs:my_applications')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """
    Simple logout view that redirects after logging out.
    """
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('jobs:job_list')
