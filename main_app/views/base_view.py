"""
Base view classes for ensuring consistent context data.
"""

from django.conf import settings
from django.views import View

class BaseContextMixin:
    """Mixin to provide consistent context data to all views."""
    
    def get_context_data(self, **kwargs):
        """Add common context data to all views."""
        # Start with existing context if provided, otherwise empty dict
        context = kwargs.copy() if kwargs else {}
        
        # Add debug flag from settings
        context['debug'] = getattr(settings, 'DEBUG', False)
        
        # Ensure active_page is always available
        if 'active_page' not in context:
            # Try to get active_page from class attribute
            context['active_page'] = getattr(self, 'active_page', None)
        
        # Add user theme preferences if available
        if hasattr(self, 'request') and self.request.user.is_authenticated:
            try:
                user_profile = self.request.user.profile
                context['theme'] = user_profile.appearance_settings.get('theme', 'light')
                context['color_scheme'] = user_profile.appearance_settings.get('color_scheme', 'blue')
            except:
                context['theme'] = 'light'
                context['color_scheme'] = 'blue'
        
        return context
