import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from main_app.models import UserHabit, HabitCompletion, MissedHabit, HabitStreak, Habit, User
from main_app.updater.scheduler import check_missed_habits

@pytest.mark.django_db
class TestHabitScheduler(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test habits with different periodicities
        self.daily_habit = Habit.objects.create(
            name='Daily Exercise',
            description='Exercise every day',
            periodicity='DAILY'
        )
        
        self.weekly_habit = Habit.objects.create(
            name='Weekly Review',
            description='Review goals weekly',
            periodicity='WEEKLY'
        )
        
        self.monthly_habit = Habit.objects.create(
            name='Monthly Planning',
            description='Plan for the month',
            periodicity='MONTHLY'
        )
        
        # Create UserHabit instances
        self.daily_user_habit = UserHabit.objects.create(
            user=self.user,
            habit=self.daily_habit,
            is_active=True,
            start_date=timezone.now().date() - timedelta(days=30)
        )
        
        self.weekly_user_habit = UserHabit.objects.create(
            user=self.user,
            habit=self.weekly_habit,
            is_active=True,
            start_date=timezone.now().date() - timedelta(days=30)
        )
        
        self.monthly_user_habit = UserHabit.objects.create(
            user=self.user,
            habit=self.monthly_habit,
            is_active=True,
            start_date=timezone.now().date() - timedelta(days=60)
        )
    
    def test_daily_habit_missed(self):
        """Test that daily habits are properly marked as missed"""
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Run the check
        check_missed_habits(start_date=yesterday)
        
        # Verify habit was marked as missed
        missed = MissedHabit.objects.filter(
            user_habit=self.daily_user_habit,
            missed_date=yesterday
        ).exists()
        
        self.assertTrue(missed)
    
    def test_daily_habit_completed(self):
        """Test that completed daily habits are not marked as missed"""
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Mark habit as completed
        HabitCompletion.objects.create(
            user_habit=self.daily_user_habit,
            completion_date=yesterday
        )
        
        # Run the check
        check_missed_habits(start_date=yesterday)
        
        # Verify habit was not marked as missed
        missed = MissedHabit.objects.filter(
            user_habit=self.daily_user_habit,
            missed_date=yesterday
        ).exists()
        
        self.assertFalse(missed)
    
    def test_weekly_habit_missed(self):
        """Test that weekly habits are properly marked as missed"""
        today = timezone.now().date()
        last_week_start = today - timedelta(days=today.weekday() + 7)
        last_week_end = last_week_start + timedelta(days=6)
        
        # Run the check
        check_missed_habits(start_date=last_week_start)
        
        # Verify habit was marked as missed
        missed = MissedHabit.objects.filter(
            user_habit=self.weekly_user_habit,
            missed_date=last_week_end
        ).exists()
        
        self.assertTrue(missed)
    
    def test_monthly_habit_missed(self):
        """Test that monthly habits are properly marked as missed"""
        today = timezone.now().date()
        last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_month_end = today.replace(day=1) - timedelta(days=1)
        
        # Run the check
        check_missed_habits(start_date=last_month_start)
        
        # Verify habit was marked as missed
        missed = MissedHabit.objects.filter(
            user_habit=self.monthly_user_habit,
            missed_date=last_month_end
        ).exists()
        
        self.assertTrue(missed)
    
    def test_streak_reset_on_miss(self):
        """Test that streaks are reset when habits are missed"""
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Set up a streak
        self.daily_user_habit.streak = 5
        self.daily_user_habit.save()
        
        # Run the check
        check_missed_habits(start_date=yesterday)
        
        # Refresh from database
        self.daily_user_habit.refresh_from_db()
        
        # Verify streak was reset
        self.assertEqual(self.daily_user_habit.streak, 0)
    
    def test_streak_history_created(self):
        """Test that streak history is recorded when streak is reset"""
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Set up a streak
        streak_length = 5
        self.daily_user_habit.streak = streak_length
        self.daily_user_habit.save()
        
        # Run the check
        check_missed_habits(start_date=yesterday)
        
        # Verify streak history was created
        streak_history = HabitStreak.objects.filter(
            user_habit=self.daily_user_habit,
            streak_length=streak_length
        ).first()
        
        self.assertIsNotNone(streak_history)
        self.assertEqual(streak_history.end_date, yesterday)
        self.assertEqual(streak_history.start_date, yesterday - timedelta(days=streak_length))
    
    def test_system_downtime_recovery(self):
        """Test that the system properly handles multiple missed days"""
        today = timezone.now().date()
        three_days_ago = today - timedelta(days=3)
        
        # Run the check with a start date from 3 days ago
        check_missed_habits(start_date=three_days_ago)
        
        # Verify all days were marked as missed
        missed_count = MissedHabit.objects.filter(
            user_habit=self.daily_user_habit,
            missed_date__gte=three_days_ago,
            missed_date__lt=today
        ).count()
        
        self.assertEqual(missed_count, 3)
    
    def test_inactive_habits_not_checked(self):
        """Test that inactive habits are not marked as missed"""
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Deactivate the habit
        self.daily_user_habit.is_active = False
        self.daily_user_habit.save()
        
        # Run the check
        check_missed_habits(start_date=yesterday)
        
        # Verify habit was not marked as missed
        missed = MissedHabit.objects.filter(
            user_habit=self.daily_user_habit,
            missed_date=yesterday
        ).exists()
        
        self.assertFalse(missed)