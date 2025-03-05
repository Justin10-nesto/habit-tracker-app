"""
Services package for the Habit Tracker application.
"""

# Initialize the services package

# Import main services for convenience
from .points.points_service import PointsService
from .notification_service import NotificationService
from .achievements import AchievementService
from .events import EventSystem, EventTypes
