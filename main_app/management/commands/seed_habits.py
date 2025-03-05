from django.core.management.base import BaseCommand
from main_app.models import Category, Habit
from django.utils import timezone
from datetime import datetime
import uuid

class Command(BaseCommand):
    help = 'Seeds the database with predefined habit categories and habits'

    def handle(self, *args, **kwargs):
        # Define categories with their habits
        categories_data = {
            'Health & Fitness': [
                ('Daily Exercise', 'Maintain physical fitness through regular exercise', 'DAILY'),
                ('Drink Water', 'Stay hydrated by drinking 8 glasses of water', 'DAILY'),
                ('Sleep Early', 'Maintain a healthy sleep schedule', 'DAILY'),
            ],
            'Productivity': [
                ('Time Blocking', 'Plan and organize daily tasks using time blocks', 'DAILY'),
                ('Email Management', 'Process and organize emails', 'DAILY'),
                ('Weekly Planning', 'Plan tasks and goals for the week ahead', 'WEEKLY'),
            ],
            'Learning': [
                ('Read Books', 'Read educational or personal development books', 'DAILY'),
                ('Learn New Skill', 'Dedicate time to learning a new skill', 'WEEKLY'),
                ('Practice Language', 'Practice a foreign language', 'DAILY'),
            ],
            'Mental Wellbeing': [
                ('Meditation', 'Practice mindfulness meditation', 'DAILY'),
                ('Gratitude Journal', 'Write down things you\'re grateful for', 'DAILY'),
                ('Digital Detox', 'Take breaks from digital devices', 'WEEKLY'),
            ],
            'Personal Growth': [
                ('Network Building', 'Connect with professionals in your field', 'WEEKLY'),
                ('Personal Reflection', 'Reflect on personal goals and progress', 'WEEKLY'),
                ('Creative Expression', 'Engage in creative activities', 'DAILY'),
            ],
        }

        # Create categories and habits
        for category_name, habits in categories_data.items():
            # Create category
            category = Category.objects.create(
                id=str(uuid.uuid4()),
                name=category_name,
                created_at=timezone.now()
            )
            self.stdout.write(self.style.SUCCESS(f'Created category: {category_name}'))

            # Create habits for this category
            for habit_name, description, periodicity in habits:
                habit = Habit.objects.create(
                    id=str(uuid.uuid4()),
                    name=habit_name,
                    description=description,
                    periodicity=periodicity,
                    created_at=timezone.now(),
                    category=category
                )
                self.stdout.write(self.style.SUCCESS(f'Created habit: {habit_name}'))

        self.stdout.write(self.style.SUCCESS('Successfully seeded habit categories and habits'))