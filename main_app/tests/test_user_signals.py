from django.test import TestCase
from django.contrib.auth.models import User
from main_app.models.user_models import UserProfile
from django.db.models.signals import post_save

class UserSignalsTest(TestCase):
    def test_profile_created_on_user_creation(self):
        """Test that UserProfile is automatically created when a User is created"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Check if a UserProfile was created for this user
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)
        
    def test_profile_creation_idempotent(self):
        """Test that signal handlers don't create duplicate profiles"""
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='password123'
        )
        
        # Initial profile should exist
        initial_profile = user.profile
        
        # Save the user again to trigger the signal
        user.save()
        
        # Get the current profile
        user.refresh_from_db()
        current_profile = user.profile
        
        # Check that it's the same profile (not a new one)
        self.assertEqual(initial_profile.id, current_profile.id)
        
        # Verify only one profile exists for this user
        profile_count = UserProfile.objects.filter(user=user).count()
        self.assertEqual(profile_count, 1)
        
    def test_profile_created_if_missing(self):
        """Test that a profile is created if it doesn't exist when saving a user"""
        user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='password123'
        )
        
        # Store the profile ID
        profile_id = user.profile.id
        
        # Delete the profile directly from the database to bypass signals
        UserProfile.objects.filter(user=user).delete()
        
        # Force refresh from database
        user = User.objects.get(pk=user.pk)
        
        # Since the signal likely recreates the profile when accessing user.profile
        # We'll check profile.id directly from database instead
        try:
            # This should fail if the profile doesn't exist
            profile = UserProfile.objects.get(user=user)
            # If we got here, a profile exists, but it should be a new one
            self.assertNotEqual(profile.id, profile_id, "Profile was not recreated")
        except UserProfile.DoesNotExist:
            # If we reach here, no profile exists. Save the user to trigger signal
            user.save()
            user = User.objects.get(pk=user.pk)
            # Now the profile should exist
            self.assertTrue(hasattr(user, 'profile'))
            self.assertIsInstance(user.profile, UserProfile)
            # And it should have a different ID than the original
            self.assertNotEqual(user.profile.id, profile_id, "Profile was not recreated")
