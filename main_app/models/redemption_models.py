"""
Models related to point redemption and rewards.
"""

from django.db import models
from django.contrib.auth.models import User
from .base import get_uuid, get_current_datetime


class Reward(models.Model):
    """Reward that can be redeemed with points."""
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.PositiveIntegerField()
    image = models.ImageField(upload_to='rewards/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=get_current_datetime)
    stock = models.PositiveIntegerField(default=0)  # 0 = unlimited
    
    def __str__(self):
        return f"{self.name} ({self.points_required} points)"


class Redemption(models.Model):
    """Record of a user redeeming a reward."""
    REDEMPTION_STATUS = [
        ('PENDING', 'Pending'),
        ('FULFILLED', 'Fulfilled'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    id = models.CharField(primary_key=True, max_length=36, default=get_uuid)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redemptions')
    reward = models.ForeignKey(Reward, on_delete=models.PROTECT, related_name='redemptions')
    points_spent = models.PositiveIntegerField()
    redeemed_at = models.DateTimeField(default=get_current_datetime)
    status = models.CharField(max_length=20, choices=REDEMPTION_STATUS, default='PENDING')
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    transaction = models.ForeignKey(
        'PointTransaction', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='redemptions'
    )
    
    def __str__(self):
        return f"{self.user.username} redeemed {self.reward.name}"
