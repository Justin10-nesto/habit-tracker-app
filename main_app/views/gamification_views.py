"""
Views related to gamification features like achievements, badges, points, and leaderboards.
"""

from datetime import datetime, timedelta
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

from ..models import (
    LeaderboardEntry, PointTransaction, UserAchievement,
    UserBadge, UserPoints, UserProfile
)


class UserGamificationView(LoginRequiredMixin, View):
    """Display user's gamification profile (points, badges, achievements)"""
    login_url = 'login'
    
    def get(self, request):
        user_points, _ = UserPoints.objects.get_or_create(user=request.user)
        badges = UserBadge.objects.filter(user=request.user).select_related('badge')
        achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')
        
        # Get next level information
        next_level = user_points.level + 1
        points_needed = (next_level * 1000) - user_points.total_points
        
        # Recent point transactions
        recent_transactions = PointTransaction.objects.filter(user=request.user).order_by('-timestamp')[:10]
        
        # User appearance preferences
        try:
            theme = request.user.profile.appearance_settings.get('theme', 'light')
            show_animations = request.user.profile.appearance_settings.get('show_animations', True)
        except:
            theme = 'light'
            show_animations = True
        
        context = {
            'user_points': user_points,
            'badges': badges,
            'achievements': achievements,
            'next_level': next_level,
            'points_needed': points_needed,
            'recent_transactions': recent_transactions,
            'theme': theme,
            'show_animations': show_animations
        }
        
        return render(request, 'main_app/gamification.html', context)


class LeaderboardView(LoginRequiredMixin, View):
    """Display leaderboards"""
    login_url = 'login'
    
    def get(self, request):
        # Get period from query params, default to 'daily'
        period = request.GET.get('period', 'DAILY').upper()
        if period not in ['DAILY', 'WEEKLY', 'MONTHLY', 'ALL_TIME']:
            period = 'DAILY'
            
        # Get current date for period calculation
        today = datetime.utcnow().date()
        
        # Calculate date range based on period
        if period == 'DAILY':
            start_date = end_date = today
        elif period == 'WEEKLY':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'MONTHLY':
            start_date = today.replace(day=1)
            next_month = today.replace(month=today.month + 1) if today.month < 12 else today.replace(year=today.year + 1, month=1)
            end_date = next_month - timedelta(days=1)
        else:  # ALL_TIME
            start_date = datetime(2000, 1, 1).date()
            end_date = datetime(2100, 1, 1).date()
        
        # Apply privacy settings - only show users who allow being on leaderboards
        public_profiles = UserProfile.objects.filter(
            _privacy_settings__contains='"show_on_leaderboard":true'
        ).values_list('user_id', flat=True)
        
        # Get leaderboard entries for the period
        leaderboard = LeaderboardEntry.objects.filter(
            period_type=period,
            period_start=start_date,
            period_end=end_date,
            user_id__in=public_profiles
        ).select_related('user').order_by('-points')[:50]
        
        # Get user's position on the leaderboard
        try:
            user_entry = LeaderboardEntry.objects.get(
                user=request.user,
                period_type=period,
                period_start=start_date,
                period_end=end_date
            )
            user_rank = list(leaderboard).index(user_entry) + 1 if user_entry in leaderboard else \
                         LeaderboardEntry.objects.filter(
                             period_type=period,
                             period_start=start_date,
                             period_end=end_date,
                             points__gt=user_entry.points
                         ).count() + 1
            user_entry.rank = user_rank
        except LeaderboardEntry.DoesNotExist:
            user_entry = None
            user_rank = None
        
        # Get overall stats
        total_participants = LeaderboardEntry.objects.filter(
            period_type=period,
            period_start=start_date,
            period_end=end_date
        ).count()
        
        top_achievers = UserAchievement.objects.values('user__username').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        context = {
            'leaderboard': leaderboard,
            'user_entry': user_entry,
            'user_rank': user_rank,
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'total_participants': total_participants,
            'top_achievers': top_achievers
        }
        
        return render(request, 'main_app/leaderboard.html', context)


class AchievementsView(LoginRequiredMixin, View):
    """Display all achievements and user's progress"""
    login_url = 'login'
    
    def get(self, request):
        from ..models import Achievement, UserAchievement
        
        # Get all achievements
        all_achievements = Achievement.objects.all()
        
        # Get user's earned achievements
        user_achievements = UserAchievement.objects.filter(
            user=request.user
        ).select_related('achievement')
        
        earned_ids = [ua.achievement.id for ua in user_achievements]
        
        # Group achievements by category for better organization
        categorized_achievements = {}
        for achievement in all_achievements:
            category = achievement.category if hasattr(achievement, 'category') else 'General'
            if category not in categorized_achievements:
                categorized_achievements[category] = {
                    'earned': [],
                    'unearned': []
                }
            
            if achievement.id in earned_ids:
                # Find the UserAchievement to get the earned date
                user_achievement = next((ua for ua in user_achievements if ua.achievement.id == achievement.id), None)
                categorized_achievements[category]['earned'].append({
                    'achievement': achievement,
                    'earned_date': user_achievement.earned_date if user_achievement else None
                })
            else:
                categorized_achievements[category]['unearned'].append({
                    'achievement': achievement,
                    'earned_date': None
                })
        
        context = {
            'categorized_achievements': categorized_achievements,
            'total_earned': len(earned_ids),
            'total_achievements': all_achievements.count()
        }
        
        return render(request, 'main_app/achievements.html', context)


class BadgesView(LoginRequiredMixin, View):
    """Display all badges and user's progress"""
    login_url = 'login'
    
    def get(self, request):
        from ..models import Badge, UserBadge
        
        # Get all badges
        all_badges = Badge.objects.all()
        
        # Get user's earned badges
        user_badges = UserBadge.objects.filter(
            user=request.user
        ).select_related('badge')
        
        earned_ids = [ub.badge.id for ub in user_badges]
        
        # Group badges by type
        badges_by_type = {}
        for badge in all_badges:
            badge_type = badge.badge_type
            if badge_type not in badges_by_type:
                badges_by_type[badge_type] = {
                    'earned': [],
                    'unearned': []
                }
            
            if badge.id in earned_ids:
                # Find the UserBadge to get the earned date
                user_badge = next((ub for ub in user_badges if ub.badge.id == badge.id), None)
                badges_by_type[badge_type]['earned'].append({
                    'badge': badge,
                    'earned_date': user_badge.earned_date if user_badge else None
                })
            else:
                badges_by_type[badge_type]['unearned'].append({
                    'badge': badge,
                    'earned_date': None
                })
        
        context = {
            'badges_by_type': badges_by_type,
            'total_earned': len(earned_ids),
            'total_badges': all_badges.count()
        }
        
        return render(request, 'main_app/badges.html', context)
