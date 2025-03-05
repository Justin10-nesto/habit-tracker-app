"""
Admin panel views for the habit tracker application.
Contains view classes for the admin dashboard and main administrative functions.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views import View
from django.utils import timezone
from django.core.paginator import Paginator

from ..models import (
    Habit, Category, MissedHabit, Reminder, UserHabit, HabitCompletion,
    UserProfile, UserSession, get_uuid
)

import datetime


class AdminViewMixin:
    """
    Mixin to add common functionality to all admin views.
    Ensures the user has proper permissions to access admin features.
    """
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # Check if user is a staff member or has admin privileges
        if not request.user.is_active:
            return redirect('dashboard')  # Redirect to regular dashboard if not staff
        return super().dispatch(request, *args, **kwargs)


class AdminDashboardView(AdminViewMixin, View):
    """Admin dashboard view showing key statistics and recent activity."""
    
    def get(self, request):
        # Get today's date
        today = timezone.now().date()
        
        # Get counts for dashboard stats
        active_habits_count = UserHabit.objects.filter(user=request.user, is_active=True).count()
        
        # Get active streaks
        active_streaks = UserHabit.objects.filter(
            user=request.user, 
            is_active=True, 
            streak__gt=0
        ).count()
        
        # Get daily habits
        daily_habits = UserHabit.objects.filter(
            user=request.user,
            is_active=True,
            habit__periodicity='DAILY'
        )
        daily_habits_count = daily_habits.count()
        
        # Get completions for today
        completed_today = HabitCompletion.objects.filter(
            user_habit__user=request.user,
            completion_date=today
        ).count()
        
        # Get habits with progress for today
        today_habits = []
        for habit in daily_habits:
            # Calculate progress based on completion status
            completion = HabitCompletion.objects.filter(
                user_habit=habit,
                completion_date=today
            ).exists()
            
            today_habits.append({
                'name': habit.habit.name,
                'progress': 100 if completion else 0
            })
        
        # Get user points and level progress from a helper method
        points_data = self._get_user_points_data(request.user)
        
        context = {
            'active_page': 'dashboard',
            'active_habits_count': active_habits_count,
            'active_streaks_count': active_streaks,
            'daily_habits_count': daily_habits_count,
            'completed_today': completed_today,
            'today_habits': today_habits,
            'recent_badges': self._get_recent_badges(request.user),
            **points_data
        }
        
        return render(request, 'admin/dashboard.html', context)
    
    def _get_recent_badges(self, user):
        """Get recent badges earned by the user"""
        from ..models import UserBadge
        return UserBadge.objects.filter(
            user=user
        ).select_related('badge').order_by('-earned_date')[:5]
    
    def _get_user_points_data(self, user):
        """Get points and level data for the user"""
        from ..models import UserPoints
        
        try:
            user_points = UserPoints.objects.get(user=user)
            total_points = user_points.total_points
            level = user_points.level
            
            # Calculate progress to next level (assuming 1000 points per level)
            points_in_current_level = total_points % 1000
            level_progress = int((points_in_current_level / 1000) * 100)
            
            return {
                'total_points': total_points,
                'level': level,
                'level_progress': level_progress,
                'points_needed': 1000 - points_in_current_level
            }
        except UserPoints.DoesNotExist:
            return {
                'total_points': 0,
                'level': 1,
                'level_progress': 0,
                'points_needed': 1000
            }


# Import the sub-views that belong in other files
from .admin_habit_views import AdminHabitsView, AdminCategoriesView, AdminMyHabitsView
from .admin_analytics_views import AdminAnalyticsView
from .admin_social_views import AdminSocialView
from .admin_achievement_views import AdminAchievementsView
from .admin_settings_views import AdminSettingsView