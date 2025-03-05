"""
Analytics models for the Habit Tracker application.
"""

from django.db import models
from django.contrib.auth.models import User
from .base import get_uuid


class HabitAnalytics(models.Model):
    """Analytics data for habits"""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habit_analytics')
    habit = models.ForeignKey('Habit', on_delete=models.CASCADE, related_name='analytics', to_field='id')
    longest_streak = models.IntegerField(default=0)
    missed_count = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0)  # Percentage of days completed
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'habit']
        verbose_name_plural = "Habit analytics"
    
    def __str__(self):
        return f"Analytics for {self.user.username}'s {self.habit.name}"
    
    def calculate_analytics(self):
        """Calculate analytics for this habit"""
        from .habit_models import HabitCompletion, MissedHabit
        from django.db.models import Max, Count
        from django.utils import timezone
        import datetime
        
        # Get the user habit
        user_habit = self.habit.users.filter(user=self.user).first()
        if not user_habit:
            return
        
        # Calculate longest streak
        self.longest_streak = user_habit.streak
        
        # Calculate missed count
        self.missed_count = MissedHabit.objects.filter(user_habit=user_habit).count()
        
        # Calculate completion rate
        start_date = user_habit.start_date
        today = timezone.now().date()
        days_since_start = (today - start_date).days + 1
        completions = HabitCompletion.objects.filter(user_habit=user_habit).count()
        
        if days_since_start > 0:
            self.completion_rate = (completions / days_since_start) * 100
        else:
            self.completion_rate = 0
            
        self.save()
