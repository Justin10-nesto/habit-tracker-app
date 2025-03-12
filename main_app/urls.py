from django.urls import path
from .views import (
    # Auth views
    LoginView, RegisterView, LogoutView, PasswordResetView,
    
    # Main app views
    DashboardView, HabitListView, UserHabitListView, 
    HabitCompletionView, HabitCreateView,
    
    # Gamification views
    UserGamificationView, LeaderboardView, AchievementsView, BadgesView,
    
    # Admin views
    AdminDashboardView, AdminHabitsView, AdminCategoriesView,
    AdminMyHabitsView, AdminAnalyticsView, AdminSocialView,
    AdminAchievementsView, AdminSettingsView, ExportAnalyticsView,
    
    # Points views
    UserPointsView, TransactionsView, RewardsListView,
    RedeemRewardView, UserRedemptionsView,
)

urlpatterns = [
    # Auth URLs
    path('', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),

    # Admin panel URLs
    path('admin-panel/', AdminDashboardView.as_view(), name='dashboard'),
    path('admin-panel/habits/', AdminHabitsView.as_view(), name='admin_habits'),
    path('admin-panel/categories/', AdminCategoriesView.as_view(), name='admin_categories'),
    path('admin-panel/my-habits/', AdminMyHabitsView.as_view(), name='admin_my_habits'),
    path('admin-panel/analytics/', AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('admin-panel/analytics/export/', ExportAnalyticsView.as_view(), name='admin_analytics_export'),
    path('admin-panel/social/', AdminSocialView.as_view(), name='admin_social'),
    path('admin-panel/achievements/', AdminAchievementsView.as_view(), name='admin_achievements'),
    path('admin-panel/settings/', AdminSettingsView.as_view(), name='admin_settings'),
    
    # Points URLs
    path('points/', UserPointsView.as_view(), name='points'),
    path('points/transactions/', TransactionsView.as_view(), name='transactions'),
    path('points/rewards/', RewardsListView.as_view(), name='rewards'),
    path('points/redeem/<str:reward_id>/', RedeemRewardView.as_view(), name='redeem_reward'),
    path('points/redemptions/', UserRedemptionsView.as_view(), name='redemptions'),
    
]
