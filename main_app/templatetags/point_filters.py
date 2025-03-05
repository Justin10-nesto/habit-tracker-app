"""
Custom template filters for formatting point-related data.
"""

from django import template

register = template.Library()

@register.filter
def point_format(value):
    """Format point values with a + sign for positive values"""
    if value > 0:
        return f"+{value}"
    return str(value)

@register.filter
def transaction_type(value):
    """Convert transaction types to human-readable format"""
    type_mapping = {
        'COMPLETION': 'Habit Completion',
        'STREAK': 'Streak Milestone',
        'ACHIEVEMENT': 'Achievement',
        'BADGE': 'Badge',
        'BONUS': 'Bonus',
        'REDEMPTION': 'Redemption'
    }
    return type_mapping.get(value, value)

@register.filter
def modulo(value, arg):
    """Return the remainder when value is divided by arg"""
    try:
        return value % arg
    except (ValueError, TypeError):
        return 0
