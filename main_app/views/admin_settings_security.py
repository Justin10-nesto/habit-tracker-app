"""
Security settings handlers for the admin settings view.
Includes password management, two-factor authentication, and session management.
"""

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from ..forms import SecuritySettingsForm
from ..models import UserSession


def handle_security_form(self, request, profile):
    """Handle security form submission (password change)"""
    form = SecuritySettingsForm(request.user, request.POST)
    
    if form.is_valid():
        # Set the new password
        request.user.set_password(form.cleaned_data['new_password'])
        request.user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully!')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    return redirect('admin_settings')


def handle_two_factor_form(self, request, profile):
    """Handle two-factor authentication toggle"""
    # Toggle the two-factor authentication setting
    profile.two_factor_enabled = not profile.two_factor_enabled
    profile.save()
    
    if profile.two_factor_enabled:
        messages.success(request, 'Two-factor authentication enabled!')
    else:
        messages.info(request, 'Two-factor authentication disabled.')
    
    return redirect('admin_settings')


def handle_sessions_form(self, request):
    """Handle active sessions management"""
    if 'logout_all' in request.POST:
        # Delete all sessions except the current one
        current_session_key = request.session.session_key
        UserSession.objects.filter(user=request.user).exclude(session_key=current_session_key).delete()
        messages.success(request, 'All other sessions have been terminated.')
    elif 'session_id' in request.POST:
        # Terminate a specific session
        session_id = request.POST.get('session_id')
        try:
            session = UserSession.objects.get(id=session_id, user=request.user)
            session.delete()
            messages.success(request, 'Session terminated successfully.')
        except UserSession.DoesNotExist:
            messages.error(request, 'Session not found.')
    
    return redirect('admin_settings')
