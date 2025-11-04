from .models import Application


def notification_counts(request):
    """Provide unread notification counts for company and applicant users.

    Adds two keys to the template context:
    - company_unread_count
    - applicant_unread_count
    """
    company_unread = 0
    applicant_unread = 0

    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        try:
            if getattr(user, 'is_company', False):
                company_unread = Application.objects.filter(
                    job__company=user, company_unread=True).count()
            else:
                applicant_unread = Application.objects.filter(
                    applicant=user, applicant_unread=True).count()
        except Exception:
            # Avoid crashing templates if DB not ready
            company_unread = 0
            applicant_unread = 0

    return {
        'company_unread_count': company_unread,
        'applicant_unread_count': applicant_unread,
    }
