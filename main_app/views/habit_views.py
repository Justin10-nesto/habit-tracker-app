"""
Views for managing habits, including creating, editing, and completing habits.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone

from ..models import Habit, UserHabit, Category, HabitCompletion, get_uuid
from ..services.notification_service import NotificationService
import datetime


class HabitListView(LoginRequiredMixin, View):
    """View to display all habits available to the user"""
    login_url = 'login'
    
    def get(self, request):
        # Get filtering and sorting parameters
        category_filter = request.GET.get('category', '')
        search_query = request.GET.get('search', '')
        sort_by = request.GET.get('sort', 'name')
        
        # Get all habits
        habits = Habit.objects.all()
        
        # Apply filters
        if category_filter:
            habits = habits.filter(category_id=category_filter)
        
        if search_query:
            habits = habits.filter(name__icontains=search_query)
        
        # Apply sorting
        if sort_by == 'name':
            habits = habits.order_by('name')
        elif sort_by == 'newest':
            habits = habits.order_by('-created_at')
        elif sort_by == 'category':
            habits = habits.order_by('category__name', 'name')
        
        # Get categories for filter dropdown
        categories = Category.objects.all()
        
        # Get user's existing habits
        user_habit_ids = UserHabit.objects.filter(
            user=request.user
        ).values_list('habit_id', flat=True)
        
        context = {
            'habits': habits,
            'categories': categories,
            'user_habit_ids': user_habit_ids,
            'category_filter': category_filter,
            'search_query': search_query,
            'sort_by': sort_by
        }
        
        return render(request, 'main_app/habits.html', context)


class UserHabitListView(LoginRequiredMixin, View):
    """View to display user's habits"""
    login_url = 'login'
    
    def get(self, request):
        # Get user's active habits
        user_habits = UserHabit.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('habit', 'habit__category')
        
        # Get today's completions
        today = timezone.now().date()
        completed_today = set(
            HabitCompletion.objects.filter(
                user_habit__user=request.user,
                completion_date=today
            ).values_list('user_habit_id', flat=True)
        )
        
        # Group habits by category
        habits_by_category = {}
        for user_habit in user_habits:
            category_name = user_habit.habit.category.name if user_habit.habit.category else "Uncategorized"
            
            if category_name not in habits_by_category:
                habits_by_category[category_name] = []
                
            habits_by_category[category_name].append({
                'id': user_habit.id,
                'name': user_habit.habit.name,
                'description': user_habit.habit.description,
                'streak': user_habit.streak,
                'completed_today': user_habit.id in completed_today,
                'periodicity': user_habit.habit.periodicity
            })
        
        context = {
            'habits_by_category': habits_by_category,
            'today': today
        }
        
        return render(request, 'main_app/my_habits.html', context)


class HabitCompletionView(LoginRequiredMixin, View):
    """View to mark habits as complete"""
    login_url = 'login'
    
    def post(self, request, habit_id):
        user_habit = get_object_or_404(UserHabit, id=habit_id, user=request.user)
        today = timezone.now().date()
        
        # Check if already completed today
        already_completed = HabitCompletion.objects.filter(
            user_habit=user_habit,
            completion_date=today
        ).exists()
        
        if already_completed:
            messages.info(request, f"You've already completed '{user_habit.habit.name}' today.")
            return redirect('my_habits')
        
        # Create completion record
        completion = HabitCompletion(
            id=get_uuid(),
            user_habit=user_habit,
            completion_date=today,
            timestamp=timezone.now()
        )
        completion.save()
        
        # Update streak
        yesterday = today - datetime.timedelta(days=1)
        completed_yesterday = HabitCompletion.objects.filter(
            user_habit=user_habit,
            completion_date=yesterday
        ).exists()
        
        # Update streak logic
        if completed_yesterday or user_habit.streak == 0:
            user_habit.streak += 1
        else:
            # Reset streak if chain was broken
            user_habit.streak = 1
            
        user_habit.last_completed = today
        user_habit.save()
        
        # Check for streak milestones and send notifications if applicable
        if user_habit.streak in [7, 14, 21, 30, 60, 90, 180, 365]:
            NotificationService.send_streak_milestone_email(user_habit, user_habit.streak)
            
        messages.success(request, f"You've completed '{user_habit.habit.name}' for today!")
        return redirect('my_habits')


class HabitCreateView(LoginRequiredMixin, View):
    """View to create a new custom habit"""
    login_url = 'login'
    
    def get(self, request):
        # Get all categories for the form
        categories = Category.objects.filter(user=request.user)
        
        context = {
            'categories': categories,
            'periodicities': Habit.PERIODICITY_CHOICES
        }
        
        return render(request, 'main_app/create_habit.html', context)
    
    def post(self, request):
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        periodicity = request.POST.get('periodicity')
        category_id = request.POST.get('category')
        
        if not name:
            messages.error(request, "Habit name is required.")
            return redirect('create_habit')
            
        # Create the habit
        habit = Habit(
            id=get_uuid(),
            name=name,
            description=description,
            periodicity=periodicity,
            created_at=timezone.now()
        )
        
        # Set category if provided
        if category_id:
            try:
                category = Category.objects.get(id=category_id, user=request.user)
                habit.category = category
            except Category.DoesNotExist:
                pass
                
        habit.save()
        
        # Add to user's habits
        user_habit = UserHabit(
            id=get_uuid(),
            user=request.user,
            habit=habit,
            streak=0,
            is_active=True,
            start_date=timezone.now().date()
        )
        user_habit.save()
        
        messages.success(request, f"Habit '{name}' created successfully!")
        return redirect('my_habits')
