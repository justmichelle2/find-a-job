from django.db import models
from django.conf import settings
from django.utils import timezone


class JobPost(models.Model):
    """
    Model representing a job posting created by a company.
    """
    # Job categories
    FULL_TIME = 'FT'
    PART_TIME = 'PT'
    INTERNSHIP = 'INT'
    CONTRACT = 'CON'

    JOB_TYPE_CHOICES = [
        (FULL_TIME, 'Full Time'),
        (PART_TIME, 'Part Time'),
        (INTERNSHIP, 'Internship'),
        (CONTRACT, 'Contract'),
    ]

    IT = 'IT'
    MARKETING = 'MKT'
    FINANCE = 'FIN'
    SALES = 'SLS'
    HR = 'HR'
    ENGINEERING = 'ENG'
    EDUCATION = 'EDU'
    HEALTHCARE = 'HLT'
    MEDIA = 'MED'
    LAW = 'LAW'
    CONSTRUCTION = 'CON'
    CUSTOMER_SERVICE = 'CS'
    ARCHITECTURE = 'ARC'
    ACCOUNTING = 'ACC'
    OTHER = 'OTH'

    CATEGORY_CHOICES = [
        (IT, 'IT & Software'),
        (FINANCE, 'Finance & Accounting'),
        (ACCOUNTING, 'Accounting'),
        (MARKETING, 'Marketing & Sales'),
        (SALES, 'Sales'),
        (EDUCATION, 'Education & Training'),
        (ENGINEERING, 'Engineering'),
        (ARCHITECTURE, 'Architecture'),
        (HEALTHCARE, 'Healthcare & Medicine'),
        (MEDIA, 'Media & Design'),
        (HR, 'Human Resources'),
        (LAW, 'Law & Administration'),
        (CONSTRUCTION, 'Construction & Real Estate'),
        (CUSTOMER_SERVICE, 'Customer Service'),
        (OTHER, 'Others'),
    ]

    CURRENCY_CHOICES = [
        ('USD', 'USD - US Dollar'),
        ('GHS', 'GHS - Ghanaian Cedi'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
        ('NGN', 'NGN - Nigerian Naira'),
        ('KES', 'KES - Kenyan Shilling'),
        ('ZAR', 'ZAR - South African Rand'),
        ('CAD', 'CAD - Canadian Dollar'),
        ('AUD', 'AUD - Australian Dollar'),
    ]

    title = models.CharField(max_length=200)
    company = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                limit_choices_to={'is_company': True},
                                related_name='job_posts')
    description = models.TextField(help_text="Detailed job description")
    requirements = models.TextField(
        help_text="Required qualifications and skills")
    location = models.CharField(max_length=200)
    category = models.CharField(max_length=3,
                                choices=CATEGORY_CHOICES,
                                default=IT)
    job_type = models.CharField(max_length=3,
                                choices=JOB_TYPE_CHOICES,
                                default=FULL_TIME)
    date_posted = models.DateTimeField(default=timezone.now)
    deadline = models.DateField(help_text="Application deadline")
    salary = models.DecimalField(max_digits=10,
                                 decimal_places=2,
                                 null=True,
                                 blank=True,
                                 help_text="Salary range (optional)")
    currency = models.CharField(max_length=3,
                                choices=CURRENCY_CHOICES,
                                default='USD',
                                help_text="Currency for salary")
    image = models.ImageField(
        upload_to='job_images/',
        null=True,
        blank=True,
        help_text="Optional image for the job posting")
    is_approved = models.BooleanField(
        default=False, help_text="Whether this job post is approved by admin")

    class Meta:
        ordering = ['-date_posted']
        indexes = [
            models.Index(fields=['-date_posted']),
            models.Index(fields=['category']),
            models.Index(fields=['job_type']),
        ]

    def __str__(self):
        return f"{self.title} - {self.company.username}"


class Application(models.Model):
    """
    Model representing a job application submitted by a student/job seeker.
    """
    PENDING = 'P'
    ACCEPTED = 'A'
    REJECTED = 'R'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
    ]

    job = models.ForeignKey(JobPost,
                            on_delete=models.CASCADE,
                            related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.CASCADE,
                                  limit_choices_to={'is_company': False},
                                  related_name='job_applications')
    cover_letter = models.TextField(
        help_text="Why you're interested in this position")
    cv = models.FileField(upload_to='applications/cv/',
                          null=True,
                          blank=True,
                          help_text="Upload your CV/Resume (PDF, DOC, DOCX)")
    transcript = models.FileField(
        upload_to='applications/transcripts/',
        null=True,
        blank=True,
        help_text="Upload your academic transcript (PDF)")
    certificate = models.FileField(
        upload_to='applications/certificates/',
        null=True,
        blank=True,
        help_text="Upload any relevant certificates (PDF)")
    other_document = models.FileField(
        upload_to='applications/other/',
        null=True,
        blank=True,
        help_text="Upload any other supporting document")
    date_applied = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=1,
                              choices=STATUS_CHOICES,
                              default=PENDING)

    class Meta:
        ordering = ['-date_applied']
        # Ensure a user can only apply once per job
        unique_together = [['job', 'applicant']]
        indexes = [
            models.Index(fields=['-date_applied']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"
