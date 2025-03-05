"""
Views for user points, transactions, and rewards.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator

from .base_view import BaseContextMixin
from ..services.points import PointsService
from ..models import UserPoints, PointTransaction, Reward, Redemption


class UserPointsView(LoginRequiredMixin, BaseContextMixin, View):
    """View for displaying user points summary."""
    login_url = 'login'
    active_page = 'points'
    
    def get(self, request):
        # Get points service
        points_service = PointsService()
        
        # Get user's points information
        user_points = points_service.get_user_points(request.user)
        
        # Get points summary
        summary = points_service.get_points_summary(request.user)
        
        # Get recent transactions
        recent_transactions = points_service.get_transactions(request.user, limit=5)
        
        context = self.get_context_data(
            user_points=user_points,
            summary=summary,
            recent_transactions=recent_transactions,
            next_level=user_points.level + 1,
            next_level_points=user_points.level * 1000,
            progress_to_next_level=((user_points.total_points % 1000) / 1000) * 100
        )
        
        return render(request, 'admin/points.html', context)


class TransactionsView(LoginRequiredMixin, BaseContextMixin, View):
    """View for displaying user point transactions."""
    login_url = 'login'
    active_page = 'transactions'
    
    def get(self, request):
        # Get filter parameters
        transaction_type = request.GET.get('type', '')
        
        # Get points service
        points_service = PointsService()
        
        # Get filtered transactions
        if transaction_type and transaction_type != 'ALL':
            transactions = points_service.get_transactions(
                request.user, 
                transaction_type=transaction_type
            )
        else:
            transactions = points_service.get_transactions(request.user)
        
        # Paginate transactions
        paginator = Paginator(transactions, 20)  # 20 transactions per page
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Get transaction types for filter dropdown
        transaction_types = PointTransaction.objects.filter(
            user=request.user
        ).values_list('transaction_type', flat=True).distinct()
        
        context = self.get_context_data(
            page_obj=page_obj,
            transaction_types=transaction_types,
            selected_type=transaction_type
        )
        
        return render(request, 'admin/transactions.html', context)


class RewardsListView(LoginRequiredMixin, BaseContextMixin, View):
    """View for displaying available rewards."""
    login_url = 'login'
    active_page = 'rewards'
    
    def get(self, request):
        # Get points service
        points_service = PointsService()
        
        # Get user's current points
        user_points = points_service.get_user_points(request.user)
        
        # Get available rewards
        available_rewards = Reward.objects.filter(is_active=True)
        
        # Add flag for each reward to indicate if user can afford it
        rewards_with_availability = []
        for reward in available_rewards:
            rewards_with_availability.append({
                'reward': reward,
                'can_afford': user_points.total_points >= reward.points_required,
                'points_needed': max(0, reward.points_required - user_points.total_points)
            })
        
        context = self.get_context_data(
            user_points=user_points,
            rewards=rewards_with_availability
        )
        
        return render(request, 'admin/rewards.html', context)


class RedeemRewardView(LoginRequiredMixin, BaseContextMixin, View):
    """View for redeeming a reward."""
    login_url = 'login'
    active_page = 'rewards'
    
    def post(self, request, reward_id):
        # Get the reward
        reward = get_object_or_404(Reward, id=reward_id, is_active=True)
        
        # Get points service
        points_service = PointsService()
        
        # Attempt to redeem the reward
        with transaction.atomic():
            # Check stock if applicable
            if reward.stock > 0:
                if reward.stock < 1:
                    messages.error(request, f"Sorry, {reward.name} is out of stock.")
                    return redirect('rewards')
                    
                # Decrement stock
                reward.stock -= 1
                reward.save()
            
            # Spend points
            user_points, point_transaction, success = points_service.spend_points(
                request.user,
                reward.points_required,
                f"Redeemed reward: {reward.name}",
                str(reward.id)
            )
            
            if not success:
                messages.error(request, 
                    f"You don't have enough points. You need {reward.points_required} points, "
                    f"but you only have {user_points.total_points} points."
                )
                return redirect('rewards')
                
            # Create redemption record
            redemption = Redemption.objects.create(
                user=request.user,
                reward=reward,
                points_spent=reward.points_required,
                transaction=point_transaction
            )
            
            messages.success(request, 
                f"You've successfully redeemed {reward.name} for "
                f"{reward.points_required} points!"
            )
            
        return redirect('redemptions')


class UserRedemptionsView(LoginRequiredMixin, BaseContextMixin, View):
    """View for displaying user's reward redemptions."""
    login_url = 'login'
    active_page = 'redemptions'
    
    def get(self, request):
        # Get user's redemptions
        redemptions = Redemption.objects.filter(
            user=request.user
        ).order_by('-redeemed_at')
        
        # Paginate redemptions
        paginator = Paginator(redemptions, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context = self.get_context_data(
            page_obj=page_obj
        )
        
        return render(request, 'admin/redemptions.html', context)
