"""
Notification settings handlers for the admin settings view.
"""

from django.shortcuts import redirect
from django.contrib import messages
from ..forms import NotificationSettingsForm


def handle_notification_form(self, request, profile):
    """Handle notification settings form submission"""
    form = NotificationSettingsForm(request.POST)
    
    if form.is_valid():
        # Get the current notification preferences or initialize new ones
        notification_prefs = profile.notification_preferences
        
        # Update with form data
        notification_prefs.update({
            'email_reminders': form.cleaned_data.get('email_reminders', False),
            'email_streak_updates': form.cleaned_data.get('email_streak_updates', False),
            'email_achievements': form.cleaned_data.get('email_achievements', False),
            'inapp_reminders': form.cleaned_data.get('inapp_reminders', False),
            'inapp_streak_updates': form.cleaned_data.get('inapp_streak_updates', False),
            'inapp_achievements': form.cleaned_data.get('inapp_achievements', False),
            'quiet_hours_enabled': form.cleaned_data.get('quiet_hours_enabled', False),
        })
        
        # Handle time fields
        if form.cleaned_data.get('daily_digest_time'):
            notification_prefs['daily_digest_time'] = form.cleaned_data.get('daily_digest_time').strftime('%H:%M')
        
        if form.cleaned_data.get('quiet_hours_start'):
            notification_prefs['quiet_hours_start'] = form.cleaned_data.get('quiet_hours_start').strftime('%H:%M')
            
        if form.cleaned_data.get('quiet_hours_end'):
            notification_prefs['quiet_hours_end'] = form.cleaned_data.get('quiet_hours_end').strftime('%H:%M')
        
        # Save to profile
        profile.notification_preferences = notification_prefs
        profile.save()
        
        messages.success(request, 'Notification settings updated successfully!')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    return redirect('admin_settings')
