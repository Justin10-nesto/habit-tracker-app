"""
Analytics metrics for measuring user engagement, habit adherence and system health
"""

from django.db.models import Count, Sum, Avg, F, Q, Window
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import (
    User, HabitCompletion, UserHabit, Habit, MissedHabit,
    PointTransaction, LeaderboardEntry
)

class EngagementMetrics:
    """
    Metrics related to user engagement with the platform
    """
    
    @staticmethod
    def daily_active_users(days_back=30):
        """Calculate DAU over the specified period"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Get daily active users (users who completed at least one habit on each day)
        daily_users = (
            HabitCompletion.objects
            .filter(completion_date__gte=start_date, completion_date__lte=end_date)
            .annotate(date=TruncDate('completion_date'))
            .values('date')
            .annotate(count=Count('user_habit__user', distinct=True))
            .order_by('date')
        )
        
        # Convert to list of dicts with date strings
        result = []
        current_date = start_date
        
        # Create a lookup dictionary for quick access
        dau_lookup = {item['date']: item['count'] for item in daily_users}
        
        while current_date <= end_date:
            count = dau_lookup.get(current_date, 0)
            result.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'active_users': count
            })
            current_date += timedelta(days=1)
            
        return result
    
    @staticmethod
    def retention_rates(cohort_days=30):
        """
        Calculate retention rates for user cohorts
        Returns percentage of users who are still active after registration
        """
        today = timezone.now().date()
        
        # Define cohorts (users who registered during specific periods)
        cohorts = []
        
        # Last 12 cohorts (months)
        for i in range(0, 12):
            cohort_start = today.replace(day=1) - timedelta(days=i*30)
            cohort_end = (cohort_start.replace(month=cohort_start.month+1) 
                         if cohort_start.month < 12 
                         else cohort_start.replace(year=cohort_start.year+1, month=1)) - timedelta(days=1)
            
            # Users who registered in this cohort
            users_in_cohort = User.objects.filter(
                date_joined__date__gte=cohort_start,
                date_joined__date__lte=cohort_end
            )
            cohort_size = users_in_cohort.count()
            
            # Skip empty cohorts
            if cohort_size == 0:
                continue
                
            # Check how many users are still active
            active_after_30d = users_in_cohort.filter(
                habitcompletion__completion_date__gte=F('date_joined') + timedelta(days=30)
            ).distinct().count()
            
            retention_30d = round(active_after_30d / cohort_size * 100, 1) if cohort_size else 0
            
            cohorts.append({
                'period': f"{cohort_start.strftime('%b %Y')}",
                'cohort_size': cohort_size,
                'retention_30d': retention_30d
            })
            
        return cohorts


class HabitMetrics:
    """
    Metrics related to habits and their completion rates
    """
    
    @staticmethod
    def completion_rates_by_periodicity():
        """Calculate habit completion rates grouped by periodicity"""
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # All active habits during the time period
        active_habits = UserHabit.objects.filter(
            is_active=True,
            start_date__lte=today
        )
        
        results = []
        
        for periodicity, _ in Habit.PERIODICITY_CHOICES:
            habits_of_type = active_habits.filter(habit__periodicity=periodicity)
            habit_count = habits_of_type.count()
            
            if habit_count == 0:
                continue
                
            # Calculate completions and misses
            completions = HabitCompletion.objects.filter(
                user_habit__in=habits_of_type,
                completion_date__gte=thirty_days_ago
            ).count()
            
            misses = MissedHabit.objects.filter(
                user_habit__in=habits_of_type,
                missed_date__gte=thirty_days_ago
            ).count()
            
            total = completions + misses
            completion_rate = round(completions / total * 100, 1) if total > 0 else 0
            
            results.append({
                'periodicity': periodicity,
                'completion_rate': completion_rate,
                'total_habits': habit_count,
                'completions': completions,
                'misses': misses
            })
            
        return results
    
    @staticmethod
    def popular_habits(limit=10):
        """Get the most popular habits based on number of users tracking them"""
        popular = (
            UserHabit.objects
            .values('habit__name', 'habit__id', 'habit__periodicity')
            .annotate(user_count=Count('user', distinct=True))
            .order_by('-user_count')
        )[:limit]
        
        return list(popular)
    
    @staticmethod
    def streak_distribution():
        """Calculate distribution of streak lengths"""
        # Define streak buckets
        buckets = [
            (0, "No streak"), 
            (1, "1 day"),
            (2, "2-3 days"),
            (4, "4-6 days"),
            (7, "1 week"),
            (14, "2 weeks"),
            (21, "3 weeks"),
            (30, "1 month"),
            (60, "2 months"),
            (90, "3 months"),
            (180, "6 months"),
            (365, "1 year+")
        ]
        
        # Count habits in each streak bucket
        results = []
        all_habits = UserHabit.objects.all()
        total_count = all_habits.count()
        
        if total_count == 0:
            return []
            
        for i, (days, label) in enumerate(buckets):
            # Define the range for this bucket
            min_streak = days
            max_streak = buckets[i+1][0]-1 if i+1 < len(buckets) else None
            
            if max_streak:
                count = all_habits.filter(streak__gte=min_streak, streak__lte=max_streak).count()
            else:
                count = all_habits.filter(streak__gte=min_streak).count()
                
            percentage = round(count / total_count * 100, 1)
            
            results.append({
                'label': label,
                'count': count,
                'percentage': percentage,
                'min_days': min_streak,
                'max_days': max_streak
            })
            
        return results
