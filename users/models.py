from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class EmailVerificationCode(models.Model):
    """
    Model to store temporary email verification codes for registration.
    """
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)  # 6-digit verification code
    data = models.JSONField(help_text="Temporarily stored registration data")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Code expires after 10 minutes
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['code']),
            models.Index(fields=['is_used']),
        ]


class CustomUser(AbstractUser):
    """
    Extended user model with is_company flag to distinguish
    between students (job seekers) and companies (employers).
    Adds institution field for ID validation.
    """
    is_company = models.BooleanField(
        default=False,
        help_text="Designates whether this user is a company/employer")
    # ID verification fields
    id_document = models.FileField(
        upload_to='user_ids/',
        null=True,
        blank=True,
        help_text='Upload an identification document (image or PDF) for verification')
    institution = models.CharField(
        max_length=255,
        help_text='Enter your school or company name for verification',
        null=True,
        blank=True
    )

    PENDING = 'P'
    VERIFIED = 'V'
    REJECTED = 'R'

    VERIFICATION_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (VERIFIED, 'Verified'),
        (REJECTED, 'Rejected'),
    ]

    verification_status = models.CharField(
        max_length=1,
        choices=VERIFICATION_STATUS_CHOICES,
        default=PENDING,
        help_text='Status of identity verification')

    # Email verification fields
    email_verified = models.BooleanField(
        default=False,
        help_text='Whether the user has verified their email address')
    email_verification_token = models.CharField(
        max_length=6,
        null=True,
        blank=True,
        help_text='Temporary token for email verification')

    def __str__(self):
        return self.username
