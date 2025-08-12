from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
import json

from .models import Course, Content, Quiz, UserProgress, ClickstreamEvent, VideoAnalytics
from .utils import get_client_ip, log_clickstream_event


def home(request):
    """Homepage view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    log_clickstream_event(
        request=request,
        event_name='page_view',
        component='Homepage',
        description='User viewed the homepage'
    )
    
    return render(request, 'learning_app/home.html')


def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email', '')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            user = User.objects.create_user(username=username, password=password, email=email)
            
            log_clickstream_event(
                request=request,
                event_name='registration',
                component='Registration Form',
                description=f'New user registered with username: {username}',
                user=user
            )
            
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    
    log_clickstream_event(
        request=request,
        event_name='page_view',
        component='Registration Page',
        description='User viewed the registration page'
    )
    
    return render(request, 'learning_app/register.html')


def login_view(request):
    """User login view - accepts any credentials for demo purposes"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # If username is provided, try to authenticate or create user
        if username:
            # Try to get existing user
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create new user with provided credentials
                user = User.objects.create_user(
                    username=username, 
                    password=password or 'demo123',
                    email=f'{username}@demo.com'
                )
                messages.info(request, f'New account created for {username}')
            
            # Log them in regardless
            login(request, user)
            
            log_clickstream_event(
                request=request,
                event_name='login',
                component='Login Form',
                description=f'User {username} logged in successfully (demo mode)',
                user=user
            )
            
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please enter a username')
    
    log_clickstream_event(
        request=request,
        event_name='page_view',
        component='Login Page',
        description='User viewed the login page'
    )
    
    return render(request, 'learning_app/login.html')


def logout_view(request):
    """User logout view"""
    log_clickstream_event(
        request=request,
        event_name='logout',
        component='Logout',
        description=f'User {request.user.username} logged out',
        user=request.user
    )
    
    logout(request)
    messages.success(request, 'Logout successful!')
    return redirect('home')


@login_required
def dashboard(request):
    """User dashboard view"""
    courses = Course.objects.all()
    user_progress = UserProgress.objects.filter(user=request.user)
    
    # Calculate progress statistics
    total_content = Content.objects.count()
    completed_content = user_progress.filter(completed=True).count()
    progress_percentage = (completed_content / total_content * 100) if total_content > 0 else 0
    
    log_clickstream_event(
        request=request,
        event_name='page_view',
        component='Dashboard',
        description='User viewed the dashboard',
        user=request.user
    )
    
    context = {
        'courses': courses,
        'user_progress': user_progress,
        'progress_percentage': round(progress_percentage, 2),
        'total_content': total_content,
        'completed_content': completed_content,
    }
    
    return render(request, 'learning_app/dashboard.html', context)


@login_required
def course_detail(request, course_id):
    """Course detail view"""
    course = get_object_or_404(Course, id=course_id)
    contents = course.contents.all()
    
    # Get user progress for this course
    user_progress = UserProgress.objects.filter(user=request.user, content__course=course)
    progress_dict = {up.content_id: up for up in user_progress}
    
    log_clickstream_event(
        request=request,
        event_name='page_view',
        component='Course Detail',
        description=f'User viewed course: {course.title}',
        user=request.user
    )
    
    context = {
        'course': course,
        'contents': contents,
        'progress_dict': progress_dict,
        'user_progress': user_progress,  # Add this for easier template access
    }
    
    return render(request, 'learning_app/course_detail.html', context)


@login_required
def content_view(request, content_id):
    """Content view (text, video, or quiz)"""
    content = get_object_or_404(Content, id=content_id)
    
    # Get or create user progress
    user_progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        content=content
    )
    
    quiz = None
    if content.content_type == 'quiz':
        quiz = get_object_or_404(Quiz, content=content)
    
    log_clickstream_event(
        request=request,
        event_name='page_view',
        component=f'{content.content_type.title()} Content',
        description=f'User {request.user.username} ({request.user.email}) viewed {content.content_type}: {content.title}',
        user=request.user
    )
    
    context = {
        'content': content,
        'user_progress': user_progress,
        'quiz': quiz,
    }
    
    return render(request, 'learning_app/content_view.html', context)


@login_required
@csrf_exempt
def submit_quiz(request, content_id):
    """Handle quiz submission"""
    if request.method == 'POST':
        content = get_object_or_404(Content, id=content_id)
        quiz = get_object_or_404(Quiz, content=content)
        
        try:
            data = json.loads(request.body)
            selected_answer = data.get('answer')
            
            # Check if answer is correct
            is_correct = selected_answer == quiz.correct_answer
            score = 1 if is_correct else 0
            
            # Update user progress
            user_progress, created = UserProgress.objects.get_or_create(
                user=request.user,
                content=content
            )
            
            user_progress.quiz_score = score
            user_progress.completed = is_correct
            if is_correct:
                user_progress.completed_at = timezone.now()
            user_progress.save()
            
            # Log the quiz attempt
            log_clickstream_event(
                request=request,
                event_name='quiz_submit',
                component='Quiz',
                description=f'User {request.user.username} ({request.user.email}) submitted quiz for {content.title}. Answer: {selected_answer}, Correct: {is_correct}, Score: {score}',
                user=request.user
            )
            
            return JsonResponse({
                'success': True,
                'correct': is_correct,
                'score': score,
                'correct_answer': quiz.correct_answer
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def track_video(request):
    """Track video playback events"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content_id = data.get('content_id')
            event_type = data.get('event_type')  # play, pause, complete
            current_time = data.get('current_time', 0)
            
            content = get_object_or_404(Content, id=content_id)
            
            # Get or create video analytics record
            video_analytics, created = VideoAnalytics.objects.get_or_create(
                user=request.user,
                content=content,
                defaults={'current_time': current_time}
            )
            
            # Update analytics based on event type
            if event_type == 'play':
                event_name = 'video_play'
                description = f'User {request.user.username} ({request.user.email}) started playing video: {content.title} at {current_time}s'
            elif event_type == 'pause':
                event_name = 'video_pause'
                description = f'User {request.user.username} ({request.user.email}) paused video: {content.title} at {current_time}s'
                video_analytics.pause_timestamp = timezone.now()
            elif event_type == 'complete':
                event_name = 'video_complete'
                description = f'User {request.user.username} ({request.user.email}) completed video: {content.title}'
                video_analytics.completed = True
                
                # Mark content as completed
                user_progress, created = UserProgress.objects.get_or_create(
                    user=request.user,
                    content=content
                )
                user_progress.completed = True
                user_progress.completed_at = timezone.now()
                user_progress.video_watched_duration = content.video_duration
                user_progress.save()
            
            video_analytics.current_time = current_time
            video_analytics.save()
            
            # Log the event
            log_clickstream_event(
                request=request,
                event_name=event_name,
                component='Video Player',
                description=description,
                user=request.user
            )
            
            return JsonResponse({'success': True})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def mark_content_read(request, content_id):
    """Mark text content as read and log the event"""
    if request.method == 'POST':
        content = get_object_or_404(Content, id=content_id)
        
        # Only allow marking text content as read
        if content.content_type != 'text':
            return JsonResponse({'success': False, 'error': 'Only text content can be marked as read'})
        
        # Update user progress
        user_progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            content=content
        )
        
        user_progress.completed = True
        user_progress.completed_at = timezone.now()
        user_progress.save()
        
        # Log the read event
        log_clickstream_event(
            request=request,
            event_name='text_read',  # Using the new text_read event type
            component='Text Content',
            description=f'User {request.user.username} ({request.user.email}) marked text content as read: {content.title}',
            user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Content marked as read'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def admin_login_view(request):
    """Admin login for analytics access"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username == 'root' and password == 'root':
            request.session['admin_authenticated'] = True
            messages.success(request, 'Admin authentication successful!')
            return redirect('admin_analytics')
        else:
            messages.error(request, 'Invalid admin credentials')
    
    return render(request, 'learning_app/admin_login.html')


def admin_analytics_view(request):
    """Admin-only analytics view"""
    if not request.session.get('admin_authenticated'):
        return redirect('admin_login')
    
    # Get all clickstream events for all users
    recent_events = ClickstreamEvent.objects.all()[:100]
    
    # Get user statistics
    total_users = User.objects.count()
    total_events = ClickstreamEvent.objects.count()
    total_content = Content.objects.count()
    
    # User progress statistics
    user_progress_stats = UserProgress.objects.filter(completed=True).count()
    
    context = {
        'recent_events': recent_events,
        'total_users': total_users,
        'total_events': total_events,
        'total_content': total_content,
        'user_progress_stats': user_progress_stats,
    }
    
    return render(request, 'learning_app/admin_analytics.html', context) 