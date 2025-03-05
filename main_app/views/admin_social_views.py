"""
Admin views for social features.
"""

from django.shortcuts import render, redirect
from django.contrib import messages

from .admin_views import AdminViewMixin
from django.views import View
from ..services.analytics_service import AnalyticsService


class AdminSocialView(AdminViewMixin, View):
    """View for social features like leaderboards."""
    
    def get(self, request):
        # Get user privacy preference
        try:
            show_on_leaderboard = request.user.profile.privacy_settings.get('show_on_leaderboard', True)
        except:
            show_on_leaderboard = True
        
        # Get leaderboard data with privacy filtering
        leaderboard = AnalyticsService.get_leaderboard(
            period_type='WEEKLY', 
            visibility='all',  # Admin can see all entries
            limit=10
        )
        
        # Get global stats
        global_stats = AnalyticsService.get_global_stats(visibility='all')
        
        context = {
            'active_page': 'social',
            'leaderboard': leaderboard,
            'show_on_leaderboard': show_on_leaderboard,
            'global_stats': global_stats
        }
        
        return render(request, 'admin/social.html', context)
    
    def post(self, request):
        action = request.POST.get('action')
        
        if action == 'toggle_leaderboard':
            return self._handle_toggle_leaderboard(request)
        
        return redirect('admin_social')
    
    def _handle_toggle_leaderboard(self, request):
        """Toggle user's leaderboard visibility setting"""
        try:
            profile = request.user.profile
            privacy_settings = profile.privacy_settings
            
            # Toggle the show_on_leaderboard setting
            privacy_settings['show_on_leaderboard'] = not privacy_settings.get('show_on_leaderboard', True)
            profile.privacy_settings = privacy_settings
            profile.save()
            
            if privacy_settings['show_on_leaderboard']:
                messages.success(request, "You are now visible on leaderboards.")
            else:
                messages.success(request, "You are now hidden from leaderboards.")
        except Exception as e:
            messages.error(request, f"Failed to update settings: {str(e)}")
        
        return redirect('admin_social')
