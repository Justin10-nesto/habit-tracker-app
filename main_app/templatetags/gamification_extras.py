from django import template

register = template.Library()

@register.filter
def modulo(value, arg):
    """Returns the remainder of dividing value by arg"""
    try:
        return int(value) % int(arg)
    except (ValueError, TypeError):
        return ""

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ""
