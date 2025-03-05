"""
Badge Service - Manages checking and awarding badges
Uses Singleton and Factory patterns.
"""
from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from django.db import transaction, models
from django.utils import timezone

from ...models import Badge, UserBadge
from ..points.points_service import PointsService
from ..events.event_system import EventSystem, EventTypes

class BadgeConditionChecker:
    """
    Base class for checking badge conditions
    Implements Chain of Responsibility pattern
    """
    def __init__(self, next_checker=None):
        self.next_checker = next_checker
    
    def set_next(self, checker):
        """Set the next checker in the chain"""
        self.next_checker = checker
        return checker
    
    def check(self, user: User, badge: Badge, **context) -> bool:
        """
        Check if badge conditions are met
        If this checker can't determine, pass to next checker
        """
        result = self.check_condition(user, badge, **context)
        
        # If we can determine the result, return it
        if result is not None:
            return result
        
        # Otherwise, pass to next checker if it exists
        if self.next_checker:
            return self.next_checker.check(user, badge, **context)
        
        # Default to False if no checkers remain
        return False
    
    def check_condition(self, user: User, badge: Badge, **context) -> Optional[bool]:
        """
        Check specific condition for this checker
        Return True/False if condition is met/not met
        Return None if this checker can't determine
        """
        return None


class AchievementCountBadgeChecker(BadgeConditionChecker):
    """Check if user has earned enough achievements"""
    
    def check_condition(self, user: User, badge: Badge, **context) -> Optional[bool]:
        # Check if this badge is based on achievement count
        if badge.badge_type != 'ACHIEVEMENT_COUNT':
            return None
        
        from ...models import UserAchievement
        achievement_count = UserAchievement.objects.filter(user=user).count()
        required_count = context.get('required_count', 5)
        
        return achievement_count >= required_count


class StreakBadgeChecker(BadgeConditionChecker):
    """Check if user has a streak of required length"""
    
    def check_condition(self, user: User, badge: Badge, **context) -> Optional[bool]:
        if badge.badge_type != 'STREAK':
            return None
        
        from ...models import UserHabit
        # Get the maximum streak across all habits
        max_streak = UserHabit.objects.filter(user=user).aggregate(models.Max('streak')).get('streak__max', 0) or 0
        required_streak = context.get('required_streak', 7)
        
        return max_streak >= required_streak


class BadgeService:
    """
    Service for checking and awarding badges
    Implements Singleton pattern
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BadgeService, cls).__new__(cls)
            cls._instance._points_service = PointsService()
            
            # Set up chain of responsibility for badge checking
            achievement_checker = AchievementCountBadgeChecker()
            streak_checker = StreakBadgeChecker()
            achievement_checker.set_next(streak_checker)
            
            cls._instance._checker_chain = achievement_checker
        return cls._instance
    
    def check_badges(self, user: User, event_type: str, **context) -> List[Badge]:
        """
        Check if user has earned any badges based on the event
        Returns a list of new badges awarded
        """
        # Get all badges the user doesn't already have
        user_badges = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
        available_badges = Badge.objects.exclude(id__in=user_badges)
        
        # List to store newly earned badges
        earned_badges = []
        
        for badge in available_badges:
            # Check badge conditions using chain of responsibility
            if self._checker_chain.check(user, badge, **context):
                # Award the badge
                self._award_badge(user, badge)
                earned_badges.append(badge)
        
        return earned_badges
    
    def _award_badge(self, user: User, badge: Badge) -> UserBadge:
        """Award a badge to a user and grant associated rewards"""
        try:
            with transaction.atomic():
                # Create user badge record
                user_badge = UserBadge.objects.create(
                    user=user,
                    badge=badge,
                    earned_date=timezone.now()
                )
                
                # Award points if applicable
                if badge.points_awarded > 0:
                    self._points_service.award_points(
                        user=user,
                        amount=badge.points_awarded,
                        transaction_type='BADGE',
                        description=f"Badge: {badge.name}",
                        reference_id=user_badge.id
                    )
                
                # Publish badge earned event
                EventSystem.publish(
                    EventTypes.BADGE_EARNED,
                    user=user,
                    badge=badge,
                    user_badge=user_badge
                )
                
                return user_badge
        except Exception as e:
            print(f"Error awarding badge {badge.id} to user {user.id}: {e}")
            raise
