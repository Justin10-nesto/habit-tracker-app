"""
Models package for Habit Tracker application.
Re-exports models for backward compatibility.
"""
from django.contrib.auth.models import User

# Common utilities
from .base import get_uuid, get_current_date, get_current_datetime

# User models
from .user_models import UserProfile, UserSession

# Habit models
from .habit_models import (
    Category, Habit, UserHabit, HabitCompletion,
    HabitStreak, Reminder, HabitHistory, MissedHabit
)

# Analytics models
from .analytics_models import HabitAnalytics

# Gamification models
from .gamification_models import (
    PointTransaction, UserPoints, Badge, UserBadge,
    Achievement, UserAchievement, LeaderboardEntry
)

# Redemption models
from .redemption_models import Reward, Redemption
