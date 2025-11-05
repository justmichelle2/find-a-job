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

    institution = forms.CharField(
        max_length=255,
        required=True,
        help_text='Enter your school or company name (must be a recognized institution)')

    id_document = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text='Upload an ID (image or PDF) for verification')

    # Country code dropdown (common countries). You can extend this list as needed.
    COUNTRY_CODE_CHOICES = [
        ('+1', '+1 (USA/Canada)'),
        ('+44', '+44 (UK)'),
        ('+233', '+233 (Ghana)'),
        ('+234', '+234 (Nigeria)'),
        ('+91', '+91 (India)'),
        ('+61', '+61 (Australia)'),
        ('+49', '+49 (Germany)'),
        ('+27', '+27 (South Africa)'),
        ('+254', '+254 (Kenya)'),
        ('+20', '+20 (Egypt)'),
        ('+39', '+39 (Italy)'),
        ('+33', '+33 (France)'),
        ('+55', '+55 (Brazil)'),
        ('+81', '+81 (Japan)'),
        ('+82', '+82 (South Korea)'),
    ]

    country_code = forms.ChoiceField(
        choices=COUNTRY_CODE_CHOICES,
        initial='+233',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Country code'
    )

    phone_number_local = forms.CharField(
        required=True,
        max_length=15,
        help_text='Enter your phone number without the country code, e.g. 241234567',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 241234567'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'institution',
            'id_document',
            'country_code',
            'phone_number_local',
            'password1',
            'password2',
        )

    def __init__(self, *args, **kwargs):
        # Accept account_choice to customize validation/labels
        self.account_choice = kwargs.pop('account_choice', None)
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        # For company accounts, username should not be required (we will generate it)
        if self.account_choice == 'company':
            self.fields['username'].required = False
            # Adjust institution labeling to Company Name
            self.fields['institution'].label = 'Company name'
            self.fields['institution'].help_text = 'Enter your company name. Your username will be generated from this.'
        else:
            # Student labels/help
            self.fields['institution'].label = 'School name'
            self.fields['institution'].help_text = 'Enter your school name (must be a recognized institution).'

    def clean_institution(self):
        institution = self.cleaned_data.get('institution')
        # For company accounts, accept any non-empty company name without strict recognition
        if getattr(self, 'account_choice', None) == 'company':
            if not institution:
                raise forms.ValidationError('Please enter your company name.')
            return institution

        # Student accounts: recognized institutions list
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

    def clean(self):
        cleaned_data = super().clean()
        # Validate phone number combination
        country = cleaned_data.get('country_code')
        local = cleaned_data.get('phone_number_local')
        if country and local:
            import re
            combined = f"{country}{re.sub(r'[^0-9]', '', local)}"
            # E.164-ish: + followed by 7-15 digits
            if not re.match(r'^\+\d{7,15}$', combined):
                self.add_error('phone_number_local', 'Enter a valid phone number after selecting the country code.')
        elif not local:
            self.add_error('phone_number_local', 'Phone number is required for account creation.')
        return cleaned_data

    def clean_password1(self):
        pw = self.cleaned_data.get('password1')
        if pw:
            import re
            errors = []
            if len(pw) < 8:
                errors.append('Password must be at least 8 characters long.')
            if not re.search(r'[A-Z]', pw):
                errors.append('Password must contain at least one uppercase letter.')
            if not re.search(r'[a-z]', pw):
                errors.append('Password must contain at least one lowercase letter.')
            if not re.search(r'[A-Za-z]', pw):
                errors.append('Password must contain at least one letter.')
            if not re.search(r'\d', pw):
                errors.append('Password must contain at least one number.')
            if not re.search(r'[^A-Za-z0-9]', pw):
                errors.append('Password must contain at least one symbol (e.g. !@#$%).')
            if errors:
                raise forms.ValidationError(errors)
        return pw

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # For company, username is generated from company name in the view; allow blank
        if getattr(self, 'account_choice', None) == 'company':
            return username or ''

        # For student usernames: enforce sensible rules (3-30 chars, letters/numbers/underscore)
        if username:
            import re
            if len(username) < 3 or len(username) > 30:
                raise forms.ValidationError('Username must be between 3 and 30 characters.')
            if not re.match(r'^[A-Za-z0-9_]+$', username):
                raise forms.ValidationError('Username may only contain letters, numbers, and underscores.')
            return username
        raise forms.ValidationError('Please provide a username.')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.institution = self.cleaned_data.get('institution')
        
        # Assemble phone number from country code + local part
        country_code = self.cleaned_data.get('country_code')
        phone_local = self.cleaned_data.get('phone_number_local')
        if country_code and phone_local:
            import re
            user.phone_number = f"{country_code}{re.sub(r'[^0-9]', '', phone_local)}"

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
