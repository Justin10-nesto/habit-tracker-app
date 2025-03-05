from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.utils import timezone
from main_app.services.notification_service import NotificationService
from ..models import HabitCompletion, UserHabit, MissedHabit, HabitStreak, Reminder
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def check_missed_habits():
    """
    Checks for habits that should have been completed but weren't
    and marks them as missed, updating streaks accordingly
    """
    today = timezone.now().date()
    
    # ---------- DAILY HABITS ----------
    yesterday = today - timedelta(days=1)
    
    # Get all active daily habits
    daily_habits = UserHabit.objects.filter(
        is_active=True,
        habit__periodicity='DAILY'
    )
    
    for habit in daily_habits:
        # Skip if completed yesterday
        if habit.last_completed == yesterday:
            continue
        
        # Skip if already marked as missed
        if MissedHabit.objects.filter(user_habit=habit, missed_date=yesterday).exists():
            continue
        
        # Mark as missed
        MissedHabit.objects.create(
            user_habit=habit,
            missed_date=yesterday
        )
        
        # Reset streak
        if habit.streak > 0:
            # Save old streak for historical records
            HabitStreak.objects.create(
                user_habit=habit,
                streak_length=habit.streak,
                start_date=yesterday - timedelta(days=habit.streak),
                end_date=yesterday
            )
            # Reset current streak
            habit.streak = 0
            habit.save()
            
    # ---------- WEEKLY HABITS ----------
    # Get the dates for last week (previous Sunday to Saturday)
    # Using ISO calendar: week starts on Monday (1) and ends on Sunday (7)
    current_weekday = today.weekday()  # 0=Monday, 6=Sunday
    last_week_end = today - timedelta(days=current_weekday + 1)  # Last Sunday
    last_week_start = last_week_end - timedelta(days=6)  # Last Monday
    
    # Get all active weekly habits
    weekly_habits = UserHabit.objects.filter(
        is_active=True,
        habit__periodicity='WEEKLY'
    )
    
    for habit in weekly_habits:
        # Check if completed within last week
        completed_last_week = HabitCompletion.objects.filter(
            user_habit=habit,
            completion_date__gte=last_week_start,
            completion_date__lte=last_week_end
        ).exists()
        
        if completed_last_week:
            continue
            
        # Skip if already marked as missed
        if MissedHabit.objects.filter(user_habit=habit, missed_date=last_week_end).exists():
            continue
            
        # Mark as missed (using the last day of the week as the missed date)
        MissedHabit.objects.create(
            user_habit=habit,
            missed_date=last_week_end
        )
        
        # Reset streak
        if habit.streak > 0:
            # Save streak history
            HabitStreak.objects.create(
                user_habit=habit,
                streak_length=habit.streak,
                start_date=last_week_end - timedelta(weeks=habit.streak),
                end_date=last_week_end
            )
            # Reset current streak
            habit.streak = 0
            habit.save()
            
    # ---------- MONTHLY HABITS ----------
    # Determine last month's date range
    today_day = today.day
    first_of_this_month = today.replace(day=1)
    last_of_previous_month = first_of_this_month - timedelta(days=1)
    first_of_previous_month = last_of_previous_month.replace(day=1)
    
    # Get all active monthly habits
    monthly_habits = UserHabit.objects.filter(
        is_active=True,
        habit__periodicity='MONTHLY'
    )
    
    for habit in monthly_habits:
        # Check if completed within last month
        completed_last_month = HabitCompletion.objects.filter(
            user_habit=habit,
            completion_date__gte=first_of_previous_month,
            completion_date__lte=last_of_previous_month
        ).exists()
        
        if completed_last_month:
            continue
            
        # Skip if already marked as missed
        if MissedHabit.objects.filter(user_habit=habit, missed_date=last_of_previous_month).exists():
            continue
            
        # Mark as missed (using the last day of the month as the missed date)
        MissedHabit.objects.create(
            user_habit=habit,
            missed_date=last_of_previous_month
        )
        
        # Reset streak
        if habit.streak > 0:
            # Calculate approximated start date (month calculations can be tricky)
            # This is a simplification - in real app you might need more precise calculations
            streak_start = last_of_previous_month
            for _ in range(habit.streak):
                # Go back one month (approximately)
                month = streak_start.month - 1
                year = streak_start.year
                if month == 0:
                    month = 12
                    year -= 1
                
                # Try to use the same day, but adjust if the month doesn't have that day
                day = min(streak_start.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
                streak_start = streak_start.replace(year=year, month=month, day=day)
            
            # Save streak history
            HabitStreak.objects.create(
                user_habit=habit,
                streak_length=habit.streak,
                start_date=streak_start,
                end_date=last_of_previous_month
            )
            # Reset current streak
            habit.streak = 0
            habit.save()


def check_and_send_notifications():
    """Check for due reminders and send notifications"""
    current_time = timezone.localtime(timezone.now())
    logger.info(f"Running notification check at {current_time}")

    # Get all reminders
    reminders = Reminder.objects.select_related('user_habit', 'user_habit__user', 'user_habit__habit').all()

    for reminder in reminders:
        try:
            user_habit = reminder.user_habit
            reminder_time = reminder.reminder_time

            # Convert reminder time to current date
            reminder_datetime = datetime.combine(
                current_time.date(),
                reminder_time
            )

            # Check if it's time to send the reminder (within the current hour)
            if current_time.hour == reminder_datetime.hour:
                # Send the reminder
                success = NotificationService.send_reminder_email(user_habit)
                if success:
                    logger.info(f"Sent reminder for habit '{user_habit.habit.name}' to {user_habit.user.email}")
                else:
                    logger.warning(f"Failed to send reminder for habit '{user_habit.habit.name}' to {user_habit.user.email}")

        except Exception as e:
            logger.error(f"Error processing reminder: {str(e)}")
