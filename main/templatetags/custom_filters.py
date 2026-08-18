from django import template
from django.utils.timesince import timesince

register = template.Library()

@register.filter
def short_timesince(value):
    if not value:
        return ""
    
    # Get the first unit and normalize non-breaking spaces
    raw_str = timesince(value).split(',')[0].replace('\xa0', ' ').strip()
    
    # Check if the duration starts with 0 (e.g. "0 minutes", "0 seconds")
    if raw_str.startswith('0'):
        return "Just now"
        
    return f"{raw_str} ago"