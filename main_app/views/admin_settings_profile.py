"""
Profile settings handlers for the admin settings view.
"""

from django.shortcuts import redirect
from django.contrib import messages
from ..forms import ProfileSettingsForm


def handle_profile_form(self, request, profile):
    """Handle profile form submission"""
    form = ProfileSettingsForm(request.POST, request.FILES, instance=request.user)
    
    if form.is_valid():
        # Save user model fields
        form.save()
        
        # Save profile fields
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.bio = request.POST.get('bio', '')
        profile.timezone = request.POST.get('timezone', 'UTC')
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    return redirect('admin_settings')
