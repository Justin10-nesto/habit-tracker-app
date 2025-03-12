# Habit Tracker

A comprehensive web application for tracking and managing personal habits, with gamification features to encourage consistent habit formation.

## Core Features

### 1. Habit Management
- Create and track personal habits
- Organize habits into categories
- Set custom schedules and reminders
- Mark habits as complete/incomplete
- View habit streaks and progress

### 2. Points & Rewards System
- Earn points for completing habits
- Redeem points for custom rewards
- Track point history and transactions
- View redemption history
- Set up custom rewards with point values

### 3. Analytics & Insights
- View detailed habit completion statistics
- Track progress over time
- Analyze habit patterns and trends
- Generate performance reports
- Visual data representations

### 4. Achievement System
- Unlock achievements for consistent habit completion
- Track milestone progress
- View earned achievements
- Special rewards for achievement completion

### 5. User Management
- Secure user authentication
- Customizable user profiles
- Profile picture support
- Theme customization options
- Personal dashboard

## Technical Features

### Admin Panel
- Comprehensive admin interface
- Habit management dashboard
- User activity monitoring
- System settings configuration
- Analytics and reporting tools

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Django web framework
- sqllite database
- Modern web browser

### Installation
1. Clone the repository
2. Install required dependencies
3. Configure database settings
4. Run migrations
5. Start the development server

### Configuration
- Set up environment variables
- Configure database connection
- Set email settings (optional)
- Configure static files

## Usage

## Usage

### SEEDERS
1. Run the following command to seed the database:
   ```bash
   python manage.py seed_habits
   python manage.py seed_users
   python manage.py seed_user_habits
   ```

### Login Credentials for Testing
After running the seeders, you can use the following test accounts to log in and explore the application without creating new data:

| Username       | Email                       | Password    |
|----------------|-----------------------------|-------------|
| justin_lasway  | jastinlasway10@gmail.com    | password123 |
| anzigare       | anzigare@gmail.com          | anzigar@234 |
| siaka_thomas   | siakathomas12@gmail.com     | er24@#$     |

### User Registration
1. Access the registration page
2. Fill in registration details
3. login

### Creating Habits
1. Log into your account (you can use default credentials on seeders)
2. Navigate to "My Habits"
3. Click "Create New Habit"
4. Fill in habit details
5. Set schedule and reminders

### Tracking Progress
1. Access your dashboard
2. View habit completion status
3. Check streaks and achievements
4. Review analytics data

### Managing Rewards
1. Visit the Rewards section
2. View available rewards
3. Check point balance
4. Redeem points for rewards

## Support

For support and feature requests, please create an issue in the repository or contact the development team.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Bootstrap for the responsive design framework
- Font Awesome for icons
- Django community for the web framework
- Contributors and users of the application

---

© 2025 Habit Tracker. All rights reserved.