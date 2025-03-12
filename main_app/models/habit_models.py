"""
Habit-related models for the Habit Tracker application.
"""

from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from .base import get_uuid, get_current_date, get_current_datetime


class Category(models.Model):
    """Categories for organizing habits"""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=get_current_datetime)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name


class Habit(models.Model):
    """Base habit definition"""
    PERIODICITY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    ]
    
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    name = models.CharField(max_length=100)
    description = models.TextField()
    periodicity = models.CharField(max_length=10, choices=PERIODICITY_CHOICES)
    created_at = models.DateTimeField(default=get_current_datetime)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='habits', to_field='id')
    
    def __str__(self):
        return self.name


class UserHabit(models.Model):
    """User-specific habit instance"""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='users', to_field='id')
    streak = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(default=get_current_date)
    last_completed = models.DateField(null=True, blank=True)
    
    def increment_streak(self):
        """Increment the streak count"""
        self.streak += 1
        self.save()
    
    def reset_streak(self):
        """Reset the streak count to zero"""
        self.streak = 0
        self.save()
    
    def __str__(self):
        return f"{self.user.username}'s {self.habit.name}"
    
    def calculate_streak(self):
        """Calculate the current streak based on completions"""
        from .habit_models import HabitCompletion
        from datetime import timedelta
        
        # Get completions in descending order (most recent first)
        completions = HabitCompletion.objects.filter(
            user_habit=self
        ).order_by('-completion_date')
        
        if not completions:
            return 0
        
        # Start with the most recent completion
        streak = 1
        last_date = completions[0].completion_date
        
        # Check for consecutive dates (depending on periodicity)
        for i in range(1, len(completions)):
            completion = completions[i]
            expected_date = None
            
            if self.habit.periodicity == 'DAILY':
                expected_date = last_date - timedelta(days=1)
            elif self.habit.periodicity == 'WEEKLY':
                expected_date = last_date - timedelta(days=7)
            elif self.habit.periodicity == 'MONTHLY':
                # Approximate for monthly
                expected_date = last_date - timedelta(days=30)
            
            if completion.completion_date == expected_date:
                streak += 1
                last_date = completion.completion_date
            else:
                break
        
        return streak


class HabitCompletion(models.Model):
    """Record of habit completion"""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user_habit = models.ForeignKey(UserHabit, on_delete=models.CASCADE, related_name='completions')
    completion_date = models.DateField(default=get_current_date)
    created_at = models.DateTimeField(default=get_current_datetime)
    
    class Meta:
        unique_together = ['user_habit', 'completion_date']
    
    def clean(self):
        """Validate the completion record"""
        super().clean()
        # Check for existing completion on the same date
        if HabitCompletion.objects.filter(
            user_habit=self.user_habit,
            completion_date=self.completion_date
        ).exclude(id=self.id).exists():
            raise ValidationError({
                'completion_date': 'A completion record already exists for this habit on this date.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_habit} completed on {self.completion_date}"


class HabitStreak(models.Model):
    """Tracking of continuous habit completions"""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user_habit = models.ForeignKey(UserHabit, on_delete=models.CASCADE, related_name='streaks', to_field='id')
    streak_length = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    def clean(self):
        """Validate that end_date is not before start_date"""
        from django.core.exceptions import ValidationError
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date.')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "ongoing" if self.end_date is None else "ended"
        return f"{self.user_habit} streak of {self.streak_length} days ({status})"

class HabitHistory(models.Model):
    """Historical record of habit completions"""
    id = models.CharField(primary_key=True, max_length=36)
    user_habit = models.ForeignKey(UserHabit, on_delete=models.CASCADE, related_name='history', to_field='id')
    completion_date = models.DateField()
    
    class Meta:
        verbose_name_plural = "Habit histories"
    
    def __str__(self):
        return f"{self.user_habit} completed on {self.completion_date}"

class MissedHabit(models.Model):
    """Record of habits that were missed on their scheduled day"""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user_habit = models.ForeignKey(UserHabit, on_delete=models.CASCADE, related_name='missed_days', to_field='id')
    missed_date = models.DateField()
    created_at = models.DateTimeField(default=get_current_datetime)
    
    class Meta:
        unique_together = ['user_habit', 'missed_date']
    
    def __str__(self):
        return f"{self.user_habit} missed on {self.missed_date}"


class Reminder(models.Model):
    """Reminders for habit completion"""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user_habit = models.ForeignKey(UserHabit, on_delete=models.CASCADE, related_name='reminders', to_field='id')
    reminder_time = models.TimeField()
    reminder_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        date_info = f" on {self.reminder_date}" if self.reminder_date else " (recurring)"
        return f"{self.user_habit} reminder at {self.reminder_time}{date_info}"

