from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main_app.models import UserProfile
from django.db.models.signals import post_save
from main_app.signals.user_signals import create_user_profile, save_user_profile

class Command(BaseCommand):
    help = 'Seeds the database with three initial users'

    def handle(self, *args, **options):
        # Disconnect signals temporarily
        post_save.disconnect(create_user_profile, sender=User)
        post_save.disconnect(save_user_profile, sender=User)

        # Delete all existing UserProfiles first to handle cascade properly
        UserProfile.objects.all().delete()
        # Then delete all non-superuser users
        User.objects.filter(is_superuser=False).delete()

        # Create three users with different roles
        users_data = [
            {
                'username': 'justin_lasway',
                'email': 'jastinlasway10@gmail.com',
                'password': 'password123',
                'first_name': 'Justin',
                'last_name': 'Lasway',
                'profile_data': {
                    'bio': 'Passionate about building healthy habits',
                    'timezone': 'Africa/Dar_es_Salaam',
                    'notification_preferences': {'email': True, 'push': True}
                }
            },
            {
                'username': 'anzigare',
                'email': 'anzigare@gmail.com',
                'password': 'anzigar@234',
                'first_name': 'Anzigar',
                'last_name': 'Shirima',
                'profile_data': {
                    'bio': 'Working on self-improvement',
                    'timezone': 'Africa/Nairobi',
                    'notification_preferences': {'email': True, 'push': False}
                }
            },
            {
                'username': 'siaka_thomas',
                'email': 'siakathomas12@gmail.com',
                'password': 'er24@#$',
                'first_name': 'Siaka',
                'last_name': 'Thomas',
                'profile_data': {
                    'bio': 'Fitness enthusiast and habit builder',
                    'timezone': 'Africa/Lagos',
                    'notification_preferences': {'email': False, 'push': True}
                }
            }
        ]

        for user_data in users_data:
            # Create user
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )

            # Create UserProfile manually
            profile_data = user_data['profile_data']
            UserProfile.objects.create(
                user=user,
                bio=profile_data['bio'],
                timezone=profile_data['timezone'],
                notification_preferences=profile_data['notification_preferences']
            )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created user: {user.username} with profile')
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded 3 users')
        )

        # Reconnect signals
        post_save.connect(create_user_profile, sender=User)
        post_save.connect(save_user_profile, sender=User)