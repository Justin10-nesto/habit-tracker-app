from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile  # Make sure this import is correct
import pytz

class ProfileSettingsForm(forms.ModelForm):
    """Form for updating user profile information"""
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    timezone = forms.ChoiceField(choices=[(tz, tz) for tz in pytz.common_timezones])
    profile_picture = forms.ImageField(required=False)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        
    def clean_email(self):
        email = self.cleaned_data['email']
        # Check if email is already used by another user
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError("This email is already in use by another account.")
        return email


class NotificationSettingsForm(forms.Form):
    """Form for notification settings"""
    # Email notifications
    email_reminders = forms.BooleanField(required=False)
    email_streak_updates = forms.BooleanField(required=False)
    email_achievements = forms.BooleanField(required=False)
    
    # In-app notifications
    inapp_reminders = forms.BooleanField(required=False)
    inapp_streak_updates = forms.BooleanField(required=False)
    inapp_achievements = forms.BooleanField(required=False)
    
    # Schedule
    daily_digest_time = forms.TimeField(
        required=False,
        input_formats=['%H:%M'],
        widget=forms.TimeInput(format='%H:%M')
    )
    quiet_hours_enabled = forms.BooleanField(required=False)
    quiet_hours_start = forms.TimeField(
        required=False,
        input_formats=['%H:%M'],
        widget=forms.TimeInput(format='%H:%M')
    )
    quiet_hours_end = forms.TimeField(
        required=False,
        input_formats=['%H:%M'],
        widget=forms.TimeInput(format='%H:%M')
    )


class SecuritySettingsForm(forms.Form):
    """Form for security settings (password change)"""
    current_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=True
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=True
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SecuritySettingsForm, self).__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data['current_password']
        if not self.user.check_password(current_password):
            raise ValidationError("Your current password was entered incorrectly.")
        return current_password
    
    def clean_new_password(self):
        password = self.cleaned_data['new_password']
        validate_password(password, self.user)
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError("The two password fields didn't match.")
        
        return cleaned_data


class AppearanceSettingsForm(forms.Form):
    """Form for appearance settings"""
    theme = forms.ChoiceField(
        choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System')],
        required=True
    )
    color_scheme = forms.ChoiceField(
        choices=[('blue', 'Blue'), ('green', 'Green'), ('purple', 'Purple'), ('orange', 'Orange')],
        required=True
    )
    dashboard_display = forms.ChoiceField(
        choices=[('day', 'Daily'), ('week', 'Weekly'), ('month', 'Monthly')],
        required=True
    )
    compact_view = forms.BooleanField(required=False)
    show_animations = forms.BooleanField(required=False)


class PrivacySettingsForm(forms.Form):
    """Form for privacy settings"""
    public_profile = forms.BooleanField(required=False)
    profile_visibility = forms.ChoiceField(
        choices=[
            ('everyone', 'Everyone'),
            ('friends', 'Friends Only'),
            ('private', 'Private')
        ],
        required=True
    )
    show_on_leaderboard = forms.BooleanField(required=False)
