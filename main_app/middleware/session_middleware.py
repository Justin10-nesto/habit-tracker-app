"""
Middleware for tracking user sessions.
"""

from django.utils import timezone
import logging
from ..models import UserSession

logger = logging.getLogger(__name__)

class UserSessionMiddleware:
    """
    Middleware to track user sessions and store information for security purposes.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.user.is_authenticated:
            # Try to find an existing session
            session_key = request.session.session_key
            
            if session_key:
                try:
                    # Update existing session
                    user_session, created = UserSession.objects.get_or_create(
                        user=request.user,
                        session_key=session_key,
                        defaults={
                            'ip_address': self.get_client_ip(request),
                            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                            'device_type': self.get_device_type(request),
                            'browser': self.get_browser(request),
                            'os': self.get_os(request),
                        }
                    )
                    
                    # Update last activity
                    if not created:
                        user_session.last_activity = timezone.now()
                        user_session.save(update_fields=['last_activity'])
                        
                except Exception as e:
                    logger.error(f"Error updating user session: {e}")
            
        response = self.get_response(request)
        return response
        
    def get_client_ip(self, request):
        """Get the client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
        
    def get_device_type(self, request):
        """Get the device type from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'mobile' in user_agent:
            return 'Mobile'
        elif 'tablet' in user_agent:
            return 'Tablet'
        else:
            return 'Desktop'
            
    def get_browser(self, request):
        """Get the browser from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'chrome' in user_agent:
            return 'Chrome'
        elif 'firefox' in user_agent:
            return 'Firefox'
        elif 'safari' in user_agent:
            return 'Safari'
        elif 'edge' in user_agent:
            return 'Edge'
        elif 'opera' in user_agent:
            return 'Opera'
        elif 'msie' in user_agent or 'trident' in user_agent:
            return 'Internet Explorer'
        else:
            return 'Unknown'
            
    def get_os(self, request):
        """Get the OS from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'windows' in user_agent:
            return 'Windows'
        elif 'mac' in user_agent:
            return 'Mac OS'
        elif 'android' in user_agent:
            return 'Android'
        elif 'ios' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent:
            return 'iOS'
        elif 'linux' in user_agent:
            return 'Linux'
        else:
            return 'Unknown'
