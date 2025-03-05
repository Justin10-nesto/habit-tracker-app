from django.core.management.base import BaseCommand
from main_app.models import Category, Habit, UserHabit, HabitCompletion, MissedHabit
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import uuid
import random

class Command(BaseCommand):
    help = 'Seeds the database with user habits, completions, and missed records to demonstrate streaks'

    def handle(self, *args, **kwargs):
        # Check if there are users in the system
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR('No users found. Please create at least one user first.'))
            return

        # Check if there are habits in the system
        habits = Habit.objects.all()
        if not habits.exists():
            self.stdout.write(self.style.ERROR('No habits found. Please run seed_habits command first.'))
            return

        # Get all users and habits
        users = list(users)
        habits = list(habits)
        
        # Create user habits with completions and missed records
        created_user_habits = 0
        created_completions = 0
        created_missed = 0

        # Today's date for reference
        today = timezone.now().date()
        
        # For each user, assign some random habits
        for user in users:
            # Randomly select 3-7 habits for this user
            num_habits = random.randint(3, 7)
            user_habits_to_create = random.sample(habits, min(num_habits, len(habits)))
            
            for habit in user_habits_to_create:
                # Create user habit
                user_habit = UserHabit.objects.create(
                    id=str(uuid.uuid4()),
                    user=user,
                    habit=habit,
                    streak=0,  
                    is_active=True,
                    start_date=today - timedelta(days=random.randint(14, 30))
                )
                created_user_habits += 1
                
                # Determine if this habit will have a continuous streak
                has_continuous_streak = random.choice([True, False])
                
                if has_continuous_streak:
                    # Create a continuous streak (3-10 days)
                    streak_length = random.randint(3, 10)
                    
                    # Create completion records for the streak
                    for i in range(streak_length):
                        completion_date = today - timedelta(days=i)
                        HabitCompletion.objects.create(
                            id=str(uuid.uuid4()),
                            user_habit=user_habit,
                            completion_date=completion_date,
                            timestamp=timezone.now().replace(hour=random.randint(8, 20))
                        )
                        created_completions += 1
                    
                    # Update the streak count
                    user_habit.streak = streak_length
                    user_habit.last_completed = today
                    user_habit.save()
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'Created continuous streak of {streak_length} days for {user.username} - {habit.name}'
                    ))
                else:
                    # Create 5 random completions within the last 14 days
                    completion_dates = set()
                    for _ in range(5):
                        days_ago = random.randint(0, 13)
                        completion_date = today - timedelta(days=days_ago)
                        completion_dates.add(completion_date)
                    
                    # Create completion records
                    for completion_date in completion_dates:
                        HabitCompletion.objects.create(
                            id=str(uuid.uuid4()),
                            user_habit=user_habit,
                            completion_date=completion_date,
                            timestamp=timezone.now().replace(hour=random.randint(8, 20))
                        )
                        created_completions += 1
                    
                    # Create 2 missed records
                    missed_dates = set()
                    while len(missed_dates) < 2:
                        days_ago = random.randint(1, 13)
                        missed_date = today - timedelta(days=days_ago)
                        # Ensure the date wasn't already marked as completed
                        if missed_date not in completion_dates:
                            missed_dates.add(missed_date)
                    
                    # Create missed records
                    for missed_date in missed_dates:
                        MissedHabit.objects.create(
                            id=str(uuid.uuid4()),
                            user_habit=user_habit,
                            missed_date=missed_date,
                            created_at=timezone.now()
                        )
                        created_missed += 1
                    
                    # Calculate the current streak based on consecutive completions
                    # Sort completion dates in descending order
                    sorted_dates = sorted(list(completion_dates), reverse=True)
                    current_streak = 0
                    
                    if sorted_dates:  # If there are any completions
                        current_date = sorted_dates[0]
                        current_streak = 1  # Start with the most recent completion
                        
                        for i in range(1, len(sorted_dates)):
                            # Check if this date is consecutive with the previous one
                            if sorted_dates[i] == current_date - timedelta(days=1):
                                current_streak += 1
                                current_date = sorted_dates[i]
                            else:
                                break
                    
                    # Update the streak count and last completed date
                    user_habit.streak = current_streak
                    if sorted_dates:  # If there are any completions
                        user_habit.last_completed = sorted_dates[0]  # Most recent completion
                    user_habit.save()
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'Created {len(completion_dates)} completions and {len(missed_dates)} missed records for {user.username} - {habit.name}'
                    ))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_user_habits} user habits'))
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_completions} habit completions'))
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_missed} missed habit records'))