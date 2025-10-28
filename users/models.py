from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Extended user model with is_company flag to distinguish
    between students (job seekers) and companies (employers).
    """
    is_company = models.BooleanField(
        default=False,
        help_text="Designates whether this user is a company/employer"
    )
    
    def __str__(self):
        return self.username
