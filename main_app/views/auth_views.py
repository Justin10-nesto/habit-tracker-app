"""
Authentication views for login, registration, and logout functionality.
Implements strategy pattern for form handling.
"""

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from abc import ABC, abstractmethod


# Abstract Strategy for Authentication Forms
class AuthFormStrategy(ABC):
    @abstractmethod
    def process_form(self, request, *args, **kwargs):
        """Process the submitted form and return the appropriate response"""
        pass


class LoginStrategy(AuthFormStrategy):
    """Strategy for handling login forms"""
    
    def process_form(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'main_app/login.html')


class RegisterStrategy(AuthFormStrategy):
    """Strategy for handling registration forms"""
    
    def process_form(self, request, *args, **kwargs):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth') or None
        
        errors = {}
        
        # Validation
        if User.objects.filter(username=username).exists():
            errors['username'] = 'Username already exists'
        
        if User.objects.filter(email=email).exists():
            errors['email'] = 'Email already exists'
            
        if password != password_confirm:
            errors['password'] = 'Passwords do not match'
            
        if len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters'
            
        if errors:
            return render(request, 'main_app/register.html', {'errors': errors})
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Update profile
        user.profile.gender = gender if gender else None
        user.profile.date_of_birth = date_of_birth
        user.profile.save()
        
        messages.success(request, 'Registration successful! Please log in.')
        return redirect('login')


class BaseAuthView(View):
    """Base class for authentication views, using the strategy pattern"""
    template_name = None
    strategy = None
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        return self.strategy.process_form(request, *args, **kwargs)


class LoginView(BaseAuthView):
    """View for user login"""
    template_name = 'main_app/login.html'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.strategy = LoginStrategy()


class RegisterView(BaseAuthView):
    """View for user registration"""
    template_name = 'main_app/register.html'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.strategy = RegisterStrategy()


class LogoutView(View):
    """View for user logout"""
    
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('login')


class PasswordResetView(View):
    """View for password reset functionality"""
    
    def get(self, request):
        return render(request, 'main_app/password_reset.html')
    
    def post(self, request):
        email = request.POST.get('email')
        
        # Check if user exists with this email
        if not User.objects.filter(email=email).exists():
            messages.error(request, "No user found with this email address.")
            return render(request, 'main_app/password_reset.html')
        
        # In a real app, we would generate a token and send an email
        messages.success(request, "Password reset link has been sent to your email.")
        return redirect('login')
