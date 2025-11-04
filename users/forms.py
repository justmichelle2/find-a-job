from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import CustomUser


class RegistrationForm(UserCreationForm):
    """
    Registration form with option to sign up as a company or student.
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
            'id_document',
            'password1',
            'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_company = True if self.cleaned_data.get('account_type') == 'company' else False
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
