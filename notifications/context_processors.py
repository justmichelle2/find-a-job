from .models import Notification

def notification_context(request):
    """Add notification count to the template context."""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return {'notification_count': unread_count}
    return {'notification_count': 0}