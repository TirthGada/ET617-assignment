from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Avg, Count
import json

from .models import Course, Content, Quiz, UserProgress, ClickstreamEvent, VideoAnalytics, TeacherProfile, LiveQuiz, QuizQuestion, QuizParticipant, QuizAnswer, StudentAnalysis, QuizAnalytics, Feedback, Doubt, Poll, PollOption, PollResponse, PollAnalytics
from .utils import get_client_ip, log_clickstream_event, generate_word_cloud_data, create_word_cloud_visualization
from .serializers import FeedbackSerializer, DoubtSerializer
from .llm_utils import llm_service
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import base64
from django.db import transaction
from collections import Counter
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False
import io
import base64


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

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Avg, Count
from .models import Feedback, Doubt
from .serializers import FeedbackSerializer, DoubtSerializer


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user if not serializer.validated_data.get('anonymous') else None
        serializer.save(student=user)


class DoubtViewSet(viewsets.ModelViewSet):
    queryset = Doubt.objects.all()
    serializer_class = DoubtSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user if not serializer.validated_data.get('anonymous') else None
        serializer.save(student=user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def answer(self, request, pk=None):
        doubt = self.get_object()
        doubt.resolution = request.data.get('resolution')
        doubt.status = 'answered'
        doubt.teacher = request.user
        doubt.resolved_at = timezone.now()
        doubt.save()
        return Response(DoubtSerializer(doubt).data)


# Dashboard APIs
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_summary(request):
    total_feedback = Feedback.objects.count()
    avg_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg']
    total_doubts = Doubt.objects.count()
    unanswered_doubts = Doubt.objects.filter(status='unanswered').count()

    return Response({
        "total_feedback": total_feedback,
        "avg_rating": avg_rating,
        "total_doubts": total_doubts,
        "unanswered_doubts": unanswered_doubts,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_chart_data(request):
    # Example chart data: count feedback per rating
    feedback_counts = Feedback.objects.values('rating').annotate(total=Count('id')).order_by('rating')
    labels = [str(fc['rating']) for fc in feedback_counts]
    values = [fc['total'] for fc in feedback_counts]

    return Response({
        "labels": labels,
        "values": values,
    })


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
def submit_quiz_old(request, content_id):
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


# ============ NEW QUIZ SYSTEM VIEWS ============

def teacher_login_view(request):
    """Teacher login/registration view"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'logout':
            # Teacher logout
            request.session.pop('teacher_id', None)
            request.session.pop('teacher_email', None)
            messages.success(request, 'Teacher logged out successfully!')
            return redirect('home')
        
        email = request.POST.get('email')
        
        if action == 'login':
            try:
                teacher_profile = TeacherProfile.objects.get(email=email)
                request.session['teacher_id'] = teacher_profile.id
                request.session['teacher_email'] = email
                messages.success(request, f'Welcome back, {teacher_profile.user.username}!')
                return redirect('teacher_dashboard')
            except TeacherProfile.DoesNotExist:
                messages.error(request, 'Teacher account not found. Please register first.')
        
        elif action == 'register':
            username = request.POST.get('username', email.split('@')[0])
            
            if TeacherProfile.objects.filter(email=email).exists():
                messages.error(request, 'Teacher account with this email already exists.')
            else:
                # Create user and teacher profile
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='teacher123'  # Default password
                )
                teacher_profile = TeacherProfile.objects.create(
                    user=user,
                    email=email
                )
                request.session['teacher_id'] = teacher_profile.id
                request.session['teacher_email'] = email
                messages.success(request, 'Teacher account created successfully!')
                return redirect('teacher_dashboard')
    
    return render(request, 'learning_app/teacher_login.html')


def teacher_required(view_func):
    """Decorator to ensure user is authenticated as teacher"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('teacher_id'):
            messages.error(request, 'Please login as a teacher first.')
            return redirect('teacher_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard showing all quizzes"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    
    quizzes = LiveQuiz.objects.filter(teacher=teacher_profile).order_by('-created_at')
    
    context = {
        'teacher': teacher_profile,
        'quizzes': quizzes
    }
    
    return render(request, 'learning_app/teacher_dashboard.html', context)


@teacher_required
def create_quiz(request):
    """Create a new quiz"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        time_limit = int(request.POST.get('time_limit', 30))
        
        quiz = LiveQuiz.objects.create(
            teacher=teacher_profile,
            title=title,
            description=description,
            time_limit=time_limit
        )
        
        messages.success(request, f'Quiz "{title}" created successfully!')
        return redirect('edit_quiz', quiz_id=quiz.id)
    
    return render(request, 'learning_app/create_quiz.html')


@teacher_required
def edit_quiz(request, quiz_id):
    """Edit quiz and manage questions"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    quiz = get_object_or_404(LiveQuiz, id=quiz_id, teacher=teacher_profile)
    
    questions = quiz.questions.all().order_by('order')
    
    context = {
        'quiz': quiz,
        'questions': questions
    }
    
    return render(request, 'learning_app/edit_quiz.html', context)


@teacher_required
@csrf_exempt
def add_question_manual(request, quiz_id):
    """Add question manually"""
    if request.method == 'POST':
        teacher_id = request.session.get('teacher_id')
        teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
        quiz = get_object_or_404(LiveQuiz, id=quiz_id, teacher=teacher_profile)
        
        data = json.loads(request.body)
        
        question = QuizQuestion.objects.create(
            quiz=quiz,
            question_text=data.get('question_text'),
            option_a=data.get('option_a'),
            option_b=data.get('option_b'),
            option_c=data.get('option_c'),
            option_d=data.get('option_d'),
            correct_answer=data.get('correct_answer'),
            explanation=data.get('explanation', ''),
            generation_method='manual',
            order=quiz.questions.count() + 1
        )
        
        return JsonResponse({
            'success': True,
            'question_id': question.id,
            'message': 'Question added successfully!'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@teacher_required
@csrf_exempt
def generate_questions_from_text(request, quiz_id):
    """Generate questions from text using LLM"""
    if request.method == 'POST':
        teacher_id = request.session.get('teacher_id')
        teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
        quiz = get_object_or_404(LiveQuiz, id=quiz_id, teacher=teacher_profile)
        
        data = json.loads(request.body)
        text_content = data.get('text_content')
        topic = data.get('topic', quiz.title)
        num_questions = int(data.get('num_questions', 5))
        
        print(f"🎯 Generating {num_questions} questions from text for quiz: {quiz.title}")
        
        # Generate questions using LLM
        generated_questions = llm_service.generate_questions_from_text(
            text_content, num_questions, topic
        )
        
        # Save generated questions
        questions_created = []
        for i, q_data in enumerate(generated_questions):
            question = QuizQuestion.objects.create(
                quiz=quiz,
                question_text=q_data['question_text'],
                option_a=q_data['option_a'],
                option_b=q_data['option_b'],
                option_c=q_data['option_c'],
                option_d=q_data['option_d'],
                correct_answer=q_data['correct_answer'],
                explanation=q_data.get('explanation', ''),
                generation_method='llm_text',
                source_text=text_content[:500],  # Store first 500 chars as reference
                order=quiz.questions.count() + i + 1
            )
            questions_created.append(question.id)
        
        return JsonResponse({
            'success': True,
            'questions_created': len(questions_created),
            'message': f'{len(questions_created)} questions generated successfully!'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@teacher_required
@csrf_exempt
def generate_questions_from_pdf(request, quiz_id):
    """Generate questions from PDF using LLM"""
    if request.method == 'POST':
        teacher_id = request.session.get('teacher_id')
        teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
        quiz = get_object_or_404(LiveQuiz, id=quiz_id, teacher=teacher_profile)
        
        pdf_file = request.FILES.get('pdf_file')
        topic = request.POST.get('topic', quiz.title)
        num_questions = int(request.POST.get('num_questions', 5))
        
        if not pdf_file:
            return JsonResponse({'success': False, 'error': 'No PDF file provided'})
        
        print(f"🎯 Generating {num_questions} questions from PDF for quiz: {quiz.title}")
        
        # Generate questions using LLM
        generated_questions = llm_service.generate_questions_from_pdf(
            pdf_file, num_questions, topic
        )
        
        # Save generated questions
        questions_created = []
        for i, q_data in enumerate(generated_questions):
            question = QuizQuestion.objects.create(
                quiz=quiz,
                question_text=q_data['question_text'],
                option_a=q_data['option_a'],
                option_b=q_data['option_b'],
                option_c=q_data['option_c'],
                option_d=q_data['option_d'],
                correct_answer=q_data['correct_answer'],
                explanation=q_data.get('explanation', ''),
                generation_method='llm_pdf',
                source_text=f"Generated from PDF: {pdf_file.name}",
                order=quiz.questions.count() + i + 1
            )
            questions_created.append(question.id)
        
        return JsonResponse({
            'success': True,
            'questions_created': len(questions_created),
            'message': f'{len(questions_created)} questions generated from PDF!'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@teacher_required
def start_quiz(request, quiz_id):
    """Start a quiz (make it active)"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    quiz = get_object_or_404(LiveQuiz, id=quiz_id, teacher=teacher_profile)
    
    if quiz.questions.count() == 0:
        messages.error(request, 'Cannot start quiz without questions!')
        return redirect('edit_quiz', quiz_id=quiz.id)
    
    quiz.status = 'active'
    quiz.started_at = timezone.now()
    quiz.save()
    
    messages.success(request, f'Quiz "{quiz.title}" is now live! Share code: {quiz.quiz_code}')
    return redirect('quiz_monitor', quiz_id=quiz.id)


@teacher_required
def quiz_monitor(request, quiz_id):
    """Monitor active quiz - see participants and real-time stats"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    quiz = get_object_or_404(LiveQuiz, id=quiz_id, teacher=teacher_profile)
    
    participants = quiz.participants.all().order_by('-joined_at')
    
    context = {
        'quiz': quiz,
        'participants': participants,
        'total_questions': quiz.questions.count()
    }
    
    return render(request, 'learning_app/quiz_monitor.html', context)


@teacher_required
def end_quiz(request, quiz_id):
    """End an active quiz"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    quiz = get_object_or_404(LiveQuiz, id=quiz_id, teacher=teacher_profile)
    
    quiz.status = 'ended'
    quiz.ended_at = timezone.now()
    quiz.save()
    
    # Generate analytics for the quiz
    generate_quiz_analytics(quiz)
    
    messages.success(request, f'Quiz "{quiz.title}" has been ended.')
    return redirect('quiz_results', quiz_id=quiz.id)


@teacher_required
def quiz_results(request, quiz_id):
    """View quiz results and analytics"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    quiz = get_object_or_404(LiveQuiz, id=quiz_id, teacher=teacher_profile)
    
    participants = quiz.participants.all().order_by('-score')
    analytics = getattr(quiz, 'analytics', None)
    
    # Generate word cloud if analytics exist
    word_cloud_image = None
    if analytics and analytics.common_mistakes:
        word_cloud_image = generate_word_cloud(analytics.common_mistakes)
    
    context = {
        'quiz': quiz,
        'participants': participants,
        'analytics': analytics,
        'word_cloud_image': word_cloud_image
    }
    
    return render(request, 'learning_app/quiz_results.html', context)


# ============ STUDENT QUIZ VIEWS ============

def join_quiz(request):
    """Student joins quiz using code"""
    if request.method == 'POST':
        quiz_code = request.POST.get('quiz_code', '').upper()
        student_name = request.POST.get('student_name')
        student_email = request.POST.get('student_email')
        
        try:
            quiz = LiveQuiz.objects.get(quiz_code=quiz_code, status='active')
            
            # Check if student already joined
            participant, created = QuizParticipant.objects.get_or_create(
                quiz=quiz,
                student_email=student_email,
                defaults={
                    'student_name': student_name,
                    'total_questions': quiz.questions.count()
                }
            )
            
            if not created:
                messages.info(request, 'You have already joined this quiz.')
            
            request.session['participant_id'] = participant.id
            return redirect('take_quiz', quiz_id=quiz.id)
            
        except LiveQuiz.DoesNotExist:
            messages.error(request, 'Invalid quiz code or quiz is not active.')
    
    return render(request, 'learning_app/join_quiz.html')


def take_quiz(request, quiz_id):
    """Student takes the quiz"""
    participant_id = request.session.get('participant_id')
    if not participant_id:
        messages.error(request, 'Please join the quiz first.')
        return redirect('join_quiz')
    
    participant = get_object_or_404(QuizParticipant, id=participant_id)
    quiz = get_object_or_404(LiveQuiz, id=quiz_id, status='active')
    
    if participant.submitted_at:
        messages.info(request, 'You have already submitted this quiz.')
        return redirect('quiz_result', quiz_id=quiz.id)
    
    questions = quiz.questions.all().order_by('order')
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'participant': participant
    }
    
    return render(request, 'learning_app/take_quiz.html', context)


@csrf_exempt
def submit_quiz(request, quiz_id):
    """Submit quiz answers"""
    if request.method == 'POST':
        participant_id = request.session.get('participant_id')
        if not participant_id:
            return JsonResponse({'success': False, 'error': 'Not authorized'})
        
        participant = get_object_or_404(QuizParticipant, id=participant_id)
        quiz = get_object_or_404(LiveQuiz, id=quiz_id)
        
        if participant.submitted_at:
            return JsonResponse({'success': False, 'error': 'Already submitted'})
        
        data = json.loads(request.body)
        answers = data.get('answers', {})
        
        score = 0
        total_questions = quiz.questions.count()
        
        # Save answers and calculate score
        with transaction.atomic():
            for question_id, selected_answer in answers.items():
                question = get_object_or_404(QuizQuestion, id=question_id, quiz=quiz)
                is_correct = selected_answer == question.correct_answer
                
                QuizAnswer.objects.create(
                    participant=participant,
                    question=question,
                    selected_answer=selected_answer,
                    is_correct=is_correct
                )
                
                if is_correct:
                    score += 1
            
            # Update participant
            participant.score = score
            participant.submitted_at = timezone.now()
            participant.save()
        
        # Generate student analysis
        generate_student_analysis(participant)
        
        return JsonResponse({
            'success': True,
            'score': score,
            'total': total_questions,
            'message': 'Quiz submitted successfully!'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def quiz_result(request, quiz_id):
    """Show student's quiz result and analysis"""
    participant_id = request.session.get('participant_id')
    if not participant_id:
        messages.error(request, 'Please join the quiz first.')
        return redirect('join_quiz')
    
    participant = get_object_or_404(QuizParticipant, id=participant_id)
    quiz = get_object_or_404(LiveQuiz, id=quiz_id)
    
    if not participant.submitted_at:
        messages.error(request, 'Please complete the quiz first.')
        return redirect('take_quiz', quiz_id=quiz.id)
    
    # Get student's answers
    answers = participant.answers.all().select_related('question')
    analysis = getattr(participant, 'analysis', None)
    
    # Generate Bloom's taxonomy questions if analysis exists
    bloom_questions = []
    if analysis and analysis.weak_topics:
        for topic in analysis.weak_topics[:2]:  # Limit to 2 topics
            bloom_questions.extend(
                llm_service.generate_bloom_taxonomy_questions(topic, analysis.reading_material)
            )
    
    context = {
        'quiz': quiz,
        'participant': participant,
        'answers': answers,
        'analysis': analysis,
        'bloom_questions': bloom_questions
    }
    
    return render(request, 'learning_app/quiz_result.html', context)


# ============ UTILITY FUNCTIONS ============

def generate_quiz_analytics(quiz):
    """Generate analytics for completed quiz"""
    print(f"🎯 Generating analytics for quiz: {quiz.title}")
    
    participants = quiz.participants.filter(submitted_at__isnull=False)
    total_participants = participants.count()
    
    if total_participants == 0:
        return
    
    # Calculate metrics
    total_score = sum(p.score for p in participants)
    average_score = total_score / total_participants if total_participants > 0 else 0
    completion_rate = (total_participants / quiz.participants.count()) * 100
    
    # Find difficult questions (less than 50% correct)
    difficult_questions = []
    common_mistakes = {}
    
    for question in quiz.questions.all():
        correct_answers = QuizAnswer.objects.filter(question=question, is_correct=True).count()
        total_answers = QuizAnswer.objects.filter(question=question).count()
        
        if total_answers > 0:
            success_rate = (correct_answers / total_answers) * 100
            if success_rate < 50:
                difficult_questions.append({
                    'question_id': question.id,
                    'question_text': question.question_text,
                    'success_rate': success_rate
                })
        
        # Collect wrong answers for word cloud
        wrong_answers = QuizAnswer.objects.filter(question=question, is_correct=False)
        for answer in wrong_answers:
            option_text = getattr(question, f'option_{answer.selected_answer.lower()}', '')
            if option_text:
                common_mistakes[option_text] = common_mistakes.get(option_text, 0) + 1
    
    # Save analytics
    QuizAnalytics.objects.update_or_create(
        quiz=quiz,
        defaults={
            'total_participants': total_participants,
            'average_score': average_score,
            'completion_rate': completion_rate,
            'difficult_questions': difficult_questions,
            'common_mistakes': common_mistakes,
            'topic_performance': {}  # Could be enhanced later
        }
    )


def generate_student_analysis(participant):
    """Generate personalized analysis for student"""
    print(f"🎯 Generating analysis for student: {participant.student_name}")
    
    quiz_answers = participant.answers.all()
    analysis_data = llm_service.analyze_student_performance(participant, quiz_answers)
    
    # Generate practice questions
    bloom_questions = []
    if analysis_data['weak_topics']:
        for topic in analysis_data['weak_topics'][:2]:
            bloom_questions.extend(
                llm_service.generate_bloom_taxonomy_questions(
                    topic, 
                    analysis_data['reading_material']
                )[:3]  # 3 questions per topic
            )
    
    # Save analysis
    StudentAnalysis.objects.update_or_create(
        participant=participant,
        defaults={
            'weak_topics': analysis_data['weak_topics'],
            'strong_topics': analysis_data['strong_topics'],
            'recommendations': analysis_data['recommendations'],
            'reading_material': analysis_data['reading_material'],
            'practice_questions': bloom_questions
        }
    )


def generate_word_cloud(common_mistakes):
    """Generate word cloud from common mistakes"""
    if not common_mistakes or not WORDCLOUD_AVAILABLE:
        return None
    
    try:
        # Create word cloud
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white',
            colormap='viridis'
        ).generate_from_frequencies(common_mistakes)
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        
        # Encode to base64
        img_buffer.seek(0)
        image_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        return f"data:image/png;base64,{image_base64}"
        
    except Exception as e:
        print(f"❌ Word cloud generation error: {str(e)}")
        return None


@teacher_required
def quiz_mistake_analysis(request, quiz_id):
    """Generate LLM-powered analysis of student mistakes for teachers"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    quiz = get_object_or_404(LiveQuiz, id=quiz_id, teacher=teacher_profile)
    
    print(f"🔍 DEBUG: quiz_mistake_analysis called - Method: {request.method}, Quiz: {quiz.title}")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"🔍 DEBUG: POST action received: {action}")
        
        if action == 'generate_mistake_analysis':
            print(f"🎯 Generating mistake analysis for quiz: {quiz.title}")
            
            # Collect all wrong answers from all participants
            wrong_answers = []
            participants = quiz.participants.filter(submitted_at__isnull=False)
            
            print(f"🔍 DEBUG: Found {participants.count()} completed participants")
            
            for participant in participants:
                wrong_participant_answers = participant.answers.filter(is_correct=False)
                print(f"🔍 DEBUG: {participant.student_name} has {wrong_participant_answers.count()} wrong answers")
                
                for answer in wrong_participant_answers:
                    wrong_answers.append({
                        'student': participant.student_name,
                        'question': answer.question.question_text,
                        'selected': answer.selected_answer,
                        'correct': answer.question.correct_answer,
                        'selected_text': getattr(answer.question, f'option_{answer.selected_answer.lower()}', ''),
                        'correct_text': getattr(answer.question, f'option_{answer.question.correct_answer.lower()}', '')
                    })
            
            print(f"🔍 DEBUG: Total wrong answers collected: {len(wrong_answers)}")
            
            if wrong_answers:
                # Generate analysis using Groq
                analysis_text = llm_service.generate_mistake_analysis_for_teachers(quiz, wrong_answers)
                
                # Store in session to display
                request.session['mistake_analysis'] = analysis_text
                messages.success(request, 'Mistake analysis generated successfully!')
            else:
                messages.info(request, 'No wrong answers found - all students performed perfectly!')
        
        elif action == 'generate_remedial_content':
            print(f"🎯 Generating remedial content for students")
            
            # Get the mistake analysis from session
            mistake_analysis = request.session.get('mistake_analysis', '')
            
            if mistake_analysis:
                # Generate educational content for students
                remedial_content = llm_service.generate_remedial_content_for_students(quiz, mistake_analysis)
                
                # Store in session
                request.session['remedial_content'] = remedial_content
                messages.success(request, 'Remedial content generated for students!')
            else:
                messages.error(request, 'Please generate mistake analysis first!')
    
    # Get data from session
    mistake_analysis = request.session.get('mistake_analysis', '')
    remedial_content = request.session.get('remedial_content', '')
    
    context = {
        'quiz': quiz,
        'mistake_analysis': mistake_analysis,
        'remedial_content': remedial_content,
        'participants': quiz.participants.filter(submitted_at__isnull=False)
    }
    
    return render(request, 'learning_app/quiz_mistake_analysis.html', context)


def student_help_content(request, quiz_id):
    """Show AI-generated help content to students"""
    quiz = get_object_or_404(LiveQuiz, id=quiz_id)
    participant_id = request.session.get('participant_id')
    
    # Check if student participated in this quiz
    participant = None
    if participant_id:
        try:
            participant = QuizParticipant.objects.get(id=participant_id, quiz=quiz)
        except QuizParticipant.DoesNotExist:
            pass
    
    # Get remedial content from teacher's session (this would be improved in production)
    # For now, we'll generate it on-demand if student needs help
    remedial_content = ""
    
    if participant and participant.submitted_at:
        # Check if student needs help (scored below 70%)
        if participant.score < (participant.total_questions * 0.7):
            # Generate personalized help content
            wrong_answers = []
            for answer in participant.answers.filter(is_correct=False):
                wrong_answers.append({
                    'question': answer.question.question_text,
                    'selected': answer.selected_answer,
                    'correct': answer.question.correct_answer,
                    'selected_text': getattr(answer.question, f'option_{answer.selected_answer.lower()}', ''),
                    'correct_text': getattr(answer.question, f'option_{answer.question.correct_answer.lower()}', '')
                })
            
            if wrong_answers:
                print(f"🎯 Generating personalized help content for {participant.student_name}")
                remedial_content = llm_service.generate_personalized_help_content(participant, wrong_answers)
    
    context = {
        'quiz': quiz,
        'participant': participant,
        'remedial_content': remedial_content,
        'needs_help': participant and participant.score < (participant.total_questions * 0.7) if participant else False
    }
    
    return render(request, 'learning_app/student_help_content.html', context) 


# ============ POLL SYSTEM VIEWS ============

@teacher_required
def teacher_polls(request):
    """Teacher polls dashboard"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    
    polls = Poll.objects.filter(teacher=teacher_profile).order_by('-created_at')
    
    context = {
        'teacher': teacher_profile,
        'polls': polls
    }
    
    return render(request, 'learning_app/teacher_polls.html', context)


@teacher_required
def create_poll(request):
    """Create a new poll"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        time_limit = int(request.POST.get('time_limit', 10))
        
        poll = Poll.objects.create(
            teacher=teacher_profile,
            title=title,
            description=description,
            time_limit=time_limit
        )
        
        messages.success(request, f'Poll "{title}" created successfully!')
        return redirect('edit_poll', poll_id=poll.id)
    
    return render(request, 'learning_app/create_poll.html')


@teacher_required
def edit_poll(request, poll_id):
    """Edit poll and manage options"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    poll = get_object_or_404(Poll, id=poll_id, teacher=teacher_profile)
    
    options = poll.options.all().order_by('order')
    
    context = {
        'poll': poll,
        'options': options
    }
    
    return render(request, 'learning_app/edit_poll.html', context)


@teacher_required
@csrf_exempt
def add_poll_option(request, poll_id):
    """Add poll option"""
    if request.method == 'POST':
        teacher_id = request.session.get('teacher_id')
        teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
        poll = get_object_or_404(Poll, id=poll_id, teacher=teacher_profile)
        
        data = json.loads(request.body)
        option_text = data.get('option_text')
        
        option = PollOption.objects.create(
            poll=poll,
            text=option_text,
            order=poll.options.count() + 1
        )
        
        return JsonResponse({
            'success': True,
            'option_id': option.id,
            'message': 'Option added successfully!'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@teacher_required
@csrf_exempt
def remove_poll_option(request, poll_id):
    """Remove poll option"""
    if request.method == 'POST':
        teacher_id = request.session.get('teacher_id')
        teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
        poll = get_object_or_404(Poll, id=poll_id, teacher=teacher_profile)
        
        data = json.loads(request.body)
        option_id = data.get('option_id')
        
        option = get_object_or_404(PollOption, id=option_id, poll=poll)
        option.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Option removed successfully!'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@teacher_required
def start_poll(request, poll_id):
    """Start a poll (make it active)"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    poll = get_object_or_404(Poll, id=poll_id, teacher=teacher_profile)
    
    if poll.options.count() < 2:
        messages.error(request, 'Cannot start poll with less than 2 options!')
        return redirect('edit_poll', poll_id=poll.id)
    
    poll.status = 'active'
    poll.started_at = timezone.now()
    poll.save()
    
    messages.success(request, f'Poll "{poll.title}" is now live! Share code: {poll.poll_code}')
    return redirect('poll_monitor', poll_id=poll.id)


@teacher_required
def poll_monitor(request, poll_id):
    """Monitor active poll - see responses and real-time stats"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    poll = get_object_or_404(Poll, id=poll_id, teacher=teacher_profile)
    
    responses = poll.responses.all().order_by('-responded_at')
    
    context = {
        'poll': poll,
        'responses': responses,
        'total_options': poll.options.count()
    }
    
    return render(request, 'learning_app/poll_monitor.html', context)


@teacher_required
def end_poll(request, poll_id):
    """End an active poll"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    poll = get_object_or_404(Poll, id=poll_id, teacher=teacher_profile)
    
    poll.status = 'ended'
    poll.ended_at = timezone.now()
    poll.save()
    
    # Generate analytics for the poll
    generate_poll_analytics(poll)
    
    messages.success(request, f'Poll "{poll.title}" has been ended.')
    return redirect('poll_results', poll_id=poll.id)


def generate_poll_analytics(poll):
    """Generate analytics for completed poll"""
    print(f"🎯 Generating analytics for poll: {poll.title}")
    
    responses = poll.responses.all()
    total_responses = responses.count()
    
    if total_responses == 0:
        return
    
    # Count responses per option
    option_counts = {}
    for option in poll.options.all():
        count = responses.filter(option=option).count()
        option_counts[option.id] = {
            'text': option.text,
            'count': count,
            'percentage': (count / total_responses * 100) if total_responses > 0 else 0
        }
    
    # Save analytics
    PollAnalytics.objects.update_or_create(
        poll=poll,
        defaults={
            'total_responses': total_responses,
            'option_counts': option_counts,
            'response_rate': 100.0  # Could be enhanced with target audience
        }
    )


@teacher_required
def poll_results(request, poll_id):
    """View poll results and analytics"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    poll = get_object_or_404(Poll, id=poll_id, teacher=teacher_profile)
    
    responses = poll.responses.all().order_by('-responded_at')
    analytics = getattr(poll, 'analytics', None)
    
    context = {
        'poll': poll,
        'responses': responses,
        'analytics': analytics
    }
    
    return render(request, 'learning_app/poll_results.html', context)


# ============ STUDENT POLL VIEWS ============

def join_poll(request):
    """Student joins poll using code"""
    if request.method == 'POST':
        poll_code = request.POST.get('poll_code', '').upper()
        student_name = request.POST.get('student_name')
        student_email = request.POST.get('student_email')
        
        try:
            poll = Poll.objects.get(poll_code=poll_code, status='active')
            
            request.session['student_name'] = student_name
            request.session['student_email'] = student_email
            request.session['poll_id'] = poll.id
            
            return redirect('take_poll', poll_id=poll.id)
            
        except Poll.DoesNotExist:
            messages.error(request, 'Invalid poll code or poll is not active.')
    
    return render(request, 'learning_app/join_poll.html')


def take_poll(request, poll_id):
    """Student takes the poll"""
    student_name = request.session.get('student_name')
    student_email = request.session.get('student_email')
    
    if not student_name or not student_email:
        messages.error(request, 'Please join the poll first.')
        return redirect('join_poll')
    
    poll = get_object_or_404(Poll, id=poll_id, status='active')
    
    # Check if student already responded
    if PollResponse.objects.filter(poll=poll, student_email=student_email).exists():
        messages.info(request, 'You have already responded to this poll.')
        return redirect('poll_result', poll_id=poll.id)
    
    options = poll.options.all().order_by('order')
    
    context = {
        'poll': poll,
        'options': options,
        'student_name': student_name
    }
    
    return render(request, 'learning_app/take_poll.html', context)


@csrf_exempt
def submit_poll(request, poll_id):
    """Submit poll response"""
    if request.method == 'POST':
        student_name = request.session.get('student_name')
        student_email = request.session.get('student_email')
        
        if not student_name or not student_email:
            return JsonResponse({'success': False, 'error': 'Not authorized'})
        
        poll = get_object_or_404(Poll, id=poll_id, status='active')
        
        # Check if student already responded
        if PollResponse.objects.filter(poll=poll, student_email=student_email).exists():
            return JsonResponse({'success': False, 'error': 'Already responded'})
        
        data = json.loads(request.body)
        option_id = data.get('option_id')
        
        if not option_id:
            return JsonResponse({'success': False, 'error': 'No option selected'})
        
        option = get_object_or_404(PollOption, id=option_id, poll=poll)
        
        # Save response
        PollResponse.objects.create(
            poll=poll,
            option=option,
            student_name=student_name,
            student_email=student_email
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Response submitted successfully!'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def poll_result(request, poll_id):
    """Show student's poll result"""
    student_email = request.session.get('student_email')
    if not student_email:
        messages.error(request, 'Please join the poll first.')
        return redirect('join_poll')
    
    poll = get_object_or_404(Poll, id=poll_id)
    
    # Get student's response
    try:
        response = PollResponse.objects.get(poll=poll, student_email=student_email)
    except PollResponse.DoesNotExist:
        messages.error(request, 'You have not responded to this poll.')
        return redirect('take_poll', poll_id=poll.id)
    
    # Get all responses for comparison
    all_responses = poll.responses.all()
    analytics = getattr(poll, 'analytics', None)
    
    context = {
        'poll': poll,
        'response': response,
        'all_responses': all_responses,
        'analytics': analytics
    }
    
    return render(request, 'learning_app/poll_result.html', context)


@teacher_required
def poll_word_cloud_data(request, poll_id):
    """Generate word cloud data for poll responses"""
    teacher_id = request.session.get('teacher_id')
    teacher_profile = get_object_or_404(TeacherProfile, id=teacher_id)
    poll = get_object_or_404(Poll, id=poll_id, teacher=teacher_profile)
    
    # Collect text responses for word cloud
    text_responses = []
    for response in poll.responses.all():
        text_responses.append(response.option.text)
    
    # Simple word frequency analysis
    word_freq = {}
    for text in text_responses:
        words = text.lower().split()
        for word in words:
            if len(word) > 3:  # Filter short words
                word_freq[word] = word_freq.get(word, 0) + 1
    
    return JsonResponse({
        'success': True,
        'word_data': word_freq
    })