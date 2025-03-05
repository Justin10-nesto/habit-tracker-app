"""Achievement Events - Handles achievement-related events and integrates with the event system"""
from typing import Dict, Any
from django.contrib.auth.models import User
from ..events.event_system import EventSystem, EventTypes, Event
from .achievement_strategies import AchievementStrategyFactory
from ...models import Achievement, UserAchievement

class AchievementEventHandler:
    """Handles achievement-related events and manages achievement unlocking"""
    
    def __init__(self):
        self.event_system = EventSystem()
        self._register_event_handlers()
    
    def _register_event_handlers(self) -> None:
        """Register handlers for achievement-related events"""
        self.event_system.subscribe(EventTypes.HABIT_COMPLETED, self._handle_habit_completion)
        self.event_system.subscribe(EventTypes.STREAK_UPDATED, self._handle_streak_update)
    
    def _handle_habit_completion(self, event: Event) -> None:
        """Handle habit completion events
        
        Args:
            event: The habit completion event
        """
        user: User = event.data.get('user')
        habit_type: str = event.data.get('habit_type')
        
        if user:
            self._check_completion_achievements(user, habit_type)
    
    def _handle_streak_update(self, event: Event) -> None:
        """Handle streak update events
        
        Args:
            event: The streak update event
        """
        user: User = event.data.get('user')
        habit_type: str = event.data.get('habit_type')
        streak: int = event.data.get('streak', 0)
        
        if user:
            self._check_streak_achievements(user, habit_type, streak)
    
    def _check_completion_achievements(self, user: User, habit_type: str = None) -> None:
        """Check and award completion-based achievements
        
        Args:
            user: The user to check achievements for
            habit_type: Optional habit type to filter achievements
        """
        achievements = Achievement.objects.filter(strategy_type='habit_completion_count')
        
        for achievement in achievements:
            strategy = AchievementStrategyFactory.get_strategy(achievement.strategy_type)
            context = {
                'required_count': achievement.criteria.get('required_count', 0),
                'habit_type': habit_type
            }
            
            if strategy.check_achievement(user, achievement, **context):
                self._unlock_achievement(user, achievement)
    
    def _check_streak_achievements(self, user: User, habit_type: str, streak: int) -> None:
        """Check and award streak-based achievements
        
        Args:
            user: The user to check achievements for
            habit_type: The type of habit the streak is for
            streak: The current streak value
        """
        achievements = Achievement.objects.filter(strategy_type='streak')
        
        for achievement in achievements:
            strategy = AchievementStrategyFactory.get_strategy(achievement.strategy_type)
            context = {
                'required_streak': achievement.criteria.get('required_streak', 0),
                'habit_type': habit_type
            }
            
            if strategy.check_achievement(user, achievement, **context):
                self._unlock_achievement(user, achievement)
    
    def _unlock_achievement(self, user: User, achievement: Achievement) -> None:
        """Unlock an achievement for a user
        
        Args:
            user: The user to unlock the achievement for
            achievement: The achievement to unlock
        """
        # Check if already unlocked
        if not UserAchievement.objects.filter(user=user, achievement=achievement).exists():
            # Create user achievement
            UserAchievement.objects.create(user=user, achievement=achievement)
            
            # Dispatch achievement unlocked event
            self.event_system.dispatch_event(
                EventTypes.ACHIEVEMENT_UNLOCKED,
                {
                    'user': user,
                    'achievement': achievement,
                    'achievement_name': achievement.name,
                    'achievement_description': achievement.description
                }
            )