def landing_page(request):
    """Landing page view with platform statistics"""
    context = {
        'job_count': JobPost.objects.filter(is_approved=True).count(),
        'company_count': CustomUser.objects.filter(is_company=True, verification_status=CustomUser.VERIFIED).count(),
        'student_count': CustomUser.objects.filter(is_company=False).count(),
    }
    return render(request, 'jobs/landing.html', context)