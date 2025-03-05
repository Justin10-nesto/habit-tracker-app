from django.db.models import Count, Sum, Avg, Max, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import (
    User, HabitCompletion, UserHabit, MissedHabit, 
    HabitAnalytics, LeaderboardEntry, Habit, 
    PointTransaction, UserPoints
)
from ..services.analytics_service import AnalyticsService

class AnalyticsController:
    """
    Controller class for analytics functionality.
    Provides methods to fetch and process analytics data for admin views.
    """
    
    @staticmethod
    def get_system_overview():
        """
        Get system-wide analytics for admin dashboard
        Returns counts and statistics about the entire application
        """
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        thirty_days_ago = today - timedelta(days=30)
        
        # User stats
        total_users = User.objects.count()
        active_users = User.objects.filter(
            last_login__gte=thirty_days_ago
        ).count()
        new_users_today = User.objects.filter(
            date_joined__date=today
        ).count()
        
        # Habit stats
        total_habits = Habit.objects.count()
        total_user_habits = UserHabit.objects.count()
        active_habits = UserHabit.objects.filter(
            is_active=True
        ).count()
        
        # Completion stats
        completions_today = HabitCompletion.objects.filter(
            completion_date=today
        ).count()
        completions_yesterday = HabitCompletion.objects.filter(
            completion_date=yesterday
        ).count()
        completions_this_month = HabitCompletion.objects.filter(
            completion_date__gte=thirty_days_ago
        ).count()
        
        # Missed habits
        missed_yesterday = MissedHabit.objects.filter(
            missed_date=yesterday
        ).count()
        
        # Points and gamification
        total_points_awarded = PointTransaction.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        points_today = PointTransaction.objects.filter(
            timestamp__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Activity trend
        daily_completions = []
        for i in range(30, -1, -1):
            date = today - timedelta(days=i)
            count = HabitCompletion.objects.filter(completion_date=date).count()
            daily_completions.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        
        return {
            'user_stats': {
                'total': total_users,
                'active': active_users,
                'active_percentage': round(active_users / total_users * 100 if total_users else 0, 1),
                'new_today': new_users_today,
            },
            'habit_stats': {
                'total_habits': total_habits,
                'total_user_habits': total_user_habits,
                'active_habits': active_habits,
                'inactive_habits': total_user_habits - active_habits,
            },
            'completion_stats': {
                'today': completions_today,
                'yesterday': completions_yesterday, 
                'this_month': completions_this_month,
                'completion_rate': round(
                    (completions_yesterday / active_habits * 100) if active_habits else 0, 1
                ),
                'missed_yesterday': missed_yesterday,
            },
            'points': {
                'total_awarded': total_points_awarded,
                'today': points_today,
            },
            'trends': {
                'daily_completions': daily_completions,
            }
        }
    
    @staticmethod
    def get_user_analytics(user_id=None, username=None):
        """
        Get detailed analytics for a specific user
        Pass either user_id or username
        """
        try:
            # Get the user
            user = None
            if user_id:
                user = User.objects.get(id=user_id)
            elif username:
                user = User.objects.get(username=username)
            
            if not user:
                return {'error': 'User not found'}
            
            # Get habits
            user_habits = UserHabit.objects.filter(user=user)
            habit_details = []
            
            total_completions = 0
            total_missed = 0
            max_streak = 0
            
            for habit in user_habits:
                completions_count = HabitCompletion.objects.filter(user_habit=habit).count()
                missed_count = MissedHabit.objects.filter(user_habit=habit).count()
                
                total_completions += completions_count
                total_missed += missed_count
                max_streak = max(max_streak, habit.streak)
                
                habit_details.append({
                    'id': habit.id,
                    'name': habit.habit.name,
                    'current_streak': habit.streak,
                    'completions_count': completions_count,
                    'missed_count': missed_count,
                    'is_active': habit.is_active,
                    'start_date': habit.start_date.strftime('%Y-%m-%d'),
                    'last_completed': habit.last_completed.strftime('%Y-%m-%d') if habit.last_completed else None
                })
            
            # Get points
            try:
                user_points = UserPoints.objects.get(user=user)
                points = {
                    'total': user_points.total_points,
                    'level': user_points.level
                }
            except UserPoints.DoesNotExist:
                points = {'total': 0, 'level': 0}
            
            # Recent activity
            recent_activity = []
            
            # Recent completions
            recent_completions = HabitCompletion.objects.filter(
                user_habit__user=user
            ).order_by('-completion_date', '-timestamp')[:10]
            
            for completion in recent_completions:
                recent_activity.append({
                    'type': 'completion',
                    'date': completion.completion_date.strftime('%Y-%m-%d'),
                    'habit_name': completion.user_habit.habit.name,
                    'timestamp': completion.timestamp.strftime('%Y-%m-%d %H:%M')
                })
            
            # Recent point transactions
            recent_points = PointTransaction.objects.filter(
                user=user
            ).order_by('-timestamp')[:10]
            
            for transaction in recent_points:
                recent_activity.append({
                    'type': 'points',
                    'amount': transaction.amount,
                    'description': transaction.description,
                    'timestamp': transaction.timestamp.strftime('%Y-%m-%d %H:%M')
                })
            
            # Sort by timestamp (newest first)
            recent_activity.sort(
                key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M'), 
                reverse=True
            )
            
            return {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d'),
                    'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else None
                },
                'summary': {
                    'total_habits': user_habits.count(),
                    'active_habits': user_habits.filter(is_active=True).count(),
                    'total_completions': total_completions,
                    'total_missed': total_missed,
                    'completion_ratio': round(
                        (total_completions / (total_completions + total_missed) * 100) 
                        if (total_completions + total_missed) else 0, 
                        1
                    ),
                    'max_streak': max_streak
                },
                'points': points,
                'habits': habit_details,
                'recent_activity': recent_activity[:10]  # Take only 10 most recent
            }
        
        except User.DoesNotExist:
            return {'error': 'User not found'}
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_habit_analytics(habit_id=None):
        """Get analytics for a specific habit type across all users"""
        try:
            if not habit_id:
                return {'error': 'Habit ID is required'}
            
            habit = Habit.objects.get(id=habit_id)
            
            # Get all user habits for this habit type
            user_habits = UserHabit.objects.filter(habit=habit)
            total_user_count = user_habits.count()
            active_user_count = user_habits.filter(is_active=True).count()
            
            # Completion statistics
            total_completions = HabitCompletion.objects.filter(
                user_habit__habit=habit
            ).count()
            
            # Top performers (users with highest streaks)
            top_streaks = user_habits.order_by('-streak')[:5]
            top_performers = []
            
            for user_habit in top_streaks:
                top_performers.append({
                    'user': user_habit.user.username,
                    'streak': user_habit.streak,
                    'start_date': user_habit.start_date.strftime('%Y-%m-%d')
                })
            
            # Get analytics records
            habit_analytics = HabitAnalytics.objects.filter(habit=habit)
            
            # Calculate average completion rate
            avg_completion_rate = habit_analytics.aggregate(
                avg_rate=Avg('completion_rate')
            )['avg_rate'] or 0
            
            # Calculate average missed count
            avg_missed = habit_analytics.aggregate(
                avg_missed=Avg('missed_count')
            )['avg_missed'] or 0
            
            # Abandon rate (percentage of users who have abandoned this habit)
            abandon_rate = round(
                ((total_user_count - active_user_count) / total_user_count * 100) 
                if total_user_count else 0,
                1
            )
            
            return {
                'habit': {
                    'id': habit.id,
                    'name': habit.name,
                    'description': habit.description,
                    'periodicity': habit.periodicity,
                    'category': habit.category.name if habit.category else None,
                },
                'usage': {
                    'total_users': total_user_count,
                    'active_users': active_user_count,
                    'abandon_rate': abandon_rate,
                },
                'performance': {
                    'total_completions': total_completions,
                    'avg_completion_rate': round(avg_completion_rate, 1),
                    'avg_missed': round(avg_missed, 1),
                    'top_performers': top_performers
                }
            }
            
        except Habit.DoesNotExist:
            return {'error': 'Habit not found'}
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def recalculate_all_analytics():
        """Recalculate all analytics data"""
        return AnalyticsService.recalculate_all_analytics()
        
    @staticmethod
    def fix_user_analytics(user_id=None, username=None):
        """Fix analytics for a specific user's habits"""
        try:
            # Get the user
            user = None
            if user_id:
                user = User.objects.get(id=user_id)
            elif username:
                user = User.objects.get(username=username)
            
            if not user:
                return {'error': 'User not found'}
            
            # Get habits and recalculate analytics
            user_habits = UserHabit.objects.filter(user=user)
            results = []
            
            for habit in user_habits:
                try:
                    analytics = AnalyticsService.recalculate_analytics(habit)
                    results.append({
                        'habit_name': habit.habit.name,
                        'success': True,
                        'longest_streak': analytics.longest_streak,
                        'missed_count': analytics.missed_count,
                        'completion_rate': analytics.completion_rate
                    })
                except Exception as e:
                    results.append({
                        'habit_name': habit.habit.name,
                        'success': False,
                        'error': str(e)
                    })
            
            return {
                'username': user.username,
                'fixed_count': sum(1 for r in results if r['success']),
                'total_count': len(results),
                'details': results
            }
            
        except User.DoesNotExist:
            return {'error': 'User not found'}
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def get_dashboard_data(user_id, period='monthly'):
        """
        Get analytics data for the user dashboard
        
        Parameters:
        - user_id: ID of the user to fetch data for
        - period: 'daily', 'weekly', or 'monthly'
        
        Returns:
        - Dictionary with analytics data
        """
        try:
            user = User.objects.get(id=user_id)
            today = timezone.now().date()
            
            # Define period ranges
            if period == 'Daily':
                start_date = today
                end_date = today
                previous_start = today - timedelta(days=1)
                previous_end = previous_start
                title = f"Today ({today.strftime('%b %d')})"
            elif period == 'Weekly':
                # Start of week (Monday)
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
                previous_start = start_date - timedelta(days=7)
                previous_end = previous_start + timedelta(days=6)
                title = f"This Week ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')})"
            else:  # monthly
                start_date = today.replace(day=1)
                # Last day of month
                next_month = start_date.replace(month=start_date.month + 1) if start_date.month < 12 else start_date.replace(year=start_date.year + 1, month=1)
                end_date = next_month - timedelta(days=1)
                # Previous month
                previous_end = start_date - timedelta(days=1)
                previous_start = previous_end.replace(day=1)
                title = f"This Month ({start_date.strftime('%B %Y')})"
            
            # Get user habits
            user_habits = UserHabit.objects.filter(user=user, is_active=True)
            total_habits = user_habits.count()
            
            # Get completions for current period
            completions = HabitCompletion.objects.filter(
                user_habit__in=user_habits,
                completion_date__gte=start_date,
                completion_date__lte=end_date
            )
            total_completions = completions.count()
            
            # Get missed habits for current period
            missed = MissedHabit.objects.filter(
                user_habit__in=user_habits,
                missed_date__gte=start_date,
                missed_date__lte=end_date
            )
            total_missed = missed.count()
            
            # Calculate completion rate
            completion_rate = 0
            if total_completions + total_missed > 0:
                completion_rate = round(total_completions / (total_completions + total_missed) * 100, 1)
            
            # Get completions for previous period for comparison
            previous_completions = HabitCompletion.objects.filter(
                user_habit__in=user_habits,
                completion_date__gte=previous_start,
                completion_date__lte=previous_end
            ).count()
            
            # Calculate change from previous period
            completion_change = 0
            if previous_completions > 0:
                completion_change = round((total_completions - previous_completions) / previous_completions * 100, 1)
            
            # Get points for current period
            points = PointTransaction.objects.filter(
                user=user,
                timestamp__date__gte=start_date,
                timestamp__date__lte=end_date
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Get points for previous period
            previous_points = PointTransaction.objects.filter(
                user=user,
                timestamp__date__gte=previous_start,
                timestamp__date__lte=previous_end
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Calculate points change
            points_change = 0
            if previous_points > 0:
                points_change = round((points - previous_points) / previous_points * 100, 1)
            
            # Get streak data
            max_streak = user_habits.aggregate(Max('streak'))['streak__max'] or 0
            
            return {
                'title': title,
                'period': period,
                'habits': {
                    'total': total_habits,
                    'max_streak': max_streak,
                },
                'completions': {
                    'total': total_completions,
                    'rate': completion_rate,
                    'change': completion_change,
                },
                'missed': {
                    'total': total_missed,
                },
                'points': {
                    'total': points,
                    'change': points_change,
                },
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d'),
                }
            }
            
        except User.DoesNotExist:
            return {'error': 'User not found'}
        except Exception as e:
            return {'error': str(e)}
