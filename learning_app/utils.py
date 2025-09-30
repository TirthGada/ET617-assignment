from django.utils import timezone
from .models import ClickstreamEvent


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Extract user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


def get_referrer(request):
    """Extract referrer from request"""
    return request.META.get('HTTP_REFERER', '')


def log_clickstream_event(request, event_name, component, description, user=None):
    """
    Log a clickstream event to the database
    
    Args:
        request: Django HttpRequest object
        event_name: Type of event (from ClickstreamEvent.EVENT_TYPES)
        component: Component where event occurred
        description: Detailed description of the event
        user: User object (optional, will use request.user if not provided)
    """
    # Use provided user or request.user, but allow for anonymous users
    event_user = user if user else (request.user if request.user.is_authenticated else None)
    
    # Create the clickstream event
    ClickstreamEvent.objects.create(
        user=event_user,
        event_context="Learning Platform - ET617 Assignment",
        component=component,
        event_name=event_name,
        description=description,
        origin="web",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        url=request.build_absolute_uri(),
        referrer=get_referrer(request),
        session_id=request.session.session_key or '',
    ) 