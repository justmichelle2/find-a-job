from django import forms

class EmailVerificationForm(forms.Form):
    """Form for entering email to start verification process"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )

class VerifyCodeForm(forms.Form):
    """Form for entering the verification code"""
    code = forms.CharField(
        required=True,
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit code'
        })
    )

class ChooseVerificationMethodForm(forms.Form):
    """Form to choose between email or SMS verification"""
    VERIFICATION_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS (Text Message)'),
    ]
    
    verification_method = forms.ChoiceField(
        choices=VERIFICATION_CHOICES,
        widget=forms.RadioSelect,
        initial='email',
        label='How would you like to receive your verification code?'
    )