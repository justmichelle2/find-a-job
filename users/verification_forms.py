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