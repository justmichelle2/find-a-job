from .models import Notification

def create_notification(recipient, notification_type, title, message, related_job=None, related_application=None):
    """
    Helper function to create a new notification.
    
    Args:
        recipient: User object who will receive the notification
        notification_type: Type of notification from Notification.NOTIFICATION_TYPE_CHOICES
        title: Short title for the notification
        message: Detailed message
        related_job: Optional JobPost object
        related_application: Optional Application object
    """
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        related_job=related_job,
        related_application=related_application
    )