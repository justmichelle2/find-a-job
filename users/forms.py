from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import CustomUser, EmailVerificationCode
import random
import string


class RegistrationForm(UserCreationForm):
    """
    Registration form with option to sign up as a company or student.
    Adds institution field and validates ID document.
    """
    email = forms.EmailField(required=True, max_length=254)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    ACCOUNT_CHOICES = (
        ('student', 'I am a student'),
        ('company', 'I am a company/employer'),
    )

    account_type = forms.ChoiceField(
        choices=ACCOUNT_CHOICES,
        widget=forms.RadioSelect,
        label='Account Type')

    institution = forms.CharField(
        max_length=255,
        required=True,
        help_text='Enter your school or company name (must be a recognized institution)')

    id_document = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text='Upload an ID (image or PDF) for verification')

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'account_type',
            'institution',
            'id_document',
            'password1',
            'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_institution(self):
        institution = self.cleaned_data.get('institution')
        # List of recognized Ghanaian universities and companies
        valid_ghana_institutions = [
            'University of Ghana',
            'Kwame Nkrumah University of Science and Technology',
            'Ashesi University',
            'University of Cape Coast',
            'Ghana Technology University College',
            'Koforidua Technical University',
            'Ghana Commercial Bank',
            'MTN Ghana',
            'Ecobank Ghana',
            'Ghana Revenue Authority',
            # ...add more as needed
        ]
        # Accept if institution is in Ghana list, or looks like a university/company (basic global check)
        if institution:
            inst_lower = institution.lower()
            if (
                institution in valid_ghana_institutions
                or 'university' in inst_lower
                or 'college' in inst_lower
                or 'polytechnic' in inst_lower
                or 'institute' in inst_lower
                or 'company' in inst_lower
                or 'bank' in inst_lower
                or 'school' in inst_lower
                or 'corporation' in inst_lower
                or 'limited' in inst_lower
                or 'ltd' in inst_lower
                or 'inc' in inst_lower
                or 'plc' in inst_lower
            ):
                return institution
            raise forms.ValidationError('Institution not recognized. Please enter a valid school or company in Ghana or worldwide, or contact support.')
        return institution

    def clean_id_document(self):
        id_doc = self.cleaned_data.get('id_document')
        # Basic file type check
        if id_doc:
            valid_types = ['application/pdf', 'image/jpeg', 'image/png']
            if hasattr(id_doc, 'content_type') and id_doc.content_type not in valid_types:
                raise forms.ValidationError('ID document must be a PDF or image file (jpg, png).')
        return id_doc

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_company = True if self.cleaned_data.get('account_type') == 'company' else False
        user.institution = self.cleaned_data.get('institution')
        # Attach uploaded ID document and set verification to pending
        id_doc = self.cleaned_data.get('id_document')
        if id_doc:
            user.id_document = id_doc
            user.verification_status = CustomUser.PENDING
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """
    Simple login form.
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        }))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        }))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Invalid username or password.")
            if not user.is_active:
                raise forms.ValidationError("This account is inactive.")
        return self.cleaned_data
