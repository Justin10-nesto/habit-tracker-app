from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.utils import timezone
from main_app.services.notification_service import NotificationService
from ..models import HabitCompletion, UserHabit, MissedHabit, HabitStreak, Reminder
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def check_missed_habits(start_date=None):
    """
    Checks for habits that should have been completed but weren't
    and marks them as missed, updating streaks accordingly.
    Handles system downtime by checking all dates from last operation to current date.
    
    Args:
        start_date: Optional date to start checking from. If None, checks from yesterday.
    """
    today = timezone.now().date()
    
    # If no start date provided, default to yesterday
    if not start_date:
        start_date = today - timedelta(days=1)
    
    # Ensure start_date is not in the future
    start_date = min(start_date, today - timedelta(days=1))
    
    # Generate list of dates to check
    dates_to_check = []
    current_date = start_date
    while current_date < today:
        dates_to_check.append(current_date)
        current_date += timedelta(days=1)
    
    # ---------- DAILY HABITS ----------
    # Get all active daily habits
    daily_habits = UserHabit.objects.filter(
        is_active=True,
        habit__periodicity='DAILY'
    )
    
    for habit in daily_habits:
        for check_date in dates_to_check:
            # Skip if already completed on this date
            if HabitCompletion.objects.filter(
                user_habit=habit,
                completion_date=check_date
            ).exists():
                continue
            
            # Skip if already marked as missed
            if MissedHabit.objects.filter(
                user_habit=habit,
                missed_date=check_date
            ).exists():
                continue
            
            # Mark as missed
            MissedHabit.objects.create(
                user_habit=habit,
                missed_date=check_date
            )
            
            # Reset streak if it was active
            if habit.streak > 0:
                # Save old streak for historical records
                streak_start = check_date - timedelta(days=habit.streak)
                HabitStreak.objects.create(
                    user_habit=habit,
                    streak_length=habit.streak,
                    start_date=streak_start,
                    end_date=check_date
                )
                # Reset current streak
                habit.streak = 0
                habit.save()
    
    # ---------- WEEKLY HABITS ----------
    # Process each week in the date range
    current_week_start = start_date
    while current_week_start < today:
        # Find week boundaries
        week_start = current_week_start - timedelta(days=current_week_start.weekday())
        week_end = week_start + timedelta(days=6)
        
        if week_end >= today:
            break
        
        weekly_habits = UserHabit.objects.filter(
            is_active=True,
            habit__periodicity='WEEKLY'
        )
        
        for habit in weekly_habits:
            # Check if completed within this week
            completed_this_week = HabitCompletion.objects.filter(
                user_habit=habit,
                completion_date__gte=week_start,
                completion_date__lte=week_end
            ).exists()
            
            if completed_this_week:
                continue
                
            # Skip if already marked as missed
            if MissedHabit.objects.filter(
                user_habit=habit,
                missed_date=week_end
            ).exists():
                continue
                
            # Mark as missed
            MissedHabit.objects.create(
                user_habit=habit,
                missed_date=week_end
            )
            
            # Reset streak if it was active
            if habit.streak > 0:
                # Save streak history
                streak_start = week_end - timedelta(weeks=habit.streak)
                HabitStreak.objects.create(
                    user_habit=habit,
                    streak_length=habit.streak,
                    start_date=streak_start,
                    end_date=week_end
                )
                # Reset current streak
                habit.streak = 0
                habit.save()
        
        current_week_start += timedelta(days=7)
    
    # ---------- MONTHLY HABITS ----------
    # Process each month in the date range
    current_month = start_date
    while current_month < today:
        # Find month boundaries
        month_start = current_month.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        
        if month_end >= today:
            break
        
        monthly_habits = UserHabit.objects.filter(
            is_active=True,
            habit__periodicity='MONTHLY'
        )
        
        for habit in monthly_habits:
            # Check if completed within this month
            completed_this_month = HabitCompletion.objects.filter(
                user_habit=habit,
                completion_date__gte=month_start,
                completion_date__lte=month_end
            ).exists()
            
            if completed_this_month:
                continue
                
            # Skip if already marked as missed
            if MissedHabit.objects.filter(
                user_habit=habit,
                missed_date=month_end
            ).exists():
                continue
                
            # Mark as missed
            MissedHabit.objects.create(
                user_habit=habit,
                missed_date=month_end
            )
            
            # Reset streak if it was active
            if habit.streak > 0:
                # Calculate streak start date
                streak_start = month_end
                for _ in range(habit.streak):
                    month = streak_start.month - 1
                    year = streak_start.year
                    if month == 0:
                        month = 12
                        year -= 1
                    
                    day = min(streak_start.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
                    streak_start = streak_start.replace(year=year, month=month, day=day)
                
                # Save streak history
                HabitStreak.objects.create(
                    user_habit=habit,
                    streak_length=habit.streak,
                    start_date=streak_start,
                    end_date=month_end
                )
                # Reset current streak
                habit.streak = 0
                habit.save()
        
        current_month = next_month


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
