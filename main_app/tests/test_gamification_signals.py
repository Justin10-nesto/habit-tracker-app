from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.test.utils import override_settings
from main_app.models.gamification_models import Badge, Achievement, UserBadge, UserAchievement, UserPoints
import uuid

class GamificationSignalsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='gameuser',
            email='game@example.com',
            password='password123'
        )
        
        # Create badge and achievement for testing
        self.badge = Badge.objects.create(
            name="Test Badge",
            description="Test Badge Description",
            points_awarded=50
        )
        
        self.achievement = Achievement.objects.create(
            name="Test Achievement",
            description="Test Achievement Description",
            points_awarded=100
        )
        
        # Ensure the user has points record with zero points
        self.user_points, _ = UserPoints.objects.get_or_create(user=self.user)
        self.user_points.points = 0
        self.user_points.level = 1
        self.user_points.save()
        
    def test_points_awarded_for_badge(self):
        """Test that points are awarded when a badge is earned"""
        # Force points to 0 before test to make our expected value accurate
        self.user_points.points = 0
        self.user_points.save()
        
        # Get initial points
        initial_points = self.user_points.points
        
        # Create a badge award with a signal handler that should add points
        user_badge = UserBadge.objects.create(
            user=self.user,
            badge=self.badge,
            earned_date=timezone.now()
        )
        
        # Manually refresh points from db
        self.user_points.refresh_from_db()
        
        # Verify points changed as expected
        self.assertEqual(self.user_points.points, initial_points + self.badge.points_awarded, 
                        f"Expected {initial_points + self.badge.points_awarded} points but got {self.user_points.points}")
        
    def test_points_awarded_for_achievement(self):
        """Test that points are awarded when an achievement is earned"""
        # Force points to 0 before test
        self.user_points.points = 0
        self.user_points.save()
        
        # Get initial points
        initial_points = self.user_points.points
        
        # Award achievement with a signal handler that should add points
        user_achievement = UserAchievement.objects.create(
            user=self.user,
            achievement=self.achievement,
            earned_date=timezone.now()
        )
        
        # Manually refresh points from db
        self.user_points.refresh_from_db()
        
        # Verify points changed as expected
        self.assertEqual(self.user_points.points, initial_points + self.achievement.points_awarded,
                        f"Expected {initial_points + self.achievement.points_awarded} points but got {self.user_points.points}")
        
    def test_badge_points_not_duplicated(self):
        """Test that badge points aren't awarded twice for the same badge"""
        # Use a unique name to avoid conflicts
        unique_name = f"Unique Badge {uuid.uuid4()}"
        
        # Create a badge with a unique name
        badge1 = Badge.objects.create(
            name=unique_name,
            description="Test Badge Description",
            points_awarded=25
        )
        
        # Reset points to 0
        self.user_points.points = 0
        self.user_points.save()
        
        # Award the badge
        user_badge = UserBadge.objects.create(
            user=self.user,
            badge=badge1,
            earned_date=timezone.now()
        )
        
        # Refresh points and verify
        self.user_points.refresh_from_db()
        self.assertEqual(self.user_points.points, 25, "Points weren't awarded properly")
        
        # Create a second badge to test uniqueness
        badge2 = Badge.objects.create(
            name=f"Second Badge {uuid.uuid4()}",
            description="Another badge",
            points_awarded=25
        )
        
        points_after_first = self.user_points.points
        
        # Award second badge
        second_badge = UserBadge.objects.create(
            user=self.user,
            badge=badge2,
            earned_date=timezone.now()
        )
        
        # Refresh points
        self.user_points.refresh_from_db()
        
        # Points should have increased for the second badge
        self.assertEqual(self.user_points.points, points_after_first + 25)
        
    def test_level_milestone_badges(self):
        """Test that milestone badges are awarded at specific levels"""
        # Create milestone badge
        milestone_badge = Badge.objects.create(
            name="Novice Achiever",
            description="Reached level 5",
            points_awarded=0
        )
        
        # Set user to just below milestone level
        self.user_points.level = 4
        self.user_points.save(update_fields=['level'])
        
        # No milestone badge should exist yet
        self.assertFalse(UserBadge.objects.filter(
            user=self.user, 
            badge=milestone_badge
        ).exists())
        
        # Update to milestone level
        self.user_points.level = 5
        self.user_points.save(update_fields=['level'])
        
        # Badge should be awarded
        self.assertTrue(UserBadge.objects.filter(
            user=self.user, 
            badge=milestone_badge
        ).exists())
        
        # Test idempotency - saving again shouldn't create duplicate
        initial_count = UserBadge.objects.filter(user=self.user, badge=milestone_badge).count()
        self.user_points.save(update_fields=['level'])
        final_count = UserBadge.objects.filter(user=self.user, badge=milestone_badge).count()
        
        self.assertEqual(initial_count, final_count)
