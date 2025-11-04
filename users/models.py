from django.db import models
from django.contrib.auth.models import AbstractUser


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

    def __str__(self):
        return self.username
