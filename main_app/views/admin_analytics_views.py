"""
Admin views for analytics functionality.
"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.utils import timezone

from .admin_views import AdminViewMixin
from django.views import View
from ..models import UserHabit, Category
from ..analytics.controller import AnalyticsController
import json


class AdminAnalyticsView(AdminViewMixin, View):
    """View for analytics and reporting."""
    
    def get(self, request):
        # Check for AJAX requests for specific data
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self._handle_ajax_request(request)
        # Regular page view - get user habits and categories
        user_habits = UserHabit.objects.filter(
            user=request.user, 
            is_active=True
        ).select_related('habit', 'habit__category')
        
        categories = Category.objects.filter(
            id__in=user_habits.values_list('habit__category', flat=True).distinct()
        )
        
        # Use user appearance settings for chart appearance
        try:
            theme_preference = request.user.profile.appearance_settings.get('theme', 'light')
            compact_view = request.user.profile.appearance_settings.get('compact_view', False)
            color_scheme = request.user.profile.appearance_settings.get('color_scheme', 'blue')
        except:
            theme_preference = 'light'
            compact_view = False
            color_scheme = 'blue'
        
        # Get initial dashboard data
        dashboard_data = AnalyticsController.get_dashboard_data(str(request.user.id), 'Monthly')
        # Format habits with consistent data structure
        habits_data = self._format_habits_data(user_habits, dashboard_data)
        
        context = {
            'active_page': 'analytics',
            'dashboard_data': dashboard_data,
            'habits': habits_data,
            "total_habits": len(habits_data),
            'categories': categories,
            'theme': theme_preference,
            'compact_view': compact_view,
            'color_scheme': color_scheme,
            'has_data': len(habits_data) > 0
        }
        print(context)
        
        return render(request, 'admin/analytics.html', context)
    
    def _handle_ajax_request(self, request):
        """Handle AJAX requests for analytics data"""
        data_type = request.GET.get('data_type', 'dashboard')
        timeframe = request.GET.get('timeframe', 'monthly')
        
        if data_type == 'habit':
            habit_id = request.GET.get('habit_id')
            html = AnalyticsController.get_habit_details_template(
                str(request.user.id), habit_id, timeframe
            )
            return HttpResponse(html)
            
        elif data_type == 'category':
            category_id = request.GET.get('category_id')
            html = AnalyticsController.get_category_details_template(
                str(request.user.id), category_id, timeframe
            )
            return HttpResponse(html)
            
        elif data_type == 'dashboard':
            data = AnalyticsController.get_dashboard_data(
                str(request.user.id), timeframe
            )
            return JsonResponse(data)
        
        return JsonResponse({"error": "Invalid data type requested"})
    
    def _format_habits_data(self, user_habits, dashboard_data):
        """Format habits with consistent data structure"""
        habits_data = []
        for habit in user_habits:
            completion_rate = 0
            
            # Try to get completion rate from the dashboard data if available
            if 'completion_rate' in dashboard_data and 'habit_metrics' in dashboard_data['completion_rate']:
                habit_metrics = dashboard_data['completion_rate']['habit_metrics'].get(habit.habit.id, {})
                completion_rate = habit_metrics.get('completion_rate', 0)
            
            habits_data.append({
                'id': habit.id,
                'habit': habit.habit,
                'streak': habit.streak,
                'completion_rate': completion_rate
            })
        
        return habits_data


class ExportAnalyticsView(AdminViewMixin, View):
    """View for exporting analytics data"""
    
    def get(self, request):
        export_format = request.GET.get('format', 'json')
        period = request.GET.get('period', 'monthly')
        
        data = AnalyticsController.get_dashboard_data(str(request.user.id), period)
        
        if export_format == 'csv':
            return self._export_as_csv(data, period)
        else:
            return self._export_as_json(data, period)
    
    def _export_as_json(self, data, period):
        response = HttpResponse(json.dumps(data, indent=4), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="analytics_{period}_{timezone.now().date()}.json"'
        return response
    
    def _export_as_csv(self, data, period):
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_{period}_{timezone.now().date()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Category', 'Metric', 'Value'])
        
        # Write summary data
        for category, metrics in data.items():
            if isinstance(metrics, dict) and 'summary' in metrics:
                for metric_name, value in metrics['summary'].items():
                    writer.writerow([category, metric_name, value])
        
        return response
