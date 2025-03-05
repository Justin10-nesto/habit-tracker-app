"""
Base models and utility functions for the Habit Tracker application.
"""

import uuid
from django.utils import timezone
import datetime

def get_uuid():
    """Generate a UUID string for model IDs"""
    return str(uuid.uuid4())

def get_current_date():
    """Get the current date"""
    return timezone.now().date()

def get_current_datetime():
    """Get the current datetime"""
    return timezone.now()
