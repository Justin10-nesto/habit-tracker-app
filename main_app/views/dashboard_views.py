"""
Dashboard views for the main application dashboard.
"""

from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import UserHabit, HabitCompletion
from django.utils import timezone


class DashboardView(LoginRequiredMixin, View):
    """Main dashboard view displaying user's habit overview"""
    login_url = 'login'
    
    def get(self, request, *args, **kwargs):
        # Get today's date
        today = timezone.now().date()
        
        # Get user's active habits
        active_habits = UserHabit.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('habit')
        
        # Get today's completions
        today_completions = HabitCompletion.objects.filter(
            user_habit__user=request.user,
            completion_date=today
        ).values_list('user_habit_id', flat=True)
        
        # User's appearance preferences (for UI customization)
        try:
            theme = request.user.profile.appearance_settings.get('theme', 'light')
            compact_view = request.user.profile.appearance_settings.get('compact_view', False)
        except:
            theme = 'light'
            compact_view = False
        
        # Prepare habit data for display
        habits_data = []
        for habit in active_habits:
            habits_data.append({
                'id': habit.id,
                'name': habit.habit.name,
                'description': habit.habit.description,
                'streak': habit.streak,
                'completed_today': habit.id in today_completions,
                'category': habit.habit.category.name if habit.habit.category else 'Uncategorized'
            })
            
        # Get stats for the dashboard
        completed_count = len(today_completions)
        total_count = active_habits.count()
        completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0
            
        context = {
            'habits': habits_data,
            'stats': {
                'completed_count': completed_count,
                'total_count': total_count,
                'completion_rate': round(completion_rate, 1)
            },
            'today': today,
            'theme': theme,
            'compact_view': compact_view
        }
        
        return render(request, 'main_app/dashboard.html', context)
