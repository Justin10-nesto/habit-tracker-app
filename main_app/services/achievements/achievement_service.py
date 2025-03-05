"""
Achievement Service - Manages checking and awarding achievements
Uses Singleton, Chain of Responsibility, and Factory patterns.
"""
import json
from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from django.db import transaction, models
from django.utils import timezone

from ...models import (
    Achievement, UserAchievement, HabitCompletion, UserHabit, HabitStreak
)
from ..points.points_service import PointsService
from .achievement_strategies import AchievementStrategyFactory
from ..events.event_system import EventSystem, EventTypes

class AchievementService:
    """
    Service for checking and awarding achievements
    Implements Singleton pattern
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AchievementService, cls).__new__(cls)
            cls._instance._points_service = PointsService()
        return cls._instance
    
    def check_achievements(self, user: User, event_type: str, **context) -> List[Achievement]:
        """
        Check if user has earned any achievements based on the event
        Returns a list of new achievements awarded
        """
        # Get all achievements the user doesn't already have
        user_achievements = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        available_achievements = Achievement.objects.exclude(id__in=user_achievements)
        
        # List to store newly earned achievements
        earned_achievements = []
        
        for achievement in available_achievements:
            # Determine the appropriate strategy for this achievement
            try:
                metadata = json.loads(achievement.metadata) if hasattr(achievement, 'metadata') and achievement.metadata else {}
                strategy_type = metadata.get('strategy', 'habit_completion_count')
                
                # Add event_type to context so strategies can filter by event
                context['event_type'] = event_type
                
                # Create strategy and check achievement
                strategy = AchievementStrategyFactory.get_strategy(strategy_type)
                
                # Add metadata to context for strategy
                context.update(metadata)
                
                if strategy.check_achievement(user, achievement, **context):
                    # Award the achievement
                    self._award_achievement(user, achievement)
                    earned_achievements.append(achievement)
            except Exception as e:
                print(f"Error checking achievement {achievement.id}: {e}")
        
        return earned_achievements
    
    def _award_achievement(self, user: User, achievement: Achievement) -> UserAchievement:
        """Award an achievement to a user and grant associated rewards"""
        try:
            with transaction.atomic():
                # Create user achievement record
                user_achievement = UserAchievement.objects.create(
                    user=user,
                    achievement=achievement,
                    earned_date=timezone.now()
                )
                
                # Award points if applicable
                if hasattr(achievement, 'points_awarded') and achievement.points_awarded > 0:
                    self._points_service.award_points(
                        user=user,
                        amount=achievement.points_awarded,
                        transaction_type='ACHIEVEMENT',
                        description=f"Achievement: {achievement.name}",
                        reference_id=user_achievement.id
                    )
                
                # Publish achievement earned event
                EventSystem.publish(
                    EventTypes.ACHIEVEMENT_EARNED,
                    user=user,
                    achievement=achievement,
                    user_achievement=user_achievement
                )
                
                return user_achievement
        except Exception as e:
            print(f"Error awarding achievement {achievement.id} to user {user.id}: {e}")
            raise
    
    def get_progress(self, user: User, achievement: Achievement) -> Dict[str, Any]:
        """Calculate progress towards an achievement"""
        try:
            metadata = json.loads(achievement.metadata) if hasattr(achievement, 'metadata') and achievement.metadata else {}
            strategy_type = metadata.get('strategy', 'habit_completion_count')
            
            # Create strategy
            strategy = AchievementStrategyFactory.get_strategy(strategy_type)
            
            # Calculate progress based on strategy type
            if strategy_type == 'habit_completion_count':
                current_count = self._get_habit_completion_count(user)
                required_count = metadata.get('required_count', 10)
                progress = min(100, (current_count / required_count) * 100)
                
                return {
                    'current': current_count,
                    'required': required_count,
                    'progress': progress,
                    'earned': current_count >= required_count
                }
            
            elif strategy_type == 'habit_streak':
                required_streak = metadata.get('required_streak', 7)
                current_streak = self._get_max_streak(user)
                progress = min(100, (current_streak / required_streak) * 100)
                
                return {
                    'current': current_streak,
                    'required': required_streak,
                    'progress': progress,
                    'earned': current_streak >= required_streak
                }
            
            elif strategy_type == 'user_level':
                current_level = self._points_service.get_user_level(user)
                required_level = metadata.get('required_level', 5)
                progress = min(100, (current_level / required_level) * 100)
                
                return {
                    'current': current_level,
                    'required': required_level,
                    'progress': progress,
                    'earned': current_level >= required_level
                }
            
            # Default minimal progress info
            return {
                'progress': 0,
                'earned': False
            }
        except Exception as e:
            print(f"Error calculating achievement progress: {e}")
            return {
                'progress': 0,
                'earned': False
            }
    
    def _get_habit_completion_count(self, user: User) -> int:
        """Get total habit completions for a user"""
        return HabitCompletion.objects.filter(user_habit__user=user).count()
    
    def _get_max_streak(self, user: User) -> int:
        """Get the user's maximum streak"""
        # Check current streaks
        current_max = UserHabit.objects.filter(user=user).aggregate(models.Max('streak'))
        current_max_streak = current_max.get('streak__max', 0) or 0
        
        # Check historical streaks
        historical_max = HabitStreak.objects.filter(user_habit__user=user).aggregate(models.Max('streak_length'))
        historical_max_streak = historical_max.get('streak_length__max', 0) or 0
        
        return max(current_max_streak, historical_max_streak)
