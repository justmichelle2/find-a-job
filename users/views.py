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
from .verification_forms import EmailVerificationForm, VerifyCodeForm, ChooseVerificationMethodForm
from .models import EmailVerificationCode
from .models import PhoneVerificationCode
from django.utils import timezone
from datetime import timedelta
import random
import string


def debug_send_mail(subject, message, from_email, recipient_list, fail_silently=False):
    """Send mail and always print contents to console in development for visibility."""
    try:
        # Print to console for developer visibility regardless of backend
        print("\n=== Outgoing email ===")
        print(f"To: {recipient_list}")
        print(f"Subject: {subject}")
        print("Body:\n" + message)
        print("=== End email ===\n")
    except Exception:
        pass
    # Call Django's send_mail; it will use the configured backend
    return send_mail(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list, fail_silently=fail_silently)


def generate_verification_code():
    """Generate a random 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))


def start_email_verification(request):
    """View to start email verification process"""
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            from datetime import timedelta
            # Rate limiting: don't allow rapid resends and limit per-hour sends (configurable)
            RESEND_INTERVAL_SECONDS = getattr(settings, 'VERIFICATION_RESEND_INTERVAL_SECONDS', 60)
            MAX_PER_HOUR = getattr(settings, 'VERIFICATION_MAX_PER_HOUR', 5)

            recent = EmailVerificationCode.objects.filter(
                email=email,
                created_at__gte=timezone.now() - timedelta(seconds=RESEND_INTERVAL_SECONDS)
            )
            if recent.exists():
                messages.error(request, f'Please wait a bit before requesting another code (at least {RESEND_INTERVAL_SECONDS} seconds).')
                return redirect('users:start_verification')

            hourly_count = EmailVerificationCode.objects.filter(
                email=email,
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).count()
            if hourly_count >= MAX_PER_HOUR:
                messages.error(request, 'You have requested verification too many times. Please try again later.')
                return redirect('users:start_verification')

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
                debug_send_mail(
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

    return render(request, 'users/start_verification.html', {'form': form})


def verify_code(request):
    """View to verify the email verification code"""
    if not request.user.is_authenticated:
        messages.error(request, "Please log in first.")
        return redirect('users:login')
    
    pending_email = request.session.get('pending_email')
    if not pending_email:
        messages.error(request, "Please start the verification process again.")
        return redirect('users:choose_verification_method')

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
                    
                    # Mark user's email as verified (admin verification remains separate)
                    request.user.email_verified = True
                    request.user.save()
                    
                    # Clean up session
                    if 'pending_email' in request.session:
                        del request.session['pending_email']
                    if 'verification_method' in request.session:
                        del request.session['verification_method']
                    
                    messages.success(request, "Email verified successfully! You now have full access.")
                    return redirect('jobs:job_list')
                else:
                    messages.error(request, "Verification code has expired. Please request a new one.")
                    return redirect('users:choose_verification_method')
            except EmailVerificationCode.DoesNotExist:
                messages.error(request, "Invalid verification code. Please try again.")
        else:
            messages.error(request, "Please enter a valid 6-digit code.")
    else:
        form = VerifyCodeForm()

    # Pass pending email to the template so it can show where the code was sent
    return render(request, 'users/verify_code.html', {'form': form, 'pending_email': pending_email})


def resend_verification_code(request):
    """Resend a verification code to the pending email in session (with rate limits)."""
    pending_email = request.session.get('pending_email')
    if not pending_email:
        messages.error(request, "No pending email to verify. Please start the verification process again.")
        return redirect('users:start_verification')

    from datetime import timedelta
    RESEND_INTERVAL_SECONDS = getattr(settings, 'VERIFICATION_RESEND_INTERVAL_SECONDS', 60)
    MAX_PER_HOUR = getattr(settings, 'VERIFICATION_MAX_PER_HOUR', 5)

    # Enforce rate limits
    recent = EmailVerificationCode.objects.filter(
        email=pending_email,
        created_at__gte=timezone.now() - timedelta(seconds=RESEND_INTERVAL_SECONDS)
    )
    if recent.exists():
        messages.error(request, f'Please wait at least {RESEND_INTERVAL_SECONDS} seconds before requesting another code.')
        return redirect('users:verify_code')

    hourly_count = EmailVerificationCode.objects.filter(
        email=pending_email,
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    if hourly_count >= MAX_PER_HOUR:
        messages.error(request, 'You have requested verification too many times. Please try again later.')
        return redirect('users:verify_code')

    # Generate and store new code
    code = generate_verification_code()
    # Use update_or_create to avoid UNIQUE constraint errors
    EmailVerificationCode.objects.update_or_create(
        email=pending_email,
        defaults={'code': code, 'data': {}, 'is_used': False, 'expires_at': timezone.now() + timedelta(minutes=10)}
    )

    # Send email
    try:
        debug_send_mail(
            subject='Your Campus Job Board Verification Code',
            message=f'Your verification code is: {code}\n\nThis code will expire in 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pending_email],
            fail_silently=False,
        )
        messages.success(request, 'A new verification code has been sent to your email.')
    except Exception:
        import traceback
        traceback.print_exc()
        messages.error(request, 'Failed to send verification email. Please try again later.')

    return redirect('users:verify_code')


def send_sms(phone_number, message):
    """Send SMS using Twilio."""
    from django.conf import settings
    # Ensure credentials are configured
    if not (getattr(settings, 'TWILIO_ACCOUNT_SID', '') and getattr(settings, 'TWILIO_AUTH_TOKEN', '') and getattr(settings, 'TWILIO_FROM_NUMBER', '')):
        print('Twilio credentials not configured (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM_NUMBER).')
        return False

    # Import Twilio client
    try:
        from twilio.rest import Client
    except ImportError:
        print("Twilio package not installed. Install with: pip install twilio")
        return False

    # Initialize Twilio client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Send message
    try:
        client.messages.create(
            body=message,
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone_number
        )
        return True
    except Exception as e:
        print(f"Failed to send SMS to {phone_number}: {e}")
        return False


def start_phone_verification(request):
    """Generate and send a phone verification code for the current user's phone.

    Must be logged in and have a phone number set on the user.
    """
    from django.contrib.auth.decorators import login_required
    from django.shortcuts import redirect

    @login_required
    def inner(request):
        user = request.user
        phone = getattr(user, 'phone_number', None)
        if not phone:
            from django.contrib import messages
            messages.error(request, 'No phone number found on your account. Please add one to your profile.')
            return redirect('users:register')

        from datetime import timedelta
        # Rate limiting: prevent rapid resends and cap sends per hour (configurable)
        RESEND_INTERVAL_SECONDS = getattr(settings, 'VERIFICATION_RESEND_INTERVAL_SECONDS', 60)
        MAX_PER_HOUR = getattr(settings, 'VERIFICATION_MAX_PER_HOUR', 5)

        recent = PhoneVerificationCode.objects.filter(
            phone=phone,
            created_at__gte=timezone.now() - timedelta(seconds=RESEND_INTERVAL_SECONDS)
        )
        if recent.exists():
            from django.contrib import messages
            messages.error(request, f'Please wait a bit before requesting another code (at least {RESEND_INTERVAL_SECONDS} seconds).')
            return redirect('jobs:job_list')

        hourly_count = PhoneVerificationCode.objects.filter(
            phone=phone,
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        if hourly_count >= MAX_PER_HOUR:
            from django.contrib import messages
            messages.error(request, 'You have requested verification too many times. Please try again later.')
            return redirect('jobs:job_list')

        # Remove any existing unused codes for this phone
        PhoneVerificationCode.objects.filter(phone=phone, is_used=False).delete()

        # Generate code and save
        code = generate_verification_code()
        PhoneVerificationCode.objects.create(phone=phone, code=code)

        # Send SMS (placeholder)
        sent = send_sms(phone, f'Your Campus Job Board verification code is: {code}. It expires in 10 minutes.')

        from django.contrib import messages
        if sent:
            messages.success(request, 'Verification code sent to your phone.')
        else:
            messages.warning(request, 'Could not send SMS. Please try email verification or contact support.')

        # store pending phone in session for the verification step
        request.session['pending_phone'] = phone
        return redirect('users:verify_phone')

    return inner(request)


def verify_phone(request):
    """View to accept a phone verification code and mark the user's phone verified."""
    from django.contrib.auth.decorators import login_required
    from django.shortcuts import redirect
    from django.contrib import messages

    @login_required
    def inner(request):
        pending_phone = request.session.get('pending_phone') or getattr(request.user, 'phone_number', None)
        if not pending_phone:
            messages.error(request, 'No phone verification is in progress. Start verification first.')
            return redirect('jobs:job_list')

        if request.method == 'POST':
            code = request.POST.get('code')
            if not code:
                messages.error(request, 'Please enter the verification code.')
                return render(request, 'users/verify_phone.html', {'phone': pending_phone})

            try:
                verification = PhoneVerificationCode.objects.get(phone=pending_phone, code=code, is_used=False)
            except PhoneVerificationCode.DoesNotExist:
                messages.error(request, 'Invalid verification code. Please try again.')
                return render(request, 'users/verify_phone.html', {'phone': pending_phone})

            if verification.is_valid():
                verification.is_used = True
                verification.save()
                user = request.user
                user.phone_verified = True
                user.email_verified = True  # Mark contact verified; admin verification handled separately
                user.save()

                # Clean up session
                if 'pending_phone' in request.session:
                    del request.session['pending_phone']
                if 'verification_method' in request.session:
                    del request.session['verification_method']

                # Create notification
                try:
                    create_notification(
                        recipient=user,
                        notification_type=Notification.PHONE_VERIFIED if hasattr(Notification, 'PHONE_VERIFIED') else Notification.EMAIL_VERIFIED,
                        title='Phone Number Verified',
                        message='Your phone number has been successfully verified.'
                    )
                except Exception:
                    pass

                messages.success(request, 'Phone number verified successfully! You now have full access.')
                return redirect('jobs:job_list')
            else:
                messages.error(request, 'Verification code expired. Request a new one.')
                return redirect('users:start_phone_verification')

        return render(request, 'users/verify_phone.html', {'phone': pending_phone})

    return inner(request)
from notifications.utils import create_notification
from notifications.models import Notification


def register(request):
    """
    Function-based view for user registration.
    """
    # Require that the user first choose account type on a separate page
    account_choice = request.session.get('account_type') or request.GET.get('type')
    if not account_choice:
        return redirect('users:choose_account_type')

    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES, account_choice=account_choice)
        
        # DEBUG: Log form validation errors
        if not form.is_valid():
            print("=" * 60)
            print("REGISTRATION FORM VALIDATION FAILED")
            print("=" * 60)
            for field, errors in form.errors.items():
                print(f"Field '{field}': {errors}")
            print("=" * 60)
        
        if form.is_valid():
            # Save without committing to allow overriding username / names
            user = form.save(commit=False)

            # Determine user type from session or GET param
            is_company = True if account_choice == 'company' else False
            user.is_company = is_company

            # For company accounts: use the institution as the username and clear first/last name
            if is_company:
                inst = form.cleaned_data.get('institution') or ''
                # create a sensible username from the institution
                import re
                uname = re.sub(r"[^A-Za-z0-9]+", '_', inst.strip()).strip('_').lower()[:30] or form.cleaned_data.get('username')
                # ensure uniqueness
                from .models import CustomUser
                base = uname
                i = 1
                while CustomUser.objects.filter(username=uname).exists():
                    uname = f"{base}_{i}"
                    i += 1
                user.username = uname
                user.first_name = ''
                user.last_name = ''
            else:
                # For student accounts, ensure username is sensible (cleaned in form)
                pass

            # Save the user account WITHOUT sending verification yet
            user.save()

            # Log the user in immediately after account creation
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            
            # Store user info in session for verification page
            request.session['pending_verification'] = True
            request.session['user_email'] = user.email
            request.session['user_phone'] = getattr(user, 'phone_number', None)

            messages.success(request, 'Account created successfully! Please verify your email or phone.')
            return redirect('users:choose_verification_method')
    else:
        form = RegistrationForm(account_choice=account_choice)

    # Pass the account_choice to the template so we can hide/show fields client-side
    return render(request, 'users/register.html', {'form': form, 'account_choice': account_choice})


def choose_account_type(request):
    """Simple page where the user chooses Student or Company before registration."""
    return render(request, 'users/choose_account_type.html')


def choose_verification_method(request):
    """Page where user chooses email or SMS verification AFTER account creation."""
    if not request.user.is_authenticated:
        messages.error(request, "Please create an account first.")
        return redirect('users:register')
    
    # Check if user is already verified
    if request.user.email_verified:
        messages.info(request, "Your account is already verified!")
        return redirect('jobs:job_list')
    
    user_email = request.user.email
    user_phone = getattr(request.user, 'phone_number', None)
    
    if request.method == 'POST':
        form = ChooseVerificationMethodForm(request.POST)
        if form.is_valid():
            method = form.cleaned_data['verification_method']
            
            if method == 'sms':
                if not user_phone:
                    messages.error(request, "No phone number on file. Please use email verification.")
                    return redirect('users:choose_verification_method')
                
                # Generate and send SMS code
                code = generate_verification_code()
                PhoneVerificationCode.objects.update_or_create(
                    phone=user_phone,
                    defaults={'code': code, 'is_used': False, 'expires_at': timezone.now() + timedelta(minutes=10)}
                )
                sent = send_sms(user_phone, f'Your Campus Job Board verification code is: {code}. It expires in 10 minutes.')
                
                if sent:
                    request.session['pending_phone'] = user_phone
                    request.session['verification_method'] = 'sms'
                    messages.success(request, f'Verification code sent to {user_phone}')
                    return redirect('users:verify_phone')
                else:
                    messages.error(request, 'Failed to send SMS. Please try email verification instead.')
                    return redirect('users:choose_verification_method')
            
            else:  # email verification
                # Generate and send email code
                email_code = generate_verification_code()
                EmailVerificationCode.objects.update_or_create(
                    email=user_email,
                    defaults={'code': email_code, 'data': {}, 'is_used': False, 'expires_at': timezone.now() + timedelta(minutes=10)}
                )
                
                try:
                    debug_send_mail(
                        subject='Verify your Campus Job Board email',
                        message=f'Hello {request.user.username},\n\nYour email verification code is: {email_code}\n\nPlease enter this code to verify your email address.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user_email],
                        fail_silently=False,
                    )
                    request.session['pending_email'] = user_email
                    request.session['verification_method'] = 'email'
                    messages.success(request, f'Verification code sent to {user_email}')
                    return redirect('users:verify_code')
                except Exception:
                    import traceback
                    traceback.print_exc()
                    messages.error(request, 'Failed to send verification email. Please try again.')
                    return redirect('users:choose_verification_method')
    else:
        form = ChooseVerificationMethodForm()
    
    return render(request, 'users/choose_verification_method.html', {
        'form': form,
        'user_email': user_email,
        'user_phone': user_phone,
    })


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
        debug_send_mail(
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
