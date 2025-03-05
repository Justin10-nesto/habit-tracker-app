from django.contrib import admin
from .models import (
    MissedHabit, UserProfile, Category, Habit, UserHabit, 
    HabitCompletion, HabitStreak, Reminder,
    HabitAnalytics, HabitHistory,
    # Gamification models
    PointTransaction, UserPoints, Badge, UserBadge,
    Achievement, UserAchievement, LeaderboardEntry
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'gender', 'date_of_birth']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name',  'created_at']
    search_fields = ['name']

@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ['name', 'periodicity', 'category', 'created_at']
    list_filter = ['periodicity', 'category']
    search_fields = ['name', 'description']

@admin.register(UserHabit)
class UserHabitAdmin(admin.ModelAdmin):
    list_display = ['user', 'habit', 'streak', 'is_active', 'start_date', 'last_completed']
    list_filter = ['is_active']
    search_fields = ['user__username', 'habit__name']

@admin.register(HabitCompletion)
class HabitCompletionAdmin(admin.ModelAdmin):
    list_display = ['user_habit', 'completion_date', 'timestamp']
    list_filter = ['completion_date']
    date_hierarchy = 'completion_date'

@admin.register(HabitStreak)
class HabitStreakAdmin(admin.ModelAdmin):
    list_display = ['user_habit', 'streak_length', 'start_date', 'end_date']
    list_filter = ['start_date']

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['user_habit', 'reminder_time', 'reminder_date']
    list_filter = ['reminder_time']

@admin.register(HabitAnalytics)
class HabitAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'habit', 'longest_streak', 'missed_count']

@admin.register(HabitHistory)
class HabitHistoryAdmin(admin.ModelAdmin):
    list_display = ['user_habit', 'completion_date']
    list_filter = ['completion_date']
    date_hierarchy = 'completion_date'

# Gamification admin models
@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'transaction_type', 'description', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['user__username', 'description']
    date_hierarchy = 'timestamp'

@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_points', 'level']
    search_fields = ['user__username']
    list_filter = ['level']

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_type', 'points_awarded']
    list_filter = ['badge_type']
    search_fields = ['name', 'description']

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'earned_date']
    list_filter = ['badge', 'earned_date']
    search_fields = ['user__username', 'badge__name']
    date_hierarchy = 'earned_date'

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_awarded']
    search_fields = ['name', 'description']

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_date']
    list_filter = ['achievement', 'earned_date']
    search_fields = ['user__username', 'achievement__name']
    date_hierarchy = 'earned_date'

@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'period_type', 'period_start', 'period_end', 'points', 'rank']
    list_filter = ['period_type', 'period_start']
    search_fields = ['user__username']

@admin.register(MissedHabit)
class MissedHabitAdmin(admin.ModelAdmin):
    list_display = ['user_habit', 'missed_date', 'created_at']
    list_filter = ['missed_date']
    date_hierarchy = 'missed_date'
    search_fields = ['user_habit__user__username', 'user_habit__habit__name']
