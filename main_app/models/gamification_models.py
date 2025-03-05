"""
Gamification models for the Habit Tracker application.
"""

from django.db import models
from django.contrib.auth.models import User
from .base import get_uuid, get_current_datetime


class PointTransaction(models.Model):
    """Records points earned by users for various activities"""
    TRANSACTION_TYPES = [
        ('COMPLETION', 'Habit Completion'),
        ('STREAK', 'Streak Milestone'),
        ('ACHIEVEMENT', 'Achievement Unlocked'),
        ('BADGE', 'Badge Earned'),
        ('BONUS', 'Bonus Points'),
    ]
    
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=get_current_datetime)
    reference_id = models.CharField(max_length=36, blank=True, null=True)  # Can link to habit, streak, etc.
    
    def __str__(self):
        return f"{self.user.username}: {self.amount} points ({self.get_transaction_type_display()})"


class UserPoints(models.Model):
    """Tracks total points for a user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points')
    total_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    class Meta:
        verbose_name_plural = "User points"
    
    def __str__(self):
        return f"{self.user.username}: {self.total_points} points (Level {self.level})"
    
    def add_points(self, amount, transaction_type, description, reference_id=None):
        """Add points to user and create transaction record"""
        self.total_points += amount
        # Check if user should level up
        new_level = self.calculate_level()
        level_changed = new_level > self.level
        self.level = new_level
        self.save()
        
        # Create transaction record
        transaction = PointTransaction.objects.create(
            user=self.user,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id
        )
        
        return level_changed, transaction
    
    def calculate_level(self):
        """Calculate user level based on points"""
        # Simple level formula: level = 1 + points/1000
        # You can replace with more complex formulas
        return 1 + (self.total_points // 1000)


class Badge(models.Model):
    """Badge definitions"""
    BADGE_TYPES = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
        ('SPECIAL', 'Special'),
    ]
    
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100, help_text="CSS class or image path for the badge icon")
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    points_awarded = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.get_badge_type_display()})"


class UserBadge(models.Model):
    """Tracks badges earned by users"""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='users')
    earned_date = models.DateTimeField(default=get_current_datetime)
    
    class Meta:
        unique_together = ['user', 'badge']
    
    def __str__(self):
        return f"{self.user.username} earned {self.badge.name}"


class Achievement(models.Model):
    """Achievement definitions"""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100, help_text="CSS class or image path for the achievement icon")
    points_awarded = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Tracks achievements earned by users"""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='users')
    earned_date = models.DateTimeField(default=get_current_datetime)
    
    class Meta:
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f"{self.user.username} earned {self.achievement.name}"


class LeaderboardEntry(models.Model):
    """Leaderboard entries"""
    PERIOD_TYPES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('ALL_TIME', 'All Time'),
    ]
    
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    points = models.IntegerField(default=0)
    rank = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'period_type', 'period_start']
        verbose_name_plural = "Leaderboard entries"
    
    def __str__(self):
        return f"{self.user.username} - {self.points} points ({self.get_period_type_display()})"
