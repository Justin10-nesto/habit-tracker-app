from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    return dictionary.get(key)

@register.filter
def get_attr(obj, attr):
    """Get an attribute from an object"""
    return getattr(obj, attr)

@register.filter
def divide(value, arg):
    """Divides the value by the argument"""
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return 0
    
@register.filter
def percent(value, arg):
    """Returns percentage of value to arg"""
    try:
        return int((float(value) / float(arg)) * 100)
    except (ValueError, ZeroDivisionError):
        return 0
