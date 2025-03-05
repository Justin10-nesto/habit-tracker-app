"""
Admin views for habit management.
Includes views for managing habits, categories, and user habits.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone

from .admin_views import AdminViewMixin
from django.views import View
from ..models import Habit, Category, UserHabit, HabitCompletion, MissedHabit, Reminder, get_uuid
from ..services.notification_service import NotificationService
import datetime


class AdminHabitsView(AdminViewMixin, View):
    """View for managing all habits in the system."""
    
    def get(self, request):
        # Get filtering and sorting parameters
        category_filter = request.GET.get('category', '')
        search_query = request.GET.get('search', '')
        sort_by = request.GET.get('sort', 'name')
        
        # Filter habits
        habits = Habit.objects.all()
        
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
        
        # Pagination
        paginator = Paginator(habits, 12)  # Show 12 habits per page
        page_number = request.GET.get('page', 1)
        habits_page = paginator.get_page(page_number)
        
        # Get all categories for filtering
        categories = Category.objects.all()
        
        # Get user habit IDs for the template to show correct buttons
        user_habit_ids = UserHabit.objects.filter(
            user=request.user
        ).values_list('habit_id', flat=True)
        
        context = {
            'active_page': 'habits',
            'habits': habits_page,
            'categories': categories,
            'user_habit_ids': user_habit_ids,
            'category_filter': category_filter,
            'search_query': search_query,
            'sort_by': sort_by
        }
        
        return render(request, 'admin/habits.html', context)
    
    def post(self, request):
        action = request.POST.get('action', 'add')
        
        if action == 'add':
            return self._handle_add_habit(request)
        elif action == 'edit':
            return self._handle_edit_habit(request)
        elif action == 'delete':
            return self._handle_delete_habit(request)
        elif action == 'add_to_my_habits':
            return self._handle_add_to_my_habits(request)
        elif action == 'remove_from_my_habits':
            return self._handle_remove_from_my_habits(request)
        
        # Default case - redirect back to habits page
        return redirect('admin_habits')
    
    def _handle_add_habit(self, request):
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        periodicity = request.POST.get('periodicity')
        category_id = request.POST.get('category', None)
        
        habit = Habit(
            id=get_uuid(),
            name=name,
            description=description,
            periodicity=periodicity,
            created_at=timezone.now(),
        )
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                habit.category = category
            except Category.DoesNotExist:
                pass
                
        habit.save()
        messages.success(request, f'Habit "{name}" created successfully!')
        return redirect('admin_habits')
    
    def _handle_edit_habit(self, request):
        habit_id = request.POST.get('habit_id')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        periodicity = request.POST.get('periodicity')
        category_id = request.POST.get('category', None)
        
        try:
            habit = get_object_or_404(Habit, id=habit_id)
            habit.name = name
            habit.description = description
            habit.periodicity = periodicity
            
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    habit.category = category
                except Category.DoesNotExist:
                    habit.category = None
            else:
                habit.category = None
                
            habit.save()
            messages.success(request, f'Habit "{name}" updated successfully!')
        except Habit.DoesNotExist:
            messages.error(request, 'Habit not found!')
        
        return redirect('admin_habits')
    
    def _handle_delete_habit(self, request):
        habit_id = request.POST.get('habit_id')
        
        try:
            habit = get_object_or_404(Habit, id=habit_id)
            name = habit.name
            habit.delete()
            messages.success(request, f'Habit "{name}" deleted successfully!')
        except Habit.DoesNotExist:
            messages.error(request, 'Habit not found!')
        
        return redirect('admin_habits')
    
    def _handle_add_to_my_habits(self, request):
        habit_id = request.POST.get('habit_id')
        
        try:
            habit = get_object_or_404(Habit, id=habit_id)
            
            # Check if user already has this habit
            existing = UserHabit.objects.filter(user=request.user, habit=habit).exists()
            
            if not existing:
                user_habit = UserHabit(
                    id=get_uuid(),
                    user=request.user,
                    habit=habit,
                    streak=0,
                    is_active=True,
                    start_date=timezone.now().date()
                )
                user_habit.save()
                messages.success(request, f'Added "{habit.name}" to your habits!')
            else:
                messages.info(request, f'"{habit.name}" is already in your habits!')
                
        except Habit.DoesNotExist:
            messages.error(request, 'Habit not found!')
        
        return redirect('admin_habits')
    
    def _handle_remove_from_my_habits(self, request):
        habit_id = request.POST.get('habit_id')
        
        try:
            habit = get_object_or_404(Habit, id=habit_id)
            user_habit = UserHabit.objects.get(user=request.user, habit=habit)
            user_habit.delete()
            messages.success(request, f'Removed "{habit.name}" from your habits!')
        except (Habit.DoesNotExist, UserHabit.DoesNotExist):
            messages.error(request, 'Habit not found in your list!')
        
        return redirect('admin_habits')


class AdminCategoriesView(AdminViewMixin, View):
    """View for managing habit categories."""
    
    def get(self, request):
        categories = Category.objects.all()
        
        context = {
            'active_page': 'categories',
            'categories': categories,
        }
        
        return render(request, 'admin/categories.html', context)
    
    def post(self, request):
        action = request.POST.get('action', 'add')
        
        if action == 'add':
            return self._handle_add_category(request)
        elif action == 'edit':
            return self._handle_edit_category(request)
        elif action == 'delete':
            return self._handle_delete_category(request)
        
        return redirect('admin_categories')
    
    def _handle_add_category(self, request):
        name = request.POST.get('name')
        
        if name:
            category = Category(
                id=get_uuid(),
                name=name,
                created_at=timezone.now()
            )
            category.save()
            messages.success(request, f'Category "{name}" created successfully!')
        
        return redirect('admin_categories')
    
    def _handle_edit_category(self, request):
        category_id = request.POST.get('category_id')
        name = request.POST.get('name')
        
        try:
            category = get_object_or_404(Category, id=category_id)
            category.name = name
            category.save()
            messages.success(request, f'Category "{name}" updated successfully!')
        except Category.DoesNotExist:
            messages.error(request, 'Category not found!')
        
        return redirect('admin_categories')
    
    def _handle_delete_category(self, request):
        category_id = request.POST.get('category_id')
        
        try:
            category = get_object_or_404(Category, id=category_id)
            name = category.name
            category.delete()
            messages.success(request, f'Category "{name}" deleted successfully!')
        except Category.DoesNotExist:
            messages.error(request, 'Category not found!')
        
        return redirect('admin_categories')


class AdminMyHabitsView(AdminViewMixin, View):
    """View for managing user's habits."""
    
    def get(self, request):
        today = timezone.now().date()
        user_habits = UserHabit.objects.filter(user=request.user).select_related('habit')
        
        # Get reminders for habits to display in the template
        reminders = {}
        for habit in user_habits:
            reminder = Reminder.objects.filter(user_habit=habit).first()
            if reminder:
                reminders[habit.id] = reminder
        
        # Get completions for today to know which habits are already completed
        completed_today = set(
            HabitCompletion.objects.filter(
                user_habit__user=request.user,
                completion_date=today
            ).values_list('user_habit_id', flat=True)
        )
        
        # Get missed habits within the last 7 days
        recent_missed = self._get_recent_missed_habits(request.user, today)
        
        context = {
            'active_page': 'my_habits',
            'user_habits': user_habits,
            'reminders': reminders,
            'completed_today': completed_today,
            'recent_missed': recent_missed,
            'today': today,
        }
        
        return render(request, 'admin/my_habits.html', context)
    
    def _get_recent_missed_habits(self, user, today):
        # Get missed habits within the last 7 days
        recent_missed = {}
        week_ago = today - datetime.timedelta(days=7)
        missed_records = MissedHabit.objects.filter(
            user_habit__user=user,
            missed_date__gte=week_ago
        ).select_related('user_habit')
        
        for missed in missed_records:
            if missed.user_habit_id not in recent_missed:
                recent_missed[missed.user_habit_id] = []
            recent_missed[missed.user_habit_id].append(missed.missed_date)
        
        return recent_missed
    
    def post(self, request):
        action = request.POST.get('action')
        
        if action == 'complete':
            return self._handle_complete_habit(request)
        elif action == 'set_reminder':
            return self._handle_set_reminder(request)
        elif action == 'delete_reminder':
            return self._handle_delete_reminder(request)
                
        return redirect('admin_my_habits')
    
    def _handle_complete_habit(self, request):
        habit_id = request.POST.get('habit_id')
        try:
            user_habit = UserHabit.objects.get(id=habit_id, user=request.user)
            
            # Create completion record
            completion = HabitCompletion(
                id=get_uuid(),
                user_habit=user_habit,
                completion_date=timezone.now().date(),
                timestamp=timezone.now()
            )
            completion.save()
            
            # Check preferences and send notifications if needed
            if user_habit.streak in [7, 14, 21, 30, 60, 90, 120, 180, 365]:
                NotificationService.send_streak_milestone_email(user_habit, user_habit.streak)
            
            messages.success(request, f'You completed "{user_habit.habit.name}" for today!')
        except UserHabit.DoesNotExist:
            messages.error(request, "Habit not found.")
        
        return redirect('admin_my_habits')
    
    def _handle_set_reminder(self, request):
        habit_id = request.POST.get('habit_id')
        reminder_time = request.POST.get('reminder_time')
        recurring = request.POST.get('recurring') == 'on'
        reminder_date = None if recurring else request.POST.get('reminder_date')
        
        try:
            user_habit = UserHabit.objects.get(id=habit_id, user=request.user)
            
            # Check if a reminder already exists for this habit
            reminder, created = Reminder.objects.get_or_create(
                user_habit=user_habit,
                defaults={
                    'id': get_uuid(),
                    'reminder_time': reminder_time,
                    'reminder_date': reminder_date
                }
            )
            
            if not created:
                # Update existing reminder
                reminder.reminder_time = reminder_time
                reminder.reminder_date = reminder_date
                reminder.save()
                message = "Reminder updated successfully!"
            else:
                message = "Reminder set successfully!"
            
            messages.success(request, message)
        except UserHabit.DoesNotExist:
            messages.error(request, "Habit not found.")
        except Exception as e:
            messages.error(request, f"Error setting reminder: {str(e)}")
        
        return redirect('admin_my_habits')
    
    def _handle_delete_reminder(self, request):
        reminder_id = request.POST.get('reminder_id')
        try:
            reminder = Reminder.objects.get(id=reminder_id, user_habit__user=request.user)
            habit_name = reminder.user_habit.habit.name
            reminder.delete()
            messages.success(request, f'Reminder for "{habit_name}" deleted successfully.')
        except Reminder.DoesNotExist:
            messages.error(request, "Reminder not found.")
        
        return redirect('admin_my_habits')
