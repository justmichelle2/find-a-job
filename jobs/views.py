from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponseForbidden
from django.core.mail import send_mail
from django.conf import settings
from .models import JobPost, Application
from .forms import JobPostForm, ApplicationForm
from users.models import CustomUser
from notifications.utils import create_notification
from notifications.models import Notification


class JobListView(ListView):
    """
    Class-based view to display all available job posts with search and filtering.
    """
    model = JobPost
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        # Admin sees all jobs
        if user.is_superuser:
            queryset = JobPost.objects.all()
        # Company users see only their own jobs
        elif user.is_authenticated and hasattr(user, 'is_company') and user.is_company:
            queryset = JobPost.objects.filter(company=user)
        # Students and anonymous users see only approved jobs
        else:
            queryset = JobPost.objects.filter(is_approved=True)

        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(location__icontains=search_query))

        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by job type
        job_type = self.request.GET.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type=job_type)

        return queryset.order_by('-date_posted')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['job_type_filter'] = self.request.GET.get('job_type', '')
        context['categories'] = JobPost.CATEGORY_CHOICES
        context['job_types'] = JobPost.JOB_TYPE_CHOICES
        return context


class JobDetailView(DetailView):
    """
    Class-based view to display job details.
    """
    model = JobPost
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.get_object()
        user = self.request.user

        # Check if user has already applied
        if user.is_authenticated and not user.is_company:
            context['has_applied'] = Application.objects.filter(
                job=job, applicant=user).exists()
            context['user_applications'] = Application.objects.filter(
                applicant=user)
        else:
            context['has_applied'] = False

        # Add today's date for deadline comparison
        from django.utils import timezone
        context['today'] = timezone.now().date()

        return context


@login_required
def apply_job(request, pk):
    """
    Function-based view for students to apply for a job.
    """
    job = get_object_or_404(JobPost, pk=pk)

    # Only non-company users and non-admins can apply
    if request.user.is_superuser or request.user.is_company:
        messages.warning(
            request,
            "You are not allowed to apply for jobs with this account.")
        return redirect('jobs:job_detail', pk=pk)

    # Check if already applied
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, "You have already applied for this job.")
        return redirect('jobs:job_detail', pk=pk)

    if request.method == 'POST':
        form = ApplicationForm(request.POST,
                               request.FILES,
                               user=request.user,
                               job=job)
        if form.is_valid():
            application = form.save()
            # Ensure company sees this as an unread notification
            try:
                application.company_unread = True
                application.save()
            except Exception:
                pass

            # Create notification for company
            create_notification(
                recipient=job.company,
                notification_type=Notification.APPLICATION_SUBMITTED,
                title=f"New application for {job.title}",
                message=f"{request.user.username} has applied for the position of {job.title}",
                related_job=job,
                related_application=application
            )

            try:
                send_mail(
                    subject=f'New Application for {job.title}',
                    message=
                    f'You have received a new application from {request.user.username} for the position: {job.title}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[job.company.email],
                    fail_silently=True,
                )

                send_mail(
                    subject=f'Application Submitted: {job.title}',
                    message=
                    f'Your application for {job.title} at {job.company.username} has been submitted successfully. We will notify you once there is an update.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[request.user.email],
                    fail_silently=True,
                )
            except Exception:
                pass

            messages.success(
                request,
                f'Your application for "{job.title}" has been submitted successfully!'
            )
            return redirect('jobs:job_detail', pk=pk)
    else:
        form = ApplicationForm(user=request.user, job=job)

    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})


@login_required
def create_job_post(request):
    """
    Function-based view for companies to create job posts.
    """
    # Only company users can post jobs
    if not request.user.is_company:
        messages.warning(request, "Only companies can post jobs.")
        return redirect('jobs:job_list')

    # Require identity verification for companies to post jobs
    if request.user.verification_status == CustomUser.REJECTED:
        messages.error(request, "Your account verification has been rejected. You cannot post jobs. Please contact support.")
        return redirect('jobs:company_dashboard')
    elif request.user.verification_status != CustomUser.VERIFIED:
        messages.warning(request, "Your account must be verified before posting jobs. Please wait for verification.")
        return redirect('jobs:company_dashboard')

    if request.method == 'POST':
        form = JobPostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Save but don't commit so we can set additional fields
            job_post = form.save(commit=False)
            # Ensure company is set (form.save normally handles this, but be explicit)
            if request.user and not job_post.pk:
                job_post.company = request.user
            # Jobs require admin approval before being visible
            job_post.is_approved = False
            job_post.save()

            # Create notification for admins
            for admin in CustomUser.objects.filter(is_superuser=True):
                create_notification(
                    recipient=admin,
                    notification_type=Notification.JOB_POSTED,
                    title=f"New job post: {job_post.title}",
                    message=f"Company {request.user.username} has posted a new job: {job_post.title}. Please review for approval.",
                    related_job=job_post
                )

            messages.success(
                request,
                f'Job post "{job_post.title}" has been created successfully and is now visible to applicants.'
            )
            return redirect('jobs:company_dashboard')
    else:
        form = JobPostForm(user=request.user)

    return render(request, 'jobs/create_job.html', {'form': form})


@login_required
def my_applications(request):
    """
    Function-based view to show user's applications.
    """
    if request.user.is_company:
        # Companies see applications for their posted jobs
        jobs = JobPost.objects.filter(company=request.user)
        applications = Application.objects.filter(job__in=jobs).select_related(
            'applicant', 'job')
        # Mark company notifications as read when viewing applications
        try:
            Application.objects.filter(job__company=request.user,
                                       company_unread=True).update(
                company_unread=False)
        except Exception:
            pass
    else:
        # Students see their own applications
        applications = Application.objects.filter(
            applicant=request.user).select_related('job')
        # Mark applicant notifications as read when viewing their applications
        try:
            Application.objects.filter(applicant=request.user,
                                       applicant_unread=True).update(
                applicant_unread=False)
        except Exception:
            pass

    return render(request, 'jobs/my_applications.html',
                  {'applications': applications})


@login_required
def my_jobs(request):
    """
    Function-based view for companies to manage their job posts.
    """
    if not request.user.is_company:
        messages.warning(request, "Only companies can view this page.")
        return redirect('jobs:job_list')

    from django.utils import timezone
    jobs = JobPost.objects.filter(company=request.user)
    return render(request, 'jobs/my_jobs.html', {
        'jobs': jobs,
        'today': timezone.now().date()
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    """
    Admin dashboard with statistics and job approval.
    """
    total_users = CustomUser.objects.count()
    total_students = CustomUser.objects.filter(is_company=False).count()
    total_companies = CustomUser.objects.filter(is_company=True).count()
    total_jobs = JobPost.objects.count()
    approved_jobs = JobPost.objects.filter(is_approved=True).count()
    pending_jobs = JobPost.objects.filter(is_approved=False).count()
    total_applications = Application.objects.count()
    pending_applications = Application.objects.filter(status='P').count()

    unapproved_jobs = JobPost.objects.filter(
        is_approved=False).select_related('company')

    # Get users by verification status
    unverified_users = CustomUser.objects.exclude(verification_status__in=[CustomUser.VERIFIED, CustomUser.REJECTED])

    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_companies': total_companies,
        'total_jobs': total_jobs,
        'approved_jobs': approved_jobs,
        'pending_jobs': pending_jobs,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'unapproved_jobs': unapproved_jobs,
        'unverified_users': unverified_users,
    }

    return render(request, 'jobs/admin_dashboard.html', context)


@login_required
def company_dashboard(request):
    """
    Company dashboard for managing jobs and applications.
    """
    if not request.user.is_company:
        messages.warning(request, "Only companies can access this page.")
        return redirect('jobs:job_list')

    from django.utils import timezone
    jobs = JobPost.objects.filter(company=request.user).annotate(
        application_count=Count('applications'))

    total_jobs = jobs.count()
    active_jobs = jobs.filter(deadline__gte=timezone.now().date()).count()
    total_applications = Application.objects.filter(
        job__company=request.user).count()
    pending_applications = Application.objects.filter(
        job__company=request.user, status='P').count()

    recent_applications = Application.objects.filter(
        job__company=request.user).select_related(
            'applicant', 'job').order_by('-date_applied')[:5]

    # Mark company notifications as read when visiting the company dashboard
    try:
        Application.objects.filter(job__company=request.user,
                                   company_unread=True).update(
            company_unread=False)
    except Exception:
        pass

    context = {
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'jobs': jobs[:5],
        'recent_applications': recent_applications,
    }

    return render(request, 'jobs/company_dashboard.html', context)


@login_required
def student_dashboard(request):
    """
    Student dashboard for viewing jobs and application history.
    """
    if request.user.is_company:
        messages.warning(request, "Students only.")
        return redirect('jobs:job_list')

    applications = Application.objects.filter(
        applicant=request.user).select_related('job').order_by('-date_applied')

    total_applications = applications.count()
    pending = applications.filter(status='P').count()
    accepted = applications.filter(status='A').count()
    rejected = applications.filter(status='R').count()

    recent_jobs = JobPost.objects.filter(
        is_approved=True).order_by('-date_posted')[:5]

    context = {
        'applications': applications[:5],
        'total_applications': total_applications,
        'pending': pending,
        'accepted': accepted,
        'rejected': rejected,
        'recent_jobs': recent_jobs,
    }

    # Mark applicant notifications as read when visiting student dashboard
    try:
        Application.objects.filter(applicant=request.user,
                                   applicant_unread=True).update(
            applicant_unread=False)
    except Exception:
        pass

    return render(request, 'jobs/student_dashboard.html', context)


@login_required
def update_application_status(request, pk, status):
    """
    Update application status (approve/reject).
    """
    application = get_object_or_404(Application, pk=pk)

    if application.job.company != request.user and not request.user.is_superuser:
        return HttpResponseForbidden(
            "You don't have permission to update this application.")

    if status in ['A', 'R']:
        # Accept optional custom message from POST data
        custom_message = ''
        if request.method == 'POST':
            custom_message = request.POST.get('message', '').strip()

        application.status = status
        # When company updates status, set applicant_unread so applicant sees notification
        application.applicant_unread = True
        application.save()

        status_text = 'Accepted' if status == 'A' else 'Rejected'

        # Create notification for applicant
        create_notification(
            recipient=application.applicant,
            notification_type=Notification.APPLICATION_STATUS_CHANGED,
            title=f"Application {status_text}: {application.job.title}",
            message=f"Your application for {application.job.title} has been {status_text}." +
                    (f"\n\nMessage from {request.user.username}:\n{custom_message}" if custom_message else ""),
            related_job=application.job,
            related_application=application
        )

        # Build the email body; include custom message if provided
        if custom_message:
            email_body = (
                f'Hello {application.applicant.username},\n\n'
                f'Your application for "{application.job.title}" has been {status_text}.\n\n'
                f'Message from {request.user.username}:\n{custom_message}\n\n'
                'Regards,\nCampus Job Board'
            )
        else:
            email_body = (
                f'Hello {application.applicant.username},\n\n'
                f'Your application for "{application.job.title}" has been {status_text}.\n\n'
                'Regards,\nCampus Job Board'
            )

        try:
            send_mail(
                subject=f'Application Update: {application.job.title}',
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.applicant.email],
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(request,
                         f'Application {status_text.lower()} successfully!')

    return redirect(request.META.get('HTTP_REFERER', 'jobs:my_applications'))


@login_required
def view_application_and_mark(request, pk):
    """Mark a single application as read for the current user and redirect to job detail."""
    application = get_object_or_404(Application, pk=pk)

    user = request.user
    # If company viewing an application for their job, mark company_unread False
    if user.is_authenticated and user.is_company and application.job.company == user:
        try:
            if application.company_unread:
                application.company_unread = False
                application.save()
        except Exception:
            pass

    # If applicant viewing their own application, mark applicant_unread False
    if user.is_authenticated and not user.is_company and application.applicant == user:
        try:
            if application.applicant_unread:
                application.applicant_unread = False
                application.save()
        except Exception:
            pass

    return redirect('jobs:job_detail', pk=application.job.pk)


@login_required
def edit_job(request, pk):
    """
    Edit a job post.
    """
    job = get_object_or_404(JobPost, pk=pk)

    if job.company != request.user and not request.user.is_superuser:
        return HttpResponseForbidden(
            "You don't have permission to edit this job.")

    if request.method == 'POST':
        form = JobPostForm(request.POST, request.FILES, instance=job, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully!')
            return redirect('jobs:job_detail', pk=pk)
    else:
        form = JobPostForm(instance=job, user=request.user)

    return render(request, 'jobs/edit_job.html', {'form': form, 'job': job})


@login_required
def delete_job(request, pk):
    """
    Delete a job post.
    """
    job = get_object_or_404(JobPost, pk=pk)

    if job.company != request.user and not request.user.is_superuser:
        return HttpResponseForbidden(
            "You don't have permission to delete this job.")

    if request.method == 'POST':
        job_title = job.title
        job.delete()
        messages.success(request, f'Job "{job_title}" deleted successfully!')
        return redirect('jobs:company_dashboard' if request.user.
                        is_company else 'jobs:admin_dashboard')

    return render(request, 'jobs/delete_job.html', {'job': job})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_job(request, pk):
    """
    Approve a job post (admin only).
    """
    job = get_object_or_404(JobPost, pk=pk)
    job.is_approved = True
    job.save()

    # Create notification for company
    create_notification(
        recipient=job.company,
        notification_type=Notification.JOB_APPROVED,
        title=f"Job Approved: {job.title}",
        message=f"Your job post for {job.title} has been approved and is now visible to applicants.",
        related_job=job
    )

    try:
        send_mail(
            subject=f'Job Post Approved: {job.title}',
            message=
            f'Your job post "{job.title}" has been approved and is now visible to applicants.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[job.company.email],
            fail_silently=True,
        )
    except Exception:
        pass

    messages.success(request, f'Job "{job.title}" approved!')
    return redirect('jobs:admin_dashboard')
