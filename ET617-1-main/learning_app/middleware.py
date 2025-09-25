from django.utils.deprecation import MiddlewareMixin
from .utils import log_clickstream_event


class ClickstreamMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track user clicks and page views
    """
    
    def process_request(self, request):
        """Process each request to log basic page view events"""
        # Skip tracking for admin, static files, and API endpoints that we handle manually
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/track-video/',
            '/submit-quiz/',
        ]
        
        # Check if we should skip this path
        for skip_path in skip_paths:
            if request.path.startswith(skip_path):
                return None
        
        # Log page view for GET requests only (not form submissions)
        if request.method == 'GET':
            # Don't log if we're already logging this in the view
            manual_log_paths = [
                '/',
                '/login/',
                '/register/',
                '/dashboard/',
                '/analytics/',
            ]
            
            if not any(request.path.startswith(path) for path in manual_log_paths):
                log_clickstream_event(
                    request=request,
                    event_name='page_view',
                    component='Page',
                    description=f'User viewed page: {request.path}'
                )
        
        return None 