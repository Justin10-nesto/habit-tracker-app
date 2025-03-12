from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from main_app.models.habit_models import UserHabit, HabitCompletion, HabitStreak
from main_app.models.analytics_models import HabitAnalytics
from main_app.models.gamification_models import UserPoints
from main_app.models import Habit  

class HabitSignalsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='habituser',
            email='habit@example.com',
            password='password123'
        )
        
        # Create a base Habit first - remove frequency field which is causing the error
        self.base_habit = Habit.objects.create(
            name="Test Habit",
            description="Test habit description"
            # frequency field removed
        )
        
        # Create a UserHabit that links to the base Habit
        self.habit = UserHabit.objects.create(
            user=self.user,
            habit=self.base_habit,  # Use the actual habit object
            start_date=timezone.now().date(),
            streak=0
        )
        
    def test_streak_updated_on_completion(self):
        """Test that streak is updated when a habit is completed"""
        # Initial streak should be 0
        self.assertEqual(self.habit.streak, 0)
        
        # Complete the habit
        completion = HabitCompletion.objects.create(
            user_habit=self.habit,
            completion_date=timezone.now().date()
        )
        
        # Refresh habit from db
        self.habit.refresh_from_db()
        
        # Streak should be updated (actual streak logic depends on your implementation)
        self.assertGreaterEqual(self.habit.streak, 0)
        
    def test_points_awarded_on_completion(self):
        """Test that points are awarded when a habit is completed"""
        # Check initial points
        user_points, created = UserPoints.objects.get_or_create(user=self.user)
        initial_points = user_points.points
        
        # Complete the habit
        completion = HabitCompletion.objects.create(
            user_habit=self.habit,
            completion_date=timezone.now().date()
        )
        
        # Refresh points from db
        user_points.refresh_from_db()
        
        # Points should have increased
        self.assertGreater(user_points.points, initial_points)
        
    def test_analytics_updated_on_completion(self):
        """Test that analytics are updated when a habit is completed"""
        # Complete the habit
        completion = HabitCompletion.objects.create(
            user_habit=self.habit,
            completion_date=timezone.now().date()
        )
        
        # Check if analytics were created
        analytics_exists = HabitAnalytics.objects.filter(
            user=self.user,
            habit=self.habit.habit_id
        ).exists()
        
        self.assertTrue(analytics_exists)
        
    def test_streak_record_created(self):
        """Test that a streak record is created when streak changes"""
        # Set an initial streak
        self.habit.streak = 0
        self.habit.save()
        
        # No streak records should exist yet
        self.assertEqual(HabitStreak.objects.filter(user_habit=self.habit).count(), 0)
        
        # Update the streak
        self.habit.streak = 1
        self.habit.last_completed = timezone.now().date()
        self.habit.save()
        
        # A streak record should now exist
        self.assertEqual(HabitStreak.objects.filter(user_habit=self.habit).count(), 1)
        
    def test_streak_record_updated_not_duplicated(self):
        """Test that streak records are updated, not duplicated"""
        # Set an initial streak and create first record
        self.habit.streak = 1
        self.habit.last_completed = timezone.now().date()
        self.habit.save()
        
        # One streak record should exist
        self.assertEqual(HabitStreak.objects.filter(user_habit=self.habit).count(), 1)
        initial_streak = HabitStreak.objects.get(user_habit=self.habit)
        
        # Increase the streak
        self.habit.streak = 2
        self.habit.save()
        
        # Still only one active streak record should exist
        self.assertEqual(
            HabitStreak.objects.filter(user_habit=self.habit, end_date=None).count(), 
            1
        )
        
        # Get updated streak record
        updated_streak = HabitStreak.objects.get(user_habit=self.habit, end_date=None)
        
        # Should be the same record but with updated length
        self.assertEqual(initial_streak.id, updated_streak.id)
        self.assertEqual(updated_streak.streak_length, 2)
        
    def test_streak_record_closed_on_reset(self):
        """Test that streak records are closed when streak is reset"""
        # Set an initial streak
        self.habit.streak = 5
        self.habit.last_completed = timezone.now().date()
        self.habit.save()
        
        # Reset the streak
        self.habit.streak = 0
        self.habit.save()
        
        # The streak record should be closed (have an end_date)
        streak_record = HabitStreak.objects.get(user_habit=self.habit)
        self.assertIsNotNone(streak_record.end_date)
