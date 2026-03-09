from django import forms
from .models import ContactMessage


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
