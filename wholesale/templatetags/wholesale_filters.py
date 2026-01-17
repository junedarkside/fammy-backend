"""
Custom template filters for wholesale app.
"""

from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """
    Get a value from a dictionary using a key.

    Usage: {{ mydict|dict_get:"key" }}
    """
    if d is None:
        return None
    return d.get(key)
