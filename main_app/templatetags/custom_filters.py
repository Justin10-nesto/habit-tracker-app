from django import template

register = template.Library()

@register.filter
def abs_value(value):
    """Returns the absolute value of a number"""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value

@register.filter
def map_achievement_status(achievement, user_achievements):
    """
    Check if the user has earned this achievement
    Returns dictionary with status and earned_date
    """
    for user_achievement in user_achievements:
        if user_achievement.achievement.id == achievement.id:
            return {
                'earned': True,
                'date': user_achievement.earned_date,
                'progress': 100
            }
    
    # Not earned yet
    return {
        'earned': False,
        'date': None,
        'progress': 0
    }

@register.filter
def map_badge_status(badge, user_badges):
    """
    Check if the user has earned this badge
    Returns dictionary with status and earned_date
    """
    for user_badge in user_badges:
        if user_badge.badge.id == badge.id:
            return {
                'earned': True,
                'date': user_badge.earned_date
            }
    
    # Not earned yet
    return {
        'earned': False,
        'date': None
    }
