"""
Forms for the wholesale app.
"""
from django import forms
from .models import Provider

ADAPTER_CHOICES = [
    ('zego', 'Zego'),
    ('unique_inter', 'Unique Inter'),
    ('go365', 'Go365'),
    ('checkingroup', 'CheckIn Group'),
]


class ProviderAdminForm(forms.ModelForm):
    """
    ModelForm for Provider admin with adapter_type selection.

    Adds a user-friendly dropdown for selecting the adapter type,
    which is stored in the extra JSONField.
    """
    adapter_type = forms.ChoiceField(
        choices=ADAPTER_CHOICES,
        required=False,
        help_text="Select which adapter to use for this provider"
    )

    class Meta:
        model = Provider
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        """Load adapter_type from extra JSON if it exists."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.extra:
            adapter = self.instance.extra.get('adapter_type')
            if adapter:
                self.fields['adapter_type'].initial = adapter

    def save(self, commit=True):
        """Save adapter_type to extra JSON field."""
        provider = super().save(commit=False)
        if not provider.extra:
            provider.extra = {}
        provider.extra['adapter_type'] = self.cleaned_data['adapter_type']
        if commit:
            provider.save()
        return provider
