from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib import messages
from datetime import time
from main_app.forms import NotificationSettingsForm
from main_app.views.admin_settings_notifications import handle_notification_form
from main_app.models.user_models import UserProfile

class NotificationSettingsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='notifuser',
            email='notif@example.com',
            password='password123'
        )
        
        # Create profile with empty notification preferences
        self.profile = self.user.profile
        self.profile.notification_preferences = {}
        self.profile.save()
        
        # Create a request object
        self.request = self.factory.post('/fake-url')
        self.request.user = self.user
        
        # Setup messages framework
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)
        
    def test_notification_settings_update(self):
        """Test that notification settings are updated properly"""
        # Prepare form data
        form_data = {
            'email_reminders': True,
            'email_streak_updates': False,
            'email_achievements': True,
            'inapp_reminders': True,
            'inapp_streak_updates': True,
            'inapp_achievements': False,
            'quiet_hours_enabled': True,
            'daily_digest_time': '08:30',
            'quiet_hours_start': '22:00',
            'quiet_hours_end': '07:00'
        }
        self.request.POST = form_data
        
        # Call the handler
        handle_notification_form(None, self.request, self.profile)
        
        # Refresh profile from db
        self.profile.refresh_from_db()
        
        # Check that preferences were updated
        prefs = self.profile.notification_preferences
        self.assertTrue('email_reminders' in prefs, "email_reminders key not found in preferences")
        self.assertEqual(prefs.get('email_reminders'), True)
        self.assertEqual(prefs.get('email_streak_updates'), False)
        self.assertEqual(prefs.get('email_achievements'), True)
        self.assertEqual(prefs.get('inapp_reminders'), True)
        self.assertEqual(prefs.get('daily_digest_time'), '08:30')
        
    def test_notification_settings_invalid_time(self):
        """Test handling of invalid time formats"""
        # First, run a successful update to set initial values
        valid_form_data = {
            'email_reminders': True,
            'daily_digest_time': '08:30'
        }
        self.request.POST = valid_form_data
        # Create form explicitly and validate it
        form = NotificationSettingsForm(valid_form_data)
        self.assertTrue(form.is_valid())
        
        # Process the valid form
        handle_notification_form(None, self.request, self.profile)
        
        # Refresh profile and verify it saved correctly
        self.profile.refresh_from_db()
        prefs = self.profile.notification_preferences
        self.assertTrue('email_reminders' in prefs)
        
        # Now try with invalid data
        invalid_form_data = {
            'email_reminders': True,
            'daily_digest_time': 'not-a-time'  # Invalid time
        }
        self.request.POST = invalid_form_data
        
        # Call the handler again with invalid data
        handle_notification_form(None, self.request, self.profile)
        
        # Refresh profile from db
        self.profile.refresh_from_db()
        
        # Check that valid preferences were preserved
        prefs = self.profile.notification_preferences
        self.assertTrue('email_reminders' in prefs, "email_reminders key not found in preferences")
        self.assertEqual(prefs['email_reminders'], True)
        
    def test_notification_settings_empty_update(self):
        """Test that empty update doesn't overwrite previous settings"""
        # Set initial preferences
        self.profile.notification_preferences = {
            'email_reminders': True,
            'daily_digest_time': '09:00'
        }
        self.profile.save()
        
        # Prepare form data - email_reminders is False, daily_digest_time is missing
        form_data = {
            'email_reminders': False
        }
        self.request.POST = form_data
        
        # Call the handler
        handle_notification_form(None, self.request, self.profile)
        
        # Refresh profile from db
        self.profile.refresh_from_db()
        
        # Check that specified preferences were updated
        prefs = self.profile.notification_preferences
        self.assertEqual(prefs['email_reminders'], False)
        
        # Check that unspecified preferences were preserved
        self.assertEqual(prefs['daily_digest_time'], '09:00')
