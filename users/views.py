from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegistrationForm, LoginForm


def register(request):
    """
    Function-based view for user registration.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
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

@user_passes_test(lambda u: u.is_superuser)
def verify_user(request, user_id, status):
    """
    Admin view to verify or reject a user's account
    """
    from .models import CustomUser
    user = get_object_or_404(CustomUser, pk=user_id)
    
    if status not in [CustomUser.VERIFIED, CustomUser.REJECTED]:
        messages.error(request, "Invalid verification status")
        return redirect('jobs:admin_dashboard')
    
    user.verification_status = status
    user.save()
    
    # Send email notification to user
    status_text = "verified" if status == CustomUser.VERIFIED else "rejected"
    try:
        send_mail(
            subject=f'Account Verification {status_text.capitalize()}',
            message=f'Your account has been {status_text}. {"You can now post jobs." if status == CustomUser.VERIFIED else "Please contact support for more information."}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass
    
    messages.success(request, f"User {user.username} has been {status_text}.")
    return redirect('jobs:admin_dashboard')
