"""
Signal handlers for gamification-related models.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib import messages
from django.utils import timezone

from ..models.gamification_models import (
    UserBadge, UserAchievement, UserPoints
)


@receiver(post_save, sender=UserBadge)
def award_badge_points(sender, instance, created, **kwargs):
    """Award points when a user earns a badge"""
    if created and instance.badge.points_awarded > 0:
        try:
            user_points, _ = UserPoints.objects.get_or_create(user=instance.user)
            level_changed, _ = user_points.add_points(
                instance.badge.points_awarded,
                'BADGE',
                f"Earned badge: {instance.badge.name}",
                reference_id=str(instance.badge.id)
            )
            
            # Handle level up notification (could send email, in-app notification, etc.)
            if level_changed:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"User {instance.user.username} leveled up to {user_points.level}!")

        except Exception as e:
            # Log error but don't stop execution
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error awarding points for badge: {e}")


@receiver(post_save, sender=UserAchievement)
def award_achievement_points(sender, instance, created, **kwargs):
    """Award points when a user earns an achievement"""
    if created and instance.achievement.points_awarded > 0:
        try:
            user_points, _ = UserPoints.objects.get_or_create(user=instance.user)
            level_changed, _ = user_points.add_points(
                instance.achievement.points_awarded,
                'ACHIEVEMENT',
                f"Unlocked achievement: {instance.achievement.name}",
                reference_id=str(instance.achievement.id)
            )
            
            # Handle level up notification
            if level_changed:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"User {instance.user.username} leveled up to {user_points.level}!")
                
        except Exception as e:
            # Log error but don't stop execution
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error awarding points for achievement: {e}")


@receiver(post_save, sender=UserPoints)
def check_level_milestones(sender, instance, **kwargs):
    """
    Check for level milestones and award special badges
    This runs when UserPoints are updated
    """
    # Check for changes in level
    if 'update_fields' in kwargs and kwargs['update_fields'] and 'level' in kwargs['update_fields']:
        current_level = instance.level
        
        # Award level badges at milestone levels
        milestone_levels = {
            5: "Novice Achiever",
            10: "Habit Enthusiast",
            25: "Habit Master", 
            50: "Habit Champion",
            100: "Habit Legend"
        }
        
        if current_level in milestone_levels:
            badge_name = milestone_levels[current_level]
            
            # Import here to avoid circular imports
            from ..models.gamification_models import Badge, UserBadge
            
            try:
                # Try to find the badge
                badge = Badge.objects.get(name=badge_name)
                
                # Award the badge if it exists and user doesn't have it yet
                UserBadge.objects.get_or_create(
                    user=instance.user,
                    badge=badge,
                    defaults={'earned_date': timezone.now()}
                )
                
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"User {instance.user.username} earned the {badge_name} badge!")
                
            except Badge.DoesNotExist:
                # Badge doesn't exist in system
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Badge {badge_name} not found in system.")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error awarding level badge: {e}")
