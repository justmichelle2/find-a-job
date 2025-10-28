from django import forms
from .models import JobPost, Application


class JobPostForm(forms.ModelForm):
    """
    Form for companies to create and edit job posts.
    """
    class Meta:
        model = JobPost
        fields = [
            'title', 'description', 'requirements', 'location',
            'category', 'job_type', 'deadline', 'salary'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        job_post = super().save(commit=False)
        if self.user and not job_post.pk:  # Only set on initial creation
            job_post.company = self.user
        if commit:
            job_post.save()
        return job_post


class ApplicationForm(forms.ModelForm):
    """
    Form for students to apply for jobs.
    """
    class Meta:
        model = Application
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Tell us why you\'re interested in this position and why you\'d be a great fit...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        application = super().save(commit=False)
        if self.user:
            application.applicant = self.user
        if self.job:
            application.job = self.job
        if commit:
            application.save()
        return application

