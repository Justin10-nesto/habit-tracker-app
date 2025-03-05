"""
Middleware for setting user timezone.
"""

import pytz
from django.utils import timezone

class TimezoneMiddleware:
    """
    Middleware that sets the timezone for the current request based on user preferences.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                # Get user's timezone preference
                user_profile = request.user.profile
                user_timezone = user_profile.timezone
                
                # Set timezone for this request
                if user_timezone:
                    timezone.activate(pytz.timezone(user_timezone))
                else:
                    timezone.deactivate()
            except:
                # Fall back to default timezone
                timezone.deactivate()
        else:
            # Use system default for anonymous users
            timezone.deactivate()
            
        response = self.get_response(request)
        return response
