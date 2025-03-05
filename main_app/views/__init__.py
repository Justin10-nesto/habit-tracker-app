"""
Views package for the habit tracker application.
This file exports all views from the package modules to maintain backward compatibility.
"""

# Export auth views
from .auth_views import (
    LoginView, RegisterView, LogoutView, PasswordResetView,
    BaseAuthView, LoginStrategy, RegisterStrategy
)

# Export dashboard views
from .dashboard_views import DashboardView

# Export habit views
from .habit_views import (
    HabitListView, UserHabitListView, HabitCompletionView, HabitCreateView
)

# Export gamification views
from .gamification_views import (
    UserGamificationView, LeaderboardView, AchievementsView, BadgesView
)

# Export admin views
from .admin_views import AdminViewMixin, AdminDashboardView
from .admin_habit_views import AdminHabitsView, AdminCategoriesView, AdminMyHabitsView
from .admin_analytics_views import AdminAnalyticsView, ExportAnalyticsView
from .admin_social_views import AdminSocialView
from .admin_achievement_views import AdminAchievementsView
from .admin_settings_views import AdminSettingsView

# Export points views
from .points_views import (
    UserPointsView, TransactionsView, RewardsListView,
    RedeemRewardView, UserRedemptionsView
)
