from django import forms
from .models import JobPost, Application


class JobPostForm(forms.ModelForm):
    """
    Form for companies to create and edit job posts.
    """
    salary = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 50000 or 50,000'
        }),
        help_text="Enter salary (commas are allowed)")

    class Meta:
        model = JobPost
        fields = [
            'title', 'description', 'requirements', 'location', 'category',
            'job_type', 'deadline', 'salary', 'currency'
        ]
        widgets = {
            'title':
            forms.TextInput(attrs={'class': 'form-control'}),
            'description':
            forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5
            }),
            'requirements':
            forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5
            }),
            'location':
            forms.TextInput(attrs={'class': 'form-control'}),
            'category':
            forms.Select(attrs={'class': 'form-control'}),
            'job_type':
            forms.Select(attrs={'class': 'form-control'}),
            'deadline':
            forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'currency':
            forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary:
            salary_str = str(salary).replace(',', '').strip()
            if salary_str:
                try:
                    return float(salary_str)
                except ValueError:
                    raise forms.ValidationError("Please enter a valid number")
        return None

    def save(self, commit=True):
        job_post = super().save(commit=False)
        if self.user and not job_post.pk:
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
        fields = [
            'cover_letter', 'cv', 'transcript', 'certificate', 'other_document'
        ]
        widgets = {
            'cover_letter':
            forms.Textarea(
                attrs={
                    'class':
                    'form-control',
                    'rows':
                    6,
                    'placeholder':
                    'Tell us why you\'re interested in this position and why you\'d be a great fit...'
                }),
            'cv':
            forms.FileInput(attrs={'class': 'form-control'}),
            'transcript':
            forms.FileInput(attrs={'class': 'form-control'}),
            'certificate':
            forms.FileInput(attrs={'class': 'form-control'}),
            'other_document':
            forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)

        self.fields['cv'].required = True
        self.fields[
            'cv'].help_text = "Upload your CV/Resume (Required - PDF, DOC, DOCX)"

    def save(self, commit=True):
        application = super().save(commit=False)
        if self.user:
            application.applicant = self.user
        if self.job:
            application.job = self.job
        if commit:
            application.save()
        return application
