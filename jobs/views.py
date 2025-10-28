from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import JobPost, Application
from .forms import JobPostForm, ApplicationForm


class JobListView(ListView):
    """
    Class-based view to display all available job posts with search and filtering.
    """
    model = JobPost
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = JobPost.objects.all()
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
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
                job=job,
                applicant=user
            ).exists()
            context['user_applications'] = Application.objects.filter(applicant=user)
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
    
    # Only non-company users can apply
    if request.user.is_company:
        messages.warning(request, "Companies cannot apply for jobs. Please log in as a student.")
        return redirect('jobs:job_detail', pk=pk)
    
    # Check if already applied
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, "You have already applied for this job.")
        return redirect('jobs:job_detail', pk=pk)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, user=request.user, job=job)
        if form.is_valid():
            application = form.save()
            messages.success(request, f'Your application for "{job.title}" has been submitted successfully!')
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
    
    if request.method == 'POST':
        form = JobPostForm(request.POST, user=request.user)
        if form.is_valid():
            job_post = form.save()
            messages.success(request, f'Job post "{job_post.title}" has been created successfully!')
            return redirect('jobs:job_detail', pk=job_post.pk)
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
        applications = Application.objects.filter(job__in=jobs).select_related('applicant', 'job')
    else:
        # Students see their own applications
        applications = Application.objects.filter(applicant=request.user).select_related('job')
    
    return render(request, 'jobs/my_applications.html', {'applications': applications})


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
