from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegistrationForm, LoginForm
from .verification_forms import EmailVerificationForm, VerifyCodeForm
from .models import EmailVerificationCode
from django.utils import timezone
import random
import string


def generate_verification_code():
    """Generate a random 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))


def verify_email(request):
    """View to start email verification process"""
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Generate new verification code
            code = generate_verification_code()
            
            # Save or update verification code
            EmailVerificationCode.objects.filter(email=email).delete()
            verification = EmailVerificationCode.objects.create(
                email=email,
                code=code,
                data={},  # Will be populated when registering
            )

            # Send verification email
            try:
                send_mail(
                    subject='Your Campus Job Board Verification Code',
                    message=f'Your verification code is: {code}\n\nThis code will expire in 10 minutes.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                # Store email in session for the verification step
                request.session['pending_email'] = email
                messages.success(request, "Verification code sent! Please check your email.")
                return redirect('users:verify_code')
            except Exception as e:
                messages.error(request, "Error sending verification email. Please try again.")
                return redirect('users:verify_email')
    else:
        form = EmailVerificationForm()

    return render(request, 'users/verify_email.html', {'form': form})


def verify_code(request):
    """View to verify the email verification code"""
    pending_email = request.session.get('pending_email')
    if not pending_email:
        messages.error(request, "Please start the verification process again.")
        return redirect('users:verify_email')

    if request.method == 'POST':
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                verification = EmailVerificationCode.objects.get(
                    email=pending_email,
                    code=code,
                    is_used=False
                )
                
                if verification.is_valid():
                    # Mark code as used
                    verification.is_used = True
                    verification.save()
                    
                    # Store verified email in session
                    request.session['verified_email'] = pending_email
                    del request.session['pending_email']
                    
                    messages.success(request, "Email verified successfully! You can now create your account.")
                    return redirect('users:register')
                else:
                    messages.error(request, "Verification code has expired. Please request a new one.")
                    return redirect('users:verify_email')
            except EmailVerificationCode.DoesNotExist:
                messages.error(request, "Invalid verification code. Please try again.")
        else:
            messages.error(request, "Please enter a valid 6-digit code.")
    else:
        form = VerifyCodeForm()

    return render(request, 'users/verify_code.html', {'form': form})
from notifications.utils import create_notification
from notifications.models import Notification


def register(request):
    """
    Function-based view for user registration.
    """
    # Check if there is a valid email verification code in session
    verified_email = request.session.get('verified_email')
    stored_data = request.session.get('registration_data', {})

    if not verified_email:
        messages.warning(request, "Please verify your email address first.")
        return redirect('users:verify_email')

    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data.get('email') != verified_email:
                messages.error(request, "Please use the verified email address.")
                return render(request, 'users/register.html', {'form': form})

            user = form.save()
            user.email_verified = True  # Email is pre-verified
            user.save()

            messages.success(request, f'Account created successfully! You can now log in.')
            return redirect('users:login')
    else:
        # Pre-fill the form with stored data if available
        form = RegistrationForm(initial=stored_data)

    return render(request, 'users/register.html', {'form': form})


def verify_email(request, uidb64, token):
    """Verify a user's email address from the verification link."""
    from .models import CustomUser
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except Exception:
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.email_verified = True
        user.save()

        # Create notification for email verification
        create_notification(
            recipient=user,
            notification_type=Notification.EMAIL_VERIFIED,
            title="Email Address Verified",
            message="Your email address has been successfully verified. Thank you!"
        )
        
        messages.success(request, 'Your email has been verified. Thank you!')
        return redirect('users:login')

    messages.error(request, 'The verification link is invalid or has expired.')
    return redirect('users:register')


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
    
    # Create notification for user
    create_notification(
        recipient=user,
        notification_type=Notification.ID_VERIFIED if status == CustomUser.VERIFIED else Notification.ID_REJECTED,
        title=f"Account Verification {status_text.capitalize()}",
        message=f'Your account has been {status_text}. {"You can now post jobs." if status == CustomUser.VERIFIED else "Please contact support for more information."}'
    )
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
