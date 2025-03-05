"""
Strategy Pattern implementation for point calculations.

This module provides different strategies for calculating user points
based on different actions in the system.
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class PointCalculationStrategy(ABC):
    """Abstract base class for point calculation strategies."""
    
    @abstractmethod
    def calculate_points(self, **kwargs):
        """Calculate points for a specific action"""
        pass
    
    @abstractmethod
    def get_transaction_type(self):
        """Return the transaction type string for this strategy"""
        pass


class HabitCompletionStrategy(PointCalculationStrategy):
    """Strategy for calculating points earned from habit completions."""
    
    def calculate_points(self, **kwargs):
        """
        Calculate points for completing a habit.
        
        Args:
            user_habit: UserHabit object that was completed
            streak: Current streak for this habit (optional)
            
        Returns:
            int: Points earned
        """
        user_habit = kwargs.get('user_habit')
        streak = kwargs.get('streak', 0)
        
        if not user_habit:
            logger.warning("No user_habit provided to HabitCompletionStrategy")
            return 0
            
        # Base points for completing any habit
        base_points = 10
        
        # Bonus points based on streak
        streak_bonus = 0
        if streak >= 7:
            # Calculate bonus: 5 points per week of streak, capped at 50 points
            streak_bonus = min(streak // 7 * 5, 50)
            
        # Bonus for habit difficulty level, if implemented
        difficulty_bonus = 0
        if hasattr(user_habit.habit, 'difficulty'):
            # Assume difficulty is a value from 1-5
            difficulty = getattr(user_habit.habit, 'difficulty', 1)
            difficulty_bonus = (difficulty - 1) * 2  # 0, 2, 4, 6, 8 bonus points
            
        total_points = base_points + streak_bonus + difficulty_bonus
        
        logger.info(f"Calculated {total_points} points for habit completion "
                    f"(base: {base_points}, streak bonus: {streak_bonus}, "
                    f"difficulty bonus: {difficulty_bonus})")
                    
        return total_points
    
    def get_transaction_type(self):
        return "COMPLETION"


class StreakMilestoneStrategy(PointCalculationStrategy):
    """Strategy for calculating points earned from streak milestones."""
    
    def calculate_points(self, **kwargs):
        """
        Calculate points for reaching a streak milestone.
        
        Args:
            streak: The streak milestone reached
            
        Returns:
            int: Points earned
        """
        streak = kwargs.get('streak', 0)
        
        # Points based on milestone tiers
        if streak >= 365:  # 1 year
            return 1000
        elif streak >= 180:  # 6 months
            return 500
        elif streak >= 90:  # 3 months
            return 250
        elif streak >= 30:  # 1 month
            return 100
        elif streak >= 14:  # 2 weeks
            return 50
        elif streak >= 7:   # 1 week
            return 25
        else:
            return 0
    
    def get_transaction_type(self):
        return "STREAK"


class AchievementStrategy(PointCalculationStrategy):
    """Strategy for calculating points earned from achievements."""
    
    def calculate_points(self, **kwargs):
        """
        Return the points defined on the achievement.
        
        Args:
            achievement: Achievement object that was earned
            
        Returns:
            int: Points earned
        """
        achievement = kwargs.get('achievement')
        if not achievement:
            logger.warning("No achievement provided to AchievementStrategy")
            return 0
            
        return getattr(achievement, 'points_awarded', 0)
    
    def get_transaction_type(self):
        return "ACHIEVEMENT"


class BadgeStrategy(PointCalculationStrategy):
    """Strategy for calculating points earned from badges."""
    
    def calculate_points(self, **kwargs):
        """
        Return the points defined on the badge.
        
        Args:
            badge: Badge object that was earned
            
        Returns:
            int: Points earned
        """
        badge = kwargs.get('badge')
        if not badge:
            logger.warning("No badge provided to BadgeStrategy")
            return 0
            
        return getattr(badge, 'points_awarded', 0)
    
    def get_transaction_type(self):
        return "BADGE"


class BonusPointsStrategy(PointCalculationStrategy):
    """Strategy for calculating bonus points."""
    
    def calculate_points(self, **kwargs):
        """
        Return the bonus points amount directly.
        
        Args:
            points: The amount of bonus points to award
            
        Returns:
            int: Points earned
        """
        return kwargs.get('points', 0)
    
    def get_transaction_type(self):
        return "BONUS"


class RedemptionStrategy(PointCalculationStrategy):
    """Strategy for calculating points spent on redemptions."""
    
    def calculate_points(self, **kwargs):
        """
        Calculate points for redemption (negative points).
        
        Args:
            reward: Reward object being redeemed
            
        Returns:
            int: Points spent (negative number)
        """
        reward = kwargs.get('reward')
        if not reward:
            logger.warning("No reward provided to RedemptionStrategy")
            return 0
            
        # Return negative points since this is a redemption
        return -1 * getattr(reward, 'points_required', 0)
    
    def get_transaction_type(self):
        return "REDEMPTION"


class PointCalculationFactory:
    """Factory class for creating point calculation strategies."""
    
    _strategies = {
        'completion': HabitCompletionStrategy,
        'streak': StreakMilestoneStrategy,
        'achievement': AchievementStrategy,
        'badge': BadgeStrategy,
        'bonus': BonusPointsStrategy,
        'redemption': RedemptionStrategy
    }
    
    @classmethod
    def get_strategy(cls, strategy_name):
        """
        Get the appropriate point calculation strategy.
        
        Args:
            strategy_name: String name of the strategy to use
            
        Returns:
            PointCalculationStrategy: The requested strategy
            
        Raises:
            ValueError: If the strategy name is invalid
        """
        strategy_class = cls._strategies.get(strategy_name.lower())
        
        if not strategy_class:
            raise ValueError(f"Unknown point calculation strategy: {strategy_name}")
            
        return strategy_class()
