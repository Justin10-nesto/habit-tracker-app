"""
Admin views for achievements and badges.
"""

from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse

from .admin_views import AdminViewMixin
from django.views import View
from ..models import UserBadge, UserAchievement, Badge, Achievement
from ..services.achievements.achievement_service import AchievementService
from ..services.events import EventSystem, EventTypes

class AdminAchievementsView(AdminViewMixin, View):
    """View for achievements and badges."""
    
    def __init__(self):
        super().__init__()
        self.achievement_service = AchievementService()
        self.event_system = EventSystem()
    
    def get(self, request):
        # Get user badges and achievements
        badges = UserBadge.objects.filter(user=request.user).select_related('badge')
        achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')
        
        # Get available badges and achievements
        all_badges = Badge.objects.all()
        all_achievements = Achievement.objects.all()
        
        # User appearance settings for UI customization
        try:
            theme = request.user.profile.appearance_settings.get('theme', 'light')
            color_scheme = request.user.profile.appearance_settings.get('color_scheme', 'blue')
            show_animations = request.user.profile.appearance_settings.get('show_animations', True)
        except:
            theme = 'light'
            color_scheme = 'blue'
            show_animations = True
        
        context = {
            'active_page': 'achievements',
            'user_badges': badges,
            'user_achievements': achievements,
            'all_badges': all_badges,
            'all_achievements': all_achievements,
            'theme': theme,
            'color_scheme': color_scheme,
            'show_animations': show_animations
        }
        
        return render(request, 'admin/achievements.html', context)
    
    def post(self, request):
        """Handle achievement-related actions"""
        action = request.POST.get('action')
        achievement_id = request.POST.get('achievement_id')
        
        if action == 'check_achievement':
            try:
                achievement = Achievement.objects.get(id=achievement_id)
                # Check if user meets achievement criteria
                earned = self.achievement_service.check_achievements(
                    request.user,
                    EventTypes.USER_PROFILE_UPDATED.value,
                    achievement_id=achievement_id
                )
                
                if earned:
                    messages.success(request, f'Congratulations! You\'ve earned the {achievement.name} achievement!')
                    return JsonResponse({'status': 'success', 'earned': True})
                
                return JsonResponse({'status': 'success', 'earned': False})
                
            except Achievement.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Achievement not found'}, status=404)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
