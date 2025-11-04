from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    """
    Model for storing all types of notifications in the system.
    """
    # Notification Types
    APPLICATION_SUBMITTED = 'AS'  # When student submits application
    APPLICATION_STATUS_CHANGED = 'AC'  # When company accepts/rejects
    JOB_POSTED = 'JP'  # When company posts new job
    JOB_APPROVED = 'JA'  # When admin approves job
    JOB_REJECTED = 'JR'  # When admin rejects job
    ID_VERIFIED = 'IV'  # When admin verifies ID
    ID_REJECTED = 'IR'  # When admin rejects ID
    EMAIL_VERIFIED = 'EV'  # When user verifies email

    NOTIFICATION_TYPE_CHOICES = [
        (APPLICATION_SUBMITTED, 'Application Submitted'),
        (APPLICATION_STATUS_CHANGED, 'Application Status Changed'),
        (JOB_POSTED, 'Job Posted'),
        (JOB_APPROVED, 'Job Approved'),
        (JOB_REJECTED, 'Job Rejected'),
        (ID_VERIFIED, 'ID Verified'),
        (ID_REJECTED, 'ID Rejected'),
        (EMAIL_VERIFIED, 'Email Verified'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='User who receives this notification'
    )
    notification_type = models.CharField(
        max_length=2,
        choices=NOTIFICATION_TYPE_CHOICES,
        help_text='Type of notification'
    )
    title = models.CharField(
        max_length=200,
        help_text='Short title for the notification'
    )
    message = models.TextField(
        help_text='Detailed notification message'
    )
    related_job = models.ForeignKey(
        'jobs.JobPost',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Related job post if applicable'
    )
    related_application = models.ForeignKey(
        'jobs.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Related application if applicable'
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the notification has been read'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When this notification was created'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['recipient']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient.username}"