from main_app.models.habit_models import HabitStreak
from ..models import UserProfile, HabitCompletion, UserHabit, LeaderboardEntry, HabitAnalytics, MissedHabit
from django.db.models import Count, Avg, Max, Q
from django.contrib.auth.models import User
import datetime
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service to handle analytics while respecting user privacy settings"""
    
    @staticmethod
    def filter_users_by_privacy(queryset, visibility="public_only"):
        """
        Filter a queryset of users based on privacy settings.
        
        Args:
            queryset: The User queryset to filter
            visibility: One of ("public_only", "friends_and_public", "all")
        
        Returns:
            Filtered queryset
        """
        if visibility not in ["public_only", "friends_and_public", "all"]:
            visibility = "public_only"
        
        if visibility == "all":
            # No filtering needed for admin views
            return queryset
        
        # Start with users who have public profiles
        filtered_users = queryset.filter(
            profile___privacy_settings__contains='"public_profile":true'
        )
        
        if visibility == "friends_and_public":
            # For views that should show friends and public profiles
            # In a real app, you'd add friends-based filtering here
            pass
        
        return filtered_users
    
    @classmethod
    def get_leaderboard(cls, period_type="WEEKLY", visibility="public_only", limit=10):
        """
        Get leaderboard data respecting privacy settings
        
        Args:
            period_type: One of ("DAILY", "WEEKLY", "MONTHLY", "ALL_TIME")
            visibility: One of ("public_only", "friends_and_public", "all")
            limit: Maximum number of entries to return
        
        Returns:
            List of leaderboard entries
        """
        # First step: Get only users who allow being on leaderboards
        users_on_leaderboard = User.objects.filter(
            profile___privacy_settings__contains='"show_on_leaderboard":true'
        )
        
        # Apply additional privacy filters
        users_on_leaderboard = cls.filter_users_by_privacy(users_on_leaderboard, visibility)
        
        # Get leaderboard entries for filtered users
        leaderboard = LeaderboardEntry.objects.filter(
            period_type=period_type,
            user__in=users_on_leaderboard
        ).select_related('user').order_by('-points')[:limit]
        
        return leaderboard
    
    @classmethod
    def get_global_stats(cls, visibility="public_only"):
        """
        Get global stats respecting privacy settings
        
        Args:
            visibility: One of ("public_only", "friends_and_public", "all")
            
        Returns:
            Dictionary of global stats
        """
        # Filter users based on privacy settings
        users = cls.filter_users_by_privacy(User.objects.all(), visibility)
        
        # Get completions for these users
        completions = HabitCompletion.objects.filter(
            user_habit__user__in=users
        )
        
        # Calculate totals
        today = datetime.date.today()
        total_habits = UserHabit.objects.filter(user__in=users).count()
        habits_completed_today = completions.filter(completion_date=today).count()
        total_completions = completions.count()
        
        # Get streak stats
        max_streak = UserHabit.objects.filter(user__in=users).aggregate(max_streak=Max('streak'))
        avg_streak = UserHabit.objects.filter(user__in=users).aggregate(avg_streak=Avg('streak'))
        
        return {
            'total_users': users.count(),
            'total_habits': total_habits,
            'habits_completed_today': habits_completed_today,
            'total_completions': total_completions,
            'max_streak': max_streak['max_streak'] or 0,
            'avg_streak': round(avg_streak['avg_streak'] or 0, 1),
        }
    
    @staticmethod
    def update_analytics_for_completion(user_habit):
        """
        Update analytics after a habit completion
        This should be called whenever a habit is marked as completed
        """
        user = user_habit.user
        habit = user_habit.habit
        
        # Get or create analytics record
        analytics, created = HabitAnalytics.objects.get_or_create(
            user=user,
            habit=habit
        )
        
        # Update longest streak if current streak is longer
        if user_habit.streak > analytics.longest_streak:
            analytics.longest_streak = user_habit.streak
            
        # Get the completion rate
        total_days = AnalyticsService._calculate_total_tracking_days(user_habit)
        completed_days = HabitCompletion.objects.filter(
            user_habit=user_habit
        ).count()
        
        if total_days > 0:
            completion_rate = (completed_days / total_days) * 100
            analytics.completion_rate = round(completion_rate, 2)
            
        analytics.save()
        
        # Log for debugging
        print(f"Updated analytics for {user.username}'s habit '{habit.name}': "
              f"longest_streak={analytics.longest_streak}, "
              f"missed_count={analytics.missed_count}")
    
    @staticmethod
    def update_analytics_for_missed_habit(user_habit):
        """
        Update analytics after a habit is missed
        This should be called whenever a habit is marked as missed
        """
        user = user_habit.user
        habit = user_habit.habit
        
        # Get or create analytics record
        analytics, created = HabitAnalytics.objects.get_or_create(
            user=user,
            habit=habit
        )
        
        # Increment missed count
        analytics.missed_count += 1
        
        # Recalculate completion rate
        total_days = AnalyticsService._calculate_total_tracking_days(user_habit)
        completed_days = HabitCompletion.objects.filter(
            user_habit=user_habit
        ).count()
        
        if total_days > 0:
            completion_rate = (completed_days / total_days) * 100
            analytics.completion_rate = round(completion_rate, 2)
        
        analytics.save()
        
        # Log for debugging
        print(f"Updated analytics for {user.username}'s habit '{habit.name}' after miss: "
              f"missed_count={analytics.missed_count}, "
              f"completion_rate={analytics.completion_rate}%")
    
    @staticmethod
    def _calculate_total_tracking_days(user_habit):
        """Calculate the total number of days since habit tracking began"""
        start_date = user_habit.start_date
        today = datetime.now().date()
        
        # Calculate days based on periodicity
        if user_habit.habit.periodicity == 'DAILY':
            # For daily habits, it's just the number of days since start
            delta = today - start_date
            return max(1, delta.days + 1)  # Include today
            
        elif user_habit.habit.periodicity == 'WEEKLY':
            # For weekly habits, count the number of weeks
            delta = today - start_date
            weeks = delta.days // 7 + 1  # Include current week
            return max(1, weeks)
            
        elif user_habit.habit.periodicity == 'MONTHLY':
            # For monthly habits, count the number of months
            months = (today.year - start_date.year) * 12 + today.month - start_date.month
            if today.day >= start_date.day:
                months += 1  # Include current month if we've passed the start day
            return max(1, months)
            
        return 1  # Default fallback
    
    @staticmethod
    def recalculate_analytics(user_habit):
        """
        Recalculate all analytics for a user habit based on historical data
        This can fix analytics that have gotten out of sync
        """
        user = user_habit.user
        habit = user_habit.habit
        
        # Get or create analytics record
        analytics, created = HabitAnalytics.objects.get_or_create(
            user=user,
            habit=habit
        )
        
        # Calculate longest streak from streak history
        max_streak_from_history = HabitStreak.objects.filter(
            user_habit=user_habit
        ).aggregate(Max('streak_length'))['streak_length__max'] or 0
        
        # If current streak is longer than any historical streak, use that
        analytics.longest_streak = max(max_streak_from_history, user_habit.streak)
        
        # Count missed days
        analytics.missed_count = MissedHabit.objects.filter(
            user_habit=user_habit
        ).count()
        
        # Calculate completion rate
        total_days = AnalyticsService._calculate_total_tracking_days(user_habit)
        completed_days = HabitCompletion.objects.filter(
            user_habit=user_habit
        ).count()
        
        if total_days > 0:
            completion_rate = (completed_days / total_days) * 100
            analytics.completion_rate = round(completion_rate, 2)
        else:
            analytics.completion_rate = 0
            
        analytics.save()
        
        # Log what was updated
        print(f"Recalculated analytics for {user.username}'s habit '{habit.name}': "
              f"longest_streak={analytics.longest_streak}, "
              f"missed_count={analytics.missed_count}, "
              f"completion_rate={analytics.completion_rate}%")
        
        return analytics
    
    @staticmethod
    def recalculate_all_analytics():
        """
        Recalculate analytics for all user habits
        This is useful for fixing analytics data across the entire application
        """
        user_habits = UserHabit.objects.all()
        results = []
        
        for user_habit in user_habits:
            try:
                analytics = AnalyticsService.recalculate_analytics(user_habit)
                results.append({
                    'user_habit': user_habit,
                    'analytics': analytics,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'user_habit': user_habit,
                    'error': str(e),
                    'success': False
                })
        
        # Log summary
        success_count = sum(1 for r in results if r['success'])
        print(f"Recalculated analytics for {success_count}/{len(results)} habits successfully")
        
        return results
        
    @staticmethod
    def troubleshoot_habit_analytics(user_habit):
        """
        Diagnose issues with a specific user habit's analytics
        Returns diagnostic information to help identify problems
        """
        user = user_habit.user
        habit = user_habit.habit
        
        # Get analytics data
        try:
            analytics = HabitAnalytics.objects.get(user=user, habit=habit)
        except HabitAnalytics.DoesNotExist:
            analytics = None
        
        # Gather diagnostic info
        completions = HabitCompletion.objects.filter(user_habit=user_habit)
        missed = MissedHabit.objects.filter(user_habit=user_habit)
        streaks = HabitStreak.objects.filter(user_habit=user_habit)
        
        # Compute expected values
        expected_longest_streak = max(
            streaks.aggregate(Max('streak_length'))['streak_length__max'] or 0,
            user_habit.streak
        )
        expected_missed_count = missed.count()
        
        diagnostic = {
            'user_habit': {
                'id': user_habit.id,
                'user': user.username,
                'habit_name': habit.name,
                'current_streak': user_habit.streak,
                'start_date': user_habit.start_date,
                'last_completed': user_habit.last_completed
            },
            'analytics': {
                'exists': analytics is not None
            },
            'counts': {
                'completions': completions.count(),
                'missed_days': missed.count(),
                'streaks_recorded': streaks.count()
            },
            'expected_values': {
                'longest_streak': expected_longest_streak,
                'missed_count': expected_missed_count
            },
            'discrepancies': {}
        }
        
        # Add analytics details if they exist
        if analytics:
            diagnostic['analytics'].update({
                'longest_streak': analytics.longest_streak,
                'missed_count': analytics.missed_count,
                'completion_rate': getattr(analytics, 'completion_rate', None)
            })
            
            # Check for discrepancies
            if analytics.longest_streak != expected_longest_streak:
                diagnostic['discrepancies']['longest_streak'] = {
                    'expected': expected_longest_streak,
                    'actual': analytics.longest_streak
                }
                
            if analytics.missed_count != expected_missed_count:
                diagnostic['discrepancies']['missed_count'] = {
                    'expected': expected_missed_count,
                    'actual': analytics.missed_count
                }
        
        return diagnostic
