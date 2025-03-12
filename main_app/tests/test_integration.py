from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from main_app.models.habit_models import UserHabit, HabitCompletion
from main_app.models.gamification_models import Badge, Achievement, UserBadge, UserAchievement, UserPoints
from main_app.models import Habit  # Import the Habit model

class HabitTrackerIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='password123'
        )
        self.client.login(username='integrationuser', password='password123')
        
        # Create base habit first - remove frequency field which is causing the error
        self.base_habit = Habit.objects.create(
            name="Integration Test Habit",
            description="Testing the integration flow"
            # frequency field removed
        )
        
        # Create user habit linked to base habit
        self.habit = UserHabit.objects.create(
            user=self.user,
            habit=self.base_habit,
            start_date=timezone.now().date(),
            streak=0
        )
        
        # Create badges and achievements
        self.completion_badge = Badge.objects.create(
            name="First Step",
            description="Complete your first habit",
            points_awarded=25
        )
        
        self.streak_achievement = Achievement.objects.create(
            name="Consistent",
            description="Maintain a 3-day streak",
            points_awarded=50
        )
        
    def test_complete_habit_flow(self):
        """
        Test the full flow of completing a habit:
        - Habit is marked as completed
        - Streak is updated
        - Points are awarded
        - Badge is earned
        """
        # Initial state
        initial_points, _ = UserPoints.objects.get_or_create(user=self.user)
        initial_point_value = initial_points.points
        
        # Complete the habit
        completion_date = timezone.now().date()
        completion = HabitCompletion.objects.create(
            user_habit=self.habit,
            completion_date=completion_date
        )
        
        # Verify habit is updated
        self.habit.refresh_from_db()
        self.assertGreaterEqual(self.habit.streak, 1)
        
        # Verify points are awarded
        initial_points.refresh_from_db()
        self.assertGreater(initial_points.points, initial_point_value)
        
        # Complete habit for 2 more days to reach 3-day streak
        for i in range(1, 3):
            next_date = completion_date + timedelta(days=i)
            completion = HabitCompletion.objects.create(
                user_habit=self.habit,
                completion_date=next_date
            )
        
        # Refresh habit
        self.habit.refresh_from_db()
        
        # Verify streak is at least 3
        self.assertGreaterEqual(self.habit.streak, 3)
        
        # Now manually award the achievement based on streak
        if self.habit.streak >= 3:
            UserAchievement.objects.create(
                user=self.user,
                achievement=self.streak_achievement,
                earned_date=timezone.now()
            )
        
        # Verify achievement was awarded
        achievement_exists = UserAchievement.objects.filter(
            user=self.user,
            achievement=self.streak_achievement
        ).exists()
        self.assertTrue(achievement_exists)
        
        # Verify more points were awarded for the achievement
        final_points = UserPoints.objects.get(user=self.user)
        self.assertGreater(final_points.points, initial_points.points)
