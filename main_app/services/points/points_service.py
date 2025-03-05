"""
Points service singleton for managing user points.

This service provides methods for awarding, spending, and tracking points.
"""

import logging
from django.utils import timezone
from django.db.models import Sum
from ...models import UserPoints
from .point_strategies import PointCalculationFactory

logger = logging.getLogger(__name__)


class PointsService:
    """
    Singleton service for managing user points.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def award_points(self, user, strategy_name, description, reference_id=None, **kwargs):
        """
        Award points to a user using the specified strategy.
        
        Args:
            user: User to award points to
            strategy_name: Name of the strategy to use for point calculation
            description: Description of the point transaction
            reference_id: Optional ID of the related object (habit, badge, etc.)
            **kwargs: Additional parameters for the strategy
            
        Returns:
            tuple: (UserPoints object, PointTransaction object)
        """
        try:
            # Get the strategy
            strategy = PointCalculationFactory.get_strategy(strategy_name)
            
            # Calculate points
            points = strategy.calculate_points(**kwargs)
            
            if points <= 0:
                logger.info(f"No points awarded to {user.username} using {strategy_name} strategy")
                return None, None
                
            # Get or create user points
            user_points, _ = UserPoints.objects.get_or_create(user=user)
            
            # Add points using the UserPoints model method
            level_changed, transaction = user_points.add_points(
                points,
                strategy.get_transaction_type(),
                description,
                reference_id
            )
            
            # Handle level up events if needed
            if level_changed:
                logger.info(f"User {user.username} leveled up to {user_points.level}!")
                # You could trigger events or notifications here
                
            return user_points, transaction
            
        except Exception as e:
            logger.error(f"Error awarding points to {user.username}: {str(e)}")
            return None, None
    
    def spend_points(self, user, points, description, reference_id=None):
        """
        Spend points (subtract from user's total).
        
        Args:
            user: User spending points
            points: Number of points to spend
            description: Description of the transaction
            reference_id: Optional ID of the related object
            
        Returns:
            tuple: (UserPoints object, PointTransaction object, success boolean)
        """
        # Check that points is positive
        if points <= 0:
            logger.error(f"Cannot spend negative or zero points: {points}")
            return None, None, False
        
        # Get user points
        try:
            user_points = UserPoints.objects.get(user=user)
        except UserPoints.DoesNotExist:
            user_points = UserPoints.objects.create(user=user)
        
        # Check if user has enough points
        if user_points.total_points < points:
            logger.warning(f"User {user.username} doesn't have enough points to spend {points}")
            return user_points, None, False
        
        # Deduct points
        # Note: We're using the negative of points here since we're spending
        level_changed, transaction = user_points.add_points(
            -1 * points,
            'REDEMPTION',
            description,
            reference_id
        )
        
        return user_points, transaction, True
    
    def get_user_points(self, user):
        """
        Get the total points for a user.
        
        Args:
            user: User to get points for
            
        Returns:
            UserPoints object
        """
        user_points, _ = UserPoints.objects.get_or_create(user=user)
        return user_points
    
    def get_transactions(self, user, limit=None, transaction_type=None):
        """
        Get point transactions for a user.
        
        Args:
            user: User to get transactions for
            limit: Number of transactions to return (None for all)
            transaction_type: Type of transactions to filter by (None for all)
            
        Returns:
            QuerySet of PointTransaction objects
        """
        from ...models import PointTransaction
        
        transactions = PointTransaction.objects.filter(user=user)
        
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
            
        transactions = transactions.order_by('-timestamp')
        
        if limit:
            transactions = transactions[:limit]
            
        return transactions
    
    def get_points_summary(self, user):
        """
        Get a summary of points earned and spent by category.
        
        Args:
            user: User to get summary for
            
        Returns:
            dict: Summary information
        """
        from ...models import PointTransaction
        from django.db.models import Sum
        
        # Get total earned and spent by transaction type
        transactions = PointTransaction.objects.filter(user=user)
        
        earned_by_type = transactions.filter(
            amount__gt=0
        ).values('transaction_type').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        spent_by_type = transactions.filter(
            amount__lt=0
        ).values('transaction_type').annotate(
            total=Sum('amount')
        ).order_by('total')  # Ascending since these are negative
        
        # Calculate lifetime earnings and spending
        lifetime_earned = transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
        lifetime_spent = transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Format for template display
        earned_summary = [
            {
                'type': item['transaction_type'],
                'amount': item['total'],
                'percentage': (item['total'] / lifetime_earned * 100) if lifetime_earned > 0 else 0
            } for item in earned_by_type
        ]
        
        spent_summary = []
        if lifetime_spent < 0:  # Only if there are actually spent points
            spent_summary = [
                {
                    'type': item['transaction_type'],
                    'amount': abs(item['total']),  # Convert to positive for display
                    'percentage': (abs(item['total']) / abs(lifetime_spent) * 100)
                } for item in spent_by_type
            ]
        
        return {
            'earned': earned_summary,
            'spent': spent_summary,
            'lifetime_earned': lifetime_earned,
            'lifetime_spent': abs(lifetime_spent),  # Convert to positive for display
            'current_balance': lifetime_earned + lifetime_spent  # Since spent is already negative
        }
