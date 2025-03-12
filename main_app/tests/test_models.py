import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from main_app.models import (
    UserPoints,
    User, UserProfile, Category, Habit, UserHabit,
    HabitCompletion, MissedHabit, HabitStreak, HabitAnalytics,
    Achievement, UserAchievement, PointTransaction
)
from main_app.models.base import get_uuid

@pytest.mark.django_db
class TestUserModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_creation(self):
        """Test that a user can be created with proper fields"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_profile_auto_creation(self):
        """Test that a UserProfile is automatically created with a new user"""
        self.assertIsNotNone(self.user.profile)
        self.assertIsInstance(self.user.profile, UserProfile)

@pytest.mark.django_db
class TestCategoryModel(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Health',
            description='Health related habits'
        )

    def test_category_creation(self):
        """Test that a category can be created with proper fields"""
        self.assertEqual(self.category.name, 'Health')
        self.assertEqual(self.category.description, 'Health related habits')

    def test_category_str_representation(self):
        """Test the string representation of a category"""
        self.assertEqual(str(self.category), 'Health')

@pytest.mark.django_db
class TestHabitModel(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Health')
        self.habit = Habit.objects.create(
            name='Daily Exercise',
            description='Exercise every day',
            periodicity='DAILY',
            category=self.category
        )

    def test_habit_creation(self):
        """Test that a habit can be created with proper fields"""
        self.assertEqual(self.habit.name, 'Daily Exercise')
        self.assertEqual(self.habit.description, 'Exercise every day')
        self.assertEqual(self.habit.periodicity, 'DAILY')
        self.assertEqual(self.habit.category, self.category)

    def test_habit_invalid_periodicity(self):
        """Test that a habit cannot be created with invalid periodicity"""
        with self.assertRaises(ValidationError):
            habit = Habit.objects.create(
                name='Invalid Habit',
                description='Test',
                periodicity='INVALID'
            )
            habit.full_clean()  # This will trigger validation

@pytest.mark.django_db
class TestUserHabitModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.habit = Habit.objects.create(
            name='Daily Exercise',
            description='Exercise every day',
            periodicity='DAILY'
        )
        self.user_habit = UserHabit.objects.create(
            user=self.user,
            habit=self.habit,
            is_active=True,
            start_date=timezone.now().date()
        )

    def test_user_habit_creation(self):
        """Test that a user habit can be created with proper fields"""
        self.assertEqual(self.user_habit.user, self.user)
        self.assertEqual(self.user_habit.habit, self.habit)
        self.assertTrue(self.user_habit.is_active)
        self.assertEqual(self.user_habit.streak, 0)

    def test_user_habit_streak_increment(self):
        """Test that streak can be incremented"""
        initial_streak = self.user_habit.streak
        self.user_habit.increment_streak()
        self.assertEqual(self.user_habit.streak, initial_streak + 1)

    def test_user_habit_streak_reset(self):
        """Test that streak can be reset"""
        self.user_habit.streak = 5
        self.user_habit.save()
        self.user_habit.reset_streak()
        self.assertEqual(self.user_habit.streak, 0)

@pytest.mark.django_db
class TestHabitCompletionModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.habit = Habit.objects.create(
            name='Daily Exercise',
            description='Exercise every day',
            periodicity='DAILY'
        )
        self.user_habit = UserHabit.objects.create(
            user=self.user,
            habit=self.habit,
            is_active=True,
            start_date=timezone.now().date()
        )

    def test_habit_completion_creation(self):
        """Test that a habit completion can be created"""
        completion = HabitCompletion.objects.create(
            user_habit=self.user_habit,
            completion_date=timezone.now().date()
        )
        self.assertEqual(completion.user_habit, self.user_habit)
        self.assertIsNotNone(completion.completion_date)

@pytest.mark.django_db
class TestHabitStreakModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.habit = Habit.objects.create(
            name='Daily Exercise',
            description='Exercise every day',
            periodicity='DAILY'
        )
        self.user_habit = UserHabit.objects.create(
            user=self.user,
            habit=self.habit,
            is_active=True,
            start_date=timezone.now().date()
        )

    def test_habit_streak_creation(self):
        """Test that a habit streak record can be created"""
        streak = HabitStreak.objects.create(
            user_habit=self.user_habit,
            streak_length=5,
            start_date=timezone.now().date() - timedelta(days=5),
            end_date=timezone.now().date()
        )
        self.assertEqual(streak.user_habit, self.user_habit)
        self.assertEqual(streak.streak_length, 5)

    def test_streak_date_validation(self):
        """Test that end_date cannot be before start_date"""
        with self.assertRaises(ValidationError):
            HabitStreak.objects.create(
                user_habit=self.user_habit,
                streak_length=5,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() - timedelta(days=1)
            )

@pytest.mark.django_db
class TestHabitAnalyticsModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.habit = Habit.objects.create(
            name='Daily Exercise',
            description='Exercise every day',
            periodicity='DAILY'
        )
        self.user_habit = UserHabit.objects.create(
            user=self.user,
            habit=self.habit,
            is_active=True,
            start_date=timezone.now().date() - timedelta(days=30)
        )

    def test_analytics_creation(self):
        """Test that analytics can be created for a habit"""
        analytics = HabitAnalytics.objects.create(
            user=self.user,
            habit=self.habit,
            longest_streak=10,
            missed_count=5,
            completion_rate=75.0
        )
        self.assertEqual(analytics.user, self.user)
        self.assertEqual(analytics.habit, self.habit)
        self.assertEqual(analytics.longest_streak, 10)
        self.assertEqual(analytics.missed_count, 5)
        self.assertEqual(analytics.completion_rate, 75.0)

    def test_analytics_calculation(self):
        """Test that analytics can be calculated correctly"""
        analytics = HabitAnalytics.objects.create(
            user=self.user,
            habit=self.habit
        )
        
        # Create some completions
        for i in range(5):
            HabitCompletion.objects.create(
                user_habit=self.user_habit,
                completion_date=timezone.now().date() - timedelta(days=i)
            )
        
        # Create some missed records
        for i in range(5, 8):
            MissedHabit.objects.create(
                user_habit=self.user_habit,
                missed_date=timezone.now().date() - timedelta(days=i)
            )
        
        analytics.calculate_analytics()
        
        self.assertGreater(analytics.completion_rate, 0)
        self.assertEqual(analytics.missed_count, 3)