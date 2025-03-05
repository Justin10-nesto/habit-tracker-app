"""
Privacy settings and data management handlers for the admin settings view.
"""

from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
from ..forms import PrivacySettingsForm
import json


def handle_privacy_form(self, request, profile):
    """Handle privacy settings form submission"""
    form = PrivacySettingsForm(request.POST)
    
    if form.is_valid():
        # Get the current privacy settings or initialize new ones
        privacy_settings = profile.privacy_settings
        
        # Update with form data
        privacy_settings.update({
            'public_profile': form.cleaned_data.get('public_profile', False),
            'profile_visibility': form.cleaned_data['profile_visibility'],
            'show_on_leaderboard': form.cleaned_data.get('show_on_leaderboard', False),
        })
        
        # Save to profile
        profile.privacy_settings = privacy_settings
        profile.save()
        
        messages.success(request, 'Privacy settings updated successfully!')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    return redirect('admin_settings')


def handle_data_form(self, request):
    """Handle data management actions"""
    if 'export_data' in request.POST:
        # Generate a JSON export of the user's data
        data = self._export_user_data(request.user)
        
        # Create a downloadable JSON response
        response = HttpResponse(json.dumps(data, indent=4), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{request.user.username}_data_export.json"'
        return response
    elif 'delete_data' in request.POST:
        # This would normally require additional confirmation
        messages.warning(request, 'Data deletion requires additional confirmation. Please contact support.')
    
    return redirect('admin_settings')


def _export_user_data(self, user):
    """Export all user data as a dictionary"""
    from ..models import UserHabit, HabitCompletion, UserAchievement, UserBadge, UserProfile
    
    # Get the user profile
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = None
    
    # Gather basic user data
    data = {
        'user': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        },
        'profile': {
            'bio': profile.bio if profile else '',
            'timezone': profile.timezone if profile else 'UTC',
        },
        'settings': {
            'notifications': profile.notification_preferences if profile else {},
            'appearance': profile.appearance_settings if profile else {},
            'privacy': profile.privacy_settings if profile else {},
        },
        'habits': [],
        'completions': [],
        'achievements': [],
        'badges': [],
    }
    
    # Get user habits
    user_habits = UserHabit.objects.filter(user=user).select_related('habit')
    for user_habit in user_habits:
        data['habits'].append({
            'name': user_habit.habit.name,
            'description': user_habit.habit.description,
            'periodicity': user_habit.habit.periodicity,
            'streak': user_habit.streak,
            'start_date': user_habit.start_date.isoformat(),
            'is_active': user_habit.is_active,
            'category': user_habit.habit.category.name if user_habit.habit.category else None,
        })
    
    # Get completions
    completions = HabitCompletion.objects.filter(user_habit__user=user).select_related('user_habit__habit')
    for completion in completions:
        data['completions'].append({
            'habit_name': completion.user_habit.habit.name,
            'completion_date': completion.completion_date.isoformat(),
            'timestamp': completion.timestamp.isoformat(),
        })
    
    # Get achievements
    achievements = UserAchievement.objects.filter(user=user).select_related('achievement')
    for achievement in achievements:
        data['achievements'].append({
            'name': achievement.achievement.name,
            'description': achievement.achievement.description,
            'earned_date': achievement.earned_date.isoformat(),
        })
    
    # Get badges
    badges = UserBadge.objects.filter(user=user).select_related('badge')
    for badge in badges:
        data['badges'].append({
            'name': badge.badge.name,
            'description': badge.badge.description,
            'earned_date': badge.earned_date.isoformat(),
        })
    
    return data
