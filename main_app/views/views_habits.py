from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from ..models import UserHabit, HabitCompletion, Habit, Category, get_uuid
from ..services.notification_service import NotificationService
from datetime import datetime, timedelta

@login_required
def mark_habit_complete(request, habit_id):
    """Mark a habit as complete for today"""
    user_habit = get_object_or_404(UserHabit, id=habit_id, user=request.user)
    
    # Check if already completed today
    today = timezone.localtime(timezone.now()).date()
    already_completed = HabitCompletion.objects.filter(
        user_habit=user_habit,
        completion_date=today
    ).exists()
    
    if already_completed:
        messages.info(request, "You've already completed this habit today!")
        return redirect('dashboard')
    
    # Create completion record
    completion = HabitCompletion(
        id=get_uuid(),
        user_habit=user_habit,
        completion_date=today,
        timestamp=timezone.now()
    )
    completion.save()
    
    # Update streak
    yesterday = today - timedelta(days=1)
    completed_yesterday = HabitCompletion.objects.filter(
        user_habit=user_habit,
        completion_date=yesterday
    ).exists()
    
    if completed_yesterday or user_habit.streak == 0:
        # Increment streak if completed yesterday or starting fresh
        user_habit.streak += 1
    else:
        # Reset streak if the chain was broken
        user_habit.streak = 1
    
    user_habit.last_completed = today
    user_habit.save()
    
    # Check for streak milestone notifications
    # This is where we use the notification service
    if user_habit.streak in [7, 14, 21, 30, 60, 90, 180, 365]:
        NotificationService.send_streak_milestone_email(user_habit, user_habit.streak)
    
    messages.success(request, f"Great job! You've completed '{user_habit.habit.name}' for today!")
    return redirect('dashboard')
