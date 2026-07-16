from django import forms
from .models import ContactMessage, Profile


class ContactForm(forms.ModelForm):
    # Honeypot field for spam protection
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your message...',
                'rows': 5,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        # If honeypot field is filled, it's likely a bot
        if cleaned_data.get('website'):
            raise forms.ValidationError("Spam detected.")
        return cleaned_data


class ProfileForm(forms.ModelForm):
    """Plain form used by the custom /edit-profile/ page.

    Bypasses the Django admin change form entirely, so it keeps working
    even if the admin misbehaves on a hosting provider.
    """

    class Meta:
        model = Profile
        fields = [
            'name', 'title', 'typing_texts', 'hero_tagline',
            'bio', 'academic_summary',
            'photo', 'resume',
            'email', 'github_url', 'linkedin_url', 'telegram_url',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'hero_tagline': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'academic_summary': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'typing_texts': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'telegram_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
