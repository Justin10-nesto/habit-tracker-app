"""
Signal handlers for habit-related models.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from ..models.habit_models import (
    HabitCompletion, UserHabit, HabitStreak, MissedHabit
)
from ..models.analytics_models import HabitAnalytics
from ..models.gamification_models import UserPoints


@receiver(post_save, sender=HabitCompletion)
def update_streak_on_completion(sender, instance, created, **kwargs):
    """Update streak when a habit is completed"""
    if created:
        user_habit = instance.user_habit
        today = instance.completion_date
        
        # Update analytics
        analytics, _ = HabitAnalytics.objects.get_or_create(
            user=user_habit.user,
            habit=user_habit.habit
        )
        analytics.calculate_analytics()
        
        # Award points
        try:
            user_points, _ = UserPoints.objects.get_or_create(user=user_habit.user)
            points = 10  # Basic points for completion
            
            # Award bonus points for continuing streak
            if user_habit.streak >= 7:
                streak_bonus = min(user_habit.streak // 7 * 5, 50)  # Cap bonus at 50 points
                points += streak_bonus
            
            user_points.add_points(
                points,
                'COMPLETION',
                f"Completed {user_habit.habit.name}",
                reference_id=str(instance.id)
            )
            
        except Exception as e:
            # Log error but don't stop execution
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error awarding points for habit completion: {e}")


@receiver(pre_save, sender=UserHabit)
def create_habit_streak_record(sender, instance, **kwargs):
    """Create a streak record when a streak changes"""
    if instance.pk:  # Only for existing habits
        try:
            old_instance = UserHabit.objects.get(pk=instance.pk)
            
            # Check if streak has changed
            if old_instance.streak != instance.streak:
                # If streak increased, update current streak or create new one
                if instance.streak > old_instance.streak:
                    # Find the current active streak or create a new one
                    try:
                        current_streak = HabitStreak.objects.get(
                            user_habit=instance,
                            end_date=None
                        )
                        current_streak.streak_length = instance.streak
                        current_streak.save()
                    except HabitStreak.DoesNotExist:
                        # Create a new streak record
                        HabitStreak.objects.create(
                            user_habit=instance,
                            streak_length=instance.streak,
                            start_date=instance.last_completed - timedelta(days=instance.streak - 1)
                            if instance.last_completed else timezone.now().date()
                        )
                # If streak decreased or reset, close any active streak
                elif instance.streak < old_instance.streak:
                    try:
                        active_streak = HabitStreak.objects.get(
                            user_habit=instance,
                            end_date=None
                        )
                        active_streak.end_date = timezone.now().date()
                        active_streak.save()
                        
                        # If streak didn't reset to 0, create a new one
                        if instance.streak > 0:
                            HabitStreak.objects.create(
                                user_habit=instance,
                                streak_length=instance.streak,
                                start_date=instance.last_completed - timedelta(days=instance.streak - 1)
                                if instance.last_completed else timezone.now().date()
                            )
                    except HabitStreak.DoesNotExist:
                        pass  # No active streak to close
        except UserHabit.DoesNotExist:
            pass  # This should not happen normally
