"""
User-related models for the Habit Tracker application.
"""

from django.db import models
from django.contrib.auth.models import User
import json
from .base import get_uuid


class UserProfileManager(models.Manager):
    """Manager for UserProfile model - Factory pattern approach"""
    def create_user_profile(self, user, gender=None, dob=None):
        return self.create(
            user=user,
            gender=gender,
            date_of_birth=dob,
        )


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    two_factor_enabled = models.BooleanField(default=False)
    
    # Store complex settings as JSON
    _notification_preferences = models.TextField(blank=True, null=True)
    _appearance_settings = models.TextField(blank=True, null=True)
    _privacy_settings = models.TextField(blank=True, null=True)
    
    gender = models.CharField(max_length=1, choices=(
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ), blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    objects = UserProfileManager()
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def notification_preferences(self):
        if not self._notification_preferences:
            return {
                'email_reminders': True,
                'email_streak_updates': True,
                'email_achievements': True,
                'inapp_reminders': True,
                'inapp_streak_updates': True,
                'inapp_achievements': True,
                'daily_digest_time': '08:00',
                'quiet_hours_enabled': False,
                'quiet_hours_start': '22:00',
                'quiet_hours_end': '07:00',
            }
        return json.loads(self._notification_preferences)
    
    @notification_preferences.setter
    def notification_preferences(self, value):
        self._notification_preferences = json.dumps(value)
    
    @property
    def appearance_settings(self):
        if not self._appearance_settings:
            return {
                'theme': 'light',
                'color_scheme': 'blue',
                'dashboard_display': 'month',
                'compact_view': False,
                'show_animations': True,
            }
        return json.loads(self._appearance_settings)
    
    @appearance_settings.setter
    def appearance_settings(self, value):
        self._appearance_settings = json.dumps(value)
    
    @property
    def privacy_settings(self):
        if not self._privacy_settings:
            return {
                'public_profile': False,
                'profile_visibility': 'private',
                'show_on_leaderboard': True,
            }
        return json.loads(self._privacy_settings)
    
    @privacy_settings.setter
    def privacy_settings(self, value):
        self._privacy_settings = json.dumps(value)


class UserSession(models.Model):
    """Track user sessions for security purposes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} {self.browser}"
