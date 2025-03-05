"""
Admin settings views for managing user profile, preferences, and account settings.
This file contains the base AdminSettingsView class that routes to specific handlers.
"""

from django.shortcuts import render, redirect
from django.views import View
import pytz

from .admin_views import AdminViewMixin
from ..models import UserProfile, UserSession

# Import handlers from separate modules
from .admin_settings_profile import handle_profile_form
from .admin_settings_notifications import handle_notification_form
from .admin_settings_security import handle_security_form, handle_two_factor_form, handle_sessions_form
from .admin_settings_appearance import handle_appearance_form
from .admin_settings_privacy import handle_privacy_form, handle_data_form, _export_user_data


class AdminSettingsView(AdminViewMixin, View):
    """Base view for user settings."""
    
    def get(self, request):
        # Create a list of timezones for the template
        timezones = [(tz, tz) for tz in pytz.common_timezones]
        
        # Get user sessions for the security tab
        user_sessions = UserSession.objects.filter(user=request.user).order_by('-last_activity')[:5]
        
        # Get appearance preferences for UI rendering
        try:
            theme = request.user.profile.appearance_settings.get('theme', 'light')
            color_scheme = request.user.profile.appearance_settings.get('color_scheme', 'blue')
        except:
            theme = 'light'
            color_scheme = 'blue'
            
        context = {
            'active_page': 'settings',
            'timezones': timezones,
            'user_sessions': user_sessions,
            'theme': theme,
            'color_scheme': color_scheme
        }
        
        return render(request, 'admin/settings.html', context)
    
    def post(self, request):
        form_type = request.POST.get('form_type', '')
        
        # Ensure user has a profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Route to the appropriate handler based on form type
        handlers = {
            'profile': handle_profile_form,
            'notifications': handle_notification_form,
            'security': handle_security_form,
            'two_factor': handle_two_factor_form,
            'sessions': handle_sessions_form,
            'appearance': handle_appearance_form,
            'privacy': handle_privacy_form,
            'data': handle_data_form
        }
        
        handler = handlers.get(form_type)
        if handler:
            return handler(self, request, profile)
            
        # Default case - just redirect back
        return redirect('admin_settings')
    
    # Add export user data method
    export_user_data = _export_user_data
