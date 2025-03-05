"""
Appearance settings handlers for the admin settings view.
"""

from django.shortcuts import redirect
from django.contrib import messages
from ..forms import AppearanceSettingsForm


def handle_appearance_form(self, request, profile):
    """Handle appearance settings form submission"""
    form = AppearanceSettingsForm(request.POST)
    
    if form.is_valid():
        # Get the current appearance settings or initialize new ones
        appearance_settings = profile.appearance_settings
        
        # Update with form data
        appearance_settings.update({
            'theme': form.cleaned_data['theme'],
            'color_scheme': form.cleaned_data['color_scheme'],
            'dashboard_display': form.cleaned_data['dashboard_display'],
            'compact_view': form.cleaned_data.get('compact_view', False),
            'show_animations': form.cleaned_data.get('show_animations', True),
        })
        
        # Save to profile
        profile.appearance_settings = appearance_settings
        profile.save()
        
        # Apply appearance settings immediately
        request.session['theme'] = form.cleaned_data['theme']
        request.session['color_scheme'] = form.cleaned_data['color_scheme']
        
        messages.success(request, 'Appearance settings updated successfully!')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    return redirect('admin_settings')
