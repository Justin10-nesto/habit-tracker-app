"""Achievement Strategies - Defines different strategies for checking achievements
Implements Strategy and Factory patterns.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from ...models import Achievement, HabitCompletion, UserHabit, HabitStreak

class AchievementStrategy(ABC):
    """Base class for achievement checking strategies"""
    
    @abstractmethod
    def check_achievement(self, user: User, achievement: Achievement, **context) -> bool:
        """Check if the user has earned the achievement"""
        pass

class HabitCompletionCountStrategy(AchievementStrategy):
    """Strategy for achievements based on total habit completions"""
    
    def check_achievement(self, user: User, achievement: Achievement, **context) -> bool:
        required_count = context.get('required_count', 0)
        habit_type = context.get('habit_type')
        
        # Query to get completion count
        completions_query = HabitCompletion.objects.filter(user_habit__user=user)
        
        # Filter by habit type if specified
        if habit_type:
            completions_query = completions_query.filter(user_habit__habit__type=habit_type)
            
        return completions_query.count() >= required_count

class StreakStrategy(AchievementStrategy):
    """Strategy for achievements based on habit streaks"""
    
    def check_achievement(self, user: User, achievement: Achievement, **context) -> bool:
        required_streak = context.get('required_streak', 0)
        habit_type = context.get('habit_type')
        
        # Query to get streak information
        streaks_query = HabitStreak.objects.filter(user_habit__user=user)
        
        # Filter by habit type if specified
        if habit_type:
            streaks_query = streaks_query.filter(user_habit__habit__type=habit_type)
            
        # Check if any streak meets the requirement
        return streaks_query.filter(current_streak__gte=required_streak).exists()

class HabitDiversityStrategy(AchievementStrategy):
    """Strategy for achievements based on maintaining multiple habits"""
    
    def check_achievement(self, user: User, achievement: Achievement, **context) -> bool:
        required_habits = context.get('required_habits', 0)
        active_status = context.get('active_status', True)
        
        # Count active habits
        active_habits = UserHabit.objects.filter(
            user=user,
            is_active=active_status
        ).count()
        
        return active_habits >= required_habits

class AchievementStrategyFactory:
    """Factory for creating achievement checking strategies"""
    
    _strategies: Dict[str, type] = {
        'habit_completion_count': HabitCompletionCountStrategy,
        'streak': StreakStrategy,
        'habit_diversity': HabitDiversityStrategy
    }
    
    @classmethod
    def register_strategy(cls, strategy_type: str, strategy_class: type) -> None:
        """Register a new strategy type"""
        if not issubclass(strategy_class, AchievementStrategy):
            raise ValueError(f"Strategy class must inherit from AchievementStrategy")
        cls._strategies[strategy_type] = strategy_class
    
    @classmethod
    def get_strategy(cls, strategy_type: str) -> AchievementStrategy:
        """Get an instance of the appropriate strategy"""
        strategy_class = cls._strategies.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown achievement strategy type: {strategy_type}")
        return strategy_class()