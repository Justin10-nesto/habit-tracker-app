def user_settings(request):
    """
    Add user settings to the context for all templates
    """
    context = {
        'user_appearance': {},
        'user_preferences': {},
        'user_privacy': {},
    }
    
    if request.user.is_authenticated:
        try:
            # Get the user profile if it exists
            profile = request.user.profile
            
            # Add settings to context
            context['user_appearance'] = profile.appearance_settings
            context['user_preferences'] = profile.notification_preferences
            context['user_privacy'] = profile.privacy_settings
        except Exception:
            # In case of any error, use empty dictionaries
            pass
    
    return context
