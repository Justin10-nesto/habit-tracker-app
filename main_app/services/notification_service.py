from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from ..models import UserProfile, UserHabit, Reminder
import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service to handle sending notifications based on user preferences"""
    
    @staticmethod
    def should_send_notification(user, notification_type):
        """Check if notification should be sent based on user preferences"""
        try:
            profile = UserProfile.objects.get(user=user)
            preferences = profile.notification_preferences
            
            # Check if notifications are allowed during current time (quiet hours)
            if preferences.get('quiet_hours_enabled', False):
                quiet_start = preferences.get('quiet_hours_start', '22:00')
                quiet_end = preferences.get('quiet_hours_end', '07:00')
                
                # Parse times
                try:
                    quiet_start_time = datetime.datetime.strptime(quiet_start, '%H:%M').time()
                    quiet_end_time = datetime.datetime.strptime(quiet_end, '%H:%M').time()
                    now = timezone.localtime(timezone.now(), timezone=timezone.pytz.timezone(profile.timezone)).time()
                    
                    # Check if current time is within quiet hours
                    if quiet_start_time <= quiet_end_time:
                        # Simple case: start time is before end time
                        if quiet_start_time <= now <= quiet_end_time:
                            logger.info(f"Not sending {notification_type} to {user.username} - within quiet hours")
                            return False
                    else:
                        # Complex case: quiet hours span midnight
                        if now >= quiet_start_time or now <= quiet_end_time:
                            logger.info(f"Not sending {notification_type} to {user.username} - within quiet hours")
                            return False
                except ValueError:
                    # If there's an error parsing times, default to allowing notifications
                    logger.warning(f"Error parsing quiet hours for user {user.username}")
            
            # Check notification-specific preferences
            if notification_type == 'email_reminder':
                return preferences.get('email_reminders', True)
            elif notification_type == 'email_streak':
                return preferences.get('email_streak_updates', True)
            elif notification_type == 'email_achievement':
                return preferences.get('email_achievements', True)
            elif notification_type == 'inapp_reminder':
                return preferences.get('inapp_reminders', True)
            elif notification_type == 'inapp_streak':
                return preferences.get('inapp_streak_updates', True)
            elif notification_type == 'inapp_achievement':
                return preferences.get('inapp_achievements', True)
            
            # Default to allowing the notification
            return True
            
        except UserProfile.DoesNotExist:
            # If profile doesn't exist, default to allowing notifications
            return True
    
    @classmethod
    def send_reminder_email(cls, user_habit):
        """Send reminder email for a habit"""
        user = user_habit.user
        habit = user_habit.habit
        
        # Check if the user wants email reminders
        if not cls.should_send_notification(user, 'email_reminder'):
            return False
        
        # Get the reminder for this habit
        reminder = Reminder.objects.filter(user_habit=user_habit).first()
        if not reminder:
            return False
        
        # Prepare email content
        subject = f"Reminder: Complete your habit '{habit.name}'"
        context = {
            'user': user,
            'habit': habit,
            'reminder_time': reminder.reminder_time,
        }
        html_message = render_to_string('emails/habit_reminder.html', context)
        plain_message = render_to_string('emails/habit_reminder.txt', context)
        
        # Send email
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False
            )
            logger.info(f"Sent reminder email for habit '{habit.name}' to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send reminder email: {str(e)}")
            return False
    
    @classmethod
    def send_streak_milestone_email(cls, user_habit, streak_length):
        """Send email for streak milestone"""
        user = user_habit.user
        habit = user_habit.habit
        
        # Check if the user wants streak update emails
        if not cls.should_send_notification(user, 'email_streak'):
            return False
        
        # Only send for significant milestones (7, 14, 21, 30, 60, 90, etc.)
        significant_milestones = [7, 14, 21, 30, 60, 90, 120, 180, 365]
        if streak_length not in significant_milestones:
            return False
        
        # Prepare email content
        subject = f"Congratulations! {streak_length}-day streak for '{habit.name}'"
        context = {
            'user': user,
            'habit': habit,
            'streak_length': streak_length,
        }
        html_message = render_to_string('emails/streak_milestone.html', context)
        plain_message = render_to_string('emails/streak_milestone.txt', context)
        
        # Send email
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False
            )
            logger.info(f"Sent streak milestone email ({streak_length} days) for habit '{habit.name}' to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send streak milestone email: {str(e)}")
            return False
    
    @classmethod
    def send_achievement_email(cls, user, achievement):
        """Send email for new achievement"""
        # Check if the user wants achievement emails
        if not cls.should_send_notification(user, 'email_achievement'):
            return False
        
        # Prepare email content
        subject = f"Achievement Unlocked: {achievement.name}!"
        context = {
            'user': user,
            'achievement': achievement,
        }
        html_message = render_to_string('emails/achievement_unlocked.html', context)
        plain_message = render_to_string('emails/achievement_unlocked.txt', context)
        
        # Send email
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False
            )
            logger.info(f"Sent achievement email for '{achievement.name}' to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send achievement email: {str(e)}")
            return False
