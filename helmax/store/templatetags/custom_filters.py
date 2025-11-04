from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def currency(value):
    """Formats the value as currency."""
    try:
        return f'₹{float(value):.2f}'
    except (ValueError, TypeError):
        return value
        
@register.filter
def sub(value, arg):
    try:
        return value - arg
    except (ValueError, TypeError):
        return 0
        
@register.filter
def add(value, arg):
    try:
        return value + arg
    except (ValueError, TypeError):
        return value
        
@register.filter
def mul(value, arg):
    try:
        return value * arg
    except (ValueError, TypeError):
        return 0
        
@register.filter
def div(value, arg):
    try:
        return value / arg
    except (ValueError, TypeError, ZeroDivisionError):
        return 0